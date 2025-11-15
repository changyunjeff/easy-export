"""
渲染引擎模块
负责Word、PDF、HTML文档的生成
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from jinja2 import Environment, TemplateError

from .template import Template, TEXT_FORMATS

logger = logging.getLogger(__name__)


class Renderer(ABC):
    """渲染器基类"""

    def __init__(self, *, encoding: str = "utf-8") -> None:
        self._encoding = encoding

    @abstractmethod
    def render(
        self,
        template: Template,
        data: Dict[str, Any],
    ) -> bytes:
        """
        渲染文档

        Args:
            template: 模板对象
            data: 数据字典

        Returns:
            渲染后的文档内容（字节）
        """

    @abstractmethod
    def supports_format(self, format: str) -> bool:
        """检查是否支持指定输出格式"""

    def supports_template(self, template: Template) -> bool:
        """
        检查是否支持指定模板

        默认返回 True，子类可按需覆盖。
        """
        return True

    def ensure_template_supported(self, template: Template) -> None:
        """校验模板格式是否受当前渲染器支持"""
        if not self.supports_template(template):
            raise ValueError(
                f"当前渲染器不支持模板格式: {template.format}"
            )


class DocxRenderer(Renderer):
    """Word文档渲染器
    
    使用docxtpl渲染Word模板，支持Jinja2语法。
    """

    def render(
        self,
        template: Template,
        data: Dict[str, Any],
    ) -> bytes:
        """
        渲染Word文档
        
        Args:
            template: Word模板对象（需要是docx格式）
            data: 数据字典
            
        Returns:
            渲染后的Word文档内容（字节）
            
        Raises:
            ValueError: 模板格式不支持或渲染失败
            ImportError: 缺少必要的依赖库
        """
        self.ensure_template_supported(template)
        
        try:
            from docxtpl import DocxTemplate
            from io import BytesIO
        except ImportError as exc:
            raise ImportError(
                "Word文档渲染需要安装docxtpl库。请运行: pip install docxtpl"
            ) from exc
        
        try:
            # 从字节流加载模板
            template_stream = BytesIO(template.content)
            doc = DocxTemplate(template_stream)
            
            # 使用Jinja2语法渲染数据
            doc.render(data)
            
            # 保存到字节流
            output_stream = BytesIO()
            doc.save(output_stream)
            output_stream.seek(0)
            result = output_stream.read()
            
            logger.debug(
                "Word template %s@%s rendered (%d bytes)",
                template.template_id,
                template.version,
                len(result),
            )
            return result
            
        except Exception as exc:
            raise ValueError(f"Word文档渲染失败: {exc}") from exc

    def supports_format(self, format: str) -> bool:
        return format.lower() == "docx"

    def supports_template(self, template: Template) -> bool:
        return template.format.lower() == "docx"


class PDFRenderer(Renderer):
    """PDF文档渲染器
    
    支持两种方式生成PDF：
    1. 文本模板（HTML/Jinja）-> HTML -> PDF（使用weasyprint）
    2. Word模板（docx）-> Word -> PDF（使用docx2pdf）
    """

    def __init__(
        self,
        *,
        encoding: str = "utf-8",
        converter: Optional["Converter"] = None,
    ) -> None:
        super().__init__(encoding=encoding)
        # 延迟导入Converter，避免循环依赖
        if converter is None:
            from .converter import Converter
            converter = Converter()
        self._converter = converter
        self._html_renderer = HTMLRenderer(encoding=encoding)
        self._docx_renderer = DocxRenderer(encoding=encoding)

    def render(
        self,
        template: Template,
        data: Dict[str, Any],
    ) -> bytes:
        """
        渲染PDF文档
        
        根据模板格式选择渲染路径：
        - 文本模板（HTML/Jinja）：渲染为HTML后转换为PDF
        - Word模板（docx）：渲染为Word后转换为PDF
        
        Args:
            template: 模板对象
            data: 数据字典
            
        Returns:
            渲染后的PDF文档内容（字节）
            
        Raises:
            ValueError: 模板格式不支持或渲染失败
        """
        self.ensure_template_supported(template)
        
        try:
            if template.format.lower() in TEXT_FORMATS:
                # 文本模板：先渲染为HTML，再转换为PDF
                html_bytes = self._html_renderer.render(template, data)
                html_str = html_bytes.decode(self._encoding)
                pdf_bytes = self._converter.html_to_pdf(html_str)
                
                logger.debug(
                    "PDF from HTML template %s@%s rendered (%d bytes)",
                    template.template_id,
                    template.version,
                    len(pdf_bytes),
                )
                return pdf_bytes
                
            elif template.format.lower() == "docx":
                # Word模板：先渲染为Word，再转换为PDF
                docx_bytes = self._docx_renderer.render(template, data)
                pdf_bytes = self._converter.docx_to_pdf(docx_bytes)
                
                logger.debug(
                    "PDF from Word template %s@%s rendered (%d bytes)",
                    template.template_id,
                    template.version,
                    len(pdf_bytes),
                )
                return pdf_bytes
                
            else:
                raise ValueError(f"不支持的模板格式: {template.format}")
                
        except Exception as exc:
            raise ValueError(f"PDF文档渲染失败: {exc}") from exc

    def supports_format(self, format: str) -> bool:
        return format.lower() == "pdf"

    def supports_template(self, template: Template) -> bool:
        # 支持文本模板和Word模板
        fmt = template.format.lower()
        return fmt in TEXT_FORMATS or fmt == "docx"


class HTMLRenderer(Renderer):
    """HTML文档渲染器"""

    def __init__(
        self,
        *,
        encoding: str = "utf-8",
        autoescape: bool = True,
    ) -> None:
        super().__init__(encoding=encoding)
        self._env = Environment(autoescape=autoescape)

    def render(
        self,
        template: Template,
        data: Dict[str, Any],
    ) -> bytes:
        self.ensure_template_supported(template)

        try:
            source = template.content.decode(self._encoding)
        except UnicodeDecodeError as exc:
            raise ValueError(
                f"模板内容无法使用 {self._encoding} 解码"
            ) from exc

        try:
            jinja_template = self._env.from_string(source)
            rendered = jinja_template.render(**data)
        except TemplateError as exc:
            raise ValueError(f"HTML渲染失败：{exc}") from exc

        logger.debug(
            "HTML template %s@%s rendered (%d bytes)",
            template.template_id,
            template.version,
            len(rendered),
        )
        return rendered.encode(self._encoding)

    def supports_format(self, format: str) -> bool:
        return format.lower() in {"html", "htm"}

    def supports_template(self, template: Template) -> bool:
        return template.format.lower() in TEXT_FORMATS


class RendererFactory:
    """渲染器工厂类"""

    _renderers: Dict[str, Renderer] = {}

    @classmethod
    def register_renderer(cls, format: str, renderer: Renderer) -> None:
        cls._renderers[format.lower()] = renderer
        logger.info("Renderer registered for format: %s", format)

    @classmethod
    def get_renderer(cls, format: str) -> Renderer:
        format_lower = format.lower()
        if format_lower not in cls._renderers:
            raise ValueError(f"Unsupported format: {format}")
        return cls._renderers[format_lower]

    @classmethod
    def create_default_renderers(cls) -> None:
        if "docx" not in cls._renderers:
            cls.register_renderer("docx", DocxRenderer())
        if "pdf" not in cls._renderers:
            cls.register_renderer("pdf", PDFRenderer())
        if "html" not in cls._renderers and "htm" not in cls._renderers:
            renderer = HTMLRenderer()
            cls.register_renderer("html", renderer)
            cls.register_renderer("htm", renderer)


# 初始化默认渲染器
RendererFactory.create_default_renderers()

