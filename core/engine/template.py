"""
模板引擎模块
负责模板加载、占位符解析、模板验证等功能
"""

from __future__ import annotations

import io
import logging
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set

from jinja2 import Environment, Template as JinjaTemplate, TemplateError

from core.storage import TemplateStorage

logger = logging.getLogger(__name__)


PLACEHOLDER_PATTERN = re.compile(r"{{\s*(.+?)\s*}}", re.DOTALL)
SUPPORTED_SPECIAL_TYPES = {"table", "image", "chart"}
TEXT_FORMATS = {"html", "htm", "jinja", "j2", "txt"}


@dataclass
class Placeholder:
    """占位符基类"""

    name: str
    placeholder_type: str
    raw_text: str


@dataclass
class TextPlaceholder(Placeholder):
    """文本占位符"""

    filters: Optional[List[str]] = None


@dataclass
class TablePlaceholder(Placeholder):
    """表格占位符"""

    config: Optional[Dict[str, Any]] = None


@dataclass
class ImagePlaceholder(Placeholder):
    """图片占位符"""

    config: Optional[Dict[str, Any]] = None


@dataclass
class ChartPlaceholder(Placeholder):
    """图表占位符"""

    chart_type: Optional[str] = None


@dataclass
class Template:
    """模板类"""

    template_id: str
    version: str
    format: str
    content: bytes
    placeholders: Optional[List[Placeholder]] = None


@dataclass
class ValidationResult:
    """验证结果类"""

    valid: bool
    errors: List[str]
    warnings: List[str]


class TemplateEngine:
    """
    模板引擎类
    负责模板加载、占位符解析、模板验证等
    """

    def __init__(
        self,
        template_storage: Optional[TemplateStorage] = None,
        *,
        autoescape: bool = True,
        encoding: str = "utf-8",
    ) -> None:
        self._storage = template_storage or TemplateStorage()
        self._encoding = encoding
        self._env = Environment(autoescape=autoescape)
        logger.info("Template engine initialized (autoescape=%s)", autoescape)

    def load_template(
        self,
        template_id: str,
        version: Optional[str] = None,
    ) -> Template:
        """
        加载模板并解析占位符

        Args:
            template_id: 模板ID
            version: 版本号，如果为 None 则加载最新版本

        Returns:
            模板对象

        Raises:
            FileNotFoundError: 模板文件不存在
            ValueError: 模板ID非法
        """
        self._ensure_identifier(template_id, "template_id")

        template_path = self._storage.get_template_path(template_id, version)
        resolved_version = self._resolve_version(template_id, template_path, fallback=version)
        content = template_path.read_bytes()
        template_format = self._detect_format(template_path)

        template = Template(
            template_id=template_id,
            version=resolved_version,
            format=template_format,
            content=content,
            placeholders=[],
        )
        placeholders = self.parse_placeholders(template)
        template.placeholders = placeholders

        logger.debug(
            "Template %s@%s loaded (%s) with %d placeholders",
            template_id,
            resolved_version,
            template_format,
            len(placeholders),
        )
        return template

    def parse_placeholders(self, template: Template) -> List[Placeholder]:
        """
        解析模板中的占位符

        Args:
            template: 模板对象

        Returns:
            占位符列表
        """
        raw_text = self._extract_template_text(template)
        if not raw_text:
            logger.debug("Template %s 没有可解析的文本内容", template.template_id)
            return []

        placeholders: List[Placeholder] = []
        seen: Set[Tuple[str, str]] = set()
        for match in PLACEHOLDER_PATTERN.finditer(raw_text):
            raw_placeholder = match.group(0)
            expression = match.group(1).strip()
            if not expression:
                continue

            placeholder = self._build_placeholder(expression, raw_placeholder)
            if placeholder is None:
                continue

            key = (placeholder.placeholder_type, placeholder.name)
            if key in seen:
                continue

            seen.add(key)
            placeholders.append(placeholder)

        logger.debug(
            "Parsed %d placeholders from template %s@%s",
            len(placeholders),
            template.template_id,
            template.version,
        )
        return placeholders

    def validate_template(self, template: Template) -> ValidationResult:
        """
        验证模板占位符定义

        Args:
            template: 模板对象

        Returns:
            验证结果
        """
        errors: List[str] = []
        warnings: List[str] = []

        placeholders = template.placeholders or []
        if not placeholders:
            warnings.append("模板中未检测到占位符")

        for placeholder in placeholders:
            if not placeholder.name:
                errors.append(f"{placeholder.raw_text} 缺少占位符名称")
            if placeholder.placeholder_type not in {"text", "table", "image", "chart"}:
                errors.append(
                    f"{placeholder.raw_text} 包含不支持的占位符类型 {placeholder.placeholder_type}"
                )

        return ValidationResult(valid=not errors, errors=errors, warnings=warnings)

    def render(
        self,
        template: Template,
        data: Dict[str, Any],
    ) -> str:
        """
        渲染文本模板（HTML/Jinja）

        Args:
            template: 模板对象
            data: 数据字典

        Returns:
            渲染后的文本

        Raises:
            ValueError: 模板格式不支持
            TemplateError: 渲染失败
        """
        if template.format.lower() not in TEXT_FORMATS:
            raise ValueError(f"当前模板格式 {template.format} 暂不支持直接渲染，请使用渲染引擎")

        try:
            text = template.content.decode(self._encoding)
        except UnicodeDecodeError as exc:
            raise ValueError(f"模板内容无法使用 {self._encoding} 解码") from exc

        try:
            jinja_template: JinjaTemplate = self._env.from_string(text)
            rendered = jinja_template.render(**data)
            return rendered
        except TemplateError as exc:
            logger.error(
                "Render template %s@%s failed: %s",
                template.template_id,
                template.version,
                exc,
            )
            raise

    # ------------------------------------------------------------------
    # 内部工具方法
    # ------------------------------------------------------------------

    def _build_placeholder(self, expression: str, raw: str) -> Optional[Placeholder]:
        placeholder_type = "text"
        source = expression
        chart_type: Optional[str] = None

        prefix, remainder = self._extract_prefix(expression)
        if prefix in SUPPORTED_SPECIAL_TYPES:
            placeholder_type = prefix
            source = remainder.strip()

        name, filters = self._split_filters(source)
        if not name:
            return None

        if placeholder_type == "text":
            return TextPlaceholder(name=name, raw_text=raw, placeholder_type="text", filters=filters)

        if placeholder_type == "table":
            config = {"filters": filters} if filters else {}
            return TablePlaceholder(
                name=name,
                raw_text=raw,
                placeholder_type="table",
                config=config or None,
            )

        if placeholder_type == "image":
            config = {"filters": filters} if filters else {}
            return ImagePlaceholder(
                name=name,
                raw_text=raw,
                placeholder_type="image",
                config=config or None,
            )

        if placeholder_type == "chart":
            chart_type = name if name else None
            return ChartPlaceholder(
                name=name,
                raw_text=raw,
                placeholder_type="chart",
                chart_type=chart_type,
            )

        return TextPlaceholder(name=name, raw_text=raw, placeholder_type="text", filters=filters)

    def _extract_prefix(self, expression: str) -> Tuple[str, str]:
        if ":" not in expression:
            return ("text", expression)
        prefix, remainder = expression.split(":", 1)
        normalized_prefix = prefix.strip().lower()
        if normalized_prefix in SUPPORTED_SPECIAL_TYPES:
            return (normalized_prefix, remainder)
        return ("text", expression)

    def _split_filters(self, expression: str) -> Tuple[str, List[str]]:
        if "|" not in expression:
            return expression.strip(), []

        segments = [segment.strip() for segment in expression.split("|")]
        base = segments[0]
        filters = [segment for segment in segments[1:] if segment]
        return base, filters

    def _extract_template_text(self, template: Template) -> str:
        template_format = template.format.lower()
        if template_format in TEXT_FORMATS:
            try:
                return template.content.decode(self._encoding)
            except UnicodeDecodeError:
                logger.warning(
                    "模板 %s@%s 使用编码 %s 解码失败，使用忽略错误模式",
                    template.template_id,
                    template.version,
                    self._encoding,
                )
                return template.content.decode(self._encoding, errors="ignore")

        if template_format == "docx":
            return self._extract_docx_text(template.content)

        return ""

    def _extract_docx_text(self, payload: bytes) -> str:
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as zf:
                texts: List[str] = []
                for name in zf.namelist():
                    if not name.endswith(".xml"):
                        continue
                    try:
                        data = zf.read(name).decode("utf-8", errors="ignore")
                    except KeyError:
                        continue
                    texts.append(data)
                return "\n".join(texts)
        except zipfile.BadZipFile:
            logger.warning("DOCX 模板内容损坏，无法解析占位符")
            return ""

    def _detect_format(self, path: Path) -> str:
        suffix = path.suffix.lower().lstrip(".")
        if not suffix:
            return "bin"
        return suffix

    def _resolve_version(self, template_id: str, path: Path, fallback: Optional[str]) -> str:
        template_dir = self._storage.base_path / template_id
        try:
            relative = path.relative_to(template_dir)
        except ValueError:
            return fallback or "latest"

        parts = relative.parts
        if len(parts) >= 2:
            return parts[0]
        return fallback or "latest"

    def _ensure_identifier(self, value: str, field: str) -> None:
        if not value or not isinstance(value, str):
            raise ValueError(f"{field} 不能为空")
        if value.strip() != value:
            raise ValueError(f"{field} 不能包含首尾空白")
        if any(sep and sep in value for sep in ("/", "\\")):
            raise ValueError(f"{field} 不能包含路径分隔符")

