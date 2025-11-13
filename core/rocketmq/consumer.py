"""
RocketMQ消息消费者模块

负责从RocketMQ消费导出任务消息，并调用导出服务处理任务。
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from dataclasses import dataclass, asdict

from .connection import RocketMQConnection
from .producer import ExportTaskMessage
from .exceptions import RocketMQConsumeError, RocketMQConnectionError

logger = logging.getLogger(__name__)


@dataclass
class ConsumeResult:
    """消费结果"""
    success: bool
    task_id: str
    error_message: Optional[str] = None
    processing_time: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConsumeResult':
        """从字典创建实例"""
        return cls(**data)


class RocketMQConsumer:
    """RocketMQ消息消费者"""
    
    def __init__(
        self, 
        connection: RocketMQConnection,
        message_handler: Optional[Callable[[ExportTaskMessage], ConsumeResult]] = None
    ):
        """
        初始化消息消费者
        
        Args:
            connection: RocketMQ连接管理器
            message_handler: 消息处理函数
        """
        self.connection = connection
        self.message_handler = message_handler
        self._consumer = None
        self._is_started = False
        self._is_consuming = False
        
    def set_message_handler(self, handler: Callable[[ExportTaskMessage], ConsumeResult]) -> None:
        """
        设置消息处理函数
        
        Args:
            handler: 消息处理函数，接收ExportTaskMessage，返回ConsumeResult
        """
        self.message_handler = handler
        
    def start(self) -> None:
        """启动消费者"""
        try:
            if not self.connection.is_connected():
                raise RocketMQConnectionError("RocketMQ connection is not established")
                
            if not self.message_handler:
                raise RocketMQConsumeError("Message handler is not set")
                
            logger.info("Starting RocketMQ consumer")
            
            # 这里应该实现实际的消费者启动逻辑
            # 根据具体的RocketMQ Python客户端库来实现
            # 例如：
            # from rocketmq.client import PushConsumer
            # consumer_config = self.connection.get_consumer_config()
            # self._consumer = PushConsumer(consumer_config)
            # self._consumer.subscribe(
            #     self.connection.get_connection_info().topic,
            #     self._message_listener
            # )
            # self._consumer.start()
            
            self._is_started = True
            logger.info("RocketMQ consumer started successfully")
            
        except Exception as e:
            error_msg = f"Failed to start RocketMQ consumer: {str(e)}"
            logger.error(error_msg)
            raise RocketMQConsumeError(error_msg)
            
    def stop(self) -> None:
        """停止消费者"""
        try:
            if self._is_started and self._consumer:
                logger.info("Stopping RocketMQ consumer")
                
                self._is_consuming = False
                
                # 这里应该实现实际的消费者停止逻辑
                # self._consumer.shutdown()
                
                self._is_started = False
                logger.info("RocketMQ consumer stopped successfully")
                
        except Exception as e:
            logger.error(f"Error stopping RocketMQ consumer: {str(e)}")
            
    def start_consuming(self) -> None:
        """开始消费消息"""
        if not self._is_started:
            raise RocketMQConsumeError("Consumer is not started")
            
        self._is_consuming = True
        logger.info("Started consuming messages")
        
        # 在实际实现中，这里会由RocketMQ客户端库自动调用消息监听器
        # 这里提供一个模拟的消费循环作为示例
        
    def stop_consuming(self) -> None:
        """停止消费消息"""
        self._is_consuming = False
        logger.info("Stopped consuming messages")
        
    def _message_listener(self, message_list: List[Any]) -> str:
        """
        消息监听器（由RocketMQ客户端库调用）
        
        Args:
            message_list: 消息列表
            
        Returns:
            str: 消费状态 ("SUCCESS" 或 "RECONSUME_LATER")
        """
        try:
            for message in message_list:
                result = self._process_message(message)
                if not result.success:
                    logger.error(f"Failed to process message: {result.error_message}")
                    return "RECONSUME_LATER"
                    
            return "SUCCESS"
            
        except Exception as e:
            logger.error(f"Error in message listener: {str(e)}")
            return "RECONSUME_LATER"
            
    def _process_message(self, message: Any) -> ConsumeResult:
        """
        处理单个消息
        
        Args:
            message: RocketMQ消息对象
            
        Returns:
            ConsumeResult: 处理结果
        """
        start_time = datetime.now()
        task_id = "unknown"
        
        try:
            # 解析消息
            # 在实际实现中，这里需要根据具体的RocketMQ客户端库来获取消息内容
            # message_body = message.body
            # message_id = message.msg_id
            # properties = message.properties
            
            # 模拟消息解析
            message_body = "{}"  # 实际应该从message对象获取
            
            # 解析任务消息
            task_data = json.loads(message_body)
            task_message = ExportTaskMessage(**task_data)
            task_id = task_message.task_id
            
            logger.info(f"Processing export task: {task_id}")
            
            # 调用消息处理函数
            if self.message_handler:
                result = self.message_handler(task_message)
            else:
                result = ConsumeResult(
                    success=False,
                    task_id=task_id,
                    error_message="No message handler configured"
                )
                
            # 计算处理时间
            processing_time = (datetime.now() - start_time).total_seconds()
            result.processing_time = processing_time
            
            if result.success:
                logger.info(f"Successfully processed task {task_id} in {processing_time:.2f}s")
            else:
                logger.error(f"Failed to process task {task_id}: {result.error_message}")
                
            return result
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse message JSON: {str(e)}"
            logger.error(error_msg)
            return ConsumeResult(
                success=False,
                task_id=task_id,
                error_message=error_msg
            )
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg)
            return ConsumeResult(
                success=False,
                task_id=task_id,
                error_message=error_msg
            )
            
    async def consume_message_async(self, message: Any) -> ConsumeResult:
        """
        异步处理消息
        
        Args:
            message: RocketMQ消息对象
            
        Returns:
            ConsumeResult: 处理结果
        """
        # 在异步环境中处理消息
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._process_message, message)
        
    def get_consumer_stats(self) -> Dict[str, Any]:
        """
        获取消费者统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "is_started": self._is_started,
            "is_consuming": self._is_consuming,
            "consumer_group": self.connection.get_connection_info().consumer_group,
            "topic": self.connection.get_connection_info().topic,
            "tag": self.connection.get_connection_info().tag
        }
        
    def subscribe_additional_topic(self, topic: str, tag: str = "*") -> None:
        """
        订阅额外的主题
        
        Args:
            topic: 主题名称
            tag: 标签过滤器
        """
        try:
            if not self._is_started:
                raise RocketMQConsumeError("Consumer is not started")
                
            # 这里应该实现订阅额外主题的逻辑
            # self._consumer.subscribe(topic, self._message_listener)
            
            logger.info(f"Subscribed to additional topic: {topic} with tag: {tag}")
            
        except Exception as e:
            error_msg = f"Failed to subscribe to topic {topic}: {str(e)}"
            logger.error(error_msg)
            raise RocketMQConsumeError(error_msg)
            
    def unsubscribe_topic(self, topic: str) -> None:
        """
        取消订阅主题
        
        Args:
            topic: 主题名称
        """
        try:
            if not self._is_started:
                raise RocketMQConsumeError("Consumer is not started")
                
            # 这里应该实现取消订阅的逻辑
            # self._consumer.unsubscribe(topic)
            
            logger.info(f"Unsubscribed from topic: {topic}")
            
        except Exception as e:
            error_msg = f"Failed to unsubscribe from topic {topic}: {str(e)}"
            logger.error(error_msg)
            raise RocketMQConsumeError(error_msg)
            
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()
