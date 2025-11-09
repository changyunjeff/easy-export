# Redis 客户端接口

本模块提供了 Redis 客户端的封装接口，支持连接池管理、自动 JSON 序列化/反序列化等功能。

## 特性

1. **自动 JSON 序列化/反序列化**：存储和读取时自动处理 JSON 数据
2. **连接池管理**：自动管理连接池，提高性能
3. **异常处理**：所有操作都包含异常处理和日志记录
4. **类型提示**：完整的类型提示支持
5. **自动回退到内存存储**：当 Redis 不可用时，自动使用内存存储（非持久化）
6. **接口一致性**：无论使用 Redis 还是内存存储，接口完全一致

## 快速开始

### 1. 启动 Redis 服务

#### 方式一：使用 Docker Compose（推荐）

在 `core/redis/` 目录下提供了 `docker-compose.yml` 文件，可以直接启动 Redis 服务：

```bash
cd core/redis
docker-compose up -d
```

这将启动一个 Redis 容器，端口映射到 `localhost:6379`，数据持久化到 Docker volume。

停止服务：
```bash
docker-compose down
```

#### 方式二：本地安装 Redis

如果你已经安装了 Redis，确保 Redis 服务正在运行：

```bash
# Linux/Mac
redis-server

# Windows
# 使用 WSL 或 Docker
```

### 2. 配置 Redis

在配置文件中添加 Redis 配置（如 `config.dev.yaml`）：

```yaml
redis:
  enabled: true
  host: localhost
  port: 6379
  db: 0
  password: null  # 可选，如果有密码则填写
  decode_responses: true
  max_connections: 50
  socket_connect_timeout: 5
  socket_timeout: 5
```

### 2. 使用封装类（推荐）

```python
from core.redis import RedisClient

# 获取 Redis 客户端实例（应用启动后自动初始化）
redis = RedisClient()

# 字符串操作
redis.set("user:1", {"name": "Alice", "age": 30}, ex=3600)  # 自动序列化为 JSON
user = redis.get("user:1")  # 自动反序列化
# 输出: {'name': 'Alice', 'age': 30}

# 哈希操作
redis.hset("user:1:profile", mapping={
    "email": "alice@example.com",
    "city": "Beijing"
})
profile = redis.hgetall("user:1:profile")

# 列表操作
redis.lpush("tasks", {"id": 1, "name": "Task 1"})
task = redis.lpop("tasks")

# 集合操作
redis.sadd("tags", "python", "redis", "fastapi")
tags = redis.smembers("tags")

# 有序集合操作
redis.zadd("leaderboard", {"user:1": 100.0, "user:2": 200.0})
top_users = redis.zrange("leaderboard", 0, 9, withscores=True)
```

### 3. 使用底层客户端

如果需要直接使用 Redis 原生方法：

```python
from core.redis import get_redis_client

client = get_redis_client()
client.set("key", "value")
value = client.get("key")
```

## API 文档

### RedisClient 类

#### 字符串操作

- `set(key, value, ex=None, px=None, nx=False, xx=False)` - 设置键值对
- `get(key, default=None)` - 获取键值
- `delete(*keys)` - 删除键
- `exists(*keys)` - 检查键是否存在
- `expire(key, time)` - 设置过期时间（秒）
- `ttl(key)` - 获取剩余过期时间（秒）

#### 哈希操作

- `hset(name, key=None, value=None, mapping=None)` - 设置哈希字段
- `hget(name, key, default=None)` - 获取哈希字段值
- `hgetall(name)` - 获取所有字段和值
- `hdel(name, *keys)` - 删除哈希字段

#### 列表操作

- `lpush(name, *values)` - 从左侧推入元素
- `rpush(name, *values)` - 从右侧推入元素
- `lpop(name, count=1)` - 从左侧弹出元素
- `rpop(name, count=1)` - 从右侧弹出元素
- `lrange(name, start=0, end=-1)` - 获取指定范围的元素

#### 集合操作

- `sadd(name, *values)` - 添加元素
- `smembers(name)` - 获取所有成员
- `srem(name, *values)` - 移除元素

#### 有序集合操作

- `zadd(name, mapping)` - 添加成员（mapping 为 {member: score} 字典）
- `zrange(name, start=0, end=-1, withscores=False)` - 获取指定范围的成员

#### 通用操作

- `keys(pattern="*")` - 获取匹配模式的所有键
- `ping()` - 测试连接

## 内存存储回退

当以下情况发生时，系统会自动回退到内存存储（非持久化）：

1. **配置中未启用 Redis**：如果 `redis.enabled` 为 `false` 或未配置
2. **Redis 连接失败**：如果无法连接到 Redis 服务器

内存存储提供与 Redis 完全相同的接口，但有以下限制：

- **非持久化**：应用重启后数据会丢失
- **单进程**：多进程/多实例之间数据不共享
- **内存限制**：受限于应用进程的内存

### 检查当前使用的存储类型

```python
from core.redis import is_using_memory_store

if is_using_memory_store():
    print("当前使用内存存储（非持久化）")
else:
    print("当前使用 Redis 存储（持久化）")
```

### 手动初始化内存存储

如果需要强制使用内存存储：

```python
from core.redis import init_memory_store

# 直接初始化内存存储（不尝试连接 Redis）
init_memory_store()
```

## 测试

```bash
# 运行所有 Redis 测试
pytest tests/test_redis_*.py -v
# 在Windows CMD中使用
pytest tests/ -k "test_redis"

# 运行特定测试文件
pytest tests/test_redis_memory_store.py -v
pytest tests/test_redis_client.py -v
pytest tests/test_redis_connection.py -v

# 运行特定测试
pytest tests/test_redis_memory_store.py::TestMemoryStore::test_set_get -v
```

## 注意事项

1. 应用启动时会根据配置自动初始化 Redis 连接
2. 如果 Redis 未启用或连接失败，**会自动回退到内存存储**，应用不会因此启动失败
3. 所有非字符串值会自动序列化为 JSON 字符串存储
4. 读取时会尝试自动反序列化 JSON，失败则返回原始字符串
5. 内存存储适合开发和测试环境，生产环境建议使用 Redis

