"""
模板管理接口
提供模板上传、查询、删除、版本管理等功能
"""

from fastapi import APIRouter, UploadFile, File, Form, Query, Path as PathParam
from typing import Optional, List
from pydantic import BaseModel, Field

from core.response import HttpResponse, OkWithDetail, ErrorWithDetail
from core.utils import get_api_prefix
from core.service import TemplateService

template_router = APIRouter(
    prefix=f"{get_api_prefix()}/templates",
    tags=["templates"],
)


class TemplateCreateRequest(BaseModel):
    """模板创建请求"""
    name: str = Field(..., description="模板名称")
    description: Optional[str] = Field(default=None, description="模板描述")
    tags: Optional[List[str]] = Field(default=None, description="标签列表")
    version: Optional[str] = Field(default="1.0.0", description="版本号")


class TemplateListResponse(BaseModel):
    """模板列表响应"""
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="页码")
    page_size: int = Field(..., description="每页数量")
    items: List[dict] = Field(..., description="模板列表")


@template_router.post("", response_model=HttpResponse)
async def create_template(
    file: UploadFile = File(..., description="模板文件"),
    name: str = Form(..., description="模板名称"),
    description: Optional[str] = Form(default=None, description="模板描述"),
    tags: Optional[str] = Form(default=None, description="标签（逗号分隔）"),
    version: Optional[str] = Form(default="1.0.0", description="版本号"),
):
    """
    上传模板
    
    - **file**: 模板文件（.docx/.pdf/.html）
    - **name**: 模板名称
    - **description**: 模板描述
    - **tags**: 标签（逗号分隔）
    - **version**: 版本号
    """
    raise NotImplementedError("模板上传功能待实现")


@template_router.get("", response_model=HttpResponse)
async def list_templates(
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
    name: Optional[str] = Query(default=None, description="模板名称（模糊搜索）"),
    tags: Optional[str] = Query(default=None, description="标签（逗号分隔）"),
    format: Optional[str] = Query(default=None, description="模板格式（docx/pdf/html）"),
):
    """
    获取模板列表
    
    - **page**: 页码（默认1）
    - **page_size**: 每页数量（默认20，最大100）
    - **name**: 模板名称（模糊搜索）
    - **tags**: 标签（逗号分隔）
    - **format**: 模板格式（docx/pdf/html）
    """
    raise NotImplementedError("模板列表查询功能待实现")


@template_router.get("/{template_id}", response_model=HttpResponse)
async def get_template(
    template_id: str = PathParam(..., description="模板ID"),
    version: Optional[str] = Query(default=None, description="版本号（可选，不传返回最新版本）"),
):
    """
    获取模板详情
    
    - **template_id**: 模板ID
    - **version**: 版本号（可选，不传返回最新版本）
    """
    raise NotImplementedError("模板详情查询功能待实现")


@template_router.delete("/{template_id}", response_model=HttpResponse)
async def delete_template(
    template_id: str = PathParam(..., description="模板ID"),
    version: Optional[str] = Query(default=None, description="版本号（可选，不传删除所有版本）"),
):
    """
    删除模板
    
    - **template_id**: 模板ID
    - **version**: 版本号（可选，不传删除所有版本）
    """
    raise NotImplementedError("模板删除功能待实现")


@template_router.get("/{template_id}/versions", response_model=HttpResponse)
async def list_versions(
    template_id: str = PathParam(..., description="模板ID"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, description="每页数量"),
):
    """
    获取模板版本列表
    
    - **template_id**: 模板ID
    - **page**: 页码（默认1）
    - **page_size**: 每页数量（默认20）
    """
    raise NotImplementedError("模板版本列表查询功能待实现")


@template_router.post("/{template_id}/versions", response_model=HttpResponse)
async def create_version(
    template_id: str = PathParam(..., description="模板ID"),
    file: UploadFile = File(..., description="模板文件"),
    version: str = Form(..., description="版本号"),
    changelog: Optional[str] = Form(default=None, description="变更日志"),
):
    """
    创建模板版本
    
    - **template_id**: 模板ID
    - **file**: 模板文件
    - **version**: 版本号
    - **changelog**: 变更日志
    """
    raise NotImplementedError("模板版本创建功能待实现")


@template_router.get("/{template_id}/download", response_model=HttpResponse)
async def download_template(
    template_id: str = PathParam(..., description="模板ID"),
    version: Optional[str] = Query(default=None, description="版本号（可选，不传返回最新版本）"),
):
    """
    下载模板
    
    - **template_id**: 模板ID
    - **version**: 版本号（可选，不传返回最新版本）
    
    返回文件流（Content-Type: application/octet-stream）
    """
    raise NotImplementedError("模板下载功能待实现")

