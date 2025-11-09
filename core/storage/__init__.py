"""
存储层模块
提供模板存储、文件存储、缓存存储等功能
"""

from .template_storage import TemplateStorage
from .file_storage import FileStorage
from .cache_storage import CacheStorage

__all__ = [
    "TemplateStorage",
    "FileStorage",
    "CacheStorage",
]

