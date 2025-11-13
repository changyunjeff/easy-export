"""
RocketMQ队列监控模块

提供RocketMQ队列的实时监控功能，包括队列状态、消息统计、性能指标等。
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from .connection import RocketMQConnection
from .exceptions import RocketMQException

logger = logging.getLogger(__name__)


@dataclass
class QueueStats:
    """队列统计信息"""
    topic: str
    queue_id: int
    broker_name: str
    min_offset: int
    max_offset: int
    last_update_timestamp: int
    
    @property
    def message_count(self) -> int:
        """队列中的消息数量"""
        return max(0, self.max_offset - self.min_offset)


@dataclass
class ConsumerProgress:
    """消费者进度信息"""
    consumer_group: str
    topic: str
    queue_id: int
    broker_name: str
    client_id: str
    consume_offset: int
    last_timestamp: int
    
    def get_lag(self, queue_stats: QueueStats) -> int:
        """计算消费延迟"""
        return max(0, queue_stats.max_offset - self.consume_offset)


@dataclass
class TopicStats:
    """主题统计信息"""
    topic: str
    total_messages: int
    total_queues: int
    producer_count: int
    consumer_groups: List[str]
    last_update: datetime
    
    
@dataclass
class MonitorMetrics:
    """监控指标"""
    timestamp: datetime
    topic_stats: List[TopicStats]
    queue_stats: List[QueueStats]
    consumer_progress: List[ConsumerProgress]
    system_metrics: Dict[str, Any]


@dataclass
class PerformanceMetrics:
    """性能指标"""
    message_throughput: Dict[str, Any]
    latency: Dict[str, Any]
    error_rate: Dict[str, Any]
    time_range: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


class RocketMQMonitor:
    """RocketMQ监控器"""
    
    def __init__(self, connection: RocketMQConnection):
        """
        初始化监控器
        
        Args:
            connection: RocketMQ连接管理器
        """
        self.connection = connection
        self._admin_tool = None
        self._is_initialized = False
        
    def initialize(self) -> None:
        """初始化监控器"""
        try:
            if not self.connection.is_connected():
                self.connection.connect()
                
            # 这里应该初始化RocketMQ管理工具
            # 根据具体的RocketMQ Python客户端库来实现
            # 例如：
            # from rocketmq.admin import AdminTool
            # self._admin_tool = AdminTool(self.connection.get_connection_info().name_server)
            
            self._is_initialized = True
            logger.info("RocketMQ monitor initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize RocketMQ monitor: {str(e)}"
            logger.error(error_msg)
            raise RocketMQException(error_msg)
            
    def get_topic_stats(self, topic: str) -> TopicStats:
        """
        获取主题统计信息
        
        Args:
            topic: 主题名称
            
        Returns:
            TopicStats: 主题统计信息
        """
        if not self._is_initialized:
            self.initialize()
            
        try:
            # 这里应该实现获取主题统计信息的逻辑
            # 根据具体的RocketMQ管理API来实现
            
            # 模拟获取主题统计信息
            total_messages = 0
            total_queues = 4  # 默认队列数
            producer_count = 1
            consumer_groups = [self.connection.get_connection_info().consumer_group]
            
            return TopicStats(
                topic=topic,
                total_messages=total_messages,
                total_queues=total_queues,
                producer_count=producer_count,
                consumer_groups=consumer_groups,
                last_update=datetime.now()
            )
            
        except Exception as e:
            error_msg = f"Failed to get topic stats for {topic}: {str(e)}"
            logger.error(error_msg)
            raise RocketMQException(error_msg)
            
    def get_queue_stats(self, topic: str) -> List[QueueStats]:
        """
        获取队列统计信息
        
        Args:
            topic: 主题名称
            
        Returns:
            List[QueueStats]: 队列统计信息列表
        """
        if not self._is_initialized:
            self.initialize()
            
        try:
            # 这里应该实现获取队列统计信息的逻辑
            
            # 模拟获取队列统计信息
            queue_stats = []
            for queue_id in range(4):  # 假设有4个队列
                stats = QueueStats(
                    topic=topic,
                    queue_id=queue_id,
                    broker_name="broker-a",
                    min_offset=0,
                    max_offset=0,
                    last_update_timestamp=int(datetime.now().timestamp() * 1000)
                )
                queue_stats.append(stats)
                
            return queue_stats
            
        except Exception as e:
            error_msg = f"Failed to get queue stats for {topic}: {str(e)}"
            logger.error(error_msg)
            raise RocketMQException(error_msg)
            
    def get_consumer_progress(self, consumer_group: str, topic: str) -> List[ConsumerProgress]:
        """
        获取消费者进度信息
        
        Args:
            consumer_group: 消费者组
            topic: 主题名称
            
        Returns:
            List[ConsumerProgress]: 消费者进度信息列表
        """
        if not self._is_initialized:
            self.initialize()
            
        try:
            # 这里应该实现获取消费者进度的逻辑
            
            # 模拟获取消费者进度
            progress_list = []
            for queue_id in range(4):  # 假设有4个队列
                progress = ConsumerProgress(
                    consumer_group=consumer_group,
                    topic=topic,
                    queue_id=queue_id,
                    broker_name="broker-a",
                    client_id="client-1",
                    consume_offset=0,
                    last_timestamp=int(datetime.now().timestamp() * 1000)
                )
                progress_list.append(progress)
                
            return progress_list
            
        except Exception as e:
            error_msg = f"Failed to get consumer progress for {consumer_group}/{topic}: {str(e)}"
            logger.error(error_msg)
            raise RocketMQException(error_msg)
            
    def get_consumer_lag(self, consumer_group: str, topic: str) -> Dict[int, int]:
        """
        获取消费者延迟信息
        
        Args:
            consumer_group: 消费者组
            topic: 主题名称
            
        Returns:
            Dict[int, int]: 队列ID到延迟消息数的映射
        """
        try:
            queue_stats = self.get_queue_stats(topic)
            consumer_progress = self.get_consumer_progress(consumer_group, topic)
            
            lag_info = {}
            for progress in consumer_progress:
                # 找到对应的队列统计信息
                queue_stat = next(
                    (qs for qs in queue_stats if qs.queue_id == progress.queue_id),
                    None
                )
                if queue_stat:
                    lag = progress.get_lag(queue_stat)
                    lag_info[progress.queue_id] = lag
                    
            return lag_info
            
        except Exception as e:
            error_msg = f"Failed to get consumer lag for {consumer_group}/{topic}: {str(e)}"
            logger.error(error_msg)
            raise RocketMQException(error_msg)
            
    def get_total_lag(self, consumer_group: str, topic: str) -> int:
        """
        获取总延迟消息数
        
        Args:
            consumer_group: 消费者组
            topic: 主题名称
            
        Returns:
            int: 总延迟消息数
        """
        lag_info = self.get_consumer_lag(consumer_group, topic)
        return sum(lag_info.values())
        
    def get_monitor_metrics(self) -> MonitorMetrics:
        """
        获取完整的监控指标
        
        Returns:
            MonitorMetrics: 监控指标对象
        """
        try:
            connection_info = self.connection.get_connection_info()
            topic = connection_info.topic
            consumer_group = connection_info.consumer_group
            
            # 获取各种统计信息
            topic_stats = [self.get_topic_stats(topic)]
            queue_stats = self.get_queue_stats(topic)
            consumer_progress = self.get_consumer_progress(consumer_group, topic)
            
            # 系统指标
            system_metrics = {
                "name_server": connection_info.name_server,
                "connection_status": self.connection.is_connected(),
                "total_lag": self.get_total_lag(consumer_group, topic),
                "active_queues": len(queue_stats),
                "timestamp": datetime.now().isoformat()
            }
            
            return MonitorMetrics(
                timestamp=datetime.now(),
                topic_stats=topic_stats,
                queue_stats=queue_stats,
                consumer_progress=consumer_progress,
                system_metrics=system_metrics
            )
            
        except Exception as e:
            error_msg = f"Failed to get monitor metrics: {str(e)}"
            logger.error(error_msg)
            raise RocketMQException(error_msg)
            
    def get_health_status(self) -> Dict[str, Any]:
        """
        获取健康状态
        
        Returns:
            Dict[str, Any]: 健康状态信息
        """
        try:
            metrics = self.get_monitor_metrics()
            connection_info = self.connection.get_connection_info()
            
            # 计算健康指标
            total_lag = metrics.system_metrics.get("total_lag", 0)
            is_healthy = (
                self.connection.is_connected() and
                total_lag < 1000  # 延迟消息数小于1000认为健康
            )
            
            return {
                "healthy": is_healthy,
                "connection_status": self.connection.is_connected(),
                "total_lag": total_lag,
                "topic": connection_info.topic,
                "consumer_group": connection_info.consumer_group,
                "last_check": datetime.now().isoformat(),
                "details": {
                    "active_queues": len(metrics.queue_stats),
                    "total_messages": sum(ts.total_messages for ts in metrics.topic_stats),
                    "name_server": connection_info.name_server
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get health status: {str(e)}")
            return {
                "healthy": False,
                "error": str(e),
                "last_check": datetime.now().isoformat()
            }
            
    def get_performance_metrics(self, time_range: timedelta = timedelta(minutes=5)) -> Dict[str, Any]:
        """
        获取性能指标
        
        Args:
            time_range: 时间范围
            
        Returns:
            Dict[str, Any]: 性能指标
        """
        try:
            # 这里应该实现性能指标收集逻辑
            # 可以结合时间序列数据库来存储和查询历史数据
            
            # 模拟性能指标
            return {
                "message_throughput": {
                    "produced_per_second": 0,
                    "consumed_per_second": 0
                },
                "latency": {
                    "average_ms": 0,
                    "p95_ms": 0,
                    "p99_ms": 0
                },
                "error_rate": {
                    "send_error_rate": 0.0,
                    "consume_error_rate": 0.0
                },
                "time_range": {
                    "start": (datetime.now() - time_range).isoformat(),
                    "end": datetime.now().isoformat()
                }
            }
            
        except Exception as e:
            error_msg = f"Failed to get performance metrics: {str(e)}"
            logger.error(error_msg)
            raise RocketMQException(error_msg)
            
    def export_metrics_json(self) -> str:
        """
        导出监控指标为JSON格式
        
        Returns:
            str: JSON格式的监控指标
        """
        import json
        
        try:
            metrics = self.get_monitor_metrics()
            
            # 转换为可序列化的字典
            metrics_dict = {
                "timestamp": metrics.timestamp.isoformat(),
                "topic_stats": [asdict(ts) for ts in metrics.topic_stats],
                "queue_stats": [asdict(qs) for qs in metrics.queue_stats],
                "consumer_progress": [asdict(cp) for cp in metrics.consumer_progress],
                "system_metrics": metrics.system_metrics
            }
            
            return json.dumps(metrics_dict, ensure_ascii=False, indent=2)
            
        except Exception as e:
            error_msg = f"Failed to export metrics to JSON: {str(e)}"
            logger.error(error_msg)
            raise RocketMQException(error_msg)
