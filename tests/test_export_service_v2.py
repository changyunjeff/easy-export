"""
导出服务单元测试
测试单文档导出、任务状态管理、文件下载等功能
"""

import pytest
import tempfile
import shutil
import asyncio
from pathlib import Path
from io import BytesIO
from fastapi import UploadFile

from core.service.export_service import ExportService
from core.service.template_service import TemplateService
from core.models.export import ExportRequest
from core.models.task import TaskStatus
from core.storage import TemplateStorage, FileStorage, CacheStorage
from core.engine import TemplateEngine


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    temp_path = tempfile.mkdtemp()
    yield Path(temp_path)
    # 清理临时目录
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def template_storage(temp_dir):
    """创建模板存储实例"""
    return TemplateStorage(base_path=str(temp_dir / "templates"))


@pytest.fixture
def file_storage(temp_dir):
    """创建文件存储实例"""
    return FileStorage(base_path=str(temp_dir / "outputs"))


@pytest.fixture
def cache_storage():
    """创建缓存存储实例"""
    return CacheStorage()


@pytest.fixture
def template_engine(template_storage):
    """创建模板引擎实例"""
    return TemplateEngine(template_storage=template_storage)


@pytest.fixture
def export_service(template_engine, file_storage, cache_storage):
    """创建导出服务实例"""
    return ExportService(
        template_engine=template_engine,
        file_storage=file_storage,
        cache_storage=cache_storage,
        default_output_format="html"
    )


@pytest.fixture
def template_service(template_storage):
    """创建模板服务实例"""
    return TemplateService(template_storage=template_storage)


@pytest.fixture
def sample_html_template():
    """示例HTML模板内容"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ heading }}</h1>
    <p>{{ content }}</p>
</body>
</html>
"""


async def create_upload_file(filename: str, content: bytes, content_type: str = "text/html"):
    """创建UploadFile对象"""
    file_stream = BytesIO(content)
    return UploadFile(
        filename=filename,
        file=file_stream,
        size=len(content),
        headers={"content-type": content_type}
    )


@pytest.mark.asyncio
async def test_export_document_html(export_service, template_service, sample_html_template):
    """测试HTML文档导出"""
    # 1. 创建模板
    file = await create_upload_file(
        "test_template.html",
        sample_html_template.encode("utf-8"),
        "text/html"
    )
    
    metadata = {
        "name": "测试模板",
        "description": "用于单元测试",
        "tags": ["test"],
        "version": "1.0.0"
    }
    
    template = await template_service.create_template(file, metadata)
    template_id = template.template_id
    
    # 2. 执行导出
    request = ExportRequest(
        data={
            "title": "测试标题",
            "heading": "测试大标题",
            "content": "这是测试内容"
        },
        template_ref=template_id,
        output_format="html",
        output_filename="test_output.html"
    )
    
    result = await export_service.export_document(request)
    
    # 3. 验证结果
    assert result is not None
    assert result.task_id is not None
    assert result.file_id is not None
    assert result.file_path is not None
    assert result.file_url is not None
    assert result.file_size > 0
    assert result.pages >= 1
    assert result.report is not None
    assert result.report.elapsed_ms > 0


@pytest.mark.asyncio
async def test_export_document_with_task_status(export_service, template_service, sample_html_template):
    """测试导出任务状态跟踪"""
    # 1. 创建模板
    file = await create_upload_file(
        "test_template.html",
        sample_html_template.encode("utf-8"),
        "text/html"
    )
    
    metadata = {
        "name": "测试模板",
        "description": "用于测试任务状态",
        "tags": ["test"],
        "version": "1.0.0"
    }
    
    template = await template_service.create_template(file, metadata)
    template_id = template.template_id
    
    # 2. 执行导出
    request = ExportRequest(
        data={
            "title": "测试标题",
            "heading": "测试大标题",
            "content": "这是测试内容"
        },
        template_ref=template_id,
        output_format="html"
    )
    
    result = await export_service.export_document(request)
    task_id = result.task_id
    
    # 3. 查询任务状态
    task_status = export_service.get_task_status(task_id)
    
    # 4. 验证任务状态
    assert task_status is not None
    assert task_status.task_id == task_id
    assert task_status.status == TaskStatus.COMPLETED
    assert task_status.progress == 100
    assert task_status.message == "导出完成"
    assert task_status.file_path is not None
    assert task_status.file_url is not None
    assert task_status.file_size > 0
    assert task_status.created_at is not None
    assert task_status.completed_at is not None


@pytest.mark.asyncio
async def test_get_task_status_not_found(export_service):
    """测试查询不存在的任务"""
    with pytest.raises(FileNotFoundError, match="任务不存在"):
        export_service.get_task_status("non_existent_task_id")


@pytest.mark.asyncio
async def test_download_file(export_service, template_service, sample_html_template):
    """测试文件下载"""
    # 1. 创建模板并导出
    file = await create_upload_file(
        "test_template.html",
        sample_html_template.encode("utf-8"),
        "text/html"
    )
    
    metadata = {
        "name": "测试模板",
        "description": "用于测试文件下载",
        "tags": ["test"],
        "version": "1.0.0"
    }
    
    template = await template_service.create_template(file, metadata)
    template_id = template.template_id
    
    request = ExportRequest(
        data={
            "title": "测试标题",
            "heading": "测试大标题",
            "content": "这是测试内容"
        },
        template_ref=template_id,
        output_format="html"
    )
    
    result = await export_service.export_document(request)
    file_id = result.file_id
    
    # 2. 下载文件
    file_content = export_service.download_file(file_id)
    
    # 3. 验证文件内容
    assert file_content is not None
    assert len(file_content) > 0
    assert "测试标题".encode("utf-8") in file_content
    assert "测试大标题".encode("utf-8") in file_content


@pytest.mark.asyncio
async def test_download_file_not_found(export_service):
    """测试下载不存在的文件"""
    with pytest.raises(FileNotFoundError):
        export_service.download_file("non_existent_file.html")


@pytest.mark.asyncio
async def test_generate_report(export_service, template_service, sample_html_template):
    """测试生成导出报告"""
    # 1. 创建模板并导出
    file = await create_upload_file(
        "test_template.html",
        sample_html_template.encode("utf-8"),
        "text/html"
    )
    
    metadata = {
        "name": "测试模板",
        "description": "用于测试报告生成",
        "tags": ["test"],
        "version": "1.0.0"
    }
    
    template = await template_service.create_template(file, metadata)
    template_id = template.template_id
    
    request = ExportRequest(
        data={
            "title": "测试标题",
            "heading": "测试大标题",
            "content": "这是测试内容"
        },
        template_ref=template_id,
        output_format="html"
    )
    
    result = await export_service.export_document(request)
    task_id = result.task_id
    
    # 2. 生成报告
    report = export_service.generate_report(task_id)
    
    # 3. 验证报告
    assert report is not None
    assert report["task_id"] == task_id
    assert report["status"] == TaskStatus.COMPLETED
    assert report["progress"] == 100
    assert report["message"] == "导出完成"
    assert "file_path" in report
    assert "file_url" in report
    assert "file_size" in report
    assert report["created_at"] is not None
    assert report["completed_at"] is not None


@pytest.mark.asyncio
async def test_export_with_invalid_template(export_service):
    """测试使用无效模板导出"""
    request = ExportRequest(
        data={
            "title": "测试标题",
            "content": "测试内容"
        },
        template_ref="non_existent_template_id",
        output_format="html"
    )
    
    with pytest.raises(FileNotFoundError):
        await export_service.export_document(request)


@pytest.mark.asyncio
async def test_export_with_multiple_formats(export_service, template_service, sample_html_template):
    """测试导出多种格式"""
    # 1. 创建模板
    file = await create_upload_file(
        "test_template.html",
        sample_html_template.encode("utf-8"),
        "text/html"
    )
    
    metadata = {
        "name": "测试模板",
        "description": "用于测试多格式导出",
        "tags": ["test"],
        "version": "1.0.0"
    }
    
    template = await template_service.create_template(file, metadata)
    template_id = template.template_id
    
    # 2. 测试导出HTML格式
    request_html = ExportRequest(
        data={
            "title": "HTML测试",
            "heading": "HTML标题",
            "content": "HTML内容"
        },
        template_ref=template_id,
        output_format="html"
    )
    
    result_html = await export_service.export_document(request_html)
    assert result_html is not None
    assert ".html" in result_html.file_id


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])

