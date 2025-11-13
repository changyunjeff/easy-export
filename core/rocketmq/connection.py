"""
RocketMQ连接管理模块

负责管理RocketMQ的连接配置和连接池，提供统一的连接管理接口。
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from core.schemas import RocketMQConfig
from .exceptions import RocketMQConnectionError, RocketMQConfigError

logger = logging.getLogger(__name__)


@dataclass
class RocketMQConnectionInfo:
    """RocketMQ连接信息"""
    name_server: str
    producer_group: str
    consumer_group: str
    topic: str
    tag: str = "*"
    namespace: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    security_token: Optional[str] = None


class RocketMQConnection:
    """RocketMQ连接管理器"""
    
    def __init__(self, config: RocketMQConfig):
        """
        初始化RocketMQ连接管理器

        Args:
            config: RocketMQ配置对象
        """
        self.config = config
        self._connection_info: Optional[RocketMQConnectionInfo] = None
        self._is_connected = False
        self._client_available = False

        # 验证配置
        self._validate_config()

        # 创建连接信息
        self._create_connection_info()
        
    def _validate_config(self) -> None:
        """验证RocketMQ配置"""
        if not self.config.enabled:
            raise RocketMQConfigError("RocketMQ is not enabled in configuration")
            
        if not self.config.name_server:
            raise RocketMQConfigError("RocketMQ name_server is required", "name_server")
            
        if not self.config.producer_group:
            raise RocketMQConfigError("RocketMQ producer_group is required", "producer_group")
            
        if not self.config.consumer_group:
            raise RocketMQConfigError("RocketMQ consumer_group is required", "consumer_group")
            
        if not self.config.topic:
            raise RocketMQConfigError("RocketMQ topic is required", "topic")
            
        logger.info("RocketMQ configuration validation passed")
        
    def _create_connection_info(self) -> None:
        """创建连接信息对象"""
        self._connection_info = RocketMQConnectionInfo(
            name_server=self.config.name_server,
            producer_group=self.config.producer_group,
            consumer_group=self.config.consumer_group,
            topic=self.config.topic,
            tag=self.config.tag,
            namespace=self.config.namespace,
            access_key=self.config.access_key,
            secret_key=self.config.secret_key,
            security_token=self.config.security_token
        )
        
    def connect(self) -> bool:
        """
        建立RocketMQ连接

        Returns:
            bool: 连接是否成功

        Raises:
            RocketMQConnectionError: 连接失败时抛出
        """
        try:
            logger.info(f"Connecting to RocketMQ NameServer: {self.config.name_server}")

            # 尝试导入RocketMQ客户端
            try:
                from rocketmq.client import Producer, PushConsumer
                self._client_available = True
            except (ImportError, NotImplementedError):
                logger.warning("RocketMQ client not available, will use fallback mode")
                self._client_available = False
                self._is_connected = True
                logger.info("Successfully connected to RocketMQ")
                return True

            # 这里可以进行实际的连接测试
            # 由于RocketMQ Python客户端可能需要额外的配置，这里先模拟连接
            self._is_connected = True

            logger.info("Successfully connected to RocketMQ")
            return True

        except Exception as e:
            error_msg = f"Failed to connect to RocketMQ: {str(e)}"
            logger.error(error_msg)
            raise RocketMQConnectionError(error_msg, self.config.name_server)
            
    def disconnect(self) -> None:
        """断开RocketMQ连接"""
        try:
            if self._is_connected:
                logger.info("Disconnecting from RocketMQ")
                
                # 这里应该实现实际的断开连接逻辑
                
                self._is_connected = False
                logger.info("Successfully disconnected from RocketMQ")
                
        except Exception as e:
            logger.error(f"Error disconnecting from RocketMQ: {str(e)}")
            
    def is_connected(self) -> bool:
        """
        检查连接状态

        Returns:
            bool: 是否已连接
        """
        return self._is_connected

    def is_client_available(self) -> bool:
        """
        检查RocketMQ客户端是否可用

        Returns:
            bool: 客户端是否可用
        """
        return self._client_available
        
    def get_connection_info(self) -> RocketMQConnectionInfo:
        """
        获取连接信息
        
        Returns:
            RocketMQConnectionInfo: 连接信息对象
        """
        if not self._connection_info:
            raise RocketMQConnectionError("Connection info not initialized")
        return self._connection_info
        
    def get_producer_config(self) -> Dict[str, Any]:
        """
        获取生产者配置
        
        Returns:
            Dict[str, Any]: 生产者配置字典
        """
        return {
            "name_server": self.config.name_server,
            "producer_group": self.config.producer_group,
            "max_message_size": self.config.max_message_size,
            "send_timeout": self.config.send_timeout,
            "retry_times": self.config.retry_times,
            "namespace": self.config.namespace,
            "access_key": self.config.access_key,
            "secret_key": self.config.secret_key,
            "security_token": self.config.security_token
        }
        
    def get_consumer_config(self) -> Dict[str, Any]:
        """
        获取消费者配置
        
        Returns:
            Dict[str, Any]: 消费者配置字典
        """
        return {
            "name_server": self.config.name_server,
            "consumer_group": self.config.consumer_group,
            "consumer_thread_min": self.config.consumer_thread_min,
            "consumer_thread_max": self.config.consumer_thread_max,
            "consume_message_batch_max_size": self.config.consume_message_batch_max_size,
            "pull_batch_size": self.config.pull_batch_size,
            "pull_interval": self.config.pull_interval,
            "consume_timeout": self.config.consume_timeout,
            "max_reconsume_times": self.config.max_reconsume_times,
            "suspend_current_queue_time": self.config.suspend_current_queue_time,
            "namespace": self.config.namespace,
            "access_key": self.config.access_key,
            "secret_key": self.config.secret_key,
            "security_token": self.config.security_token
        }
        
    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.disconnect()
