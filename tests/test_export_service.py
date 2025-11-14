from pathlib import Path

import pytest

from core.engine.renderer import HTMLRenderer
from core.engine.template import Template, TemplateEngine
from core.models.export import ExportRequest
from core.service.export_service import ExportService
from core.storage import FileStorage, TemplateStorage


def test_html_renderer_renders_template():
    template = Template(
        template_id="tpl_html",
        version="v1",
        format="html",
        content=b"<h1>{{ title }}</h1>",
        placeholders=None,
    )

    renderer = HTMLRenderer()
    rendered = renderer.render(template, {"title": "Report"})

    assert rendered == b"<h1>Report</h1>"


def test_html_renderer_rejects_binary_template():
    template = Template(
        template_id="tpl_docx",
        version="v1",
        format="docx",
        content=b"{{ title }}",
        placeholders=None,
    )

    renderer = HTMLRenderer()

    with pytest.raises(ValueError):
        renderer.render(template, {"title": "Report"})


@pytest.mark.asyncio
async def test_export_service_exports_html(tmp_path):
    template_storage = TemplateStorage(base_path=str(tmp_path / "templates"))
    file_storage = FileStorage(base_path=str(tmp_path / "outputs"))
    engine = TemplateEngine(template_storage=template_storage)

    template_storage.save_template(
        "tpl_html",
        "v1",
        b"<html><body><h1>{{ title }}</h1></body></html>",
        filename="report.html",
    )

    service = ExportService(template_engine=engine, file_storage=file_storage)

    request = ExportRequest(
        data={"title": "Quarterly"},
        template_ref="tpl_html",
        template_version="v1",
        output_format="html",
        output_filename="quarterly.html",
    )

    result = await service.export_document(request)

    assert result.file_id.endswith(".html")
    assert result.file_size > 0
    assert result.report is not None
    assert result.report.elapsed_ms >= 0
    assert result.report.warnings == []

    output_path = Path(result.file_path)
    assert output_path.exists()
    assert "Quarterly" in output_path.read_text("utf-8")


