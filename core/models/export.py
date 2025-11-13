"""
导出数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class ExportRequest(BaseModel):
    """导出请求模型"""
    
    data: Dict[str, Any] = Field(..., description="结构化数据")
    template_ref: str = Field(..., description="模板引用（模板ID或路径）")
    template_version: Optional[str] = Field(default=None, description="模板版本")
    output_format: str = Field(default="docx", description="输出格式（docx/pdf/html）")
    output_filename: Optional[str] = Field(default=None, description="输出文件名")
    overrides: Optional[Dict[str, Any]] = Field(default=None, description="运行时配置覆盖")
    enable_validation: bool = Field(default=True, description="是否执行格式校验")
    encrypt: Optional[Dict[str, Any]] = Field(default=None, description="加密配置")


class ExportResult(BaseModel):
    """导出结果模型"""
    
    task_id: str = Field(..., description="任务ID")
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

