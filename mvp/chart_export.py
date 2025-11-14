"""
基于 ChartGenerator 的最小可运行示例
读取 JSON 数据并生成折线/柱状/饼图图片
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# 允许作为脚本直接运行：若无法找到 core 包，则将项目根目录加入 sys.path
try:
    from core.engine.chart import ChartGenerator
except ModuleNotFoundError:  # pragma: no cover - 仅在直接以脚本运行时触发
    import sys as _sys
    from pathlib import Path as _Path

    _project_root = str(_Path(__file__).resolve().parents[1])
    if _project_root not in _sys.path:
        _sys.path.insert(0, _project_root)
    from core.engine.chart import ChartGenerator


class _MemoryChartCache:
    """简单的内存缓存，避免依赖 Redis"""

    def __init__(self):
        self._store: Dict[str, bytes] = {}

    def get_cached_chart(self, data_hash: str) -> Optional[bytes]:
        return self._store.get(data_hash)

    def cache_chart(self, data_hash: str, chart: bytes, ttl: int = 3600) -> bool:
        self._store[data_hash] = bytes(chart)
        return True


def _load_payload(path: Path) -> Dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"配置文件不存在: {path}")
    with path.open("r", encoding="utf-8") as fp:
        payload = json.load(fp)
    if "data" not in payload:
        raise ValueError("配置文件必须包含 data 字段")
    return payload


def _render_chart(
    generator: ChartGenerator,
    chart_type: str,
    data: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> bytes:
    chart_type = chart_type.lower()
    if chart_type == "line":
        return generator.generate_line_chart(data, config)
    if chart_type == "bar":
        return generator.generate_bar_chart(data, config)
    if chart_type == "pie":
        return generator.generate_pie_chart(data, config)
    raise ValueError(f"不支持的图表类型: {chart_type}")


def main() -> None:
    parser = argparse.ArgumentParser(description="MVP: 图表生成功能演示")
    parser.add_argument(
        "config_path",
        type=Path,
        help="包含 data/config/type 的 JSON 文件路径",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="输出图片路径，默认根据类型自动生成",
    )
    parser.add_argument(
        "-t",
        "--type",
        choices=["line", "bar", "pie"],
        default=None,
        help="可覆盖 JSON 中的 type",
    )
    parser.add_argument(
        "--format",
        choices=["png", "jpg", "jpeg"],
        default=None,
        help="输出格式，可覆盖 config.format",
    )
    args = parser.parse_args()

    payload = _load_payload(args.config_path)
    chart_type = args.type or payload.get("type") or "line"
    data = payload["data"]
    config = payload.get("config", {})
    config = dict(config)  # 避免修改原始配置
    config.setdefault("cache_enabled", False)

    if args.format:
        config["format"] = args.format.upper()

    generator = ChartGenerator(cache_storage=_MemoryChartCache())
    chart_bytes = _render_chart(generator, chart_type, data, config)

    extension = (config.get("format") or "png").lower()
    output_path = args.output or Path(f"chart_{chart_type}.{extension}")
    output_path.write_bytes(chart_bytes)
    print(f"[MVP] 图表已生成: {output_path.resolve()}")


if __name__ == "__main__":
    main()

