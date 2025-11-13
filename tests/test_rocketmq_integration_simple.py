"""
RocketMQ集成简化测试

测试RocketMQ各组件之间的基本集成，匹配实际的类结构。
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from core.rocketmq import (
    RocketMQManager, get_rocketmq_manager, initialize_rocketmq, start_rocketmq, stop_rocketmq
)
from core.rocketmq.producer import ExportTaskMessage
from core.rocketmq.consumer import ConsumeResult
from core.rocketmq.exceptions import RocketMQException
from core.schemas.configs import RocketMQConfig


class TestRocketMQIntegrationSimple:
    """RocketMQ简化集成测试类"""
    
    @pytest.fixture
    def rocketmq_config(self):
        """RocketMQ配置"""
        return RocketMQConfig(
            enabled=True,
            name_server="localhost:9876",
            producer_group="integration_test_producer",
            consumer_group="integration_test_consumer",
            topic="integration_test_topic"
        )
    
    @pytest.fixture
    def mock_config(self, rocketmq_config):
        """模拟全局配置"""
        config = Mock()
        config.rocketmq = rocketmq_config
        return config
    
    def test_manager_basic_lifecycle(self, mock_config):
        """测试管理器基本生命周期"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            manager = RocketMQManager()
            
            # 测试初始化
            manager.initialize()
            assert manager._is_initialized
            
            # 设置消息处理器
            def message_handler(message: ExportTaskMessage) -> ConsumeResult:
                return ConsumeResult(success=True, task_id=message.task_id)
            
            manager.set_message_handler(message_handler)
            assert manager._message_handler == message_handler
            
            # 测试启动
            manager.start()
            
            # 测试停止
            manager.stop()
            
    def test_message_handler_integration(self, mock_config):
        """测试消息处理器集成"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            manager = RocketMQManager()
            
            # 模拟消息处理结果
            processed_messages = []
            
            def message_handler(message: ExportTaskMessage) -> ConsumeResult:
                processed_messages.append(message)
                return ConsumeResult(
                    success=True,
                    task_id=message.task_id
                )
            
            # 设置处理器
            manager.set_message_handler(message_handler)
            
            # 模拟消息
            test_message = ExportTaskMessage(
                task_id="task_001",
                template_id="template_001",
                data={"title": "集成测试"},
                output_format="pdf"
            )
            
            # 调用处理器
            result = manager._message_handler(test_message)
            
            assert result.success is True
            assert result.task_id == "task_001"
            assert len(processed_messages) == 1
            assert processed_messages[0].task_id == "task_001"
            
    def test_send_task_integration(self, mock_config):
        """测试发送任务集成"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            manager = RocketMQManager()
            
            # 模拟生产者
            mock_producer = Mock()
            manager.producer = mock_producer
            mock_producer.send_export_task.return_value = "task_001"
            
            # 发送任务
            task_id = manager.send_export_task(
                template_id="template_001",
                data={"title": "集成测试"},
                output_format="pdf"
            )
            
            assert task_id == "task_001"
            mock_producer.send_export_task.assert_called_once()
            
    def test_batch_processing_integration(self, mock_config):
        """测试批量处理集成"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            manager = RocketMQManager()
            
            # 模拟生产者
            mock_producer = Mock()
            manager.producer = mock_producer
            mock_producer.send_batch_export_task.return_value = [
                "task_001", "task_002", "task_003"
            ]
            
            # 发送批量任务
            data_list = [
                {"title": "报告1", "content": "内容1"},
                {"title": "报告2", "content": "内容2"},
                {"title": "报告3", "content": "内容3"}
            ]
            
            task_ids = manager.send_batch_export_tasks(
                template_id="template_batch",
                data_list=data_list,
                output_format="xlsx"
            )
            
            assert len(task_ids) == 3
            assert task_ids == ["task_001", "task_002", "task_003"]
            
    def test_monitoring_integration(self, mock_config):
        """测试监控集成"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            manager = RocketMQManager()
            
            # 模拟监控器
            mock_monitor = Mock()
            manager.monitor = mock_monitor
            
            # 模拟监控数据
            mock_monitor.get_health_status.return_value = {
                "healthy": True,
                "connection_status": True,
                "total_lag": 5
            }
            
            mock_monitor.get_performance_metrics.return_value = {
                "message_throughput": {"produced_per_second": 50, "consumed_per_second": 48},
                "latency": {"average_ms": 25, "p95_ms": 60, "p99_ms": 120},
                "error_rate": {"send_error_rate": 0.02, "consume_error_rate": 0.01}
            }
            
            mock_monitor.export_metrics_json.return_value = '{"test": "data"}'
            
            # 测试健康检查
            assert manager.is_healthy() is True
            
            # 测试性能指标
            metrics = manager.get_performance_metrics()
            assert metrics["message_throughput"]["produced_per_second"] == 50
            
            # 测试监控数据导出
            json_data = manager.export_monitoring_data()
            assert json_data == '{"test": "data"}'
            
    def test_component_restart_integration(self, mock_config):
        """测试组件重启集成"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            manager = RocketMQManager()
            
            # 模拟组件
            mock_producer = Mock()
            mock_consumer = Mock()
            manager.producer = mock_producer
            manager.consumer = mock_consumer
            manager._message_handler = Mock()
            
            # 测试重启生产者
            manager.restart_producer()
            mock_producer.stop.assert_called_once()
            mock_producer.start.assert_called_once()
            
            # 测试重启消费者
            manager.restart_consumer()
            mock_consumer.stop_consuming.assert_called_once()
            mock_consumer.stop.assert_called_once()
            mock_consumer.start.assert_called_once()
            mock_consumer.start_consuming.assert_called_once()
            
    def test_context_manager_integration(self, mock_config):
        """测试上下文管理器集成"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            manager = RocketMQManager()
            
            with patch.object(manager, 'start') as mock_start, \
                 patch.object(manager, 'stop') as mock_stop:
                
                # 测试同步上下文管理器
                with manager:
                    pass
                
                mock_start.assert_called_once()
                mock_stop.assert_called_once()
                
    @pytest.mark.asyncio
    async def test_async_context_manager_integration(self, mock_config):
        """测试异步上下文管理器集成"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            manager = RocketMQManager()
            
            with patch.object(manager, 'start') as mock_start, \
                 patch.object(manager, 'stop') as mock_stop:
                
                # 测试异步上下文管理器
                async with manager.lifespan_context():
                    pass
                
                mock_start.assert_called_once()
                mock_stop.assert_called_once()
                
    def test_global_manager_integration(self, mock_config):
        """测试全局管理器集成"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            # 重置全局管理器
            import core.rocketmq.manager
            core.rocketmq.manager._rocketmq_manager = None
            
            # 测试获取全局管理器
            manager1 = get_rocketmq_manager()
            manager2 = get_rocketmq_manager()
            
            # 应该是同一个实例
            assert manager1 is manager2
            
            # 测试初始化
            with patch.object(manager1, 'initialize') as mock_init:
                manager1._is_initialized = False
                initialize_rocketmq()
                mock_init.assert_called_once()
                
            # 测试启动
            with patch.object(manager1, 'start') as mock_start:
                start_rocketmq()
                mock_start.assert_called_once()
                
            # 测试停止
            with patch.object(manager1, 'stop') as mock_stop:
                stop_rocketmq()
                mock_stop.assert_called_once()
                
            # 全局管理器应该被重置
            assert core.rocketmq.manager._rocketmq_manager is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
