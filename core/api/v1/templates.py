"""
模板管理接口
提供模板上传、查询、删除、版本管理等功能
"""

from fastapi import APIRouter, UploadFile, File, Form, Query, Path as PathParam, HTTPException, Response
from typing import Optional, List
from pydantic import BaseModel, Field
import logging

from core.response import HttpResponse, OkWithDetail, ErrorWithDetail
from core.utils import get_api_prefix
from core.service.template_service import TemplateService

logger = logging.getLogger(__name__)

template_router = APIRouter(
    prefix=f"{get_api_prefix()}/templates",
    tags=["templates"],
)

# 初始化模板服务
template_service = TemplateService()


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
    try:
        # 解析标签
        tags_list = [tag.strip() for tag in tags.split(",")] if tags else []
        
        # 构造元数据
        metadata = {
            "name": name,
            "description": description,
            "tags": tags_list,
            "version": version,
        }
        
        # 创建模板
        template = await template_service.create_template(file, metadata)
        
        return OkWithDetail(
            data={
                "template_id": template.template_id,
                "name": template.name,
                "version": template.version,
                "format": template.format,
                "file_size": template.file_size,
                "hash": template.hash,
                "created_at": template.created_at.isoformat(),
                "tags": template.tags,
            },
            msg="模板创建成功"
        )
    except ValueError as e:
        logger.warning("Template creation failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error("Template creation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        raise HTTPException(status_code=500, detail="服务器内部错误")


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
    try:
        # 构造过滤条件
        filters = {}
        if name:
            filters["name"] = name
        if tags:
            filters["tags"] = [tag.strip() for tag in tags.split(",")]
        if format:
            filters["format"] = format
        
        # 查询模板列表
        result = template_service.list_templates(filters, page, page_size)
        
        return OkWithDetail(data=result, msg="查询成功")
    except Exception as e:
        logger.error("Failed to list templates: %s", e)
        raise HTTPException(status_code=500, detail="查询失败")


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
    try:
        template = template_service.get_template(template_id, version)
        
        return OkWithDetail(
            data={
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "format": template.format,
                "version": template.version,
                "file_size": template.file_size,
                "hash": template.hash,
                "tags": template.tags,
                "created_at": template.created_at.isoformat(),
                "updated_at": template.updated_at.isoformat() if template.updated_at else None,
                "created_by": template.created_by,
            },
            msg="查询成功"
        )
    except FileNotFoundError as e:
        logger.warning("Template not found: %s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to get template: %s", e)
        raise HTTPException(status_code=500, detail="查询失败")


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
    try:
        success = template_service.delete_template(template_id, version)
        
        if success:
            return OkWithDetail(
                data={"deleted": True},
                msg=f"删除成功: {template_id}" + (f"@{version}" if version else "（所有版本）")
            )
        else:
            raise HTTPException(status_code=500, detail="删除失败")
    except FileNotFoundError as e:
        logger.warning("Template not found: %s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to delete template: %s", e)
        raise HTTPException(status_code=500, detail="删除失败")


@template_router.get("/{template_id}/versions", response_model=HttpResponse)
async def list_versions(
    template_id: str = PathParam(..., description="模板ID"),
    page: int = Query(default=1, ge=1, description="页码"),
    page_size: int = Query(default=20, ge=1, le=100, description="每页数量"),
):
    """
    获取模板版本列表
    
    - **template_id**: 模板ID
    - **page**: 页码（默认1）
    - **page_size**: 每页数量（默认20，最大100）
    """
    try:
        result = template_service.list_versions(template_id, page, page_size)
        
        return OkWithDetail(data=result, msg="查询成功")
    except FileNotFoundError as e:
        logger.warning("Template not found: %s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to list versions: %s", e)
        raise HTTPException(status_code=500, detail="查询失败")


@template_router.post("/{template_id}/versions", response_model=HttpResponse)
async def create_version(
    template_id: str = PathParam(..., description="模板ID"),
    file: UploadFile = File(..., description="模板文件"),
    version: str = Form(..., description="版本号"),
    changelog: Optional[str] = Form(default=None, description="变更日志"),
):
    """
    创建新版本
    
    - **template_id**: 模板ID
    - **file**: 模板文件（.docx/.pdf/.html）
    - **version**: 版本号
    - **changelog**: 变更日志
    """
    try:
        template_version = await template_service.create_version(
            template_id=template_id,
            file=file,
            version=version,
            changelog=changelog or "",
        )
        
        return OkWithDetail(
            data={
                "template_id": template_version.template_id,
                "version": template_version.version,
                "file_size": template_version.file_size,
                "hash": template_version.hash,
                "created_at": template_version.created_at.isoformat(),
                "changelog": template_version.changelog,
            },
            msg="版本创建成功"
        )
    except FileNotFoundError as e:
        logger.warning("Template not found: %s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        logger.warning("Version creation failed: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error("Version creation failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error("Unexpected error: %s", e)
        raise HTTPException(status_code=500, detail="服务器内部错误")


@template_router.get("/{template_id}/download", response_class=Response)
async def download_template(
    template_id: str = PathParam(..., description="模板ID"),
    version: Optional[str] = Query(default=None, description="版本号（可选，不传下载最新版本）"),
):
    """
    下载模板文件
    
    - **template_id**: 模板ID
    - **version**: 版本号（可选，不传下载最新版本）
    """
    try:
        # 获取模板信息
        template = template_service.get_template(template_id, version)
        
        # 下载文件内容
        file_content = template_service.download_template(template_id, version)
        
        # 设置文件名
        filename = f"{template.name}_{template.version}.{template.format}"
        
        # 设置Content-Type
        content_type = {
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "html": "text/html",
            "htm": "text/html",
        }.get(template.format, "application/octet-stream")
        
        # 返回文件流
        return Response(
            content=file_content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Length": str(len(file_content)),
            }
        )
    except FileNotFoundError as e:
        logger.warning("Template not found: %s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to download template: %s", e)
        raise HTTPException(status_code=500, detail="下载失败")


@template_router.put("/{template_id}", response_model=HttpResponse)
async def update_template(
    template_id: str = PathParam(..., description="模板ID"),
    name: Optional[str] = Form(default=None, description="模板名称"),
    description: Optional[str] = Form(default=None, description="模板描述"),
    tags: Optional[str] = Form(default=None, description="标签（逗号分隔）"),
):
    """
    更新模板元数据
    
    - **template_id**: 模板ID
    - **name**: 模板名称
    - **description**: 模板描述
    - **tags**: 标签（逗号分隔）
    """
    try:
        # 构造更新数据
        metadata = {}
        if name:
            metadata["name"] = name
        if description:
            metadata["description"] = description
        if tags:
            metadata["tags"] = [tag.strip() for tag in tags.split(",")]
        
        if not metadata:
            raise HTTPException(status_code=400, detail="至少提供一个要更新的字段")
        
        # 更新模板
        template = template_service.update_template(template_id, metadata)
        
        return OkWithDetail(
            data={
                "template_id": template.template_id,
                "name": template.name,
                "description": template.description,
                "tags": template.tags,
                "updated_at": template.updated_at.isoformat() if template.updated_at else None,
            },
            msg="更新成功"
        )
    except FileNotFoundError as e:
        logger.warning("Template not found: %s", e)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Failed to update template: %s", e)
        raise HTTPException(status_code=500, detail="更新失败")
