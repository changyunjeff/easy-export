"""
文件存储模块
负责输出文件的存储、URL 生成及临时文件清理等功能
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from core.config import get_config

logger = logging.getLogger(__name__)


class FileStorage:
    """
    文件存储类
    支持输出文件的落盘、访问 URL 生成以及过期文件清理
    """

    METADATA_SUFFIX = ".metadata.json"
    DEFAULT_DOWNLOAD_NAME = "export.bin"
    DEFAULT_URL_PREFIX = "/static/outputs"

    def __init__(self, base_path: Optional[str] = None):
        """
        初始化文件存储

        Args:
            base_path: 文件存储基础路径，如果为 None 则从配置中获取
        """
        config = get_config()
        storage_cfg = getattr(config, "storage", {}) or {}
        if base_path is None:
            base_path = storage_cfg.get("output_path", "static/outputs")

        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

        prefix = storage_cfg.get("output_url_prefix")
        if prefix:
            prefix = prefix.strip()
            if prefix.startswith(("http://", "https://")):
                self.url_prefix = prefix.rstrip("/")
            else:
                if not prefix.startswith("/"):
                    prefix = f"/{prefix}"
                self.url_prefix = prefix.rstrip("/") or "/"
        else:
            self.url_prefix = self.DEFAULT_URL_PREFIX

        logger.info("File storage initialized at: %s", self.base_path)

    def save_file(
        self,
        file_id: str,
        content: bytes,
        filename: Optional[str] = None,
    ) -> str:
        """
        保存文件

        Args:
            file_id: 文件ID（将作为存储文件名，禁止包含路径分隔符）
            content: 文件内容（字节）
            filename: 原始文件名（可选，用于记录下载名称）

        Returns:
            保存的文件路径
        """
        file_id = self._validate_file_id(file_id)
        if not isinstance(content, (bytes, bytearray)):
            raise ValueError("content 必须是 bytes 或 bytearray")

        data = bytes(content)
        file_path = self.get_file_path(file_id)
        self._atomic_write(file_path, data)

        metadata = self._build_metadata(file_id, file_path, data, filename)
        self._write_json(self._metadata_path(file_path), metadata)
        logger.debug("File %s saved (%d bytes) -> %s", file_id, metadata["file_size"], file_path)
        return str(file_path)

    def get_file(self, file_id: str) -> bytes:
        """
        获取文件内容

        Args:
            file_id: 文件ID

        Returns:
            文件内容（字节）

        Raises:
            FileNotFoundError: 文件不存在
        """
        file_id = self._validate_file_id(file_id)
        file_path = self.get_file_path(file_id)
        if not file_path.exists() or not file_path.is_file():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        return file_path.read_bytes()

    def delete_file(self, file_id: str) -> bool:
        """
        删除文件及其元数据

        Args:
            file_id: 文件ID

        Returns:
            是否删除成功
        """
        file_id = self._validate_file_id(file_id)
        file_path = self.get_file_path(file_id)
        removed = False
        if file_path.exists():
            file_path.unlink()
            removed = True

        metadata_path = self._metadata_path(file_path)
        if metadata_path.exists():
            metadata_path.unlink()

        return removed

    def get_file_url(self, file_id: str) -> str:
        """
        获取文件访问URL

        Args:
            file_id: 文件ID

        Returns:
            文件访问URL（相对或绝对路径，取决于配置）
        """
        file_id = self._validate_file_id(file_id)
        prefix = self.url_prefix.rstrip("/")
        suffix = file_id.lstrip("/")

        if prefix.startswith(("http://", "https://")):
            return f"{prefix}/{suffix}"

        if not prefix:
            return f"/{suffix}"

        if prefix.startswith("/"):
            return f"{prefix}/{suffix}"

        return f"/{prefix}/{suffix}"

    def cleanup_temp_files(self, older_than: datetime) -> int:
        """
        清理早于指定时间的文件及其元数据

        Args:
            older_than: 删除早于此 UTC 时间的文件

        Returns:
            清理的文件数量
        """
        cutoff = self._normalize_datetime(older_than)
        removed = 0

        for entry in self.base_path.iterdir():
            if not entry.is_file() or entry.name.endswith(self.METADATA_SUFFIX):
                continue

            saved_at = self._get_saved_at(entry)
            if saved_at < cutoff:
                try:
                    entry.unlink(missing_ok=True)
                    removed += 1
                except OSError as exc:
                    logger.warning("无法删除文件 %s: %s", entry, exc)
                finally:
                    meta_path = self._metadata_path(entry)
                    if meta_path.exists():
                        meta_path.unlink(missing_ok=True)

        return removed

    def get_file_path(self, file_id: str) -> Path:
        """
        获取文件路径（不验证文件是否存在）

        Args:
            file_id: 文件ID

        Returns:
            文件路径
        """
        file_id = self._validate_file_id(file_id)
        return self.base_path / file_id

    def exists(self, file_id: str) -> bool:
        """
        检查文件是否存在

        Args:
            file_id: 文件ID

        Returns:
            文件是否存在
        """
        file_id = self._validate_file_id(file_id)
        path = self.get_file_path(file_id)
        return path.exists() and path.is_file()

    # ------------------------------------------------------------------
    # 内部工具方法
    # ------------------------------------------------------------------

    def _build_metadata(
        self,
        file_id: str,
        file_path: Path,
        data: bytes,
        filename: Optional[str],
    ) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        download_name = self._sanitize_filename(filename) if filename else file_path.name
        if not download_name:
            download_name = self.DEFAULT_DOWNLOAD_NAME

        return {
            "file_id": file_id,
            "storage_name": file_path.name,
            "download_name": download_name,
            "file_size": len(data),
            "hash": self._calculate_hash(data),
            "saved_at": now.isoformat(),
            "saved_at_ts": now.timestamp(),
            "relative_path": file_id,
            "file_url": self.get_file_url(file_id),
        }

    def _metadata_path(self, file_path: Path) -> Path:
        return file_path.parent / f"{file_path.name}{self.METADATA_SUFFIX}"

    def _get_saved_at(self, file_path: Path) -> datetime:
        metadata = self._load_metadata(file_path)
        timestamp = metadata.get("saved_at_ts")
        if timestamp:
            return datetime.fromtimestamp(float(timestamp), tz=timezone.utc)

        saved_at = metadata.get("saved_at")
        if saved_at:
            try:
                return datetime.fromisoformat(saved_at)
            except ValueError:
                logger.warning("无法解析文件 %s 的 saved_at 字段：%s", file_path.name, saved_at)

        stat = file_path.stat()
        return datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

    def _load_metadata(self, file_path: Path) -> Dict[str, Any]:
        meta_path = self._metadata_path(file_path)
        if meta_path.exists():
            try:
                with meta_path.open("r", encoding="utf-8") as fp:
                    return json.load(fp)
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("无法读取文件 %s 的元数据: %s", file_path.name, exc)
        return {}

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

    def _calculate_hash(self, data: bytes) -> str:
        hash_obj = hashlib.sha256(data)
        return f"sha256:{hash_obj.hexdigest()}"

    def _sanitize_filename(self, filename: Optional[str]) -> str:
        if not filename:
            return ""
        safe_name = Path(filename).name.strip()
        if not safe_name or safe_name in {".", ".."}:
            return ""
        return safe_name

    def _validate_file_id(self, value: str) -> str:
        if not value or not isinstance(value, str):
            raise ValueError("file_id 不能为空")
        if value in {".", ".."}:
            raise ValueError("file_id 非法")
        if value != value.strip():
            raise ValueError("file_id 不能包含首尾空白字符")
        if any(sep and sep in value for sep in (os.sep, os.altsep)):
            raise ValueError("file_id 不能包含路径分隔符")
        return value

    def _normalize_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

