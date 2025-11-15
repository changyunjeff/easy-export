"""
文件服务单元测试
测试文件上传、下载、列表查询、删除等功能
"""

import io
import pytest
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

from fastapi import UploadFile

from core.service.file_service import FileService
from core.storage.file_storage import FileStorage


@pytest.fixture
def temp_dir():
    """创建临时目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def file_storage(temp_dir):
    """创建文件存储实例"""
    return FileStorage(base_path=temp_dir)


@pytest.fixture
def file_service(file_storage):
    """创建文件服务实例"""
    return FileService(file_storage=file_storage)


def create_upload_file(filename: str, content: bytes) -> UploadFile:
    """创建UploadFile对象"""
    file = UploadFile(
        filename=filename,
        file=io.BytesIO(content),
    )
    # Mock read方法
    file.read = AsyncMock(return_value=content)
    return file


class TestFileService:
    """文件服务测试类"""
    
    @pytest.mark.asyncio
    async def test_upload_file_success(self, file_service):
        """测试文件上传成功"""
        # 准备测试数据
        filename = "test.pdf"
        content = b"test content for pdf file"
        file = create_upload_file(filename, content)
        
        # 上传文件
        result = await file_service.upload_file(file)
        
        # 验证结果
        assert result["file_name"] == filename
        assert result["file_size"] == len(content)
        assert "file_id" in result
        assert "file_path" in result
        assert "file_url" in result
        assert "created_at" in result
        
        # 验证文件已保存
        file_id = result["file_id"]
        assert file_service.exists(file_id)
    
    @pytest.mark.asyncio
    async def test_upload_file_empty(self, file_service):
        """测试上传空文件失败"""
        file = create_upload_file("empty.txt", b"")
        
        with pytest.raises(ValueError, match="文件不能为空"):
            await file_service.upload_file(file)
    
    @pytest.mark.asyncio
    async def test_upload_file_no_filename(self, file_service):
        """测试上传无文件名失败"""
        file = create_upload_file("", b"content")
        
        with pytest.raises(ValueError, match="文件名不能为空"):
            await file_service.upload_file(file)
    
    @pytest.mark.asyncio
    async def test_upload_file_too_large(self, file_service):
        """测试上传文件过大失败"""
        # 创建1MB的文件
        content = b"x" * (1024 * 1024)
        file = create_upload_file("large.pdf", content)
        
        # 限制最大文件大小为1KB
        max_size = 1024
        
        with pytest.raises(ValueError, match="文件大小.*超过限制"):
            await file_service.upload_file(file, max_size=max_size)
    
    @pytest.mark.asyncio
    async def test_upload_file_with_extension(self, file_service):
        """测试上传不同扩展名的文件"""
        test_cases = [
            ("test.pdf", b"pdf content"),
            ("test.docx", b"docx content"),
            ("test.html", b"<html></html>"),
            ("test.png", b"png binary data"),
        ]
        
        for filename, content in test_cases:
            file = create_upload_file(filename, content)
            result = await file_service.upload_file(file)
            
            # 验证文件ID包含正确的扩展名
            file_id = result["file_id"]
            assert file_id.endswith(Path(filename).suffix)
    
    @pytest.mark.asyncio
    async def test_download_file_success(self, file_service):
        """测试下载文件成功"""
        # 先上传文件
        filename = "test.txt"
        content = b"test content"
        file = create_upload_file(filename, content)
        upload_result = await file_service.upload_file(file)
        file_id = upload_result["file_id"]
        
        # 下载文件
        downloaded_content = file_service.download_file(file_id)
        
        # 验证内容一致
        assert downloaded_content == content
    
    def test_download_file_not_found(self, file_service):
        """测试下载不存在的文件失败"""
        with pytest.raises(FileNotFoundError):
            file_service.download_file("nonexistent.pdf")
    
    @pytest.mark.asyncio
    async def test_get_file_info_success(self, file_service):
        """测试获取文件信息成功"""
        # 先上传文件
        filename = "test.txt"
        content = b"test content"
        file = create_upload_file(filename, content)
        upload_result = await file_service.upload_file(file)
        file_id = upload_result["file_id"]
        
        # 获取文件信息
        file_info = file_service.get_file_info(file_id)
        
        # 验证信息
        assert file_info["file_id"] == file_id
        assert file_info["file_name"] == filename
        assert file_info["file_size"] == len(content)
        assert "file_url" in file_info
        assert "hash" in file_info
        assert "created_at" in file_info
    
    def test_get_file_info_not_found(self, file_service):
        """测试获取不存在文件的信息失败"""
        with pytest.raises(FileNotFoundError):
            file_service.get_file_info("nonexistent.pdf")
    
    @pytest.mark.asyncio
    async def test_list_files_empty(self, file_service):
        """测试列表查询空结果"""
        result = file_service.list_files()
        
        assert result["total"] == 0
        assert result["page"] == 1
        assert result["page_size"] == 20
        assert result["items"] == []
    
    @pytest.mark.asyncio
    async def test_list_files_with_data(self, file_service):
        """测试列表查询有数据"""
        # 上传多个文件
        files = [
            ("test1.pdf", b"content1"),
            ("test2.docx", b"content2"),
            ("test3.html", b"content3"),
        ]
        
        for filename, content in files:
            file = create_upload_file(filename, content)
            await file_service.upload_file(file)
        
        # 查询文件列表
        result = file_service.list_files()
        
        assert result["total"] == 3
        assert len(result["items"]) == 3
    
    @pytest.mark.asyncio
    async def test_list_files_with_name_filter(self, file_service):
        """测试按文件名过滤"""
        # 上传多个文件
        files = [
            ("report1.pdf", b"content1"),
            ("report2.pdf", b"content2"),
            ("test.html", b"content3"),
        ]
        
        for filename, content in files:
            file = create_upload_file(filename, content)
            await file_service.upload_file(file)
        
        # 按文件名过滤
        result = file_service.list_files(filters={"name": "report"})
        
        assert result["total"] == 2
        assert all("report" in item["file_name"].lower() for item in result["items"])
    
    @pytest.mark.asyncio
    async def test_list_files_with_extension_filter(self, file_service):
        """测试按扩展名过滤"""
        # 上传多个文件
        files = [
            ("test1.pdf", b"content1"),
            ("test2.pdf", b"content2"),
            ("test3.html", b"content3"),
        ]
        
        for filename, content in files:
            file = create_upload_file(filename, content)
            await file_service.upload_file(file)
        
        # 按扩展名过滤
        result = file_service.list_files(filters={"extension": ".pdf"})
        
        assert result["total"] == 2
        assert all(item["file_name"].endswith(".pdf") for item in result["items"])
    
    @pytest.mark.asyncio
    async def test_list_files_pagination(self, file_service):
        """测试分页查询"""
        # 上传5个文件
        for i in range(5):
            file = create_upload_file(f"test{i}.txt", f"content{i}".encode())
            await file_service.upload_file(file)
        
        # 第一页（每页2个）
        result = file_service.list_files(page=1, page_size=2)
        assert result["total"] == 5
        assert len(result["items"]) == 2
        
        # 第二页
        result = file_service.list_files(page=2, page_size=2)
        assert result["total"] == 5
        assert len(result["items"]) == 2
        
        # 第三页
        result = file_service.list_files(page=3, page_size=2)
        assert result["total"] == 5
        assert len(result["items"]) == 1
    
    @pytest.mark.asyncio
    async def test_delete_file_success(self, file_service):
        """测试删除文件成功"""
        # 先上传文件
        file = create_upload_file("test.txt", b"content")
        upload_result = await file_service.upload_file(file)
        file_id = upload_result["file_id"]
        
        # 验证文件存在
        assert file_service.exists(file_id)
        
        # 删除文件
        result = file_service.delete_file(file_id)
        assert result is True
        
        # 验证文件已删除
        assert not file_service.exists(file_id)
    
    def test_delete_file_not_found(self, file_service):
        """测试删除不存在的文件失败"""
        with pytest.raises(FileNotFoundError):
            file_service.delete_file("nonexistent.pdf")
    
    @pytest.mark.asyncio
    async def test_cleanup_old_files(self, file_service):
        """测试清理过期文件"""
        # 上传文件
        file = create_upload_file("test.txt", b"content")
        upload_result = await file_service.upload_file(file)
        file_id = upload_result["file_id"]
        
        # 修改文件的元数据，使其看起来是7天前创建的
        file_path = file_service.file_storage.get_file_path(file_id)
        metadata = file_service.file_storage._load_metadata(file_path)
        old_time = datetime.now(timezone.utc) - timedelta(days=8)
        metadata["saved_at"] = old_time.isoformat()
        metadata["saved_at_ts"] = old_time.timestamp()
        file_service.file_storage._write_json(
            file_service.file_storage._metadata_path(file_path),
            metadata
        )
        
        # 清理7天前的文件
        older_than = datetime.now(timezone.utc) - timedelta(days=7)
        count = file_service.cleanup_old_files(older_than)
        
        # 验证文件已被清理
        assert count == 1
        assert not file_service.exists(file_id)
    
    @pytest.mark.asyncio
    async def test_get_file_url(self, file_service):
        """测试获取文件URL"""
        # 先上传文件
        file = create_upload_file("test.txt", b"content")
        upload_result = await file_service.upload_file(file)
        file_id = upload_result["file_id"]
        
        # 获取文件URL
        file_url = file_service.get_file_url(file_id)
        
        # 验证URL格式
        assert file_id in file_url
    
    def test_get_file_url_not_found(self, file_service):
        """测试获取不存在文件的URL失败"""
        with pytest.raises(FileNotFoundError):
            file_service.get_file_url("nonexistent.pdf")
    
    @pytest.mark.asyncio
    async def test_exists(self, file_service):
        """测试检查文件是否存在"""
        # 先上传文件
        file = create_upload_file("test.txt", b"content")
        upload_result = await file_service.upload_file(file)
        file_id = upload_result["file_id"]
        
        # 验证文件存在
        assert file_service.exists(file_id)
        
        # 验证不存在的文件
        assert not file_service.exists("nonexistent.pdf")
    
    def test_generate_file_id(self, file_service):
        """测试生成文件ID"""
        # 测试带扩展名的文件
        file_id = file_service._generate_file_id("test.pdf")
        assert file_id.endswith(".pdf")
        assert len(file_id) > 4  # UUID部分 + 扩展名
        
        # 测试无扩展名的文件
        file_id = file_service._generate_file_id("test")
        assert len(file_id) == 12  # 仅UUID部分
    
    def test_match_filters(self, file_service):
        """测试过滤条件匹配"""
        file_info = {
            "file_name": "report.pdf",
            "file_size": 1024,
            "created_at": "2024-01-01T00:00:00Z",
        }
        
        # 测试文件名过滤
        assert file_service._match_filters(file_info, {"name": "report"})
        assert not file_service._match_filters(file_info, {"name": "test"})
        
        # 测试扩展名过滤
        assert file_service._match_filters(file_info, {"extension": ".pdf"})
        assert not file_service._match_filters(file_info, {"extension": ".docx"})
        
        # 测试创建时间过滤
        assert file_service._match_filters(
            file_info,
            {"created_after": "2023-01-01T00:00:00Z"}
        )
        assert not file_service._match_filters(
            file_info,
            {"created_after": "2025-01-01T00:00:00Z"}
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

