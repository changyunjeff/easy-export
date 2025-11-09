from __future__ import annotations

import logging
from typing import Optional, Union
from redis import Redis
from redis.connection import ConnectionPool
from .memory_store import MemoryStore

logger = logging.getLogger(__name__)

_redis_client: Optional[Union[Redis, MemoryStore]] = None
_redis_pool: Optional[ConnectionPool] = None
_use_memory_store: bool = False


def init_redis(
    host: str = "localhost",
    port: int = 6379,
    db: int = 0,
    password: Optional[str] = None,
    decode_responses: bool = True,
    max_connections: int = 50,
    socket_connect_timeout: int = 5,
    socket_timeout: int = 5,
    fallback_to_memory: bool = True,
    **kwargs
) -> Union[Redis, MemoryStore]:
    """
    初始化 Redis 连接池和客户端
    
    Args:
        host: Redis 服务器地址
        port: Redis 服务器端口
        db: Redis 数据库编号
        password: Redis 密码
        decode_responses: 是否自动解码响应为字符串
        max_connections: 连接池最大连接数
        socket_connect_timeout: 连接超时时间（秒）
        socket_timeout:  socket 超时时间（秒）
        fallback_to_memory: 如果 Redis 连接失败，是否回退到内存存储
        **kwargs: 其他 Redis 连接参数
    
    Returns:
        Redis 客户端实例或内存存储实例
    """
    global _redis_client, _redis_pool, _use_memory_store
    
    if _redis_client is not None:
        logger.warning("Redis client already initialized, returning existing client")
        return _redis_client
    
    try:
        _redis_pool = ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=decode_responses,
            max_connections=max_connections,
            socket_connect_timeout=socket_connect_timeout,
            socket_timeout=socket_timeout,
            **kwargs
        )
        
        _redis_client = Redis(connection_pool=_redis_pool)
        
        # 测试连接
        _redis_client.ping()
        _use_memory_store = False
        logger.info(f"Redis connection initialized successfully: {host}:{port}/{db}")
        
        return _redis_client
    
    except Exception as e:
        logger.error(f"Failed to initialize Redis connection: {e}")
        if fallback_to_memory:
            logger.warning("Falling back to in-memory storage (non-persistent)")
            _redis_client = MemoryStore()
            _use_memory_store = True
            _redis_pool = None
            return _redis_client
        else:
            raise


def get_redis_client() -> Union[Redis, MemoryStore]:
    """
    获取 Redis 客户端实例或内存存储实例
    
    Returns:
        Redis 客户端实例或内存存储实例
    
    Raises:
        RuntimeError: 如果 Redis 客户端未初始化
    """
    global _redis_client, _use_memory_store
    
    if _redis_client is None:
        # 如果未初始化，尝试使用内存存储作为回退
        logger.warning("Redis client not initialized, using in-memory storage as fallback")
        _redis_client = MemoryStore()
        _use_memory_store = True
        return _redis_client
    
    return _redis_client


def is_using_memory_store() -> bool:
    """
    检查当前是否使用内存存储
    
    Returns:
        如果使用内存存储返回 True，否则返回 False
    """
    global _use_memory_store
    return _use_memory_store


def init_memory_store() -> MemoryStore:
    """
    直接初始化内存存储（不尝试连接 Redis）
    
    Returns:
        内存存储实例
    """
    global _redis_client, _use_memory_store
    
    if _redis_client is not None:
        logger.warning("Storage already initialized, returning existing instance")
        return _redis_client if isinstance(_redis_client, MemoryStore) else MemoryStore()
    
    _redis_client = MemoryStore()
    _use_memory_store = True
    logger.info("In-memory storage initialized (non-persistent)")
    return _redis_client


def close_redis() -> None:
    """
    关闭 Redis 连接池和客户端
    """
    global _redis_client, _redis_pool, _use_memory_store
    
    if _redis_client is not None:
        try:
            if not _use_memory_store:
                _redis_client.close()
                logger.info("Redis client closed")
            else:
                _redis_client.close()  # MemoryStore 的 close 是空操作
                logger.info("Memory store closed")
        except Exception as e:
            logger.error(f"Error closing Redis client: {e}")
        finally:
            _redis_client = None
            _use_memory_store = False
    
    if _redis_pool is not None:
        try:
            _redis_pool.disconnect()
            logger.info("Redis connection pool disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting Redis pool: {e}")
        finally:
            _redis_pool = None

