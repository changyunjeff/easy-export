"""
图表生成器模块：负责折线图、柱状图、饼图的生成与缓存
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass
from io import BytesIO
from numbers import Number
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import matplotlib

matplotlib.use("Agg")
from matplotlib import pyplot as plt  # noqa: E402

from core.storage import CacheStorage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _SeriesConfig:
    label: str
    x_field: str
    y_field: str
    color: Optional[str] = None
    line_style: Optional[str] = None
    line_width: Optional[float] = None
    marker: Optional[str] = None


class ChartGenerator:
    """
    图表生成器
    负责图表生成、缓存与配置归一化
    """

    DEFAULT_CONFIG: Dict[str, Any] = {
        "title": "",
        "x_label": "",
        "y_label": "",
        "width": 800,
        "height": 480,
        "dpi": 120,
        "background_color": "#ffffff",
        "plot_background": "#ffffff",
        "grid": True,
        "legend": True,
        "line_style": "-",
        "line_width": 2.0,
        "marker": None,
        "bar_width": 0.8,
        "format": "PNG",
        "palette": [
            "#2563EB",
            "#F97316",
            "#10B981",
            "#F43F5E",
            "#9333EA",
            "#14B8A6",
        ],
        "cache_enabled": True,
        "cache_ttl": 3600,
        "sort_x": False,
        "autopct": "%1.1f%%",
        "show_labels": True,
    }

    SUPPORTED_FORMATS = {"PNG", "JPEG"}

    def __init__(self, cache_storage: Optional[CacheStorage] = None):
        """
        Args:
            cache_storage: 缓存存储实例，缺省时创建默认 CacheStorage
        """

        self.cache_storage = cache_storage or CacheStorage()
        logger.info("Chart generator initialized")

    # ---------------------------- 公有 API ---------------------------- #

    def generate_line_chart(
        self,
        data: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        normalized = self._normalize_config(config, chart_type="line")
        x_field = normalized.get("x_field")
        y_field = normalized.get("y_field")
        series_list = self._resolve_series(
            normalized, default_y_field=y_field, require_x_field=True
        )
        return self._render_with_cache(
            "line",
            data,
            normalized,
            lambda fig, ax: self._plot_line_chart(ax, data, normalized, series_list),
            {"series": [series.__dict__ for series in series_list], "x_field": x_field},
        )

    def generate_bar_chart(
        self,
        data: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        normalized = self._normalize_config(config, chart_type="bar")
        category_field = normalized.get("category_field") or normalized.get("x_field")
        if not category_field:
            raise ValueError("柱状图需要指定 category_field 或 x_field")

        series_list = self._resolve_series(
            normalized,
            default_y_field=normalized.get("y_field"),
            require_x_field=True,
            x_field_override=category_field,
        )

        return self._render_with_cache(
            "bar",
            data,
            normalized,
            lambda fig, ax: self._plot_bar_chart(
                ax, data, normalized, series_list, category_field
            ),
            {
                "series": [series.__dict__ for series in series_list],
                "category_field": category_field,
            },
        )

    def generate_pie_chart(
        self,
        data: List[Dict[str, Any]],
        config: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        normalized = self._normalize_config(config, chart_type="pie")
        label_field = (
            normalized.get("label_field")
            or normalized.get("category_field")
            or normalized.get("x_field")
        )
        value_field = normalized.get("value_field") or normalized.get("y_field")

        if not label_field or not value_field:
            raise ValueError("饼图需要指定 label_field 与 value_field/y_field")

        return self._render_with_cache(
            "pie",
            data,
            normalized,
            lambda fig, ax: self._plot_pie_chart(
                ax, data, normalized, label_field, value_field
            ),
            {"label_field": label_field, "value_field": value_field},
        )

    def get_cached_chart(self, data_hash: str) -> Optional[bytes]:
        return self.cache_storage.get_cached_chart(data_hash)

    def cache_chart(
        self,
        data_hash: str,
        chart: bytes,
        ttl: int = 3600,
    ) -> bool:
        return self.cache_storage.cache_chart(data_hash, chart, ttl)

    def calculate_data_hash(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> str:
        combined = {
            "data": data,
            "config": config,
        }
        json_str = json.dumps(combined, sort_keys=True, ensure_ascii=False)
        hash_obj = hashlib.sha256(json_str.encode("utf-8"))
        return hash_obj.hexdigest()

    # ---------------------------- 绘图实现 ---------------------------- #

    def _plot_line_chart(
        self,
        ax,
        data: List[Dict[str, Any]],
        config: Dict[str, Any],
        series_list: Sequence[_SeriesConfig],
    ) -> None:
        plotted = 0
        palette = self._resolve_palette(config, len(series_list))

        for idx, series in enumerate(series_list):
            points = self._extract_xy_points(data, series.x_field, series.y_field)
            if not points:
                logger.debug(
                    "Line chart skip series %s: no valid points", series.label
                )
                continue

            if config.get("sort_x"):
                try:
                    points.sort(key=lambda item: item[0])
                except TypeError:
                    logger.debug("Line chart skip sorting due to incomparable x values")

            xs, ys = zip(*points)
            color = series.color or palette[idx % len(palette)]
            ax.plot(
                xs,
                ys,
                label=series.label,
                color=color,
                linestyle=series.line_style or config["line_style"],
                linewidth=series.line_width or config["line_width"],
                marker=series.marker or config["marker"],
            )
            plotted += 1

        if plotted == 0:
            raise ValueError("折线图缺少可绘制的数据点")

        self._apply_axes_style(ax, config)

    def _plot_bar_chart(
        self,
        ax,
        data: List[Dict[str, Any]],
        config: Dict[str, Any],
        series_list: Sequence[_SeriesConfig],
        category_field: str,
    ) -> None:
        categories, aggregated = self._aggregate_bar_values(
            data, category_field, series_list
        )
        if not categories:
            raise ValueError("柱状图缺少有效的分类数据")

        palette = self._resolve_palette(config, len(series_list))
        total_series = len(series_list)
        group_width = config["bar_width"]
        single_width = group_width / max(total_series, 1)
        indices = list(range(len(categories)))

        for idx, series in enumerate(series_list):
            offsets = [
                i + (idx - (total_series - 1) / 2) * single_width for i in indices
            ]
            values = [
                aggregated[cat].get(series.y_field, 0.0) for cat in categories
            ]
            color = series.color or palette[idx % len(palette)]
            ax.bar(
                offsets,
                values,
                width=single_width * 0.9,
                label=series.label,
                color=color,
            )

        ax.set_xticks(indices)
        ax.set_xticklabels(categories)
        self._apply_axes_style(ax, config)

    def _plot_pie_chart(
        self,
        ax,
        data: List[Dict[str, Any]],
        config: Dict[str, Any],
        label_field: str,
        value_field: str,
    ) -> None:
        labels: List[Any] = []
        values: List[float] = []
        for row in data:
            if not isinstance(row, dict):
                continue
            label = row.get(label_field)
            numeric = self._coerce_numeric(row.get(value_field))
            if label is None or numeric is None:
                continue
            labels.append(label)
            values.append(numeric)

        if not values:
            raise ValueError("饼图缺少有效的数据")

        if sum(values) == 0:
            raise ValueError("饼图数值总和不能为 0")

        colors = self._resolve_palette(config, len(values))
        explode = self._normalize_explode(config.get("explode"), len(values))
        autopct = config.get("autopct")
        show_labels = config.get("show_labels", True)

        ax.pie(
            values,
            labels=labels if show_labels else None,
            autopct=autopct,
            colors=colors,
            explode=explode,
            startangle=config.get("start_angle", 90),
        )
        ax.axis("equal")
        title = config.get("title")
        if title:
            ax.set_title(title)

    # ---------------------------- 辅助方法 ---------------------------- #

    def _render_with_cache(
        self,
        chart_type: str,
        data: List[Dict[str, Any]],
        config: Dict[str, Any],
        plotter,
        extra_hash_fields: Optional[Dict[str, Any]] = None,
    ) -> bytes:
        self._validate_dataset(data)
        hash_config = self._config_for_hash(config, chart_type, extra_hash_fields)
        data_hash = self.calculate_data_hash(data, hash_config)

        if config.get("cache_enabled", True):
            cached = self.get_cached_chart(data_hash)
            if cached is not None:
                logger.debug("Chart cache hit (%s)", chart_type)
                return cached

        fig, ax = self._create_figure(config)
        try:
            plotter(fig, ax)
            chart_bytes = self._figure_to_bytes(fig, config)
        finally:
            plt.close(fig)

        if config.get("cache_enabled", True):
            ttl = max(int(config.get("cache_ttl", 3600)), 1)
            self.cache_chart(data_hash, chart_bytes, ttl)

        return chart_bytes

    def _normalize_config(
        self,
        config: Optional[Dict[str, Any]],
        chart_type: str,
    ) -> Dict[str, Any]:
        cfg = deepcopy(self.DEFAULT_CONFIG)
        user_cfg = config or {}
        for key, value in user_cfg.items():
            if value is None:
                continue
            cfg[key] = value

        cfg["format"] = self._normalize_format(cfg.get("format", "PNG"))
        cfg["grid"] = self._normalize_bool(cfg.get("grid", True))
        cfg["legend"] = self._normalize_bool(cfg.get("legend", True))
        cfg["cache_enabled"] = self._normalize_bool(cfg.get("cache_enabled", True))
        cfg["chart_type"] = chart_type
        cfg["width"] = self._ensure_positive_int(cfg.get("width"), "width")
        cfg["height"] = self._ensure_positive_int(cfg.get("height"), "height")
        cfg["dpi"] = self._ensure_positive_int(cfg.get("dpi"), "dpi")
        cfg["cache_ttl"] = max(int(cfg.get("cache_ttl", 3600)), 1)
        cfg["line_width"] = self._ensure_positive_float(
            cfg.get("line_width", self.DEFAULT_CONFIG["line_width"]),
            "line_width",
        )
        cfg["palette"] = self._normalize_palette(cfg.get("palette"))

        cfg["bar_width"] = max(
            self._ensure_positive_float(cfg.get("bar_width"), "bar_width"),
            0.2,
        )

        return cfg

    def _resolve_series(
        self,
        config: Dict[str, Any],
        default_y_field: Optional[str],
        require_x_field: bool,
        x_field_override: Optional[str] = None,
    ) -> List[_SeriesConfig]:
        x_field_default = x_field_override or config.get("x_field")
        raw_series = config.get("series")
        result: List[_SeriesConfig] = []

        if raw_series:
            if not isinstance(raw_series, (list, tuple)):
                raise ValueError("series 必须是列表")
            for idx, entry in enumerate(raw_series, start=1):
                if not isinstance(entry, dict):
                    raise ValueError("series 配置必须是字典")
                y_field = entry.get("y_field") or default_y_field
                x_field = entry.get("x_field") or x_field_default
                if not y_field:
                    raise ValueError("series.y_field 不能为空")
                if require_x_field and not x_field:
                    raise ValueError("series.x_field 或 x_field 必须指定")
                result.append(
                    _SeriesConfig(
                        label=entry.get("label") or f"Series {idx}",
                        y_field=y_field,
                        x_field=x_field if x_field else "",
                        color=entry.get("color"),
                        line_style=entry.get("line_style"),
                        line_width=entry.get("line_width"),
                        marker=entry.get("marker"),
                    )
                )
        elif default_y_field:
            if require_x_field and not x_field_default:
                raise ValueError("x_field 必须指定")
            result.append(
                _SeriesConfig(
                    label=config.get("series_label") or default_y_field,
                    y_field=default_y_field,
                    x_field=x_field_default if x_field_default else "",
                    color=config.get("series_color"),
                    line_style=config.get("line_style"),
                    line_width=config.get("line_width"),
                    marker=config.get("marker"),
                )
            )
        else:
            raise ValueError("必须提供 y_field 或 series 配置")

        return result

    def _resolve_palette(
        self,
        config: Dict[str, Any],
        series_count: int,
    ) -> List[str]:
        palette = [color for color in config.get("palette", []) if color]
        if not palette:
            palette = list(self.DEFAULT_CONFIG["palette"])

        while len(palette) < series_count:
            palette.extend(self.DEFAULT_CONFIG["palette"])
        return palette[:series_count]

    def _extract_xy_points(
        self,
        data: Iterable[Dict[str, Any]],
        x_field: str,
        y_field: str,
    ) -> List[Tuple[Any, float]]:
        points: List[Tuple[Any, float]] = []
        for row in data:
            if not isinstance(row, dict):
                continue
            if x_field not in row or y_field not in row:
                continue
            numeric = self._coerce_numeric(row[y_field])
            if numeric is None:
                continue
            points.append((row[x_field], numeric))
        return points

    def _aggregate_bar_values(
        self,
        data: Iterable[Dict[str, Any]],
        category_field: str,
        series_list: Sequence[_SeriesConfig],
    ) -> Tuple[List[Any], Dict[Any, Dict[str, float]]]:
        categories: List[Any] = []
        aggregated: Dict[Any, Dict[str, float]] = defaultdict(dict)

        for row in data:
            if not isinstance(row, dict):
                continue
            category = row.get(category_field)
            if category is None:
                continue
            if category not in categories:
                categories.append(category)
            for series in series_list:
                if series.y_field not in row:
                    continue
                numeric = self._coerce_numeric(row[series.y_field])
                if numeric is None:
                    continue
                aggregated.setdefault(category, {})
                aggregated[category][series.y_field] = (
                    aggregated[category].get(series.y_field, 0.0) + numeric
                )

        return categories, aggregated

    def _apply_axes_style(self, ax, config: Dict[str, Any]) -> None:
        title = config.get("title")
        if title:
            ax.set_title(title)
        if config.get("x_label"):
            ax.set_xlabel(config["x_label"])
        if config.get("y_label"):
            ax.set_ylabel(config["y_label"])
        if config.get("grid", True):
            ax.grid(True, linestyle="--", alpha=0.3)
        if config.get("legend", True):
            ax.legend()

    def _create_figure(self, config: Dict[str, Any]):
        figsize = (
            config["width"] / config["dpi"],
            config["height"] / config["dpi"],
        )
        fig, ax = plt.subplots(figsize=figsize, dpi=config["dpi"])
        fig.patch.set_facecolor(config.get("background_color"))
        ax.set_facecolor(config.get("plot_background"))
        fig.tight_layout()
        return fig, ax

    def _figure_to_bytes(self, fig, config: Dict[str, Any]) -> bytes:
        buffer = BytesIO()
        fig.savefig(
            buffer,
            format=config["format"],
            dpi=config["dpi"],
            bbox_inches="tight",
        )
        buffer.seek(0)
        return buffer.getvalue()

    def _config_for_hash(
        self,
        config: Dict[str, Any],
        chart_type: str,
        extra: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        excluded = {"cache_enabled", "cache_ttl"}
        payload = {k: v for k, v in config.items() if k not in excluded}
        payload["chart_type"] = chart_type
        if extra:
            payload.update(extra)
        return payload

    def _normalize_format(self, fmt: str) -> str:
        if not fmt:
            raise ValueError("format 不能为空")
        normalized = fmt.strip().upper()
        if normalized == "JPG":
            normalized = "JPEG"
        if normalized not in self.SUPPORTED_FORMATS:
            raise ValueError(f"不支持的图表格式: {fmt}")
        return normalized

    def _normalize_palette(self, palette: Optional[Iterable[str]]) -> List[str]:
        if palette is None:
            return list(self.DEFAULT_CONFIG["palette"])
        result = [color for color in palette if isinstance(color, str) and color]
        return result or list(self.DEFAULT_CONFIG["palette"])

    def _normalize_explode(
        self,
        explode: Optional[Iterable[Any]],
        count: int,
    ) -> Optional[List[float]]:
        if explode is None:
            return None
        normalized: List[float] = []
        for value in explode:
            numeric = self._coerce_numeric(value)
            normalized.append(numeric if numeric is not None else 0.0)
        if not normalized:
            return None
        while len(normalized) < count:
            normalized.append(0.0)
        return normalized[:count]

    def _normalize_bool(self, value: Any, default: bool = True) -> bool:
        if value is None:
            return default
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "on"}
        return bool(value)

    def _coerce_numeric(self, value: Any) -> Optional[float]:
        if isinstance(value, Number):
            return float(value)
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return None
            try:
                return float(stripped)
            except ValueError:
                return None
        return None

    def _validate_dataset(self, data: Any) -> None:
        if not isinstance(data, list) or not data:
            raise ValueError("data 必须是非空列表")
        if not any(isinstance(item, dict) for item in data):
            raise ValueError("data 需要至少包含一个字典元素")

    def _ensure_positive_int(self, value: Any, field: str) -> int:
        try:
            numeric = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field} 必须是正整数") from exc
        if numeric <= 0:
            raise ValueError(f"{field} 必须大于 0")
        return numeric

    def _ensure_positive_float(self, value: Any, field: str) -> float:
        try:
            numeric = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{field} 必须是正数") from exc
        if numeric <= 0:
            raise ValueError(f"{field} 必须大于 0")
        return numeric

