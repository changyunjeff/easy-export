"""
模板服务模块
负责模板CRUD操作、模板版本管理、模板元数据管理
"""

import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path
from fastapi import UploadFile
import uuid

from core.models.template import Template, TemplateVersion
from core.storage import TemplateStorage
from core.service.i_template_service import ITemplateService

logger = logging.getLogger(__name__)


class TemplateService(ITemplateService):
    """
    模板服务类
    负责模板CRUD操作、模板版本管理等
    """
    
    # 支持的文件格式
    SUPPORTED_FORMATS = {".docx", ".html", ".htm"}
    
    # 最大文件大小：50MB
    MAX_FILE_SIZE = 50 * 1024 * 1024
    
    def __init__(self, template_storage: Optional[TemplateStorage] = None):
        """
        初始化模板服务
        
        Args:
            template_storage: 模板存储实例，如果为 None 则创建新实例
        """
        self.template_storage = template_storage or TemplateStorage()
        logger.info("Template service initialized")
    
    async def create_template(
        self,
        file: UploadFile,
        metadata: Dict[str, Any],
    ) -> Template:
        """
        创建模板
        
        Args:
            file: 上传的文件
            metadata: 模板元数据（name, description, tags, version等）
            
        Returns:
            模板对象
            
        Raises:
            ValueError: 参数验证失败
            FileNotFoundError: 文件不存在
            RuntimeError: 创建失败
        """
        # 验证必填字段
        name = metadata.get("name")
        if not name:
            raise ValueError("模板名称不能为空")
        
        # 验证文件格式
        if not file.filename:
            raise ValueError("文件名不能为空")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"不支持的文件格式: {file_ext}，"
                f"支持的格式: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 验证文件大小
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"文件大小超过限制: {file_size} bytes，"
                f"最大允许: {self.MAX_FILE_SIZE} bytes"
            )
        
        # 生成模板ID
        template_id = metadata.get("template_id") or f"tpl_{uuid.uuid4().hex[:12]}"
        version = metadata.get("version", "1.0.0")
        
        # 保存模板文件
        try:
            file_path = self.template_storage.save_template(
                template_id=template_id,
                version=version,
                file_content=file_content,
                filename=file.filename,
            )
        except Exception as e:
            logger.error("Failed to save template: %s", e)
            raise RuntimeError(f"保存模板失败: {e}")
        
        # 保存模板元数据到manifest
        file_hash = self.calculate_file_hash(file_content)
        now = datetime.now()
        
        manifest = self.template_storage._load_manifest(template_id)
        manifest.update({
            "name": name,
            "description": metadata.get("description", ""),
            "tags": metadata.get("tags", []),
            "format": file_ext.lstrip("."),
            "created_by": metadata.get("created_by"),
        })
        self.template_storage._write_manifest(template_id, manifest)
        
        # 构造返回对象
        template = Template(
            template_id=template_id,
            name=name,
            description=metadata.get("description"),
            format=file_ext.lstrip("."),
            version=version,
            file_size=file_size,
            hash=file_hash,
            tags=metadata.get("tags", []),
            created_at=now,
            updated_at=now,
            created_by=metadata.get("created_by"),
        )
        
        logger.info("Template created: %s@%s", template_id, version)
        return template
    
    def get_template(
        self,
        template_id: str,
        version: Optional[str] = None,
    ) -> Template:
        """
        获取模板
        
        Args:
            template_id: 模板ID
            version: 版本号，如果为 None 则返回最新版本
            
        Returns:
            模板对象
            
        Raises:
            FileNotFoundError: 模板不存在
        """
        # 加载manifest
        manifest = self.template_storage._load_manifest(template_id)
        if not manifest:
            raise FileNotFoundError(f"模板不存在: {template_id}")
        
        # 确定版本号
        target_version = version or manifest.get("latest_version")
        if not target_version:
            raise FileNotFoundError(f"模板 {template_id} 没有可用版本")
        
        # 获取版本信息
        versions = manifest.get("versions", {})
        version_info = versions.get(target_version)
        if not version_info:
            raise FileNotFoundError(
                f"模板版本不存在: {template_id}@{target_version}"
            )
        
        # 构造返回对象
        # 处理datetime字段 - 可能是字符串或datetime对象
        created_at = manifest.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif not isinstance(created_at, datetime):
            created_at = datetime.now()
            
        updated_at = manifest.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif not isinstance(updated_at, datetime):
            updated_at = datetime.now()
        
        template = Template(
            template_id=template_id,
            name=manifest.get("name", template_id),
            description=manifest.get("description"),
            format=manifest.get("format", "unknown"),
            version=target_version,
            file_size=version_info.get("file_size", 0),
            hash=version_info.get("hash", ""),
            tags=manifest.get("tags", []),
            created_at=created_at,
            updated_at=updated_at,
            created_by=manifest.get("created_by"),
        )
        
        return template
    
    def list_templates(
        self,
        filters: Dict[str, Any],
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        列表查询模板
        
        Args:
            filters: 筛选条件（name, tags, format等）
            page: 页码
            page_size: 每页数量
            
        Returns:
            分页结果（包含total, page, page_size, items）
        """
        # 获取所有模板
        all_templates = self.template_storage.list_templates()
        
        # 过滤
        name_filter = filters.get("name", "").lower()
        tags_filter = set(filters.get("tags", []))
        format_filter = filters.get("format", "").lower()
        
        filtered_templates = []
        for template_id in all_templates:
            try:
                manifest = self.template_storage._load_manifest(template_id)
                if not manifest:
                    continue
                
                # 名称过滤
                if name_filter:
                    template_name = manifest.get("name", "").lower()
                    if name_filter not in template_name:
                        continue
                
                # 标签过滤
                if tags_filter:
                    template_tags = set(manifest.get("tags", []))
                    if not tags_filter.intersection(template_tags):
                        continue
                
                # 格式过滤
                if format_filter:
                    template_format = manifest.get("format", "").lower()
                    if format_filter != template_format:
                        continue
                
                # 获取最新版本信息
                latest_version = manifest.get("latest_version")
                version_info = manifest.get("versions", {}).get(latest_version, {})
                
                filtered_templates.append({
                    "template_id": template_id,
                    "name": manifest.get("name", template_id),
                    "description": manifest.get("description", ""),
                    "format": manifest.get("format", "unknown"),
                    "latest_version": latest_version,
                    "file_size": version_info.get("file_size", 0),
                    "tags": manifest.get("tags", []),
                    "created_at": manifest.get("created_at"),
                    "updated_at": manifest.get("updated_at"),
                })
            except Exception as e:
                logger.warning("Failed to load template %s: %s", template_id, e)
                continue
        
        # 分页
        total = len(filtered_templates)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        items = filtered_templates[start_idx:end_idx]
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
    
    def update_template(
        self,
        template_id: str,
        metadata: Dict[str, Any],
    ) -> Template:
        """
        更新模板元数据
        
        Args:
            template_id: 模板ID
            metadata: 要更新的元数据
            
        Returns:
            更新后的模板对象
            
        Raises:
            FileNotFoundError: 模板不存在
        """
        # 加载manifest
        manifest = self.template_storage._load_manifest(template_id)
        if not manifest:
            raise FileNotFoundError(f"模板不存在: {template_id}")
        
        # 更新元数据
        if "name" in metadata:
            manifest["name"] = metadata["name"]
        if "description" in metadata:
            manifest["description"] = metadata["description"]
        if "tags" in metadata:
            manifest["tags"] = metadata["tags"]
        
        manifest["updated_at"] = datetime.now().isoformat()
        
        # 保存manifest
        self.template_storage._write_manifest(template_id, manifest)
        
        # 返回更新后的模板对象
        return self.get_template(template_id)
    
    def delete_template(
        self,
        template_id: str,
        version: Optional[str] = None,
    ) -> bool:
        """
        删除模板
        
        Args:
            template_id: 模板ID
            version: 版本号，如果为 None 则删除所有版本
            
        Returns:
            是否删除成功
            
        Raises:
            FileNotFoundError: 模板不存在
        """
        try:
            result = self.template_storage.delete_template(template_id, version)
            # 如果删除失败（返回False），说明模板不存在
            if not result:
                raise FileNotFoundError(f"模板不存在: {template_id}")
            return result
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error("Failed to delete template %s: %s", template_id, e)
            return False
    
    async def create_version(
        self,
        template_id: str,
        file: UploadFile,
        version: str,
        changelog: str,
    ) -> TemplateVersion:
        """
        创建新版本
        
        Args:
            template_id: 模板ID
            file: 上传的文件
            version: 版本号
            changelog: 更新日志
            
        Returns:
            模板版本对象
            
        Raises:
            FileNotFoundError: 模板不存在
            ValueError: 版本号已存在
        """
        # 验证模板是否存在
        template_dir = self.template_storage._get_template_dir(template_id)
        manifest_path = template_dir / self.template_storage.MANIFEST_FILENAME
        if not manifest_path.exists():
            raise FileNotFoundError(f"模板不存在: {template_id}")
        
        manifest = self.template_storage._load_manifest(template_id)
        
        # 验证版本号是否已存在
        versions = manifest.get("versions", {})
        if version in versions:
            raise ValueError(f"版本号已存在: {version}")
        
        # 验证文件格式
        if not file.filename:
            raise ValueError("文件名不能为空")
        
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"不支持的文件格式: {file_ext}，"
                f"支持的格式: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        # 验证文件大小
        if file_size > self.MAX_FILE_SIZE:
            raise ValueError(
                f"文件大小超过限制: {file_size} bytes，"
                f"最大允许: {self.MAX_FILE_SIZE} bytes"
            )
        
        # 保存模板文件
        try:
            file_path = self.template_storage.save_template(
                template_id=template_id,
                version=version,
                file_content=file_content,
                filename=file.filename,
            )
        except Exception as e:
            logger.error("Failed to save template version: %s", e)
            raise RuntimeError(f"保存模板版本失败: {e}")
        
        # 计算文件哈希
        file_hash = self.calculate_file_hash(file_content)
        now = datetime.now()
        
        # 构造返回对象
        template_version = TemplateVersion(
            template_id=template_id,
            version=version,
            file_size=file_size,
            hash=file_hash,
            created_at=now,
            changelog=changelog,
        )
        
        logger.info("Template version created: %s@%s", template_id, version)
        return template_version
    
    def list_versions(
        self,
        template_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        查询模板版本列表
        
        Args:
            template_id: 模板ID
            page: 页码
            page_size: 每页数量
            
        Returns:
            分页结果（包含total, page, page_size, items）
            
        Raises:
            FileNotFoundError: 模板不存在
        """
        # 加载manifest
        manifest = self.template_storage._load_manifest(template_id)
        if not manifest:
            raise FileNotFoundError(f"模板不存在: {template_id}")
        
        # 获取所有版本
        versions = manifest.get("versions", {})
        version_list = []
        
        for ver, ver_info in versions.items():
            version_list.append({
                "version": ver,
                "file_size": ver_info.get("file_size", 0),
                "hash": ver_info.get("hash", ""),
                "created_at": ver_info.get("saved_at"),
                "changelog": ver_info.get("changelog", ""),
            })
        
        # 按创建时间倒序排序
        version_list.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        
        # 分页
        total = len(version_list)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        items = version_list[start_idx:end_idx]
        
        return {
            "template_id": template_id,
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
    
    def download_template(
        self,
        template_id: str,
        version: Optional[str] = None,
    ) -> bytes:
        """
        下载模板文件
        
        Args:
            template_id: 模板ID
            version: 版本号，如果为 None 则下载最新版本
            
        Returns:
            文件内容（字节）
            
        Raises:
            FileNotFoundError: 模板不存在
        """
        return self.template_storage.get_template(template_id, version)
    
    def calculate_file_hash(self, content: bytes) -> str:
        """
        计算文件哈希值
        
        Args:
            content: 文件内容
            
        Returns:
            哈希值（SHA-256）
        """
        return self.template_storage.calculate_hash(content)
