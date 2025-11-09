from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional, Union, List, Dict


class BaseStore(ABC):
    """
    底层存储抽象基类
    定义底层存储（Redis 或 MemoryStore）的公共接口
    """
    
    # ==================== 字符串操作 ====================
    
    @abstractmethod
    def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """设置键值对"""
        pass
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取键值"""
        pass
    
    @abstractmethod
    def delete(self, *keys: str) -> int:
        """删除一个或多个键"""
        pass
    
    @abstractmethod
    def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    def expire(self, key: str, time: int) -> bool:
        """设置键的过期时间（秒）"""
        pass
    
    @abstractmethod
    def ttl(self, key: str) -> int:
        """获取键的剩余过期时间（秒）"""
        pass
    
    # ==================== 哈希操作 ====================
    
    @abstractmethod
    def hset(
        self,
        name: str,
        key: Optional[str] = None,
        value: Any = None,
        mapping: Optional[Dict[str, Any]] = None,
    ) -> int:
        """设置哈希字段"""
        pass
    
    @abstractmethod
    def hget(self, name: str, key: str) -> Optional[Any]:
        """获取哈希字段值"""
        pass
    
    @abstractmethod
    def hgetall(self, name: str) -> Dict[str, Any]:
        """获取哈希表所有字段和值"""
        pass
    
    @abstractmethod
    def hdel(self, name: str, *keys: str) -> int:
        """删除哈希字段"""
        pass
    
    # ==================== 列表操作 ====================
    
    @abstractmethod
    def lpush(self, name: str, *values: Any) -> int:
        """从列表左侧推入元素"""
        pass
    
    @abstractmethod
    def rpush(self, name: str, *values: Any) -> int:
        """从列表右侧推入元素"""
        pass
    
    @abstractmethod
    def lpop(self, name: str, count: int = 1) -> Union[Any, List[Any], None]:
        """从列表左侧弹出元素"""
        pass
    
    @abstractmethod
    def rpop(self, name: str, count: int = 1) -> Union[Any, List[Any], None]:
        """从列表右侧弹出元素"""
        pass
    
    @abstractmethod
    def lrange(self, name: str, start: int = 0, end: int = -1) -> List[Any]:
        """获取列表指定范围的元素"""
        pass
    
    # ==================== 集合操作 ====================
    
    @abstractmethod
    def sadd(self, name: str, *values: Any) -> int:
        """向集合添加元素"""
        pass
    
    @abstractmethod
    def smembers(self, name: str) -> set:
        """获取集合所有成员"""
        pass
    
    @abstractmethod
    def srem(self, name: str, *values: Any) -> int:
        """从集合移除元素"""
        pass
    
    # ==================== 有序集合操作 ====================
    
    @abstractmethod
    def zadd(self, name: str, mapping: Dict[Any, float]) -> int:
        """向有序集合添加成员"""
        pass
    
    @abstractmethod
    def zrange(
        self,
        name: str,
        start: int = 0,
        end: int = -1,
        withscores: bool = False,
    ) -> List[Any]:
        """获取有序集合指定范围的成员"""
        pass
    
    # ==================== 通用操作 ====================
    
    @abstractmethod
    def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配模式的所有键"""
        pass
    
    @abstractmethod
    def ping(self) -> bool:
        """测试连接"""
        pass
    
    @abstractmethod
    def close(self) -> None:
        """关闭连接"""
        pass


class BaseClient(ABC):
    """
    高级客户端抽象基类
    定义高级客户端（带 JSON 序列化）的公共接口
    """
    
    # ==================== 字符串操作 ====================
    
    @abstractmethod
    def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """设置键值对（自动序列化为 JSON）"""
        pass
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """获取键值（自动反序列化 JSON）"""
        pass
    
    @abstractmethod
    def delete(self, *keys: str) -> int:
        """删除一个或多个键"""
        pass
    
    @abstractmethod
    def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        pass
    
    @abstractmethod
    def expire(self, key: str, time: int) -> bool:
        """设置键的过期时间（秒）"""
        pass
    
    @abstractmethod
    def ttl(self, key: str) -> int:
        """获取键的剩余过期时间（秒）"""
        pass
    
    # ==================== 哈希操作 ====================
    
    @abstractmethod
    def hset(
        self,
        name: str,
        key: Optional[str] = None,
        value: Any = None,
        mapping: Optional[Dict[str, Any]] = None,
    ) -> int:
        """设置哈希字段（自动序列化为 JSON）"""
        pass
    
    @abstractmethod
    def hget(self, name: str, key: str, default: Any = None) -> Any:
        """获取哈希字段值（自动反序列化 JSON）"""
        pass
    
    @abstractmethod
    def hgetall(self, name: str) -> Dict[str, Any]:
        """获取哈希表所有字段和值（自动反序列化 JSON）"""
        pass
    
    @abstractmethod
    def hdel(self, name: str, *keys: str) -> int:
        """删除哈希字段"""
        pass
    
    # ==================== 列表操作 ====================
    
    @abstractmethod
    def lpush(self, name: str, *values: Any) -> int:
        """从列表左侧推入元素（自动序列化为 JSON）"""
        pass
    
    @abstractmethod
    def rpush(self, name: str, *values: Any) -> int:
        """从列表右侧推入元素（自动序列化为 JSON）"""
        pass
    
    @abstractmethod
    def lpop(self, name: str, count: int = 1) -> Union[Any, List[Any], None]:
        """从列表左侧弹出元素（自动反序列化 JSON）"""
        pass
    
    @abstractmethod
    def rpop(self, name: str, count: int = 1) -> Union[Any, List[Any], None]:
        """从列表右侧弹出元素（自动反序列化 JSON）"""
        pass
    
    @abstractmethod
    def lrange(self, name: str, start: int = 0, end: int = -1) -> List[Any]:
        """获取列表指定范围的元素（自动反序列化 JSON）"""
        pass
    
    # ==================== 集合操作 ====================
    
    @abstractmethod
    def sadd(self, name: str, *values: Any) -> int:
        """向集合添加元素（自动序列化为 JSON）"""
        pass
    
    @abstractmethod
    def smembers(self, name: str) -> set:
        """获取集合所有成员（自动反序列化 JSON）"""
        pass
    
    @abstractmethod
    def srem(self, name: str, *values: Any) -> int:
        """从集合移除元素（自动序列化为 JSON）"""
        pass
    
    # ==================== 有序集合操作 ====================
    
    @abstractmethod
    def zadd(self, name: str, mapping: Dict[Any, float]) -> int:
        """向有序集合添加成员（自动序列化为 JSON）"""
        pass
    
    @abstractmethod
    def zrange(
        self,
        name: str,
        start: int = 0,
        end: int = -1,
        withscores: bool = False,
    ) -> List[Any]:
        """获取有序集合指定范围的成员（自动反序列化 JSON）"""
        pass
    
    # ==================== 通用操作 ====================
    
    @abstractmethod
    def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配模式的所有键"""
        pass
    
    @abstractmethod
    def ping(self) -> bool:
        """测试连接"""
        pass

