"""
异步文件处理器模块
提供异步文件I/O、分块读写等功能
"""

import aiofiles
import asyncio
import logging
from pathlib import Path
from typing import AsyncIterator, Optional, Union, Callable, Any

logger = logging.getLogger(__name__)


class AsyncFileProcessor:
    """
    异步文件处理器
    提供高性能的异步文件I/O操作
    """
    
    DEFAULT_CHUNK_SIZE = 4096  # 4KB
    LARGE_FILE_THRESHOLD = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    async def read_file(
        file_path: Union[str, Path],
        encoding: str = 'utf-8',
        errors: str = 'strict'
    ) -> str:
        """
        异步读取文本文件
        
        Args:
            file_path: 文件路径
            encoding: 文件编码（默认utf-8）
            errors: 错误处理方式（默认strict）
        
        Returns:
            文件内容
        
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 读取错误
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.debug(f"Reading file asynchronously: {file_path}")
        
        try:
            async with aiofiles.open(
                file_path,
                mode='r',
                encoding=encoding,
                errors=errors
            ) as f:
                content = await f.read()
            
            logger.debug(f"Read {len(content)} bytes from {file_path}")
            return content
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            raise
    
    @staticmethod
    async def write_file(
        file_path: Union[str, Path],
        content: str,
        encoding: str = 'utf-8',
        errors: str = 'strict',
        create_dirs: bool = True
    ) -> None:
        """
        异步写入文本文件
        
        Args:
            file_path: 文件路径
            content: 文件内容
            encoding: 文件编码（默认utf-8）
            errors: 错误处理方式（默认strict）
            create_dirs: 是否自动创建父目录（默认True）
        
        Raises:
            IOError: 写入错误
        """
        file_path = Path(file_path)
        
        # 自动创建父目录
        if create_dirs and not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {file_path.parent}")
        
        logger.debug(f"Writing file asynchronously: {file_path}")
        
        try:
            async with aiofiles.open(
                file_path,
                mode='w',
                encoding=encoding,
                errors=errors
            ) as f:
                await f.write(content)
            
            logger.debug(f"Wrote {len(content)} bytes to {file_path}")
            
        except Exception as e:
            logger.error(f"Error writing file {file_path}: {e}")
            raise
    
    @staticmethod
    async def read_binary(file_path: Union[str, Path]) -> bytes:
        """
        异步读取二进制文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件内容（字节）
        
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 读取错误
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        logger.debug(f"Reading binary file asynchronously: {file_path}")
        
        try:
            async with aiofiles.open(file_path, mode='rb') as f:
                content = await f.read()
            
            logger.debug(f"Read {len(content)} bytes from {file_path}")
            return content
            
        except Exception as e:
            logger.error(f"Error reading binary file {file_path}: {e}")
            raise
    
    @staticmethod
    async def write_binary(
        file_path: Union[str, Path],
        content: bytes,
        create_dirs: bool = True
    ) -> None:
        """
        异步写入二进制文件
        
        Args:
            file_path: 文件路径
            content: 文件内容（字节）
            create_dirs: 是否自动创建父目录（默认True）
        
        Raises:
            IOError: 写入错误
        """
        file_path = Path(file_path)
        
        # 自动创建父目录
        if create_dirs and not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {file_path.parent}")
        
        logger.debug(f"Writing binary file asynchronously: {file_path}")
        
        try:
            async with aiofiles.open(file_path, mode='wb') as f:
                await f.write(content)
            
            logger.debug(f"Wrote {len(content)} bytes to {file_path}")
            
        except Exception as e:
            logger.error(f"Error writing binary file {file_path}: {e}")
            raise
    
    @staticmethod
    async def copy_file(
        src: Union[str, Path],
        dst: Union[str, Path],
        chunk_size: Optional[int] = None,
        create_dirs: bool = True
    ) -> None:
        """
        异步复制文件（分块复制，内存优化）
        
        Args:
            src: 源文件路径
            dst: 目标文件路径
            chunk_size: 分块大小（默认使用DEFAULT_CHUNK_SIZE）
            create_dirs: 是否自动创建目标目录（默认True）
        
        Raises:
            FileNotFoundError: 源文件不存在
            IOError: 复制错误
        """
        src_path = Path(src)
        dst_path = Path(dst)
        
        if not src_path.exists():
            raise FileNotFoundError(f"Source file not found: {src_path}")
        
        # 自动创建目标目录
        if create_dirs and not dst_path.parent.exists():
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {dst_path.parent}")
        
        chunk_size = chunk_size or AsyncFileProcessor.DEFAULT_CHUNK_SIZE
        logger.debug(f"Copying file asynchronously: {src_path} -> {dst_path} (chunk_size={chunk_size})")
        
        try:
            bytes_copied = 0
            async with aiofiles.open(src_path, mode='rb') as f_src:
                async with aiofiles.open(dst_path, mode='wb') as f_dst:
                    while True:
                        chunk = await f_src.read(chunk_size)
                        if not chunk:
                            break
                        await f_dst.write(chunk)
                        bytes_copied += len(chunk)
            
            logger.debug(f"Copied {bytes_copied} bytes from {src_path} to {dst_path}")
            
        except Exception as e:
            logger.error(f"Error copying file {src_path} to {dst_path}: {e}")
            raise
    
    @staticmethod
    async def read_chunked(
        file_path: Union[str, Path],
        chunk_size: Optional[int] = None
    ) -> AsyncIterator[bytes]:
        """
        异步分块读取文件（内存优化）
        适用于大文件处理
        
        Args:
            file_path: 文件路径
            chunk_size: 分块大小（默认使用DEFAULT_CHUNK_SIZE）
        
        Yields:
            文件数据块（字节）
        
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 读取错误
        
        Example:
            async for chunk in AsyncFileProcessor.read_chunked("large_file.bin"):
                # 处理数据块
                process_chunk(chunk)
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        chunk_size = chunk_size or AsyncFileProcessor.DEFAULT_CHUNK_SIZE
        logger.debug(f"Reading file in chunks: {file_path} (chunk_size={chunk_size})")
        
        try:
            async with aiofiles.open(file_path, mode='rb') as f:
                while True:
                    chunk = await f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
                    
        except Exception as e:
            logger.error(f"Error reading file in chunks {file_path}: {e}")
            raise
    
    @staticmethod
    async def write_chunked(
        file_path: Union[str, Path],
        chunks: AsyncIterator[bytes],
        create_dirs: bool = True
    ) -> int:
        """
        异步分块写入文件（内存优化）
        适用于流式写入
        
        Args:
            file_path: 文件路径
            chunks: 数据块异步迭代器
            create_dirs: 是否自动创建父目录（默认True）
        
        Returns:
            写入的总字节数
        
        Raises:
            IOError: 写入错误
        
        Example:
            async def data_generator():
                for i in range(100):
                    yield f"chunk {i}\n".encode()
            
            bytes_written = await AsyncFileProcessor.write_chunked(
                "output.txt",
                data_generator()
            )
        """
        file_path = Path(file_path)
        
        # 自动创建父目录
        if create_dirs and not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {file_path.parent}")
        
        logger.debug(f"Writing file in chunks: {file_path}")
        
        try:
            total_bytes = 0
            async with aiofiles.open(file_path, mode='wb') as f:
                async for chunk in chunks:
                    await f.write(chunk)
                    total_bytes += len(chunk)
            
            logger.debug(f"Wrote {total_bytes} bytes to {file_path}")
            return total_bytes
            
        except Exception as e:
            logger.error(f"Error writing file in chunks {file_path}: {e}")
            raise
    
    @staticmethod
    async def process_file_chunked(
        file_path: Union[str, Path],
        processor: Callable[[bytes], Any],
        chunk_size: Optional[int] = None
    ) -> list:
        """
        异步分块处理文件
        对每个数据块应用处理函数
        
        Args:
            file_path: 文件路径
            processor: 处理函数，接收数据块（bytes），返回处理结果
            chunk_size: 分块大小（默认使用DEFAULT_CHUNK_SIZE）
        
        Returns:
            处理结果列表
        
        Raises:
            FileNotFoundError: 文件不存在
            IOError: 读取错误
        
        Example:
            def count_lines(chunk: bytes) -> int:
                return chunk.count(b'\n')
            
            line_counts = await AsyncFileProcessor.process_file_chunked(
                "large_file.txt",
                count_lines
            )
            total_lines = sum(line_counts)
        """
        results = []
        
        async for chunk in AsyncFileProcessor.read_chunked(file_path, chunk_size):
            result = processor(chunk)
            results.append(result)
        
        return results
    
    @staticmethod
    async def get_file_size(file_path: Union[str, Path]) -> int:
        """
        获取文件大小
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件大小（字节）
        
        Raises:
            FileNotFoundError: 文件不存在
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        return file_path.stat().st_size
    
    @staticmethod
    async def is_large_file(file_path: Union[str, Path]) -> bool:
        """
        判断是否为大文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            是否为大文件（大于LARGE_FILE_THRESHOLD）
        
        Raises:
            FileNotFoundError: 文件不存在
        """
        size = await AsyncFileProcessor.get_file_size(file_path)
        return size > AsyncFileProcessor.LARGE_FILE_THRESHOLD
    
    @staticmethod
    async def append_file(
        file_path: Union[str, Path],
        content: str,
        encoding: str = 'utf-8',
        create_dirs: bool = True
    ) -> None:
        """
        异步追加内容到文件
        
        Args:
            file_path: 文件路径
            content: 要追加的内容
            encoding: 文件编码（默认utf-8）
            create_dirs: 是否自动创建父目录（默认True）
        
        Raises:
            IOError: 写入错误
        """
        file_path = Path(file_path)
        
        # 自动创建父目录
        if create_dirs and not file_path.parent.exists():
            file_path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {file_path.parent}")
        
        logger.debug(f"Appending to file asynchronously: {file_path}")
        
        try:
            async with aiofiles.open(file_path, mode='a', encoding=encoding) as f:
                await f.write(content)
            
            logger.debug(f"Appended {len(content)} bytes to {file_path}")
            
        except Exception as e:
            logger.error(f"Error appending to file {file_path}: {e}")
            raise

