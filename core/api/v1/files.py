"""
文件管理API接口
提供文件上传、下载、列表查询、删除等接口
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from core.utils import get_api_prefix
from fastapi import APIRouter, UploadFile, File, Query, HTTPException, status
from fastapi.responses import Response

from core.service.file_service import FileService
from core.response import success_response, error_response

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(f"{get_api_prefix()}/files", tags=["files"])

# 初始化文件服务
file_service = FileService()


@router.post("", summary="上传文件")
async def upload_file(
    file: UploadFile = File(..., description="上传的文件"),
    max_size: int = Query(
        50 * 1024 * 1024,
        description="最大文件大小（字节），默认50MB",
        ge=1,
        le=100 * 1024 * 1024,
    ),
):
    """
    上传文件接口
    
    - **file**: 上传的文件
    - **max_size**: 最大文件大小限制（默认50MB，最大100MB）
    
    返回文件ID、文件路径、文件大小、访问URL等信息
    """
    try:
        result = await file_service.upload_file(file, max_size)
        logger.info("文件上传成功: %s", result.get("file_id"))
        return success_response(data=result, msg="文件上传成功")
    except ValueError as exc:
        logger.warning("文件上传失败（参数错误）: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("文件上传失败: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {exc}",
        )


@router.get("", summary="获取文件列表")
def list_files(
    name: Optional[str] = Query(None, description="文件名筛选（模糊匹配）"),
    extension: Optional[str] = Query(None, description="文件扩展名筛选（如：.pdf）"),
    created_after: Optional[str] = Query(None, description="创建时间筛选（ISO格式）"),
    page: int = Query(1, description="页码", ge=1),
    page_size: int = Query(20, description="每页数量", ge=1, le=100),
):
    """
    获取文件列表接口
    
    支持按文件名、扩展名、创建时间筛选，支持分页
    
    - **name**: 文件名筛选（模糊匹配）
    - **extension**: 文件扩展名筛选（如：.pdf）
    - **created_after**: 创建时间筛选（ISO格式）
    - **page**: 页码
    - **page_size**: 每页数量
    """
    try:
        # 构建筛选条件
        filters = {}
        if name:
            filters["name"] = name
        if extension:
            filters["extension"] = extension
        if created_after:
            filters["created_after"] = created_after
        
        result = file_service.list_files(filters, page, page_size)
        return success_response(data=result)
    except Exception as exc:
        logger.error("获取文件列表失败: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件列表失败: {exc}",
        )


@router.get("/{file_id}", summary="获取文件信息")
def get_file_info(
    file_id: str,
):
    """
    获取文件信息接口
    
    返回文件ID、文件名、文件大小、创建时间、访问URL等信息
    
    - **file_id**: 文件ID
    """
    try:
        result = file_service.get_file_info(file_id)
        return success_response(data=result)
    except FileNotFoundError as exc:
        logger.warning("文件不存在: %s", file_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("获取文件信息失败: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取文件信息失败: {exc}",
        )


@router.get("/{file_id}/download", summary="下载文件")
def download_file(
    file_id: str,
):
    """
    下载文件接口
    
    返回文件内容（字节流）
    
    - **file_id**: 文件ID
    """
    try:
        # 获取文件信息
        file_info = file_service.get_file_info(file_id)
        file_name = file_info.get("file_name", file_id)
        
        # 下载文件
        content = file_service.download_file(file_id)
        
        # 根据文件扩展名设置Content-Type
        content_type = _get_content_type(file_name)
        
        return Response(
            content=content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{file_name}"',
            },
        )
    except FileNotFoundError as exc:
        logger.warning("文件不存在: %s", file_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("下载文件失败: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"下载文件失败: {exc}",
        )


@router.delete("/{file_id}", summary="删除文件")
def delete_file(
    file_id: str,
):
    """
    删除文件接口
    
    删除指定ID的文件及其元数据
    
    - **file_id**: 文件ID
    """
    try:
        result = file_service.delete_file(file_id)
        logger.info("文件已删除: %s", file_id)
        return success_response(
            data={"deleted": result},
            msg="文件删除成功"
        )
    except FileNotFoundError as exc:
        logger.warning("文件不存在: %s", file_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error("删除文件失败: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除文件失败: {exc}",
        )


@router.post("/cleanup", summary="清理过期文件")
def cleanup_old_files(
    days: int = Query(7, description="清理多少天前的文件", ge=1, le=365),
):
    """
    清理过期文件接口
    
    删除早于指定天数的文件及其元数据
    
    - **days**: 清理多少天前的文件（默认7天）
    """
    try:
        # 计算截止时间
        older_than = datetime.now(timezone.utc) - timedelta(days=days)
        
        # 清理文件
        count = file_service.cleanup_old_files(older_than)
        logger.info("已清理 %d 个文件（早于 %d 天）", count, days)
        
        return success_response(
            data={
                "cleaned_count": count,
                "older_than": older_than.isoformat(),
                "days": days,
            },
            msg=f"已清理 {count} 个文件"
        )
    except Exception as exc:
        logger.error("清理文件失败: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清理文件失败: {exc}",
        )


# ------------------------------------------------------------------
# 工具函数
# ------------------------------------------------------------------

def _get_content_type(filename: str) -> str:
    """
    根据文件扩展名获取Content-Type
    
    Args:
        filename: 文件名
        
    Returns:
        Content-Type
    """
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    
    content_types = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "doc": "application/msword",
        "html": "text/html",
        "htm": "text/html",
        "txt": "text/plain",
        "json": "application/json",
        "xml": "application/xml",
        "csv": "text/csv",
        "png": "image/png",
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "gif": "image/gif",
        "webp": "image/webp",
    }
    
    return content_types.get(ext, "application/octet-stream")

