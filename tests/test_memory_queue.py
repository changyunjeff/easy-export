"""
RocketMQ内存队列降级测试

测试内存队列在RocketMQ不可用时的降级功能。
"""

import pytest
import json
import time
from unittest.mock import Mock, patch
from datetime import datetime

from core.rocketmq.memory_queue import MemoryQueueManager, MemoryQueueProducer, MemoryQueueConsumer, MemoryQueueMessage
from core.rocketmq.connection import RocketMQConnection
from core.rocketmq.producer import ExportTaskMessage
from core.rocketmq.consumer import ConsumeResult
from core.schemas.configs import RocketMQConfig


class TestMemoryQueueMessage:
    """内存队列消息测试"""

    def test_message_creation(self):
        """测试消息创建"""
        message = MemoryQueueMessage(
            message_id="test-id",
            topic="test-topic",
            tag="test-tag",
            body='{"test": "data"}',
            keys="test-key",
            properties={"prop1": "value1"},
            timestamp=datetime.now()
        )

        assert message.message_id == "test-id"
        assert message.topic == "test-topic"
        assert message.tag == "test-tag"
        assert message.body == '{"test": "data"}'
        assert message.keys == "test-key"
        assert message.properties == {"prop1": "value1"}
        assert isinstance(message.timestamp, datetime)

    def test_message_to_dict(self):
        """测试消息转换为字典"""
        timestamp = datetime.now()
        message = MemoryQueueMessage(
            message_id="test-id",
            topic="test-topic",
            tag="test-tag",
            body='{"test": "data"}',
            keys="test-key",
            properties={"prop1": "value1"},
            timestamp=timestamp
        )

        data = message.to_dict()
        assert data["message_id"] == "test-id"
        assert data["topic"] == "test-topic"
        assert data["timestamp"] == timestamp.isoformat()


class TestMemoryQueueProducer:
    """内存队列生产者测试"""

    @pytest.fixture
    def connection(self):
        """模拟连接"""
        config = RocketMQConfig(
            enabled=True,
            name_server="localhost:9876",
            producer_group="test_producer_group",
            consumer_group="test_consumer_group",
            topic="test_topic"
        )
        connection = RocketMQConnection(config)
        return connection

    @pytest.fixture
    def producer(self, connection):
        """创建生产者"""
        return MemoryQueueProducer(connection)

    def test_producer_init(self, producer):
        """测试生产者初始化"""
        assert not producer._is_started
        assert producer._message_queue is None

    def test_producer_start_stop(self, producer):
        """测试生产者启动和停止"""
        producer.start()
        assert producer._is_started
        assert producer._message_queue is not None

        producer.stop()
        assert not producer._is_started

    def test_send_export_task(self, producer):
        """测试发送导出任务"""
        producer.start()

        task_id = producer.send_export_task(
            template_id="template_001",
            data={"title": "测试报告", "content": "测试内容"},
            output_format="docx",
            priority=1
        )

        assert task_id is not None
        assert len(task_id) > 0

        # 检查队列中是否有消息
        assert producer._message_queue.qsize() == 1

        producer.stop()

    def test_send_batch_export_tasks(self, producer):
        """测试发送批量导出任务"""
        producer.start()

        data_list = [
            {"title": "报告1", "content": "内容1"},
            {"title": "报告2", "content": "内容2"}
        ]

        task_ids = producer.send_batch_export_tasks(
            template_id="template_001",
            data_list=data_list,
            output_format="pdf"
        )

        assert len(task_ids) == 2
        assert producer._message_queue.qsize() == 2

        producer.stop()


class TestMemoryQueueConsumer:
    """内存队列消费者测试"""

    @pytest.fixture
    def connection(self):
        """模拟连接"""
        config = RocketMQConfig(
            enabled=True,
            name_server="localhost:9876",
            producer_group="test_producer_group",
            consumer_group="test_consumer_group",
            topic="test_topic"
        )
        connection = RocketMQConnection(config)
        return connection

    @pytest.fixture
    def consumer(self, connection):
        """创建消费者"""
        return MemoryQueueConsumer(connection)

    def test_consumer_init(self, consumer):
        """测试消费者初始化"""
        assert not consumer._is_started
        assert not consumer._is_consuming
        assert consumer._message_queue is None
        assert consumer.message_handler is None

    def test_set_message_handler(self, consumer):
        """测试设置消息处理器"""
        def handler(message):
            return ConsumeResult(success=True, task_id=message.task_id)

        consumer.set_message_handler(handler)
        assert consumer.message_handler == handler

    def test_consumer_start_stop(self, consumer):
        """测试消费者启动和停止"""
        consumer.start()
        assert consumer._is_started
        assert consumer._message_queue is not None

        consumer.stop()
        assert not consumer._is_started
        assert not consumer._is_consuming

    def test_process_message(self, consumer):
        """测试消息处理"""
        processed_messages = []

        def handler(message):
            processed_messages.append(message)
            return ConsumeResult(success=True, task_id=message.task_id)

        consumer.set_message_handler(handler)
        consumer.start()

        # 创建测试消息
        task_message = ExportTaskMessage(
            task_id="test-task-001",
            template_id="template_001",
            data={"title": "测试"},
            output_format="docx"
        )

        queue_message = MemoryQueueMessage(
            message_id="msg-001",
            topic="test_topic",
            tag="EXPORT_TASK",
            body=json.dumps({
                "task_id": task_message.task_id,
                "template_id": task_message.template_id,
                "data": task_message.data,
                "output_format": task_message.output_format,
                "priority": task_message.priority,
                "created_at": task_message.created_at
            }, ensure_ascii=False),
            keys=task_message.task_id,
            properties={},
            timestamp=datetime.now()
        )

        # 处理消息
        result = consumer._process_message(queue_message)

        assert result.success
        assert result.task_id == "test-task-001"
        assert len(processed_messages) == 1

        consumer.stop()


class TestMemoryQueueManager:
    """内存队列管理器测试"""

    @pytest.fixture
    def connection(self):
        """模拟连接"""
        config = RocketMQConfig(
            enabled=True,
            name_server="localhost:9876",
            producer_group="test_producer_group",
            consumer_group="test_consumer_group",
            topic="test_topic"
        )
        connection = RocketMQConnection(config)
        return connection

    @pytest.fixture
    def manager(self, connection):
        """创建管理器"""
        return MemoryQueueManager(connection)

    def test_manager_init(self, manager):
        """测试管理器初始化"""
        assert manager.producer is not None
        assert manager.consumer is None
        assert not manager._is_started

    def test_manager_start_stop(self, manager):
        """测试管理器启动和停止"""
        manager.start()
        assert manager._is_started
        assert manager.consumer is not None
        assert manager.producer._is_started

        manager.stop()
        assert not manager._is_started

    def test_send_export_task(self, manager):
        """测试发送导出任务"""
        manager.start()

        task_id = manager.send_export_task(
            template_id="template_001",
            data={"title": "测试报告"},
            output_format="docx"
        )

        assert task_id is not None

        manager.stop()

    def test_send_batch_export_tasks(self, manager):
        """测试发送批量导出任务"""
        manager.start()

        data_list = [
            {"title": "报告1"},
            {"title": "报告2"}
        ]

        task_ids = manager.send_batch_export_tasks(
            template_id="template_001",
            data_list=data_list,
            output_format="pdf"
        )

        assert len(task_ids) == 2

        manager.stop()

    def test_message_processing(self, manager):
        """测试消息处理流程"""
        processed_tasks = []

        def handler(message):
            processed_tasks.append(message.task_id)
            return ConsumeResult(success=True, task_id=message.task_id)

        manager.set_message_handler(handler)
        manager.start()
        manager.start_consuming()

        # 发送任务
        task_id = manager.send_export_task(
            template_id="template_001",
            data={"title": "测试"},
            output_format="docx"
        )

        # 等待处理
        time.sleep(0.1)

        assert task_id in processed_tasks

        manager.stop()

    def test_get_queue_status(self, manager):
        """测试获取队列状态"""
        manager.start()

        status = manager.get_queue_status()

        assert status["topic"] == "test_topic"
        assert status["consumer_group"] == "test_consumer_group"
        assert status["health"]["healthy"] is True
        assert "metrics" in status
        assert "connection" in status
        assert "components" in status

        manager.stop()

    def test_get_performance_metrics(self, manager):
        """测试获取性能指标"""
        manager.start()

        metrics = manager.get_performance_metrics()

        assert "message_throughput" in metrics
        assert "latency" in metrics
        assert "error_rate" in metrics
        assert "time_range" in metrics
        assert "queue_size" in metrics

        manager.stop()

    def test_is_healthy(self, manager):
        """测试健康检查"""
        assert not manager.is_healthy()

        manager.start()
        assert manager.is_healthy()

        manager.stop()
        assert not manager.is_healthy()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
