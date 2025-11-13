"""
RocketMQ队列监控简化测试

测试RocketMQ队列监控的基本功能，匹配实际的类结构。
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any

from core.rocketmq.monitor import (
    RocketMQMonitor, TopicStats, QueueStats, ConsumerProgress, 
    MonitorMetrics, PerformanceMetrics
)
from core.rocketmq.connection import RocketMQConnection
from core.rocketmq.exceptions import RocketMQException
from core.schemas.configs import RocketMQConfig


class TestTopicStats:
    """主题统计测试类"""
    
    def test_topic_stats_creation(self):
        """测试主题统计创建"""
        last_update = datetime.now()
        stats = TopicStats(
            topic="test_topic",
            total_messages=1000,
            total_queues=4,
            producer_count=2,
            consumer_groups=["group1", "group2"],
            last_update=last_update
        )
        
        assert stats.topic == "test_topic"
        assert stats.total_messages == 1000
        assert stats.total_queues == 4
        assert stats.producer_count == 2
        assert stats.consumer_groups == ["group1", "group2"]
        assert stats.last_update == last_update


class TestQueueStats:
    """队列统计测试类"""
    
    def test_queue_stats_creation(self):
        """测试队列统计创建"""
        stats = QueueStats(
            topic="test_topic",
            queue_id=0,
            broker_name="broker-a",
            min_offset=100,
            max_offset=250,
            last_update_timestamp=1234567890
        )
        
        assert stats.topic == "test_topic"
        assert stats.queue_id == 0
        assert stats.broker_name == "broker-a"
        assert stats.min_offset == 100
        assert stats.max_offset == 250
        assert stats.message_count == 150


class TestConsumerProgress:
    """消费者进度测试类"""
    
    def test_consumer_progress_creation(self):
        """测试消费者进度创建"""
        progress = ConsumerProgress(
            consumer_group="test_group",
            topic="test_topic",
            queue_id=0,
            broker_name="broker-a",
            client_id="client-1",
            consume_offset=200,
            last_timestamp=1234567890
        )
        
        assert progress.consumer_group == "test_group"
        assert progress.topic == "test_topic"
        assert progress.queue_id == 0
        assert progress.consume_offset == 200
        
    def test_get_lag(self):
        """测试计算消费延迟"""
        queue_stats = QueueStats(
            topic="test_topic",
            queue_id=0,
            broker_name="broker-a",
            min_offset=100,
            max_offset=250,
            last_update_timestamp=1234567890
        )
        
        progress = ConsumerProgress(
            consumer_group="test_group",
            topic="test_topic",
            queue_id=0,
            broker_name="broker-a",
            client_id="client-1",
            consume_offset=200,
            last_timestamp=1234567890
        )
        
        lag = progress.get_lag(queue_stats)
        assert lag == 50


class TestPerformanceMetrics:
    """性能指标测试类"""
    
    def test_performance_metrics_creation(self):
        """测试性能指标创建"""
        start_time = datetime.now()
        end_time = datetime.now()
        
        metrics = PerformanceMetrics(
            message_throughput={"produced_per_second": 100, "consumed_per_second": 95},
            latency={"average_ms": 50, "p95_ms": 100, "p99_ms": 200},
            error_rate={"send_error_rate": 0.01, "consume_error_rate": 0.005},
            time_range={"start": start_time, "end": end_time}
        )
        
        assert metrics.message_throughput["produced_per_second"] == 100
        assert metrics.latency["average_ms"] == 50
        assert metrics.error_rate["send_error_rate"] == 0.01
        assert metrics.time_range["start"] == start_time
        
    def test_performance_metrics_to_dict(self):
        """测试性能指标转换为字典"""
        start_time = datetime.now()
        end_time = datetime.now()
        
        metrics = PerformanceMetrics(
            message_throughput={"produced_per_second": 50, "consumed_per_second": 48},
            latency={"average_ms": 30, "p95_ms": 80, "p99_ms": 150},
            error_rate={"send_error_rate": 0.02, "consume_error_rate": 0.01},
            time_range={"start": start_time, "end": end_time}
        )
        
        result = metrics.to_dict()
        
        assert result["message_throughput"]["produced_per_second"] == 50
        assert result["latency"]["average_ms"] == 30
        assert result["error_rate"]["send_error_rate"] == 0.02


class TestRocketMQMonitor:
    """RocketMQ监控器测试类"""
    
    @pytest.fixture
    def mock_connection(self):
        """模拟连接对象"""
        connection = Mock(spec=RocketMQConnection)
        connection.is_connected.return_value = True
        connection.connect.return_value = None
        return connection
    
    @pytest.fixture
    def monitor(self, mock_connection):
        """创建监控器实例"""
        return RocketMQMonitor(mock_connection)
    
    def test_monitor_init(self, mock_connection):
        """测试监控器初始化"""
        monitor = RocketMQMonitor(mock_connection)
        
        assert monitor.connection == mock_connection
        assert not monitor._is_initialized
        assert monitor._admin_tool is None
        
    @patch('core.rocketmq.monitor.logger')
    def test_initialize_success(self, mock_logger, monitor, mock_connection):
        """测试初始化成功"""
        mock_connection.is_connected.return_value = True
        
        monitor.initialize()
        
        assert monitor._is_initialized
        mock_logger.info.assert_called_with("RocketMQ monitor initialized successfully")
        
    @patch('core.rocketmq.monitor.logger')
    def test_initialize_not_connected(self, mock_logger, monitor, mock_connection):
        """测试未连接时初始化"""
        mock_connection.is_connected.return_value = False
        
        monitor.initialize()
        
        # 应该尝试连接
        mock_connection.connect.assert_called_once()
        assert monitor._is_initialized


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
