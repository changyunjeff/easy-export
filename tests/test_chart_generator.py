from __future__ import annotations

import pytest

from core.engine.chart import ChartGenerator


class _FakeCacheStorage:
    def __init__(self):
        self._store = {}
        self.set_calls = 0
        self.get_calls = 0

    def get_cached_chart(self, data_hash: str):
        self.get_calls += 1
        return self._store.get(data_hash)

    def cache_chart(self, data_hash: str, chart: bytes, ttl: int = 3600):
        self.set_calls += 1
        self._store[data_hash] = bytes(chart)
        return True


def test_generate_line_chart_returns_png_and_uses_cache():
    cache = _FakeCacheStorage()
    generator = ChartGenerator(cache_storage=cache)
    data = [
        {"month": "Jan", "value": 120},
        {"month": "Feb", "value": 150},
        {"month": "Mar", "value": 90},
    ]
    config = {
        "x_field": "month",
        "y_field": "value",
        "title": "Monthly Revenue",
    }

    first = generator.generate_line_chart(data, config)
    second = generator.generate_line_chart(data, config)

    assert first.startswith(b"\x89PNG")
    assert second == first
    assert cache.set_calls == 1
    assert cache.get_calls >= 2


def test_generate_bar_chart_supports_multiple_series_and_jpeg_output():
    cache = _FakeCacheStorage()
    generator = ChartGenerator(cache_storage=cache)
    data = [
        {"quarter": "Q1", "sales": 120, "target": 110},
        {"quarter": "Q2", "sales": 140, "target": 135},
        {"quarter": "Q3", "sales": 130, "target": 125},
    ]
    config = {
        "x_field": "quarter",
        "series": [
            {"y_field": "sales", "label": "Actual"},
            {"y_field": "target", "label": "Target"},
        ],
        "format": "JPEG",
        "title": "Quarterly Sales",
        "y_label": "Revenue (£k)",
    }

    chart_bytes = generator.generate_bar_chart(data, config)

    assert chart_bytes.startswith(b"\xff\xd8\xff")
    assert cache.set_calls == 1


def test_generate_pie_chart_allows_custom_palette_and_no_labels():
    cache = _FakeCacheStorage()
    generator = ChartGenerator(cache_storage=cache)
    data = [
        {"name": "North", "ratio": 0.4},
        {"name": "South", "ratio": 0.35},
        {"name": "West", "ratio": 0.25},
    ]
    config = {
        "label_field": "name",
        "value_field": "ratio",
        "palette": ["#FF6B6B", "#4ECDC4", "#556270"],
        "show_labels": False,
        "autopct": None,
    }

    chart_bytes = generator.generate_pie_chart(data, config)

    assert chart_bytes.startswith(b"\x89PNG")
    assert cache.set_calls == 1


def test_generate_line_chart_requires_x_field():
    generator = ChartGenerator(cache_storage=_FakeCacheStorage())
    data = [{"value": 1}, {"value": 2}]

    with pytest.raises(ValueError):
        generator.generate_line_chart(data, {"y_field": "value"})

