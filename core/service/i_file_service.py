"""
文件服务抽象接口
定义文件管理的标准接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from fastapi import UploadFile
from datetime import datetime


class IFileService(ABC):
    """
    文件服务抽象接口
    定义文件上传、下载、列表查询、删除等标准接口
    """
    
    @abstractmethod
    async def upload_file(
        self,
        file: UploadFile,
        max_size: int = 50 * 1024 * 1024,  # 50MB
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass

