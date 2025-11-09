"""
模板数据模型
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class Template(BaseModel):
    """模板模型"""
    
    template_id: str = Field(..., description="模板ID")
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(default=None, description="模板描述")
    format: str = Field(..., description="模板格式（docx/pdf/html）")
    version: str = Field(..., description="版本号")
    file_size: int = Field(..., description="文件大小（字节）")
    hash: str = Field(..., description="文件哈希值")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: Optional[datetime] = Field(default=None, description="更新时间")
    created_by: Optional[str] = Field(default=None, description="创建者")


class TemplateVersion(BaseModel):
    """模板版本模型"""
    
    template_id: str = Field(..., description="模板ID")
    version: str = Field(..., description="版本号")
    file_size: int = Field(..., description="文件大小（字节）")
    hash: str = Field(..., description="文件哈希值")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    created_by: Optional[str] = Field(default=None, description="创建者")
    changelog: Optional[str] = Field(default=None, description="变更日志")

