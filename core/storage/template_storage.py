"""
模板存储模块
负责模板文件的存储、版本管理、文件哈希计算等功能
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.config import get_config

logger = logging.getLogger(__name__)


class TemplateStorage:
    """
    模板存储类
    负责模板文件的存储、版本管理、文件哈希计算等
    """

    MANIFEST_FILENAME = "manifest.json"
    VERSION_META_FILENAME = "metadata.json"
    DEFAULT_FILENAME = "template.bin"

    def __init__(self, base_path: Optional[str] = None):
        """
        初始化模板存储

        Args:
            base_path: 模板存储基础路径，如果为 None 则从配置中获取
        """
        if base_path is None:
            config = get_config()
            storage_config = getattr(config, "storage", {}) or {}
            base_path = storage_config.get("template_path", "static/templates")

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info("Template storage initialized at %s", self.base_path)

    def save_template(
        self,
        template_id: str,
        version: str,
        file_content: bytes,
        filename: Optional[str] = None,
    ) -> str:
        """
        保存模板文件

        Args:
            template_id: 模板ID
            version: 版本号
            file_content: 文件内容（字节）
            filename: 原始文件名（可选，用于保留扩展名）

        Returns:
            保存的文件路径（绝对路径）
        """
        template_id = self._validate_identifier(template_id, "template_id")
        version = self._validate_identifier(version, "version")

        if not isinstance(file_content, (bytes, bytearray)):
            raise ValueError("file_content 必须是 bytes 或 bytearray")

        file_bytes = bytes(file_content)
        safe_filename = self._sanitize_filename(filename) if filename else f"{version}_{self.DEFAULT_FILENAME}"

        template_dir = self._get_template_dir(template_id)
        version_dir = template_dir / version
        if version_dir.exists():
            shutil.rmtree(version_dir)
        version_dir.mkdir(parents=True, exist_ok=True)

        file_path = version_dir / safe_filename
        self._atomic_write(file_path, file_bytes)

        now = datetime.now(timezone.utc)
        version_metadata = {
            "filename": safe_filename,
            "file_size": len(file_bytes),
            "hash": self.calculate_hash(file_bytes),
            "saved_at": now.isoformat(),
            "saved_at_ts": now.timestamp(),
            "relative_path": str(file_path.relative_to(template_dir)),
        }
        self._write_json(version_dir / self.VERSION_META_FILENAME, version_metadata)

        manifest = self._load_manifest(template_id)
        manifest.setdefault("template_id", template_id)
        manifest.setdefault("created_at", now.isoformat())
        manifest["updated_at"] = now.isoformat()
        manifest.setdefault("versions", {})
        manifest["versions"][version] = version_metadata
        manifest["latest_version"] = self._determine_latest_version(manifest["versions"])

        self._write_manifest(template_id, manifest)
        logger.debug("Template %s@%s saved to %s", template_id, version, file_path)
        return str(file_path)

    def get_template(
        self,
        template_id: str,
        version: Optional[str] = None,
    ) -> bytes:
        """
        获取模板文件内容

        Args:
            template_id: 模板ID
            version: 版本号，如果为 None 则返回最新版本

        Returns:
            模板文件内容（字节）

        Raises:
            FileNotFoundError: 模板或指定版本不存在
        """
        path = self.get_template_path(template_id, version)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"模板文件不存在: {path}")
        return path.read_bytes()

    def delete_template(
        self,
        template_id: str,
        version: Optional[str] = None,
    ) -> bool:
        """
        删除模板文件

        Args:
            template_id: 模板ID
            version: 版本号，如果为 None 则删除所有版本

        Returns:
            是否删除成功
        """
        template_id = self._validate_identifier(template_id, "template_id")
        template_dir = self._get_template_dir(template_id)

        if version is None:
            if not template_dir.exists():
                return False
            shutil.rmtree(template_dir)
            logger.debug("Template %s removed completely", template_id)
            return True

        version = self._validate_identifier(version, "version")
        manifest = self._load_manifest(template_id)
        versions = manifest.get("versions", {})

        version_path = template_dir / version
        removed = False
        if version_path.exists():
            shutil.rmtree(version_path)
            removed = True

        if version in versions:
            versions.pop(version, None)
            removed = True
            manifest["versions"] = versions
            manifest["latest_version"] = self._determine_latest_version(versions)
            now = datetime.now(timezone.utc).isoformat()
            manifest["updated_at"] = now

            if versions:
                self._write_manifest(template_id, manifest)
            else:
                manifest_path = template_dir / self.MANIFEST_FILENAME
                if manifest_path.exists():
                    manifest_path.unlink()
                if template_dir.exists():
                    try:
                        template_dir.rmdir()
                    except OSError:
                        # 目录仍包含其他文件，忽略
                        pass
        return removed

    def calculate_hash(self, file_content: bytes) -> str:
        """
        计算文件哈希值

        Args:
            file_content: 文件内容（字节）

        Returns:
            文件哈希值（SHA256格式：sha256:xxx...）
        """
        hash_obj = hashlib.sha256(file_content)
        hash_value = hash_obj.hexdigest()
        return f"sha256:{hash_value}"

    def list_versions(self, template_id: str) -> List[str]:
        """
        列出模板的所有版本

        Args:
            template_id: 模板ID

        Returns:
            版本号列表，按创建时间倒序排列
        """
        template_id = self._validate_identifier(template_id, "template_id")
        manifest = self._load_manifest(template_id, ensure_exists=False)
        versions: Dict[str, Dict[str, Any]] = manifest.get("versions", {})
        if not versions:
            return []

        sorted_versions = sorted(
            versions.items(),
            key=lambda item: item[1].get("saved_at_ts", 0),
            reverse=True,
        )
        return [version for version, _ in sorted_versions]

    def get_template_path(
        self,
        template_id: str,
        version: Optional[str] = None,
    ) -> Path:
        """
        获取模板文件路径（不验证文件是否存在）

        Args:
            template_id: 模板ID
            version: 版本号，如果为 None 则返回最新版本路径

        Returns:
            模板文件路径

        Raises:
            FileNotFoundError: 当模板或版本不存在时
        """
        template_id = self._validate_identifier(template_id, "template_id")
        manifest = self._load_manifest(template_id, ensure_exists=False)
        versions = manifest.get("versions", {})

        selected_version = version
        if selected_version is None:
            selected_version = manifest.get("latest_version")

        if selected_version is None:
            raise FileNotFoundError(f"模板 {template_id} 不存在可用版本")

        if version is not None:
            selected_version = self._validate_identifier(selected_version, "version")

        version_entry = versions.get(selected_version)
        template_dir = self._get_template_dir(template_id)

        if version_entry:
            relative_path = version_entry.get("relative_path")
            if relative_path:
                return template_dir / relative_path
            filename = version_entry.get("filename", self.DEFAULT_FILENAME)
            return template_dir / selected_version / filename

        # 回退：直接使用目录结构推断
        version_dir = template_dir / selected_version
        if not version_dir.exists():
            raise FileNotFoundError(f"模板 {template_id} 的版本 {selected_version} 不存在")

        for child in version_dir.iterdir():
            if child.is_file() and child.name != self.VERSION_META_FILENAME:
                return child

        raise FileNotFoundError(f"模板 {template_id} 的版本 {selected_version} 没有可用文件")

    def exists(
        self,
        template_id: str,
        version: Optional[str] = None,
    ) -> bool:
        """
        检查模板文件是否存在

        Args:
            template_id: 模板ID
            version: 版本号，如果为 None 则检查最新版本

        Returns:
            文件是否存在
        """
        try:
            path = self.get_template_path(template_id, version)
        except FileNotFoundError:
            return False
        return path.exists() and path.is_file()

    # ---------------------------------------------------------------------
    # 内部工具方法
    # ---------------------------------------------------------------------

    def _get_template_dir(self, template_id: str) -> Path:
        return self.base_path / template_id

    def _validate_identifier(self, value: str, field: str) -> str:
        if not value or not isinstance(value, str):
            raise ValueError(f"{field} 不能为空")
        if any(sep in value for sep in (os.sep, os.altsep) if sep):
            raise ValueError(f"{field} 不能包含路径分隔符")
        if ".." in value:
            raise ValueError(f"{field} 不能包含路径跳转")
        return value.strip()

    def _sanitize_filename(self, filename: str) -> str:
        safe_name = Path(filename).name
        if not safe_name or safe_name in {".", ".."}:
            return self.DEFAULT_FILENAME
        return safe_name

    def _load_manifest(
        self,
        template_id: str,
        ensure_exists: bool = True,
    ) -> Dict[str, Any]:
        template_dir = self._get_template_dir(template_id)
        manifest_path = template_dir / self.MANIFEST_FILENAME
        if manifest_path.exists():
            try:
                with manifest_path.open("r", encoding="utf-8") as fp:
                    data: Dict[str, Any] = json.load(fp)
                    data.setdefault("versions", {})
                    return data
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("无法读取模板 %s 的 manifest: %s", template_id, exc)

        if ensure_exists and not template_dir.exists():
            template_dir.mkdir(parents=True, exist_ok=True)

        return {
            "template_id": template_id,
            "versions": {},
            "created_at": None,
            "updated_at": None,
            "latest_version": None,
        }

    def _write_manifest(self, template_id: str, manifest: Dict[str, Any]) -> None:
        template_dir = self._get_template_dir(template_id)
        manifest_path = template_dir / self.MANIFEST_FILENAME
        payload = json.dumps(manifest, ensure_ascii=False, indent=2)
        self._atomic_write(manifest_path, payload.encode("utf-8"))

    def _write_json(self, path: Path, payload: Dict[str, Any]) -> None:
        data = json.dumps(payload, ensure_ascii=False, indent=2)
        self._atomic_write(path, data.encode("utf-8"))

    def _atomic_write(self, path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(dir=str(path.parent))
        try:
            with os.fdopen(fd, "wb") as tmp_file:
                tmp_file.write(data)
            os.replace(temp_path, path)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    @staticmethod
    def _determine_latest_version(versions: Dict[str, Dict[str, Any]]) -> Optional[str]:
        if not versions:
            return None
        return max(
            versions.items(),
            key=lambda item: item[1].get("saved_at_ts", 0),
        )[0]


