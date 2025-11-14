"""
渲染引擎模块
负责Word、PDF、HTML文档的生成
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

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
    """Word文档渲染器（待实现）"""

    def render(
        self,
        template: Template,
        data: Dict[str, Any],
    ) -> bytes:
        raise NotImplementedError("Word文档渲染功能待实现")

    def supports_format(self, format: str) -> bool:
        return format.lower() == "docx"

    def supports_template(self, template: Template) -> bool:
        return template.format.lower() == "docx"


class PDFRenderer(Renderer):
    """PDF文档渲染器（待实现）"""

    def render(
        self,
        template: Template,
        data: Dict[str, Any],
    ) -> bytes:
        raise NotImplementedError("PDF文档渲染功能待实现")

    def supports_format(self, format: str) -> bool:
        return format.lower() == "pdf"

    def supports_template(self, template: Template) -> bool:
        # 默认要求文本模板（HTML/Jinja），后续可扩展
        return template.format.lower() in TEXT_FORMATS


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

