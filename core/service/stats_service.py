"""
统计服务模块
负责导出统计、性能统计、模板使用统计
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.storage.cache_storage import CacheStorage

logger = logging.getLogger(__name__)


class StatsService:
    """
    统计服务类
    负责导出统计、性能统计等
    """
    
    def __init__(self, cache_storage: Optional[CacheStorage] = None):
        """
        初始化统计服务
        
        Args:
            cache_storage: 缓存存储实例，如果为None则创建新实例
        """
        self._cache = cache_storage or CacheStorage()
        logger.info("Stats service initialized")
    
    def record_export_task(
        self,
        task_id: str,
        template_id: str,
        output_format: str,
        file_size: int,
        pages: int,
        elapsed_ms: int,
        success: bool,
    ) -> bool:
        """
        记录导出任务统计数据
        
        Args:
            task_id: 任务ID
            template_id: 模板ID
            output_format: 输出格式
            file_size: 文件大小（字节）
            pages: 页数
            elapsed_ms: 耗时（毫秒）
            success: 是否成功
            
        Returns:
            是否记录成功
        """
        try:
            return self._cache.record_export_task(
                task_id=task_id,
                template_id=template_id,
                output_format=output_format,
                file_size=file_size,
                pages=pages,
                elapsed_ms=elapsed_ms,
                success=success,
            )
        except Exception as e:
            logger.error(f"Failed to record export task: {e}")
            return False
    
    def get_export_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        template_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        获取导出统计
        
        Args:
            start_date: 开始日期（暂不支持过滤）
            end_date: 结束日期（暂不支持过滤）
            template_id: 模板ID（可选，暂不支持过滤）
            
        Returns:
            统计信息（总任务数、成功率、平均耗时等）
        """
        try:
            stats = self._cache.get_export_stats(start_date, end_date)
            
            # 添加时间范围（如果提供）
            period = {}
            if start_date:
                period["start_date"] = start_date.strftime("%Y-%m-%d")
            if end_date:
                period["end_date"] = end_date.strftime("%Y-%m-%d")
            
            # 如果没有提供日期，返回全部数据的周期说明
            if not period:
                period = {
                    "start_date": "N/A",
                    "end_date": "N/A",
                    "note": "全部统计数据（不区分时间范围）"
                }
            
            # 获取模板使用统计
            template_usage = self._cache.get_template_usage_stats(template_id)
            
            result = {
                "period": period,
                **stats,
                "template_usage": template_usage,
            }
            
            logger.info(f"Retrieved export stats: {result['total_tasks']} tasks")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get export stats: {e}")
            return {
                "period": {},
                "total_tasks": 0,
                "success_tasks": 0,
                "failed_tasks": 0,
                "success_rate": 0.0,
                "total_pages": 0,
                "total_file_size": 0,
                "avg_elapsed_ms": 0.0,
                "format_distribution": {},
                "template_usage": [],
            }
    
    def get_performance_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        获取性能统计
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            性能统计信息（平均耗时、响应时间等）
        """
        try:
            # 性能统计复用导出统计的数据
            export_stats = self._cache.get_export_stats(start_date, end_date)
            
            result = {
                "avg_elapsed_ms": export_stats.get("avg_elapsed_ms", 0.0),
                "total_tasks": export_stats.get("total_tasks", 0),
                "total_pages": export_stats.get("total_pages", 0),
                "total_file_size": export_stats.get("total_file_size", 0),
            }
            
            logger.info(f"Retrieved performance stats: avg {result['avg_elapsed_ms']}ms")
            return result
            
        except Exception as e:
            logger.error(f"Failed to get performance stats: {e}")
            return {
                "avg_elapsed_ms": 0.0,
                "total_tasks": 0,
                "total_pages": 0,
                "total_file_size": 0,
            }
    
    def get_template_usage_stats(
        self,
        template_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取模板使用统计
        
        Args:
            template_id: 模板ID（可选）
            
        Returns:
            模板使用统计信息（使用率、使用次数等）
        """
        try:
            template_usage = self._cache.get_template_usage_stats(template_id)
            
            # 如果没有数据，返回空列表
            if not template_usage:
                logger.info("No template usage stats found")
                return []
            
            logger.info(f"Retrieved template usage stats: {len(template_usage)} templates")
            return template_usage
            
        except Exception as e:
            logger.error(f"Failed to get template usage stats: {e}")
            return []
    
    def reset_stats(self) -> bool:
        """
        重置所有统计数据（用于测试）
        
        Returns:
            是否重置成功
        """
        try:
            return self._cache.reset_stats()
        except Exception as e:
            logger.error(f"Failed to reset stats: {e}")
            return False

