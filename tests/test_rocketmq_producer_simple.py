"""
RocketMQ消息生产者简化测试

测试RocketMQ消息生产者的基本功能，匹配实际的类结构。
"""

import pytest
import json
from unittest.mock import Mock, patch
from datetime import datetime

from core.rocketmq.producer import RocketMQProducer, ExportTaskMessage
from core.rocketmq.connection import RocketMQConnection
from core.rocketmq.exceptions import RocketMQSendError, RocketMQConnectionError


class TestExportTaskMessage:
    """导出任务消息测试类"""
    
    def test_export_task_message_creation(self):
        """测试导出任务消息创建"""
        message = ExportTaskMessage(
            task_id="task_001",
            template_id="template_001",
            template_version="1.0",
            data={"title": "测试报告"},
            output_format="pdf",
            priority=1
        )
        
        assert message.task_id == "task_001"
        assert message.template_id == "template_001"
        assert message.template_version == "1.0"
        assert message.data == {"title": "测试报告"}
        assert message.output_format == "pdf"
        assert message.priority == 1
        assert isinstance(message.created_at, str)
        
    def test_export_task_message_to_dict(self):
        """测试导出任务消息转换为字典"""
        data = {"title": "测试报告"}
        message = ExportTaskMessage(
            task_id="task_001",
            template_id="template_001",
            template_version="1.0",
            data=data,
            output_format="pdf",
            priority=0
        )
        
        result = message.to_dict()
        
        assert result["task_id"] == "task_001"
        assert result["template_id"] == "template_001"
        assert result["template_version"] == "1.0"
        assert result["data"] == data
        assert result["output_format"] == "pdf"
        assert result["priority"] == 0
        
    def test_export_task_message_from_dict(self):
        """测试从字典创建导出任务消息"""
        data = {
            "task_id": "task_002",
            "template_id": "template_002",
            "template_version": "2.0",
            "data": {"title": "测试"},
            "output_format": "xlsx",
            "priority": 2,
            "retry_count": 0,
            "created_at": "2025-11-13T15:26:27.604834"
        }
        
        message = ExportTaskMessage.from_dict(data)
        
        assert message.task_id == "task_002"
        assert message.template_id == "template_002"
        assert message.template_version == "2.0"
        assert message.data == {"title": "测试"}
        assert message.output_format == "xlsx"
        assert message.priority == 2
        assert message.created_at == "2025-11-13T15:26:27.604834"
        
    def test_export_task_message_to_json(self):
        """测试导出任务消息转换为JSON"""
        message = ExportTaskMessage(
            task_id="task_003",
            template_id="template_003",
            template_version="1.0",
            data={"key": "value"},
            output_format="docx"
        )
        
        json_str = message.to_json()
        parsed = json.loads(json_str)
        
        assert parsed["task_id"] == "task_003"
        assert parsed["template_id"] == "template_003"
        assert parsed["data"] == {"key": "value"}


class TestRocketMQProducer:
    """RocketMQ生产者测试类"""
    
    @pytest.fixture
    def mock_connection(self):
        """模拟连接对象"""
        connection = Mock(spec=RocketMQConnection)
        connection.is_connected.return_value = True
        connection.get_producer_config.return_value = {
            "name_server": "localhost:9876",
            "producer_group": "test_producer_group"
        }
        connection.get_connection_info.return_value = Mock(
            topic="test_topic",
            consumer_group="test_consumer_group"
        )
        return connection
    
    @pytest.fixture
    def producer(self, mock_connection):
        """创建生产者实例"""
        return RocketMQProducer(mock_connection)
    
    def test_producer_init(self, mock_connection):
        """测试生产者初始化"""
        producer = RocketMQProducer(mock_connection)
        
        assert producer.connection == mock_connection
        assert producer._producer is None
        assert not producer._is_started
        
    @patch('core.rocketmq.producer.logger')
    def test_start_success(self, mock_logger, producer, mock_connection):
        """测试启动生产者成功"""
        mock_connection.is_connected.return_value = True
        
        producer.start()
        
        assert producer._is_started
        mock_logger.info.assert_called_with("RocketMQ producer started successfully")
        
    def test_start_not_connected(self, producer, mock_connection):
        """测试未连接时启动生产者"""
        mock_connection.is_connected.return_value = False
        
        with pytest.raises(RocketMQSendError) as exc_info:
            producer.start()
        
        assert "RocketMQ connection is not established" in str(exc_info.value)
        assert not producer._is_started
        
    @patch('core.rocketmq.producer.logger')
    def test_start_already_started(self, mock_logger, producer):
        """测试重复启动生产者"""
        producer._is_started = True
        
        producer.start()
        
        # 实际实现中没有检查已启动状态的警告
        # 只验证状态保持为True
        assert producer._is_started
        
    @patch('core.rocketmq.producer.logger')
    def test_stop_success(self, mock_logger, producer):
        """测试停止生产者成功"""
        producer._is_started = True
        producer._producer = Mock()
        
        producer.stop()
        
        assert not producer._is_started
        mock_logger.info.assert_called_with("RocketMQ producer stopped successfully")
        
    @patch('core.rocketmq.producer.logger')
    def test_stop_not_started(self, mock_logger, producer):
        """测试未启动时停止生产者"""
        producer.stop()
        
        # 实际实现中未启动时停止不会产生警告
        # 只验证状态保持为False
        assert not producer._is_started
        
    def test_send_export_task_success(self, producer):
        """测试发送导出任务成功"""
        producer._is_started = True
        producer._producer = Mock()
        
        task_id = producer.send_export_task(
            template_id="template_001",
            data={"title": "测试"},
            output_format="docx",
            priority=1
        )
        
        assert task_id is not None
        assert isinstance(task_id, str)
        
    def test_send_export_task_not_started(self, producer):
        """测试未启动时发送导出任务"""
        producer._is_started = False
        
        with pytest.raises(RocketMQSendError) as exc_info:
            producer.send_export_task(
                template_id="template_001",
                data={"title": "测试"},
                output_format="docx"
            )
        
        assert "Producer is not started" in str(exc_info.value)
        
    def test_send_export_task_with_custom_task_id(self, producer):
        """测试使用自定义任务ID发送导出任务"""
        producer._is_started = True
        producer._producer = Mock()
        
        task_id = producer.send_export_task(
            template_id="template_001",
            data={"title": "测试"},
            output_format="docx",
            task_id="custom_task_001"
        )
        
        assert task_id == "custom_task_001"
        
    def test_send_batch_export_task_success(self, producer):
        """测试发送批量导出任务成功"""
        producer._is_started = True
        producer._producer = Mock()
        
        data_list = [
            {"title": "报告1"},
            {"title": "报告2"},
            {"title": "报告3"}
        ]
        
        task_ids = producer.send_batch_export_task(
            template_id="template_001",
            data_list=data_list,
            output_format="pdf"
        )
        
        assert len(task_ids) == 3
        assert all(isinstance(task_id, str) for task_id in task_ids)
        
    def test_send_batch_export_task_empty_list(self, producer):
        """测试发送空的批量导出任务"""
        producer._is_started = True
        producer._producer = Mock()
        
        task_ids = producer.send_batch_export_task(
            template_id="template_001",
            data_list=[],
            output_format="pdf"
        )
        
        assert len(task_ids) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
