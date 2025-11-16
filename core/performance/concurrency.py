"""
并发控制器模块
提供线程池、进程池、并发限制等功能
"""

import asyncio
import logging
from typing import Any, Callable, List, Optional, TypeVar, Coroutine
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from functools import partial

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ConcurrencyController:
    """
    并发控制器
    提供线程池、进程池、并发限制等功能
    """
    
    # 默认配置
    DEFAULT_THREAD_WORKERS = 8
    DEFAULT_PROCESS_WORKERS = 4
    DEFAULT_ASYNC_CONCURRENCY = 50
    MAX_THREAD_WORKERS = 50
    MAX_PROCESS_WORKERS = 16
    MAX_ASYNC_CONCURRENCY = 100
    
    def __init__(
        self,
        thread_workers: Optional[int] = None,
        process_workers: Optional[int] = None,
        async_concurrency: Optional[int] = None
    ):
        """
        初始化并发控制器
        
        Args:
            thread_workers: 线程池工作线程数（默认8）
            process_workers: 进程池工作进程数（默认4）
            async_concurrency: 异步并发数（默认50）
        """
        self.thread_workers = min(
            thread_workers or self.DEFAULT_THREAD_WORKERS,
            self.MAX_THREAD_WORKERS
        )
        self.process_workers = min(
            process_workers or self.DEFAULT_PROCESS_WORKERS,
            self.MAX_PROCESS_WORKERS
        )
        self.async_concurrency = min(
            async_concurrency or self.DEFAULT_ASYNC_CONCURRENCY,
            self.MAX_ASYNC_CONCURRENCY
        )
        
        logger.info(
            f"ConcurrencyController initialized - "
            f"thread_workers={self.thread_workers}, "
            f"process_workers={self.process_workers}, "
            f"async_concurrency={self.async_concurrency}"
        )
    
    async def run_in_threadpool(
        self,
        tasks: List[Callable[[], T]],
        max_workers: Optional[int] = None
    ) -> List[T]:
        """
        在线程池中并发执行任务
        适用于I/O密集型任务（如文件读写、网络请求）
        
        Args:
            tasks: 任务列表（可调用对象列表）
            max_workers: 最大工作线程数（默认使用self.thread_workers）
        
        Returns:
            任务结果列表
        
        Example:
            def read_file(path):
                with open(path) as f:
                    return f.read()
            
            tasks = [partial(read_file, f"file_{i}.txt") for i in range(10)]
            results = await controller.run_in_threadpool(tasks)
        """
        max_workers = min(
            max_workers or self.thread_workers,
            self.MAX_THREAD_WORKERS
        )
        
        logger.info(f"Running {len(tasks)} tasks in thread pool (max_workers={max_workers})")
        
        loop = asyncio.get_event_loop()
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [loop.run_in_executor(executor, task) for task in tasks]
            results = await asyncio.gather(*futures)
        
        logger.info(f"Thread pool execution completed: {len(results)} results")
        return results
    
    async def run_in_processpool(
        self,
        func: Callable,
        args_list: List[tuple],
        max_workers: Optional[int] = None
    ) -> List[T]:
        """
        在进程池中并发执行任务
        适用于CPU密集型任务（如数据处理、图表生成）
        
        Args:
            func: 要执行的函数（必须可pickle）
            args_list: 参数列表，每个元素是一个元组，对应一次函数调用的参数
            max_workers: 最大工作进程数（默认使用self.process_workers）
        
        Returns:
            任务结果列表
        
        Example:
            def process_data(data, multiplier):
                return sum(data) * multiplier
            
            args_list = [([1, 2, 3], 2), ([4, 5, 6], 3)]
            results = await controller.run_in_processpool(process_data, args_list)
        """
        max_workers = min(
            max_workers or self.process_workers,
            self.MAX_PROCESS_WORKERS
        )
        
        logger.info(f"Running {len(args_list)} tasks in process pool (max_workers={max_workers})")
        
        loop = asyncio.get_event_loop()
        results = []
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            futures = [
                loop.run_in_executor(executor, func, *args)
                for args in args_list
            ]
            results = await asyncio.gather(*futures)
        
        logger.info(f"Process pool execution completed: {len(results)} results")
        return results
    
    async def run_with_semaphore(
        self,
        coroutines: List[Coroutine],
        max_concurrent: Optional[int] = None
    ) -> List[T]:
        """
        使用信号量控制异步任务的并发数
        适用于I/O密集型异步任务
        
        Args:
            coroutines: 协程列表
            max_concurrent: 最大并发数（默认使用self.async_concurrency）
        
        Returns:
            任务结果列表
        
        Example:
            async def fetch_data(url):
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        return await response.text()
            
            coroutines = [fetch_data(f"http://api.example.com/{i}") for i in range(100)]
            results = await controller.run_with_semaphore(coroutines, max_concurrent=10)
        """
        max_concurrent = min(
            max_concurrent or self.async_concurrency,
            self.MAX_ASYNC_CONCURRENCY
        )
        
        logger.info(f"Running {len(coroutines)} coroutines with semaphore (max_concurrent={max_concurrent})")
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def run_with_limit(coro):
            async with semaphore:
                return await coro
        
        results = await asyncio.gather(*[run_with_limit(coro) for coro in coroutines])
        
        logger.info(f"Semaphore-controlled execution completed: {len(results)} results")
        return results
    
    async def map_threadpool(
        self,
        func: Callable[[Any], T],
        items: List[Any],
        max_workers: Optional[int] = None
    ) -> List[T]:
        """
        在线程池中映射函数到项目列表
        适用于I/O密集型任务
        
        Args:
            func: 要映射的函数
            items: 要处理的项目列表
            max_workers: 最大工作线程数（默认使用self.thread_workers）
        
        Returns:
            结果列表
        
        Example:
            def process_file(file_path):
                with open(file_path) as f:
                    return len(f.read())
            
            file_paths = ["file1.txt", "file2.txt", "file3.txt"]
            sizes = await controller.map_threadpool(process_file, file_paths)
        """
        tasks = [partial(func, item) for item in items]
        return await self.run_in_threadpool(tasks, max_workers)
    
    async def map_processpool(
        self,
        func: Callable[[Any], T],
        items: List[Any],
        max_workers: Optional[int] = None
    ) -> List[T]:
        """
        在进程池中映射函数到项目列表
        适用于CPU密集型任务
        
        Args:
            func: 要映射的函数（必须可pickle）
            items: 要处理的项目列表
            max_workers: 最大工作进程数（默认使用self.process_workers）
        
        Returns:
            结果列表
        
        Example:
            def compute_factorial(n):
                result = 1
                for i in range(1, n + 1):
                    result *= i
                return result
            
            numbers = [10, 20, 30, 40, 50]
            factorials = await controller.map_processpool(compute_factorial, numbers)
        """
        args_list = [(item,) for item in items]
        return await self.run_in_processpool(func, args_list, max_workers)
    
    async def batch_process(
        self,
        items: List[Any],
        processor: Callable[[Any], Coroutine[Any, Any, T]],
        batch_size: int = 10,
        max_concurrent: Optional[int] = None
    ) -> List[T]:
        """
        分批处理项目列表（内存优化）
        每批处理完成后释放内存，避免内存溢出
        
        Args:
            items: 要处理的项目列表
            processor: 异步处理函数
            batch_size: 每批处理的项目数（默认10）
            max_concurrent: 每批内的最大并发数（默认使用self.async_concurrency）
        
        Returns:
            所有结果列表
        
        Example:
            async def process_item(item):
                # 处理item
                return result
            
            items = list(range(1000))
            results = await controller.batch_process(
                items,
                process_item,
                batch_size=50,
                max_concurrent=10
            )
        """
        max_concurrent = max_concurrent or self.async_concurrency
        
        logger.info(
            f"Batch processing {len(items)} items - "
            f"batch_size={batch_size}, max_concurrent={max_concurrent}"
        )
        
        all_results = []
        
        # 分批处理
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            logger.debug(f"Processing batch {i // batch_size + 1}: {len(batch)} items")
            
            # 处理当前批次
            coroutines = [processor(item) for item in batch]
            batch_results = await self.run_with_semaphore(coroutines, max_concurrent)
            all_results.extend(batch_results)
            
            # 批次完成后可以做一些清理工作
            logger.debug(f"Batch {i // batch_size + 1} completed")
        
        logger.info(f"Batch processing completed: {len(all_results)} results")
        return all_results


# 全局单例
_global_controller: Optional[ConcurrencyController] = None


def get_concurrency_controller() -> ConcurrencyController:
    """
    获取全局并发控制器单例
    
    Returns:
        全局并发控制器实例
    """
    global _global_controller
    if _global_controller is None:
        _global_controller = ConcurrencyController()
        logger.info("Created global ConcurrencyController instance")
    return _global_controller


async def run_concurrent_tasks(
    tasks: List[Callable[[], T]],
    max_workers: Optional[int] = None,
    use_processpool: bool = False
) -> List[T]:
    """
    便捷函数：并发执行任务
    
    Args:
        tasks: 任务列表
        max_workers: 最大工作线程/进程数
        use_processpool: 是否使用进程池（默认False，使用线程池）
    
    Returns:
        任务结果列表
    
    Example:
        # 使用线程池
        results = await run_concurrent_tasks([task1, task2, task3])
        
        # 使用进程池
        results = await run_concurrent_tasks(
            [task1, task2, task3],
            use_processpool=True
        )
    """
    controller = get_concurrency_controller()
    
    if use_processpool:
        # 进程池需要特殊处理，这里简化为线程池
        logger.warning("Process pool mode not supported in convenience function, using thread pool instead")
    
    return await controller.run_in_threadpool(tasks, max_workers)


async def run_concurrent_coroutines(
    coroutines: List[Coroutine],
    max_concurrent: Optional[int] = None
) -> List[T]:
    """
    便捷函数：并发执行协程（控制并发数）
    
    Args:
        coroutines: 协程列表
        max_concurrent: 最大并发数
    
    Returns:
        任务结果列表
    
    Example:
        async def fetch(url):
            # 异步获取数据
            return data
        
        coroutines = [fetch(url) for url in urls]
        results = await run_concurrent_coroutines(coroutines, max_concurrent=10)
    """
    controller = get_concurrency_controller()
    return await controller.run_with_semaphore(coroutines, max_concurrent)

