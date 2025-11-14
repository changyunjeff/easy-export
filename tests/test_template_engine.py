import io
import zipfile

import pytest

from core.engine.template import (
    TemplateEngine,
    Template,
    TextPlaceholder,
)
from core.storage import TemplateStorage


@pytest.fixture
def template_storage(tmp_path) -> TemplateStorage:
    base = tmp_path / "templates"
    return TemplateStorage(base_path=str(base))


@pytest.fixture
def engine(template_storage: TemplateStorage) -> TemplateEngine:
    return TemplateEngine(template_storage=template_storage)


def test_load_template_parses_multiple_placeholder_types(
    engine: TemplateEngine, template_storage: TemplateStorage
) -> None:
    html_template = """
    <html>
      <body>
        <h1>{{ title }}</h1>
        <p>{{ user.name | default("Anonymous") }}</p>
        <section>{{table:items | columns(['name', 'value'])}}</section>
        <figure><img src="{{image:logo | format('png')}}" /></figure>
        <div>{{chart:sales_line}}</div>
      </body>
    </html>
    """.strip().encode("utf-8")

    template_storage.save_template(
        "tpl_html",
        "v1.0.0",
        html_template,
        filename="report.html",
    )

    template = engine.load_template("tpl_html", "v1.0.0")

    assert template.template_id == "tpl_html"
    assert template.version == "v1.0.0"
    assert template.format == "html"
    assert template.placeholders is not None
    kinds = {(placeholder.placeholder_type, placeholder.name) for placeholder in template.placeholders}

    assert ("text", "title") in kinds
    assert ("text", "user.name") in kinds
    assert ("table", "items") in kinds
    assert ("image", "logo") in kinds
    assert ("chart", "sales_line") in kinds

    table_placeholder = next(p for p in template.placeholders if p.placeholder_type == "table")
    assert table_placeholder.config is not None
    assert "filters" in table_placeholder.config


def test_validate_template_detects_invalid_placeholders(engine: TemplateEngine) -> None:
    template = Template(
        template_id="tpl_invalid",
        version="v1",
        format="html",
        content=b"",
        placeholders=[
            TextPlaceholder(name="", placeholder_type="text", raw_text="{{  }}", filters=None)
        ],
    )

    result = engine.validate_template(template)

    assert result.valid is False
    assert len(result.errors) == 1
    assert "缺少占位符名称" in result.errors[0]
    assert "模板中未检测到占位符" not in result.warnings


def test_render_html_template(engine: TemplateEngine, template_storage: TemplateStorage) -> None:
    html_template = "<h1>{{ title }}</h1><p>{{ description }}</p>".encode("utf-8")
    template_storage.save_template("tpl_render", "v1", html_template, filename="page.html")

    template = engine.load_template("tpl_render", "v1")
    rendered = engine.render(
        template,
        {"title": "Hello", "description": "World"},
    )

    assert "<h1>Hello</h1>" in rendered
    assert "<p>World</p>" in rendered


def test_parse_docx_template_placeholders(
    engine: TemplateEngine,
    template_storage: TemplateStorage,
) -> None:
    docx_buffer = io.BytesIO()
    with zipfile.ZipFile(docx_buffer, "w") as zf:
        zf.writestr("word/document.xml", "<w:t>{{ docx_value }}</w:t>")

    template_storage.save_template(
        "tpl_docx",
        "v1",
        docx_buffer.getvalue(),
        filename="document.docx",
    )

    template = engine.load_template("tpl_docx", "v1")
    placeholder_names = {placeholder.name for placeholder in template.placeholders}

    assert "docx_value" in placeholder_names

