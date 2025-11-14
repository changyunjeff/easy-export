"""
填充引擎模块
负责数据映射、占位符替换、复杂数据类型处理
"""

from __future__ import annotations

import ast
import logging
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from io import BytesIO
from numbers import Number
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union

from PIL import Image, UnidentifiedImageError

from .chart import ChartGenerator
from .image import ImageProcessor
from .template import (
    Placeholder,
    TextPlaceholder,
    TablePlaceholder,
    ImagePlaceholder,
    ChartPlaceholder,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TableFillResult:
    """表格填充结果"""

    rows: List[Dict[str, Any]]
    columns: Optional[List[str]] = None
    merge_fields: Optional[List[str]] = None


@dataclass(frozen=True)
class ImageFillResult:
    """图片填充结果"""

    content: bytes
    format: str
    width: int
    height: int
    source: Optional[str] = None


@dataclass(frozen=True)
class ChartFillResult:
    """图表填充结果"""

    content: bytes
    format: str
    chart_type: str
    cache_key: Optional[str] = None


@dataclass(frozen=True)
class _FilterCall:
    name: str
    args: Tuple[Any, ...]
    kwargs: Dict[str, Any]


class Filler(ABC):
    """填充器基类"""

    @abstractmethod
    def fill(
        self,
        placeholder: Placeholder,
        data: Dict[str, Any],
    ) -> Any:
        """
        填充占位符

        Args:
            placeholder: 占位符对象
            data: 数据字典

        Returns:
            填充后的内容
        """

    @abstractmethod
    def supports_placeholder(self, placeholder: Placeholder) -> bool:
        """检查是否支持指定占位符"""


class TextFiller(Filler):
    """文本填充器"""

    def fill(
        self,
        placeholder: Placeholder,
        data: Dict[str, Any],
    ) -> str:
        if not isinstance(placeholder, TextPlaceholder):
            raise TypeError("TextFiller 仅支持 TextPlaceholder")

        try:
            value = _DataResolver.resolve(data, placeholder.name)
        except KeyError:
            value = None

        filters = _parse_filters(placeholder.filters)
        for filter_call in filters:
            value = self._apply_filter(value, filter_call)

        if value is None:
            raise KeyError(f"文本占位符 {placeholder.name} 未找到对应数据")

        return str(value)

    def supports_placeholder(self, placeholder: Placeholder) -> bool:
        return isinstance(placeholder, TextPlaceholder)

    def _apply_filter(self, value: Any, filter_call: _FilterCall) -> Any:
        name = filter_call.name.lower()

        if name == "default":
            default_value = filter_call.args[0] if filter_call.args else ""
            return value if value not in (None, "") else default_value

        if name == "upper" and value is not None:
            return str(value).upper()

        if name == "lower" and value is not None:
            return str(value).lower()

        if name in {"title", "capitalize"} and value is not None:
            text = str(value)
            return text.title() if name == "title" else text.capitalize()

        if name == "strip" and value is not None:
            return str(value).strip()

        if name == "date":
            fmt = filter_call.args[0] if filter_call.args else "%Y-%m-%d"
            return self._format_date(value, fmt)

        if name == "format" and filter_call.args:
            try:
                return str(filter_call.args[0]).format(value)
            except Exception as exc:
                raise ValueError(f"format 过滤器应用失败: {exc}") from exc

        logger.debug("忽略未支持的文本过滤器 %s", filter_call.name)
        return value

    @staticmethod
    def _format_date(value: Any, fmt: str) -> str:
        target: Optional[datetime]
        if isinstance(value, datetime):
            target = value
        elif isinstance(value, date):
            target = datetime.combine(value, datetime.min.time())
        elif isinstance(value, (int, float)):
            target = datetime.fromtimestamp(value)
        elif isinstance(value, str):
            for parser in (datetime.fromisoformat, lambda v: datetime.strptime(v, "%Y-%m-%d")):
                try:
                    target = parser(value)
                    break
                except ValueError:
                    target = None
            if target is None:
                raise ValueError(f"无法解析日期字符串: {value}")
        else:
            raise ValueError(f"不支持的日期类型: {type(value)!r}")

        if target is None:
            raise ValueError("日期值解析失败")
        return target.strftime(fmt)


class TableFiller(Filler):
    """表格填充器"""

    def fill(
        self,
        placeholder: Placeholder,
        data: Dict[str, Any],
    ) -> TableFillResult:
        if not isinstance(placeholder, TablePlaceholder):
            raise TypeError("TableFiller 仅支持 TablePlaceholder")

        try:
            raw_value = _DataResolver.resolve(data, placeholder.name)
        except KeyError:
            rows = []
        else:
            rows = _coerce_table_rows(raw_value)

        filters = _parse_filters((placeholder.config or {}).get("filters"))

        columns: Optional[List[str]] = None
        merge_fields: Optional[List[str]] = None

        for filter_call in filters:
            name = filter_call.name.lower()
            if name == "columns" and filter_call.args:
                columns = _ensure_str_list(filter_call.args[0])
                rows = [_project_row(row, columns) for row in rows]
            elif name in {"limit", "take"} and filter_call.args:
                limit = max(int(filter_call.args[0]), 0)
                rows = rows[:limit]
            elif name in {"sort", "order_by"} and filter_call.args:
                field = str(filter_call.args[0])
                reverse = bool(
                    filter_call.kwargs.get(
                        "reverse",
                        filter_call.args[1] if len(filter_call.args) > 1 else False,
                    )
                )
                rows.sort(key=lambda item: _sortable(item.get(field)), reverse=reverse)
            elif name == "merge" and filter_call.args:
                merge_fields = _ensure_str_list(filter_call.args[0])
            else:
                logger.debug("忽略未支持的表格过滤器 %s", filter_call.name)

        return TableFillResult(rows=rows, columns=columns, merge_fields=merge_fields)

    def supports_placeholder(self, placeholder: Placeholder) -> bool:
        return isinstance(placeholder, TablePlaceholder)


class ImageFiller(Filler):
    """图片填充器"""

    def __init__(self, image_processor: Optional[ImageProcessor] = None) -> None:
        self._image_processor = image_processor or ImageProcessor()

    def fill(
        self,
        placeholder: Placeholder,
        data: Dict[str, Any],
    ) -> ImageFillResult:
        if not isinstance(placeholder, ImagePlaceholder):
            raise TypeError("ImageFiller 仅支持 ImagePlaceholder")

        try:
            resolved = _DataResolver.resolve(data, placeholder.name)
            content, source = self._materialize_content(resolved)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "图片占位符 %s 加载失败，使用占位图: %s",
                placeholder.name,
                exc,
            )
            content = self._image_processor.get_placeholder_image(text=placeholder.name)
            source = "placeholder"

        filters = _parse_filters((placeholder.config or {}).get("filters"))
        for filter_call in filters:
            name = filter_call.name.lower()
            if name == "format" and filter_call.args:
                content = self._image_processor.convert_format(content, filter_call.args[0])
            elif name == "resize" and len(filter_call.args) >= 2:
                width = int(filter_call.args[0])
                height = int(filter_call.args[1])
                keep_ratio = bool(filter_call.kwargs.get("keep_ratio", True))
                content = self._image_processor.resize(
                    content,
                    width,
                    height,
                    keep_aspect_ratio=keep_ratio,
                )
            else:
                logger.debug("忽略未支持的图片过滤器 %s", filter_call.name)

        fmt = self._image_processor.identify_format(content)
        width, height = _calculate_dimensions(content)

        return ImageFillResult(content=content, format=fmt, width=width, height=height, source=source)

    def supports_placeholder(self, placeholder: Placeholder) -> bool:
        return isinstance(placeholder, ImagePlaceholder)

    def _materialize_content(self, value: Any) -> Tuple[bytes, Optional[str]]:
        if isinstance(value, bytes):
            return value, None

        if isinstance(value, str):
            text = value.strip()
            if text.startswith("http://") or text.startswith("https://"):
                return self._image_processor.load_from_url(text), text
            if text.startswith("data:"):
                return self._image_processor.load_from_base64(text), "inline"
            try:
                return self._image_processor.load_from_base64(text), "inline"
            except ValueError:
                return self._image_processor.load_from_path(text), text

        if isinstance(value, Mapping):
            source: Optional[str] = value.get("source") if isinstance(value.get("source"), str) else None
            timeout = int(value.get("timeout", 3))

            if "content" in value and isinstance(value["content"], (bytes, bytearray)):
                content = bytes(value["content"])
            elif "bytes" in value and isinstance(value["bytes"], (bytes, bytearray)):
                content = bytes(value["bytes"])
            elif "base64" in value and isinstance(value["base64"], str):
                content = self._image_processor.load_from_base64(value["base64"])
                source = source or "inline"
            elif "url" in value and isinstance(value["url"], str):
                content = self._image_processor.load_from_url(value["url"], timeout=timeout)
                source = source or value["url"]
            elif "path" in value and isinstance(value["path"], str):
                content = self._image_processor.load_from_path(value["path"])
                source = source or value["path"]
            else:
                raise ValueError("图片数据未提供有效的 content/url/path/base64 字段")

            if "width" in value and "height" in value:
                content = self._image_processor.resize(
                    content,
                    int(value["width"]),
                    int(value["height"]),
                    keep_aspect_ratio=bool(value.get("keep_ratio", True)),
                )

            if "format" in value:
                content = self._image_processor.convert_format(content, str(value["format"]))

            return content, source

        raise TypeError(f"不支持的图片数据类型: {type(value)!r}")


class ChartFiller(Filler):
    """图表填充器"""

    def __init__(self, chart_generator: Optional[ChartGenerator] = None) -> None:
        self._chart_generator = chart_generator or ChartGenerator()

    def fill(
        self,
        placeholder: Placeholder,
        data: Dict[str, Any],
    ) -> ChartFillResult:
        if not isinstance(placeholder, ChartPlaceholder):
            raise TypeError("ChartFiller 仅支持 ChartPlaceholder")

        try:
            payload = _DataResolver.resolve(data, placeholder.name)
        except KeyError as exc:
            raise KeyError(f"图表占位符 {placeholder.name} 缺少数据") from exc

        dataset, chart_type, config = self._normalize_payload(payload, placeholder)

        chart_type_lower = chart_type.lower()
        if chart_type_lower == "line":
            content = self._chart_generator.generate_line_chart(dataset, config)
        elif chart_type_lower == "bar":
            content = self._chart_generator.generate_bar_chart(dataset, config)
        elif chart_type_lower == "pie":
            content = self._chart_generator.generate_pie_chart(dataset, config)
        else:
            raise ValueError(f"不支持的图表类型: {chart_type}")

        fmt = (config.get("format") or self._chart_generator.DEFAULT_CONFIG["format"]).upper()
        cache_key = None
        try:
            cache_key = self._chart_generator.calculate_data_hash(
                dataset,
                {"chart_type": chart_type_lower, **config},
            )
        except Exception:  # noqa: BLE001
            cache_key = None

        return ChartFillResult(content=content, format=fmt, chart_type=chart_type_lower, cache_key=cache_key)

    def supports_placeholder(self, placeholder: Placeholder) -> bool:
        return isinstance(placeholder, ChartPlaceholder)

    @staticmethod
    def _normalize_payload(
        payload: Any,
        placeholder: ChartPlaceholder,
    ) -> Tuple[List[Dict[str, Any]], str, Dict[str, Any]]:
        chart_type = (placeholder.chart_type or "line").lower()
        config: Dict[str, Any] = {}
        dataset: List[Dict[str, Any]] = []

        if isinstance(payload, Mapping):
            config = deepcopy(payload.get("config") or {})
            data_block = payload.get("data") or payload.get("values") or payload.get("rows") or []
            dataset = _coerce_sequence_of_mappings(data_block)
            chart_type = str(payload.get("type") or chart_type).lower()
            if "format" not in config and isinstance(payload.get("format"), str):
                config["format"] = payload["format"]
        elif isinstance(payload, Sequence) and not isinstance(payload, (str, bytes, bytearray)):
            dataset = _coerce_sequence_of_mappings(payload)
        else:
            raise TypeError(f"图表数据必须是列表或包含 data 字段的字典，当前类型: {type(payload)!r}")

        if not dataset:
            raise ValueError(f"图表占位符 {placeholder.name} 缺少 data 数组")

        return dataset, chart_type, config


# ---------------------------------------------------------------------------
# 辅助函数
# ---------------------------------------------------------------------------

class _DataResolver:
    """负责根据占位符名称解析嵌套数据"""

    @staticmethod
    def resolve(data: Any, path: str) -> Any:
        if path is None or path == "":
            return data

        current = data
        for token in _DataResolver._tokenize(path):
            if isinstance(current, Mapping):
                if token in current:
                    current = current[token]
                    continue
            if isinstance(current, Sequence) and not isinstance(current, (str, bytes, bytearray)):
                if isinstance(token, int):
                    current = current[token]
                    continue
            if hasattr(current, token):
                current = getattr(current, token)
                continue
            raise KeyError(f"数据中缺少路径 {path!r}（停止于 {token!r}）")
        return current

    @staticmethod
    def _tokenize(path: str) -> List[Union[str, int]]:
        tokens: List[Union[str, int]] = []
        buffer = ""
        i = 0
        length = len(path)

        while i < length:
            char = path[i]
            if char == ".":
                if buffer:
                    tokens.append(buffer)
                    buffer = ""
                i += 1
                continue
            if char == "[":
                if buffer:
                    tokens.append(buffer)
                    buffer = ""
                end_idx = path.find("]", i)
                if end_idx == -1:
                    raise ValueError(f"路径 {path!r} 中的括号未闭合")
                content = path[i + 1 : end_idx].strip()
                if (content.startswith("'") and content.endswith("'")) or (
                    content.startswith('"') and content.endswith('"')
                ):
                    tokens.append(content[1:-1])
                else:
                    try:
                        tokens.append(int(content))
                    except ValueError:
                        tokens.append(content)
                i = end_idx + 1
                continue
            buffer += char
            i += 1

        if buffer:
            tokens.append(buffer)

        return [token for token in tokens if token != ""]


def _parse_filters(filters: Optional[Sequence[str]]) -> List[_FilterCall]:
    parsed: List[_FilterCall] = []
    if not filters:
        return parsed

    for entry in filters:
        if not entry:
            continue
        try:
            parsed.append(_parse_filter_expression(entry))
        except ValueError as exc:
            logger.warning("解析过滤器 %s 失败: %s", entry, exc)
    return parsed


def _parse_filter_expression(expression: str) -> _FilterCall:
    expr = expression.strip()
    try:
        node = ast.parse(expr, mode="eval").body
    except SyntaxError as exc:
        raise ValueError(f"过滤器表达式语法错误: {expression}") from exc

    if isinstance(node, ast.Name):
        return _FilterCall(name=node.id, args=(), kwargs={})

    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
        args = tuple(ast.literal_eval(arg) for arg in node.args)
        kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords if kw.arg}
        return _FilterCall(name=node.func.id, args=args, kwargs=kwargs)

    raise ValueError(f"不支持的过滤器表达式: {expression}")


def _coerce_table_rows(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        rows_source = value.get("rows") or value.get("data") or value.get("values")
        if rows_source is None:
            raise TypeError("表格数据字典必须包含 rows/data 字段")
    else:
        rows_source = value

    return _coerce_sequence_of_mappings(rows_source)


def _coerce_sequence_of_mappings(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        raise TypeError("表格/图表数据必须是由字典组成的列表")

    normalized: List[Dict[str, Any]] = []
    for row in value:
        if row is None:
            continue
        if isinstance(row, Mapping):
            normalized.append(dict(row))
        elif hasattr(row, "__dict__"):
            normalized.append(dict(row.__dict__))
        else:
            raise TypeError(f"数据行必须是字典或可转换为字典的对象，当前类型: {type(row)!r}")
    return normalized


def _ensure_str_list(value: Any) -> List[str]:
    if isinstance(value, (list, tuple, set)):
        items = value
    else:
        items = [value]
    result = [str(item) for item in items if item is not None]
    if not result:
        raise ValueError("过滤器需要至少一个字段名称")
    return result


def _project_row(row: Dict[str, Any], columns: Sequence[str]) -> Dict[str, Any]:
    return {column: row.get(column) for column in columns}


def _sortable(value: Any) -> Tuple[int, Union[float, str]]:
    if value is None:
        return (1, "")
    if isinstance(value, Number):
        return (0, float(value))
    return (0, str(value))


def _calculate_dimensions(content: bytes) -> Tuple[int, int]:
    try:
        with Image.open(BytesIO(content)) as img:
            return img.width, img.height
    except (UnidentifiedImageError, OSError):  # pragma: no cover - 已通过格式校验
        return (0, 0)


