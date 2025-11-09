"""
Redis 连接管理白盒测试
测试连接初始化、获取、关闭等功能
"""
from __future__ import annotations

import pytest
import sys
import os
from unittest.mock import patch, MagicMock

# Mock 依赖模块以避免导入问题（在 patch 之前）
sys.modules['core.config'] = MagicMock()
sys.modules['pydantic_yaml'] = MagicMock()
# redis 模块会在测试中被 patch，这里先 mock 以避免导入错误
sys.modules['redis'] = MagicMock()
sys.modules['redis.connection'] = MagicMock()

from core.redis.connection import (
    init_redis,
    get_redis_client,
    init_memory_store,
    is_using_memory_store,
    close_redis,
)
from core.redis.memory_store import MemoryStore


class TestRedisConnection:
    """Redis 连接管理测试类"""
    
    def teardown_method(self):
        """每个测试后清理全局状态"""
        # 重置全局变量
        import core.redis.connection as conn_module
        conn_module._redis_client = None
        conn_module._redis_pool = None
        conn_module._use_memory_store = False
    
    def test_init_memory_store(self):
        """测试直接初始化内存存储"""
        store = init_memory_store()
        assert isinstance(store, MemoryStore)
        assert is_using_memory_store() is True
        
        # 再次调用应该返回同一个实例
        store2 = init_memory_store()
        assert store is store2
    
    def test_init_memory_store_when_already_initialized(self):
        """测试在已初始化时调用 init_memory_store"""
        store1 = init_memory_store()
        store2 = init_memory_store()
        assert store1 is store2
    
    @patch('core.redis.connection.Redis')
    @patch('core.redis.connection.ConnectionPool')
    def test_init_redis_success(self, mock_pool_class, mock_redis_class):
        """测试成功初始化 Redis 连接"""
        # 模拟 Redis 连接成功
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        client = init_redis(
            host="localhost",
            port=6379,
            db=0
        )
        
        assert client is not None
        assert is_using_memory_store() is False
        mock_redis_instance.ping.assert_called_once()
    
    @patch('core.redis.connection.Redis')
    @patch('core.redis.connection.ConnectionPool')
    def test_init_redis_failure_with_fallback(self, mock_pool_class, mock_redis_class):
        """测试 Redis 连接失败时回退到内存存储"""
        # 模拟 Redis 连接失败
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.side_effect = Exception("Connection failed")
        mock_redis_class.return_value = mock_redis_instance
        
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        client = init_redis(
            host="localhost",
            port=6379,
            db=0,
            fallback_to_memory=True
        )
        
        assert isinstance(client, MemoryStore)
        assert is_using_memory_store() is True
    
    @patch('core.redis.connection.Redis')
    @patch('core.redis.connection.ConnectionPool')
    def test_init_redis_failure_without_fallback(self, mock_pool_class, mock_redis_class):
        """测试 Redis 连接失败时不回退"""
        # 模拟 Redis 连接失败
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.side_effect = Exception("Connection failed")
        mock_redis_class.return_value = mock_redis_instance
        
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        with pytest.raises(Exception):
            init_redis(
                host="localhost",
                port=6379,
                db=0,
                fallback_to_memory=False
            )
    
    @patch('core.redis.connection.Redis')
    @patch('core.redis.connection.ConnectionPool')
    def test_init_redis_already_initialized(self, mock_pool_class, mock_redis_class):
        """测试重复初始化 Redis"""
        # 第一次初始化
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        client1 = init_redis(host="localhost", port=6379)
        
        # 第二次初始化应该返回同一个客户端
        client2 = init_redis(host="localhost", port=6379)
        
        assert client1 is client2
        # ping 应该只被调用一次（第一次初始化时）
        assert mock_redis_instance.ping.call_count == 1
    
    def test_get_redis_client_when_not_initialized(self):
        """测试在未初始化时获取客户端"""
        client = get_redis_client()
        assert isinstance(client, MemoryStore)
        assert is_using_memory_store() is True
    
    def test_get_redis_client_when_initialized(self):
        """测试在已初始化时获取客户端"""
        store = init_memory_store()
        client = get_redis_client()
        assert client is store
    
    @patch('core.redis.connection.Redis')
    @patch('core.redis.connection.ConnectionPool')
    def test_get_redis_client_after_init_redis(self, mock_pool_class, mock_redis_class):
        """测试在 init_redis 后获取客户端"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        init_redis(host="localhost", port=6379)
        client = get_redis_client()
        
        assert client is not None
        assert is_using_memory_store() is False
    
    def test_is_using_memory_store(self):
        """测试 is_using_memory_store 函数"""
        # 初始状态
        assert is_using_memory_store() is False
        
        # 初始化内存存储
        init_memory_store()
        assert is_using_memory_store() is True
    
    @patch('core.redis.connection.Redis')
    @patch('core.redis.connection.ConnectionPool')
    def test_is_using_memory_store_after_redis_init(self, mock_pool_class, mock_redis_class):
        """测试在 Redis 初始化后 is_using_memory_store"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        init_redis(host="localhost", port=6379)
        assert is_using_memory_store() is False
    
    def test_close_redis_memory_store(self):
        """测试关闭内存存储"""
        store = init_memory_store()
        assert get_redis_client() is store
        
        close_redis()
        
        # 关闭后，get_redis_client 应该返回新的内存存储实例
        new_client = get_redis_client()
        assert new_client is not store
        assert isinstance(new_client, MemoryStore)
    
    @patch('core.redis.connection.Redis')
    @patch('core.redis.connection.ConnectionPool')
    def test_close_redis_connection(self, mock_pool_class, mock_redis_class):
        """测试关闭 Redis 连接"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        init_redis(host="localhost", port=6379)
        
        close_redis()
        
        # 验证 close 和 disconnect 被调用
        mock_redis_instance.close.assert_called_once()
        mock_pool.disconnect.assert_called_once()
    
    def test_close_redis_when_not_initialized(self):
        """测试在未初始化时关闭 Redis"""
        # 不应该抛出异常
        close_redis()
        close_redis()  # 可以多次调用
    
    @patch('core.redis.connection.Redis')
    @patch('core.redis.connection.ConnectionPool')
    def test_init_redis_with_custom_params(self, mock_pool_class, mock_redis_class):
        """测试使用自定义参数初始化 Redis"""
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.return_value = True
        mock_redis_class.return_value = mock_redis_instance
        
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        init_redis(
            host="192.168.1.100",
            port=6380,
            db=1,
            password="secret",
            decode_responses=False,
            max_connections=100,
            socket_connect_timeout=10,
            socket_timeout=10
        )
        
        # 验证 ConnectionPool 使用正确的参数创建
        mock_pool_class.assert_called_once()
        call_kwargs = mock_pool_class.call_args[1]
        assert call_kwargs["host"] == "192.168.1.100"
        assert call_kwargs["port"] == 6380
        assert call_kwargs["db"] == 1
        assert call_kwargs["password"] == "secret"
        assert call_kwargs["decode_responses"] is False
        assert call_kwargs["max_connections"] == 100
        assert call_kwargs["socket_connect_timeout"] == 10
        assert call_kwargs["socket_timeout"] == 10
    
    def test_multiple_init_memory_store_calls(self):
        """测试多次调用 init_memory_store"""
        store1 = init_memory_store()
        store2 = init_memory_store()
        store3 = init_memory_store()
        
        # 应该返回同一个实例
        assert store1 is store2
        assert store2 is store3
    
    @patch('core.redis.connection.Redis')
    @patch('core.redis.connection.ConnectionPool')
    def test_fallback_after_redis_failure(self, mock_pool_class, mock_redis_class):
        """测试 Redis 失败后的回退机制"""
        # 第一次尝试连接失败
        mock_redis_instance = MagicMock()
        mock_redis_instance.ping.side_effect = Exception("Connection failed")
        mock_redis_class.return_value = mock_redis_instance
        
        mock_pool = MagicMock()
        mock_pool_class.return_value = mock_pool
        
        client = init_redis(host="localhost", port=6379, fallback_to_memory=True)
        assert isinstance(client, MemoryStore)
        assert is_using_memory_store() is True
        
        # 获取客户端应该返回内存存储
        client2 = get_redis_client()
        assert isinstance(client2, MemoryStore)
        assert client is client2
    
    def test_get_redis_client_creates_memory_store_on_demand(self):
        """测试 get_redis_client 在未初始化时自动创建内存存储"""
        # 确保未初始化
        close_redis()
        
        client = get_redis_client()
        assert isinstance(client, MemoryStore)
        assert is_using_memory_store() is True
        
        # 再次调用应该返回同一个实例
        client2 = get_redis_client()
        assert client is client2

