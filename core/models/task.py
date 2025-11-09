"""
任务数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportTask(BaseModel):
    """导出任务模型"""
    
    task_id: str = Field(..., description="任务ID")
    template_id: str = Field(..., description="模板ID")
    template_version: Optional[str] = Field(default=None, description="模板版本")
    output_format: str = Field(..., description="输出格式（docx/pdf/html）")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    progress: int = Field(default=0, ge=0, le=100, description="进度（0-100）")
    file_path: Optional[str] = Field(default=None, description="文件路径")
    file_size: Optional[int] = Field(default=None, description="文件大小（字节）")
    pages: Optional[int] = Field(default=None, description="页数")
    report: Optional[Dict[str, Any]] = Field(default=None, description="导出报告")
    error: Optional[Dict[str, Any]] = Field(default=None, description="错误信息")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")


class BatchTask(BaseModel):
    """批量任务模型"""
    
    task_id: str = Field(..., description="任务ID")
    total: int = Field(..., description="总任务数")
    success: int = Field(default=0, description="成功数")
    failed: int = Field(default=0, description="失败数")
    outputs: List[Dict[str, Any]] = Field(default_factory=list, description="输出列表")
    summary: Optional[Dict[str, Any]] = Field(default=None, description="汇总信息")
    status: TaskStatus = Field(default=TaskStatus.PENDING, description="任务状态")
    progress: int = Field(default=0, ge=0, le=100, description="进度（0-100）")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    completed_at: Optional[datetime] = Field(default=None, description="完成时间")

