# CORS 配置说明

## 什么是 CORS？

CORS（Cross-Origin Resource Sharing，跨域资源共享）是一种机制，允许 Web 页面从不同域（协议、域名或端口）请求资源。当你的前端应用（例如运行在 `http://localhost:3000`）需要访问后端 API（例如运行在 `http://localhost:8000`）时，就需要配置 CORS。

## 配置方法

### 1. 在配置文件中启用 CORS

编辑你的配置文件（如 `config.dev.yaml`），在 `api.cors` 部分进行配置：

```yaml
api:
  prefix: "/api/v1"
  cors:
    enabled: true                    # 启用 CORS 中间件
    allow_origins:                   # 允许的源（域名）列表
      - "http://localhost:3000"      # 前端应用地址
      - "http://localhost:5173"      # 可以添加多个源
      - "https://yourdomain.com"     # 生产环境域名
    allow_headers:                   # 允许的请求头
      - "Content-Type"
      - "Authorization"
      - "X-Requested-With"           # 可选：某些框架需要
    allow_credentials: true          # 允许发送 Cookie 和认证信息
    expose_headers: []               # 暴露给前端的响应头（可选）
    max_age: 7200                    # 预检请求缓存时间（秒）
```

### 2. 配置参数说明

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `enabled` | `bool` | 是否启用 CORS 中间件 | `false` |
| `allow_origins` | `list[str]` | 允许的源列表，支持通配符 `["*"]`（不推荐生产环境使用） | `[]` |
| `allow_headers` | `list[str]` | 允许的请求头列表 | `["Content-Type"]` |
| `allow_credentials` | `bool` | 是否允许发送凭证（Cookie、Authorization 等） | `false` |
| `expose_headers` | `list[str]` | 暴露给前端的响应头列表 | `[]` |
| `max_age` | `int` | 预检请求（OPTIONS）的缓存时间（秒） | `600` |

### 3. 常见配置场景

#### 场景 1：开发环境（本地开发）

```yaml
api:
  cors:
    enabled: true
    allow_origins:
      - "http://localhost:3000"      # React 默认端口
      - "http://localhost:5173"      # Vite 默认端口
      - "http://localhost:8080"      # Vue CLI 默认端口
    allow_headers:
      - "Content-Type"
      - "Authorization"
    allow_credentials: true
    max_age: 7200
```

#### 场景 2：生产环境（特定域名）

```yaml
api:
  cors:
    enabled: true
    allow_origins:
      - "https://yourdomain.com"
      - "https://www.yourdomain.com"
    allow_headers:
      - "Content-Type"
      - "Authorization"
      - "X-Requested-With"
    allow_credentials: true
    expose_headers:
      - "X-Total-Count"              # 如果 API 返回分页总数
    max_age: 86400                    # 24 小时
```

#### 场景 3：允许所有源（仅限开发/测试，不推荐生产环境）

```yaml
api:
  cors:
    enabled: true
    allow_origins:
      - "*"                           # 允许所有源
    allow_headers:
      - "*"                           # 允许所有请求头
    allow_credentials: false         # 注意：使用 "*" 时不能为 true
    max_age: 3600
```

⚠️ **警告**：在生产环境中使用 `allow_origins: ["*"]` 会带来安全风险，建议仅用于开发或测试环境。

## 验证配置

### 1. 检查服务器日志

启动服务器后，如果 CORS 配置正确，你应该在日志中看到：

```
INFO - CORS middleware enabled with origins: ['http://localhost:3000']
```

### 2. 使用浏览器开发者工具

1. 打开浏览器开发者工具（F12）
2. 切换到 **Network** 标签
3. 发送一个跨域请求
4. 检查请求头中的 `Access-Control-*` 响应头：

```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
Access-Control-Allow-Methods: *
Access-Control-Allow-Headers: Content-Type, Authorization
```

### 3. 使用 curl 测试

#### 测试简单请求（GET）

```bash
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -v http://localhost:8000/health
```

#### 测试预检请求（OPTIONS）

```bash
curl -X OPTIONS \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type,Authorization" \
     -v http://localhost:8000/api/v1/examples/health
```

## 常见问题排查

### 问题 1：CORS 错误 "Access to fetch at '...' from origin '...' has been blocked by CORS policy"

**原因**：前端请求的源不在 `allow_origins` 列表中。

**解决方案**：
1. 检查前端应用的完整 URL（包括协议、域名、端口）
2. 确保该 URL 已添加到 `allow_origins` 列表中
3. 重启服务器使配置生效

### 问题 2：预检请求（OPTIONS）失败

**原因**：请求头不在 `allow_headers` 列表中。

**解决方案**：
1. 检查浏览器控制台的错误信息，确认缺少哪个请求头
2. 将该请求头添加到 `allow_headers` 列表中
3. 重启服务器

### 问题 3：无法发送 Cookie 或认证信息

**原因**：`allow_credentials` 设置为 `false`，或者使用了 `allow_origins: ["*"]`。

**解决方案**：
1. 设置 `allow_credentials: true`
2. 如果使用通配符 `*`，必须改为具体的域名列表（通配符和 `allow_credentials: true` 不能同时使用）

### 问题 4：CORS 配置不生效

**可能原因**：
1. 配置文件中 `enabled: false` 或缺少 `cors` 配置
2. 配置文件路径不正确
3. 服务器未重启

**解决方案**：
1. 检查配置文件中的 `api.cors.enabled` 是否为 `true`
2. 确认配置文件路径正确（默认使用 `config.dev.yaml`）
3. 重启服务器
4. 检查日志中是否有 CORS 相关的错误信息

### 问题 5：生产环境配置

**建议**：
1. 不要使用 `allow_origins: ["*"]`
2. 明确列出所有允许的域名
3. 使用 HTTPS
4. 设置合理的 `max_age` 值（建议 86400 秒，即 24 小时）
5. 只暴露必要的响应头

## 前端代码示例

### JavaScript / Fetch API

```javascript
// 简单请求（GET）
fetch('http://localhost:8000/api/v1/examples/health', {
  method: 'GET',
  credentials: 'include',  // 如果需要发送 Cookie
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-token'  // 如果需要认证
  }
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));

// 复杂请求（POST）
fetch('http://localhost:8000/api/v1/examples/health', {
  method: 'POST',
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer your-token'
  },
  body: JSON.stringify({ key: 'value' })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

### Axios

```javascript
import axios from 'axios';

// 配置 axios 实例
const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true,  // 发送 Cookie
  headers: {
    'Content-Type': 'application/json'
  }
});

// 使用
api.get('/api/v1/examples/health')
  .then(response => console.log(response.data))
  .catch(error => console.error('Error:', error));
```

## 安全建议

1. **最小权限原则**：只允许必要的源和请求头
2. **生产环境**：不要使用通配符 `*`
3. **HTTPS**：生产环境使用 HTTPS
4. **定期审查**：定期检查 `allow_origins` 列表，移除不再需要的域名
5. **监控**：监控 CORS 相关的错误日志，及时发现异常请求

## 相关资源

- [MDN - CORS](https://developer.mozilla.org/zh-CN/docs/Web/HTTP/CORS)
- [FastAPI CORS 文档](https://fastapi.tiangolo.com/tutorial/cors/)
- [W3C CORS 规范](https://www.w3.org/TR/cors/)

## 测试

项目提供了 CORS 白盒测试，运行以下命令进行测试：

```bash
pytest tests/test_cors.py -v
```

测试会验证：
- CORS 中间件是否正确启用
- 允许的源是否正确配置
- 预检请求（OPTIONS）是否正常工作
- 简单请求和复杂请求的 CORS 响应头是否正确
- 不允许的源是否被正确拒绝

