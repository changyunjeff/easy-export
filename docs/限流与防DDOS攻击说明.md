## 概述

本项目内置两道网关级防护能力：

- 率先进行的限流（Rate Limiting，`RateLimitMiddleware`）：按分钟/小时/天与突发上限进行配额控制，平滑削峰。
- 随后进行的 DDoS 防护（`DDoSProtectionMiddleware`）：按秒/分钟阈值快速识别异常流量，并短期拉黑源 IP。

二者协同工作：

1) 提取客户端 IP → 2) 执行限流 → 3) 执行 DDoS 检测（含白/黑名单） → 4) 放行或阻断。

存储层使用 Redis 计数与过期控制，具备高性能与可观测性。


## 客户端 IP 提取

按优先级提取：

1. `client.host`（例如来自反向代理或框架提供的直连地址）
2. 请求头 `X-Forwarded-For`（取链首/最左侧 IP）
3. 请求头 `X-Real-IP`
4. 回退为 `unknown`（最低概率路径，仅当无法获取任何来源时）

建议在生产环境配合可信代理设置，确保转发链条中的真实客户端 IP 可被识别。


## 限流（Rate Limit）

- 配置键空间：`rate_limit`
- 支持维度：
  - `requests_per_minute`
  - `requests_per_hour`
  - `requests_per_day`
  - `burst_size`（突发令牌数，控制瞬时并发）
  - `key_prefix`（Redis 键前缀）
  - `enabled`（是否启用）

实现要点：

- 采用「固定窗口计数」与「令牌桶突发」的组合策略：
  - 固定窗口负责长期配额（分钟/小时/天）。
  - 令牌桶负责瞬时突发控制（`burst_size`）。
- 键设计：`{key_prefix}:{ip}:{window}`，例如：`test_rate_limit:203.0.113.10:m`（分钟窗口）。
- 发生 Redis 异常时，默认降级为「放行并记录错误」，避免自损可用性。

返回头部（建议）：

- `X-RateLimit-Limit`：该窗口的总配额
- `X-RateLimit-Remaining`：当前剩余额度
- `Retry-After`：当被限流时，告知重试秒数

被触发时的表现：

- 返回 429 Too Many Requests（包含错误描述与可重试提示）。


## DDoS 防护

- 配置键空间：`ddos_protection`
- 支持维度：
  - `max_requests_per_second`
  - `max_requests_per_minute`
  - `block_duration`（秒，自动拉黑时长）
  - `whitelist_ips`（跳过检测）
  - `blacklist_ips`（静态黑名单，直接阻断）
  - `key_prefix`（Redis 键前缀）
  - `enabled`（是否启用）

实现要点：

- 白名单优先：在白名单中的 IP 直接放行。
- 黑名单拦截：静态黑名单或自动加入的黑名单命中即阻断。
- 速率检测：
  - 秒级与分钟级计数键分别为 `...:sec`、`...:min`，设置短过期。
  - 超阈值即刻将 IP 加入黑名单键，过期时间为 `block_duration`。
- 发生 Redis 异常时，默认降级为「放行并记录错误」，避免误伤。

被触发时的表现：

- 返回 429 或 403（实现可二选一；推荐 429 统一限流类响应）。


## 配置示例

生产默认建议写入 `config.yaml`；测试场景已提供 `config.test.yaml`（极端低阈值，便于快速验证）。

```yaml
rate_limit:
  enabled: true
  requests_per_minute: 120
  requests_per_hour: 3000
  requests_per_day: 50000
  burst_size: 20
  key_prefix: "rate_limit"

ddos_protection:
  enabled: true
  max_requests_per_second: 10
  max_requests_per_minute: 300
  block_duration: 600
  whitelist_ips:
    - "127.0.0.1"
  blacklist_ips: []
  key_prefix: "ddos_protection"
```

测试用极端配置（节选，自带于 `config.test.yaml`）：

```yaml
rate_limit:
  enabled: true
  requests_per_minute: 2
  requests_per_hour: 5
  requests_per_day: 10
  burst_size: 1
  key_prefix: "test_rate_limit"

ddos_protection:
  enabled: true
  max_requests_per_second: 1
  max_requests_per_minute: 3
  block_duration: 60
  whitelist_ips:
    - "127.0.0.1"
    - "10.0.0.1"
  blacklist_ips:
    - "192.168.1.100"
    - "192.168.1.200"
  key_prefix: "test_ddos_protection"
```


## 运行与测试

- 单元测试（非异步部分）：

```bash
pytest tests/test_rate_limit.py tests/test_ddos_protection.py -v -k "not asyncio"
```

- 若需运行异步测试，请安装插件：

```bash
pip install pytest-asyncio
pytest -v
```

测试覆盖点包含：初始化、IP 提取、白/黑名单策略、计数与阈值命中、Redis 异常降级等。


## 故障与排查

- 频繁 429：
  - 检查是否命中 DDoS 黑名单（静态或自动），确认 `block_duration` 是否过长。
  - 评估业务峰值并适调 `burst_size` 与各时间窗额度。
  - 分流或启用缓存减轻上游压力。
- 误判过严：
  - 放宽 `max_requests_per_second`/`minute` 或提高 `requests_per_minute` 等值。
  - 将可信来源加入 `whitelist_ips`。
- Redis 异常：
  - 中间件会降级放行，请关注日志并恢复 Redis；必要时可暂时调低阈值。


## 调优建议

- 用分钟/小时/天三个窗口覆盖短中长期速率，防止「细水长流型」滥用。
- 使用 `burst_size` 允许合理突发，兼顾用户体验与系统保护。
- DDoS 阈值宜偏紧，以黑名单短封为主，避免长时间误封。
- 为关键路径接入观测，记录：命中窗口、剩余额度、拉黑原因与剩余封禁时间。


## HTTP 示例

- 正常请求：

```bash
curl -i https://api.example.com/resource
```

可能返回头：

```
HTTP/1.1 200 OK
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 87
```

- 被限流（429）：

```bash
curl -i https://api.example.com/resource
```

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
Content-Type: application/json

{"error":"rate_limited","message":"Too many requests. Please retry later."}
```

- 被 DDoS 封禁（示例同 429，或可返回 403）：

```
HTTP/1.1 429 Too Many Requests
Content-Type: application/json

{"error":"blocked","message":"Your IP has been temporarily blocked."}
```


## 版本与兼容

- 需要 Redis 作为后端计数与黑名单寄存。
- 测试于 Windows + Python 3.9 + pytest 8.x 验证通过。


## 变更记录（摘要）

- 新增：`RateLimitMiddleware` 与 `DDoSProtectionMiddleware` 双重防护。
- 新增：`config.test.yaml` 极端低阈值便捷测试。
- 测试：非异步用例全部通过；异步用例需 `pytest-asyncio` 支持。


