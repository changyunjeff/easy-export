"""
RedisClient 白盒测试
测试高级客户端的所有功能，包括 JSON 序列化/反序列化
"""
from __future__ import annotations

import pytest
import json
import sys
import os
from unittest.mock import MagicMock

# Mock 依赖模块以避免导入问题
sys.modules['core.config'] = MagicMock()
sys.modules['pydantic_yaml'] = MagicMock()
sys.modules['redis'] = MagicMock()
sys.modules['redis.connection'] = MagicMock()



from core.redis.client import RedisClient
from core.redis.memory_store import MemoryStore


class TestRedisClient:
    """RedisClient 测试类"""
    
    @pytest.fixture
    def client(self):
        """创建 RedisClient 实例（使用 MemoryStore 作为底层存储）"""
        store = MemoryStore()
        return RedisClient(store)
    
    # ==================== 字符串操作测试 ====================
    
    def test_set_get_string(self, client):
        """测试字符串的 set 和 get"""
        assert client.set("key1", "value1") is True
        assert client.get("key1") == "value1"
    
    def test_set_get_json_serialization(self, client):
        """测试 JSON 序列化/反序列化"""
        # 字典
        data = {"name": "test", "age": 30, "active": True}
        assert client.set("key1", data) is True
        result = client.get("key1")
        assert result == data
        assert isinstance(result, dict)
        
        # 列表
        data = [1, 2, 3, "a", "b"]
        assert client.set("key2", data) is True
        result = client.get("key2")
        assert result == data
        
        # 嵌套结构
        data = {"users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}
        assert client.set("key3", data) is True
        result = client.get("key3")
        assert result == data
    
    def test_set_get_with_default(self, client):
        """测试 get 的 default 参数"""
        assert client.get("nonexistent") is None
        assert client.get("nonexistent", "default") == "default"
        assert client.get("nonexistent", {"key": "value"}) == {"key": "value"}
    
    def test_set_string_no_serialization(self, client):
        """测试字符串不进行序列化"""
        # 字符串应该直接存储，不进行 JSON 序列化
        value = "simple string"
        client.set("key1", value)
        result = client.get("key1")
        assert result == value
        assert isinstance(result, str)
    
    def test_set_get_with_expire(self, client):
        """测试带过期时间的 set 和 get"""
        import time
        data = {"key": "value"}
        assert client.set("key1", data, ex=1) is True
        assert client.get("key1") == data
        
        time.sleep(1.1)
        assert client.get("key1") is None
        assert client.get("key1", "default") == "default"
    
    def test_set_nx_xx(self, client):
        """测试 nx 和 xx 选项"""
        data = {"value": 1}
        assert client.set("key1", data, nx=True) is True
        assert client.set("key1", {"value": 2}, nx=True) is False
        assert client.get("key1") == {"value": 1}
        
        assert client.set("key2", data, xx=True) is False
        client.set("key2", data)
        assert client.set("key2", {"value": 2}, xx=True) is True
        assert client.get("key2") == {"value": 2}
    
    def test_delete(self, client):
        """测试 delete 操作"""
        client.set("key1", "value1")
        client.set("key2", "value2")
        
        assert client.delete("key1") == 1
        assert client.get("key1") is None
        
        assert client.delete("key2", "key3") == 1
    
    def test_exists(self, client):
        """测试 exists 操作"""
        assert client.exists("key1") == 0
        
        client.set("key1", "value1")
        assert client.exists("key1") == 1
        
        client.set("key2", "value2")
        assert client.exists("key1", "key2") == 2
    
    def test_expire_ttl(self, client):
        """测试 expire 和 ttl 操作"""
        client.set("key1", "value1")
        assert client.expire("key1", 10) is True
        ttl = client.ttl("key1")
        assert 0 < ttl <= 10
        
        assert client.ttl("nonexistent") == -2
    
    # ==================== 哈希操作测试 ====================
    
    def test_hset_hget_single(self, client):
        """测试单个字段的 hset 和 hget"""
        assert client.hset("hash1", "field1", "value1") == 1
        assert client.hget("hash1", "field1") == "value1"
        
        assert client.hset("hash1", "field1", "value2") == 0
        assert client.hget("hash1", "field1") == "value2"
    
    def test_hset_hget_json(self, client):
        """测试哈希字段的 JSON 序列化"""
        data = {"name": "test", "age": 30}
        assert client.hset("hash1", "field1", data) == 1
        
        result = client.hget("hash1", "field1")
        assert result == data
        assert isinstance(result, dict)
        
        # 列表
        data = [1, 2, 3]
        assert client.hset("hash1", "field2", data) == 1
        result = client.hget("hash1", "field2")
        assert result == data
    
    def test_hset_mapping(self, client):
        """测试使用 mapping 参数的 hset"""
        mapping = {
            "field1": "value1",
            "field2": {"nested": "data"},
            "field3": [1, 2, 3],
            "field4": 123
        }
        assert client.hset("hash1", mapping=mapping) == 4
        
        assert client.hget("hash1", "field1") == "value1"
        assert client.hget("hash1", "field2") == {"nested": "data"}
        assert client.hget("hash1", "field3") == [1, 2, 3]
        assert client.hget("hash1", "field4") == 123
    
    def test_hget_with_default(self, client):
        """测试 hget 的 default 参数"""
        assert client.hget("hash1", "field1") is None
        assert client.hget("hash1", "field1", "default") == "default"
        
        client.hset("hash1", "field1", "value1")
        assert client.hget("hash1", "field1", "default") == "value1"
    
    def test_hgetall(self, client):
        """测试 hgetall 操作"""
        mapping = {
            "field1": "value1",
            "field2": {"data": "test"},
            "field3": 123
        }
        client.hset("hash1", mapping=mapping)
        
        result = client.hgetall("hash1")
        assert result == mapping
        assert isinstance(result["field2"], dict)
    
    def test_hgetall_json_deserialization(self, client):
        """测试 hgetall 的 JSON 反序列化"""
        mapping = {
            "str_field": "string",
            "dict_field": {"key": "value"},
            "list_field": [1, 2, 3],
            "int_field": 42
        }
        client.hset("hash1", mapping=mapping)
        
        result = client.hgetall("hash1")
        assert result["str_field"] == "string"
        assert result["dict_field"] == {"key": "value"}
        assert result["list_field"] == [1, 2, 3]
        assert result["int_field"] == 42
    
    def test_hdel(self, client):
        """测试 hdel 操作"""
        mapping = {"field1": "value1", "field2": "value2", "field3": "value3"}
        client.hset("hash1", mapping=mapping)
        
        assert client.hdel("hash1", "field1") == 1
        assert client.hget("hash1", "field1") is None
        
        assert client.hdel("hash1", "field2", "field3") == 2
        assert client.hgetall("hash1") == {}
    
    # ==================== 列表操作测试 ====================
    
    def test_lpush_lpop(self, client):
        """测试 lpush 和 lpop"""
        data1 = {"value": 1}
        data2 = {"value": 2}
        data3 = {"value": 3}
        
        assert client.lpush("list1", data1, data2, data3) == 3
        
        result = client.lpop("list1")
        assert result == data3
        
        result = client.lpop("list1")
        assert result == data2
        
        result = client.lpop("list1")
        assert result == data1
    
    def test_rpush_rpop(self, client):
        """测试 rpush 和 rpop"""
        data1 = {"value": 1}
        data2 = {"value": 2}
        
        assert client.rpush("list1", data1, data2) == 2
        
        result = client.rpop("list1")
        assert result == data2
        
        result = client.rpop("list1")
        assert result == data1
    
    def test_lpop_count(self, client):
        """测试 lpop 的 count 参数"""
        data = [{"id": i} for i in range(5)]
        client.lpush("list1", *data)
        
        result = client.lpop("list1", count=2)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == {"id": 4}
        assert result[1] == {"id": 3}
    
    def test_rpop_count(self, client):
        """测试 rpop 的 count 参数"""
        data = [{"id": i} for i in range(5)]
        client.rpush("list1", *data)
        
        result = client.rpop("list1", count=2)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0] == {"id": 4}
        assert result[1] == {"id": 3}
    
    def test_lrange(self, client):
        """测试 lrange 操作"""
        data = [{"id": i} for i in range(5)]
        client.rpush("list1", *data)
        
        result = client.lrange("list1", 0, -1)
        assert len(result) == 5
        assert result[0] == {"id": 0}
        assert result[4] == {"id": 4}
        
        result = client.lrange("list1", 1, 3)
        assert len(result) == 3
        assert result[0] == {"id": 1}
    
    def test_list_json_serialization(self, client):
        """测试列表元素的 JSON 序列化"""
        data = [
            "string",
            123,
            {"dict": "value"},
            [1, 2, 3],
            True,
            None
        ]
        client.lpush("list1", *data)
        
        result = client.lrange("list1", 0, -1)
        # 注意：lpush 是逆序的
        assert result == list(reversed(data))
    
    # ==================== 集合操作测试 ====================
    
    def test_sadd_smembers(self, client):
        """测试 sadd 和 smembers"""
        data1 = {"id": 1}
        data2 = {"id": 2}
        data3 = {"id": 3}
        
        assert client.sadd("set1", data1, data2, data3) == 3
        
        members = client.smembers("set1")
        assert len(members) == 3
        # 注意：集合中的元素会被序列化，所以需要检查序列化后的值
        assert any(m == data1 for m in members)
        assert any(m == data2 for m in members)
        assert any(m == data3 for m in members)
    
    def test_srem(self, client):
        """测试 srem 操作"""
        data1 = {"id": 1}
        data2 = {"id": 2}
        data3 = {"id": 3}
        
        client.sadd("set1", data1, data2, data3)
        assert client.srem("set1", data1, data2) == 2
        
        members = client.smembers("set1")
        assert len(members) == 1
    
    def test_set_string_members(self, client):
        """测试集合中的字符串成员"""
        assert client.sadd("set1", "a", "b", "c") == 3
        members = client.smembers("set1")
        assert "a" in members
        assert "b" in members
        assert "c" in members
    
    # ==================== 有序集合操作测试 ====================
    
    def test_zadd_zrange(self, client):
        """测试 zadd 和 zrange"""
        mapping = {
            "member1": 1.0,
            "member2": 2.0,
            "member3": 3.0
        }
        assert client.zadd("zset1", mapping) == 3
        
        result = client.zrange("zset1", 0, -1)
        assert result == ["member1", "member2", "member3"]
        
        result = client.zrange("zset1", 0, -1, withscores=True)
        assert result == [("member1", 1.0), ("member2", 2.0), ("member3", 3.0)]
    
    def test_zadd_json_members(self, client):
        """测试有序集合中的 JSON 成员"""
        # 注意：字典不能作为字典的键，所以我们需要先序列化
        import json
        mapping = {
            json.dumps({"id": 1}, ensure_ascii=False): 1.0,
            json.dumps({"id": 2}, ensure_ascii=False): 2.0,
            json.dumps({"id": 3}, ensure_ascii=False): 3.0
        }
        assert client.zadd("zset1", mapping) == 3
        
        result = client.zrange("zset1", 0, -1)
        assert len(result) == 3
        # 验证成员被正确反序列化
        assert any(m == {"id": 1} for m in result)
    
    def test_zrange_with_range(self, client):
        """测试 zrange 的范围参数"""
        mapping = {f"member{i}": float(i) for i in range(5)}
        client.zadd("zset1", mapping)
        
        result = client.zrange("zset1", 0, 2)
        assert len(result) == 3
        
        result = client.zrange("zset1", 1, 3, withscores=True)
        assert len(result) == 3
        assert all(isinstance(item, tuple) and len(item) == 2 for item in result)
    
    # ==================== 通用操作测试 ====================
    
    def test_keys(self, client):
        """测试 keys 操作"""
        client.set("string1", "value1")
        client.hset("hash1", "field1", "value1")
        client.lpush("list1", "a")
        
        keys = client.keys()
        assert "string1" in keys
        assert "hash1" in keys
        assert "list1" in keys
    
    def test_keys_pattern(self, client):
        """测试 keys 的模式匹配"""
        client.set("user:1", "value1")
        client.set("user:2", "value2")
        client.set("post:1", "value3")
        
        user_keys = client.keys("user:*")
        assert len(user_keys) == 2
        assert "user:1" in user_keys
        assert "user:2" in user_keys
    
    def test_ping(self, client):
        """测试 ping 操作"""
        assert client.ping() is True
    
    # ==================== 错误处理测试 ====================
    
    def test_invalid_json_handling(self, client):
        """测试无效 JSON 的处理"""
        # 如果底层存储返回的不是有效 JSON，应该返回原始值
        store = client.client
        # 直接设置一个非 JSON 字符串
        store.set("key1", "not a json string")
        
        # get 应该返回原始字符串
        result = client.get("key1")
        assert result == "not a json string"
    
    def test_none_value_handling(self, client):
        """测试 None 值的处理"""
        client.set("key1", None)
        result = client.get("key1")
        # None 会被序列化为 "null"，然后反序列化为 None
        assert result is None or result == "null"
    
    # ==================== 边界情况测试 ====================
    
    def test_empty_values(self, client):
        """测试空值"""
        client.set("empty_str", "")
        assert client.get("empty_str") == ""
        
        client.set("empty_list", [])
        assert client.get("empty_list") == []
        
        client.set("empty_dict", {})
        assert client.get("empty_dict") == {}
    
    def test_unicode_values(self, client):
        """测试 Unicode 值"""
        data = {"name": "测试", "message": "こんにちは"}
        client.set("key1", data)
        result = client.get("key1")
        assert result == data
    
    def test_special_characters(self, client):
        """测试特殊字符"""
        data = {"key": "value\nwith\nnewlines", "tab": "value\twith\ttabs"}
        client.set("key1", data)
        result = client.get("key1")
        assert result == data
    
    def test_nested_structures(self, client):
        """测试嵌套结构"""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "value": "deep"
                    }
                }
            },
            "list": [
                {"item": 1},
                {"item": 2},
                {"item": 3}
            ]
        }
        client.set("key1", data)
        result = client.get("key1")
        assert result == data
        assert result["level1"]["level2"]["level3"]["value"] == "deep"
        assert len(result["list"]) == 3

