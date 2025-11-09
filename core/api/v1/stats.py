"""
统计接口
提供导出统计功能
"""

from fastapi import APIRouter, Query
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field

from core.response import HttpResponse, OkWithDetail, ErrorWithDetail
from core.utils import get_api_prefix

stats_router = APIRouter(
    prefix=f"{get_api_prefix()}/stats",
    tags=["stats"],
)


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


@stats_router.get("/export", response_model=HttpResponse)
async def get_export_stats(
    start_date: Optional[str] = Query(default=None, description="开始日期（YYYY-MM-DD）"),
    end_date: Optional[str] = Query(default=None, description="结束日期（YYYY-MM-DD）"),
    template_id: Optional[str] = Query(default=None, description="模板ID（可选）"),
):
    """
    获取导出统计
    
    - **start_date**: 开始日期（YYYY-MM-DD）
    - **end_date**: 结束日期（YYYY-MM-DD）
    - **template_id**: 模板ID（可选）
    
    返回统计信息：
    - 总任务数、成功率
    - 平均耗时、响应时间
    - 格式分布
    - 模板使用情况
    """
    raise NotImplementedError("导出统计功能待实现")

