from __future__ import annotations

import base64
from datetime import datetime

import pytest

from core.engine.filler import (
    ChartFillResult,
    ChartFiller,
    ImageFillResult,
    ImageFiller,
    TableFillResult,
    TableFiller,
    TextFiller,
)
from core.engine.image import ImageProcessor
from core.engine.template import (
    ChartPlaceholder,
    ImagePlaceholder,
    TablePlaceholder,
    TextPlaceholder,
)


def test_text_filler_supports_nested_fields_and_filters() -> None:
    filler = TextFiller()
    upper_placeholder = TextPlaceholder(
        name="user.name",
        placeholder_type="text",
        raw_text="{{ user.name | upper }}",
        filters=["upper"],
    )
    default_placeholder = TextPlaceholder(
        name="profile.title",
        placeholder_type="text",
        raw_text="{{ profile.title | default('N/A') }}",
        filters=["default('N/A')"],
    )
    date_placeholder = TextPlaceholder(
        name="meta.generated_at",
        placeholder_type="text",
        raw_text="{{ meta.generated_at | date('%Y-%m') }}",
        filters=["date('%Y-%m')"],
    )

    data = {
        "user": {"name": "alice"},
        "meta": {"generated_at": datetime(2024, 1, 15, 8, 30)},
    }

    assert filler.fill(upper_placeholder, data) == "ALICE"
    assert filler.fill(default_placeholder, data) == "N/A"
    assert filler.fill(date_placeholder, data) == "2024-01"

    missing_placeholder = TextPlaceholder(
        name="missing.field",
        placeholder_type="text",
        raw_text="{{ missing.field }}",
    )
    with pytest.raises(KeyError):
        filler.fill(missing_placeholder, data)


def test_table_filler_applies_filters_and_projection() -> None:
    filler = TableFiller()
    placeholder = TablePlaceholder(
        name="items",
        placeholder_type="table",
        raw_text="{{table:items}}",
        config={
            "filters": [
                "columns(['label', 'value'])",
                "limit(2)",
                "merge(['category'])",
                "sort('value', reverse=True)",
            ]
        },
    )

    data = {
        "items": [
            {"label": "A", "value": 10, "category": "alpha"},
            {"label": "B", "value": 20, "category": "beta"},
            {"label": "C", "value": 5, "category": "alpha"},
        ]
    }

    result = filler.fill(placeholder, data)

    assert isinstance(result, TableFillResult)
    assert result.columns == ["label", "value"]
    assert result.merge_fields == ["category"]
    assert len(result.rows) == 2
    assert result.rows[0] == {"label": "B", "value": 20}
    assert result.rows[1] == {"label": "A", "value": 10}

    empty_placeholder = TablePlaceholder(
        name="missing",
        placeholder_type="table",
        raw_text="{{table:missing}}",
    )
    empty_result = filler.fill(empty_placeholder, data)
    assert empty_result.rows == []


def test_image_filler_loads_base64_and_converts_format() -> None:
    processor = ImageProcessor()
    image_bytes = processor.get_placeholder_image(width=4, height=4, text="X")
    encoded = base64.b64encode(image_bytes).decode("ascii")

    filler = ImageFiller(image_processor=processor)
    placeholder = ImagePlaceholder(
        name="logo",
        placeholder_type="image",
        raw_text="{{image:logo}}",
        config={"filters": ["format('JPEG')"]},
    )

    data = {"logo": f"data:image/png;base64,{encoded}"}
    result = filler.fill(placeholder, data)

    assert isinstance(result, ImageFillResult)
    assert result.format == "JPG"
    assert result.width == 4 and result.height == 4
    assert result.content.startswith(b"\xff\xd8\xff")


def test_chart_filler_renders_line_chart() -> None:
    filler = ChartFiller()
    placeholder = ChartPlaceholder(
        name="sales_chart",
        placeholder_type="chart",
        raw_text="{{chart:sales_chart}}",
        chart_type="line",
    )

    data = {
        "sales_chart": {
            "type": "line",
            "data": [
                {"month": "Jan", "value": 120},
                {"month": "Feb", "value": 150},
            ],
            "config": {
                "x_field": "month",
                "series": [{"y_field": "value", "label": "Value"}],
                "width": 400,
                "height": 240,
            },
        }
    }

    result = filler.fill(placeholder, data)

    assert isinstance(result, ChartFillResult)
    assert result.chart_type == "line"
    assert result.content.startswith(b"\x89PNG")
    assert result.format == "PNG"

