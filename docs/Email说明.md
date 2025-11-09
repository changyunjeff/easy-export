# 邮件服务配置说明

## 什么是邮件服务？

邮件服务模块提供了完整的 SMTP 邮件发送功能，支持：
- 纯文本邮件发送
- HTML 邮件发送
- 基于 Jinja2 模板的邮件发送
- 多个收件人支持
- 自动连接管理和错误处理

## 配置方法

### 1. 在配置文件中启用邮件服务

编辑你的配置文件（如 `config.dev.yaml`），在 `email` 部分进行配置：

```yaml
email:
  enabled: true                    # 启用邮件服务
  smtp:
    host: "smtp.qq.com"           # SMTP 服务器地址
    port: 587                     # SMTP 端口
    user: "your-email@qq.com"     # 发件人邮箱
    password: "your-password"     # SMTP 密码（通常是授权码）
    tls: true                     # 是否启用 TLS
    template_dir: "static/email_template"  # 邮件模板目录（可选）
```

### 2. 配置参数说明

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `enabled` | `bool` | 是否启用邮件服务 | `false` |
| `smtp.host` | `str` | SMTP 服务器地址 | 必填 |
| `smtp.port` | `int` | SMTP 端口（通常 587 或 465） | 必填 |
| `smtp.user` | `str` | 发件人邮箱地址 | 必填 |
| `smtp.password` | `str` | SMTP 密码或授权码 | 必填 |
| `smtp.tls` | `bool` | 是否启用 TLS（587 端口通常为 true，465 端口通常为 false） | `true` |
| `smtp.template_dir` | `str` | 邮件模板目录路径（可选） | `None` |

### 3. 常见邮件服务商配置

#### 场景 1：QQ 邮箱

```yaml
email:
  enabled: true
  smtp:
    host: "smtp.qq.com"
    port: 587
    user: "your-email@qq.com"
    password: "your-authorization-code"  # 需要在 QQ 邮箱设置中生成授权码
    tls: true
    template_dir: "static/email_template"
```

**获取 QQ 邮箱授权码：**
1. 登录 QQ 邮箱网页版
2. 进入"设置" → "账户"
3. 找到"POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV服务"
4. 开启"POP3/SMTP服务"或"IMAP/SMTP服务"
5. 点击"生成授权码"，按提示操作获取授权码

#### 场景 2：Gmail

```yaml
email:
  enabled: true
  smtp:
    host: "smtp.gmail.com"
    port: 587
    user: "your-email@gmail.com"
    password: "your-app-password"  # 需要使用应用专用密码
    tls: true
    template_dir: "static/email_template"
```

**获取 Gmail 应用专用密码：**
1. 登录 Google 账户
2. 进入"安全性" → "两步验证"
3. 在底部找到"应用专用密码"
4. 生成新的应用专用密码用于 SMTP

#### 场景 3：Outlook / Hotmail

```yaml
email:
  enabled: true
  smtp:
    host: "smtp-mail.outlook.com"
    port: 587
    user: "your-email@outlook.com"
    password: "your-password"
    tls: true
    template_dir: "static/email_template"
```

#### 场景 4：163 邮箱

```yaml
email:
  enabled: true
  smtp:
    host: "smtp.163.com"
    port: 465
    user: "your-email@163.com"
    password: "your-authorization-code"  # 需要在 163 邮箱设置中生成授权码
    tls: false  # 465 端口使用 SSL，不需要 TLS
    template_dir: "static/email_template"
```

#### 场景 5：企业邮箱（自定义 SMTP）

```yaml
email:
  enabled: true
  smtp:
    host: "smtp.yourcompany.com"
    port: 587
    user: "noreply@yourcompany.com"
    password: "your-password"
    tls: true
    template_dir: "static/email_template"
```

## 使用方法

### 1. 初始化邮件服务

邮件服务会在应用启动时自动初始化（如果配置了 `email.enabled: true`）。你也可以手动初始化：

```python
from core.email import init_email

# 初始化邮件服务
success = init_email(
    host="smtp.qq.com",
    port=587,
    user="your-email@qq.com",
    password="your-password",
    tls=True
)

if success:
    print("邮件服务初始化成功")
else:
    print("邮件服务初始化失败")
```

### 2. 发送纯文本邮件

```python
from core.email import send_email

# 发送纯文本邮件
success = send_email(
    to="recipient@example.com",
    subject="测试邮件",
    body="这是一封测试邮件。"
)

if success:
    print("邮件发送成功")
else:
    print("邮件发送失败")
```

### 3. 发送 HTML 邮件

```python
from core.email import send_email

# 发送 HTML 邮件
html_content = """
<html>
<body>
    <h1>欢迎使用</h1>
    <p>这是一封 <strong>HTML</strong> 格式的邮件。</p>
</body>
</html>
"""

success = send_email(
    to="recipient@example.com",
    subject="HTML 测试邮件",
    body="这是纯文本版本（如果邮件客户端不支持 HTML）",
    html=html_content
)
```

### 4. 使用模板发送邮件

首先，确保在配置中设置了 `template_dir`，然后在模板目录中创建模板文件。

**模板文件示例：`static/email_template/welcome.html`**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <h1>欢迎，{{ name }}！</h1>
    <p>您的验证码是：<strong>{{ code }}</strong></p>
    <p>有效期：{{ expire_time }} 分钟</p>
</body>
</html>
```

**使用模板发送邮件：**

```python
from core.email import send_email

# 使用模板发送邮件
success = send_email(
    to="recipient@example.com",
    subject="欢迎邮件",
    template="welcome",  # 模板名称（不含扩展名）
    context={
        "name": "张三",
        "code": "123456",
        "expire_time": 10
    }
)
```

### 5. 发送给多个收件人

```python
from core.email import send_email

# 发送给多个收件人
success = send_email(
    to=["user1@example.com", "user2@example.com", "user3@example.com"],
    subject="群发邮件",
    body="这是一封群发邮件。"
)
```

### 6. 使用 EmailClient 类

如果需要更多控制，可以直接使用 `EmailClient` 类：

```python
from core.email import get_email_client

# 获取邮件客户端实例
client = get_email_client(template_dir="static/email_template")

# 发送邮件
success = client.send(
    to="recipient@example.com",
    subject="测试邮件",
    body="邮件内容",
    html="<html><body><h1>HTML 内容</h1></body></html>"
)

# 使用模板发送
success = client.send_template(
    to="recipient@example.com",
    subject="模板邮件",
    template="welcome",
    context={"name": "张三", "code": "123456"}
)
```

### 7. 指定发件人

默认情况下，发件人使用配置中的 `user`。你可以指定不同的发件人：

```python
from core.email import send_email

success = send_email(
    to="recipient@example.com",
    subject="测试邮件",
    body="邮件内容",
    from_email="custom-sender@example.com"  # 自定义发件人
)
```

## 模板系统

### 模板目录结构

```
static/
  email_template/
    welcome.html          # HTML 模板
    welcome.txt           # 纯文本模板（可选）
    notification.html     # 另一个模板
    notification.txt      # 对应的纯文本模板（可选）
```

### 模板语法

邮件模板使用 Jinja2 语法，支持：

- **变量插值**：`{{ variable_name }}`
- **条件语句**：`{% if condition %}...{% endif %}`
- **循环语句**：`{% for item in items %}...{% endfor %}`
- **过滤器**：`{{ value | default('默认值') }}`

**示例模板：**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
</head>
<body>
    <h1>{{ title | default('欢迎') }}</h1>
    
    {% if name %}
    <p>亲爱的 {{ name }}，</p>
    {% endif %}
    
    <p>{{ content }}</p>
    
    {% if items %}
    <ul>
        {% for item in items %}
        <li>{{ item }}</li>
        {% endfor %}
    </ul>
    {% endif %}
    
    {% if button_text and button_url %}
    <a href="{{ button_url }}">{{ button_text }}</a>
    {% endif %}
</body>
</html>
```

### 模板变量

模板变量通过 `context` 参数传递：

```python
send_email(
    to="recipient@example.com",
    subject="通知",
    template="notification",
    context={
        "title": "系统通知",
        "name": "张三",
        "content": "您有一条新消息",
        "items": ["项目1", "项目2", "项目3"],
        "button_text": "查看详情",
        "button_url": "https://example.com/details"
    }
)
```

### 内置模板示例

项目提供了一个示例模板 `test.html`，展示了完整的邮件模板结构，包括：
- 响应式设计
- 渐变头部
- 信息卡片
- 按钮链接
- 页脚信息

可以参考该模板创建自己的邮件模板。

## 验证配置

### 1. 检查服务器日志

启动服务器后，如果邮件服务配置正确，你应该在日志中看到：

```
INFO - Email service initialized successfully
INFO - Email client connected to smtp.qq.com:587
```

如果配置错误，会看到：

```
ERROR - Failed to connect to email server: ...
WARNING - Email service initialization failed
```

### 2. 使用测试脚本

创建一个简单的测试脚本：

```python
from core.email import init_email, send_email, close_email

# 初始化
init_email(
    host="smtp.qq.com",
    port=587,
    user="your-email@qq.com",
    password="your-password",
    tls=True
)

# 发送测试邮件
success = send_email(
    to="your-test-email@example.com",
    subject="配置测试",
    body="如果您收到这封邮件，说明配置成功！"
)

if success:
    print("✓ 邮件发送成功，请检查收件箱")
else:
    print("✗ 邮件发送失败，请检查配置和日志")

# 关闭连接
close_email()
```

### 3. 运行测试套件

项目提供了完整的邮件功能测试，运行以下命令：

```bash
# 运行所有测试（不发送实际邮件）
pytest tests/test_email_client.py -v

# 运行所有测试（包括实际发送邮件）
# Linux/Mac (Bash):
ENABLE_EMAIL_TESTS=true pytest tests/test_email_client.py -v

# Windows PowerShell:
$env:ENABLE_EMAIL_TESTS="true"; pytest tests/test_email_client.py -v

# Windows CMD:
set ENABLE_EMAIL_TESTS=true && pytest tests/test_email_client.py -v
```

## 常见问题排查

### 问题 1：连接失败 "Failed to connect to email server"

**可能原因：**
1. SMTP 服务器地址或端口错误
2. 网络连接问题
3. 防火墙阻止连接

**解决方案：**
1. 检查 `host` 和 `port` 配置是否正确
2. 确认网络连接正常
3. 检查防火墙设置
4. 尝试使用不同的端口（587 或 465）

### 问题 2：认证失败 "Authentication failed"

**可能原因：**
1. 用户名或密码错误
2. 使用了邮箱登录密码而不是授权码
3. 未开启 SMTP 服务

**解决方案：**
1. 确认使用的是授权码而不是邮箱登录密码
2. 检查邮箱设置中是否已开启 SMTP 服务
3. 重新生成授权码并更新配置

### 问题 3：邮件发送失败但无错误信息

**可能原因：**
1. 收件人地址格式错误
2. 邮件被标记为垃圾邮件
3. SMTP 服务器限制

**解决方案：**
1. 检查收件人邮箱地址格式是否正确
2. 检查垃圾邮件文件夹
3. 查看服务器日志获取详细错误信息
4. 确认发件人邮箱没有被限制发送

### 问题 4：模板未找到 "Template not found"

**可能原因：**
1. 模板目录路径配置错误
2. 模板文件不存在
3. 模板名称拼写错误

**解决方案：**
1. 检查 `template_dir` 配置路径是否正确
2. 确认模板文件存在于指定目录
3. 检查模板名称（不含扩展名）是否正确
4. 确认模板文件有读取权限

### 问题 5：TLS/SSL 连接错误

**可能原因：**
1. `tls` 配置与端口不匹配
2. SMTP 服务器不支持 TLS

**解决方案：**
1. 端口 587 通常使用 `tls: true`
2. 端口 465 通常使用 `tls: false`（使用 SSL）
3. 查看邮件服务商的官方文档确认正确的配置

### 问题 6：邮件服务未启用

**可能原因：**
1. 配置文件中 `enabled: false`
2. 初始化失败但未检查返回值

**解决方案：**
1. 检查配置文件中 `email.enabled` 是否为 `true`
2. 检查初始化函数的返回值
3. 使用 `is_email_enabled()` 检查服务状态：

```python
from core.email import is_email_enabled

if is_email_enabled():
    print("邮件服务已启用")
else:
    print("邮件服务未启用")
```

## 安全建议

1. **保护授权码**：
   - 不要在代码中硬编码密码
   - 使用环境变量或配置文件（不要提交到版本控制）
   - 定期更换授权码

2. **限制发送频率**：
   - 实现发送频率限制，避免被标记为垃圾邮件
   - 使用队列系统处理大量邮件

3. **验证收件人**：
   - 验证收件人邮箱地址格式
   - 实现退订机制

4. **内容安全**：
   - 使用模板时，注意防止 XSS 攻击
   - 对用户输入进行转义（Jinja2 的 `autoescape=True` 已默认启用）

5. **错误处理**：
   - 记录所有发送失败的邮件
   - 实现重试机制
   - 监控邮件发送成功率

## 最佳实践

1. **使用模板**：
   - 统一邮件样式和格式
   - 便于维护和更新
   - 支持多语言

2. **提供纯文本版本**：
   - 创建对应的 `.txt` 模板文件
   - 确保不支持 HTML 的邮件客户端也能正常显示

3. **测试邮件**：
   - 在不同邮件客户端测试（Gmail、Outlook、Apple Mail 等）
   - 测试移动端显示效果
   - 测试不同邮件服务商的接收情况

4. **日志记录**：
   - 记录所有邮件发送操作
   - 记录发送成功/失败状态
   - 记录收件人和主题

5. **异步发送**：
   - 对于大量邮件，使用异步任务队列
   - 避免阻塞主应用流程

## 代码示例

### 完整示例：发送验证码邮件

```python
from core.email import send_email
import random

def send_verification_code(email: str, name: str) -> bool:
    """发送验证码邮件"""
    # 生成 6 位验证码
    code = str(random.randint(100000, 999999))
    
    # 发送邮件
    success = send_email(
        to=email,
        subject="验证码邮件",
        template="verification",
        context={
            "name": name,
            "code": code,
            "expire_time": 10
        }
    )
    
    if success:
        # 将验证码存储到缓存或数据库
        # cache.set(f"verification_code:{email}", code, expire=600)
        pass
    
    return success
```

### 完整示例：发送通知邮件

```python
from core.email import send_email
from typing import List

def send_notification_email(
    recipients: List[str],
    title: str,
    content: str,
    button_text: str = None,
    button_url: str = None
) -> bool:
    """发送通知邮件"""
    return send_email(
        to=recipients,
        subject=title,
        template="notification",
        context={
            "title": title,
            "content": content,
            "button_text": button_text,
            "button_url": button_url
        }
    )
```

## 相关资源

- [Python SMTP 文档](https://docs.python.org/3/library/smtplib.html)
- [Jinja2 模板文档](https://jinja.palletsprojects.com/)
- [邮件模板设计最佳实践](https://www.campaignmonitor.com/dev-resources/guides/coding/)

## 测试

项目提供了完整的邮件功能白盒测试，运行以下命令进行测试：

```bash
pytest tests/test_email_client.py -v
```

测试会验证：
- 邮件客户端初始化
- 模板渲染功能
- 纯文本邮件发送
- HTML 邮件发送
- 模板邮件发送
- 多个收件人支持
- 错误处理

默认情况下，实际发送邮件的测试会被跳过。需要实际发送邮件时，请设置环境变量 `ENABLE_EMAIL_TESTS=true`。

