"""
导出服务模块
负责单文档导出、导出任务管理、导出报告生成
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from uuid import uuid4

from core.engine import RendererFactory, TemplateEngine
from core.models.export import ExportReport, ExportRequest, ExportResult
from core.models.task import ExportTask, TaskStatus
from core.storage import FileStorage, CacheStorage

logger = logging.getLogger(__name__)


class AbstractExportService(ABC):
    """导出服务接口"""

    @abstractmethod
    async def export_document(self, request: ExportRequest) -> ExportResult:
        """执行单文档导出"""

    @abstractmethod
    def get_task_status(self, task_id: str) -> ExportTask:
        """查询任务状态"""

    @abstractmethod
    def download_file(self, file_id: str) -> bytes:
        """下载导出文件"""

    @abstractmethod
    def generate_report(self, task_id: str) -> dict:
        """生成导出报告"""


class ExportService(AbstractExportService):
    """
    导出服务类
    负责单文档导出、导出任务管理等
    """

    def __init__(
        self,
        *,
        template_engine: Optional[TemplateEngine] = None,
        file_storage: Optional[FileStorage] = None,
        cache_storage: Optional[CacheStorage] = None,
        renderer_factory: type[RendererFactory] = RendererFactory,
        default_output_format: str = "html",
    ) -> None:
        self._template_engine = template_engine or TemplateEngine()
        self._file_storage = file_storage or FileStorage()
        self._cache_storage = cache_storage or CacheStorage()
        self._renderer_factory = renderer_factory
        self._default_output_format = default_output_format
        logger.info("Export service initialized (default_format=%s)", default_output_format)

    async def export_document(
        self,
        request: ExportRequest,
    ) -> ExportResult:
        start = time.perf_counter()
        task_id = self._generate_task_id()
        
        # 保存任务状态：pending
        self._save_task_status(
            task_id=task_id,
            status=TaskStatus.PENDING,
            progress=0,
            message="任务已创建，准备处理"
        )
        
        try:
            # 更新任务状态：processing
            self._save_task_status(
                task_id=task_id,
                status=TaskStatus.PROCESSING,
                progress=10,
                message="正在加载模板"
            )
            
            template_id = self._resolve_template_id(request.template_ref)
            template = self._template_engine.load_template(template_id, request.template_version)
            
            # 更新任务状态：validating
            self._save_task_status(
                task_id=task_id,
                status=TaskStatus.PROCESSING,
                progress=30,
                message="正在验证模板"
            )
            
            validation = self._template_engine.validate_template(template)
            if not validation.valid:
                error_msg = "；".join(validation.errors) or "模板校验失败"
                self._save_task_status(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    progress=0,
                    message=error_msg,
                    error=error_msg
                )
                raise ValueError(error_msg)

            # 更新任务状态：rendering
            self._save_task_status(
                task_id=task_id,
                status=TaskStatus.PROCESSING,
                progress=50,
                message="正在渲染文档"
            )
            
            target_format = (request.output_format or template.format or self._default_output_format).lower()
            renderer = self._renderer_factory.get_renderer(target_format)
            renderer.ensure_template_supported(template)
            rendered_bytes = await asyncio.to_thread(renderer.render, template, request.data)

            # 更新任务状态：saving
            self._save_task_status(
                task_id=task_id,
                status=TaskStatus.PROCESSING,
                progress=80,
                message="正在保存文件"
            )
            
            file_id, download_name = self._build_file_identity(
                task_id=task_id,
                target_format=target_format,
                template_id=template.template_id,
                desired_name=request.output_filename,
            )
            file_path = self._file_storage.save_file(file_id, rendered_bytes, filename=download_name)
            file_url = self._file_storage.get_file_url(file_id)

            elapsed_ms = int((time.perf_counter() - start) * 1000)
            report = ExportReport(
                elapsed_ms=elapsed_ms,
                memory_peak_mb=None,
                validation={
                    "warnings": validation.warnings,
                    "placeholder_count": len(template.placeholders or []),
                },
                errors=validation.errors,
                warnings=validation.warnings,
            )

            result = ExportResult(
                task_id=task_id,
                file_id=file_id,
                file_path=file_path,
                file_url=file_url,
                file_size=len(rendered_bytes),
                pages=self._estimate_pages(target_format),
                report=report,
            )

            # 更新任务状态：completed
            self._save_task_status(
                task_id=task_id,
                status=TaskStatus.COMPLETED,
                progress=100,
                message="导出完成",
                file_path=file_path,
                file_url=file_url,
                file_size=len(rendered_bytes)
            )

            logger.info(
                "Export task %s completed (%s, %d bytes)",
                task_id,
                target_format,
                result.file_size,
            )
            return result
            
        except Exception as e:
            # 更新任务状态：failed
            self._save_task_status(
                task_id=task_id,
                status=TaskStatus.FAILED,
                progress=0,
                message=f"导出失败: {str(e)}",
                error=str(e)
            )
            raise

    def get_task_status(
        self,
        task_id: str,
    ) -> ExportTask:
        """
        查询任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            ExportTask: 任务状态对象
            
        Raises:
            FileNotFoundError: 任务不存在
        """
        status_data = self._cache_storage.get_task_status(task_id)
        if not status_data:
            raise FileNotFoundError(f"任务不存在: {task_id}")
        
        return ExportTask(
            task_id=task_id,
            template_id=status_data.get("template_id", ""),
            template_version=status_data.get("template_version"),
            output_format=status_data.get("output_format", ""),
            status=status_data.get("status", TaskStatus.PENDING),
            progress=status_data.get("progress", 0),
            message=status_data.get("message"),
            file_path=status_data.get("file_path"),
            file_url=status_data.get("file_url"),
            file_size=status_data.get("file_size"),
            pages=status_data.get("pages"),
            error=status_data.get("error"),
            created_at=status_data.get("created_at"),
            completed_at=status_data.get("completed_at")
        )

    def download_file(
        self,
        file_id: str,
    ) -> bytes:
        return self._file_storage.get_file(file_id)

    def generate_report(
        self,
        task_id: str,
    ) -> Dict[str, Any]:
        """
        生成导出报告
        
        Args:
            task_id: 任务ID
            
        Returns:
            dict: 导出报告
            
        Raises:
            FileNotFoundError: 任务不存在
        """
        task = self.get_task_status(task_id)
        
        report = {
            "task_id": task_id,
            "status": task.status,
            "progress": task.progress,
            "message": task.message,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        }
        
        if task.status == TaskStatus.COMPLETED:
            report.update({
                "file_path": task.file_path,
                "file_url": task.file_url,
                "file_size": task.file_size,
                "pages": task.pages,
            })
        elif task.status == TaskStatus.FAILED:
            report["error"] = task.error
        
        return report

    @staticmethod
    def _resolve_template_id(template_ref: str) -> str:
        path = Path(template_ref)
        if path.exists():
            raise ValueError("暂不支持通过文件路径直接引用模板，请先上传至模板存储")
        return template_ref

    @staticmethod
    def _generate_task_id() -> str:
        return uuid4().hex

    @staticmethod
    def _estimate_pages(target_format: str) -> int:
        # 对于HTML输出，默认按照单页估算
        if target_format in {"html", "htm"}:
            return 1
        return 1

    def _save_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: int,
        message: str,
        **extra_data
    ) -> bool:
        """
        保存任务状态
        
        Args:
            task_id: 任务ID
            status: 任务状态
            progress: 进度（0-100）
            message: 状态消息
            **extra_data: 额外数据（如 file_path, file_url, error等）
            
        Returns:
            是否保存成功
        """
        now = datetime.now(timezone.utc)
        status_data = {
            "status": status,
            "progress": progress,
            "message": message,
            "updated_at": now.isoformat(),
        }
        
        # 如果是首次创建，设置created_at
        existing = self._cache_storage.get_task_status(task_id)
        if not existing:
            status_data["created_at"] = now.isoformat()
        else:
            status_data["created_at"] = existing.get("created_at", now.isoformat())
        
        # 如果任务完成或失败，设置completed_at
        if status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
            status_data["completed_at"] = now.isoformat()
        
        # 添加额外数据
        status_data.update(extra_data)
        
        # 任务状态缓存5分钟
        return self._cache_storage.cache_task_status(task_id, status_data, ttl=300)

    @staticmethod
    def _build_file_identity(
        *,
        task_id: str,
        target_format: str,
        template_id: str,
        desired_name: Optional[str],
    ) -> Tuple[str, str]:
        extension = target_format.lower()
        file_id = f"{task_id}.{extension}"

        if desired_name:
            download_name = Path(desired_name).name
        else:
            download_name = f"{template_id}_{task_id}.{extension}"

        if not download_name.lower().endswith(f".{extension}"):
            download_name = f"{download_name}.{extension}"

        return file_id, download_name
