"""
RocketMQ内存队列降级实现

当RocketMQ服务器不可用时，提供基于内存的简单消息队列实现。
"""

import json
import logging
import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional, Callable, List, Union
from dataclasses import dataclass, asdict
from queue import Queue, Empty
import uuid

from .connection import RocketMQConnection
from .producer import ExportTaskMessage
from .consumer import ConsumeResult
from .exceptions import RocketMQException, RocketMQSendError, RocketMQConsumeError

logger = logging.getLogger(__name__)


@dataclass
class MemoryQueueMessage:
    """内存队列消息"""
    message_id: str
    topic: str
    tag: str
    body: str
    keys: Optional[str]
    properties: Dict[str, str]
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "message_id": self.message_id,
            "topic": self.topic,
            "tag": self.tag,
            "body": self.body,
            "keys": self.keys,
            "properties": self.properties,
            "timestamp": self.timestamp.isoformat()
        }


class MemoryQueueProducer:
    """内存队列生产者"""

    def __init__(self, connection: RocketMQConnection):
        """
        初始化内存队列生产者

        Args:
            connection: RocketMQ连接管理器
        """
        self.connection = connection
        self._is_started = False
        self._message_queue: Optional[Queue] = None

    def start(self, message_queue: Optional[Queue] = None) -> None:
        """启动生产者"""
        if not self._is_started:
            self._message_queue = message_queue if message_queue is not None else Queue()
            self._is_started = True
            logger.info("Memory queue producer started")
        elif message_queue is not None and self._message_queue is not message_queue:
            # 允许在运行时更新为共享队列
            self._message_queue = message_queue
            logger.debug("Memory queue producer bound to external queue")

    def stop(self) -> None:
        """停止生产者"""
        self._is_started = False
        self._message_queue = None
        logger.info("Memory queue producer stopped")

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
        发送导出任务消息

        Args:
            template_id: 模板ID
            data: 导出数据
            output_format: 输出格式
            template_version: 模板版本
            priority: 优先级
            task_id: 任务ID

        Returns:
            str: 任务ID

        Raises:
            RocketMQSendError: 发送失败时抛出
        """
        if not self._is_started:
            raise RocketMQSendError("Memory queue producer is not started")

        if task_id is None:
            task_id = str(uuid.uuid4())

        # 创建任务消息
        task_message = ExportTaskMessage(
            task_id=task_id,
            template_id=template_id,
            data=data,
            output_format=output_format,
            priority=priority
        )

        try:
            # 创建队列消息
            queue_message = MemoryQueueMessage(
                message_id=str(uuid.uuid4()),
                topic=self.connection.get_connection_info().topic,
                tag="EXPORT_TASK",
                body=json.dumps(asdict(task_message), ensure_ascii=False),
                keys=task_id,
                properties={
                    "TASK_ID": task_id,
                    "TEMPLATE_ID": template_id,
                    "OUTPUT_FORMAT": output_format,
                    "PRIORITY": str(priority)
                },
                timestamp=datetime.now()
            )

            # 放入队列
            self._message_queue.put(queue_message)

            logger.info(f"Export task message sent to memory queue: {task_id}")
            return task_id

        except Exception as e:
            error_msg = f"Failed to send export task message to memory queue: {str(e)}"
            logger.error(error_msg)
            raise RocketMQSendError(error_msg, task_id=task_id)

    def send_batch_export_tasks(
        self,
        template_id: str,
        data_list: list[Dict[str, Any]],
        output_format: str,
        template_version: Optional[str] = None,
        priority: int = 0
    ) -> list[str]:
        """
        发送批量导出任务消息

        Args:
            template_id: 模板ID
            data_list: 导出数据列表
            output_format: 输出格式
            template_version: 模板版本
            priority: 优先级

        Returns:
            list[str]: 任务ID列表
        """
        task_ids = []

        for data in data_list:
            task_id = self.send_export_task(
                template_id=template_id,
                data=data,
                output_format=output_format,
                template_version=template_version,
                priority=priority
            )
            task_ids.append(task_id)

        logger.info(f"Batch export tasks sent to memory queue: {len(task_ids)} tasks")
        return task_ids


class MemoryQueueConsumer:
    """内存队列消费者"""

    def __init__(
        self,
        connection: RocketMQConnection,
        message_handler: Optional[Callable[[ExportTaskMessage], ConsumeResult]] = None
    ):
        """
        初始化内存队列消费者

        Args:
            connection: RocketMQ连接管理器
            message_handler: 消息处理函数
        """
        self.connection = connection
        self.message_handler = message_handler
        self._is_started = False
        self._is_consuming = False
        self._message_queue: Optional[Queue] = None
        self._consume_thread: Optional[threading.Thread] = None

    def set_message_handler(self, handler: Callable[[ExportTaskMessage], ConsumeResult]) -> None:
        """
        设置消息处理函数

        Args:
            handler: 消息处理函数
        """
        self.message_handler = handler

    def start(self, message_queue: Optional[Queue] = None) -> None:
        """启动消费者"""
        if not self._is_started:
            self._message_queue = message_queue if message_queue is not None else Queue()
            self._is_started = True
            logger.info("Memory queue consumer started")
        elif message_queue is not None and self._message_queue is not message_queue:
            self._message_queue = message_queue
            logger.debug("Memory queue consumer bound to external queue")

    def stop(self) -> None:
        """停止消费者"""
        if self._is_started:
            self._is_consuming = False

            if self._consume_thread and self._consume_thread.is_alive():
                self._consume_thread.join(timeout=5)

            self._is_started = False
            self._message_queue = None
            logger.info("Memory queue consumer stopped")

    def start_consuming(self) -> None:
        """开始消费消息"""
        if not self._is_started:
            raise RocketMQConsumeError("Memory queue consumer is not started")

        if not self.message_handler:
            raise RocketMQConsumeError("Message handler is not set")

        self._is_consuming = True

        # 启动消费线程
        self._consume_thread = threading.Thread(target=self._consume_loop, daemon=True)
        self._consume_thread.start()

        logger.info("Started consuming messages from memory queue")

    def stop_consuming(self) -> None:
        """停止消费消息"""
        self._is_consuming = False
        logger.info("Stopped consuming messages from memory queue")

    def _consume_loop(self) -> None:
        """消费循环"""
        logger.info("Memory queue consumer loop started")

        while self._is_consuming:
            try:
                # 从队列获取消息，带超时
                message = self._message_queue.get(timeout=1)

                if message:
                    self._process_message(message)
                    self._message_queue.task_done()

            except Empty:
                # 队列为空，继续等待
                continue
            except Exception as e:
                logger.error(f"Error in consume loop: {str(e)}")
                time.sleep(1)  # 避免过于频繁的错误日志

        logger.info("Memory queue consumer loop stopped")

    def _process_message(self, message: MemoryQueueMessage) -> ConsumeResult:
        """
        处理单个消息

        Args:
            message: 队列消息
        """
        start_time = datetime.now()
        task_id = message.keys or message.properties.get("TASK_ID") if message.properties else None
        task_id = task_id or "unknown"

        try:
            # 解析任务消息
            task_data = json.loads(message.body)
            task_message = ExportTaskMessage(**task_data)
            task_id = task_message.task_id

            logger.info(f"Processing export task from memory queue: {task_id}")

            # 调用消息处理函数
            if self.message_handler:
                result = self.message_handler(task_message)
                if not isinstance(result, ConsumeResult):
                    raise TypeError("Message handler must return ConsumeResult")

                processing_time = (datetime.now() - start_time).total_seconds()
                result.processing_time = processing_time

                if result.success:
                    logger.info(
                        f"Successfully processed task {task_id} from memory queue "
                        f"in {processing_time:.4f}s"
                    )
                else:
                    logger.error(
                        f"Failed to process task {task_id} from memory queue: {result.error_message}"
                    )

                return result

            error_msg = f"No message handler configured for task {task_id}"
            logger.error(error_msg)
            return ConsumeResult(
                success=False,
                task_id=task_id,
                error_message=error_msg,
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message JSON from memory queue: {str(e)}")
            return ConsumeResult(
                success=False,
                task_id=task_id,
                error_message=f"JSON decode error: {str(e)}",
                processing_time=(datetime.now() - start_time).total_seconds(),
            )
        except Exception as e:
            logger.error(f"Error processing message from memory queue: {str(e)}", exc_info=True)
            return ConsumeResult(
                success=False,
                task_id=task_id,
                error_message=str(e),
                processing_time=(datetime.now() - start_time).total_seconds(),
            )

    def get_consumer_stats(self) -> Dict[str, Any]:
        """
        获取消费者统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "is_started": self._is_started,
            "is_consuming": self._is_consuming,
            "queue_size": self._message_queue.qsize() if self._message_queue else 0,
            "consumer_group": self.connection.get_connection_info().consumer_group,
            "topic": self.connection.get_connection_info().topic,
            "tag": self.connection.get_connection_info().tag
        }


class MemoryQueueManager:
    """内存队列管理器"""

    def __init__(self, connection: RocketMQConnection):
        """
        初始化内存队列管理器

        Args:
            connection: RocketMQ连接管理器
        """
        self.connection = connection
        self.producer = MemoryQueueProducer(connection)
        self.consumer: Optional[MemoryQueueConsumer] = None
        self._message_handler: Optional[Callable[[ExportTaskMessage], ConsumeResult]] = None
        self._is_started = False
        self._message_queue: Optional[Queue] = None

    def start(self) -> None:
        """启动内存队列"""
        if not self._is_started:
            self._message_queue = Queue()
            self.producer.start(self._message_queue)

            # 创建消费者但不自动启动消费，需要手动调用
            self.consumer = MemoryQueueConsumer(self.connection)

            # 如果之前设置了处理器，现在应用到消费者
            if self._message_handler:
                self.consumer.set_message_handler(self._message_handler)

            self.consumer.start(self._message_queue)

            self._is_started = True
            logger.info("Memory queue manager started")

    def stop(self) -> None:
        """停止内存队列"""
        if self._is_started:
            if self.consumer:
                self.consumer.stop()

            self.producer.stop()
            self._message_queue = None
            self._is_started = False
            logger.info("Memory queue manager stopped")

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
        return self.producer.send_batch_export_tasks(
            template_id=template_id,
            data_list=data_list,
            output_format=output_format,
            template_version=template_version,
            priority=priority
        )

    def start_consuming(self) -> None:
        """开始消费消息"""
        if not self._is_started:
            raise RocketMQConsumeError("Memory queue manager is not started")

        if not self.consumer:
            raise RocketMQConsumeError("Memory queue consumer is not initialized")

        if not self._message_queue:
            self._message_queue = Queue()
            self.producer.start(self._message_queue)

        if not self.consumer._is_started:
            self.consumer.start(self._message_queue)

        self.consumer.start_consuming()

    def get_queue_status(self) -> Dict[str, Any]:
        """
        获取队列状态

        Returns:
            Dict[str, Any]: 队列状态信息
        """
        consumer_stats = self.consumer.get_consumer_stats() if self.consumer else {}

        return {
            "topic": self.connection.get_connection_info().topic,
            "consumer_group": self.connection.get_connection_info().consumer_group,
            "health": {
                "healthy": True,
                "connection_status": True,
                "total_lag": consumer_stats.get("queue_size", 0)
            },
            "metrics": {
                "total_messages": consumer_stats.get("queue_size", 0),
                "active_queues": 1,
                "consumer_lag": {
                    "0": consumer_stats.get("queue_size", 0)
                },
                "total_lag": consumer_stats.get("queue_size", 0)
            },
            "connection": {
                "name_server": "memory",
                "connected": True
            },
            "components": {
                "producer_started": self.producer._is_started,
                "consumer_started": consumer_stats.get("is_started", False),
                "consumer_consuming": consumer_stats.get("is_consuming", False)
            }
        }

    def is_healthy(self) -> bool:
        """
        检查内存队列是否健康

        Returns:
            bool: 是否健康
        """
        return self._is_started

    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        获取性能指标

        Returns:
            Dict[str, Any]: 性能指标
        """
        consumer_stats = self.consumer.get_consumer_stats() if self.consumer else {}

        return {
            "message_throughput": {
                "produced_per_second": 0,  # 内存队列不统计实时吞吐量
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
                "start": datetime.now().isoformat(),
                "end": datetime.now().isoformat()
            },
            "queue_size": consumer_stats.get("queue_size", 0)
        }
