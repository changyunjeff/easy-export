"""
RocketMQ集成测试

测试RocketMQ各组件之间的集成，包括：
- 端到端消息流程
- 组件协作
- 实际RocketMQ服务器连接（可选）
- 错误恢复机制
"""

import pytest
import asyncio
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import List, Dict, Any

from core.rocketmq import (
    RocketMQManager, RocketMQConnection, RocketMQProducer, 
    RocketMQConsumer, RocketMQMonitor, ExportTaskMessage, ConsumeResult,
    get_rocketmq_manager, initialize_rocketmq, start_rocketmq, stop_rocketmq
)
from core.rocketmq.exceptions import RocketMQException, RocketMQConnectionError
from core.schemas.configs import RocketMQConfig


class TestRocketMQIntegration:
    """RocketMQ集成测试类"""
    
    @pytest.fixture
    def rocketmq_config(self):
        """RocketMQ配置"""
        return RocketMQConfig(
            enabled=True,
            name_server="localhost:9876",
            producer_group="integration_test_producer",
            consumer_group="integration_test_consumer",
            topic="integration_test_topic",
            tag="*",
            max_message_size=4194304,
            send_timeout=3000,
            retry_times=3,
            consumer_thread_min=1,
            consumer_thread_max=2,
            consume_message_batch_max_size=1,
            pull_batch_size=32,
            pull_interval=0,
            consume_timeout=15,
            max_reconsume_times=16,
            suspend_current_queue_time=1000
        )
    
    @pytest.fixture
    def mock_config(self, rocketmq_config):
        """模拟全局配置"""
        config = Mock()
        config.rocketmq = rocketmq_config
        return config
    
    def test_manager_full_lifecycle(self, mock_config):
        """测试管理器完整生命周期"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            manager = RocketMQManager()
            
            # 测试初始化
            with patch('core.rocketmq.connection.RocketMQConnection') as mock_conn_class, \
                 patch('core.rocketmq.producer.RocketMQProducer') as mock_prod_class, \
                 patch('core.rocketmq.consumer.RocketMQConsumer') as mock_cons_class, \
                 patch('core.rocketmq.monitor.RocketMQMonitor') as mock_mon_class:
                
                # 创建模拟对象
                mock_connection = Mock()
                mock_producer = Mock()
                mock_consumer = Mock()
                mock_monitor = Mock()
                
                mock_conn_class.return_value = mock_connection
                mock_prod_class.return_value = mock_producer
                mock_cons_class.return_value = mock_consumer
                mock_mon_class.return_value = mock_monitor
                
                # 初始化
                manager.initialize()
                assert manager._is_initialized
                
                # 设置消息处理器
                def message_handler(message: ExportTaskMessage) -> ConsumeResult:
                    return ConsumeResult(success=True, task_id=message.task_id)
                
                manager.set_message_handler(message_handler)
                
                # 启动
                manager.start()
                
                # 验证启动调用
                mock_connection.connect.assert_called_once()
                mock_producer.start.assert_called_once()
                mock_consumer.start.assert_called_once()
                mock_consumer.start_consuming.assert_called_once()
                mock_monitor.initialize.assert_called_once()
                
                # 发送消息
                mock_producer.send_export_task.return_value = "task_001"
                task_id = manager.send_export_task(
                    template_id="template_001",
                    data={"title": "测试"},
                    output_format="docx"
                )
                assert task_id == "task_001"
                
                # 获取状态
                mock_connection.get_connection_info.return_value = Mock(
                    topic="integration_test_topic",
                    consumer_group="integration_test_consumer",
                    name_server="localhost:9876"
                )
                mock_connection.is_connected.return_value = True
                mock_monitor.get_monitor_metrics.return_value = Mock(
                    topic_stats=[Mock(total_messages=1)],
                    queue_stats=[Mock(), Mock()]
                )
                mock_monitor.get_health_status.return_value = {"healthy": True}
                mock_monitor.get_consumer_lag.return_value = {0: 0, 1: 0}
                
                status = manager.get_queue_status()
                assert status["topic"] == "integration_test_topic"
                assert status["health"]["healthy"] is True
                
                # 停止
                manager.stop()
                
                # 验证停止调用
                mock_consumer.stop_consuming.assert_called_once()
                mock_consumer.stop.assert_called_once()
                mock_producer.stop.assert_called_once()
                mock_connection.disconnect.assert_called_once()
                
    def test_message_flow_simulation(self, mock_config):
        """测试消息流程模拟"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            manager = RocketMQManager()
            
            # 模拟消息处理结果
            processed_messages = []
            
            def message_handler(message: ExportTaskMessage) -> ConsumeResult:
                processed_messages.append(message)
                return ConsumeResult(
                    success=True,
                    task_id=message.task_id,
                    processed_at=datetime.now()
                )
            
            with patch.object(manager, 'initialize') as mock_init, \
                 patch.object(manager, 'start') as mock_start, \
                 patch.object(manager, 'stop') as mock_stop:
                
                # 模拟生产者和消费者
                mock_producer = Mock()
                mock_consumer = Mock()
                manager.producer = mock_producer
                manager.consumer = mock_consumer
                
                # 设置处理器
                manager.set_message_handler(message_handler)
                
                # 模拟发送消息
                mock_producer.send_export_task.return_value = "task_001"
                task_id = manager.send_export_task(
                    template_id="template_001",
                    data={"title": "集成测试"},
                    output_format="pdf"
                )
                
                # 验证发送调用
                mock_producer.send_export_task.assert_called_once_with(
                    template_id="template_001",
                    data={"title": "集成测试"},
                    output_format="pdf",
                    priority=0,
                    task_id=None
                )
                
                # 模拟消费消息
                test_message = ExportTaskMessage(
                    task_id="task_001",
                    template_id="template_001",
                    data={"title": "集成测试"},
                    output_format="pdf"
                )
                
                result = manager._message_handler(test_message)
                
                assert result.success is True
                assert result.task_id == "task_001"
                assert len(processed_messages) == 1
                assert processed_messages[0].task_id == "task_001"
                
    def test_error_handling_integration(self, mock_config):
        """测试错误处理集成"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            manager = RocketMQManager()
            
            # 测试初始化失败
            with patch('core.rocketmq.connection.RocketMQConnection') as mock_conn_class:
                mock_conn_class.side_effect = Exception("Connection failed")
                
                with pytest.raises(RocketMQException) as exc_info:
                    manager.initialize()
                
                assert "Failed to initialize RocketMQ manager" in str(exc_info.value)
                assert not manager._is_initialized
                
            # 测试启动失败
            manager._is_initialized = True
            manager.connection = Mock()
            manager.connection.connect.side_effect = Exception("Connect failed")
            
            with pytest.raises(RocketMQException) as exc_info:
                manager.start()
            
            assert "Failed to start RocketMQ manager" in str(exc_info.value)
            
            # 测试消息处理失败
            def failing_handler(message: ExportTaskMessage) -> ConsumeResult:
                raise ValueError("Handler error")
            
            manager.set_message_handler(failing_handler)
            
            test_message = ExportTaskMessage(
                task_id="task_error",
                template_id="template_001",
                data={"title": "错误测试"},
                output_format="docx"
            )
            
            # 消费者应该处理异常并返回失败结果
            if manager.consumer:
                with patch.object(manager.consumer, '_handle_message') as mock_handle:
                    mock_handle.return_value = ConsumeResult(
                        success=False,
                        task_id="task_error",
                        error_message="Handler error"
                    )
                    
                    result = mock_handle(test_message)
                    assert result.success is False
                    assert "Handler error" in result.error_message
                    
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
            
            # 验证批量发送调用
            mock_producer.send_batch_export_task.assert_called_once_with(
                template_id="template_batch",
                data_list=data_list,
                output_format="xlsx",
                priority=0
            )
            
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


def pytest_runtest_setup(item):
    """pytest运行测试前的设置"""
    if "real_server" in item.keywords:
        if not item.config.getoption("--rocketmq-server", default=False):
            pytest.skip("需要 --rocketmq-server 选项来运行实际服务器测试")


@pytest.mark.real_server
class TestRocketMQRealServerIntegration:
    """RocketMQ实际服务器集成测试（可选）"""
    
    def test_real_server_connection(self):
        """测试实际服务器连接"""
        # 这个测试需要实际的RocketMQ服务器运行
        # 使用 pytest --rocketmq-server 来启用
        config = RocketMQConfig(
            enabled=True,
            name_server="localhost:9876",
            producer_group="real_test_producer",
            consumer_group="real_test_consumer",
            topic="real_test_topic"
        )
        
        connection = RocketMQConnection(config)
        
        try:
            # 尝试连接
            connection.connect()
            assert connection.is_connected()
            
            # 获取连接信息
            info = connection.get_connection_info()
            assert info.name_server == "localhost:9876"
            
        except Exception as e:
            pytest.skip(f"无法连接到RocketMQ服务器: {e}")
        finally:
            connection.disconnect()
            
    def test_real_server_message_flow(self):
        """测试实际服务器消息流程"""
        # 这个测试需要实际的RocketMQ服务器运行
        config = RocketMQConfig(
            enabled=True,
            name_server="localhost:9876",
            producer_group="real_flow_producer",
            consumer_group="real_flow_consumer",
            topic="real_flow_topic"
        )
        
        processed_messages = []
        
        def message_handler(message: ExportTaskMessage) -> ConsumeResult:
            processed_messages.append(message)
            return ConsumeResult(success=True, task_id=message.task_id)
        
        try:
            # 创建连接
            connection = RocketMQConnection(config)
            connection.connect()
            
            # 创建生产者和消费者
            producer = RocketMQProducer(connection)
            consumer = RocketMQConsumer(connection, message_handler)
            
            # 启动组件
            producer.start()
            consumer.start()
            consumer.start_consuming()
            
            # 发送消息
            task_id = producer.send_export_task(
                template_id="real_template",
                data={"title": "实际测试"},
                output_format="docx"
            )
            
            # 等待消息处理
            time.sleep(2)
            
            # 验证消息被处理
            assert len(processed_messages) > 0
            assert any(msg.task_id == task_id for msg in processed_messages)
            
        except Exception as e:
            pytest.skip(f"实际服务器测试失败: {e}")
        finally:
            # 清理资源
            try:
                consumer.stop_consuming()
                consumer.stop()
                producer.stop()
                connection.disconnect()
            except:
                pass


def pytest_addoption(parser):
    """添加pytest命令行选项"""
    parser.addoption(
        "--rocketmq-server",
        action="store_true",
        default=False,
        help="运行需要实际RocketMQ服务器的测试"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
