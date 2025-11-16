# HTTPS配置指南

## 1. 概述

本文档介绍如何为Easy Export项目启用HTTPS支持，包括开发环境的自签名证书配置和生产环境的真实证书配置。

### 1.1 为什么需要HTTPS？

- **数据安全**：加密客户端与服务器之间的通信
- **身份验证**：确认服务器身份，防止中间人攻击
- **合规要求**：许多安全标准要求使用HTTPS
- **浏览器信任**：现代浏览器对HTTP连接显示不安全警告
- **SEO优势**：搜索引擎更青睐HTTPS网站

### 1.2 证书类型

- **自签名证书**：用于开发和测试环境，浏览器会显示不受信任警告
- **CA签发证书**：用于生产环境，由受信任的证书颁发机构签发
  - 免费：Let's Encrypt、ZeroSSL
  - 付费：DigiCert、GlobalSign、Comodo等

---

## 2. 开发环境配置（自签名证书）

### 2.1 生成自签名证书

使用项目提供的证书生成工具：

```bash
# 生成开发环境证书（默认）
python script/generate_ssl_cert.py

# 生成测试环境证书
python script/generate_ssl_cert.py --env test

# 生成有效期为730天的证书
python script/generate_ssl_cert.py --env dev --days 730

# 自定义域名
python script/generate_ssl_cert.py --common-name example.com
```

**输出示例**：
```
============================================================
🔐 SSL证书生成工具
============================================================
环境: dev
通用名称: localhost
组织: Easy Export
有效期: 365 天
============================================================

📁 输出目录: /path/to/easy_export/certs
🔑 生成RSA私钥...
📜 生成自签名证书...
💾 保存私钥: certs/dev-key.pem
💾 保存证书: certs/dev-cert.pem

✅ SSL证书生成成功！
   证书文件: certs/dev-cert.pem
   私钥文件: certs/dev-key.pem
   有效期: 365 天
   过期时间: 2025-11-16 10:00:00 UTC

📝 配置提示:
   在 config.dev.yaml 中设置:
   ssl:
     enabled: true
     certfile: "certs/dev-cert.pem"
     keyfile: "certs/dev-key.pem"
```

### 2.2 安装依赖

证书生成工具需要`cryptography`库：

```bash
pip install cryptography
```

或者安装开发依赖：

```bash
pip install -r requirements-dev.txt
```

### 2.3 启用HTTPS

编辑`config.dev.yaml`：

```yaml
ssl:
  enabled: true                        # 启用HTTPS
  certfile: "certs/dev-cert.pem"       # 证书文件路径
  keyfile: "certs/dev-key.pem"         # 私钥文件路径
  ca_certs: null                       # CA证书（可选）
  cert_reqs: 0                         # 不要求客户端证书
  ssl_version: null                    # 自动选择SSL版本
  ciphers: null                        # 使用默认加密套件
```

### 2.4 启动服务

```bash
python main.py
```

**输出示例**：
```
2024-11-16 10:00:00 - __main__ - INFO - 🔒 HTTPS已启用
2024-11-16 10:00:00 - __main__ - INFO -    证书文件: certs/dev-cert.pem
2024-11-16 10:00:00 - __main__ - INFO -    私钥文件: certs/dev-key.pem
2024-11-16 10:00:00 - __main__ - INFO -    访问地址: https://localhost:8000
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on https://localhost:8000 (Press CTRL+C to quit)
```

### 2.5 访问服务

浏览器访问：`https://localhost:8000`

**⚠️ 自签名证书警告**：
- Chrome/Edge：显示"您的连接不是私密连接"
- Firefox：显示"警告：潜在的安全风险"
- Safari：显示"此连接不是私密连接"

这是正常的，因为证书是自签名的。在开发环境中，你可以：
1. 点击"高级"→"继续访问"
2. 将证书添加到系统信任存储（不推荐）

### 2.6 使用curl测试

```bash
# 跳过证书验证（开发环境）
curl -k https://localhost:8000/health

# 或指定证书
curl --cacert certs/dev-cert.pem https://localhost:8000/health
```

---

## 3. 生产环境配置（真实证书）

### 3.1 获取SSL证书

#### 选项1：Let's Encrypt（免费，推荐）

**使用Certbot自动获取证书**：

```bash
# 安装Certbot
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install certbot

# CentOS/RHEL
sudo yum install certbot

# macOS
brew install certbot

# 获取证书（需要域名和80端口）
sudo certbot certonly --standalone -d yourdomain.com

# 证书位置：
# 证书：/etc/letsencrypt/live/yourdomain.com/fullchain.pem
# 私钥：/etc/letsencrypt/live/yourdomain.com/privkey.pem
```

#### 选项2：购买商业证书

从证书颁发机构购买证书，如：
- DigiCert
- GlobalSign
- Comodo/Sectigo
- GoDaddy

购买后会得到：
- 证书文件（.crt或.pem格式）
- 私钥文件（.key或.pem格式）
- 中间证书（可选）

### 3.2 配置生产环境

编辑`config.prod.yaml`：

```yaml
ssl:
  enabled: true                        # ⚠️ 生产环境必须启用HTTPS
  certfile: "/etc/letsencrypt/live/yourdomain.com/fullchain.pem"  # 真实证书路径
  keyfile: "/etc/letsencrypt/live/yourdomain.com/privkey.pem"     # 真实私钥路径
  ca_certs: null                       # CA证书链（如需要）
  cert_reqs: 0                         # 证书要求
  ssl_version: null                    # 使用TLS 1.2+（推荐）
  ciphers: null                        # 使用安全的默认加密套件
```

### 3.3 证书权限设置

确保证书文件权限正确：

```bash
# 证书文件权限
sudo chmod 644 /etc/letsencrypt/live/yourdomain.com/fullchain.pem

# 私钥文件权限（仅所有者可读）
sudo chmod 600 /etc/letsencrypt/live/yourdomain.com/privkey.pem

# 确保应用有权限读取（如果使用非root用户运行）
sudo chown youruser:youruser /etc/letsencrypt/live/yourdomain.com/*.pem
```

### 3.4 证书自动续期

Let's Encrypt证书有效期为90天，需要定期续期：

```bash
# 测试续期
sudo certbot renew --dry-run

# 配置自动续期（crontab）
sudo crontab -e

# 添加以下行（每天凌晨2点检查续期）
0 2 * * * certbot renew --quiet --post-hook "systemctl restart easy-export"
```

### 3.5 使用Nginx反向代理（推荐）

在生产环境中，推荐使用Nginx作为反向代理处理SSL：

**Nginx配置示例**：

```nginx
server {
    listen 80;
    server_name yourdomain.com;
    
    # HTTP重定向到HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;
    
    # SSL证书配置
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL协议和加密套件
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
    ssl_prefer_server_ciphers on;
    
    # HSTS（强制HTTPS）
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # 反向代理到Easy Export
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

这种方式的优势：
- Nginx专业的SSL/TLS处理
- 更好的性能
- 统一的证书管理
- 更容易配置负载均衡

---

## 4. 高级配置

### 4.1 双向TLS（mTLS）

要求客户端也提供证书：

```yaml
ssl:
  enabled: true
  certfile: "certs/server-cert.pem"
  keyfile: "certs/server-key.pem"
  ca_certs: "certs/ca-cert.pem"        # CA证书用于验证客户端
  cert_reqs: 2                         # 2=CERT_REQUIRED，要求客户端证书
  ssl_version: null
  ciphers: null
```

### 4.2 指定SSL版本

```yaml
ssl:
  enabled: true
  certfile: "certs/cert.pem"
  keyfile: "certs/key.pem"
  ssl_version: 5  # 5=PROTOCOL_TLSv1_2（Python ssl.PROTOCOL_TLSv1_2）
```

**SSL版本常量**：
- `2`: SSLv23 (自动协商，推荐)
- `3`: TLSv1
- `4`: TLSv1_1
- `5`: TLSv1_2 (推荐)
- `6`: TLSv1_3 (最新，推荐)

### 4.3 自定义加密套件

```yaml
ssl:
  enabled: true
  certfile: "certs/cert.pem"
  keyfile: "certs/key.pem"
  ciphers: "ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256"
```

---

## 5. 故障排查

### 5.1 证书文件不存在

**错误**：
```
❌ SSL证书文件不存在: certs/dev-cert.pem
请运行: python script/generate_ssl_cert.py --env dev
```

**解决方案**：
1. 运行证书生成工具
2. 检查配置文件中的证书路径是否正确
3. 使用绝对路径而不是相对路径

### 5.2 证书权限错误

**错误**：
```
PermissionError: [Errno 13] Permission denied: 'certs/dev-key.pem'
```

**解决方案**：
```bash
# 检查文件权限
ls -l certs/

# 修改权限
chmod 600 certs/dev-key.pem
chmod 644 certs/dev-cert.pem

# 检查所有者
chown youruser:youruser certs/*
```

### 5.3 浏览器不信任证书

**现象**：浏览器显示"不安全"或"证书无效"

**解决方案**：
- **开发环境**：这是正常的（自签名证书），点击"继续访问"
- **生产环境**：
  1. 确保使用受信任CA签发的证书
  2. 检查证书是否过期
  3. 检查域名是否匹配
  4. 检查中间证书是否包含

### 5.4 证书过期

**检查证书有效期**：
```bash
# 查看证书信息
openssl x509 -in certs/dev-cert.pem -text -noout | grep "Not After"

# 输出示例：
# Not After : Nov 16 10:00:00 2025 GMT
```

**解决方案**：
- **开发环境**：重新生成证书
- **生产环境**：续期证书（Let's Encrypt自动续期或联系CA）

### 5.5 端口冲突

**错误**：
```
OSError: [Errno 48] Address already in use
```

**解决方案**：
```bash
# 查找占用端口的进程
lsof -i :8000

# 或
netstat -tulnp | grep 8000

# 停止进程
kill -9 <PID>

# 或更改配置中的端口
```

---

## 6. 安全最佳实践

### 6.1 证书管理

- ✅ 使用强私钥（至少2048位RSA或256位ECC）
- ✅ 定期更新证书（建议90天）
- ✅ 保护私钥文件（权限600，不要提交到Git）
- ✅ 使用通配符证书覆盖子域名
- ❌ 不要在多个服务器共享私钥

### 6.2 SSL/TLS配置

- ✅ 仅启用TLS 1.2和TLS 1.3
- ✅ 禁用SSLv2、SSLv3、TLS 1.0、TLS 1.1
- ✅ 使用强加密套件（ECDHE、AES-GCM）
- ✅ 启用HSTS（HTTP Strict Transport Security）
- ✅ 启用OCSP Stapling（如使用Nginx）

### 6.3 生产环境检查清单

- [ ] 使用受信任CA签发的证书
- [ ] 配置自动证书续期
- [ ] 启用HTTPS重定向（HTTP → HTTPS）
- [ ] 配置HSTS头
- [ ] 定期检查证书过期时间
- [ ] 配置证书过期告警
- [ ] 使用安全的SSL/TLS版本
- [ ] 定期更新SSL/TLS配置
- [ ] 配置适当的日志记录
- [ ] 进行SSL/TLS安全测试（如SSL Labs）

---

## 7. 测试和验证

### 7.1 本地测试

```bash
# 使用curl测试
curl -k https://localhost:8000/health

# 使用Python测试
python -c "import requests; print(requests.get('https://localhost:8000/health', verify=False).json())"
```

### 7.2 证书信息查看

```bash
# 查看证书详细信息
openssl x509 -in certs/dev-cert.pem -text -noout

# 验证证书和私钥是否匹配
openssl x509 -noout -modulus -in certs/dev-cert.pem | openssl md5
openssl rsa -noout -modulus -in certs/dev-key.pem | openssl md5
# 两个MD5值应该相同
```

### 7.3 SSL/TLS测试工具

**在线测试（生产环境）**：
- [SSL Labs](https://www.ssllabs.com/ssltest/)：最权威的SSL测试工具
- [SSL Checker](https://www.sslshopper.com/ssl-checker.html)：快速检查证书状态

**命令行测试**：
```bash
# 使用nmap测试SSL
nmap --script ssl-enum-ciphers -p 443 yourdomain.com

# 使用testssl.sh（推荐）
git clone https://github.com/drwetter/testssl.sh.git
cd testssl.sh
./testssl.sh https://yourdomain.com
```

---

## 8. 参考资源

- [Let's Encrypt官方文档](https://letsencrypt.org/docs/)
- [Mozilla SSL Configuration Generator](https://ssl-config.mozilla.org/)
- [Python ssl模块文档](https://docs.python.org/3/library/ssl.html)
- [Uvicorn SSL配置](https://www.uvicorn.org/deployment/#running-with-https)
- [OWASP TLS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Protection_Cheat_Sheet.html)

---

## 9. 常见问题

### Q1: 开发环境必须使用HTTPS吗？

A: 不是必须的。对于纯后端开发，HTTP已经足够。但如果需要测试HTTPS相关功能（如HSTS、Secure Cookie等），则需要启用HTTPS。

### Q2: 自签名证书可以用于生产环境吗？

A: 强烈不推荐。自签名证书会导致浏览器显示安全警告，影响用户体验和信任。生产环境应使用受信任CA签发的证书。

### Q3: 如何强制所有请求使用HTTPS？

A: 在Nginx中配置HTTP到HTTPS的重定向（见3.5节），或在应用中添加中间件检查`X-Forwarded-Proto`头。

### Q4: 证书快过期了怎么办？

A: 
- Let's Encrypt：运行`certbot renew`
- 其他CA：联系CA续期或重新购买
- 推荐配置自动续期和过期告警

### Q5: 性能影响有多大？

A: SSL/TLS加密会有一定性能开销（约1-5%），但在现代硬件上几乎可以忽略。使用Nginx作为反向代理可以优化性能。

---

**文档版本**：v1.0  
**最后更新**：2025-11-16  
**维护者**：开发团队

