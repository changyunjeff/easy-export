"""
缓存存储模块
负责图表缓存、模板元数据缓存、任务状态缓存等功能
"""

from __future__ import annotations

import base64
import binascii
import logging
from copy import deepcopy
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Union, List

from core.redis import RedisClient, get_redis_client

logger = logging.getLogger(__name__)


class CacheStorage:
    """
    缓存存储类
    负责图表缓存、模板元数据缓存、任务状态缓存等
    """

    CHART_PREFIX = "chart:"
    TEMPLATE_METADATA_PREFIX = "template:metadata:"
    TASK_STATUS_PREFIX = "task:status:"
    BATCH_TASK_PREFIX = "batch:task:"
    STATS_PREFIX = "stats:"
    STATS_COUNTER_KEY = "stats:counters"
    STATS_TEMPLATE_USAGE_PREFIX = "stats:template:"

    def __init__(self, redis_client: Optional[RedisClient] = None):
        """
        初始化缓存存储

        Args:
            redis_client: Redis客户端实例，如果为 None 则使用全局客户端
        """
        self._client = redis_client or RedisClient(get_redis_client())
        logger.info("Cache storage initialized")

    # ==================== 图表缓存 ====================

    def cache_chart(
        self,
        data_hash: str,
        chart: Union[bytes, bytearray, memoryview],
        ttl: Union[int, float, timedelta] = 3600,
    ) -> bool:
        """
        缓存图表

        Args:
            data_hash: 数据哈希值
            chart: 图表内容（字节）
            ttl: 缓存过期时间（秒或 timedelta），默认1小时

        Returns:
            是否缓存成功
        """
        key = self._chart_key(data_hash)
        data = self._ensure_bytes(chart)
        payload = {
            "content": self._encode_bytes(data),
            "size": len(data),
            "cached_at": self._utcnow(),
        }
        ttl_seconds = self._normalize_ttl(ttl)
        return bool(self._client.set(key, payload, ex=ttl_seconds))

    def get_cached_chart(self, data_hash: str) -> Optional[bytes]:
        """
        获取缓存的图表

        Args:
            data_hash: 数据哈希值

        Returns:
            图表内容（字节），如果不存在则返回 None
        """
        key = self._chart_key(data_hash)
        cached = self._client.get(key)
        if cached is None:
            return None

        encoded = None
        if isinstance(cached, dict):
            encoded = cached.get("content")
        elif isinstance(cached, str):
            encoded = cached

        if not encoded:
            logger.debug("Cache miss for chart %s (content missing)", key)
            return None

        try:
            return self._decode_bytes(encoded)
        except (binascii.Error, ValueError) as exc:
            logger.warning("图表缓存内容损坏，自动清理: %s (%s)", key, exc)
            self._client.delete(key)
            return None

    def delete_cached_chart(self, data_hash: str) -> bool:
        """
        删除缓存的图表

        Args:
            data_hash: 数据哈希值

        Returns:
            是否删除成功
        """
        key = self._chart_key(data_hash)
        return self._client.delete(key) > 0

    # ==================== 模板元数据缓存 ====================

    def cache_template_metadata(
        self,
        template_id: str,
        metadata: Dict[str, Any],
        ttl: Union[int, float, timedelta] = 1800,
    ) -> bool:
        """
        缓存模板元数据

        Args:
            template_id: 模板ID
            metadata: 模板元数据（字典）
            ttl: 缓存过期时间（秒或 timedelta），默认30分钟

        Returns:
            是否缓存成功
        """
        if not isinstance(metadata, dict):
            raise ValueError("metadata 必须是字典")

        key = self._template_key(template_id)
        payload = {
            "metadata": deepcopy(metadata),
            "cached_at": self._utcnow(),
        }
        ttl_seconds = self._normalize_ttl(ttl)
        return bool(self._client.set(key, payload, ex=ttl_seconds))

    def get_template_metadata(
        self,
        template_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存的模板元数据

        Args:
            template_id: 模板ID

        Returns:
            模板元数据（字典），如果不存在则返回 None
        """
        key = self._template_key(template_id)
        cached = self._client.get(key)
        if cached is None:
            return None

        if isinstance(cached, dict):
            metadata = cached.get("metadata", cached)
            return deepcopy(metadata)

        logger.debug("Template metadata cache entry is not a dict: %s", key)
        return None

    def delete_template_metadata(self, template_id: str) -> bool:
        """
        删除缓存的模板元数据

        Args:
            template_id: 模板ID

        Returns:
            是否删除成功
        """
        key = self._template_key(template_id)
        return self._client.delete(key) > 0

    # ==================== 任务状态缓存 ====================

    def cache_task_status(
        self,
        task_id: str,
        status: Dict[str, Any],
        ttl: Union[int, float, timedelta] = 300,
    ) -> bool:
        """
        缓存任务状态

        Args:
            task_id: 任务ID
            status: 任务状态（字典）
            ttl: 缓存过期时间（秒或 timedelta），默认5分钟

        Returns:
            是否缓存成功
        """
        if not isinstance(status, dict):
            raise ValueError("status 必须是字典")

        key = self._task_key(task_id)
        payload = {
            "status": deepcopy(status),
            "cached_at": self._utcnow(),
        }
        ttl_seconds = self._normalize_ttl(ttl)
        return bool(self._client.set(key, payload, ex=ttl_seconds))

    def get_task_status(
        self,
        task_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存的任务状态

        Args:
            task_id: 任务ID

        Returns:
            任务状态（字典），如果不存在则返回 None
        """
        key = self._task_key(task_id)
        cached = self._client.get(key)
        if cached is None:
            return None

        if isinstance(cached, dict):
            status = cached.get("status", cached)
            return deepcopy(status)

        logger.debug("Task status cache entry is not a dict: %s", key)
        return None

    def delete_task_status(self, task_id: str) -> bool:
        """
        删除缓存的任务状态

        Args:
            task_id: 任务ID

        Returns:
            是否删除成功
        """
        key = self._task_key(task_id)
        return self._client.delete(key) > 0

    # ==================== 批量任务缓存 ====================

    def cache_batch_task(
        self,
        batch_task_id: str,
        batch_data: Dict[str, Any],
        ttl: Union[int, float, timedelta] = 3600,
    ) -> bool:
        """
        缓存批量任务信息

        Args:
            batch_task_id: 批量任务ID
            batch_data: 批量任务数据（字典）
            ttl: 缓存过期时间（秒或 timedelta），默认1小时

        Returns:
            是否缓存成功
        """
        if not isinstance(batch_data, dict):
            raise ValueError("batch_data 必须是字典")

        key = self._batch_task_key(batch_task_id)
        payload = {
            "batch_data": deepcopy(batch_data),
            "cached_at": self._utcnow(),
        }
        ttl_seconds = self._normalize_ttl(ttl)
        return bool(self._client.set(key, payload, ex=ttl_seconds))

    def get_batch_task(
        self,
        batch_task_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        获取缓存的批量任务信息

        Args:
            batch_task_id: 批量任务ID

        Returns:
            批量任务数据（字典），如果不存在则返回 None
        """
        key = self._batch_task_key(batch_task_id)
        cached = self._client.get(key)
        if cached is None:
            return None

        if isinstance(cached, dict):
            batch_data = cached.get("batch_data", cached)
            return deepcopy(batch_data)

        logger.debug("Batch task cache entry is not a dict: %s", key)
        return None

    def delete_batch_task(self, batch_task_id: str) -> bool:
        """
        删除缓存的批量任务信息

        Args:
            batch_task_id: 批量任务ID

        Returns:
            是否删除成功
        """
        key = self._batch_task_key(batch_task_id)
        return self._client.delete(key) > 0

    # ==================== 工具方法 ====================

    def _chart_key(self, data_hash: str) -> str:
        value = self._ensure_identifier(data_hash, "data_hash")
        return f"{self.CHART_PREFIX}{value}"

    def _template_key(self, template_id: str) -> str:
        value = self._ensure_identifier(template_id, "template_id")
        return f"{self.TEMPLATE_METADATA_PREFIX}{value}"

    def _task_key(self, task_id: str) -> str:
        value = self._ensure_identifier(task_id, "task_id")
        return f"{self.TASK_STATUS_PREFIX}{value}"

    def _batch_task_key(self, batch_task_id: str) -> str:
        value = self._ensure_identifier(batch_task_id, "batch_task_id")
        return f"{self.BATCH_TASK_PREFIX}{value}"

    def _ensure_identifier(self, value: str, field_name: str) -> str:
        if not value or not isinstance(value, str):
            raise ValueError(f"{field_name} 不能为空")
        trimmed = value.strip()
        if not trimmed:
            raise ValueError(f"{field_name} 不能为空")
        return trimmed

    def _ensure_bytes(self, data: Union[bytes, bytearray, memoryview]) -> bytes:
        if isinstance(data, bytes):
            result = data
        elif isinstance(data, bytearray):
            result = bytes(data)
        elif isinstance(data, memoryview):
            result = data.tobytes()
        else:
            raise ValueError("chart 必须是 bytes/bytearray/memoryview 类型")

        if not result:
            raise ValueError("chart 内容不能为空")
        return result

    def _encode_bytes(self, data: bytes) -> str:
        return base64.b64encode(data).decode("ascii")

    def _decode_bytes(self, payload: Union[str, bytes]) -> bytes:
        if isinstance(payload, str):
            payload = payload.encode("ascii")
        return base64.b64decode(payload)

    def _normalize_ttl(self, ttl: Union[int, float, timedelta, None]) -> Optional[int]:
        if ttl is None:
            return None
        if isinstance(ttl, timedelta):
            seconds = int(ttl.total_seconds())
        else:
            try:
                seconds = int(ttl)
            except (TypeError, ValueError) as exc:
                raise ValueError("ttl 必须是整数或 timedelta") from exc
        if seconds <= 0:
            raise ValueError("ttl 必须大于 0 秒")
        return seconds

    def _utcnow(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    # ==================== 统计数据 ====================

    def record_export_task(
        self,
        task_id: str,
        template_id: str,
        output_format: str,
        file_size: int,
        pages: int,
        elapsed_ms: int,
        success: bool,
        ttl: Union[int, float, timedelta] = 2592000,  # 30天
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
            ttl: 数据保留时间（秒或 timedelta），默认30天

        Returns:
            是否记录成功
        """
        try:
            # 记录任务详情
            task_key = f"{self.STATS_PREFIX}task:{task_id}"
            task_data = {
                "task_id": task_id,
                "template_id": template_id,
                "output_format": output_format,
                "file_size": file_size,
                "pages": pages,
                "elapsed_ms": elapsed_ms,
                "success": success,
                "timestamp": self._utcnow(),
            }
            ttl_seconds = self._normalize_ttl(ttl)
            self._client.set(task_key, task_data, ex=ttl_seconds)

            # 更新统计计数器
            self._client.hincrby(self.STATS_COUNTER_KEY, "total_tasks", 1)
            if success:
                self._client.hincrby(self.STATS_COUNTER_KEY, "success_tasks", 1)
            else:
                self._client.hincrby(self.STATS_COUNTER_KEY, "failed_tasks", 1)

            # 更新格式分布计数
            self._client.hincrby(self.STATS_COUNTER_KEY, f"format:{output_format}", 1)

            # 更新模板使用统计
            template_key = f"{self.STATS_TEMPLATE_USAGE_PREFIX}{template_id}"
            self._client.hincrby(template_key, "usage_count", 1)
            self._client.set(f"{template_key}:name", template_id, ex=ttl_seconds)

            # 累加总页数和总文件大小
            self._client.hincrby(self.STATS_COUNTER_KEY, "total_pages", pages)
            self._client.hincrby(self.STATS_COUNTER_KEY, "total_file_size", file_size)

            # 累加总耗时（用于计算平均值）
            self._client.hincrby(self.STATS_COUNTER_KEY, "total_elapsed_ms", elapsed_ms)

            logger.debug(f"Recorded export task stats: {task_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to record export task stats: {e}")
            return False

    def get_export_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        获取导出统计数据

        Args:
            start_date: 开始日期（暂不支持过滤）
            end_date: 结束日期（暂不支持过滤）

        Returns:
            统计数据字典
        """
        try:
            counters = self._client.hgetall(self.STATS_COUNTER_KEY) or {}

            # 提取基础统计
            total_tasks = int(counters.get("total_tasks", 0))
            success_tasks = int(counters.get("success_tasks", 0))
            failed_tasks = int(counters.get("failed_tasks", 0))
            total_pages = int(counters.get("total_pages", 0))
            total_file_size = int(counters.get("total_file_size", 0))
            total_elapsed_ms = int(counters.get("total_elapsed_ms", 0))

            # 计算成功率
            success_rate = success_tasks / total_tasks if total_tasks > 0 else 0.0

            # 计算平均耗时
            avg_elapsed_ms = total_elapsed_ms / total_tasks if total_tasks > 0 else 0.0

            # 提取格式分布
            format_distribution = {}
            for key, value in counters.items():
                if key.startswith("format:"):
                    format_name = key.replace("format:", "")
                    format_distribution[format_name] = int(value)

            return {
                "total_tasks": total_tasks,
                "success_tasks": success_tasks,
                "failed_tasks": failed_tasks,
                "success_rate": round(success_rate, 4),
                "total_pages": total_pages,
                "total_file_size": total_file_size,
                "avg_elapsed_ms": round(avg_elapsed_ms, 2),
                "format_distribution": format_distribution,
            }

        except Exception as e:
            logger.error(f"Failed to get export stats: {e}")
            return {
                "total_tasks": 0,
                "success_tasks": 0,
                "failed_tasks": 0,
                "success_rate": 0.0,
                "total_pages": 0,
                "total_file_size": 0,
                "avg_elapsed_ms": 0.0,
                "format_distribution": {},
            }

    def get_template_usage_stats(
        self,
        template_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        获取模板使用统计

        Args:
            template_id: 模板ID（可选，如果指定则只返回该模板的统计）

        Returns:
            模板使用统计列表
        """
        try:
            if template_id:
                # 查询特定模板
                template_key = f"{self.STATS_TEMPLATE_USAGE_PREFIX}{template_id}"
                usage_count = self._client.hget(template_key, "usage_count")
                if usage_count:
                    return [
                        {
                            "template_id": template_id,
                            "template_name": template_id,
                            "usage_count": int(usage_count),
                        }
                    ]
                return []

            # 查询所有模板
            pattern = f"{self.STATS_TEMPLATE_USAGE_PREFIX}*"
            keys = self._client.keys(pattern)
            
            template_stats = []
            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                
                # 跳过name键
                if key.endswith(":name"):
                    continue
                
                template_id = key.replace(self.STATS_TEMPLATE_USAGE_PREFIX, "")
                usage_count = self._client.hget(key, "usage_count")
                
                if usage_count:
                    template_stats.append({
                        "template_id": template_id,
                        "template_name": template_id,
                        "usage_count": int(usage_count),
                    })

            # 按使用次数降序排序
            template_stats.sort(key=lambda x: x["usage_count"], reverse=True)
            return template_stats

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
            # 删除计数器
            self._client.delete(self.STATS_COUNTER_KEY)
            
            # 删除所有模板统计
            pattern = f"{self.STATS_TEMPLATE_USAGE_PREFIX}*"
            keys = self._client.keys(pattern)
            if keys:
                self._client.delete(*keys)
            
            # 删除所有任务统计
            pattern = f"{self.STATS_PREFIX}task:*"
            keys = self._client.keys(pattern)
            if keys:
                self._client.delete(*keys)
            
            logger.info("Stats reset successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to reset stats: {e}")
            return False

