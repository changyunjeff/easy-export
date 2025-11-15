"""
数据脱敏模块
提供敏感数据脱敏功能，用于日志记录和数据展示
"""

import re
import logging
from typing import Any, Dict, List, Set, Union

logger = logging.getLogger(__name__)


class DataMasker:
    """
    数据脱敏器
    
    功能:
    1. 识别敏感字段（密码、Token、密钥等）
    2. 对敏感数据进行脱敏处理
    3. 支持自定义敏感字段
    4. 支持多种脱敏策略
    """
    
    # 敏感字段关键词（小写）
    SENSITIVE_KEYWORDS = {
        'password', 'passwd', 'pwd',
        'token', 'access_token', 'refresh_token', 'id_token',
        'secret', 'api_secret', 'client_secret',
        'key', 'api_key', 'private_key', 'public_key', 'secret_key',
        'credential', 'credentials',
        'auth', 'authorization',
        'session', 'session_id',
        'cookie',
        'apikey', 'accesskey', 'secretkey',
    }
    
    # 敏感值模式（正则表达式）
    SENSITIVE_PATTERNS = [
        # JWT Token
        (re.compile(r'eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}'), 'JWT Token'),
        # API Key (sk_live_xxx, pk_test_xxx, etc.)
        (re.compile(r'[sp]k_(live|test)_[A-Za-z0-9]{20,}'), 'API Key'),
        # Bearer Token
        (re.compile(r'Bearer\s+[A-Za-z0-9_-]{20,}'), 'Bearer Token'),
        # 基础认证
        (re.compile(r'Basic\s+[A-Za-z0-9+/=]{20,}'), 'Basic Auth'),
    ]
    
    def __init__(self, custom_keywords: Set[str] = None):
        """
        初始化数据脱敏器
        
        Args:
            custom_keywords: 自定义敏感字段关键词
        """
        self.sensitive_keywords = self.SENSITIVE_KEYWORDS.copy()
        if custom_keywords:
            self.sensitive_keywords.update(k.lower() for k in custom_keywords)
        logger.info(f"DataMasker initialized with {len(self.sensitive_keywords)} sensitive keywords")
    
    def is_sensitive_key(self, key: str) -> bool:
        """
        判断键名是否为敏感字段
        
        Args:
            key: 字段名
            
        Returns:
            是否为敏感字段
        """
        key_lower = key.lower()
        return any(keyword in key_lower for keyword in self.sensitive_keywords)
    
    def is_sensitive_value(self, value: str) -> bool:
        """
        判断值是否为敏感数据（通过模式匹配）
        
        Args:
            value: 字段值
            
        Returns:
            是否为敏感数据
        """
        if not isinstance(value, str):
            return False
        
        for pattern, _ in self.SENSITIVE_PATTERNS:
            if pattern.search(value):
                return True
        
        return False
    
    def mask_string(self, value: str, mask_char: str = '*', keep_length: int = 2) -> str:
        """
        脱敏字符串
        
        Args:
            value: 原始值
            mask_char: 脱敏字符
            keep_length: 保留前后字符数量
            
        Returns:
            脱敏后的字符串
        """
        if not isinstance(value, str):
            return value
        
        value_len = len(value)
        
        # 如果字符串太短，完全脱敏
        if value_len <= keep_length * 2:
            return mask_char * 3
        
        # 保留前后部分，中间脱敏
        masked_length = value_len - keep_length * 2
        return value[:keep_length] + mask_char * masked_length + value[-keep_length:]
    
    def mask_email(self, email: str) -> str:
        """
        脱敏邮箱地址
        
        Args:
            email: 邮箱地址
            
        Returns:
            脱敏后的邮箱
        """
        if '@' not in email:
            return self.mask_string(email)
        
        username, domain = email.rsplit('@', 1)
        
        if len(username) <= 2:
            masked_username = '*' * len(username)
        else:
            masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
        
        return f"{masked_username}@{domain}"
    
    def mask_phone(self, phone: str) -> str:
        """
        脱敏手机号
        
        Args:
            phone: 手机号
            
        Returns:
            脱敏后的手机号
        """
        # 移除非数字字符
        digits = ''.join(c for c in phone if c.isdigit())
        
        if len(digits) < 7:
            return '*' * len(digits)
        
        # 保留前3位和后4位
        return digits[:3] + '*' * (len(digits) - 7) + digits[-4:]
    
    def mask_id_card(self, id_card: str) -> str:
        """
        脱敏身份证号
        
        Args:
            id_card: 身份证号
            
        Returns:
            脱敏后的身份证号
        """
        if len(id_card) < 8:
            return '*' * len(id_card)
        
        # 保留前4位和后4位
        return id_card[:4] + '*' * (len(id_card) - 8) + id_card[-4:]
    
    def mask_value(self, value: Any, field_name: str = "") -> Any:
        """
        脱敏单个值
        
        Args:
            value: 原始值
            field_name: 字段名（用于判断脱敏策略）
            
        Returns:
            脱敏后的值
        """
        if not isinstance(value, str):
            return value
        
        field_lower = field_name.lower()
        
        # 邮箱
        if 'email' in field_lower or 'mail' in field_lower:
            return self.mask_email(value)
        
        # 手机号
        if 'phone' in field_lower or 'mobile' in field_lower or 'tel' in field_lower:
            return self.mask_phone(value)
        
        # 身份证
        if 'id_card' in field_lower or 'idcard' in field_lower:
            return self.mask_id_card(value)
        
        # 默认脱敏策略
        return self.mask_string(value)
    
    def mask_dict(self, data: Dict[str, Any], recursive: bool = True) -> Dict[str, Any]:
        """
        脱敏字典数据
        
        Args:
            data: 原始数据字典
            recursive: 是否递归处理嵌套字典
            
        Returns:
            脱敏后的数据字典
        """
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        
        for key, value in data.items():
            # 检查键名是否为敏感字段
            if self.is_sensitive_key(key):
                masked_data[key] = self.mask_value(value, key)
            # 检查值是否为敏感数据
            elif isinstance(value, str) and self.is_sensitive_value(value):
                masked_data[key] = self.mask_string(value)
            # 递归处理嵌套字典
            elif recursive and isinstance(value, dict):
                masked_data[key] = self.mask_dict(value, recursive=True)
            # 递归处理列表
            elif recursive and isinstance(value, list):
                masked_data[key] = self.mask_list(value, recursive=True)
            else:
                masked_data[key] = value
        
        return masked_data
    
    def mask_list(self, data: List[Any], recursive: bool = True) -> List[Any]:
        """
        脱敏列表数据
        
        Args:
            data: 原始数据列表
            recursive: 是否递归处理嵌套结构
            
        Returns:
            脱敏后的数据列表
        """
        if not isinstance(data, list):
            return data
        
        masked_list = []
        
        for item in data:
            if recursive and isinstance(item, dict):
                masked_list.append(self.mask_dict(item, recursive=True))
            elif recursive and isinstance(item, list):
                masked_list.append(self.mask_list(item, recursive=True))
            elif isinstance(item, str) and self.is_sensitive_value(item):
                masked_list.append(self.mask_string(item))
            else:
                masked_list.append(item)
        
        return masked_list
    
    def mask_data(self, data: Union[Dict, List, str, Any]) -> Any:
        """
        脱敏任意类型数据（统一入口）
        
        Args:
            data: 原始数据
            
        Returns:
            脱敏后的数据
        """
        if isinstance(data, dict):
            return self.mask_dict(data)
        elif isinstance(data, list):
            return self.mask_list(data)
        elif isinstance(data, str) and self.is_sensitive_value(data):
            return self.mask_string(data)
        else:
            return data
    
    def mask_log_message(self, message: str) -> str:
        """
        脱敏日志消息
        
        Args:
            message: 原始日志消息
            
        Returns:
            脱敏后的日志消息
        """
        masked_message = message
        
        # 使用模式匹配脱敏
        for pattern, label in self.SENSITIVE_PATTERNS:
            def replacer(match):
                value = match.group(0)
                return self.mask_string(value, keep_length=3)
            
            masked_message = pattern.sub(replacer, masked_message)
        
        return masked_message


# 全局实例
_data_masker: DataMasker = None


def get_data_masker() -> DataMasker:
    """获取数据脱敏器全局实例"""
    global _data_masker
    if _data_masker is None:
        _data_masker = DataMasker()
    return _data_masker


def mask_sensitive_data(data: Any) -> Any:
    """
    脱敏敏感数据（便捷函数）
    
    Args:
        data: 原始数据
        
    Returns:
        脱敏后的数据
    """
    masker = get_data_masker()
    return masker.mask_data(data)

