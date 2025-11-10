from __future__ import annotations

import json
import logging
from typing import Any, Optional, Union, List, Dict
from datetime import timedelta
from redis import Redis
from .connection import get_redis_client
from .memory_store import MemoryStore
from .base import BaseClient

logger = logging.getLogger(__name__)


class RedisClient(BaseClient):
    """
    Redis 客户端封装类，提供便捷的操作接口
    支持真实的 Redis 连接和内存存储回退
    """
    
    def __init__(self, client: Optional[Union[Redis, MemoryStore]] = None):
        """
        初始化 Redis 客户端
        
        Args:
            client: Redis 客户端实例或内存存储实例，如果为 None 则使用全局客户端
        """
        self._client = client or get_redis_client()
    
    @property
    def client(self) -> Union[Redis, MemoryStore]:
        """获取底层 Redis 客户端或内存存储实例"""
        return self._client
    
    # ==================== 字符串操作 ====================
    
    def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """
        设置键值对
        
        Args:
            key: 键名
            value: 值（会自动序列化为 JSON 字符串）
            ex: 过期时间（秒）
            px: 过期时间（毫秒）
            nx: 仅在键不存在时设置
            xx: 仅在键存在时设置
        
        Returns:
            是否设置成功
        """
        try:
            if not isinstance(value, str):
                value = json.dumps(value, ensure_ascii=False)
            return self._client.set(key, value, ex=ex, px=px, nx=nx, xx=xx)
        except Exception as e:
            logger.error(f"Redis set error: {key} - {e}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取键值
        
        Args:
            key: 键名
            default: 默认值（如果键不存在）
        
        Returns:
            值（会自动反序列化 JSON 字符串）
        """
        try:
            value = self._client.get(key)
            if value is None:
                return default
            
            # 尝试解析 JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Redis get error: {key} - {e}")
            return default
    
    def delete(self, *keys: str) -> int:
        """
        删除一个或多个键
        
        Args:
            *keys: 键名列表
        
        Returns:
            删除的键数量
        """
        try:
            return self._client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis delete error: {keys} - {e}")
            raise
    
    def exists(self, *keys: str) -> int:
        """
        检查键是否存在
        
        Args:
            *keys: 键名列表
        
        Returns:
            存在的键数量
        """
        try:
            return self._client.exists(*keys)
        except Exception as e:
            logger.error(f"Redis exists error: {keys} - {e}")
            raise
    
    def expire(self, key: str, time: int) -> bool:
        """
        设置键的过期时间（秒）
        
        Args:
            key: 键名
            time: 过期时间（秒）
        
        Returns:
            是否设置成功
        """
        try:
            return self._client.expire(key, time)
        except Exception as e:
            logger.error(f"Redis expire error: {key} - {e}")
            raise
    
    def ttl(self, key: str) -> int:
        """
        获取键的剩余过期时间（秒）
        
        Args:
            key: 键名
        
        Returns:
            剩余过期时间（秒），-1 表示永不过期，-2 表示键不存在
        """
        try:
            return self._client.ttl(key)
        except Exception as e:
            logger.error(f"Redis ttl error: {key} - {e}")
            raise
    
    def incr(self, key: str, amount: int = 1) -> int:
        """
        增加键的值（原子操作）
        
        Args:
            key: 键名
            amount: 增加的数量，默认为1
        
        Returns:
            增加后的值
        """
        try:
            # 如果底层支持incr方法（Redis或MemoryStore）
            if hasattr(self._client, 'incr'):
                if amount == 1:
                    # Redis的incr方法只接受key参数
                    if hasattr(self._client, 'incrby'):
                        # 真实Redis
                        return self._client.incr(key)
                    else:
                        # MemoryStore
                        return self._client.incr(key, amount)
                else:
                    # 需要增加指定数量
                    if hasattr(self._client, 'incrby'):
                        # 真实Redis
                        return self._client.incrby(key, amount)
                    else:
                        # MemoryStore
                        return self._client.incr(key, amount)
            else:
                # 回退方案：使用get/set（非原子操作，但可用）
                current = self.get(key, 0)
                if not isinstance(current, int):
                    try:
                        current = int(current)
                    except (ValueError, TypeError):
                        current = 0
                new_value = current + amount
                self.set(key, new_value)
                return new_value
        except Exception as e:
            logger.error(f"Redis incr error: {key} - {e}")
            raise
    
    # ==================== 哈希操作 ====================
    
    def hset(self, name: str, key: Optional[str] = None, value: Any = None, mapping: Optional[Dict[str, Any]] = None) -> int:
        """
        设置哈希字段
        
        Args:
            name: 哈希表名
            key: 字段名（如果提供 mapping 则忽略）
            value: 字段值（如果提供 mapping 则忽略）
            mapping: 字段字典
        
        Returns:
            设置的字段数量
        """
        try:
            if mapping:
                # 序列化字典中的值
                serialized_mapping = {
                    k: json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                    for k, v in mapping.items()
                }
                return self._client.hset(name, mapping=serialized_mapping)
            else:
                if not isinstance(value, str):
                    value = json.dumps(value, ensure_ascii=False)
                return self._client.hset(name, key, value)
        except Exception as e:
            logger.error(f"Redis hset error: {name} - {e}")
            raise
    
    def hget(self, name: str, key: str, default: Any = None) -> Any:
        """
        获取哈希字段值
        
        Args:
            name: 哈希表名
            key: 字段名
            default: 默认值
        
        Returns:
            字段值（会自动反序列化 JSON 字符串）
        """
        try:
            value = self._client.hget(name, key)
            if value is None:
                return default
            
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        except Exception as e:
            logger.error(f"Redis hget error: {name}.{key} - {e}")
            return default
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """
        获取哈希表所有字段和值
        
        Args:
            name: 哈希表名
        
        Returns:
            字段字典（值会自动反序列化 JSON 字符串）
        """
        try:
            data = self._client.hgetall(name)
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except (json.JSONDecodeError, TypeError):
                    result[k] = v
            return result
        except Exception as e:
            logger.error(f"Redis hgetall error: {name} - {e}")
            raise
    
    def hdel(self, name: str, *keys: str) -> int:
        """
        删除哈希字段
        
        Args:
            name: 哈希表名
            *keys: 字段名列表
        
        Returns:
            删除的字段数量
        """
        try:
            return self._client.hdel(name, *keys)
        except Exception as e:
            logger.error(f"Redis hdel error: {name} - {e}")
            raise
    
    # ==================== 列表操作 ====================
    
    def lpush(self, name: str, *values: Any) -> int:
        """
        从列表左侧推入元素
        
        Args:
            name: 列表名
            *values: 值列表
        
        Returns:
            列表长度
        """
        try:
            serialized_values = [
                json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                for v in values
            ]
            return self._client.lpush(name, *serialized_values)
        except Exception as e:
            logger.error(f"Redis lpush error: {name} - {e}")
            raise
    
    def rpush(self, name: str, *values: Any) -> int:
        """
        从列表右侧推入元素
        
        Args:
            name: 列表名
            *values: 值列表
        
        Returns:
            列表长度
        """
        try:
            serialized_values = [
                json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                for v in values
            ]
            return self._client.rpush(name, *serialized_values)
        except Exception as e:
            logger.error(f"Redis rpush error: {name} - {e}")
            raise
    
    def lpop(self, name: str, count: int = 1) -> Union[Any, List[Any], None]:
        """
        从列表左侧弹出元素
        
        Args:
            name: 列表名
            count: 弹出元素数量
        
        Returns:
            弹出的元素（会自动反序列化 JSON 字符串）
        """
        try:
            values = self._client.lpop(name, count)
            if values is None:
                return None
            
            if isinstance(values, list):
                result = []
                for v in values:
                    try:
                        result.append(json.loads(v))
                    except (json.JSONDecodeError, TypeError):
                        result.append(v)
                return result
            else:
                try:
                    return json.loads(values)
                except (json.JSONDecodeError, TypeError):
                    return values
        except Exception as e:
            logger.error(f"Redis lpop error: {name} - {e}")
            raise
    
    def rpop(self, name: str, count: int = 1) -> Union[Any, List[Any], None]:
        """
        从列表右侧弹出元素
        
        Args:
            name: 列表名
            count: 弹出元素数量
        
        Returns:
            弹出的元素（会自动反序列化 JSON 字符串）
        """
        try:
            values = self._client.rpop(name, count)
            if values is None:
                return None
            
            if isinstance(values, list):
                result = []
                for v in values:
                    try:
                        result.append(json.loads(v))
                    except (json.JSONDecodeError, TypeError):
                        result.append(v)
                return result
            else:
                try:
                    return json.loads(values)
                except (json.JSONDecodeError, TypeError):
                    return values
        except Exception as e:
            logger.error(f"Redis rpop error: {name} - {e}")
            raise
    
    def lrange(self, name: str, start: int = 0, end: int = -1) -> List[Any]:
        """
        获取列表指定范围的元素
        
        Args:
            name: 列表名
            start: 起始索引
            end: 结束索引
        
        Returns:
            元素列表（会自动反序列化 JSON 字符串）
        """
        try:
            values = self._client.lrange(name, start, end)
            result = []
            for v in values:
                try:
                    result.append(json.loads(v))
                except (json.JSONDecodeError, TypeError):
                    result.append(v)
            return result
        except Exception as e:
            logger.error(f"Redis lrange error: {name} - {e}")
            raise
    
    # ==================== 集合操作 ====================
    
    def sadd(self, name: str, *values: Any) -> int:
        """
        向集合添加元素
        
        Args:
            name: 集合名
            *values: 值列表
        
        Returns:
            添加的元素数量
        """
        try:
            serialized_values = [
                json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                for v in values
            ]
            return self._client.sadd(name, *serialized_values)
        except Exception as e:
            logger.error(f"Redis sadd error: {name} - {e}")
            raise
    
    def smembers(self, name: str) -> set:
        """
        获取集合所有成员
        
        Args:
            name: 集合名
        
        Returns:
            成员集合（会自动反序列化 JSON 字符串）
            注意：如果反序列化后的值不可哈希（如字典），则返回列表
        """
        try:
            values = self._client.smembers(name)
            result = set()
            unhashable_items = []
            for v in values:
                try:
                    deserialized = json.loads(v)
                    # 尝试添加到集合中
                    try:
                        result.add(deserialized)
                    except TypeError:
                        # 不可哈希的值（如字典），收集到列表中
                        unhashable_items.append(deserialized)
                except (json.JSONDecodeError, TypeError):
                    result.add(v)
            
            # 如果有不可哈希的值，返回列表（包含集合和列表中的所有元素）
            if unhashable_items:
                return list(result) + unhashable_items
            return result
        except Exception as e:
            logger.error(f"Redis smembers error: {name} - {e}")
            raise
    
    def srem(self, name: str, *values: Any) -> int:
        """
        从集合移除元素
        
        Args:
            name: 集合名
            *values: 值列表
        
        Returns:
            移除的元素数量
        """
        try:
            serialized_values = [
                json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
                for v in values
            ]
            return self._client.srem(name, *serialized_values)
        except Exception as e:
            logger.error(f"Redis srem error: {name} - {e}")
            raise
    
    # ==================== 有序集合操作 ====================
    
    def zadd(self, name: str, mapping: Dict[Any, float]) -> int:
        """
        向有序集合添加成员
        
        Args:
            name: 有序集合名
            mapping: 成员和分数的字典
        
        Returns:
            添加的成员数量
        """
        try:
            serialized_mapping = {
                json.dumps(k, ensure_ascii=False) if not isinstance(k, str) else k: v
                for k, v in mapping.items()
            }
            return self._client.zadd(name, serialized_mapping)
        except Exception as e:
            logger.error(f"Redis zadd error: {name} - {e}")
            raise
    
    def zrange(self, name: str, start: int = 0, end: int = -1, withscores: bool = False) -> List[Any]:
        """
        获取有序集合指定范围的成员
        
        Args:
            name: 有序集合名
            start: 起始索引
            end: 结束索引
            withscores: 是否包含分数
        
        Returns:
            成员列表（会自动反序列化 JSON 字符串）
        """
        try:
            values = self._client.zrange(name, start, end, withscores=withscores)
            if withscores:
                # 检查返回格式：MemoryStore 返回 [(member, score), ...]，真实 Redis 返回 [member1, score1, member2, score2, ...]
                if values and isinstance(values[0], tuple):
                    # 已经是元组列表格式，直接处理
                    result = []
                    for member, score in values:
                        try:
                            member = json.loads(member)
                        except (json.JSONDecodeError, TypeError):
                            pass
                        result.append((member, score))
                    return result
                else:
                    # 扁平列表格式 [member1, score1, member2, score2, ...]
                    result = []
                    for i in range(0, len(values), 2):
                        try:
                            member = json.loads(values[i])
                        except (json.JSONDecodeError, TypeError):
                            member = values[i]
                        result.append((member, values[i + 1]))
                    return result
            else:
                result = []
                for v in values:
                    try:
                        result.append(json.loads(v))
                    except (json.JSONDecodeError, TypeError):
                        result.append(v)
                return result
        except Exception as e:
            logger.error(f"Redis zrange error: {name} - {e}")
            raise
    
    # ==================== 通用操作 ====================
    
    def keys(self, pattern: str = "*") -> List[str]:
        """
        获取匹配模式的所有键
        
        Args:
            pattern: 匹配模式（支持通配符）
        
        Returns:
            键列表
        """
        try:
            return list(self._client.keys(pattern))
        except Exception as e:
            logger.error(f"Redis keys error: {pattern} - {e}")
            raise
    
    def ping(self) -> bool:
        """
        测试 Redis 连接
        
        Returns:
            连接是否正常
        """
        try:
            return self._client.ping()
        except Exception as e:
            logger.error(f"Redis ping error: {e}")
            return False

