"""
RocketMQ消费者简化测试

测试RocketMQ消费者的基本功能，匹配实际的类结构。
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from core.rocketmq.consumer import RocketMQConsumer, ConsumeResult
from core.rocketmq.producer import ExportTaskMessage
from core.rocketmq.connection import RocketMQConnection
from core.rocketmq.exceptions import RocketMQConsumeError, RocketMQConnectionError


class TestConsumeResult:
    """消费结果测试类"""
    
    def test_consume_result_success(self):
        """测试成功的消费结果"""
        result = ConsumeResult(
            success=True,
            task_id="task_001"
        )
        
        assert result.success is True
        assert result.task_id == "task_001"
        assert result.error_message is None
        assert result.processing_time is None
        
    def test_consume_result_failure(self):
        """测试失败的消费结果"""
        result = ConsumeResult(
            success=False,
            task_id="task_002",
            error_message="Processing failed",
            processing_time=1.5
        )
        
        assert result.success is False
        assert result.task_id == "task_002"
        assert result.error_message == "Processing failed"
        assert result.processing_time == 1.5
        
    def test_consume_result_to_dict(self):
        """测试消费结果转换为字典"""
        result = ConsumeResult(
            success=True,
            task_id="task_003",
            processing_time=0.8
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["success"] is True
        assert result_dict["task_id"] == "task_003"
        assert result_dict["error_message"] is None
        assert result_dict["processing_time"] == 0.8
        
    def test_consume_result_from_dict(self):
        """测试从字典创建消费结果"""
        data = {
            "success": False,
            "task_id": "task_004",
            "error_message": "Test error",
            "processing_time": 1.5
        }
        
        result = ConsumeResult.from_dict(data)
        
        assert result.success is False
        assert result.task_id == "task_004"
        assert result.error_message == "Test error"
        assert result.processing_time == 1.5


class TestRocketMQConsumer:
    """RocketMQ消费者测试类"""
    
    @pytest.fixture
    def mock_connection(self):
        """模拟连接对象"""
        connection = Mock(spec=RocketMQConnection)
        connection.is_connected.return_value = True
        connection.get_consumer_config.return_value = {
            "name_server": "localhost:9876",
            "consumer_group": "test_consumer_group"
        }
        connection.get_connection_info.return_value = Mock(
            topic="test_topic",
            consumer_group="test_consumer_group"
        )
        return connection
    
    @pytest.fixture
    def mock_handler(self):
        """模拟消息处理器"""
        def handler(message: ExportTaskMessage) -> ConsumeResult:
            return ConsumeResult(success=True, task_id=message.task_id)
        return handler
    
    @pytest.fixture
    def consumer(self, mock_connection):
        """创建消费者实例"""
        return RocketMQConsumer(mock_connection)
    
    def test_consumer_init_without_handler(self, mock_connection):
        """测试无处理器初始化消费者"""
        consumer = RocketMQConsumer(mock_connection)
        
        assert consumer.connection == mock_connection
        assert consumer.message_handler is None
        assert consumer._consumer is None
        assert not consumer._is_started
        assert not consumer._is_consuming
        
    def test_consumer_init_with_handler(self, mock_connection, mock_handler):
        """测试带处理器初始化消费者"""
        consumer = RocketMQConsumer(mock_connection, mock_handler)
        
        assert consumer.connection == mock_connection
        assert consumer.message_handler == mock_handler
        assert consumer._consumer is None
        assert not consumer._is_started
        assert not consumer._is_consuming
        
    def test_set_message_handler(self, consumer, mock_handler):
        """测试设置消息处理器"""
        consumer.set_message_handler(mock_handler)
        
        assert consumer.message_handler == mock_handler
        
    @patch('core.rocketmq.consumer.logger')
    def test_start_success(self, mock_logger, consumer, mock_handler, mock_connection):
        """测试启动消费者成功"""
        consumer.message_handler = mock_handler
        mock_connection.is_connected.return_value = True
        
        consumer.start()
        
        assert consumer._is_started
        mock_logger.info.assert_called_with("RocketMQ consumer started successfully")
        
    def test_start_not_connected(self, consumer, mock_handler, mock_connection):
        """测试未连接时启动消费者"""
        consumer.message_handler = mock_handler
        mock_connection.is_connected.return_value = False
        
        with pytest.raises(RocketMQConsumeError) as exc_info:
            consumer.start()
        
        assert "RocketMQ connection is not established" in str(exc_info.value)
        assert not consumer._is_started
        
    def test_start_no_handler(self, consumer, mock_connection):
        """测试无处理器时启动消费者"""
        mock_connection.is_connected.return_value = True
        
        with pytest.raises(RocketMQConsumeError) as exc_info:
            consumer.start()
        
        assert "Message handler is not set" in str(exc_info.value)
        assert not consumer._is_started
        
    @patch('core.rocketmq.consumer.logger')
    def test_stop_success(self, mock_logger, consumer):
        """测试停止消费者成功"""
        consumer._is_started = True
        consumer._consumer = Mock()
        
        consumer.stop()
        
        assert not consumer._is_started
        assert not consumer._is_consuming
        mock_logger.info.assert_called_with("RocketMQ consumer stopped successfully")
        
    @patch('core.rocketmq.consumer.logger')
    def test_start_consuming_success(self, mock_logger, consumer):
        """测试开始消费成功"""
        consumer._is_started = True
        
        consumer.start_consuming()
        
        assert consumer._is_consuming
        mock_logger.info.assert_called_with("Started consuming messages")
        
    def test_start_consuming_not_started(self, consumer):
        """测试未启动时开始消费"""
        consumer._is_started = False
        
        with pytest.raises(RocketMQConsumeError) as exc_info:
            consumer.start_consuming()
        
        assert "Consumer is not started" in str(exc_info.value)
        
    @patch('core.rocketmq.consumer.logger')
    def test_stop_consuming(self, mock_logger, consumer):
        """测试停止消费"""
        consumer._is_consuming = True
        
        consumer.stop_consuming()
        
        assert not consumer._is_consuming
        mock_logger.info.assert_called_with("Stopped consuming messages")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
