"""
RocketMQ消息生产者模块

负责向RocketMQ发送导出任务消息，支持同步和异步发送模式。
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, asdict

from .connection import RocketMQConnection
from .exceptions import RocketMQSendError, RocketMQConnectionError

logger = logging.getLogger(__name__)


@dataclass
class ExportTaskMessage:
    """导出任务消息结构"""
    task_id: str
    template_id: str
    data: Dict[str, Any]
    output_format: str
    template_version: Optional[str] = None
    priority: int = 0
    retry_count: int = 0
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExportTaskMessage':
        """从字典创建实例"""
        return cls(**data)


class RocketMQProducer:
    """RocketMQ消息生产者"""
    
    def __init__(self, connection: RocketMQConnection):
        """
        初始化消息生产者
        
        Args:
            connection: RocketMQ连接管理器
        """
        self.connection = connection
        self._producer = None
        self._is_started = False
        
    def start(self) -> None:
        """启动生产者"""
        try:
            if not self.connection.is_connected():
                raise RocketMQConnectionError("RocketMQ connection is not established")
                
            logger.info("Starting RocketMQ producer")
            
            # 这里应该实现实际的生产者启动逻辑
            # 根据具体的RocketMQ Python客户端库来实现
            # 例如：
            # from rocketmq.client import Producer
            # producer_config = self.connection.get_producer_config()
            # self._producer = Producer(producer_config)
            # self._producer.start()
            
            self._is_started = True
            logger.info("RocketMQ producer started successfully")
            
        except Exception as e:
            error_msg = f"Failed to start RocketMQ producer: {str(e)}"
            logger.error(error_msg)
            raise RocketMQSendError(error_msg)
            
    def stop(self) -> None:
        """停止生产者"""
        try:
            if self._is_started and self._producer:
                logger.info("Stopping RocketMQ producer")
                
                # 这里应该实现实际的生产者停止逻辑
                # self._producer.shutdown()
                
                self._is_started = False
                logger.info("RocketMQ producer stopped successfully")
                
        except Exception as e:
            logger.error(f"Error stopping RocketMQ producer: {str(e)}")
            
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
            output_format: 输出格式 (docx/pdf/html)
            template_version: 模板版本
            priority: 优先级 (0-9, 数字越大优先级越高)
            task_id: 任务ID，如果不提供则自动生成
            
        Returns:
            str: 任务ID
            
        Raises:
            RocketMQSendError: 发送失败时抛出
        """
        if not self._is_started:
            raise RocketMQSendError("Producer is not started")
            
        if task_id is None:
            task_id = str(uuid.uuid4())
            
        # 创建任务消息
        task_message = ExportTaskMessage(
            task_id=task_id,
            template_id=template_id,
            template_version=template_version,
            data=data,
            output_format=output_format,
            priority=priority
        )
        
        try:
            # 序列化消息
            message_body = json.dumps(asdict(task_message), ensure_ascii=False)
            
            # 发送消息
            self._send_message(
                topic=self.connection.get_connection_info().topic,
                tag="EXPORT_TASK",
                body=message_body,
                keys=task_id,
                properties={
                    "TASK_ID": task_id,
                    "TEMPLATE_ID": template_id,
                    "OUTPUT_FORMAT": output_format,
                    "PRIORITY": str(priority)
                }
            )
            
            logger.info(f"Export task message sent successfully: {task_id}")
            return task_id
            
        except Exception as e:
            error_msg = f"Failed to send export task message: {str(e)}"
            logger.error(error_msg)
            raise RocketMQSendError(error_msg, task_id=task_id)
            
    def send_batch_export_task(
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
            
        logger.info(f"Batch export tasks sent: {len(task_ids)} tasks")
        return task_ids
        
    def _send_message(
        self,
        topic: str,
        tag: str,
        body: str,
        keys: Optional[str] = None,
        properties: Optional[Dict[str, str]] = None
    ) -> None:
        """
        发送消息到RocketMQ
        
        Args:
            topic: 主题
            tag: 标签
            body: 消息体
            keys: 消息键
            properties: 消息属性
        """
        try:
            # 这里应该实现实际的消息发送逻辑
            # 根据具体的RocketMQ Python客户端库来实现
            # 例如：
            # from rocketmq.client import Message
            # message = Message(topic)
            # message.set_tags(tag)
            # message.set_keys(keys)
            # message.set_body(body)
            # if properties:
            #     for key, value in properties.items():
            #         message.put_property(key, value)
            # 
            # send_result = self._producer.send_sync(message)
            # logger.debug(f"Message sent: {send_result}")
            
            # 模拟发送成功
            logger.debug(f"Message sent to topic: {topic}, tag: {tag}, keys: {keys}")
            
        except Exception as e:
            raise RocketMQSendError(f"Failed to send message: {str(e)}", topic=topic)
            
    def send_async(
        self,
        template_id: str,
        data: Dict[str, Any],
        output_format: str,
        callback: Optional[Callable[[str, bool, Optional[str]], None]] = None,
        template_version: Optional[str] = None,
        priority: int = 0,
        task_id: Optional[str] = None
    ) -> str:
        """
        异步发送导出任务消息
        
        Args:
            template_id: 模板ID
            data: 导出数据
            output_format: 输出格式
            callback: 回调函数 (task_id, success, error_message)
            template_version: 模板版本
            priority: 优先级
            task_id: 任务ID
            
        Returns:
            str: 任务ID
        """
        if task_id is None:
            task_id = str(uuid.uuid4())
            
        try:
            # 这里应该实现异步发送逻辑
            # 可以使用线程池或异步库来实现
            
            # 模拟异步发送
            result_task_id = self.send_export_task(
                template_id=template_id,
                data=data,
                output_format=output_format,
                template_version=template_version,
                priority=priority,
                task_id=task_id
            )
            
            if callback:
                callback(result_task_id, True, None)
                
            return result_task_id
            
        except Exception as e:
            if callback:
                callback(task_id, False, str(e))
            raise
            
    def __enter__(self):
        """上下文管理器入口"""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.stop()
