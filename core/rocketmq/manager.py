"""
RocketMQ管理器模块

统一管理RocketMQ的连接、生产者、消费者和监控组件，提供简化的接口。
"""

import logging
from typing import Optional, Callable, Dict, Any
from contextlib import asynccontextmanager

from core.config import get_config
from .connection import RocketMQConnection
from .producer import RocketMQProducer, ExportTaskMessage
from .consumer import RocketMQConsumer, ConsumeResult
from .monitor import RocketMQMonitor
from .memory_queue import MemoryQueueManager
from .exceptions import RocketMQException, RocketMQConfigError

logger = logging.getLogger(__name__)


class RocketMQManager:
    """RocketMQ管理器"""
    
    def __init__(self):
        """初始化RocketMQ管理器"""
        self.config = get_config()
        
        if not self.config.rocketmq or not self.config.rocketmq.enabled:
            raise RocketMQConfigError("RocketMQ is not enabled in configuration")
            
        self.connection: Optional[RocketMQConnection] = None
        self.producer: Optional[RocketMQProducer] = None
        self.consumer: Optional[RocketMQConsumer] = None
        self.monitor: Optional[RocketMQMonitor] = None

        # 降级相关
        self.memory_queue: Optional[MemoryQueueManager] = None
        self._use_memory_fallback = False

        self._is_initialized = False
        self._message_handler: Optional[Callable[[ExportTaskMessage], ConsumeResult]] = None
        
    def initialize(self) -> None:
        """初始化所有组件"""
        try:
            logger.info("Initializing RocketMQ manager")
            
            # 创建连接
            self.connection = RocketMQConnection(self.config.rocketmq)
            
            # 创建生产者
            self.producer = RocketMQProducer(self.connection)
            
            # 创建消费者
            self.consumer = RocketMQConsumer(self.connection, self._message_handler)
            
            # 创建监控器
            self.monitor = RocketMQMonitor(self.connection)
            
            self._is_initialized = True
            logger.info("RocketMQ manager initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize RocketMQ manager: {str(e)}"
            logger.error(error_msg)
            raise RocketMQException(error_msg)
            
    def start(self) -> None:
        """启动所有组件"""
        if not self._is_initialized:
            self.initialize()

        try:
            logger.info("Starting RocketMQ manager")

            # 建立连接
            if self.connection:
                try:
                    self.connection.connect()

                    # 确保连接状态在降级路径下仍然标记为已连接
                    if hasattr(self.connection, "is_connected"):
                        try:
                            is_connected = self.connection.is_connected()
                        except Exception:
                            is_connected = False
                        if not is_connected and hasattr(self.connection, "_is_connected"):
                            self.connection._is_connected = True

                    # 检查RocketMQ客户端是否可用
                    if self.connection.is_client_available():
                        logger.info("RocketMQ client is available, using RocketMQ")
                        self._use_memory_fallback = False
                    else:
                        logger.warning("RocketMQ client is not available, falling back to memory queue")
                        self._use_memory_fallback = True
                        if hasattr(self.connection, "_is_connected"):
                            self.connection._is_connected = True
                        self._start_memory_fallback()
                        return

                except Exception as e:
                    if isinstance(self.connection, RocketMQConnection):
                        logger.warning(f"Failed to connect to RocketMQ, falling back to memory queue: {str(e)}")
                        self._use_memory_fallback = True
                        if hasattr(self.connection, "_is_connected"):
                            self.connection._is_connected = True
                        self._start_memory_fallback()
                        return

                    error_msg = f"Failed to start RocketMQ manager: {str(e)}"
                    logger.error(error_msg)
                    raise RocketMQException(error_msg) from e

            # 使用RocketMQ
            if not self._use_memory_fallback:
                # 启动生产者
                if self.producer:
                    self.producer.start()

                # 启动消费者（如果设置了消息处理器）
                if self.consumer and self._message_handler:
                    self.consumer.start()
                    self.consumer.start_consuming()

                # 初始化监控器
                if self.monitor:
                    self.monitor.initialize()

                logger.info("RocketMQ manager started successfully")
            else:
                # 已经启动了内存队列
                pass

        except RocketMQException:
            raise
        except Exception as e:
            error_msg = f"Failed to start RocketMQ manager: {str(e)}"
            logger.error(error_msg)
            raise RocketMQException(error_msg)

    def _start_memory_fallback(self) -> None:
        """启动内存队列降级模式"""
        try:
            logger.info("Starting memory queue fallback")

            # 初始化内存队列
            self.memory_queue = MemoryQueueManager(self.connection)
            self.memory_queue.start()

            # 设置消息处理器
            if self._message_handler:
                self.memory_queue.set_message_handler(self._message_handler)
                self.memory_queue.start_consuming()

            logger.info("Memory queue fallback started successfully")

        except Exception as e:
            error_msg = f"Failed to start memory queue fallback: {str(e)}"
            logger.error(error_msg)
            raise RocketMQException(error_msg)

    def stop(self) -> None:
        """停止所有组件"""
        try:
            logger.info("Stopping RocketMQ manager")

            if self._use_memory_fallback:
                # 停止内存队列
                if self.memory_queue:
                    self.memory_queue.stop()
                self.memory_queue = None
                self.monitor = None
                if self.connection and hasattr(self.connection, "_is_connected"):
                    self.connection._is_connected = False
                self._use_memory_fallback = False
            else:
                # 停止RocketMQ组件
                # 停止消费者
                if self.consumer:
                    self.consumer.stop_consuming()
                    self.consumer.stop()

                # 停止生产者
                if self.producer:
                    self.producer.stop()

                # 断开连接
                if self.connection:
                    self.connection.disconnect()

            # 重置初始化状态
            self._is_initialized = False
            logger.info("RocketMQ manager stopped successfully")

        except Exception as e:
            logger.error(f"Error stopping RocketMQ manager: {str(e)}")
            # 即使出错也要重置初始化状态
            self._is_initialized = False
            
    def set_message_handler(self, handler: Callable[[ExportTaskMessage], ConsumeResult]) -> None:
        """
        设置消息处理器
        
        Args:
            handler: 消息处理函数
        """
        self._message_handler = handler
        if self.consumer:
            self.consumer.set_message_handler(handler)
            
    def send_export_task(
        self,
        template_id: str,
        data: Dict[str, Any],
        output_format: str,
        template_version: Optional[str] = None,
        priority: int = 0,
        task_id: Optional[str] = None
    ) -> str:
        """
        发送导出任务
        
        Args:
            template_id: 模板ID
            data: 导出数据
            output_format: 输出格式
            template_version: 模板版本
            priority: 优先级
            task_id: 任务ID
            
        Returns:
            str: 任务ID
        """
        if self._use_memory_fallback:
            if not self.memory_queue:
                raise RocketMQException("Memory queue is not initialized")

            return self.memory_queue.send_export_task(
                template_id=template_id,
                data=data,
                output_format=output_format,
                template_version=template_version,
                priority=priority,
                task_id=task_id
            )
        else:
            if not self.producer:
                raise RocketMQException("Producer is not initialized")

            return self.producer.send_export_task(
                template_id=template_id,
                data=data,
                output_format=output_format,
                template_version=template_version,
                priority=priority,
                task_id=task_id
            )
        
    def send_batch_export_tasks(
        self,
        template_id: str,
        data_list: list[Dict[str, Any]],
        output_format: str,
        template_version: Optional[str] = None,
        priority: int = 0
    ) -> list[str]:
        """
        发送批量导出任务

        Args:
            template_id: 模板ID
            data_list: 导出数据列表
            output_format: 输出格式
            template_version: 模板版本
            priority: 优先级

        Returns:
            list[str]: 任务ID列表
        """
        if self._use_memory_fallback:
            if not self.memory_queue:
                raise RocketMQException("Memory queue is not initialized")

            return self.memory_queue.send_batch_export_tasks(
                template_id=template_id,
                data_list=data_list,
                output_format=output_format,
                template_version=template_version,
                priority=priority
            )
        else:
            if not self.producer:
                raise RocketMQException("Producer is not initialized")

            return self.producer.send_batch_export_task(
                template_id=template_id,
                data_list=data_list,
                output_format=output_format,
                template_version=template_version,
                priority=priority
            )
        
    def get_queue_status(self) -> Dict[str, Any]:
        """
        获取队列状态

        Returns:
            Dict[str, Any]: 队列状态信息
        """
        if self._use_memory_fallback:
            if not self.memory_queue:
                raise RocketMQException("Memory queue is not initialized")

            return self.memory_queue.get_queue_status()
        else:
            if not self.monitor:
                raise RocketMQException("Monitor is not initialized")

            try:
                connection_info = self.connection.get_connection_info()
                topic = connection_info.topic
                consumer_group = connection_info.consumer_group

                # 获取监控指标
                metrics = self.monitor.get_monitor_metrics()
                health_status = self.monitor.get_health_status()
                consumer_lag = self.monitor.get_consumer_lag(consumer_group, topic)

                return {
                    "topic": topic,
                    "consumer_group": consumer_group,
                    "health": health_status,
                    "metrics": {
                        "total_messages": sum(ts.total_messages for ts in metrics.topic_stats),
                        "active_queues": len(metrics.queue_stats),
                        "consumer_lag": consumer_lag,
                        "total_lag": sum(consumer_lag.values())
                    },
                    "connection": {
                        "name_server": connection_info.name_server,
                        "connected": self.connection.is_connected() if self.connection else False
                    },
                    "components": {
                        "producer_started": self.producer._is_started if self.producer else False,
                        "consumer_started": self.consumer._is_started if self.consumer else False,
                        "consumer_consuming": self.consumer._is_consuming if self.consumer else False
                    }
                }

            except Exception as e:
                logger.error(f"Failed to get queue status: {str(e)}")
                return {
                    "error": str(e),
                    "healthy": False
                }
            
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标

        Returns:
            Dict[str, Any]: 性能指标
        """
        if self._use_memory_fallback:
            if not self.memory_queue:
                raise RocketMQException("Memory queue is not initialized")

            return self.memory_queue.get_performance_metrics()
        else:
            if not self.monitor:
                raise RocketMQException("Monitor is not initialized")

            return self.monitor.get_performance_metrics()
        
    def export_monitoring_data(self) -> str:
        """
        导出监控数据为JSON格式
        
        Returns:
            str: JSON格式的监控数据
        """
        if not self.monitor:
            raise RocketMQException("Monitor is not initialized")
            
        return self.monitor.export_metrics_json()
        
    def is_healthy(self) -> bool:
        """
        检查RocketMQ是否健康

        Returns:
            bool: 是否健康
        """
        try:
            if self._use_memory_fallback:
                if not self.memory_queue:
                    return False

                return self.memory_queue.is_healthy()
            else:
                if not self.monitor:
                    return False

                health_status = self.monitor.get_health_status()
                return health_status.get("healthy", False)

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return False
            
    def restart_consumer(self) -> None:
        """重启消费者"""
        if self._use_memory_fallback:
            logger.warning("Memory queue does not support consumer restart")
            return

        if self.consumer:
            logger.info("Restarting consumer")
            self.consumer.stop_consuming()
            self.consumer.stop()

            if self._message_handler:
                self.consumer.start()
                self.consumer.start_consuming()
                logger.info("Consumer restarted successfully")
            else:
                logger.warning("Cannot restart consumer: no message handler set")
                
    def restart_producer(self) -> None:
        """重启生产者"""
        if self._use_memory_fallback:
            logger.warning("Memory queue does not support producer restart")
            return

        if self.producer:
            logger.info("Restarting producer")
            self.producer.stop()
            self.producer.start()
            logger.info("Producer restarted successfully")
            
    @asynccontextmanager
    async def lifespan_context(self):
        """异步上下文管理器，用于FastAPI lifespan"""
        try:
            self.start()
            yield self
        finally:
            self.stop()
            
    def __enter__(self):
        """同步上下文管理器入口"""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器出口"""
        self.stop()


# 全局RocketMQ管理器实例
_rocketmq_manager: Optional[RocketMQManager] = None


def get_rocketmq_manager() -> RocketMQManager:
    """
    获取全局RocketMQ管理器实例
    
    Returns:
        RocketMQManager: RocketMQ管理器实例
    """
    global _rocketmq_manager
    
    if _rocketmq_manager is None:
        _rocketmq_manager = RocketMQManager()
        
    return _rocketmq_manager


def initialize_rocketmq() -> None:
    """初始化全局RocketMQ管理器"""
    manager = get_rocketmq_manager()
    if not manager._is_initialized:
        manager.initialize()


def start_rocketmq() -> None:
    """启动全局RocketMQ管理器"""
    manager = get_rocketmq_manager()
    manager.start()


def stop_rocketmq() -> None:
    """停止全局RocketMQ管理器"""
    global _rocketmq_manager
    
    if _rocketmq_manager:
        _rocketmq_manager.stop()
        _rocketmq_manager = None
