"""
性能优化模块
提供资源管理、异步文件处理、并发控制等性能优化功能
"""

from core.performance.resource_manager import ResourceManager, managed_temp_file, managed_temp_directory
from core.performance.async_file import AsyncFileProcessor
from core.performance.concurrency import ConcurrencyController

__all__ = [
    'ResourceManager',
    'managed_temp_file',
    'managed_temp_directory',
    'AsyncFileProcessor',
    'ConcurrencyController',
]

