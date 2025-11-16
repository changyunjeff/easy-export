"""
API文档配置
为FastAPI应用提供完善的OpenAPI文档配置
"""

from typing import Dict, Any

# OpenAPI文档配置
OPENAPI_CONFIG = {
    "title": "FastExport API",
    "description": """
# 通用内容导出工具集 API

FastExport 是一个强大的文档导出服务，支持将结构化数据（JSON/CSV）转换为多种格式的文档。

## 主要功能

### 📄 模板管理
- 上传和管理 Word/PDF/HTML 模板
- 支持模板版本管理
- 支持占位符定义（文本、表格、图片、图表）

### 🚀 文档导出
- **单文档导出**：快速导出单个文档
- **批量导出**：支持并发批量生成多个文档
- **异步处理**：通过 RocketMQ 队列异步处理，避免阻塞

### ✅ 格式校验
- 数据错位检查
- 链接有效性验证
- 样式统一性检查

### 📊 统计分析
- 导出任务统计
- 性能指标监控
- 模板使用统计

## 快速开始

### 1. 上传模板

```bash
curl -X POST "http://localhost:8000/api/v1/templates" \\
  -F "file=@template.docx" \\
  -F "name=报告模板" \\
  -F "description=用于生成分析报告"
```

### 2. 导出文档

```bash
curl -X POST "http://localhost:8000/api/v1/export" \\
  -H "Content-Type: application/json" \\
  -d '{
    "data": {
      "title": "2024年度报告",
      "author": "张三"
    },
    "template_ref": "tpl_123456",
    "output_format": "docx"
  }'
```

### 3. 查询任务状态

```bash
curl "http://localhost:8000/api/v1/export/tasks/{task_id}"
```

## 技术特性

- ⚡ **高性能**：支持异步处理和批量并发
- 🔒 **安全可靠**：支持限流、DDoS防护、数据脱敏
- 📈 **可扩展**：插件化架构，易于扩展
- 🛠️ **易集成**：RESTful API，标准化接口

## 支持的格式

### 输入
- JSON 数据
- CSV 数据
- Word/PDF/HTML 模板

### 输出
- Word (.docx)
- PDF (.pdf)
- HTML (.html)

## 占位符语法

### 文本占位符
- `{{title}}` - 基础文本
- `{{date | date('%Y-%m-%d')}}` - 带过滤器
- `{{author | default('未知')}}` - 默认值

### 表格占位符
- `{{table:data}}` - 基础表格
- `{{table:data | columns(['name', 'sales'])}}` - 指定列

### 图片占位符
- `{{image:logo}}` - 支持 Base64/URL/本地路径

### 图表占位符
- `{{chart:sales_line}}` - 折线图
- `{{chart:sales_bar}}` - 柱状图
- `{{chart:sales_pie}}` - 饼图

## API 规范

### 请求格式
- Content-Type: `application/json`
- 字符编码: UTF-8
- Base URL: `/api/v1`

### 响应格式
```json
{
  "code": 0,
  "msg": "success",
  "data": {}
}
```

### 错误码
- `0`: 成功
- `4xx`: 客户端错误（参数错误、资源不存在等）
- `5xx`: 服务器错误（渲染失败、存储失败等）

## 更多信息

- 📖 [完整文档](https://github.com/your-repo/docs)
- 🐛 [问题反馈](https://github.com/your-repo/issues)
- 💬 [社区讨论](https://github.com/your-repo/discussions)
    """,
    "version": "0.1.6",
    "terms_of_service": "https://example.com/terms/",
    "contact": {
        "name": "FastExport Team",
        "url": "https://github.com/your-repo",
        "email": "support@example.com"
    },
    "license_info": {
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html"
    }
}

# API标签分组配置
OPENAPI_TAGS = [
    {
        "name": "templates",
        "description": "**模板管理接口** - 模板的上传、查询、删除、版本管理等操作"
    },
    {
        "name": "export",
        "description": "**导出接口** - 单文档导出、批量导出、任务状态查询、文件下载等操作"
    },
    {
        "name": "validate",
        "description": "**校验接口** - 文档格式校验、数据完整性检查等操作"
    },
    {
        "name": "stats",
        "description": "**统计接口** - 导出统计、性能统计、模板使用统计等操作"
    },
    {
        "name": "files",
        "description": "**文件管理接口** - 文件上传、下载、列表、删除等操作"
    },
    {
        "name": "queue",
        "description": "**队列监控接口** - RocketMQ队列状态、性能指标、消费者管理等操作"
    },
    {
        "name": "health",
        "description": "**健康检查接口** - 服务健康状态、存活探针、就绪探针等操作"
    }
]

# OpenAPI配置选项
OPENAPI_OPTIONS = {
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "openapi_url": "/openapi.json",
}

# Swagger UI 配置
SWAGGER_UI_PARAMETERS = {
    "deepLinking": True,
    "displayRequestDuration": True,
    "filter": True,
    "showExtensions": True,
    "showCommonExtensions": True,
    "syntaxHighlight.theme": "monokai",
    "tryItOutEnabled": True,
    "requestSnippetsEnabled": True,
    "defaultModelsExpandDepth": 3,
    "defaultModelExpandDepth": 3,
    "docExpansion": "list",  # "list", "full", "none"
    "persistAuthorization": True,
}


def get_openapi_schema_config() -> Dict[str, Any]:
    """
    获取OpenAPI文档配置
    
    Returns:
        Dict[str, Any]: OpenAPI配置字典
    """
    return {
        **OPENAPI_CONFIG,
        "openapi_tags": OPENAPI_TAGS,
        **OPENAPI_OPTIONS,
        "swagger_ui_parameters": SWAGGER_UI_PARAMETERS,
    }


# 示例数据配置（用于API文档中的示例展示）
API_EXAMPLES = {
    "export_request": {
        "summary": "基础导出示例",
        "description": "导出一个简单的Word文档",
        "value": {
            "data": {
                "title": "2024年度报告",
                "author": "张三",
                "date": "2024-01-01",
                "content": "这是报告的主要内容...",
            },
            "template_ref": "tpl_123456",
            "output_format": "docx",
            "output_filename": "report_2024.docx",
            "validate": True
        }
    },
    "export_request_with_table": {
        "summary": "包含表格的导出示例",
        "description": "导出包含表格数据的文档",
        "value": {
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
            "validate": True
        }
    },
    "export_request_with_chart": {
        "summary": "包含图表的导出示例",
        "description": "导出包含图表的文档",
        "value": {
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
        }
    },
    "batch_export_request": {
        "summary": "批量导出示例",
        "description": "批量导出多个文档",
        "value": {
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
            "enable_validation": True
        }
    },
    "template_create": {
        "summary": "上传模板示例",
        "description": "上传一个Word模板文件",
        "value": {
            "name": "报告模板",
            "description": "用于生成分析报告的模板",
            "tags": "报告,分析",
            "version": "1.0.0"
        }
    },
    "validate_request": {
        "summary": "文档校验示例",
        "description": "校验文档的完整性和正确性",
        "value": {
            "file_path": "/outputs/report_2024.docx",
            "template_id": "tpl_123456",
            "data": {
                "title": "2024年度报告",
                "author": "张三"
            },
            "rules": {
                "check_required_fields": True,
                "check_table_dimensions": True,
                "check_links": True,
                "check_style": False,
                "link_timeout": 3
            }
        }
    }
}


def get_api_examples() -> Dict[str, Any]:
    """
    获取API示例数据
    
    Returns:
        Dict[str, Any]: API示例字典
    """
    return API_EXAMPLES

