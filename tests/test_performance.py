"""
性能优化模块单元测试
测试资源管理、异步文件处理、并发控制等功能
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from functools import partial

from core.performance.resource_manager import (
    ResourceManager,
    managed_temp_file,
    managed_temp_directory,
    managed_temp_file_sync,
    managed_temp_directory_sync
)
from core.performance.async_file import AsyncFileProcessor
from core.performance.concurrency import (
    ConcurrencyController,
    get_concurrency_controller,
    run_concurrent_coroutines
)


# ========================================
# 资源管理器测试
# ========================================

class TestResourceManager:
    """资源管理器测试"""
    
    def test_resource_manager_init(self):
        """测试资源管理器初始化"""
        rm = ResourceManager()
        assert rm.open_files == []
        assert rm.temp_files == []
        assert rm.temp_dirs == []
    
    def test_register_file(self):
        """测试注册文件句柄"""
        rm = ResourceManager()
        temp_file = tempfile.NamedTemporaryFile(delete=False)
        
        rm.register_file(temp_file)
        assert len(rm.open_files) == 1
        assert rm.open_files[0] == temp_file
        
        # 清理
        rm.cleanup()
        assert len(rm.open_files) == 0
        Path(temp_file.name).unlink()
    
    def test_register_temp_file(self):
        """测试注册临时文件"""
        rm = ResourceManager()
        temp_path = Path(tempfile.mktemp())
        temp_path.write_text("test")
        
        rm.register_temp_file(str(temp_path))
        assert len(rm.temp_files) == 1
        assert rm.temp_files[0] == temp_path
        
        # 清理
        rm.cleanup()
        assert len(rm.temp_files) == 0
        assert not temp_path.exists()
    
    def test_register_temp_directory(self):
        """测试注册临时目录"""
        rm = ResourceManager()
        temp_dir = Path(tempfile.mkdtemp())
        
        rm.register_temp_directory(str(temp_dir))
        assert len(rm.temp_dirs) == 1
        assert rm.temp_dirs[0] == temp_dir
        
        # 清理
        rm.cleanup()
        assert len(rm.temp_dirs) == 0
        assert not temp_dir.exists()
    
    def test_context_manager(self):
        """测试上下文管理器"""
        temp_path = Path(tempfile.mktemp())
        temp_path.write_text("test")
        
        with ResourceManager() as rm:
            rm.register_temp_file(str(temp_path))
            assert temp_path.exists()
        
        # 退出上下文后自动清理
        assert not temp_path.exists()
    
    @pytest.mark.asyncio
    async def test_managed_temp_file(self):
        """测试临时文件上下文管理器"""
        temp_path_str = None
        
        async with managed_temp_file(suffix='.txt') as temp_file:
            temp_path_str = temp_file
            temp_path = Path(temp_file)
            assert temp_path.exists()
            
            # 写入数据
            temp_path.write_text("test data")
            assert temp_path.read_text() == "test data"
        
        # 退出上下文后自动删除
        assert not Path(temp_path_str).exists()
    
    @pytest.mark.asyncio
    async def test_managed_temp_directory(self):
        """测试临时目录上下文管理器"""
        temp_dir_str = None
        
        async with managed_temp_directory() as temp_dir:
            temp_dir_str = temp_dir
            temp_path = Path(temp_dir)
            assert temp_path.exists()
            assert temp_path.is_dir()
            
            # 创建文件
            test_file = temp_path / "test.txt"
            test_file.write_text("test")
            assert test_file.exists()
        
        # 退出上下文后自动删除
        assert not Path(temp_dir_str).exists()
    
    def test_managed_temp_file_sync(self):
        """测试同步临时文件上下文管理器"""
        temp_path_str = None
        
        with managed_temp_file_sync(suffix='.txt') as temp_file:
            temp_path_str = temp_file
            temp_path = Path(temp_file)
            assert temp_path.exists()
            
            # 写入数据
            temp_path.write_text("test data")
            assert temp_path.read_text() == "test data"
        
        # 退出上下文后自动删除
        assert not Path(temp_path_str).exists()
    
    def test_managed_temp_directory_sync(self):
        """测试同步临时目录上下文管理器"""
        temp_dir_str = None
        
        with managed_temp_directory_sync() as temp_dir:
            temp_dir_str = temp_dir
            temp_path = Path(temp_dir)
            assert temp_path.exists()
            assert temp_path.is_dir()
            
            # 创建文件
            test_file = temp_path / "test.txt"
            test_file.write_text("test")
            assert test_file.exists()
        
        # 退出上下文后自动删除
        assert not Path(temp_dir_str).exists()


# ========================================
# 异步文件处理器测试
# ========================================

class TestAsyncFileProcessor:
    """异步文件处理器测试"""
    
    @pytest.mark.asyncio
    async def test_read_write_file(self):
        """测试异步读写文本文件"""
        async with managed_temp_file(suffix='.txt') as temp_file:
            # 写入
            content = "这是测试内容\n第二行"
            await AsyncFileProcessor.write_file(temp_file, content)
            
            # 读取
            read_content = await AsyncFileProcessor.read_file(temp_file)
            assert read_content == content
    
    @pytest.mark.asyncio
    async def test_read_write_binary(self):
        """测试异步读写二进制文件"""
        async with managed_temp_file(suffix='.bin') as temp_file:
            # 写入
            content = b"\x00\x01\x02\x03\x04\x05"
            await AsyncFileProcessor.write_binary(temp_file, content)
            
            # 读取
            read_content = await AsyncFileProcessor.read_binary(temp_file)
            assert read_content == content
    
    @pytest.mark.asyncio
    async def test_copy_file(self):
        """测试异步复制文件"""
        async with managed_temp_file(suffix='.txt') as src_file:
            async with managed_temp_file(suffix='.txt') as dst_file:
                # 写入源文件
                content = "test content"
                await AsyncFileProcessor.write_file(src_file, content)
                
                # 复制
                await AsyncFileProcessor.copy_file(src_file, dst_file)
                
                # 验证
                dst_content = await AsyncFileProcessor.read_file(dst_file)
                assert dst_content == content
    
    @pytest.mark.asyncio
    async def test_read_chunked(self):
        """测试分块读取文件"""
        async with managed_temp_file(suffix='.txt') as temp_file:
            # 写入测试数据
            content = "abcdefghij" * 100  # 1000字节
            await AsyncFileProcessor.write_file(temp_file, content)
            
            # 分块读取
            chunks = []
            async for chunk in AsyncFileProcessor.read_chunked(temp_file, chunk_size=100):
                chunks.append(chunk)
            
            # 验证
            assert len(chunks) == 10
            assert b"".join(chunks).decode('utf-8') == content
    
    @pytest.mark.asyncio
    async def test_write_chunked(self):
        """测试分块写入文件"""
        async def data_generator():
            for i in range(10):
                yield f"chunk{i}\n".encode('utf-8')
        
        async with managed_temp_file(suffix='.txt') as temp_file:
            # 分块写入
            bytes_written = await AsyncFileProcessor.write_chunked(
                temp_file,
                data_generator()
            )
            
            # 验证
            assert bytes_written > 0
            content = await AsyncFileProcessor.read_file(temp_file)
            assert "chunk0" in content
            assert "chunk9" in content
    
    @pytest.mark.asyncio
    async def test_get_file_size(self):
        """测试获取文件大小"""
        async with managed_temp_file(suffix='.txt') as temp_file:
            content = "test" * 100
            await AsyncFileProcessor.write_file(temp_file, content)
            
            size = await AsyncFileProcessor.get_file_size(temp_file)
            assert size == len(content.encode('utf-8'))
    
    @pytest.mark.asyncio
    async def test_is_large_file(self):
        """测试判断是否为大文件"""
        async with managed_temp_file(suffix='.txt') as temp_file:
            # 小文件
            await AsyncFileProcessor.write_file(temp_file, "test")
            is_large = await AsyncFileProcessor.is_large_file(temp_file)
            assert not is_large
    
    @pytest.mark.asyncio
    async def test_append_file(self):
        """测试追加文件"""
        async with managed_temp_file(suffix='.txt') as temp_file:
            # 写入初始内容
            await AsyncFileProcessor.write_file(temp_file, "line1\n")
            
            # 追加内容
            await AsyncFileProcessor.append_file(temp_file, "line2\n")
            await AsyncFileProcessor.append_file(temp_file, "line3\n")
            
            # 验证
            content = await AsyncFileProcessor.read_file(temp_file)
            assert content == "line1\nline2\nline3\n"
    
    @pytest.mark.asyncio
    async def test_file_not_found(self):
        """测试文件不存在的情况"""
        with pytest.raises(FileNotFoundError):
            await AsyncFileProcessor.read_file("nonexistent_file.txt")
    
    @pytest.mark.asyncio
    async def test_process_file_chunked(self):
        """测试分块处理文件"""
        async with managed_temp_file(suffix='.txt') as temp_file:
            # 写入测试数据
            content = "line\n" * 100
            await AsyncFileProcessor.write_file(temp_file, content)
            
            # 定义处理函数：计算每个块中的换行符数量
            def count_newlines(chunk: bytes) -> int:
                return chunk.count(b'\n')
            
            # 分块处理
            results = await AsyncFileProcessor.process_file_chunked(
                temp_file,
                count_newlines,
                chunk_size=100
            )
            
            # 验证
            total_lines = sum(results)
            assert total_lines == 100


# ========================================
# 并发控制器测试
# ========================================

class TestConcurrencyController:
    """并发控制器测试"""
    
    def test_init(self):
        """测试初始化"""
        controller = ConcurrencyController(
            thread_workers=4,
            process_workers=2,
            async_concurrency=10
        )
        
        assert controller.thread_workers == 4
        assert controller.process_workers == 2
        assert controller.async_concurrency == 10
    
    def test_init_with_limits(self):
        """测试初始化时的限制"""
        controller = ConcurrencyController(
            thread_workers=100,  # 超过最大值
            process_workers=100,  # 超过最大值
            async_concurrency=200  # 超过最大值
        )
        
        assert controller.thread_workers == ConcurrencyController.MAX_THREAD_WORKERS
        assert controller.process_workers == ConcurrencyController.MAX_PROCESS_WORKERS
        assert controller.async_concurrency == ConcurrencyController.MAX_ASYNC_CONCURRENCY
    
    @pytest.mark.asyncio
    async def test_run_in_threadpool(self):
        """测试线程池执行"""
        controller = ConcurrencyController(thread_workers=4)
        
        def task(n):
            return n * 2
        
        tasks = [partial(task, i) for i in range(10)]
        results = await controller.run_in_threadpool(tasks)
        
        assert len(results) == 10
        assert results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
    
    @pytest.mark.asyncio
    async def test_run_with_semaphore(self):
        """测试信号量控制"""
        controller = ConcurrencyController(async_concurrency=5)
        
        async def task(n):
            await asyncio.sleep(0.01)
            return n * 2
        
        coroutines = [task(i) for i in range(10)]
        results = await controller.run_with_semaphore(coroutines)
        
        assert len(results) == 10
        assert results == [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]
    
    @pytest.mark.asyncio
    async def test_map_threadpool(self):
        """测试线程池映射"""
        controller = ConcurrencyController(thread_workers=4)
        
        def process(n):
            return n ** 2
        
        items = list(range(10))
        results = await controller.map_threadpool(process, items)
        
        assert len(results) == 10
        assert results == [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
    
    @pytest.mark.asyncio
    async def test_batch_process(self):
        """测试分批处理"""
        controller = ConcurrencyController(async_concurrency=5)
        
        async def processor(item):
            await asyncio.sleep(0.01)
            return item * 2
        
        items = list(range(20))
        results = await controller.batch_process(
            items,
            processor,
            batch_size=5,
            max_concurrent=3
        )
        
        assert len(results) == 20
        assert results == [i * 2 for i in range(20)]
    
    def test_get_global_controller(self):
        """测试获取全局控制器"""
        controller1 = get_concurrency_controller()
        controller2 = get_concurrency_controller()
        
        # 应该是同一个实例
        assert controller1 is controller2
    
    @pytest.mark.asyncio
    async def test_run_concurrent_coroutines(self):
        """测试并发执行协程便捷函数"""
        async def task(n):
            await asyncio.sleep(0.01)
            return n * 3
        
        coroutines = [task(i) for i in range(10)]
        results = await run_concurrent_coroutines(coroutines, max_concurrent=5)
        
        assert len(results) == 10
        assert results == [i * 3 for i in range(10)]


# ========================================
# 集成测试
# ========================================

class TestIntegration:
    """集成测试"""
    
    @pytest.mark.asyncio
    async def test_resource_manager_with_async_file(self):
        """测试资源管理器与异步文件处理的集成"""
        with ResourceManager() as rm:
            # 创建临时文件
            async with managed_temp_file(suffix='.txt') as temp_file:
                rm.register_temp_file(temp_file)
                
                # 异步写入
                await AsyncFileProcessor.write_file(temp_file, "test")
                
                # 异步读取
                content = await AsyncFileProcessor.read_file(temp_file)
                assert content == "test"
    
    @pytest.mark.asyncio
    async def test_concurrent_file_processing(self):
        """测试并发文件处理"""
        controller = ConcurrencyController(async_concurrency=5)
        
        # 创建多个临时文件
        temp_files = []
        for i in range(5):
            temp_file = Path(tempfile.mktemp(suffix='.txt'))
            await AsyncFileProcessor.write_file(str(temp_file), f"content{i}")
            temp_files.append(temp_file)
        
        try:
            # 并发读取所有文件
            async def read_file(path):
                return await AsyncFileProcessor.read_file(str(path))
            
            coroutines = [read_file(f) for f in temp_files]
            results = await controller.run_with_semaphore(coroutines)
            
            # 验证
            assert len(results) == 5
            for i, content in enumerate(results):
                assert content == f"content{i}"
        
        finally:
            # 清理临时文件
            for temp_file in temp_files:
                if temp_file.exists():
                    temp_file.unlink()

