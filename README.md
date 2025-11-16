<div align="center">
  <h1>📄 Easy Export</h1>
  <p><strong>通用内容导出工具集</strong></p>
  <p>一个高性能、标准化的结构化数据导出工具，支持 Word、PDF、HTML 等多种格式导出</p>
  
  <p>
    <img src="https://img.shields.io/badge/Python-3.8+-blue.svg" alt="Python Version">
    <img src="https://img.shields.io/badge/FastAPI-0.121.1-green.svg" alt="FastAPI">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License">
    <img src="https://img.shields.io/badge/Status-Production-success.svg" alt="Status">
  </p>
</div>

---

<h2 id="table-of-contents">📚 目录</h2>

<details open>
<summary><b>点击展开/收起目录</b></summary>

- [项目简介](#项目简介)
- [核心特性](#核心特性)
- [技术架构](#技术架构)
- [快速开始](#快速开始)
  - [环境要求](#环境要求)
  - [安装步骤](#安装步骤)
  - [环境变量配置](#环境变量配置)
  - [启动服务](#启动服务)
  - [Docker部署](#docker部署)
- [API接口说明](#api接口说明)
  - [模板管理接口](#模板管理接口)
  - [导出接口](#导出接口)
  - [校验接口](#校验接口)
  - [统计接口](#统计接口)
  - [队列监控接口](#队列监控接口)
  - [文件管理接口](#文件管理接口)
- [配置说明](#配置说明)
  - [应用配置](#应用配置)
  - [Redis配置](#redis配置)
  - [RocketMQ配置](#rocketmq配置)
  - [邮件服务配置](#邮件服务配置)
  - [安全配置](#安全配置)
- [使用示例](#使用示例)
  - [Python示例](#python示例)
  - [cURL示例](#curl示例)
- [开发指南](#开发指南)
- [项目结构](#项目结构)
- [常见问题](#常见问题)
- [贡献指南](#贡献指南)
- [许可证](#许可证)
- [联系方式](#联系方式)

</details>

---

<h2 id="项目简介">🎯 项目简介</h2>

<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white;">
  
**Easy Export** 是一个针对结构化数据（如 JSON/CSV 格式的分析结果、报表数据）转化为可交付文档（如 Word/PDF/HTML）的标准化导出组件。

### 🎓 核心目标

- ✅ **格式还原度高**：模板样式还原度 ≥95%，数据填充无错位
- ✅ **样式一致性**：支持自定义模板，保持页眉页脚、字体等样式统一
- ✅ **批量处理高效**：支持并行处理，100份个性化报告稳定生成，无内存溢出
- ✅ **标准化交付**：通过 REST API 提供核心能力，便于集成到各类业务系统

</div>

### 🔧 适用场景

<table>
  <tr>
    <td>📊 数据分析报告生成</td>
    <td>📈 业务报表导出</td>
  </tr>
  <tr>
    <td>📑 合同/协议生成</td>
    <td>🔬 科研文献定制导出</td>
  </tr>
  <tr>
    <td>📝 简历解析与排版</td>
    <td>🎨 其他结构化数据转文档场景</td>
  </tr>
</table>

---

<h2 id="核心特性">⚡ 核心特性</h2>

<div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px;">

<div style="border: 2px solid #4CAF50; border-radius: 10px; padding: 15px;">
  <h3>🎨 模板管理</h3>
  <ul>
    <li>支持 Word (.docx)、PDF、HTML 格式模板</li>
    <li>占位符支持：文本、表格、图片、图表</li>
    <li>版本管理：保留历史、支持回滚</li>
    <li>元数据管理：名称、描述、标签、哈希值</li>
  </ul>
</div>

<div style="border: 2px solid #2196F3; border-radius: 10px; padding: 15px;">
  <h3>📝 动态数据填充</h3>
  <ul>
    <li>文本填充：支持过滤器（date、default、upper等）</li>
    <li>表格填充：自动匹配列数、支持合并单元格</li>
    <li>图表填充：支持折线图、柱状图、饼图</li>
    <li>图片填充：支持 Base64、URL、本地路径</li>
  </ul>
</div>

<div style="border: 2px solid #FF9800; border-radius: 10px; padding: 15px;">
  <h3>⚙️ 批量导出</h3>
  <ul>
    <li>并行处理：支持线程池/进程池</li>
    <li>队列管理：RocketMQ异步任务队列</li>
    <li>分块处理：大任务分块，避免内存溢出</li>
    <li>失败重试：自动重试，指数退避策略</li>
  </ul>
</div>

<div style="border: 2px solid #9C27B0; border-radius: 10px; padding: 15px;">
  <h3>🔍 格式校验</h3>
  <ul>
    <li>数据错位检查：表格行数、字段映射</li>
    <li>链接有效性：HTTP/HTTPS链接检查</li>
    <li>样式统一性：字体、页眉页脚一致性</li>
    <li>必填字段检查：完整性验证</li>
  </ul>
</div>

</div>

---

<h2 id="技术架构">🏗️ 技术架构</h2>

```
┌─────────────────────────────────────────────────────────────┐
│                        客户端层                               │
│  (Web前端 / 移动端 / 第三方系统 / API调用)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/HTTPS
┌──────────────────────▼──────────────────────────────────────┐
│                   应用服务层 (FastAPI)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 模板管理服务 │  │  导出服务    │  │  校验服务    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                     核心引擎层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 模板引擎     │  │  渲染引擎    │  │  填充引擎    │      │
│  │ (Jinja2)     │  │ (python-docx)│  │ (数据映射)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────┬──────────────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                     数据存储层                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Redis缓存    │  │  RocketMQ    │  │  文件存储    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### 📦 核心技术栈

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| Web框架 | FastAPI | 0.121.1 | 高性能异步Web框架 |
| 模板引擎 | Jinja2 | 3.1.6 | 模板渲染 |
| Word处理 | python-docx | 1.2.0 | Word文档生成 |
| PDF转换 | weasyprint | 66.0 | HTML转PDF |
| 图表生成 | matplotlib | 3.9.2 | 图表可视化 |
| 消息队列 | RocketMQ | 2.0.0 | 异步任务处理 |
| 缓存 | Redis | 7.0.1 | 数据缓存 |
| 图片处理 | Pillow | 10.4.0 | 图片处理 |

---

<h2 id="快速开始">🚀 快速开始</h2>

<h3 id="环境要求">📋 环境要求</h3>

<table style="width: 100%;">
  <tr>
    <th>组件</th>
    <th>要求</th>
  </tr>
  <tr>
    <td>Python</td>
    <td>3.8+</td>
  </tr>
  <tr>
    <td>Redis</td>
    <td>7.0+ (可选，有内存回退)</td>
  </tr>
  <tr>
    <td>RocketMQ</td>
    <td>4.9.4+ (可选)</td>
  </tr>
  <tr>
    <td>GTK3/Cairo</td>
    <td>用于PDF生成（Windows需要MSYS2）</td>
  </tr>
  <tr>
    <td>LibreOffice/MS Word</td>
    <td>用于Word转PDF（可选）</td>
  </tr>
</table>

<h3 id="安装步骤">📥 安装步骤</h3>

<details>
<summary><b>步骤 1: 克隆项目</b></summary>

```bash
git clone https://github.com/your-org/easy_export.git
cd easy_export
```
</details>

<details>
<summary><b>步骤 2: 创建虚拟环境</b></summary>

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```
</details>

<details>
<summary><b>步骤 3: 安装依赖</b></summary>

```bash
# 生产环境
pip install -r requirements.txt

# 开发环境（包含测试工具）
pip install -r requirements-dev.txt
```
</details>

<details>
<summary><b>步骤 4: 安装GTK3（用于PDF生成）</b></summary>

**Windows (使用MSYS2):**
```bash
# 1. 下载并安装 MSYS2: https://www.msys2.org/
# 2. 在MSYS2终端中安装GTK3
pacman -S mingw-w64-ucrt-x86_64-gtk3 mingw-w64-ucrt-x86_64-cairo

# 3. 将MSYS2的bin目录添加到环境变量（见下方环境变量配置）
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0 \
    libgirepository1.0-dev libcairo2-dev pkg-config
```

**Mac:**
```bash
brew install gtk+3 cairo pango gdk-pixbuf libffi
```

详细说明请参考：[docs/GTK3配置指南.md](docs/GTK3配置指南.md)

</details>

<h3 id="环境变量配置">🔧 环境变量配置</h3>

在项目根目录创建 `.env` 文件：

```bash
# 环境配置
ENV=dev

# SMTP邮件服务密码（如果启用邮件功能）
SMTP_PASSWORD=your-password

# JWT密钥（如果启用认证功能）
JWT_SECRET_KEY=your-secret-key-at-least-32-characters-long

# GTK3路径（Windows MSYS2）
MSYS2_BIN=D:/chang/app/msys2/ucrt64/bin

# Redis配置（可选）
# REDIS_HOST=localhost
# REDIS_PORT=6379
# REDIS_PASSWORD=

# RocketMQ配置（可选）
# ROCKETMQ_NAMESERVER=localhost:9876
```

<h3 id="启动服务">▶️ 启动服务</h3>

<details>
<summary><b>开发模式（带热重载）</b></summary>

```bash
python main.py
```

服务将在 `http://localhost:8000` 启动

- API文档: http://localhost:8000/docs
- ReDoc文档: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

</details>

<details>
<summary><b>生产模式</b></summary>

```bash
# 使用uvicorn启动
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 或使用gunicorn（Linux/Mac）
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

</details>

<h3 id="docker部署">🐳 Docker部署</h3>

<details open>
<summary><b>使用Docker Compose一键启动</b></summary>

**启动Redis:**
```bash
cd .docker/redis
docker-compose up -d
```

**启动RocketMQ:**
```bash
cd .docker/rocketmq
docker-compose up -d
```

**验证服务:**
```bash
# 检查Redis
docker exec -it easy_export_redis redis-cli ping

# 检查RocketMQ
docker ps | grep rocketmq
```

**Docker Compose配置详情:**

Redis (`docker-compose.yml`):
```yaml
services:
  redis:
    image: redis:7-alpine
    container_name: easy_export_redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
```

RocketMQ (`docker-compose.yml`):
```yaml
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
```

</details>

---

<h2 id="api接口说明">📡 API接口说明</h2>

> 完整的API文档可通过 `/docs` 或 `/redoc` 访问

<h3 id="模板管理接口">📁 模板管理接口</h3>

<table>
  <thead>
    <tr>
      <th>方法</th>
      <th>端点</th>
      <th>描述</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>POST</code></td>
      <td><code>/api/v1/templates</code></td>
      <td>上传模板文件</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/templates</code></td>
      <td>获取模板列表（支持分页、筛选）</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/templates/{id}</code></td>
      <td>获取模板详情</td>
    </tr>
    <tr>
      <td><code>PUT</code></td>
      <td><code>/api/v1/templates/{id}</code></td>
      <td>更新模板元数据</td>
    </tr>
    <tr>
      <td><code>DELETE</code></td>
      <td><code>/api/v1/templates/{id}</code></td>
      <td>删除模板</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/templates/{id}/versions</code></td>
      <td>获取模板版本列表</td>
    </tr>
    <tr>
      <td><code>POST</code></td>
      <td><code>/api/v1/templates/{id}/versions</code></td>
      <td>创建新版本</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/templates/{id}/download</code></td>
      <td>下载模板文件</td>
    </tr>
  </tbody>
</table>

<h3 id="导出接口">📤 导出接口</h3>

<table>
  <thead>
    <tr>
      <th>方法</th>
      <th>端点</th>
      <th>描述</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>POST</code></td>
      <td><code>/api/v1/export</code></td>
      <td>单文档导出（支持Word/PDF/HTML）</td>
    </tr>
    <tr>
      <td><code>POST</code></td>
      <td><code>/api/v1/export/batch</code></td>
      <td>批量导出（异步处理）</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/export/tasks/{id}</code></td>
      <td>查询导出任务状态</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/export/batch/{id}</code></td>
      <td>查询批量任务状态</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/export/files/{id}</code></td>
      <td>下载导出文件</td>
    </tr>
  </tbody>
</table>

<h3 id="校验接口">✅ 校验接口</h3>

<table>
  <thead>
    <tr>
      <th>方法</th>
      <th>端点</th>
      <th>描述</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>POST</code></td>
      <td><code>/api/v1/validate</code></td>
      <td>校验文档（数据错位、链接、样式）</td>
    </tr>
  </tbody>
</table>

<h3 id="统计接口">📊 统计接口</h3>

<table>
  <thead>
    <tr>
      <th>方法</th>
      <th>端点</th>
      <th>描述</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/stats/export</code></td>
      <td>导出任务统计（成功率、耗时等）</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/stats/performance</code></td>
      <td>性能统计</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/stats/templates</code></td>
      <td>模板使用统计</td>
    </tr>
  </tbody>
</table>

<h3 id="队列监控接口">🔍 队列监控接口</h3>

<table>
  <thead>
    <tr>
      <th>方法</th>
      <th>端点</th>
      <th>描述</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/queue/status</code></td>
      <td>获取队列状态</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/queue/health</code></td>
      <td>队列健康检查</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/queue/metrics</code></td>
      <td>获取性能指标</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/queue/consumer/lag</code></td>
      <td>获取消费者延迟</td>
    </tr>
    <tr>
      <td><code>POST</code></td>
      <td><code>/api/v1/queue/consumer/restart</code></td>
      <td>重启消费者</td>
    </tr>
  </tbody>
</table>

<h3 id="文件管理接口">📂 文件管理接口</h3>

<table>
  <thead>
    <tr>
      <th>方法</th>
      <th>端点</th>
      <th>描述</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><code>POST</code></td>
      <td><code>/api/v1/files</code></td>
      <td>上传文件</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/files</code></td>
      <td>获取文件列表</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/files/{file_id}</code></td>
      <td>获取文件信息</td>
    </tr>
    <tr>
      <td><code>GET</code></td>
      <td><code>/api/v1/files/{file_id}/download</code></td>
      <td>下载文件</td>
    </tr>
    <tr>
      <td><code>DELETE</code></td>
      <td><code>/api/v1/files/{file_id}</code></td>
      <td>删除文件</td>
    </tr>
    <tr>
      <td><code>POST</code></td>
      <td><code>/api/v1/files/cleanup</code></td>
      <td>清理过期文件</td>
    </tr>
  </tbody>
</table>

---

<h2 id="配置说明">⚙️ 配置说明</h2>

<h3 id="应用配置">📱 应用配置 (config.dev.yaml)</h3>

```yaml
app:
  title: Easy Export
  port: 8000
  host: localhost
  description: Easy Export
  version: 1.0.0
  contact:
    email: changyunjeff@outlook.com
    name: Chang Yun jeff

logging:
  level: DEBUG    # DEBUG, INFO, WARNING, ERROR, CRITICAL
  console_enabled: true
  log_path: "logs/dev.log"
  access_log_path: "logs/access.log"
  error_log_path: "logs/error.log"
```

<h3 id="redis配置">🔴 Redis配置</h3>

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

<blockquote>
💡 <strong>注意：</strong> 如果Redis连接失败，系统会自动降级到内存存储（非持久化）
</blockquote>

<h3 id="rocketmq配置">🚀 RocketMQ配置</h3>

```yaml
rocketmq:
  enabled: true
  name_server: "localhost:9876"           # RocketMQ NameServer地址
  producer_group: "export_producer_group" # 生产者组名
  consumer_group: "export_consumer_group" # 消费者组名
  topic: "export_tasks"                   # 导出任务主题
  tag: "*"                               # 消息标签过滤器
  max_message_size: 4194304              # 最大消息大小(4MB)
  send_timeout: 3000                     # 发送超时时间(毫秒)
  retry_times: 3                         # 发送失败重试次数
  consumer_thread_min: 1                 # 最小消费者线程数
  consumer_thread_max: 5                 # 最大消费者线程数
```

<h3 id="邮件服务配置">📧 邮件服务配置</h3>

```yaml
email:
  enabled: true
  smtp:
    host: "smtp.qq.com"
    port: 587
    user: "1405766437@qq.com"
    tls: true
    template_dir: "static/email_template"
```

<blockquote>
🔐 <strong>安全提示：</strong> SMTP密码应通过环境变量 <code>SMTP_PASSWORD</code> 设置
</blockquote>

<h3 id="安全配置">🔒 安全配置</h3>

```yaml
# CORS配置
api:
  prefix: "/api/v1"
  cors:
    enabled: true
    allow_origins:
      - "http://localhost:3000"
    allow_headers:
      - "Content-Type"
      - "Authorization"
    allow_credentials: true
    max_age: 7200

# JWT认证配置（可选）
auth:
  enabled: true
  jwt:
    secret_key: "your-256-bit-secret"  # 应通过环境变量设置
    algorithm: "HS256"
    access_token_expire: "30m"
    refresh_token_expire: "7d"

# 限流配置
rate_limit:
  enabled: false
  requests_per_minute: 600
  requests_per_hour: 10000
  requests_per_day: 100000

# DDoS防护
ddos_protection:
  enabled: false
  max_requests_per_second: 100
  max_requests_per_minute: 1000
  block_duration: 3600
```

---

<h2 id="使用示例">💻 使用示例</h2>

<h3 id="python示例">🐍 Python示例</h3>

<details open>
<summary><b>单文档导出示例</b></summary>

```python
import requests

# 1. 上传模板
with open('template.docx', 'rb') as f:
    files = {'file': f}
    data = {
        'name': '报告模板',
        'description': '用于生成分析报告',
        'tags': '报告,分析'
    }
    response = requests.post(
        'http://localhost:8000/api/v1/templates',
        files=files,
        data=data
    )
    template = response.json()['data']
    template_id = template['template_id']

# 2. 单文档导出
export_data = {
    'data': {
        'title': '2024年度报告',
        'author': '张三',
        'date': '2024-01-01',
        'table:sales_data': [
            {'product': '产品A', 'sales': 1000, 'profit': 200},
            {'product': '产品B', 'sales': 2000, 'profit': 400}
        ],
        'chart:sales_trend': {
            'type': 'line',
            'data': [
                {'month': '1月', 'value': 1000},
                {'month': '2月', 'value': 1200},
                {'month': '3月', 'value': 1500}
            ],
            'title': '销售趋势图',
            'xlabel': '月份',
            'ylabel': '销售额'
        }
    },
    'template_ref': template_id,
    'output_format': 'pdf',
    'validate': True
}

response = requests.post(
    'http://localhost:8000/api/v1/export',
    json=export_data
)
result = response.json()['data']

# 3. 查询任务状态
task_id = result['task_id']
status_response = requests.get(
    f'http://localhost:8000/api/v1/export/tasks/{task_id}'
)
task_status = status_response.json()['data']

# 4. 下载文件
if task_status['status'] == 'completed':
    file_url = task_status['file_url']
    file_response = requests.get(file_url)
    with open('output.pdf', 'wb') as f:
        f.write(file_response.content)
    print(f"✅ 文件已下载: output.pdf")
```

</details>

<details>
<summary><b>批量导出示例</b></summary>

```python
import requests

# 批量导出
batch_data = {
    'items': [
        {
            'data': {'title': f'报告{i}', 'author': '张三'},
            'template_ref': template_id,
            'output_format': 'pdf'
        }
        for i in range(1, 101)  # 生成100份报告
    ],
    'concurrency': 10,
    'validate': True
}

response = requests.post(
    'http://localhost:8000/api/v1/export/batch',
    json=batch_data
)
batch_task = response.json()['data']
batch_task_id = batch_task['task_id']

# 轮询批量任务状态
import time
while True:
    status_response = requests.get(
        f'http://localhost:8000/api/v1/export/batch/{batch_task_id}'
    )
    status = status_response.json()['data']
    
    print(f"进度: {status['progress']}% | "
          f"成功: {status['success']} | "
          f"失败: {status['failed']}")
    
    if status['status'] in ['completed', 'failed']:
        break
    
    time.sleep(2)

print(f"✅ 批量任务完成！")
print(f"总计: {status['total']} | 成功: {status['success']} | 失败: {status['failed']}")
```

</details>

<h3 id="curl示例">📝 cURL示例</h3>

<details>
<summary><b>基础API调用</b></summary>

```bash
# 1. 健康检查
curl http://localhost:8000/health

# 2. 上传模板
curl -X POST "http://localhost:8000/api/v1/templates" \
  -F "file=@template.docx" \
  -F "name=报告模板" \
  -F "description=用于生成分析报告"

# 3. 单文档导出
curl -X POST "http://localhost:8000/api/v1/export" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "title": "2024年度报告",
      "author": "张三",
      "date": "2024-01-01"
    },
    "template_ref": "tpl_123456",
    "output_format": "pdf"
  }'

# 4. 查询任务状态
curl "http://localhost:8000/api/v1/export/tasks/task_789012"

# 5. 下载文件
curl "http://localhost:8000/api/v1/export/files/file_123456" \
  -o output.pdf

# 6. 获取统计信息
curl "http://localhost:8000/api/v1/stats/export?start_date=2024-01-01&end_date=2024-01-31"
```

</details>

---

<h2 id="开发指南">👨‍💻 开发指南</h2>

### 🧪 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_export_service.py

# 运行测试并生成覆盖率报告
pytest --cov=core --cov-report=html

# 运行性能测试
pytest tests/test_performance.py
```

### 📝 代码规范

```bash
# 代码格式化
black core/ tests/

# 代码检查
flake8 core/ tests/

# 类型检查
mypy core/
```

### 🔧 开发环境配置

1. 复制配置文件：`cp config.dev.yaml config.local.yaml`
2. 修改 `config.local.yaml` 为本地配置
3. 设置环境变量：`export ENV=local`

---

<h2 id="项目结构">📁 项目结构</h2>

```
easy_export/
├── 📁 core/                    # 核心代码
│   ├── 📁 api/                # API路由
│   │   └── 📁 v1/            # v1版本API
│   │       ├── templates.py  # 模板管理
│   │       ├── export.py     # 导出功能
│   │       ├── validate.py   # 校验功能
│   │       ├── stats.py      # 统计功能
│   │       ├── queue.py      # 队列监控
│   │       └── files.py      # 文件管理
│   ├── 📁 engine/             # 核心引擎
│   │   ├── template.py       # 模板引擎
│   │   ├── renderer.py       # 渲染引擎
│   │   ├── filler.py         # 填充引擎
│   │   ├── chart.py          # 图表生成器
│   │   ├── image.py          # 图片处理器
│   │   └── converter.py      # 格式转换器
│   ├── 📁 service/            # 业务服务
│   │   ├── template_service.py
│   │   ├── export_service.py
│   │   ├── batch_service.py
│   │   ├── validate_service.py
│   │   ├── stats_service.py
│   │   └── file_service.py
│   ├── 📁 storage/            # 存储层
│   │   ├── template_storage.py
│   │   ├── file_storage.py
│   │   └── cache_storage.py
│   ├── 📁 models/             # 数据模型
│   ├── 📁 middlewares/        # 中间件
│   ├── 📁 redis/              # Redis客户端
│   ├── 📁 rocketmq/           # RocketMQ客户端
│   └── 📁 security/           # 安全模块
├── 📁 .docker/                # Docker配置
│   ├── 📁 redis/
│   │   └── docker-compose.yml
│   └── 📁 rocketmq/
│       └── docker-compose.yml
├── 📁 tests/                  # 测试代码
├── 📁 docs/                   # 文档
├── 📁 mvp/                    # MVP示例
├── 📁 static/                 # 静态资源
├── 📁 logs/                   # 日志文件
├── 📄 main.py                 # 应用入口
├── 📄 requirements.txt        # 生产依赖
├── 📄 requirements-dev.txt    # 开发依赖
├── 📄 config.dev.yaml         # 开发环境配置
├── 📄 config.prod.yaml        # 生产环境配置
├── 📄 .env                    # 环境变量
└── 📄 README.md               # 项目说明
```

---

<h2 id="常见问题">❓ 常见问题</h2>

<details>
<summary><b>Q: PDF生成失败，提示GTK3相关错误？</b></summary>

**A:** 这是因为WeasyPrint依赖GTK3库。请按照以下步骤解决：

1. **Windows**: 安装MSYS2并配置环境变量（参考 [GTK3配置指南](docs/GTK3配置指南.md)）
2. **Linux**: `sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0`
3. **Mac**: `brew install gtk+3 cairo pango`

</details>

<details>
<summary><b>Q: Redis连接失败怎么办？</b></summary>

**A:** 系统会自动降级到内存存储（非持久化）。如需使用Redis：

1. 确保Redis服务已启动
2. 检查配置文件中的Redis连接信息
3. 使用Docker快速启动：`cd .docker/redis && docker-compose up -d`

</details>

<details>
<summary><b>Q: 批量导出任务失败？</b></summary>

**A:** 可能的原因：

1. **内存不足**: 降低并发数（`concurrency`参数）
2. **RocketMQ未启动**: 检查RocketMQ服务状态或禁用RocketMQ
3. **模板问题**: 检查模板文件是否损坏
4. **数据格式**: 验证输入数据格式是否正确

</details>

<details>
<summary><b>Q: 如何提高导出性能？</b></summary>

**A:** 优化建议：

1. 启用Redis缓存（图表、模板元数据）
2. 使用RocketMQ异步处理
3. 增加并发数（`concurrency`）
4. 使用分块处理大批量任务
5. 确保服务器资源充足（CPU、内存）

</details>

<details>
<summary><b>Q: 支持哪些占位符语法？</b></summary>

**A:** 支持以下占位符类型：

- **文本**: `{{title}}`、`{{author | default('未知')}}`
- **日期**: `{{date | date('%Y-%m-%d')}}`
- **表格**: `{{table:sales_data}}`
- **图片**: `{{image:logo}}`（支持Base64/URL/本地路径）
- **图表**: `{{chart:sales_trend}}`（line/bar/pie）

详见：[API使用指南](docs/API使用指南.md)

</details>

---

<h2 id="贡献指南">🤝 贡献指南</h2>

我们欢迎所有形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

### 贡献流程

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

### 开发规范

- 遵循 PEP 8 代码规范
- 编写单元测试
- 更新相关文档
- 提交信息清晰明确

---

<h2 id="许可证">📄 许可证</h2>

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

<h2 id="联系方式">📧 联系方式</h2>

<div align="center">

**项目维护者**: Chang Yun Jeff  
**邮箱**: [changyunjeff@outlook.com](mailto:changyunjeff@outlook.com)  

---

<p>
  <strong>⭐ 如果这个项目对你有帮助，请给我们一个 Star！</strong>
</p>

<p>
  <a href="https://github.com/your-org/easy_export/issues">报告Bug</a> ·
  <a href="https://github.com/your-org/easy_export/issues">请求功能</a> ·
  <a href="docs/">查看文档</a>
</p>

---

<p><sub>Made with ❤️ by Easy Export Team</sub></p>

</div>

