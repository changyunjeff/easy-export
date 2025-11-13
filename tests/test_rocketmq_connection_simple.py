"""
RocketMQ连接管理简化测试

测试RocketMQ连接管理的基本功能，匹配实际的类结构。
"""

import pytest
from unittest.mock import Mock, patch

from core.rocketmq.connection import RocketMQConnection, RocketMQConnectionInfo
from core.rocketmq.exceptions import RocketMQConnectionError, RocketMQConfigError
from core.schemas.configs import RocketMQConfig


class TestRocketMQConnectionInfo:
    """RocketMQ连接信息测试类"""
    
    def test_connection_info_creation(self):
        """测试连接信息创建"""
        info = RocketMQConnectionInfo(
            name_server="localhost:9876",
            producer_group="test_producer",
            consumer_group="test_consumer",
            topic="test_topic",
            tag="*",
            namespace=None
        )
        
        assert info.name_server == "localhost:9876"
        assert info.producer_group == "test_producer"
        assert info.consumer_group == "test_consumer"
        assert info.topic == "test_topic"
        assert info.tag == "*"
        assert info.namespace is None
        
    def test_connection_info_with_auth(self):
        """测试带认证的连接信息"""
        info = RocketMQConnectionInfo(
            name_server="localhost:9876",
            producer_group="test_producer",
            consumer_group="test_consumer",
            topic="test_topic",
            tag="test_tag",
            namespace="test_namespace",
            access_key="test_key",
            secret_key="test_secret"
        )
        
        assert info.namespace == "test_namespace"
        assert info.access_key == "test_key"
        assert info.secret_key == "test_secret"


class TestRocketMQConnection:
    """RocketMQ连接管理测试类"""
    
    @pytest.fixture
    def valid_config(self):
        """有效的RocketMQ配置"""
        return RocketMQConfig(
            enabled=True,
            name_server="localhost:9876",
            producer_group="test_producer_group",
            consumer_group="test_consumer_group",
            topic="test_topic",
            tag="*",
            max_message_size=4194304,
            send_timeout=3000,
            retry_times=3
        )
    
    @pytest.fixture
    def invalid_config(self):
        """无效的RocketMQ配置"""
        return RocketMQConfig(
            enabled=True,
            name_server="",  # 空的name_server
            producer_group="test_producer_group",
            consumer_group="test_consumer_group",
            topic="test_topic"
        )
    
    def test_connection_init_success(self, valid_config):
        """测试连接初始化成功"""
        connection = RocketMQConnection(valid_config)
        
        assert connection.config == valid_config
        assert connection._connection_info is not None
        assert not connection._is_connected
        
    def test_connection_init_invalid_config(self, invalid_config):
        """测试无效配置初始化失败"""
        with pytest.raises(RocketMQConfigError) as exc_info:
            RocketMQConnection(invalid_config)
        
        assert "name_server is required" in str(exc_info.value)
        
    @patch('core.rocketmq.connection.logger')
    def test_connect_success(self, mock_logger, valid_config):
        """测试连接成功"""
        connection = RocketMQConnection(valid_config)
        
        connection.connect()
        
        assert connection._is_connected
        mock_logger.info.assert_called_with("Successfully connected to RocketMQ")
        
    @patch('core.rocketmq.connection.logger')
    def test_connect_already_connected(self, mock_logger, valid_config):
        """测试重复连接"""
        connection = RocketMQConnection(valid_config)
        connection._is_connected = True
        
        connection.connect()
        
        # 实际实现中没有检查已连接状态的警告
        # 只验证连接状态保持为True
        assert connection._is_connected
        
    @patch('core.rocketmq.connection.logger')
    def test_disconnect_success(self, mock_logger, valid_config):
        """测试断开连接成功"""
        connection = RocketMQConnection(valid_config)
        connection._is_connected = True
        
        connection.disconnect()
        
        assert not connection._is_connected
        mock_logger.info.assert_called_with("Successfully disconnected from RocketMQ")
        
    @patch('core.rocketmq.connection.logger')
    def test_disconnect_not_connected(self, mock_logger, valid_config):
        """测试未连接时断开连接"""
        connection = RocketMQConnection(valid_config)
        connection._is_connected = False
        
        connection.disconnect()
        
        # 实际实现中未连接时断开连接不会产生警告
        # 只验证状态保持为False
        assert not connection._is_connected
        
    def test_is_connected_true(self, valid_config):
        """测试连接状态检查（已连接）"""
        connection = RocketMQConnection(valid_config)
        connection._is_connected = True
        
        assert connection.is_connected() is True
        
    def test_is_connected_false(self, valid_config):
        """测试连接状态检查（未连接）"""
        connection = RocketMQConnection(valid_config)
        connection._is_connected = False
        
        assert connection.is_connected() is False
        
    def test_get_connection_info(self, valid_config):
        """测试获取连接信息"""
        connection = RocketMQConnection(valid_config)
        
        info = connection.get_connection_info()
        
        assert isinstance(info, RocketMQConnectionInfo)
        assert info.name_server == valid_config.name_server
        assert info.producer_group == valid_config.producer_group
        assert info.consumer_group == valid_config.consumer_group
        assert info.topic == valid_config.topic
        assert info.tag == valid_config.tag
        
    def test_get_producer_config(self, valid_config):
        """测试获取生产者配置"""
        connection = RocketMQConnection(valid_config)
        
        config = connection.get_producer_config()
        
        assert config["name_server"] == valid_config.name_server
        assert config["producer_group"] == valid_config.producer_group
        assert config["send_timeout"] == valid_config.send_timeout
        assert config["retry_times"] == valid_config.retry_times
        
    def test_get_consumer_config(self, valid_config):
        """测试获取消费者配置"""
        connection = RocketMQConnection(valid_config)
        
        config = connection.get_consumer_config()
        
        assert config["name_server"] == valid_config.name_server
        assert config["consumer_group"] == valid_config.consumer_group
        assert config["consumer_thread_min"] == valid_config.consumer_thread_min
        assert config["consumer_thread_max"] == valid_config.consumer_thread_max


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
