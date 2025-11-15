"""
BatchService 单元测试

测试批量处理服务的核心功能，包括批量任务创建、状态查询和结果汇总
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from core.service.batch_service import BatchService
from core.models.task import BatchTask, ExportTask, TaskStatus
from core.storage import CacheStorage


@pytest.fixture
def mock_cache_storage():
    """Mock CacheStorage"""
    return Mock(spec=CacheStorage)


@pytest.fixture
def mock_export_service():
    """Mock ExportService"""
    from core.service.export_service import ExportService
    return Mock(spec=ExportService)


@pytest.fixture
def batch_service(mock_cache_storage, mock_export_service):
    """创建BatchService实例"""
    return BatchService(
        cache_storage=mock_cache_storage,
        export_service=mock_export_service,
    )


@pytest.mark.asyncio
async def test_create_batch_task(batch_service, mock_cache_storage):
    """测试创建批量任务"""
    # 准备测试数据
    task_ids = ["task_001", "task_002", "task_003"]
    metadata = {
        "output_format": "pdf",
        "concurrency": 10,
    }
    
    # 执行测试
    batch_task = await batch_service.create_batch_task(
        task_ids=task_ids,
        metadata=metadata,
    )
    
    # 验证结果
    assert batch_task.task_id.startswith("batch_")
    assert batch_task.total == 3
    assert batch_task.success == 0
    assert batch_task.failed == 0
    assert batch_task.status == TaskStatus.PENDING
    assert batch_task.progress == 0
    
    # 验证缓存调用
    mock_cache_storage.cache_batch_task.assert_called_once()
    call_args = mock_cache_storage.cache_batch_task.call_args
    assert call_args[0][0] == batch_task.task_id  # batch_task_id
    assert call_args[0][1]["total"] == 3  # batch_data


def test_get_batch_status_pending(batch_service, mock_cache_storage, mock_export_service):
    """测试查询批量任务状态 - 所有任务等待中"""
    # 准备测试数据
    batch_task_id = "batch_test_001"
    task_ids = ["task_001", "task_002", "task_003"]
    
    # Mock缓存返回
    mock_cache_storage.get_batch_task.return_value = {
        "task_id": batch_task_id,
        "sub_task_ids": task_ids,
        "total": 3,
        "metadata": {},
        "created_at": datetime.now().isoformat(),
    }
    
    # Mock所有任务都是PENDING状态
    mock_tasks = [
        ExportTask(
            task_id=task_id,
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.PENDING,
            progress=0,
        )
        for task_id in task_ids
    ]
    mock_export_service.get_task_status.side_effect = mock_tasks
    
    # 执行测试
    batch_task = batch_service.get_batch_status(batch_task_id)
    
    # 验证结果
    assert batch_task.task_id == batch_task_id
    assert batch_task.total == 3
    assert batch_task.success == 0
    assert batch_task.failed == 0
    assert batch_task.status == TaskStatus.PENDING
    assert batch_task.progress == 0
    assert len(batch_task.outputs) == 3


def test_get_batch_status_processing(batch_service, mock_cache_storage, mock_export_service):
    """测试查询批量任务状态 - 部分任务处理中"""
    # 准备测试数据
    batch_task_id = "batch_test_002"
    task_ids = ["task_001", "task_002", "task_003"]
    
    # Mock缓存返回
    mock_cache_storage.get_batch_task.return_value = {
        "task_id": batch_task_id,
        "sub_task_ids": task_ids,
        "total": 3,
        "metadata": {},
        "created_at": datetime.now().isoformat(),
    }
    
    # Mock任务状态：1个完成，1个处理中，1个等待
    mock_tasks = [
        ExportTask(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.COMPLETED,
            progress=100,
            file_path="/outputs/file1.pdf",
            file_size=102400,
            pages=10,
        ),
        ExportTask(
            task_id="task_002",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.PROCESSING,
            progress=50,
        ),
        ExportTask(
            task_id="task_003",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.PENDING,
            progress=0,
        ),
    ]
    mock_export_service.get_task_status.side_effect = mock_tasks
    
    # 执行测试
    batch_task = batch_service.get_batch_status(batch_task_id)
    
    # 验证结果
    assert batch_task.task_id == batch_task_id
    assert batch_task.total == 3
    assert batch_task.success == 1
    assert batch_task.failed == 0
    assert batch_task.status == TaskStatus.PROCESSING
    assert batch_task.progress == 33  # 1/3 完成
    assert len(batch_task.outputs) == 3


def test_get_batch_status_completed(batch_service, mock_cache_storage, mock_export_service):
    """测试查询批量任务状态 - 所有任务已完成"""
    # 准备测试数据
    batch_task_id = "batch_test_003"
    task_ids = ["task_001", "task_002"]
    
    # Mock缓存返回
    mock_cache_storage.get_batch_task.return_value = {
        "task_id": batch_task_id,
        "sub_task_ids": task_ids,
        "total": 2,
        "metadata": {},
        "created_at": datetime.now().isoformat(),
    }
    
    # Mock所有任务都已完成
    mock_tasks = [
        ExportTask(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.COMPLETED,
            progress=100,
            file_path="/outputs/file1.pdf",
            file_size=102400,
            pages=10,
        ),
        ExportTask(
            task_id="task_002",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.COMPLETED,
            progress=100,
            file_path="/outputs/file2.pdf",
            file_size=204800,
            pages=20,
        ),
    ]
    mock_export_service.get_task_status.side_effect = mock_tasks
    
    # 执行测试
    batch_task = batch_service.get_batch_status(batch_task_id)
    
    # 验证结果
    assert batch_task.task_id == batch_task_id
    assert batch_task.total == 2
    assert batch_task.success == 2
    assert batch_task.failed == 0
    assert batch_task.status == TaskStatus.COMPLETED
    assert batch_task.progress == 100
    assert len(batch_task.outputs) == 2
    assert batch_task.completed_at is not None
    
    # 验证汇总信息
    assert batch_task.summary is not None
    assert batch_task.summary["total_file_size"] == 307200  # 102400 + 204800
    assert batch_task.summary["total_pages"] == 30  # 10 + 20


def test_get_batch_status_with_failures(batch_service, mock_cache_storage, mock_export_service):
    """测试查询批量任务状态 - 部分任务失败"""
    # 准备测试数据
    batch_task_id = "batch_test_004"
    task_ids = ["task_001", "task_002", "task_003"]
    
    # Mock缓存返回
    mock_cache_storage.get_batch_task.return_value = {
        "task_id": batch_task_id,
        "sub_task_ids": task_ids,
        "total": 3,
        "metadata": {},
        "created_at": datetime.now().isoformat(),
    }
    
    # Mock任务状态：1个成功，2个失败
    mock_tasks = [
        ExportTask(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.COMPLETED,
            progress=100,
            file_path="/outputs/file1.pdf",
            file_size=102400,
            pages=10,
        ),
        ExportTask(
            task_id="task_002",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.FAILED,
            progress=0,
            error="模板不存在",
        ),
        ExportTask(
            task_id="task_003",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.FAILED,
            progress=0,
            error="数据格式错误",
        ),
    ]
    mock_export_service.get_task_status.side_effect = mock_tasks
    
    # 执行测试
    batch_task = batch_service.get_batch_status(batch_task_id)
    
    # 验证结果
    assert batch_task.task_id == batch_task_id
    assert batch_task.total == 3
    assert batch_task.success == 1
    assert batch_task.failed == 2
    assert batch_task.status == TaskStatus.FAILED  # 有失败任务且所有任务已结束
    assert batch_task.progress == 100  # 所有任务都已完成（成功或失败）
    assert len(batch_task.outputs) == 3
    
    # 验证失败任务包含错误信息
    failed_outputs = [o for o in batch_task.outputs if o.get("error")]
    assert len(failed_outputs) == 2


def test_get_batch_status_not_found(batch_service, mock_cache_storage):
    """测试查询不存在的批量任务"""
    # Mock缓存返回None
    mock_cache_storage.get_batch_task.return_value = None
    
    # 执行测试并验证异常
    with pytest.raises(FileNotFoundError) as exc_info:
        batch_service.get_batch_status("batch_not_exist")
    
    assert "Batch task not found" in str(exc_info.value)


@pytest.mark.asyncio
async def test_process_batch(batch_service, mock_cache_storage, mock_export_service):
    """测试处理批量任务"""
    # 准备测试数据
    batch_task_id = "batch_test_005"
    
    # Mock缓存返回
    mock_cache_storage.get_batch_task.return_value = {
        "task_id": batch_task_id,
        "sub_task_ids": ["task_001", "task_002"],
        "total": 2,
        "metadata": {},
        "created_at": datetime.now().isoformat(),
    }
    
    # Mock任务状态
    mock_tasks = [
        ExportTask(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.COMPLETED,
            progress=100,
        ),
        ExportTask(
            task_id="task_002",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.PROCESSING,
            progress=50,
        ),
    ]
    mock_export_service.get_task_status.side_effect = mock_tasks
    
    # 执行测试
    result = await batch_service.process_batch(batch_task_id)
    
    # 验证结果
    assert result["task_id"] == batch_task_id
    assert result["total"] == 2
    assert result["success"] == 1
    assert result["failed"] == 0
    assert result["status"] == TaskStatus.PROCESSING.value
    assert result["progress"] == 50


@pytest.mark.asyncio
async def test_retry_failed_items(batch_service, mock_cache_storage, mock_export_service):
    """测试重试失败任务"""
    # 准备测试数据
    batch_task_id = "batch_test_006"
    
    # Mock缓存返回
    mock_cache_storage.get_batch_task.return_value = {
        "task_id": batch_task_id,
        "sub_task_ids": ["task_001", "task_002", "task_003"],
        "total": 3,
        "metadata": {},
        "created_at": datetime.now().isoformat(),
    }
    
    # Mock任务状态：1个成功，2个失败
    mock_tasks = [
        ExportTask(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.COMPLETED,
            progress=100,
        ),
        ExportTask(
            task_id="task_002",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.FAILED,
            progress=0,
            error="模板不存在",
        ),
        ExportTask(
            task_id="task_003",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.FAILED,
            progress=0,
            error="数据格式错误",
        ),
    ]
    
    # 为每次调用get_task_status设置返回值
    mock_export_service.get_task_status.side_effect = [
        mock_tasks[0], mock_tasks[1], mock_tasks[2],  # get_batch_status调用
        mock_tasks[0], mock_tasks[1], mock_tasks[2],  # retry_failed_items调用
    ]
    
    # 执行测试
    result = await batch_service.retry_failed_items(batch_task_id)
    
    # 验证结果
    assert result["retry_count"] == 2
    assert len(result["failed_task_ids"]) == 2
    assert "task_002" in result["failed_task_ids"]
    assert "task_003" in result["failed_task_ids"]


@pytest.mark.asyncio
async def test_retry_failed_items_no_failures(batch_service, mock_cache_storage, mock_export_service):
    """测试重试失败任务 - 没有失败任务"""
    # 准备测试数据
    batch_task_id = "batch_test_007"
    
    # Mock缓存返回
    mock_cache_storage.get_batch_task.return_value = {
        "task_id": batch_task_id,
        "sub_task_ids": ["task_001", "task_002"],
        "total": 2,
        "metadata": {},
        "created_at": datetime.now().isoformat(),
    }
    
    # Mock所有任务都成功
    mock_tasks = [
        ExportTask(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.COMPLETED,
            progress=100,
        ),
        ExportTask(
            task_id="task_002",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.COMPLETED,
            progress=100,
        ),
    ]
    
    # 为每次调用get_task_status设置返回值
    mock_export_service.get_task_status.side_effect = [
        mock_tasks[0], mock_tasks[1],  # get_batch_status调用
        mock_tasks[0], mock_tasks[1],  # retry_failed_items调用
    ]
    
    # 执行测试
    result = await batch_service.retry_failed_items(batch_task_id)
    
    # 验证结果
    assert result["retry_count"] == 0
    assert "没有需要重试的失败任务" in result["message"]


def test_calculate_summary(batch_service):
    """测试计算汇总信息"""
    # 准备测试数据
    sub_tasks = [
        ExportTask(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.COMPLETED,
            progress=100,
            file_size=102400,
            pages=10,
        ),
        ExportTask(
            task_id="task_002",
            template_id="tpl_001",
            output_format="docx",
            status=TaskStatus.COMPLETED,
            progress=100,
            file_size=204800,
            pages=20,
        ),
        ExportTask(
            task_id="task_003",
            template_id="tpl_001",
            output_format="pdf",
            status=TaskStatus.FAILED,
            progress=0,
        ),
    ]

    # 使用一个稍早的时间（1秒前）以确保elapsed_ms > 0
    from datetime import timedelta
    batch_data = {
        "created_at": (datetime.now() - timedelta(seconds=1)).isoformat(),
    }
    
    # 执行测试
    summary = batch_service._calculate_summary(sub_tasks, batch_data)
    
    # 验证结果
    assert summary["total_file_size"] == 307200  # 只统计成功的任务
    assert summary["total_pages"] == 30
    assert summary["format_distribution"]["pdf"] == 2
    assert summary["format_distribution"]["docx"] == 1
    assert summary["elapsed_ms"] > 0
    assert summary["avg_elapsed_ms"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

