"""
资源管理器模块
提供文件句柄自动释放、临时文件清理等资源管理功能
"""

import tempfile
import logging
from pathlib import Path
from typing import Any, List, Optional, AsyncIterator
from contextlib import asynccontextmanager, contextmanager
import shutil

logger = logging.getLogger(__name__)


class ResourceManager:
    """
    资源管理器
    自动跟踪和释放资源（文件句柄、临时文件、临时目录等）
    
    使用方式:
        with ResourceManager() as rm:
            # 注册资源
            rm.register_file(file_obj)
            rm.register_temp_file(temp_path)
            # 退出时自动清理
    """
    
    def __init__(self):
        self.open_files: List[Any] = []
        self.temp_files: List[Path] = []
        self.temp_dirs: List[Path] = []
        logger.debug("ResourceManager initialized")
    
    def register_file(self, file_obj: Any) -> None:
        """
        注册文件句柄
        
        Args:
            file_obj: 文件对象（需要有close方法）
        """
        if file_obj and hasattr(file_obj, 'close'):
            self.open_files.append(file_obj)
            logger.debug(f"Registered file handle: {file_obj}")
        else:
            logger.warning(f"Invalid file object: {file_obj}")
    
    def register_temp_file(self, file_path: str) -> None:
        """
        注册临时文件
        
        Args:
            file_path: 临时文件路径
        """
        path = Path(file_path)
        if path not in self.temp_files:
            self.temp_files.append(path)
            logger.debug(f"Registered temp file: {file_path}")
    
    def register_temp_directory(self, dir_path: str) -> None:
        """
        注册临时目录
        
        Args:
            dir_path: 临时目录路径
        """
        path = Path(dir_path)
        if path not in self.temp_dirs:
            self.temp_dirs.append(path)
            logger.debug(f"Registered temp directory: {dir_path}")
    
    def close_files(self) -> None:
        """关闭所有文件句柄"""
        closed_count = 0
        for file_obj in self.open_files:
            try:
                if hasattr(file_obj, 'closed') and not file_obj.closed:
                    file_obj.close()
                    closed_count += 1
                    logger.debug(f"Closed file handle: {file_obj}")
                elif hasattr(file_obj, 'close'):
                    file_obj.close()
                    closed_count += 1
                    logger.debug(f"Closed file handle: {file_obj}")
            except Exception as e:
                logger.error(f"Error closing file handle {file_obj}: {e}")
        
        self.open_files.clear()
        if closed_count > 0:
            logger.info(f"Closed {closed_count} file handle(s)")
    
    def cleanup_temp_files(self) -> None:
        """删除所有临时文件"""
        deleted_count = 0
        for temp_file in self.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    deleted_count += 1
                    logger.debug(f"Deleted temp file: {temp_file}")
            except Exception as e:
                logger.error(f"Error deleting temp file {temp_file}: {e}")
        
        self.temp_files.clear()
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} temp file(s)")
    
    def cleanup_temp_directories(self) -> None:
        """删除所有临时目录"""
        deleted_count = 0
        for temp_dir in self.temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
                    deleted_count += 1
                    logger.debug(f"Deleted temp directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Error deleting temp directory {temp_dir}: {e}")
        
        self.temp_dirs.clear()
        if deleted_count > 0:
            logger.info(f"Deleted {deleted_count} temp director(y/ies)")
    
    def cleanup(self) -> None:
        """清理所有资源"""
        logger.debug("Starting resource cleanup...")
        
        # 1. 关闭文件句柄
        self.close_files()
        
        # 2. 删除临时文件
        self.cleanup_temp_files()
        
        # 3. 删除临时目录
        self.cleanup_temp_directories()
        
        logger.debug("Resource cleanup completed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()
        return False


@asynccontextmanager
async def managed_temp_file(
    suffix: str = '.tmp',
    prefix: str = 'easy_export_',
    dir: Optional[str] = None,
    mode: str = 'w+b'
):
    """
    管理临时文件的异步上下文管理器
    确保临时文件在使用后自动删除
    
    Args:
        suffix: 文件后缀（默认.tmp）
        prefix: 文件前缀（默认easy_export_）
        dir: 临时文件目录（默认系统临时目录）
        mode: 文件打开模式（默认w+b）
    
    Yields:
        临时文件路径（str）
    
    Example:
        async with managed_temp_file(suffix='.txt') as temp_file:
            # 使用临时文件
            async with aiofiles.open(temp_file, 'w') as f:
                await f.write("temp data")
        # 临时文件自动删除
    """
    temp_file = None
    temp_path = None
    
    try:
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(
            mode=mode,
            suffix=suffix,
            prefix=prefix,
            dir=dir,
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()  # 关闭文件句柄，但不删除文件
        
        logger.debug(f"Created temp file: {temp_path}")
        yield temp_path
        
    finally:
        # 自动清理临时文件
        if temp_path:
            try:
                path = Path(temp_path)
                if path.exists():
                    path.unlink()
                    logger.debug(f"Deleted temp file: {temp_path}")
            except Exception as e:
                logger.error(f"Error deleting temp file {temp_path}: {e}")


@asynccontextmanager
async def managed_temp_directory(prefix: str = 'easy_export_', dir: Optional[str] = None):
    """
    管理临时目录的异步上下文管理器
    确保临时目录在使用后自动删除
    
    Args:
        prefix: 目录前缀（默认easy_export_）
        dir: 父目录（默认系统临时目录）
    
    Yields:
        临时目录路径（str）
    
    Example:
        async with managed_temp_directory() as temp_dir:
            # 使用临时目录
            temp_file = Path(temp_dir) / "data.txt"
            temp_file.write_text("temp data")
        # 临时目录及其内容自动删除
    """
    temp_dir = None
    
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix=prefix, dir=dir)
        logger.debug(f"Created temp directory: {temp_dir}")
        
        yield temp_dir
        
    finally:
        # 自动清理临时目录
        if temp_dir:
            try:
                temp_path = Path(temp_dir)
                if temp_path.exists():
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Deleted temp directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Error deleting temp directory {temp_dir}: {e}")


@contextmanager
def managed_temp_file_sync(
    suffix: str = '.tmp',
    prefix: str = 'easy_export_',
    dir: Optional[str] = None,
    mode: str = 'w+b'
):
    """
    管理临时文件的同步上下文管理器
    确保临时文件在使用后自动删除
    
    Args:
        suffix: 文件后缀（默认.tmp）
        prefix: 文件前缀（默认easy_export_）
        dir: 临时文件目录（默认系统临时目录）
        mode: 文件打开模式（默认w+b）
    
    Yields:
        临时文件路径（str）
    
    Example:
        with managed_temp_file_sync(suffix='.txt') as temp_file:
            # 使用临时文件
            with open(temp_file, 'w') as f:
                f.write("temp data")
        # 临时文件自动删除
    """
    temp_file = None
    temp_path = None
    
    try:
        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(
            mode=mode,
            suffix=suffix,
            prefix=prefix,
            dir=dir,
            delete=False
        )
        temp_path = temp_file.name
        temp_file.close()  # 关闭文件句柄，但不删除文件
        
        logger.debug(f"Created temp file: {temp_path}")
        yield temp_path
        
    finally:
        # 自动清理临时文件
        if temp_path:
            try:
                path = Path(temp_path)
                if path.exists():
                    path.unlink()
                    logger.debug(f"Deleted temp file: {temp_path}")
            except Exception as e:
                logger.error(f"Error deleting temp file {temp_path}: {e}")


@contextmanager
def managed_temp_directory_sync(prefix: str = 'easy_export_', dir: Optional[str] = None):
    """
    管理临时目录的同步上下文管理器
    确保临时目录在使用后自动删除
    
    Args:
        prefix: 目录前缀（默认easy_export_）
        dir: 父目录（默认系统临时目录）
    
    Yields:
        临时目录路径（str）
    
    Example:
        with managed_temp_directory_sync() as temp_dir:
            # 使用临时目录
            temp_file = Path(temp_dir) / "data.txt"
            temp_file.write_text("temp data")
        # 临时目录及其内容自动删除
    """
    temp_dir = None
    
    try:
        # 创建临时目录
        temp_dir = tempfile.mkdtemp(prefix=prefix, dir=dir)
        logger.debug(f"Created temp directory: {temp_dir}")
        
        yield temp_dir
        
    finally:
        # 自动清理临时目录
        if temp_dir:
            try:
                temp_path = Path(temp_dir)
                if temp_path.exists():
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Deleted temp directory: {temp_dir}")
            except Exception as e:
                logger.error(f"Error deleting temp directory {temp_dir}: {e}")

