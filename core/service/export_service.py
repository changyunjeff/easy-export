"""
导出服务模块
负责单文档导出、导出任务管理、导出报告生成
"""

from __future__ import annotations

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

from core.engine import RendererFactory, TemplateEngine
from core.models.export import ExportReport, ExportRequest, ExportResult
from core.models.task import ExportTask
from core.storage import FileStorage

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
        renderer_factory: type[RendererFactory] = RendererFactory,
        default_output_format: str = "html",
    ) -> None:
        self._template_engine = template_engine or TemplateEngine()
        self._file_storage = file_storage or FileStorage()
        self._renderer_factory = renderer_factory
        self._default_output_format = default_output_format
        logger.info("Export service initialized (default_format=%s)", default_output_format)

    async def export_document(
        self,
        request: ExportRequest,
    ) -> ExportResult:
        start = time.perf_counter()
        template_id = self._resolve_template_id(request.template_ref)

        template = self._template_engine.load_template(template_id, request.template_version)
        validation = self._template_engine.validate_template(template)
        if not validation.valid:
            error_msg = "；".join(validation.errors) or "模板校验失败"
            raise ValueError(error_msg)

        target_format = (request.output_format or template.format or self._default_output_format).lower()
        renderer = self._renderer_factory.get_renderer(target_format)
        renderer.ensure_template_supported(template)

        rendered_bytes = await asyncio.to_thread(renderer.render, template, request.data)

        task_id = self._generate_task_id()
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

        logger.info(
            "Export task %s completed (%s, %d bytes)",
            task_id,
            target_format,
            result.file_size,
        )
        return result

    def get_task_status(
        self,
        task_id: str,
    ) -> ExportTask:
        raise NotImplementedError("任务状态查询功能待实现")

    def download_file(
        self,
        file_id: str,
    ) -> bytes:
        return self._file_storage.get_file(file_id)

    def generate_report(
        self,
        task_id: str,
    ) -> dict:
        raise NotImplementedError("导出报告生成功能待实现")

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
