import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from core.storage import FileStorage


@pytest.fixture
def storage(tmp_path):
    base = tmp_path / "outputs"
    return FileStorage(base_path=str(base))


def read_metadata(storage: FileStorage, file_id: str):
    file_path = storage.get_file_path(file_id)
    meta_path = file_path.parent / f"{file_path.name}{FileStorage.METADATA_SUFFIX}"
    with meta_path.open("r", encoding="utf-8") as fp:
        return json.load(fp)


def test_save_and_get_file_roundtrip(storage):
    file_id = "task_001.docx"
    content = b"exported-content"

    saved_path = storage.save_file(file_id, content, filename="report.docx")

    assert Path(saved_path).exists()
    assert storage.exists(file_id)
    assert storage.get_file(file_id) == content

    file_path = storage.get_file_path(file_id)
    assert file_path.name == file_id

    metadata = read_metadata(storage, file_id)
    assert metadata["download_name"] == "report.docx"
    assert metadata["file_size"] == len(content)


def test_save_file_sanitizes_filename(storage):
    file_id = "file_without_ext"
    storage.save_file(file_id, b"data", filename="../secret/report.pdf")

    metadata = read_metadata(storage, file_id)
    assert metadata["download_name"] == "report.pdf"


def test_get_file_url_uses_config_prefix(storage):
    file_id = "abc123.pdf"
    storage.save_file(file_id, b"content")

    url = storage.get_file_url(file_id)
    assert url.endswith(f"/{file_id}")
    assert url.startswith("/")


def test_delete_file_removes_metadata(storage):
    file_id = "delete_me.txt"
    storage.save_file(file_id, b"bye")

    file_path = storage.get_file_path(file_id)
    meta_path = file_path.parent / f"{file_path.name}{FileStorage.METADATA_SUFFIX}"
    assert file_path.exists() and meta_path.exists()

    assert storage.delete_file(file_id)
    assert not file_path.exists()
    assert not meta_path.exists()
    assert storage.delete_file(file_id) is False


def test_cleanup_temp_files(storage):
    old_file = "old.bin"
    new_file = "new.bin"

    storage.save_file(old_file, b"old")
    storage.save_file(new_file, b"new")

    # 手动调整元数据时间，使 old_file 早于 1 小时前
    old_meta = read_metadata(storage, old_file)
    old_meta["saved_at_ts"] = (datetime.now(timezone.utc) - timedelta(hours=2)).timestamp()
    old_path = storage.get_file_path(old_file)
    meta_path = old_path.parent / f"{old_path.name}{FileStorage.METADATA_SUFFIX}"
    meta_path.write_text(json.dumps(old_meta), encoding="utf-8")
    time.sleep(0.01)  # 确保文件系统时间更新

    cutoff = datetime.now(timezone.utc) - timedelta(hours=1)
    removed = storage.cleanup_temp_files(cutoff)

    assert removed == 1
    assert not storage.exists(old_file)
    assert storage.exists(new_file)


def test_invalid_file_id_rejected(storage):
    with pytest.raises(ValueError):
        storage.save_file("../hack", b"boom")


def test_get_missing_file_raises(storage):
    with pytest.raises(FileNotFoundError):
        storage.get_file("no_such_file")

