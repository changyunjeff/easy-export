"""
统计接口
提供导出统计功能
"""

from fastapi import APIRouter, Query
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field
from datetime import datetime

from core.response import HttpResponse, OkWithDetail, ErrorWithDetail
from core.utils import get_api_prefix
from core.service.stats_service import StatsService

stats_router = APIRouter(
    prefix=f"{get_api_prefix()}/stats",
    tags=["stats"],
)

# 初始化统计服务
stats_service = StatsService()


class StatsResponse(BaseModel):
    """统计响应"""
    period: Dict[str, str] = Field(..., description="统计周期（start_date, end_date）")
    total_tasks: int = Field(..., description="总任务数")
    success_tasks: int = Field(..., description="成功任务数")
    failed_tasks: int = Field(..., description="失败任务数")
    success_rate: float = Field(..., description="成功率")
    total_pages: int = Field(..., description="总页数")
    total_file_size: int = Field(..., description="总文件大小（字节）")
    avg_elapsed_ms: float = Field(..., description="平均耗时（毫秒）")
    format_distribution: Dict[str, int] = Field(..., description="格式分布")
    template_usage: List[Dict[str, Any]] = Field(..., description="模板使用情况")


class PerformanceStatsResponse(BaseModel):
    """性能统计响应"""
    avg_elapsed_ms: float = Field(..., description="平均耗时（毫秒）")
    total_tasks: int = Field(..., description="总任务数")
    total_pages: int = Field(..., description="总页数")
    total_file_size: int = Field(..., description="总文件大小（字节）")


class TemplateUsageResponse(BaseModel):
    """模板使用统计响应"""
    template_id: str = Field(..., description="模板ID")
    template_name: str = Field(..., description="模板名称")
    usage_count: int = Field(..., description="使用次数")


@stats_router.get("/export", response_model=HttpResponse)
async def get_export_stats(
    start_date: Optional[str] = Query(default=None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(default=None, description="结束日期（YYYY-MM-DD）"),
    template_id: Optional[str] = Query(default=None, description="模板ID（可选）"),
):
    """
    获取导出统计
    
    - **start_date**: 开始日期（YYYY-MM-DD，暂不支持过滤）
    - **end_date**: 结束日期（YYYY-MM-DD，暂不支持过滤）
    - **template_id**: 模板ID（可选，暂不支持过滤）
    
    返回统计信息：
    - 总任务数、成功率
    - 平均耗时、响应时间
    - 格式分布
    - 模板使用情况
    """
    try:
        # 解析日期（如果提供）
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                return ErrorWithDetail(
                    msg="Invalid start_date format",
                    code=400,
                    data={"detail": "start_date must be in YYYY-MM-DD format"}
                )
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                return ErrorWithDetail(
                    msg="Invalid end_date format",
                    code=400,
                    data={"detail": "end_date must be in YYYY-MM-DD format"}
                )
        
        # 获取统计数据
        stats = stats_service.get_export_stats(
            start_date=start_dt,
            end_date=end_dt,
            template_id=template_id,
        )
        
        return OkWithDetail(msg="获取导出统计成功", data=stats)
        
    except Exception as e:
        return ErrorWithDetail(
            msg="Failed to get export stats",
            code=500,
            data={"error": str(e)}
        )


@stats_router.get("/performance", response_model=HttpResponse)
async def get_performance_stats(
    start_date: Optional[str] = Query(default=None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(default=None, description="结束日期（YYYY-MM-DD）"),
):
    """
    获取性能统计
    
    - **start_date**: 开始日期（YYYY-MM-DD，暂不支持过滤）
    - **end_date**: 结束日期（YYYY-MM-DD，暂不支持过滤）
    
    返回性能统计信息：
    - 平均耗时
    - 总任务数
    - 总页数
    - 总文件大小
    """
    try:
        # 解析日期（如果提供）
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                return ErrorWithDetail(
                    msg="Invalid start_date format",
                    code=400,
                    data={"detail": "start_date must be in YYYY-MM-DD format"}
                )
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            except ValueError:
                return ErrorWithDetail(
                    msg="Invalid end_date format",
                    code=400,
                    data={"detail": "end_date must be in YYYY-MM-DD format"}
                )
        
        # 获取性能统计
        stats = stats_service.get_performance_stats(
            start_date=start_dt,
            end_date=end_dt,
        )
        
        return OkWithDetail(msg="获取性能统计成功", data=stats)
        
    except Exception as e:
        return ErrorWithDetail(
            msg="Failed to get performance stats",
            code=500,
            data={"error": str(e)}
        )


@stats_router.get("/templates", response_model=HttpResponse)
async def get_template_usage_stats(
    template_id: Optional[str] = Query(default=None, description="模板ID（可选）"),
):
    """
    获取模板使用统计
    
    - **template_id**: 模板ID（可选，不传则返回所有模板统计）
    
    返回模板使用统计信息：
    - 模板ID
    - 模板名称
    - 使用次数
    """
    try:
        # 获取模板使用统计
        stats = stats_service.get_template_usage_stats(template_id=template_id)
        
        return OkWithDetail(
            msg="获取模板使用统计成功",
            data={"templates": stats, "total": len(stats)}
        )
        
    except Exception as e:
        return ErrorWithDetail(
            msg="Failed to get template usage stats",
            code=500,
            data={"error": str(e)}
        )

