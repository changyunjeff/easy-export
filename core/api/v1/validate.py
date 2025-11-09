"""
校验接口
提供文档格式校验功能
"""

from fastapi import APIRouter, Query
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from core.response import HttpResponse, OkWithDetail, ErrorWithDetail
from core.utils import get_api_prefix

validate_router = APIRouter(
    prefix=f"{get_api_prefix()}/validate",
    tags=["validate"],
)


class ValidateRequest(BaseModel):
    """校验请求"""
    file_path: str = Field(..., description="文件路径")
    rules: Optional[Dict[str, Any]] = Field(
        default=None,
        description="校验规则（check_links, check_style, check_table_dimensions等）",
    )


class ValidateResponse(BaseModel):
    """校验响应"""
    file_path: str = Field(..., description="文件路径")
    passed: bool = Field(..., description="是否通过")
    errors: List[Dict[str, Any]] = Field(default_factory=list, description="错误列表")
    warnings: List[Dict[str, Any]] = Field(default_factory=list, description="警告列表")
    summary: Optional[Dict[str, Any]] = Field(default=None, description="汇总信息")


@validate_router.post("", response_model=HttpResponse)
async def validate_document(request: ValidateRequest):
    """
    校验文档
    
    - **file_path**: 文件路径
    - **rules**: 校验规则
      - **check_links**: 是否检查链接有效性
      - **check_style**: 是否检查样式统一性
      - **check_table_dimensions**: 是否检查表格维度
      - **link_timeout_sec**: 链接检查超时时间（秒，默认3）
    """
    raise NotImplementedError("文档校验功能待实现")

