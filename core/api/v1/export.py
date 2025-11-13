"""
导出接口
提供单文档导出、批量导出、任务状态查询、文件下载等功能
"""

from fastapi import APIRouter, Query, Path as PathParam, HTTPException
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import logging

from core.response import HttpResponse, OkWithDetail, ErrorWithDetail, success_response, error_response
from core.utils import get_api_prefix
from core.models.export import ExportRequest
from core.rocketmq import get_rocketmq_manager, RocketMQException

logger = logging.getLogger(__name__)

export_router = APIRouter(
    prefix=f"{get_api_prefix()}/export",
    tags=["export"],
)


class ExportResponse(BaseModel):
    """导出响应"""
    task_id: str = Field(..., description="任务ID")
    file_path: str = Field(..., description="文件路径")
    file_url: Optional[str] = Field(default=None, description="文件URL")
    file_size: int = Field(..., description="文件大小（字节）")
    pages: int = Field(..., description="页数")
    report: Optional[Dict[str, Any]] = Field(default=None, description="导出报告")
    created_at: str = Field(..., description="创建时间")


class BatchExportItem(BaseModel):
    """批量导出项"""
    data: Dict[str, Any] = Field(..., description="结构化数据")
    template_ref: str = Field(..., description="模板引用")
    output_format: Optional[str] = Field(default=None, description="输出格式")
    output_filename: Optional[str] = Field(default=None, description="输出文件名")


class BatchExportRequest(BaseModel):
    """批量导出请求"""
    items: List[BatchExportItem] = Field(..., description="导出项列表（最多1000项）")
    output_format: Optional[str] = Field(default="docx", description="默认输出格式")
    concurrency: Optional[int] = Field(default=8, ge=1, le=50, description="并发数（默认8，最大50）")
    enable_validation: Optional[bool] = Field(default=True, description="是否执行格式校验")


@export_router.post("", response_model=HttpResponse)
async def export_document(request: ExportRequest):
    """
    单文档导出（异步处理）

    将导出任务发送到RocketMQ队列进行异步处理，确保服务器能够逐个处理转换请求，
    避免批量请求导致的服务器过载问题。

    - **data**: 结构化数据（必填）
    - **template_ref**: 模板引用（模板ID或路径，必填）
    - **template_version**: 模板版本（可选，不传使用最新版本）
    - **output_format**: 输出格式（docx/pdf/html，默认docx）
    - **output_filename**: 输出文件名（可选，不传自动生成）
    - **overrides**: 运行时配置覆盖（可选）
    - **validate**: 是否执行格式校验（默认true）
    - **encrypt**: 加密配置（可选）
    """
    try:
        # 获取RocketMQ管理器
        mq_manager = get_rocketmq_manager()

        # 发送任务到队列
        task_id = mq_manager.send_export_task(
            template_id=request.template_ref,  # 使用template_ref作为template_id
            data=request.data,
            output_format=request.output_format or "docx",
            priority=0  # 默认优先级
        )

        logger.info(f"Export task submitted to queue: {task_id}")

        return success_response(
            data={
                "task_id": task_id,
                "output_format": request.output_format or "docx",
                "template_ref": request.template_ref,
            },
            message="导出任务已提交到队列，将异步处理"
        )

    except RocketMQException as e:
        logger.error(f"RocketMQ error in export_document: {str(e)}")
        return error_response(
            message=f"RocketMQ错误: {str(e)}",
            error_code="ROCKETMQ_ERROR"
        )

    except Exception as e:
        logger.error(f"Error in export_document: {str(e)}")
        return error_response(
            message=f"提交导出任务失败: {str(e)}",
            error_code="EXPORT_SUBMIT_FAILED"
        )


@export_router.post("/batch", response_model=HttpResponse)
async def batch_export(request: BatchExportRequest):
    """
    批量导出（异步处理）

    将批量导出任务发送到RocketMQ队列进行异步处理，支持并发处理多个导出任务。

    - **items**: 导出项列表（必填，最多1000项）
    - **output_format**: 默认输出格式（可选，可被items中的配置覆盖）
    - **concurrency**: 并发数（可选，默认8，最大50）
    - **validate**: 是否执行格式校验（默认true）
    """
    try:
        # 验证批量导出参数
        if not request.items:
            return error_response(
                message="导出项列表不能为空",
                error_code="EMPTY_BATCH_ITEMS"
            )

        if len(request.items) > 1000:
            return error_response(
                message="批量导出项不能超过1000个",
                error_code="TOO_MANY_BATCH_ITEMS"
            )

        # 获取RocketMQ管理器
        mq_manager = get_rocketmq_manager()

        # 准备批量数据
        batch_data = []
        for item in request.items:
            batch_data.append({
                "template_id": item.template_ref,  # 使用template_ref作为template_id
                "data": item.data,
                "output_format": item.output_format or request.output_format or "docx",
                "output_filename": item.output_filename,
                "priority": 0  # 默认优先级，可根据需求调整
            })

        # 发送批量任务到队列
        task_ids = mq_manager.send_batch_export_tasks(
            template_id="batch_template",  # 批量任务的统一模板ID
            data_list=batch_data,
            output_format=request.output_format or "docx",
            priority=0
        )

        logger.info(f"Batch export tasks submitted to queue: {len(task_ids)} tasks")

        return success_response(
            data={
                "task_ids": task_ids,
                "total_tasks": len(task_ids),
                "output_format": request.output_format or "docx",
                "concurrency": request.concurrency,
                "enable_validation": request.enable_validation
            },
            message=f"批量导出任务已提交到队列，将异步处理 {len(task_ids)} 个任务"
        )

    except RocketMQException as e:
        logger.error(f"RocketMQ error in batch_export: {str(e)}")
        return error_response(
            message=f"RocketMQ错误: {str(e)}",
            error_code="ROCKETMQ_ERROR"
        )

    except Exception as e:
        logger.error(f"Error in batch_export: {str(e)}")
        return error_response(
            message=f"提交批量导出任务失败: {str(e)}",
            error_code="BATCH_EXPORT_SUBMIT_FAILED"
        )


@export_router.get("/tasks/{task_id}", response_model=HttpResponse)
async def get_task_status(
    task_id: str = PathParam(..., description="任务ID"),
):
    """
    查询导出任务状态

    - **task_id**: 任务ID

    任务状态：
    - **pending**: 等待处理
    - **processing**: 处理中
    - **completed**: 已完成
    - **failed**: 失败
    """
    try:
        # TODO: 实现任务状态查询逻辑
        # 这里应该从Redis或其他存储中查询任务状态
        # 目前返回模拟状态

        # 检查RocketMQ队列状态
        mq_manager = get_rocketmq_manager()
        queue_status = mq_manager.get_queue_status()

        # 模拟任务状态查询
        # 在实际实现中，应该有专门的任务状态存储
        task_status = {
            "task_id": task_id,
            "status": "pending",  # pending, processing, completed, failed
            "progress": 0,
            "message": "任务已提交到队列，等待处理",
            "queue_info": {
                "total_lag": queue_status.get("metrics", {}).get("total_lag", 0),
                "is_healthy": queue_status.get("health", {}).get("healthy", False)
            },
            "created_at": None,  # 应该从存储中获取
            "updated_at": None   # 应该从存储中获取
        }

        return success_response(
            data=task_status,
            message="获取任务状态成功"
        )

    except Exception as e:
        logger.error(f"Error getting task status for {task_id}: {str(e)}")
        return error_response(
            message=f"获取任务状态失败: {str(e)}",
            error_code="TASK_STATUS_QUERY_FAILED"
        )


@export_router.get("/files/{file_id}")
async def download_file(
    file_id: str = PathParam(..., description="文件ID"),
    download: bool = Query(default=False, description="是否直接下载（默认false，返回文件流）"),
):
    """
    下载导出文件

    - **file_id**: 文件ID（可从导出响应中获取）
    - **download**: 是否直接下载（默认false，返回文件流）

    返回文件流（Content-Type根据文件类型）
    """
    try:
        # TODO: 实现文件下载逻辑
        # 这里应该从文件存储中获取文件
        # 目前返回未实现的错误

        return error_response(
            message="文件下载功能暂未实现，请稍后查看任务状态获取文件信息",
            error_code="FILE_DOWNLOAD_NOT_IMPLEMENTED"
        )

    except Exception as e:
        logger.error(f"Error downloading file {file_id}: {str(e)}")
        return error_response(
            message=f"文件下载失败: {str(e)}",
            error_code="FILE_DOWNLOAD_FAILED"
        )

