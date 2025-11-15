"""
批量处理服务模块
负责批量任务管理、并发控制、任务队列管理
"""

import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from core.models.export import ExportRequest
from core.models.task import BatchTask, TaskStatus, ExportTask
from core.storage import CacheStorage
from core.service.export_service import ExportService

logger = logging.getLogger(__name__)


class BatchService:
    """
    批量处理服务类
    负责批量任务管理、并发控制等
    """
    
    def __init__(
        self,
        cache_storage: Optional[CacheStorage] = None,
        export_service: Optional[ExportService] = None,
    ):
        """
        初始化批量处理服务
        
        Args:
            cache_storage: 缓存存储实例
            export_service: 导出服务实例
        """
        self.cache_storage = cache_storage or CacheStorage()
        self.export_service = export_service or ExportService()
        logger.info("Batch service initialized")
    
    async def create_batch_task(
        self,
        task_ids: List[str],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BatchTask:
        """
        创建批量任务记录
        
        Args:
            task_ids: 子任务ID列表
            metadata: 批量任务元数据（如output_format、concurrency等）
            
        Returns:
            批量任务对象
        """
        try:
            # 生成批量任务ID
            batch_task_id = f"batch_{uuid.uuid4().hex[:16]}"
            
            # 创建批量任务对象
            batch_task = BatchTask(
                task_id=batch_task_id,
                total=len(task_ids),
                success=0,
                failed=0,
                outputs=[],
                status=TaskStatus.PENDING,
                progress=0,
                created_at=datetime.now(),
            )
            
            # 将批量任务信息存储到缓存
            batch_data = {
                "task_id": batch_task_id,
                "sub_task_ids": task_ids,
                "total": len(task_ids),
                "metadata": metadata or {},
                "created_at": batch_task.created_at.isoformat(),
            }
            self.cache_storage.cache_batch_task(batch_task_id, batch_data)
            
            logger.info(f"Batch task created: {batch_task_id} with {len(task_ids)} sub-tasks")
            return batch_task
            
        except Exception as e:
            logger.error(f"Error creating batch task: {str(e)}")
            raise
    
    def get_batch_status(
        self,
        batch_task_id: str,
    ) -> BatchTask:
        """
        查询批量任务状态
        
        Args:
            batch_task_id: 批量任务ID
            
        Returns:
            批量任务状态对象
            
        Raises:
            FileNotFoundError: 批量任务不存在
        """
        try:
            # 从缓存获取批量任务信息
            batch_data = self.cache_storage.get_batch_task(batch_task_id)
            
            if not batch_data:
                raise FileNotFoundError(f"Batch task not found: {batch_task_id}")
            
            # 获取子任务ID列表
            sub_task_ids = batch_data.get("sub_task_ids", [])
            
            # 查询所有子任务状态
            sub_tasks_status = []
            for task_id in sub_task_ids:
                try:
                    task = self.export_service.get_task_status(task_id)
                    sub_tasks_status.append(task)
                except FileNotFoundError:
                    # 任务不存在，可能还未创建
                    logger.warning(f"Sub-task not found: {task_id}")
                    continue
            
            # 计算批量任务状态
            total = len(sub_task_ids)
            success = sum(1 for t in sub_tasks_status if t.status == TaskStatus.COMPLETED)
            failed = sum(1 for t in sub_tasks_status if t.status == TaskStatus.FAILED)
            processing = sum(1 for t in sub_tasks_status if t.status == TaskStatus.PROCESSING)
            
            # 计算进度
            completed = success + failed
            progress = int((completed / total * 100)) if total > 0 else 0
            
            # 确定整体状态
            if failed > 0 and (success + failed) == total:
                # 有失败且所有任务已结束
                status = TaskStatus.FAILED
                completed_at = datetime.now()
            elif completed == total:
                # 所有任务已完成且没有失败
                status = TaskStatus.COMPLETED
                completed_at = datetime.now()
            elif processing > 0 or completed > 0:
                # 有任务正在处理或已完成部分
                status = TaskStatus.PROCESSING
                completed_at = None
            else:
                # 所有任务都在等待
                status = TaskStatus.PENDING
                completed_at = None
            
            # 构建输出列表
            outputs = []
            for task in sub_tasks_status:
                output = {
                    "task_id": task.task_id,
                    "status": task.status.value,
                    "file_path": task.file_path,
                    "file_size": task.file_size,
                    "pages": task.pages,
                }
                if task.status == TaskStatus.FAILED:
                    output["error"] = task.error
                outputs.append(output)
            
            # 计算汇总信息
            summary = self._calculate_summary(sub_tasks_status, batch_data)
            
            # 创建批量任务对象
            created_at_str = batch_data.get("created_at")
            created_at = datetime.fromisoformat(created_at_str) if created_at_str else datetime.now()
            
            batch_task = BatchTask(
                task_id=batch_task_id,
                total=total,
                success=success,
                failed=failed,
                outputs=outputs,
                summary=summary,
                status=status,
                progress=progress,
                created_at=created_at,
                completed_at=completed_at,
            )
            
            logger.info(f"Batch task status retrieved: {batch_task_id} ({progress}% complete)")
            return batch_task
            
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error getting batch status for {batch_task_id}: {str(e)}")
            raise
    
    def _calculate_summary(
        self,
        sub_tasks: List[ExportTask],
        batch_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        计算批量任务汇总信息
        
        Args:
            sub_tasks: 子任务列表
            batch_data: 批量任务数据
            
        Returns:
            汇总信息字典
        """
        try:
            # 统计完成的任务
            completed_tasks = [t for t in sub_tasks if t.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]]
            
            if not completed_tasks:
                return {
                    "elapsed_ms": 0,
                    "avg_elapsed_ms": 0,
                    "total_file_size": 0,
                    "total_pages": 0,
                }
            
            # 计算总耗时（从创建到现在）
            created_at_str = batch_data.get("created_at")
            if created_at_str:
                created_at = datetime.fromisoformat(created_at_str)
                elapsed_ms = int((datetime.now() - created_at).total_seconds() * 1000)
            else:
                elapsed_ms = 0
            
            # 计算平均耗时
            task_count = len(completed_tasks)
            avg_elapsed_ms = elapsed_ms // task_count if task_count > 0 else 0
            
            # 计算总文件大小
            total_file_size = sum(
                t.file_size for t in completed_tasks 
                if t.file_size is not None and t.status == TaskStatus.COMPLETED
            )
            
            # 计算总页数
            total_pages = sum(
                t.pages for t in completed_tasks 
                if t.pages is not None and t.status == TaskStatus.COMPLETED
            )
            
            # 统计格式分布
            format_distribution = {}
            for task in sub_tasks:
                fmt = task.output_format
                format_distribution[fmt] = format_distribution.get(fmt, 0) + 1
            
            return {
                "elapsed_ms": elapsed_ms,
                "avg_elapsed_ms": avg_elapsed_ms,
                "total_file_size": total_file_size,
                "total_pages": total_pages,
                "format_distribution": format_distribution,
            }
            
        except Exception as e:
            logger.error(f"Error calculating summary: {str(e)}")
            return {
                "elapsed_ms": 0,
                "avg_elapsed_ms": 0,
                "total_file_size": 0,
                "total_pages": 0,
            }
    
    async def process_batch(
        self,
        batch_task_id: str,
    ) -> Dict[str, Any]:
        """
        处理批量任务（已通过RocketMQ异步处理，此方法返回状态）
        
        Args:
            batch_task_id: 批量任务ID
            
        Returns:
            批量处理结果
        """
        try:
            # 获取批量任务状态
            batch_task = self.get_batch_status(batch_task_id)
            
            return {
                "task_id": batch_task.task_id,
                "total": batch_task.total,
                "success": batch_task.success,
                "failed": batch_task.failed,
                "status": batch_task.status.value,
                "progress": batch_task.progress,
                "summary": batch_task.summary,
            }
            
        except Exception as e:
            logger.error(f"Error processing batch {batch_task_id}: {str(e)}")
            raise
    
    async def retry_failed_items(
        self,
        batch_task_id: str,
    ) -> Dict[str, Any]:
        """
        重试失败的任务项
        
        Args:
            batch_task_id: 批量任务ID
            
        Returns:
            重试结果
        """
        try:
            # 获取批量任务状态
            batch_task = self.get_batch_status(batch_task_id)
            
            # 获取失败的子任务ID
            batch_data = self.cache_storage.get_batch_task(batch_task_id)
            if not batch_data:
                raise FileNotFoundError(f"Batch task not found: {batch_task_id}")
            
            sub_task_ids = batch_data.get("sub_task_ids", [])
            
            # 查找失败的任务
            failed_task_ids = []
            for task_id in sub_task_ids:
                try:
                    task = self.export_service.get_task_status(task_id)
                    if task.status == TaskStatus.FAILED:
                        failed_task_ids.append(task_id)
                except FileNotFoundError:
                    continue
            
            if not failed_task_ids:
                return {
                    "message": "没有需要重试的失败任务",
                    "retry_count": 0,
                }
            
            # TODO: 实现重试逻辑（需要重新发送任务到队列）
            # 目前返回失败任务列表
            logger.info(f"Found {len(failed_task_ids)} failed tasks in batch {batch_task_id}")
            
            return {
                "message": f"找到 {len(failed_task_ids)} 个失败任务",
                "failed_task_ids": failed_task_ids,
                "retry_count": len(failed_task_ids),
            }
            
        except Exception as e:
            logger.error(f"Error retrying failed items for batch {batch_task_id}: {str(e)}")
            raise

