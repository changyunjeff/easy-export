"""
模板存储模块
负责模板文件的存储、版本管理、文件哈希计算等功能
"""

import os
import hashlib
import logging
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from core.config import get_config

logger = logging.getLogger(__name__)


class TemplateStorage:
    """
    模板存储类
    负责模板文件的存储、版本管理、文件哈希计算等
    """
    
    def __init__(self, base_path: Optional[str] = None):
        """
        初始化模板存储
        
        Args:
            base_path: 模板存储基础路径，如果为 None 则从配置中获取
        """
        config = get_config()
        if base_path is None:
            # 从配置中获取模板存储路径，默认为 static/templates
            base_path = getattr(config, "storage", {}).get("template_path", "static/templates")
        
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Template storage initialized at: {self.base_path}")
    
    def save_template(
        self,
        template_id: str,
        version: str,
        file_content: bytes,
    ) -> str:
        """
        保存模板文件
        
        Args:
            template_id: 模板ID
            version: 版本号
            file_content: 文件内容（字节）
            
        Returns:
            保存的文件路径
            
        Raises:
            NotImplementedError: 功能未实现
        """
        raise NotImplementedError("模板保存功能待实现")
    
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
            NotImplementedError: 功能未实现
            FileNotFoundError: 模板文件不存在
        """
        raise NotImplementedError("模板获取功能待实现")
    
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
            
        Raises:
            NotImplementedError: 功能未实现
        """
        raise NotImplementedError("模板删除功能待实现")
    
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
            
        Raises:
            NotImplementedError: 功能未实现
        """
        raise NotImplementedError("版本列表功能待实现")
    
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
        """
        template_dir = self.base_path / template_id
        if version:
            return template_dir / f"{version}.docx"  # 默认格式，实际应从元数据获取
        # 如果没有指定版本，返回最新版本路径（需要从元数据获取）
        return template_dir / "latest"
    
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
        path = self.get_template_path(template_id, version)
        return path.exists() and path.is_file()

