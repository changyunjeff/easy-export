"""
性能优化MVP示例
演示异步处理、资源管理、内存优化等性能优化技术

功能演示：
1. 异步文件I/O - 异步读写文件
2. 资源管理 - 自动释放文件句柄和临时资源
3. 内存优化 - 分块处理大文件
4. 并发控制 - 使用线程池/进程池并发处理任务
"""

import asyncio
import aiofiles
import tempfile
import time
from pathlib import Path
from typing import List, Dict, Any, AsyncIterator
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from contextlib import asynccontextmanager
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ========================================
# 1. 异步文件I/O
# ========================================

async def async_read_file(file_path: str) -> str:
    """异步读取文件内容"""
    logger.info(f"异步读取文件: {file_path}")
    start = time.perf_counter()
    
    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as f:
        content = await f.read()
    
    elapsed = time.perf_counter() - start
    logger.info(f"异步读取完成，耗时: {elapsed:.3f}秒，大小: {len(content)} 字节")
    return content


async def async_write_file(file_path: str, content: str) -> None:
    """异步写入文件内容"""
    logger.info(f"异步写入文件: {file_path}")
    start = time.perf_counter()
    
    async with aiofiles.open(file_path, mode='w', encoding='utf-8') as f:
        await f.write(content)
    
    elapsed = time.perf_counter() - start
    logger.info(f"异步写入完成，耗时: {elapsed:.3f}秒，大小: {len(content)} 字节")


async def async_copy_file(src: str, dst: str, chunk_size: int = 4096) -> None:
    """异步复制文件（分块读写）"""
    logger.info(f"异步复制文件: {src} -> {dst} (chunk_size={chunk_size})")
    start = time.perf_counter()
    bytes_copied = 0
    
    async with aiofiles.open(src, mode='rb') as f_src:
        async with aiofiles.open(dst, mode='wb') as f_dst:
            while True:
                chunk = await f_src.read(chunk_size)
                if not chunk:
                    break
                await f_dst.write(chunk)
                bytes_copied += len(chunk)
    
    elapsed = time.perf_counter() - start
    logger.info(f"异步复制完成，耗时: {elapsed:.3f}秒，大小: {bytes_copied} 字节")


async def async_read_file_chunked(file_path: str, chunk_size: int = 4096) -> AsyncIterator[bytes]:
    """异步分块读取文件（内存优化）"""
    logger.info(f"异步分块读取文件: {file_path} (chunk_size={chunk_size})")
    
    async with aiofiles.open(file_path, mode='rb') as f:
        while True:
            chunk = await f.read(chunk_size)
            if not chunk:
                break
            yield chunk


# ========================================
# 2. 资源管理
# ========================================

@asynccontextmanager
async def managed_temp_file(suffix: str = '.tmp', prefix: str = 'easy_export_'):
    """
    管理临时文件的上下文管理器
    确保临时文件在使用后自动删除
    """
    temp_file = None
    try:
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(
            mode='w+b',
            suffix=suffix,
            prefix=prefix,
            delete=False
        )
        logger.info(f"创建临时文件: {temp_file.name}")
        
        yield temp_file.name
        
    finally:
        # 自动清理临时文件
        if temp_file:
            temp_file.close()
            temp_path = Path(temp_file.name)
            if temp_path.exists():
                temp_path.unlink()
                logger.info(f"删除临时文件: {temp_file.name}")


@asynccontextmanager
async def managed_temp_directory():
    """
    管理临时目录的上下文管理器
    确保临时目录在使用后自动删除
    """
    temp_dir = None
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix='easy_export_')
        logger.info(f"创建临时目录: {temp_dir}")
        
        yield temp_dir
        
    finally:
        # 自动清理临时目录
        if temp_dir:
            temp_path = Path(temp_dir)
            if temp_path.exists():
                # 删除目录中的所有文件
                for file_path in temp_path.glob('*'):
                    file_path.unlink()
                # 删除目录
                temp_path.rmdir()
                logger.info(f"删除临时目录: {temp_dir}")


class ResourceManager:
    """
    资源管理器
    自动跟踪和释放资源（文件句柄、临时文件等）
    """
    
    def __init__(self):
        self.open_files: List[Any] = []
        self.temp_files: List[Path] = []
        logger.info("资源管理器已初始化")
    
    def register_file(self, file_obj):
        """注册文件句柄"""
        self.open_files.append(file_obj)
        logger.debug(f"注册文件句柄: {file_obj}")
    
    def register_temp_file(self, file_path: str):
        """注册临时文件"""
        self.temp_files.append(Path(file_path))
        logger.debug(f"注册临时文件: {file_path}")
    
    def cleanup(self):
        """清理所有资源"""
        logger.info("开始清理资源...")
        
        # 关闭所有文件句柄
        for file_obj in self.open_files:
            try:
                if hasattr(file_obj, 'close') and not file_obj.closed:
                    file_obj.close()
                    logger.debug(f"关闭文件句柄: {file_obj}")
            except Exception as e:
                logger.error(f"关闭文件句柄失败: {e}")
        
        self.open_files.clear()
        
        # 删除所有临时文件
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug(f"删除临时文件: {temp_file}")
            except Exception as e:
                logger.error(f"删除临时文件失败: {e}")
        
        self.temp_files.clear()
        logger.info("资源清理完成")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()


# ========================================
# 3. 内存优化
# ========================================

async def process_large_file_chunked(file_path: str, chunk_size: int = 1024 * 1024):
    """
    分块处理大文件（内存优化）
    每次只读取指定大小的数据块，避免内存溢出
    """
    logger.info(f"分块处理大文件: {file_path} (chunk_size={chunk_size / 1024}KB)")
    start = time.perf_counter()
    
    total_size = 0
    chunk_count = 0
    
    # 使用异步迭代器分块读取
    async for chunk in async_read_file_chunked(file_path, chunk_size):
        # 处理数据块（这里只是计数示例）
        chunk_count += 1
        total_size += len(chunk)
        
        # 模拟处理操作（如解析、转换等）
        await asyncio.sleep(0.001)  # 模拟处理耗时
    
    elapsed = time.perf_counter() - start
    logger.info(
        f"分块处理完成 - 总大小: {total_size / 1024:.2f}KB, "
        f"分块数: {chunk_count}, 耗时: {elapsed:.3f}秒"
    )
    return total_size, chunk_count


async def stream_process_files(file_paths: List[str], max_concurrent: int = 5):
    """
    流式处理多个文件（内存优化 + 并发控制）
    限制同时处理的文件数量，避免内存溢出
    """
    logger.info(f"流式处理文件列表（并发数: {max_concurrent}）")
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_limit(file_path: str):
        async with semaphore:
            return await process_large_file_chunked(file_path)
    
    # 并发处理所有文件（但同时最多max_concurrent个）
    results = await asyncio.gather(*[
        process_with_limit(fp) for fp in file_paths
    ])
    
    logger.info(f"流式处理完成，共处理 {len(results)} 个文件")
    return results


# ========================================
# 4. 并发控制
# ========================================

def cpu_intensive_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """CPU密集型任务（如数据处理、图表生成）"""
    task_id = data.get('id', 'unknown')
    logger.info(f"CPU密集型任务开始: {task_id}")
    
    # 模拟CPU密集型操作（如复杂计算、图表渲染）
    result = 0
    for i in range(1000000):
        result += i * i
    
    time.sleep(0.1)  # 模拟耗时操作
    
    logger.info(f"CPU密集型任务完成: {task_id}")
    return {
        'task_id': task_id,
        'result': result,
        'status': 'success'
    }


async def io_intensive_task(data: Dict[str, Any]) -> Dict[str, Any]:
    """I/O密集型任务（如文件读写、网络请求）"""
    task_id = data.get('id', 'unknown')
    logger.info(f"I/O密集型任务开始: {task_id}")
    
    # 模拟I/O密集型操作（如文件读写）
    await asyncio.sleep(0.5)
    
    logger.info(f"I/O密集型任务完成: {task_id}")
    return {
        'task_id': task_id,
        'status': 'success'
    }


async def concurrent_process_with_threadpool(
    tasks: List[Dict[str, Any]],
    max_workers: int = 8
) -> List[Dict[str, Any]]:
    """
    使用线程池并发处理CPU密集型任务
    适用于CPU密集型任务（如图表生成、数据处理）
    """
    logger.info(f"使用线程池并发处理 {len(tasks)} 个任务（workers: {max_workers}）")
    start = time.perf_counter()
    
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 将CPU密集型任务提交到线程池
        results = await asyncio.gather(*[
            loop.run_in_executor(executor, cpu_intensive_task, task)
            for task in tasks
        ])
    
    elapsed = time.perf_counter() - start
    logger.info(f"线程池并发处理完成，耗时: {elapsed:.3f}秒")
    return results


async def concurrent_process_with_processpool(
    tasks: List[Dict[str, Any]],
    max_workers: int = 4
) -> List[Dict[str, Any]]:
    """
    使用进程池并发处理CPU密集型任务
    适用于CPU密集型任务（比线程池更适合Python的GIL限制）
    """
    logger.info(f"使用进程池并发处理 {len(tasks)} 个任务（workers: {max_workers}）")
    start = time.perf_counter()
    
    loop = asyncio.get_event_loop()
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # 将CPU密集型任务提交到进程池
        results = await asyncio.gather(*[
            loop.run_in_executor(executor, cpu_intensive_task, task)
            for task in tasks
        ])
    
    elapsed = time.perf_counter() - start
    logger.info(f"进程池并发处理完成，耗时: {elapsed:.3f}秒")
    return results


async def concurrent_process_io_tasks(
    tasks: List[Dict[str, Any]],
    max_concurrent: int = 50
) -> List[Dict[str, Any]]:
    """
    并发处理I/O密集型任务
    使用asyncio的Semaphore控制并发数
    """
    logger.info(f"并发处理 {len(tasks)} 个I/O任务（并发数: {max_concurrent}）")
    start = time.perf_counter()
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_with_limit(task: Dict[str, Any]):
        async with semaphore:
            return await io_intensive_task(task)
    
    results = await asyncio.gather(*[
        process_with_limit(task) for task in tasks
    ])
    
    elapsed = time.perf_counter() - start
    logger.info(f"I/O任务并发处理完成，耗时: {elapsed:.3f}秒")
    return results


# ========================================
# 主测试函数
# ========================================

async def demo_async_io():
    """演示异步文件I/O"""
    logger.info("\n========== 演示1: 异步文件I/O ==========")
    
    # 创建测试文件
    test_file = "test_async.txt"
    test_content = "这是一个异步I/O测试文件\n" * 1000
    
    # 异步写入
    await async_write_file(test_file, test_content)
    
    # 异步读取
    content = await async_read_file(test_file)
    logger.info(f"读取的内容长度: {len(content)} 字节")
    
    # 异步复制
    await async_copy_file(test_file, "test_async_copy.txt")
    
    # 清理测试文件
    Path(test_file).unlink()
    Path("test_async_copy.txt").unlink()


async def demo_resource_management():
    """演示资源管理"""
    logger.info("\n========== 演示2: 资源管理 ==========")
    
    # 使用临时文件上下文管理器
    async with managed_temp_file(suffix='.txt') as temp_file:
        logger.info(f"使用临时文件: {temp_file}")
        async with aiofiles.open(temp_file, 'w') as f:
            await f.write("临时数据")
    # 临时文件自动删除
    
    # 使用资源管理器
    with ResourceManager() as rm:
        # 创建临时文件
        temp_path = Path(tempfile.mktemp(suffix='.txt'))
        temp_path.write_text("测试数据")
        rm.register_temp_file(str(temp_path))
        
        # 打开文件
        f = open(temp_path, 'r')
        rm.register_file(f)
        
        logger.info(f"资源管理器跟踪中: {len(rm.open_files)} 个文件句柄, {len(rm.temp_files)} 个临时文件")
    # 退出时自动清理


async def demo_memory_optimization():
    """演示内存优化"""
    logger.info("\n========== 演示3: 内存优化 ==========")
    
    # 创建大测试文件
    test_file = "test_large.txt"
    with open(test_file, 'w') as f:
        for i in range(10000):
            f.write(f"这是第 {i} 行数据\n" * 10)
    
    # 分块处理大文件
    total_size, chunk_count = await process_large_file_chunked(test_file, chunk_size=4096)
    logger.info(f"处理完成: {total_size} 字节, {chunk_count} 个分块")
    
    # 清理测试文件
    Path(test_file).unlink()


async def demo_concurrency_control():
    """演示并发控制"""
    logger.info("\n========== 演示4: 并发控制 ==========")
    
    # 准备测试任务
    cpu_tasks = [{'id': f'cpu_task_{i}'} for i in range(10)]
    io_tasks = [{'id': f'io_task_{i}'} for i in range(20)]
    
    # 线程池处理CPU密集型任务
    logger.info("\n--- 线程池处理 ---")
    results1 = await concurrent_process_with_threadpool(cpu_tasks, max_workers=4)
    logger.info(f"线程池处理结果: {len(results1)} 个任务完成")
    
    # 并发处理I/O密集型任务
    logger.info("\n--- I/O并发处理 ---")
    results2 = await concurrent_process_io_tasks(io_tasks, max_concurrent=10)
    logger.info(f"I/O并发处理结果: {len(results2)} 个任务完成")


async def main():
    """主函数"""
    logger.info("========================================")
    logger.info("性能优化MVP示例")
    logger.info("========================================")
    
    # 演示1: 异步文件I/O
    await demo_async_io()
    
    # 演示2: 资源管理
    await demo_resource_management()
    
    # 演示3: 内存优化
    await demo_memory_optimization()
    
    # 演示4: 并发控制
    await demo_concurrency_control()
    
    logger.info("\n========================================")
    logger.info("所有演示完成！")
    logger.info("========================================")


if __name__ == "__main__":
    asyncio.run(main())

