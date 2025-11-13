"""
RocketMQ管理器白盒测试

测试RocketMQ管理器的各种场景，包括：
- 管理器初始化
- 组件启动和停止
- 消息发送
- 队列状态获取
- 异常处理
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
from typing import Dict, Any, List

from core.rocketmq.manager import RocketMQManager, get_rocketmq_manager, initialize_rocketmq, start_rocketmq, stop_rocketmq
from core.rocketmq.connection import RocketMQConnection
from core.rocketmq.producer import RocketMQProducer, ExportTaskMessage
from core.rocketmq.consumer import RocketMQConsumer, ConsumeResult
from core.rocketmq.monitor import RocketMQMonitor
from core.rocketmq.exceptions import RocketMQException, RocketMQConfigError
from core.schemas.configs import RocketMQConfig


class TestRocketMQManager:
    """RocketMQ管理器测试类"""
    
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
    
    def test_manager_init_success(self, mock_config):
        """测试管理器初始化成功"""
        with patch('core.rocketmq.manager.get_config', return_value=mock_config):
            manager = RocketMQManager()
            
            assert manager.config == mock_config
            assert manager.connection is None
            assert manager.producer is None
            assert manager.consumer is None
            assert manager.monitor is None
            assert not manager._is_initialized
            assert manager._message_handler is None
            
    def test_manager_init_disabled_config(self):
        """测试RocketMQ未启用时初始化失败"""
        config = Mock()
        config.rocketmq = None
        
        with patch('core.rocketmq.manager.get_config', return_value=config):
            with pytest.raises(RocketMQConfigError) as exc_info:
                RocketMQManager()
            
            assert "RocketMQ is not enabled" in str(exc_info.value)
            
    def test_manager_init_config_disabled(self):
        """测试RocketMQ配置禁用时初始化失败"""
        config = Mock()
        config.rocketmq = RocketMQConfig(
            enabled=False,
            name_server="localhost:9876",
            producer_group="test_producer_group",
            consumer_group="test_consumer_group",
            topic="test_topic"
        )
        
        with patch('core.rocketmq.manager.get_config', return_value=config):
            with pytest.raises(RocketMQConfigError) as exc_info:
                RocketMQManager()
            
            assert "RocketMQ is not enabled" in str(exc_info.value)
            
    @patch('core.rocketmq.manager.logger')
    def test_initialize_success(self, mock_logger, manager):
        """测试初始化成功"""
        with patch('core.rocketmq.manager.RocketMQConnection') as mock_conn_class, \
             patch('core.rocketmq.manager.RocketMQProducer') as mock_prod_class, \
             patch('core.rocketmq.manager.RocketMQConsumer') as mock_cons_class, \
             patch('core.rocketmq.manager.RocketMQMonitor') as mock_mon_class:
            
            mock_connection = Mock()
            mock_producer = Mock()
            mock_consumer = Mock()
            mock_monitor = Mock()
            
            mock_conn_class.return_value = mock_connection
            mock_prod_class.return_value = mock_producer
            mock_cons_class.return_value = mock_consumer
            mock_mon_class.return_value = mock_monitor
            
            manager.initialize()
            
            assert manager._is_initialized
            assert manager.connection == mock_connection
            assert manager.producer == mock_producer
            assert manager.consumer == mock_consumer
            assert manager.monitor == mock_monitor
            mock_logger.info.assert_called_with("RocketMQ manager initialized successfully")
            
    @patch('core.rocketmq.manager.logger')
    def test_initialize_failure(self, mock_logger, manager):
        """测试初始化失败"""
        with patch('core.rocketmq.manager.RocketMQConnection') as mock_conn_class:
            mock_conn_class.side_effect = Exception("Connection failed")
            
            with pytest.raises(RocketMQException) as exc_info:
                manager.initialize()
            
            assert "Failed to initialize RocketMQ manager" in str(exc_info.value)
            assert not manager._is_initialized
            mock_logger.error.assert_called()
            
    @patch('core.rocketmq.manager.logger')
    def test_start_success(self, mock_logger, manager):
        """测试启动成功"""
        # 模拟已初始化状态
        manager._is_initialized = True
        manager.connection = Mock()
        manager.producer = Mock()
        manager.consumer = Mock()
        manager.monitor = Mock()
        manager._message_handler = Mock()
        
        manager.start()
        
        manager.connection.connect.assert_called_once()
        manager.producer.start.assert_called_once()
        manager.consumer.start.assert_called_once()
        manager.consumer.start_consuming.assert_called_once()
        manager.monitor.initialize.assert_called_once()
        mock_logger.info.assert_called_with("RocketMQ manager started successfully")
        
    @patch('core.rocketmq.manager.logger')
    def test_start_without_handler(self, mock_logger, manager):
        """测试无消息处理器时启动"""
        # 模拟已初始化状态
        manager._is_initialized = True
        manager.connection = Mock()
        manager.producer = Mock()
        manager.consumer = Mock()
        manager.monitor = Mock()
        manager._message_handler = None
        
        manager.start()
        
        manager.connection.connect.assert_called_once()
        manager.producer.start.assert_called_once()
        # 无处理器时不应该启动消费者
        manager.consumer.start.assert_not_called()
        manager.consumer.start_consuming.assert_not_called()
        manager.monitor.initialize.assert_called_once()
        
    def test_start_not_initialized(self, manager):
        """测试未初始化时启动"""
        manager._is_initialized = False
        
        # 模拟初始化后的状态
        manager._is_initialized = True
        manager.connection = Mock()
        manager.producer = Mock()
        manager.consumer = Mock()
        manager.monitor = Mock()
        manager._message_handler = Mock()
        
        # 重置为未初始化状态测试自动初始化
        manager._is_initialized = False
        
        with patch.object(manager, 'initialize') as mock_init:
            mock_init.side_effect = lambda: setattr(manager, '_is_initialized', True)
            manager.start()
            mock_init.assert_called_once()
                
    @patch('core.rocketmq.manager.logger')
    def test_start_failure(self, mock_logger, manager):
        """测试启动失败"""
        manager._is_initialized = True
        manager.connection = Mock()
        manager.connection.connect.side_effect = Exception("Connect failed")
        
        with pytest.raises(RocketMQException) as exc_info:
            manager.start()
        
        assert "Failed to start RocketMQ manager" in str(exc_info.value)
        mock_logger.error.assert_called()
        
    @patch('core.rocketmq.manager.logger')
    def test_stop_success(self, mock_logger, manager):
        """测试停止成功"""
        manager.consumer = Mock()
        manager.producer = Mock()
        manager.connection = Mock()
        
        manager.stop()
        
        manager.consumer.stop_consuming.assert_called_once()
        manager.consumer.stop.assert_called_once()
        manager.producer.stop.assert_called_once()
        manager.connection.disconnect.assert_called_once()
        mock_logger.info.assert_called_with("RocketMQ manager stopped successfully")
        
    @patch('core.rocketmq.manager.logger')
    def test_stop_with_error(self, mock_logger, manager):
        """测试停止时发生错误"""
        manager.consumer = Mock()
        manager.consumer.stop_consuming.side_effect = Exception("Stop error")
        manager.producer = Mock()
        manager.connection = Mock()
        
        manager.stop()
        
        # 验证异常被记录
        mock_logger.error.assert_called()
        # 由于异常，后续的stop调用可能不会执行
        # 这是实际的行为，因为try-catch包围了整个方法
        
    def test_set_message_handler(self, manager):
        """测试设置消息处理器"""
        def handler(message: ExportTaskMessage) -> ConsumeResult:
            return ConsumeResult(success=True, task_id=message.task_id)
        
        manager.consumer = Mock()
        
        manager.set_message_handler(handler)
        
        assert manager._message_handler == handler
        manager.consumer.set_message_handler.assert_called_once_with(handler)
        
    def test_set_message_handler_no_consumer(self, manager):
        """测试无消费者时设置消息处理器"""
        def handler(message: ExportTaskMessage) -> ConsumeResult:
            return ConsumeResult(success=True, task_id=message.task_id)
        
        manager.consumer = None
        
        manager.set_message_handler(handler)
        
        assert manager._message_handler == handler
        
    def test_send_export_task_success(self, manager):
        """测试发送导出任务成功"""
        manager.producer = Mock()
        manager.producer.send_export_task.return_value = "task_001"
        
        task_id = manager.send_export_task(
            template_id="template_001",
            data={"title": "测试"},
            output_format="docx",
            priority=1
        )
        
        assert task_id == "task_001"
        manager.producer.send_export_task.assert_called_once_with(
            template_id="template_001",
            data={"title": "测试"},
            output_format="docx",
            template_version=None,
            priority=1,
            task_id=None
        )
        
    def test_send_export_task_no_producer(self, manager):
        """测试无生产者时发送导出任务"""
        manager.producer = None
        
        with pytest.raises(RocketMQException) as exc_info:
            manager.send_export_task(
                template_id="template_001",
                data={"title": "测试"},
                output_format="docx"
            )
        
        assert "Producer is not initialized" in str(exc_info.value)
        
    def test_send_batch_export_tasks_success(self, manager):
        """测试发送批量导出任务成功"""
        manager.producer = Mock()
        manager.producer.send_batch_export_task.return_value = ["task_001", "task_002"]
        
        data_list = [{"title": "报告1"}, {"title": "报告2"}]
        task_ids = manager.send_batch_export_tasks(
            template_id="template_001",
            data_list=data_list,
            output_format="pdf"
        )
        
        assert task_ids == ["task_001", "task_002"]
        manager.producer.send_batch_export_task.assert_called_once_with(
            template_id="template_001",
            data_list=data_list,
            output_format="pdf",
            template_version=None,
            priority=0
        )
        
    def test_get_queue_status_success(self, manager):
        """测试获取队列状态成功"""
        manager.connection = Mock()
        manager.connection.get_connection_info.return_value = Mock(
            topic="test_topic",
            consumer_group="test_group",
            name_server="localhost:9876"
        )
        manager.connection.is_connected.return_value = True
        
        manager.monitor = Mock()
        manager.monitor.get_monitor_metrics.return_value = Mock(
            topic_stats=[Mock(total_messages=100)],
            queue_stats=[Mock(), Mock(), Mock(), Mock()]  # 4个队列
        )
        manager.monitor.get_health_status.return_value = {"healthy": True}
        manager.monitor.get_consumer_lag.return_value = {0: 0, 1: 0, 2: 0, 3: 0}
        
        manager.producer = Mock()
        manager.producer._is_started = True
        manager.consumer = Mock()
        manager.consumer._is_started = True
        manager.consumer._is_consuming = True
        
        status = manager.get_queue_status()
        
        assert status["topic"] == "test_topic"
        assert status["consumer_group"] == "test_group"
        assert status["health"]["healthy"] is True
        assert status["metrics"]["total_messages"] == 100
        assert status["metrics"]["active_queues"] == 4
        assert status["connection"]["connected"] is True
        assert status["components"]["producer_started"] is True
        assert status["components"]["consumer_started"] is True
        assert status["components"]["consumer_consuming"] is True
        
    def test_get_queue_status_error(self, manager):
        """测试获取队列状态时发生错误"""
        manager.monitor = None  # 设置为None来触发异常
        
        with pytest.raises(RocketMQException) as exc_info:
            manager.get_queue_status()
        
        assert "Monitor is not initialized" in str(exc_info.value)
            
    def test_get_performance_metrics_success(self, manager):
        """测试获取性能指标成功"""
        manager.monitor = Mock()
        expected_metrics = {"throughput": 100, "latency": 50}
        manager.monitor.get_performance_metrics.return_value = expected_metrics
        
        metrics = manager.get_performance_metrics()
        
        assert metrics == expected_metrics
        
    def test_get_performance_metrics_no_monitor(self, manager):
        """测试无监控器时获取性能指标"""
        manager.monitor = None
        
        with pytest.raises(RocketMQException) as exc_info:
            manager.get_performance_metrics()
        
        assert "Monitor is not initialized" in str(exc_info.value)
        
    def test_export_monitoring_data_success(self, manager):
        """测试导出监控数据成功"""
        manager.monitor = Mock()
        manager.monitor.export_metrics_json.return_value = '{"metrics": "data"}'
        
        result = manager.export_monitoring_data()
        
        assert result == '{"metrics": "data"}'
        
    def test_is_healthy_true(self, manager):
        """测试健康检查返回True"""
        manager.monitor = Mock()
        manager.monitor.get_health_status.return_value = {"healthy": True}
        
        assert manager.is_healthy() is True
        
    def test_is_healthy_false(self, manager):
        """测试健康检查返回False"""
        manager.monitor = Mock()
        manager.monitor.get_health_status.return_value = {"healthy": False}
        
        assert manager.is_healthy() is False
        
    def test_is_healthy_no_monitor(self, manager):
        """测试无监控器时健康检查"""
        manager.monitor = None
        
        assert manager.is_healthy() is False
        
    def test_is_healthy_exception(self, manager):
        """测试健康检查时发生异常"""
        manager.monitor = Mock()
        manager.monitor.get_health_status.side_effect = Exception("Health check error")
        
        with patch('core.rocketmq.manager.logger') as mock_logger:
            result = manager.is_healthy()
            
            assert result is False
            mock_logger.error.assert_called()
            
    @patch('core.rocketmq.manager.logger')
    def test_restart_consumer_success(self, mock_logger, manager):
        """测试重启消费者成功"""
        manager.consumer = Mock()
        manager._message_handler = Mock()
        
        manager.restart_consumer()
        
        manager.consumer.stop_consuming.assert_called_once()
        manager.consumer.stop.assert_called_once()
        manager.consumer.start.assert_called_once()
        manager.consumer.start_consuming.assert_called_once()
        mock_logger.info.assert_called_with("Consumer restarted successfully")
        
    @patch('core.rocketmq.manager.logger')
    def test_restart_consumer_no_handler(self, mock_logger, manager):
        """测试无处理器时重启消费者"""
        manager.consumer = Mock()
        manager._message_handler = None
        
        manager.restart_consumer()
        
        manager.consumer.stop_consuming.assert_called_once()
        manager.consumer.stop.assert_called_once()
        # 无处理器时不应该启动消费
        manager.consumer.start.assert_not_called()
        mock_logger.warning.assert_called_with("Cannot restart consumer: no message handler set")
        
    @patch('core.rocketmq.manager.logger')
    def test_restart_producer_success(self, mock_logger, manager):
        """测试重启生产者成功"""
        manager.producer = Mock()
        
        manager.restart_producer()
        
        manager.producer.stop.assert_called_once()
        manager.producer.start.assert_called_once()
        mock_logger.info.assert_called_with("Producer restarted successfully")
        
    @pytest.mark.asyncio
    async def test_lifespan_context_success(self, manager):
        """测试异步上下文管理器成功"""
        with patch.object(manager, 'start') as mock_start, \
             patch.object(manager, 'stop') as mock_stop:
            
            async with manager.lifespan_context():
                pass
            
            mock_start.assert_called_once()
            mock_stop.assert_called_once()
            
    @pytest.mark.asyncio
    async def test_lifespan_context_with_exception(self, manager):
        """测试异步上下文管理器异常场景"""
        with patch.object(manager, 'start') as mock_start, \
             patch.object(manager, 'stop') as mock_stop:
            
            with pytest.raises(ValueError):
                async with manager.lifespan_context():
                    raise ValueError("Test exception")
            
            mock_start.assert_called_once()
            mock_stop.assert_called_once()
            
    def test_context_manager_success(self, manager):
        """测试同步上下文管理器成功"""
        with patch.object(manager, 'start') as mock_start, \
             patch.object(manager, 'stop') as mock_stop:
            
            with manager:
                pass
            
            mock_start.assert_called_once()
            mock_stop.assert_called_once()
            
    def test_context_manager_with_exception(self, manager):
        """测试同步上下文管理器异常场景"""
        with patch.object(manager, 'start') as mock_start, \
             patch.object(manager, 'stop') as mock_stop:
            
            with pytest.raises(ValueError):
                with manager:
                    raise ValueError("Test exception")
            
            mock_start.assert_called_once()
            mock_stop.assert_called_once()


class TestGlobalFunctions:
    """全局函数测试类"""
    
    def test_get_rocketmq_manager_singleton(self):
        """测试获取RocketMQ管理器单例"""
        with patch('core.rocketmq.manager.RocketMQManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager
            
            # 重置全局变量
            import core.rocketmq.manager
            core.rocketmq.manager._rocketmq_manager = None
            
            # 第一次调用应该创建新实例
            manager1 = get_rocketmq_manager()
            assert manager1 == mock_manager
            
            # 第二次调用应该返回同一个实例
            manager2 = get_rocketmq_manager()
            assert manager2 == mock_manager
            assert manager1 is manager2
            
            # 只应该创建一次
            mock_manager_class.assert_called_once()
            
    def test_initialize_rocketmq(self):
        """测试初始化全局RocketMQ管理器"""
        with patch('core.rocketmq.manager.get_rocketmq_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager._is_initialized = False
            mock_get_manager.return_value = mock_manager
            
            initialize_rocketmq()
            
            mock_manager.initialize.assert_called_once()
            
    def test_initialize_rocketmq_already_initialized(self):
        """测试初始化已初始化的RocketMQ管理器"""
        with patch('core.rocketmq.manager.get_rocketmq_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager._is_initialized = True
            mock_get_manager.return_value = mock_manager
            
            initialize_rocketmq()
            
            # 已初始化时不应该再次初始化
            mock_manager.initialize.assert_not_called()
            
    def test_start_rocketmq(self):
        """测试启动全局RocketMQ管理器"""
        with patch('core.rocketmq.manager.get_rocketmq_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_get_manager.return_value = mock_manager
            
            start_rocketmq()
            
            mock_manager.start.assert_called_once()
            
    def test_stop_rocketmq(self):
        """测试停止全局RocketMQ管理器"""
        # 设置全局管理器
        import core.rocketmq.manager
        mock_manager = Mock()
        core.rocketmq.manager._rocketmq_manager = mock_manager
        
        stop_rocketmq()
        
        mock_manager.stop.assert_called_once()
        # 全局变量应该被重置
        assert core.rocketmq.manager._rocketmq_manager is None
        
    def test_stop_rocketmq_no_manager(self):
        """测试停止不存在的全局RocketMQ管理器"""
        # 重置全局变量
        import core.rocketmq.manager
        core.rocketmq.manager._rocketmq_manager = None
        
        # 不应该抛出异常
        stop_rocketmq()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
