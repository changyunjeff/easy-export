"""
模板服务抽象接口
定义模板管理的标准接口
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from fastapi import UploadFile

from core.models.template import Template, TemplateVersion


class ITemplateService(ABC):
    """
    模板服务抽象接口
    定义模板CRUD操作、版本管理等标准接口
    """
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    def calculate_file_hash(self, content: bytes) -> str:
        """
        计算文件哈希值
        
        Args:
            content: 文件内容
            
        Returns:
            哈希值（SHA-256）
        """
        pass

