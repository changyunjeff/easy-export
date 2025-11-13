# RocketMQ接口实现说明

## 1. 概述

### 1.1 背景
为了解决服务器承载不了批量转换请求的问题，项目集成了RocketMQ消息队列中间件。通过消息队列实现导出任务的异步处理，确保服务器能够逐个处理转换请求，避免系统过载。

### 1.2 核心功能
- **异步任务处理**：将导出请求发送到消息队列，异步处理
- **负载均衡**：通过队列机制实现任务的均匀分发
- **故障恢复**：支持消息重试和失败处理
- **实时监控**：提供队列状态和性能指标的实时监控
- **可扩展性**：支持多消费者实例，便于水平扩展

### 1.3 技术架构
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   客户端    │───▶│  FastAPI    │───▶│  RocketMQ   │
│   请求      │    │   应用      │    │   生产者    │
└─────────────┘    └─────────────┘    └─────────────┘
                                             │
                                             ▼
                   ┌─────────────┐    ┌─────────────┐
                   │  导出服务   │◀───│  RocketMQ   │
                   │   处理      │    │   消费者    │
                   └─────────────┘    └─────────────┘
```

---

## 2. 模块结构

### 2.1 目录结构
```
core/rocketmq/
├── __init__.py          # 模块入口
├── connection.py        # 连接管理
├── producer.py          # 消息生产者
├── consumer.py          # 消息消费者
├── monitor.py           # 队列监控
├── manager.py           # 统一管理器
└── exceptions.py        # 异常定义
```

### 2.2 核心组件

#### 2.2.1 RocketMQConnection (连接管理)
- **功能**：管理RocketMQ的连接配置和连接状态
- **主要方法**：
  - `connect()`: 建立连接
  - `disconnect()`: 断开连接
  - `is_connected()`: 检查连接状态
  - `get_connection_info()`: 获取连接信息

#### 2.2.2 RocketMQProducer (消息生产者)
- **功能**：发送导出任务消息到队列
- **主要方法**：
  - `send_export_task()`: 发送单个导出任务
  - `send_batch_export_tasks()`: 发送批量导出任务
  - `send_async()`: 异步发送消息

#### 2.2.3 RocketMQConsumer (消息消费者)
- **功能**：从队列消费导出任务并处理
- **主要方法**：
  - `set_message_handler()`: 设置消息处理器
  - `start_consuming()`: 开始消费消息
  - `stop_consuming()`: 停止消费消息

#### 2.2.4 RocketMQMonitor (队列监控)
- **功能**：提供队列状态和性能指标监控
- **主要方法**：
  - `get_queue_status()`: 获取队列状态
  - `get_consumer_lag()`: 获取消费者延迟
  - `get_health_status()`: 获取健康状态

#### 2.2.5 RocketMQManager (统一管理器)
- **功能**：统一管理所有RocketMQ组件
- **主要方法**：
  - `start()`: 启动所有组件
  - `stop()`: 停止所有组件
  - `send_export_task()`: 发送导出任务
  - `get_queue_status()`: 获取队列状态

---

## 3. 配置说明

### 3.1 配置文件 (config.dev.yaml)
```yaml
rocketmq:
  enabled: true                              # 启用RocketMQ
  name_server: "localhost:9876"              # NameServer地址
  producer_group: "export_producer_group"    # 生产者组名
  consumer_group: "export_consumer_group"    # 消费者组名
  topic: "export_tasks"                      # 主题名称
  tag: "*"                                   # 消息标签过滤器
  max_message_size: 4194304                  # 最大消息大小(4MB)
  send_timeout: 3000                         # 发送超时时间(毫秒)
  retry_times: 3                             # 发送失败重试次数
  consumer_thread_min: 1                     # 最小消费者线程数
  consumer_thread_max: 5                     # 最大消费者线程数
  consume_message_batch_max_size: 1          # 批量消费最大消息数
  pull_batch_size: 32                        # 拉取批次大小
  pull_interval: 0                           # 拉取间隔(毫秒)
  consume_timeout: 15                        # 消费超时时间(分钟)
  max_reconsume_times: 16                    # 最大重新消费次数
  suspend_current_queue_time: 1000           # 暂停当前队列时间(毫秒)
  access_key: null                           # 访问密钥(可选)
  secret_key: null                           # 秘密密钥(可选)
  security_token: null                       # 安全令牌(可选)
  namespace: null                            # 命名空间(可选)
```

### 3.2 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| enabled | bool | false | 是否启用RocketMQ |
| name_server | str | localhost:9876 | NameServer地址 |
| producer_group | str | export_producer_group | 生产者组名 |
| consumer_group | str | export_consumer_group | 消费者组名 |
| topic | str | export_tasks | 主题名称 |
| send_timeout | int | 3000 | 发送超时时间(毫秒) |
| retry_times | int | 3 | 发送失败重试次数 |
| consumer_thread_max | int | 5 | 最大消费者线程数 |

---

## 4. API接口

### 4.1 队列监控接口

#### 4.1.1 获取队列状态
```http
GET /api/v1/queue/status
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "topic": "export_tasks",
    "consumer_group": "export_consumer_group",
    "health": {
      "healthy": true,
      "connection_status": true,
      "total_lag": 0
    },
    "metrics": {
      "total_messages": 0,
      "active_queues": 4,
      "consumer_lag": {
        "0": 0,
        "1": 0,
        "2": 0,
        "3": 0
      },
      "total_lag": 0
    },
    "connection": {
      "name_server": "localhost:9876",
      "connected": true
    },
    "components": {
      "producer_started": true,
      "consumer_started": true,
      "consumer_consuming": true
    }
  },
  "message": "获取队列状态成功"
}
```

#### 4.1.2 队列健康检查
```http
GET /api/v1/queue/health
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "healthy": true,
    "details": {
      "healthy": true,
      "connection_status": true,
      "total_lag": 0,
      "topic": "export_tasks",
      "consumer_group": "export_consumer_group",
      "last_check": "2024-12-19T14:30:00.000Z"
    }
  },
  "message": "健康检查完成"
}
```

#### 4.1.3 获取性能指标
```http
GET /api/v1/queue/metrics
```

**响应示例**：
```json
{
  "success": true,
  "data": {
    "message_throughput": {
      "produced_per_second": 0,
      "consumed_per_second": 0
    },
    "latency": {
      "average_ms": 0,
      "p95_ms": 0,
      "p99_ms": 0
    },
    "error_rate": {
      "send_error_rate": 0.0,
      "consume_error_rate": 0.0
    },
    "time_range": {
      "start": "2024-12-19T14:25:00.000Z",
      "end": "2024-12-19T14:30:00.000Z"
    }
  },
  "message": "获取性能指标成功"
}
```

#### 4.1.4 获取消费者延迟
```http
GET /api/v1/queue/consumer/lag
```

#### 4.1.5 重启消费者
```http
POST /api/v1/queue/consumer/restart
```

#### 4.1.6 重启生产者
```http
POST /api/v1/queue/producer/restart
```

### 4.2 导出任务接口集成

在现有的导出接口中集成RocketMQ，示例：

```python
from core.rocketmq import get_rocketmq_manager

@router.post("/export")
async def export_document(request: ExportRequest):
    """导出文档（异步处理）"""
    try:
        # 获取RocketMQ管理器
        mq_manager = get_rocketmq_manager()
        
        # 发送任务到队列
        task_id = mq_manager.send_export_task(
            template_id=request.template_id,
            data=request.data,
            output_format=request.output_format,
            priority=request.priority or 0
        )
        
        return success_response(
            data={"task_id": task_id},
            message="导出任务已提交到队列"
        )
        
    except Exception as e:
        return error_response(
            message=f"提交导出任务失败: {str(e)}"
        )
```

---

## 5. 使用示例

### 5.1 初始化RocketMQ
```python
from core.rocketmq import get_rocketmq_manager, initialize_rocketmq

# 初始化RocketMQ管理器
initialize_rocketmq()

# 获取管理器实例
manager = get_rocketmq_manager()

# 启动所有组件
manager.start()
```

### 5.2 发送导出任务
```python
# 发送单个导出任务
task_id = manager.send_export_task(
    template_id="template_001",
    data={"title": "测试报告", "content": "这是测试内容"},
    output_format="docx",
    priority=1
)

# 发送批量导出任务
task_ids = manager.send_batch_export_tasks(
    template_id="template_001",
    data_list=[
        {"title": "报告1", "content": "内容1"},
        {"title": "报告2", "content": "内容2"}
    ],
    output_format="pdf"
)
```

### 5.3 设置消息处理器
```python
from core.rocketmq import ConsumeResult

def handle_export_task(task_message):
    """处理导出任务消息"""
    try:
        # 调用导出服务处理任务
        result = export_service.process_task(
            template_id=task_message.template_id,
            data=task_message.data,
            output_format=task_message.output_format
        )
        
        return ConsumeResult(
            success=True,
            task_id=task_message.task_id
        )
        
    except Exception as e:
        return ConsumeResult(
            success=False,
            task_id=task_message.task_id,
            error_message=str(e)
        )

# 设置消息处理器
manager.set_message_handler(handle_export_task)
```

### 5.4 监控队列状态
```python
# 获取队列状态
status = manager.get_queue_status()
print(f"队列健康状态: {status['health']['healthy']}")
print(f"总延迟消息数: {status['metrics']['total_lag']}")

# 检查健康状态
is_healthy = manager.is_healthy()
print(f"RocketMQ是否健康: {is_healthy}")

# 获取性能指标
metrics = manager.get_performance_metrics()
print(f"消息吞吐量: {metrics['message_throughput']}")
```

---

## 6. 部署说明

### 6.1 RocketMQ服务器部署

#### 6.1.1 Docker部署（推荐）
```bash
# 启动NameServer
docker run -d \
  --name rocketmq-nameserver \
  -p 9876:9876 \
  apache/rocketmq:4.9.4 \
  sh mqnamesrv

# 启动Broker
docker run -d \
  --name rocketmq-broker \
  --link rocketmq-nameserver:namesrv \
  -p 10909:10909 \
  -p 10911:10911 \
  -e "NAMESRV_ADDR=namesrv:9876" \
  apache/rocketmq:4.9.4 \
  sh mqbroker -c /home/rocketmq/rocketmq-4.9.4/conf/broker.conf
```

#### 6.1.2 Docker Compose部署
```yaml
version: '3.8'
services:
  rocketmq-nameserver:
    image: apache/rocketmq:4.9.4
    container_name: rocketmq-nameserver
    ports:
      - "9876:9876"
    command: sh mqnamesrv
    
  rocketmq-broker:
    image: apache/rocketmq:4.9.4
    container_name: rocketmq-broker
    ports:
      - "10909:10909"
      - "10911:10911"
    depends_on:
      - rocketmq-nameserver
    environment:
      - NAMESRV_ADDR=rocketmq-nameserver:9876
    command: sh mqbroker -c /home/rocketmq/rocketmq-4.9.4/conf/broker.conf
```

### 6.2 Python依赖安装
```bash
# 安装RocketMQ Python客户端
pip install rocketmq-client-python

# 或者使用其他RocketMQ Python客户端
pip install rocketmq
```

### 6.3 应用配置
1. 更新配置文件中的RocketMQ连接信息
2. 确保RocketMQ服务器可访问
3. 启动应用时会自动初始化RocketMQ组件

---

## 7. 监控和运维

### 7.1 监控指标
- **连接状态**：RocketMQ连接是否正常
- **队列深度**：待处理消息数量
- **消费延迟**：消费者处理延迟
- **吞吐量**：消息生产和消费速率
- **错误率**：发送和消费失败率

### 7.2 告警规则
- 队列深度超过1000条消息
- 消费延迟超过5分钟
- 连接断开超过30秒
- 错误率超过5%

### 7.3 故障处理
1. **连接失败**：检查RocketMQ服务器状态和网络连接
2. **消费延迟**：增加消费者线程数或实例数
3. **消息积压**：检查消费者处理逻辑和性能
4. **发送失败**：检查消息大小和网络状况

---

## 8. 最佳实践

### 8.1 性能优化
- 合理设置消费者线程数
- 控制消息大小，避免超过4MB
- 使用批量发送减少网络开销
- 合理设置超时时间

### 8.2 可靠性保证
- 启用消息重试机制
- 设置合理的重试次数
- 实现幂等性处理
- 监控消息处理状态

### 8.3 扩展性考虑
- 支持多消费者实例
- 使用队列分区提高并发
- 合理设计主题和标签
- 预留扩容空间

---

## 9. 常见问题

### 9.1 连接问题
**Q**: RocketMQ连接失败怎么办？
**A**: 检查NameServer地址是否正确，确保网络连通性，查看防火墙设置。

### 9.2 消息积压
**Q**: 队列中消息积压严重怎么处理？
**A**: 增加消费者线程数，优化消息处理逻辑，考虑水平扩展消费者实例。

### 9.3 消息丢失
**Q**: 如何防止消息丢失？
**A**: 启用消息持久化，设置合理的重试机制，实现消息确认机制。

### 9.4 重复消费
**Q**: 如何处理消息重复消费？
**A**: 在消息处理逻辑中实现幂等性，使用唯一标识符去重。

---

## 10. 版本信息

- **文档版本**: v1.0
- **创建日期**: 2024-12-19
- **最后更新**: 2024-12-19
- **维护者**: 开发团队

---

## 11. 参考资料

- [RocketMQ官方文档](https://rocketmq.apache.org/docs/quick-start/)
- [RocketMQ Python客户端](https://github.com/apache/rocketmq-client-python)
- [FastAPI异步编程](https://fastapi.tiangolo.com/async/)
- [项目架构设计文档](../架构设计.md)
