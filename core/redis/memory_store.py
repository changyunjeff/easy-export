from __future__ import annotations

import json
import time
import threading
from typing import Any, Optional, Union, List, Dict, Tuple
from collections import defaultdict, OrderedDict
from .base import BaseStore


class MemoryStore(BaseStore):
    """
    内存存储实现，提供与 Redis 兼容的接口
    用于在 Redis 不可用时的回退方案
    """
    
    def __init__(self):
        """初始化内存存储"""
        self._lock = threading.RLock()
        self._strings: Dict[str, Tuple[Any, Optional[float]]] = {}  # key -> (value, expire_time)
        self._hashes: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._lists: Dict[str, List[Any]] = defaultdict(list)
        self._sets: Dict[str, set] = defaultdict(set)
        self._zsets: Dict[str, Dict[Any, float]] = defaultdict(dict)  # key -> {member: score}
        self._expire_times: Dict[str, float] = {}  # key -> expire_time
    
    def _is_expired(self, key: str) -> bool:
        """检查键是否已过期"""
        if key in self._expire_times:
            if time.time() > self._expire_times[key]:
                return True
        return False
    
    def _cleanup_expired(self, key: str):
        """清理过期的键"""
        if self._is_expired(key):
            self._expire_times.pop(key, None)
            self._strings.pop(key, None)
            self._hashes.pop(key, None)
            self._lists.pop(key, None)
            self._sets.pop(key, None)
            self._zsets.pop(key, None)
    
    def _set_expire(self, key: str, ex: Optional[int] = None, px: Optional[int] = None):
        """设置过期时间"""
        if ex is not None:
            self._expire_times[key] = time.time() + ex
        elif px is not None:
            self._expire_times[key] = time.time() + (px / 1000.0)
        else:
            self._expire_times.pop(key, None)
    
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
        """设置键值对"""
        with self._lock:
            self._cleanup_expired(key)
            
            exists = key in self._strings or key in self._hashes or key in self._lists or key in self._sets or key in self._zsets
            
            if nx and exists:
                return False
            if xx and not exists:
                return False
            
            # 清理其他类型的数据
            self._hashes.pop(key, None)
            self._lists.pop(key, None)
            self._sets.pop(key, None)
            self._zsets.pop(key, None)
            
            self._strings[key] = (value, None)
            self._set_expire(key, ex, px)
            return True
    
    def get(self, key: str) -> Optional[Any]:
        """获取键值"""
        with self._lock:
            self._cleanup_expired(key)
            if key in self._strings:
                return self._strings[key][0]
            return None
    
    def incr(self, key: str, amount: int = 1) -> int:
        """增加键的值（原子操作）"""
        with self._lock:
            self._cleanup_expired(key)
            current = self._strings.get(key, (0, None))[0]
            try:
                new_value = int(current) + amount
            except (ValueError, TypeError):
                new_value = amount
            self._strings[key] = (new_value, None)
            return new_value
    
    def delete(self, *keys: str) -> int:
        """删除一个或多个键"""
        with self._lock:
            count = 0
            for key in keys:
                self._cleanup_expired(key)
                if key in self._strings or key in self._hashes or key in self._lists or key in self._sets or key in self._zsets:
                    self._strings.pop(key, None)
                    self._hashes.pop(key, None)
                    self._lists.pop(key, None)
                    self._sets.pop(key, None)
                    self._zsets.pop(key, None)
                    self._expire_times.pop(key, None)
                    count += 1
            return count
    
    def exists(self, *keys: str) -> int:
        """检查键是否存在"""
        with self._lock:
            count = 0
            for key in keys:
                self._cleanup_expired(key)
                if key in self._strings or key in self._hashes or key in self._lists or key in self._sets or key in self._zsets:
                    count += 1
            return count
    
    def expire(self, key: str, time: int) -> bool:
        """设置键的过期时间（秒）"""
        with self._lock:
            self._cleanup_expired(key)
            exists = key in self._strings or key in self._hashes or key in self._lists or key in self._sets or key in self._zsets
            if exists:
                self._set_expire(key, ex=time)
                return True
            return False
    
    def ttl(self, key: str) -> int:
        """获取键的剩余过期时间（秒）"""
        with self._lock:
            self._cleanup_expired(key)
            if key not in self._expire_times:
                exists = key in self._strings or key in self._hashes or key in self._lists or key in self._sets or key in self._zsets
                return -1 if exists else -2
            remaining = self._expire_times[key] - time.time()
            return int(remaining) if remaining > 0 else -2
    
    # ==================== 哈希操作 ====================
    
    def hset(self, name: str, key: Optional[str] = None, value: Any = None, mapping: Optional[Dict[str, Any]] = None) -> int:
        """设置哈希字段"""
        with self._lock:
            self._cleanup_expired(name)
            
            # 清理其他类型的数据
            self._strings.pop(name, None)
            self._lists.pop(name, None)
            self._sets.pop(name, None)
            self._zsets.pop(name, None)
            
            if mapping:
                count = 0
                for k, v in mapping.items():
                    if k not in self._hashes[name]:
                        count += 1
                    self._hashes[name][k] = v
                return count
            else:
                if key not in self._hashes[name]:
                    self._hashes[name][key] = value
                    return 1
                else:
                    self._hashes[name][key] = value
                    return 0
    
    def hget(self, name: str, key: str) -> Optional[Any]:
        """获取哈希字段值"""
        with self._lock:
            self._cleanup_expired(name)
            return self._hashes.get(name, {}).get(key)
    
    def hgetall(self, name: str) -> Dict[str, Any]:
        """获取哈希表所有字段和值"""
        with self._lock:
            self._cleanup_expired(name)
            return dict(self._hashes.get(name, {}))
    
    def hdel(self, name: str, *keys: str) -> int:
        """删除哈希字段"""
        with self._lock:
            self._cleanup_expired(name)
            count = 0
            for key in keys:
                if key in self._hashes.get(name, {}):
                    del self._hashes[name][key]
                    count += 1
            return count
    
    # ==================== 列表操作 ====================
    
    def lpush(self, name: str, *values: Any) -> int:
        """从列表左侧推入元素"""
        with self._lock:
            self._cleanup_expired(name)
            
            # 清理其他类型的数据
            self._strings.pop(name, None)
            self._hashes.pop(name, None)
            self._sets.pop(name, None)
            self._zsets.pop(name, None)
            
            # lpush 从左到右依次推入，最后推入的在最左边
            for value in values:
                self._lists[name].insert(0, value)
            return len(self._lists[name])
    
    def rpush(self, name: str, *values: Any) -> int:
        """从列表右侧推入元素"""
        with self._lock:
            self._cleanup_expired(name)
            
            # 清理其他类型的数据
            self._strings.pop(name, None)
            self._hashes.pop(name, None)
            self._sets.pop(name, None)
            self._zsets.pop(name, None)
            
            self._lists[name].extend(values)
            return len(self._lists[name])
    
    def lpop(self, name: str, count: int = 1) -> Union[Any, List[Any], None]:
        """从列表左侧弹出元素"""
        with self._lock:
            self._cleanup_expired(name)
            if name not in self._lists or not self._lists[name]:
                return None
            
            if count == 1:
                return self._lists[name].pop(0)
            else:
                result = []
                for _ in range(min(count, len(self._lists[name]))):
                    result.append(self._lists[name].pop(0))
                return result if result else None
    
    def rpop(self, name: str, count: int = 1) -> Union[Any, List[Any], None]:
        """从列表右侧弹出元素"""
        with self._lock:
            self._cleanup_expired(name)
            if name not in self._lists or not self._lists[name]:
                return None
            
            if count == 1:
                return self._lists[name].pop()
            else:
                result = []
                for _ in range(min(count, len(self._lists[name]))):
                    result.append(self._lists[name].pop())
                # rpop 返回的顺序是按弹出顺序，先弹出的在前
                return result if result else None
    
    def lrange(self, name: str, start: int = 0, end: int = -1) -> List[Any]:
        """获取列表指定范围的元素"""
        with self._lock:
            self._cleanup_expired(name)
            if name not in self._lists:
                return []
            
            lst = self._lists[name]
            if end == -1:
                end = len(lst)
            return lst[start:end+1]
    
    # ==================== 集合操作 ====================
    
    def sadd(self, name: str, *values: Any) -> int:
        """向集合添加元素"""
        with self._lock:
            self._cleanup_expired(name)
            
            # 清理其他类型的数据
            self._strings.pop(name, None)
            self._hashes.pop(name, None)
            self._lists.pop(name, None)
            self._zsets.pop(name, None)
            
            count = 0
            for value in values:
                # 集合需要可哈希的值
                try:
                    hash(value)
                    if value not in self._sets[name]:
                        self._sets[name].add(value)
                        count += 1
                except TypeError:
                    # 不可哈希的值，转换为字符串
                    value_str = str(value)
                    if value_str not in self._sets[name]:
                        self._sets[name].add(value_str)
                        count += 1
            return count
    
    def smembers(self, name: str) -> set:
        """获取集合所有成员"""
        with self._lock:
            self._cleanup_expired(name)
            return set(self._sets.get(name, set()))
    
    def srem(self, name: str, *values: Any) -> int:
        """从集合移除元素"""
        with self._lock:
            self._cleanup_expired(name)
            count = 0
            for value in values:
                try:
                    hash(value)
                    if value in self._sets.get(name, set()):
                        self._sets[name].discard(value)
                        count += 1
                except TypeError:
                    value_str = str(value)
                    if value_str in self._sets.get(name, set()):
                        self._sets[name].discard(value_str)
                        count += 1
            return count
    
    # ==================== 有序集合操作 ====================
    
    def zadd(self, name: str, mapping: Dict[Any, float]) -> int:
        """向有序集合添加成员"""
        with self._lock:
            self._cleanup_expired(name)
            
            # 清理其他类型的数据
            self._strings.pop(name, None)
            self._hashes.pop(name, None)
            self._lists.pop(name, None)
            self._sets.pop(name, None)
            
            count = 0
            for member, score in mapping.items():
                if member not in self._zsets[name]:
                    count += 1
                self._zsets[name][member] = score
            return count
    
    def zrange(self, name: str, start: int = 0, end: int = -1, withscores: bool = False) -> List[Any]:
        """获取有序集合指定范围的成员"""
        with self._lock:
            self._cleanup_expired(name)
            if name not in self._zsets:
                return []
            
            # 按分数排序
            sorted_items = sorted(self._zsets[name].items(), key=lambda x: x[1])
            
            if end == -1:
                end = len(sorted_items)
            
            items = sorted_items[start:end+1]
            
            if withscores:
                return [(member, score) for member, score in items]
            else:
                return [member for member, score in items]
    
    # ==================== 通用操作 ====================
    
    def keys(self, pattern: str = "*") -> List[str]:
        """获取匹配模式的所有键"""
        with self._lock:
            all_keys = set()
            all_keys.update(self._strings.keys())
            all_keys.update(self._hashes.keys())
            all_keys.update(self._lists.keys())
            all_keys.update(self._sets.keys())
            all_keys.update(self._zsets.keys())
            
            # 简单的通配符匹配
            if pattern == "*":
                return list(all_keys)
            
            # 支持简单的通配符
            import fnmatch
            return [key for key in all_keys if fnmatch.fnmatch(key, pattern)]
    
    def ping(self) -> bool:
        """测试连接（内存存储总是可用）"""
        return True
    
    def close(self) -> None:
        """关闭连接（内存存储无需关闭）"""
        pass

