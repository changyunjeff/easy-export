"""
渲染引擎模块
负责Word、PDF、HTML文档的生成
"""

import logging
from typing import Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class Renderer(ABC):
    """渲染器基类"""
    
    @abstractmethod
    def render(
        self,
        template_content: bytes,
        data: Dict[str, Any],
    ) -> bytes:
        """
        渲染文档
        
        Args:
            template_content: 模板内容（字节）
            data: 数据字典
            
        Returns:
            渲染后的文档内容（字节）
            
        Raises:
            NotImplementedError: 功能未实现
        """
        raise NotImplementedError("渲染功能待实现")
    
    @abstractmethod
    def supports_format(self, format: str) -> bool:
        """
        检查是否支持指定格式
        
        Args:
            format: 格式名称（docx/pdf/html）
            
        Returns:
            是否支持
        """
        raise NotImplementedError("格式支持检查功能待实现")


class DocxRenderer(Renderer):
    """Word文档渲染器"""
    
    def render(
        self,
        template_content: bytes,
        data: Dict[str, Any],
    ) -> bytes:
        """
        渲染Word文档
        
        Args:
            template_content: 模板内容（字节）
            data: 数据字典
            
        Returns:
            渲染后的Word文档内容（字节）
            
        Raises:
            NotImplementedError: 功能未实现
        """
        raise NotImplementedError("Word文档渲染功能待实现")
    
    def supports_format(self, format: str) -> bool:
        """检查是否支持docx格式"""
        return format.lower() == "docx"


class PDFRenderer(Renderer):
    """PDF文档渲染器"""
    
    def render(
        self,
        template_content: bytes,
        data: Dict[str, Any],
    ) -> bytes:
        """
        渲染PDF文档
        
        Args:
            template_content: 模板内容（字节）
            data: 数据字典
            
        Returns:
            渲染后的PDF文档内容（字节）
            
        Raises:
            NotImplementedError: 功能未实现
        """
        raise NotImplementedError("PDF文档渲染功能待实现")
    
    def supports_format(self, format: str) -> bool:
        """检查是否支持pdf格式"""
        return format.lower() == "pdf"


class HTMLRenderer(Renderer):
    """HTML文档渲染器"""
    
    def render(
        self,
        template_content: bytes,
        data: Dict[str, Any],
    ) -> bytes:
        """
        渲染HTML文档
        
        Args:
            template_content: 模板内容（字节）
            data: 数据字典
            
        Returns:
            渲染后的HTML文档内容（字节）
            
        Raises:
            NotImplementedError: 功能未实现
        """
        raise NotImplementedError("HTML文档渲染功能待实现")
    
    def supports_format(self, format: str) -> bool:
        """检查是否支持html格式"""
        return format.lower() == "html"


class RendererFactory:
    """渲染器工厂类"""
    
    _renderers: Dict[str, Renderer] = {}
    
    @classmethod
    def register_renderer(cls, format: str, renderer: Renderer):
        """
        注册渲染器
        
        Args:
            format: 格式名称
            renderer: 渲染器实例
        """
        cls._renderers[format.lower()] = renderer
        logger.info(f"Renderer registered for format: {format}")
    
    @classmethod
    def get_renderer(cls, format: str) -> Renderer:
        """
        获取渲染器
        
        Args:
            format: 格式名称（docx/pdf/html）
            
        Returns:
            渲染器实例
            
        Raises:
            ValueError: 不支持的格式
        """
        format_lower = format.lower()
        if format_lower not in cls._renderers:
            raise ValueError(f"Unsupported format: {format}")
        return cls._renderers[format_lower]
    
    @classmethod
    def create_default_renderers(cls):
        """创建默认渲染器并注册"""
        if "docx" not in cls._renderers:
            cls.register_renderer("docx", DocxRenderer())
        if "pdf" not in cls._renderers:
            cls.register_renderer("pdf", PDFRenderer())
        if "html" not in cls._renderers:
            cls.register_renderer("html", HTMLRenderer())


# 初始化默认渲染器
RendererFactory.create_default_renderers()

