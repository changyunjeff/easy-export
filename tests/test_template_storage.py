import time
from pathlib import Path

import pytest

from core.storage import TemplateStorage


@pytest.fixture
def storage(tmp_path):
    base = tmp_path / "templates"
    return TemplateStorage(base_path=str(base))


def test_save_and_get_template_roundtrip(storage):
    template_id = "tpl_unit"
    version = "1.0.0"
    content = b"hello template"

    saved_path = storage.save_template(template_id, version, content, filename="report.docx")

    assert Path(saved_path).exists()
    assert storage.exists(template_id, version)
    assert storage.get_template(template_id, version) == content
    assert storage.get_template(template_id) == content

    file_path = storage.get_template_path(template_id, version)
    assert file_path.name == "report.docx"


def test_list_versions_returns_latest_first(storage):
    template_id = "tpl_versions"
    storage.save_template(template_id, "1.0.0", b"a", filename="v1.docx")
    time.sleep(0.01)
    storage.save_template(template_id, "1.1.0", b"b", filename="v2.docx")
    time.sleep(0.01)
    storage.save_template(template_id, "2.0.0", b"c", filename="v3.docx")

    versions = storage.list_versions(template_id)
    assert versions == ["2.0.0", "1.1.0", "1.0.0"]


def test_delete_specific_version_updates_manifest(storage):
    template_id = "tpl_delete_version"
    storage.save_template(template_id, "1.0.0", b"a")
    storage.save_template(template_id, "1.1.0", b"b")

    assert storage.delete_template(template_id, "1.0.0")
    assert not storage.exists(template_id, "1.0.0")
    assert storage.exists(template_id, "1.1.0")
    assert storage.list_versions(template_id) == ["1.1.0"]


def test_delete_entire_template(storage):
    template_id = "tpl_full_delete"
    storage.save_template(template_id, "1.0.0", b"a")

    assert storage.delete_template(template_id)
    assert storage.list_versions(template_id) == []
    assert not storage.exists(template_id, "1.0.0")
    assert storage.delete_template(template_id) is False


def test_invalid_identifier_rejected(storage):
    with pytest.raises(ValueError):
        storage.save_template("../bad", "1.0.0", b"data")

    storage.save_template("tpl_safe", "1.0.0", b"data")
    with pytest.raises(ValueError):
        storage.save_template("tpl_safe", "../bad", b"data")


