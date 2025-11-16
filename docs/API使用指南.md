# FastExport API 使用指南

## 概述

FastExport 提供完整的 RESTful API 接口，支持文档模板管理、单文档导出、批量导出、格式校验等功能。

## API 文档访问

启动服务后，可以通过以下地址访问 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 快速开始

### 1. 启动服务

```bash
# 开发模式
python main.py

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. 检查服务健康状态

```bash
curl http://localhost:8000/health
```

响应：
```json
{
  "status": "ok"
}
```

## 核心功能使用示例

### 模板管理

#### 1. 上传模板

```bash
curl -X POST "http://localhost:8000/api/v1/templates" \
  -F "file=@template.docx" \
  -F "name=报告模板" \
  -F "description=用于生成分析报告" \
  -F "tags=报告,分析" \
  -F "version=1.0.0"
```

响应：
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "template_id": "tpl_123456",
    "name": "报告模板",
    "version": "1.0.0",
    "format": "docx",
    "file_size": 102400,
    "hash": "sha256:abc123...",
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

#### 2. 查询模板列表

```bash
curl "http://localhost:8000/api/v1/templates?page=1&page_size=20&name=报告"
```

响应：
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "total": 10,
    "page": 1,
    "page_size": 20,
    "items": [
      {
        "template_id": "tpl_123456",
        "name": "报告模板",
        "description": "用于生成分析报告",
        "format": "docx",
        "latest_version": "1.0.0",
        "created_at": "2024-01-01T10:00:00Z",
        "updated_at": "2024-01-01T10:00:00Z"
      }
    ]
  }
}
```

#### 3. 获取模板详情

```bash
curl "http://localhost:8000/api/v1/templates/tpl_123456"
```

#### 4. 下载模板

```bash
curl "http://localhost:8000/api/v1/templates/tpl_123456/download" \
  --output template.docx
```

#### 5. 创建新版本

```bash
curl -X POST "http://localhost:8000/api/v1/templates/tpl_123456/versions" \
  -F "file=@template_v2.docx" \
  -F "version=1.1.0" \
  -F "changelog=优化表格样式"
```

#### 6. 删除模板

```bash
# 删除所有版本
curl -X DELETE "http://localhost:8000/api/v1/templates/tpl_123456"

# 删除指定版本
curl -X DELETE "http://localhost:8000/api/v1/templates/tpl_123456?version=1.0.0"
```

### 文档导出

#### 1. 单文档导出（基础）

```bash
curl -X POST "http://localhost:8000/api/v1/export" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "title": "2024年度报告",
      "author": "张三",
      "date": "2024-01-01",
      "content": "这是报告的主要内容..."
    },
    "template_ref": "tpl_123456",
    "output_format": "docx",
    "output_filename": "report_2024.docx",
    "enable_validation": true
  }'
```

响应：
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "task_id": "task_789012",
    "status": "pending",
    "message": "任务已提交到队列，等待处理"
  }
}
```

#### 2. 导出包含表格的文档

```bash
curl -X POST "http://localhost:8000/api/v1/export" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "title": "销售报告",
      "author": "李四",
      "table:sales": [
        {"product": "产品A", "sales": 1000, "profit": 200},
        {"product": "产品B", "sales": 2000, "profit": 400},
        {"product": "产品C", "sales": 1500, "profit": 300}
      ]
    },
    "template_ref": "tpl_123456",
    "output_format": "pdf",
    "enable_validation": true
  }'
```

#### 3. 导出包含图表的文档

```bash
curl -X POST "http://localhost:8000/api/v1/export" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "title": "年度销售趋势",
      "chart:sales_trend": {
        "type": "line",
        "data": [
          {"month": "1月", "value": 1000},
          {"month": "2月", "value": 1200},
          {"month": "3月", "value": 1500},
          {"month": "4月", "value": 1800}
        ],
        "config": {
          "title": "月度销售额",
          "xlabel": "月份",
          "ylabel": "销售额（元）"
        }
      }
    },
    "template_ref": "tpl_123456",
    "output_format": "pdf"
  }'
```

#### 4. 查询任务状态

```bash
curl "http://localhost:8000/api/v1/export/tasks/task_789012"
```

响应：
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "task_id": "task_789012",
    "status": "completed",
    "progress": 100,
    "file_path": "/outputs/report_2024.docx",
    "file_url": "http://localhost:8000/static/outputs/report_2024.docx",
    "file_size": 204800,
    "pages": 10,
    "report": {
      "elapsed_ms": 3200,
      "memory_peak_mb": 150,
      "validation": {
        "passed": true,
        "errors": [],
        "warnings": []
      }
    },
    "created_at": "2024-01-01T10:00:00Z",
    "completed_at": "2024-01-01T10:00:03Z"
  }
}
```

#### 5. 下载导出文件

```bash
curl "http://localhost:8000/api/v1/export/files/report_2024.docx" \
  --output report.docx
```

### 批量导出

```bash
curl -X POST "http://localhost:8000/api/v1/export/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "items": [
      {
        "data": {"title": "报告1", "author": "张三"},
        "template_ref": "tpl_123456",
        "output_format": "docx",
        "output_filename": "report_1.docx"
      },
      {
        "data": {"title": "报告2", "author": "李四"},
        "template_ref": "tpl_123456",
        "output_format": "pdf",
        "output_filename": "report_2.pdf"
      }
    ],
    "concurrency": 10,
    "enable_validation": true
  }'
```

响应：
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "task_id": "batch_345678",
    "status": "pending",
    "total": 2,
    "message": "批量任务已提交"
  }
}
```

查询批量任务状态：
```bash
curl "http://localhost:8000/api/v1/export/batch/batch_345678"
```

### 文档校验

```bash
curl -X POST "http://localhost:8000/api/v1/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/outputs/report_2024.docx",
    "template_id": "tpl_123456",
    "data": {
      "title": "2024年度报告",
      "author": "张三"
    },
    "rules": {
      "check_required_fields": true,
      "check_table_dimensions": true,
      "check_links": true,
      "check_style": false,
      "link_timeout": 3
    }
  }'
```

响应：
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "passed": true,
    "errors": [],
    "warnings": [
      {
        "type": "link_check",
        "message": "链接响应较慢",
        "detail": "https://example.com 响应时间超过2秒"
      }
    ],
    "summary": {
      "total_checks": 5,
      "passed_checks": 4,
      "failed_checks": 0,
      "warning_checks": 1
    }
  }
}
```

### 统计查询

#### 1. 导出统计

```bash
curl "http://localhost:8000/api/v1/stats/export?start_date=2024-01-01&end_date=2024-01-31"
```

响应：
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "period": {
      "start_date": "2024-01-01",
      "end_date": "2024-01-31"
    },
    "total_tasks": 1000,
    "success_tasks": 980,
    "failed_tasks": 20,
    "success_rate": 0.98,
    "format_distribution": {
      "docx": 600,
      "pdf": 300,
      "html": 80
    }
  }
}
```

#### 2. 性能统计

```bash
curl "http://localhost:8000/api/v1/stats/performance"
```

#### 3. 模板使用统计

```bash
curl "http://localhost:8000/api/v1/stats/templates?limit=10"
```

### 队列监控

#### 1. 队列状态

```bash
curl "http://localhost:8000/api/v1/queue/status"
```

响应：
```json
{
  "code": 0,
  "msg": "success",
  "data": {
    "queue_size": 10,
    "processing": 5,
    "completed": 100,
    "failed": 2,
    "consumer_count": 4
  }
}
```

#### 2. 队列健康检查

```bash
curl "http://localhost:8000/api/v1/queue/health"
```

#### 3. 性能指标

```bash
curl "http://localhost:8000/api/v1/queue/metrics"
```

## 占位符语法

### 文本占位符

```
{{title}}                          # 基础文本
{{date | date('%Y-%m-%d')}}        # 带过滤器
{{author | default('未知')}}        # 默认值
{{content | upper}}                 # 转大写
```

### 表格占位符

```
{{table:sales}}                                            # 基础表格
{{table:sales | columns(['product', 'sales'])}}            # 指定列
{{table:sales | limit(10)}}                                # 限制行数
{{table:sales | sort('sales', 'desc')}}                    # 排序
```

### 图片占位符

```
{{image:logo}}                     # 支持 Base64/URL/本地路径
{{image:avatar | width(100)}}      # 指定宽度
```

### 图表占位符

```
{{chart:sales_line}}               # 折线图
{{chart:sales_bar}}                # 柱状图
{{chart:sales_pie}}                # 饼图
```

## 错误处理

### 错误响应格式

```json
{
  "code": 40001,
  "msg": "数据字段缺失",
  "data": {
    "field": "title",
    "detail": "必填字段 title 缺失"
  },
  "trace_id": "abc123"
}
```

### 常见错误码

| 错误码 | 说明 | 解决方案 |
|--------|------|----------|
| 40001 | 数据字段缺失 | 检查请求数据是否包含必填字段 |
| 40002 | 模板不匹配 | 确认模板ID正确 |
| 40003 | 模板版本不存在 | 检查版本号是否正确 |
| 40401 | 模板不存在 | 确认模板已上传 |
| 40402 | 任务不存在 | 检查任务ID是否正确 |
| 50010 | 渲染失败 | 检查模板和数据格式 |
| 50020 | 存储失败 | 检查磁盘空间 |

## 性能优化建议

### 1. 批量导出

对于大量文档导出，建议使用批量接口并合理设置并发数：

```bash
# 并发数设置为 CPU 核心数的 2 倍
{
  "items": [...],
  "concurrency": 16
}
```

### 2. 图表缓存

相同数据的图表会自动缓存，无需重复生成。

### 3. 模板版本管理

频繁使用的模板建议固定版本号，避免每次查询最新版本。

## 安全建议

### 1. API 访问控制

生产环境建议配置：
- JWT 认证
- 限流策略
- DDoS 防护

### 2. 数据验证

- 使用 `enable_validation` 参数启用数据校验
- 定期检查导出报告中的警告信息

### 3. 敏感数据

- 日志中的敏感数据会自动脱敏
- 建议对敏感文档启用加密功能

## Python SDK 示例

```python
import requests

class FastExportClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.api_prefix = "/api/v1"
    
    def upload_template(self, file_path, name, description=None, tags=None):
        """上传模板"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'name': name,
                'description': description or '',
                'tags': ','.join(tags) if tags else ''
            }
            response = requests.post(
                f"{self.base_url}{self.api_prefix}/templates",
                files=files,
                data=data
            )
            return response.json()
    
    def export_document(self, data, template_ref, output_format='docx'):
        """导出文档"""
        payload = {
            'data': data,
            'template_ref': template_ref,
            'output_format': output_format,
            'enable_validation': True
        }
        response = requests.post(
            f"{self.base_url}{self.api_prefix}/export",
            json=payload
        )
        return response.json()
    
    def get_task_status(self, task_id):
        """查询任务状态"""
        response = requests.get(
            f"{self.base_url}{self.api_prefix}/export/tasks/{task_id}"
        )
        return response.json()

# 使用示例
client = FastExportClient()

# 上传模板
template_result = client.upload_template(
    'template.docx',
    '报告模板',
    tags=['报告', '分析']
)
template_id = template_result['data']['template_id']

# 导出文档
export_result = client.export_document(
    data={
        'title': '2024年度报告',
        'author': '张三',
        'date': '2024-01-01'
    },
    template_ref=template_id,
    output_format='pdf'
)

# 查询状态
task_id = export_result['data']['task_id']
status = client.get_task_status(task_id)
print(f"任务状态: {status['data']['status']}")
```

## 更多资源

- [GitHub 仓库](https://github.com/your-repo)
- [问题反馈](https://github.com/your-repo/issues)
- [变更日志](../CHANGELOG.md)
- [架构设计](../架构设计.md)
- [需求分析](../需求分析.md)

