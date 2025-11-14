import time
from datetime import timedelta

import pytest

from core.redis import MemoryStore
from core.redis.client import RedisClient
from core.storage import CacheStorage


@pytest.fixture
def storage():
    client = RedisClient(MemoryStore())
    return CacheStorage(redis_client=client)


def test_cache_chart_roundtrip(storage: CacheStorage):
    data_hash = "chart-hash-001"
    chart_bytes = b"\x00\xffchart-bytes"

    assert storage.cache_chart(data_hash, chart_bytes, ttl=60)

    cached = storage.get_cached_chart(data_hash)
    assert cached == chart_bytes

    assert storage.delete_cached_chart(data_hash)
    assert storage.get_cached_chart(data_hash) is None


def test_cache_chart_expiration(storage: CacheStorage):
    data_hash = "chart-expire"
    storage.cache_chart(data_hash, b"payload", ttl=1)

    time.sleep(1.1)
    assert storage.get_cached_chart(data_hash) is None


def test_cache_template_metadata_roundtrip(storage: CacheStorage):
    template_id = "tpl_001"
    metadata = {"name": "report", "version": "v1.0.0", "tags": ["monthly"]}

    assert storage.cache_template_metadata(template_id, metadata, ttl=timedelta(minutes=5))

    cached = storage.get_template_metadata(template_id)
    assert cached == metadata

    # 修改返回值不会影响缓存内容
    cached["name"] = "mutated"
    fresh = storage.get_template_metadata(template_id)
    assert fresh["name"] == "report"

    assert storage.delete_template_metadata(template_id)
    assert storage.get_template_metadata(template_id) is None


def test_cache_task_status_roundtrip(storage: CacheStorage):
    task_id = "task_123"
    status = {"status": "pending", "progress": 30}

    assert storage.cache_task_status(task_id, status)
    cached = storage.get_task_status(task_id)
    assert cached == status

    assert storage.delete_task_status(task_id)
    assert storage.get_task_status(task_id) is None


def test_cache_task_status_expiration(storage: CacheStorage):
    task_id = "task_expire"
    storage.cache_task_status(task_id, {"status": "running"}, ttl=1)

    time.sleep(1.1)
    assert storage.get_task_status(task_id) is None


def test_cache_invalid_inputs(storage: CacheStorage):
    with pytest.raises(ValueError):
        storage.cache_chart("", b"data")

    with pytest.raises(ValueError):
        storage.cache_chart("hash", "not-bytes")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        storage.cache_template_metadata("tpl", ["invalid"])  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        storage.cache_task_status("task", "invalid")  # type: ignore[arg-type]

    with pytest.raises(ValueError):
        storage.cache_task_status("task", {}, ttl=0)

