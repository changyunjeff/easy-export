"""
导出数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ExportRequest(BaseModel):
    """导出请求模型"""
    
    data: Dict[str, Any] = Field(
        ..., 
        description="结构化数据",
        examples=[
            {
                "title": "2024年度报告",
                "author": "张三",
                "date": "2024-01-01",
                "content": "这是报告的主要内容...",
                "table:sales": [
                    {"product": "产品A", "sales": 1000, "profit": 200},
                    {"product": "产品B", "sales": 2000, "profit": 400}
                ]
            }
        ]
    )
    template_ref: str = Field(
        ..., 
        description="模板引用（模板ID或路径）",
        examples=["tpl_123456", "/templates/report.docx"]
    )
    template_version: Optional[str] = Field(
        default=None, 
        description="模板版本",
        examples=["1.0.0", "1.2.0"]
    )
    output_format: str = Field(
        default="docx", 
        description="输出格式（docx/pdf/html）",
        examples=["docx", "pdf", "html"]
    )
    output_filename: Optional[str] = Field(
        default=None, 
        description="输出文件名",
        examples=["report_2024.docx", "analysis.pdf"]
    )
    overrides: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="运行时配置覆盖",
        examples=[{"font": "Microsoft YaHei", "page_size": "A4"}]
    )
    enable_validation: bool = Field(
        default=True, 
        description="是否执行格式校验"
    )
    encrypt: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="加密配置",
        examples=[{"enabled": False, "password": ""}]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "data": {
                        "title": "2024年度报告",
                        "author": "张三",
                        "date": "2024-01-01"
                    },
                    "template_ref": "tpl_123456",
                    "output_format": "docx",
                    "output_filename": "report_2024.docx",
                    "enable_validation": True
                },
                {
                    "data": {
                        "title": "销售报告",
                        "table:sales": [
                            {"product": "产品A", "sales": 1000},
                            {"product": "产品B", "sales": 2000}
                        ]
                    },
                    "template_ref": "tpl_123456",
                    "output_format": "pdf",
                    "enable_validation": True
                }
            ]
        }
    }


class ExportResult(BaseModel):
    """导出结果模型"""
    
    task_id: str = Field(..., description="任务ID")
    file_id: str = Field(..., description="文件ID")
    file_path: str = Field(..., description="文件路径")
    file_url: Optional[str] = Field(default=None, description="文件URL")
    file_size: int = Field(..., description="文件大小（字节）")
    pages: int = Field(..., description="页数")
    report: Optional["ExportReport"] = Field(default=None, description="导出报告")
    log_path: Optional[str] = Field(default=None, description="日志路径")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")


class ExportReport(BaseModel):
    """导出报告模型"""
    
    elapsed_ms: int = Field(..., description="生成耗时（毫秒）")
    memory_peak_mb: Optional[float] = Field(default=None, description="内存使用峰值（MB）")
    validation: Optional[Dict[str, Any]] = Field(default=None, description="校验结果")
    errors: List[str] = Field(default_factory=list, description="错误列表")
    warnings: List[str] = Field(default_factory=list, description="警告列表")

