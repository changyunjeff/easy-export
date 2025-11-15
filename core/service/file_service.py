"""
文件服务模块
负责文件上传、下载、管理
"""

import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import UploadFile

from core.storage import FileStorage
from core.service.i_file_service import IFileService

logger = logging.getLogger(__name__)


class FileService(IFileService):
    """
    文件服务类
    负责文件上传、下载、管理等
    """
    
    # 默认配置
    DEFAULT_MAX_SIZE = 50 * 1024 * 1024  # 50MB
    ALLOWED_EXTENSIONS = {
        '.pdf', '.docx', '.doc', '.html', '.htm',
        '.png', '.jpg', '.jpeg', '.gif', '.webp',
        '.txt', '.json', '.xml', '.csv',
    }
    
    def __init__(self, file_storage: Optional[FileStorage] = None):
        """
        初始化文件服务
        
        Args:
            file_storage: 文件存储实例，如果为 None 则创建新实例
        """
        self.file_storage = file_storage or FileStorage()
        logger.info("File service initialized")
    
    async def upload_file(
        self,
        file: UploadFile,
        max_size: int = DEFAULT_MAX_SIZE,
    ) -> Dict[str, Any]:
        """
        上传文件
        
        Args:
            file: 上传的文件
            max_size: 最大文件大小（字节），默认50MB
            
        Returns:
            文件信息（file_id, file_path, file_size, file_url等）
            
        Raises:
            ValueError: 文件大小超限或验证失败
            RuntimeError: 上传失败
        """
        # 验证文件
        if not file.filename:
            raise ValueError("文件名不能为空")
        
        # 读取文件内容
        content = await file.read()
        file_size = len(content)
        
        # 验证文件大小
        if file_size == 0:
            raise ValueError("文件不能为空")
        if file_size > max_size:
            raise ValueError(
                f"文件大小 {file_size} 字节超过限制 {max_size} 字节 "
                f"({max_size / 1024 / 1024:.1f}MB)"
            )
        
        # 验证文件扩展名
        file_ext = Path(file.filename).suffix.lower()
        if file_ext and file_ext not in self.ALLOWED_EXTENSIONS:
            logger.warning(
                "文件扩展名 %s 不在允许列表中，但仍允许上传",
                file_ext
            )
        
        # 生成文件ID
        file_id = self._generate_file_id(file.filename)
        
        # 保存文件
        try:
            file_path = self.file_storage.save_file(
                file_id=file_id,
                content=content,
                filename=file.filename,
            )
            logger.info("文件 %s 上传成功: %s (%d 字节)", file.filename, file_id, file_size)
        except Exception as exc:
            logger.error("文件上传失败: %s", exc, exc_info=True)
            raise RuntimeError(f"文件上传失败: {exc}") from exc
        
        # 返回文件信息
        return {
            "file_id": file_id,
            "file_name": file.filename,
            "file_path": file_path,
            "file_size": file_size,
            "file_url": self.file_storage.get_file_url(file_id),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
    
    def download_file(
        self,
        file_id: str,
    ) -> bytes:
        """
        下载文件
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件内容（字节）
            
        Raises:
            FileNotFoundError: 文件不存在
        """
        logger.debug("下载文件: %s", file_id)
        try:
            return self.file_storage.get_file(file_id)
        except FileNotFoundError:
            logger.error("文件不存在: %s", file_id)
            raise
    
    def get_file_info(
        self,
        file_id: str,
    ) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件信息（file_id, file_name, file_size, created_at等）
            
        Raises:
            FileNotFoundError: 文件不存在
        """
        file_path = self.file_storage.get_file_path(file_id)
        if not file_path.exists():
            raise FileNotFoundError(f"文件不存在: {file_id}")
        
        # 读取元数据
        metadata = self.file_storage._load_metadata(file_path)
        
        # 获取文件统计信息
        stat = file_path.stat()
        
        return {
            "file_id": file_id,
            "file_name": metadata.get("download_name", file_id),
            "file_size": metadata.get("file_size", stat.st_size),
            "file_url": self.file_storage.get_file_url(file_id),
            "hash": metadata.get("hash", ""),
            "created_at": metadata.get("saved_at", ""),
        }
    
    def list_files(
        self,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        文件列表查询
        
        Args:
            filters: 筛选条件（name, extension, created_after等）
            page: 页码
            page_size: 每页数量
            
        Returns:
            分页结果（包含total, page, page_size, items）
        """
        filters = filters or {}
        
        # 获取所有文件
        all_files = []
        for file_path in self.file_storage.base_path.iterdir():
            # 跳过元数据文件和目录
            if not file_path.is_file() or file_path.name.endswith(
                self.file_storage.METADATA_SUFFIX
            ):
                continue
            
            # 读取文件信息
            try:
                file_id = file_path.name
                metadata = self.file_storage._load_metadata(file_path)
                stat = file_path.stat()
                
                file_info = {
                    "file_id": file_id,
                    "file_name": metadata.get("download_name", file_id),
                    "file_size": metadata.get("file_size", stat.st_size),
                    "file_url": self.file_storage.get_file_url(file_id),
                    "created_at": metadata.get("saved_at", ""),
                }
                
                # 应用过滤器
                if self._match_filters(file_info, filters):
                    all_files.append(file_info)
            except Exception as exc:
                logger.warning("无法读取文件信息: %s - %s", file_path.name, exc)
                continue
        
        # 排序（按创建时间降序）
        all_files.sort(
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )
        
        # 分页
        total = len(all_files)
        start = (page - 1) * page_size
        end = start + page_size
        items = all_files[start:end]
        
        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": items,
        }
    
    def delete_file(
        self,
        file_id: str,
    ) -> bool:
        """
        删除文件
        
        Args:
            file_id: 文件ID
            
        Returns:
            是否删除成功
            
        Raises:
            FileNotFoundError: 文件不存在
        """
        # 检查文件是否存在
        if not self.file_storage.exists(file_id):
            raise FileNotFoundError(f"文件不存在: {file_id}")
        
        # 删除文件
        result = self.file_storage.delete_file(file_id)
        if result:
            logger.info("文件已删除: %s", file_id)
        return result
    
    def cleanup_old_files(
        self,
        older_than: datetime,
    ) -> int:
        """
        清理过期文件
        
        Args:
            older_than: 删除早于此时间的文件
            
        Returns:
            清理的文件数量
        """
        logger.info("开始清理早于 %s 的文件", older_than.isoformat())
        count = self.file_storage.cleanup_temp_files(older_than)
        logger.info("已清理 %d 个文件", count)
        return count
    
    def get_file_url(
        self,
        file_id: str,
    ) -> str:
        """
        获取文件访问URL
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件访问URL
            
        Raises:
            FileNotFoundError: 文件不存在
        """
        # 检查文件是否存在
        if not self.file_storage.exists(file_id):
            raise FileNotFoundError(f"文件不存在: {file_id}")
        
        return self.file_storage.get_file_url(file_id)
    
    def exists(
        self,
        file_id: str,
    ) -> bool:
        """
        检查文件是否存在
        
        Args:
            file_id: 文件ID
            
        Returns:
            文件是否存在
        """
        return self.file_storage.exists(file_id)
    
    # ------------------------------------------------------------------
    # 私有方法
    # ------------------------------------------------------------------
    
    def _generate_file_id(self, filename: str) -> str:
        """
        生成文件ID
        
        Args:
            filename: 原始文件名
            
        Returns:
            文件ID（格式：uuid_filename）
        """
        # 提取文件扩展名
        file_ext = Path(filename).suffix.lower()
        
        # 生成UUID
        unique_id = uuid.uuid4().hex[:12]
        
        # 组合文件ID
        if file_ext:
            return f"{unique_id}{file_ext}"
        return unique_id
    
    def _match_filters(
        self,
        file_info: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> bool:
        """
        检查文件是否匹配过滤条件
        
        Args:
            file_info: 文件信息
            filters: 过滤条件
            
        Returns:
            是否匹配
        """
        # 文件名过滤
        if "name" in filters:
            name_filter = filters["name"].lower()
            file_name = file_info.get("file_name", "").lower()
            if name_filter not in file_name:
                return False
        
        # 扩展名过滤
        if "extension" in filters:
            ext_filter = filters["extension"].lower()
            if not ext_filter.startswith("."):
                ext_filter = f".{ext_filter}"
            file_name = file_info.get("file_name", "")
            file_ext = Path(file_name).suffix.lower()
            if file_ext != ext_filter:
                return False
        
        # 创建时间过滤
        if "created_after" in filters:
            created_after = filters["created_after"]
            created_at = file_info.get("created_at", "")
            if created_at and created_at < created_after:
                return False
        
        return True

