"""
RocketMQ降级机制测试

测试RocketMQ连接失败时自动降级到内存队列的功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from core.rocketmq.manager import RocketMQManager, get_rocketmq_manager
from core.rocketmq.connection import RocketMQConnection
from core.rocketmq.producer import ExportTaskMessage
from core.rocketmq.consumer import ConsumeResult
from core.schemas.configs import RocketMQConfig
from core.rocketmq.exceptions import RocketMQException


class TestRocketMQFallback:
    """RocketMQ降级机制测试"""

    @pytest.fixture
    def mock_config(self):
        """模拟配置对象"""
        config = Mock()
        config.rocketmq = RocketMQConfig(
            enabled=True,
            name_server="localhost:9876",
            producer_group="test_producer_group",
            consumer_group="test_consumer_group",
            topic="test_topic"
        )
        return config

    @pytest.fixture
    def manager(self, mock_config):
        """创建管理器实例"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            return RocketMQManager()

    def test_fallback_when_client_not_available(self, mock_config):
        """测试RocketMQ客户端不可用时降级"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            with patch('core.rocketmq.connection.RocketMQConnection.connect') as mock_connect:
                # 模拟客户端不可用
                with patch('core.rocketmq.connection.RocketMQConnection.is_client_available', return_value=False):
                    manager = RocketMQManager()
                    manager.start()

                    assert manager._use_memory_fallback
                    assert manager.memory_queue is not None
                    assert manager.connection.is_connected()

                    manager.stop()

    def test_fallback_when_connection_fails(self, mock_config):
        """测试连接失败时降级"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            with patch('core.rocketmq.connection.RocketMQConnection.connect', side_effect=Exception("Connection failed")):
                manager = RocketMQManager()
                manager.start()

                assert manager._use_memory_fallback
                assert manager.memory_queue is not None

                manager.stop()

    def test_normal_rocketmq_when_available(self, mock_config):
        """测试RocketMQ可用时正常使用"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            with patch('core.rocketmq.connection.RocketMQConnection.connect') as mock_connect:
                with patch('core.rocketmq.connection.RocketMQConnection.is_client_available', return_value=True):
                    with patch('core.rocketmq.manager.RocketMQProducer') as mock_producer_class:
                        with patch('core.rocketmq.manager.RocketMQConsumer') as mock_consumer_class:
                            with patch('core.rocketmq.manager.RocketMQMonitor') as mock_monitor_class:

                                manager = RocketMQManager()
                                manager.start()

                                assert not manager._use_memory_fallback
                                assert manager.memory_queue is None
                                assert manager.producer is not None
                                assert manager.consumer is not None
                                assert manager.monitor is not None

                                manager.stop()

    def test_send_export_task_with_fallback(self, mock_config):
        """测试降级模式下发送导出任务"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            with patch('core.rocketmq.connection.RocketMQConnection.connect', side_effect=Exception("Connection failed")):
                manager = RocketMQManager()
                manager.start()

                # 应该使用内存队列
                assert manager._use_memory_fallback

                task_id = manager.send_export_task(
                    template_id="template_001",
                    data={"title": "测试报告"},
                    output_format="docx"
                )

                assert task_id is not None

                manager.stop()

    def test_send_batch_export_tasks_with_fallback(self, mock_config):
        """测试降级模式下发送批量导出任务"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            with patch('core.rocketmq.connection.RocketMQConnection.connect', side_effect=Exception("Connection failed")):
                manager = RocketMQManager()
                manager.start()

                assert manager._use_memory_fallback

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

    def test_get_queue_status_with_fallback(self, mock_config):
        """测试降级模式下获取队列状态"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            with patch('core.rocketmq.connection.RocketMQConnection.connect', side_effect=Exception("Connection failed")):
                manager = RocketMQManager()
                manager.start()

                assert manager._use_memory_fallback

                status = manager.get_queue_status()

                assert "topic" in status
                assert "consumer_group" in status
                assert "health" in status
                assert "metrics" in status
                assert status["health"]["healthy"] is True

                manager.stop()

    def test_get_performance_metrics_with_fallback(self, mock_config):
        """测试降级模式下获取性能指标"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            with patch('core.rocketmq.connection.RocketMQConnection.connect', side_effect=Exception("Connection failed")):
                manager = RocketMQManager()
                manager.start()

                assert manager._use_memory_fallback

                metrics = manager.get_performance_metrics()

                assert "message_throughput" in metrics
                assert "latency" in metrics
                assert "error_rate" in metrics
                assert "queue_size" in metrics

                manager.stop()

    def test_is_healthy_with_fallback(self, mock_config):
        """测试降级模式下的健康检查"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            with patch('core.rocketmq.connection.RocketMQConnection.connect', side_effect=Exception("Connection failed")):
                manager = RocketMQManager()
                manager.start()

                assert manager._use_memory_fallback
                assert manager.is_healthy()

                manager.stop()
                assert not manager.is_healthy()

    def test_restart_consumer_with_fallback(self, mock_config):
        """测试降级模式下重启消费者"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            with patch('core.rocketmq.connection.RocketMQConnection.connect', side_effect=Exception("Connection failed")):
                manager = RocketMQManager()
                manager.start()

                assert manager._use_memory_fallback

                # 重启消费者应该不会抛出异常，但也不会做任何事情
                manager.restart_consumer()  # 应该只是记录警告日志

                manager.stop()

    def test_restart_producer_with_fallback(self, mock_config):
        """测试降级模式下重启生产者"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            with patch('core.rocketmq.connection.RocketMQConnection.connect', side_effect=Exception("Connection failed")):
                manager = RocketMQManager()
                manager.start()

                assert manager._use_memory_fallback

                # 重启生产者应该不会抛出异常，但也不会做任何事情
                manager.restart_producer()  # 应该只是记录警告日志

                manager.stop()

    def test_message_processing_with_fallback(self, mock_config):
        """测试降级模式下的消息处理"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            with patch('core.rocketmq.connection.RocketMQConnection.connect', side_effect=Exception("Connection failed")):
                manager = RocketMQManager()

                processed_tasks = []

                def handler(message):
                    processed_tasks.append(message.task_id)
                    return ConsumeResult(success=True, task_id=message.task_id)

                manager.set_message_handler(handler)
                manager.start()

                assert manager._use_memory_fallback

                # 发送任务
                task_id = manager.send_export_task(
                    template_id="template_001",
                    data={"title": "测试"},
                    output_format="docx"
                )

                # 等待处理
                import time
                time.sleep(0.1)

                assert task_id in processed_tasks

                manager.stop()

    def test_stop_with_fallback(self, mock_config):
        """测试降级模式下的停止操作"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            with patch('core.rocketmq.connection.RocketMQConnection.connect', side_effect=Exception("Connection failed")):
                manager = RocketMQManager()
                manager.start()

                assert manager._use_memory_fallback
                assert manager.memory_queue is not None

                manager.stop()

                assert not manager._is_initialized
                assert manager.memory_queue is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
