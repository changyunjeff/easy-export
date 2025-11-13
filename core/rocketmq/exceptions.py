"""
RocketMQ异常定义模块

定义RocketMQ相关的异常类，用于错误处理和异常传播。
"""

from typing import Optional


class RocketMQException(Exception):
    """RocketMQ基础异常类"""
    
    def __init__(self, message: str, error_code: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        
    def __str__(self):
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message


class RocketMQConnectionError(RocketMQException):
    """RocketMQ连接异常"""
    
    def __init__(self, message: str, name_server: Optional[str] = None):
        super().__init__(message, "CONNECTION_ERROR")
        self.name_server = name_server


class RocketMQSendError(RocketMQException):
    """RocketMQ消息发送异常"""
    
    def __init__(self, message: str, topic: Optional[str] = None, message_id: Optional[str] = None):
        super().__init__(message, "SEND_ERROR")
        self.topic = topic
        self.message_id = message_id


class RocketMQConsumeError(RocketMQException):
    """RocketMQ消息消费异常"""
    
    def __init__(self, message: str, topic: Optional[str] = None, message_id: Optional[str] = None):
        super().__init__(message, "CONSUME_ERROR")
        self.topic = topic
        self.message_id = message_id


class RocketMQConfigError(RocketMQException):
    """RocketMQ配置异常"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, "CONFIG_ERROR")
        self.config_key = config_key


class RocketMQTimeoutError(RocketMQException):
    """RocketMQ超时异常"""
    
    def __init__(self, message: str, timeout: Optional[int] = None):
        super().__init__(message, "TIMEOUT_ERROR")
        self.timeout = timeout
