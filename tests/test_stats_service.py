"""
测试统计服务
"""

import pytest
from datetime import datetime
from core.service.stats_service import StatsService
from core.storage.cache_storage import CacheStorage


@pytest.fixture
def cache_storage():
    """创建测试用缓存存储"""
    cache = CacheStorage()
    # 重置统计数据
    cache.reset_stats()
    yield cache
    # 清理
    cache.reset_stats()


@pytest.fixture
def stats_service(cache_storage):
    """创建统计服务实例"""
    return StatsService(cache_storage=cache_storage)


class TestStatsService:
    """测试StatsService类"""

    def test_init(self, stats_service):
        """测试初始化"""
        assert stats_service is not None
        assert stats_service._cache is not None

    def test_record_export_task_success(self, stats_service):
        """测试记录成功的导出任务"""
        result = stats_service.record_export_task(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        
        assert result is True

    def test_record_export_task_failure(self, stats_service):
        """测试记录失败的导出任务"""
        result = stats_service.record_export_task(
            task_id="task_002",
            template_id="tpl_001",
            output_format="docx",
            file_size=0,
            pages=0,
            elapsed_ms=500,
            success=False,
        )
        
        assert result is True

    def test_get_export_stats_empty(self, stats_service):
        """测试获取空统计数据"""
        stats = stats_service.get_export_stats()
        
        assert stats["total_tasks"] == 0
        assert stats["success_tasks"] == 0
        assert stats["failed_tasks"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["avg_elapsed_ms"] == 0.0
        assert stats["total_pages"] == 0
        assert stats["total_file_size"] == 0
        assert stats["format_distribution"] == {}
        assert stats["template_usage"] == []

    def test_get_export_stats_with_data(self, stats_service):
        """测试获取有数据的统计"""
        # 记录几个任务
        stats_service.record_export_task(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        stats_service.record_export_task(
            task_id="task_002",
            template_id="tpl_002",
            output_format="docx",
            file_size=204800,
            pages=20,
            elapsed_ms=2500,
            success=True,
        )
        stats_service.record_export_task(
            task_id="task_003",
            template_id="tpl_001",
            output_format="pdf",
            file_size=0,
            pages=0,
            elapsed_ms=500,
            success=False,
        )
        
        stats = stats_service.get_export_stats()
        
        assert stats["total_tasks"] == 3
        assert stats["success_tasks"] == 2
        assert stats["failed_tasks"] == 1
        assert stats["success_rate"] == 0.6667  # 2/3
        assert stats["avg_elapsed_ms"] == 1500.0  # (1500 + 2500 + 500) / 3
        assert stats["total_pages"] == 30  # 10 + 20 + 0
        assert stats["total_file_size"] == 307200  # 102400 + 204800 + 0
        assert stats["format_distribution"]["pdf"] == 2
        assert stats["format_distribution"]["docx"] == 1
        assert len(stats["template_usage"]) == 2  # tpl_001 and tpl_002

    def test_get_export_stats_with_dates(self, stats_service):
        """测试带日期参数的导出统计"""
        # 记录任务
        stats_service.record_export_task(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        stats = stats_service.get_export_stats(
            start_date=start_date,
            end_date=end_date,
        )
        
        assert "period" in stats
        assert stats["period"]["start_date"] == "2024-01-01"
        assert stats["period"]["end_date"] == "2024-12-31"
        assert stats["total_tasks"] == 1

    def test_get_export_stats_no_dates(self, stats_service):
        """测试不带日期参数的导出统计"""
        stats_service.record_export_task(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        
        stats = stats_service.get_export_stats()
        
        assert "period" in stats
        assert "note" in stats["period"]
        assert "全部统计数据" in stats["period"]["note"]

    def test_get_performance_stats_empty(self, stats_service):
        """测试获取空性能统计"""
        stats = stats_service.get_performance_stats()
        
        assert stats["avg_elapsed_ms"] == 0.0
        assert stats["total_tasks"] == 0
        assert stats["total_pages"] == 0
        assert stats["total_file_size"] == 0

    def test_get_performance_stats_with_data(self, stats_service):
        """测试获取有数据的性能统计"""
        # 记录任务
        stats_service.record_export_task(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        stats_service.record_export_task(
            task_id="task_002",
            template_id="tpl_002",
            output_format="docx",
            file_size=204800,
            pages=20,
            elapsed_ms=2500,
            success=True,
        )
        
        stats = stats_service.get_performance_stats()
        
        assert stats["avg_elapsed_ms"] == 2000.0  # (1500 + 2500) / 2
        assert stats["total_tasks"] == 2
        assert stats["total_pages"] == 30
        assert stats["total_file_size"] == 307200

    def test_get_template_usage_stats_empty(self, stats_service):
        """测试获取空模板使用统计"""
        usage = stats_service.get_template_usage_stats()
        
        assert usage == []

    def test_get_template_usage_stats_all(self, stats_service):
        """测试获取所有模板使用统计"""
        # 记录多个任务
        stats_service.record_export_task(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        stats_service.record_export_task(
            task_id="task_002",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        stats_service.record_export_task(
            task_id="task_003",
            template_id="tpl_002",
            output_format="docx",
            file_size=204800,
            pages=20,
            elapsed_ms=2500,
            success=True,
        )
        
        usage = stats_service.get_template_usage_stats()
        
        assert len(usage) == 2
        # 按使用次数排序，tpl_001应该在前面
        assert usage[0]["template_id"] == "tpl_001"
        assert usage[0]["usage_count"] == 2
        assert usage[1]["template_id"] == "tpl_002"
        assert usage[1]["usage_count"] == 1

    def test_get_template_usage_stats_specific(self, stats_service):
        """测试获取特定模板使用统计"""
        # 记录任务
        stats_service.record_export_task(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        stats_service.record_export_task(
            task_id="task_002",
            template_id="tpl_002",
            output_format="docx",
            file_size=204800,
            pages=20,
            elapsed_ms=2500,
            success=True,
        )
        
        # 查询特定模板
        usage = stats_service.get_template_usage_stats(template_id="tpl_001")
        
        assert len(usage) == 1
        assert usage[0]["template_id"] == "tpl_001"
        assert usage[0]["usage_count"] == 1

    def test_get_template_usage_stats_nonexistent(self, stats_service):
        """测试获取不存在的模板统计"""
        usage = stats_service.get_template_usage_stats(template_id="tpl_nonexistent")
        
        assert usage == []

    def test_reset_stats(self, stats_service):
        """测试重置统计数据"""
        # 记录任务
        stats_service.record_export_task(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        
        # 验证有数据
        stats = stats_service.get_export_stats()
        assert stats["total_tasks"] == 1
        
        # 重置
        result = stats_service.reset_stats()
        assert result is True
        
        # 验证数据已清空
        stats = stats_service.get_export_stats()
        assert stats["total_tasks"] == 0

    def test_success_rate_calculation(self, stats_service):
        """测试成功率计算"""
        # 记录10个成功，2个失败
        for i in range(10):
            stats_service.record_export_task(
                task_id=f"task_{i}",
                template_id="tpl_001",
                output_format="pdf",
                file_size=102400,
                pages=10,
                elapsed_ms=1500,
                success=True,
            )
        
        for i in range(2):
            stats_service.record_export_task(
                task_id=f"task_fail_{i}",
                template_id="tpl_001",
                output_format="pdf",
                file_size=0,
                pages=0,
                elapsed_ms=500,
                success=False,
            )
        
        stats = stats_service.get_export_stats()
        
        assert stats["total_tasks"] == 12
        assert stats["success_tasks"] == 10
        assert stats["failed_tasks"] == 2
        # 10/12 = 0.8333
        assert 0.833 <= stats["success_rate"] <= 0.834

    def test_format_distribution(self, stats_service):
        """测试格式分布统计"""
        # 记录不同格式的任务
        stats_service.record_export_task(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        stats_service.record_export_task(
            task_id="task_002",
            template_id="tpl_002",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        stats_service.record_export_task(
            task_id="task_003",
            template_id="tpl_003",
            output_format="docx",
            file_size=204800,
            pages=20,
            elapsed_ms=2500,
            success=True,
        )
        stats_service.record_export_task(
            task_id="task_004",
            template_id="tpl_004",
            output_format="html",
            file_size=50000,
            pages=5,
            elapsed_ms=800,
            success=True,
        )
        
        stats = stats_service.get_export_stats()
        
        assert stats["format_distribution"]["pdf"] == 2
        assert stats["format_distribution"]["docx"] == 1
        assert stats["format_distribution"]["html"] == 1

    def test_multiple_templates_usage(self, stats_service):
        """测试多个模板的使用统计"""
        # 模板1使用5次
        for i in range(5):
            stats_service.record_export_task(
                task_id=f"task_1_{i}",
                template_id="tpl_001",
                output_format="pdf",
                file_size=102400,
                pages=10,
                elapsed_ms=1500,
                success=True,
            )
        
        # 模板2使用3次
        for i in range(3):
            stats_service.record_export_task(
                task_id=f"task_2_{i}",
                template_id="tpl_002",
                output_format="docx",
                file_size=204800,
                pages=20,
                elapsed_ms=2500,
                success=True,
            )
        
        # 模板3使用1次
        stats_service.record_export_task(
            task_id="task_3",
            template_id="tpl_003",
            output_format="html",
            file_size=50000,
            pages=5,
            elapsed_ms=800,
            success=True,
        )
        
        usage = stats_service.get_template_usage_stats()
        
        assert len(usage) == 3
        # 按使用次数降序排序
        assert usage[0]["template_id"] == "tpl_001"
        assert usage[0]["usage_count"] == 5
        assert usage[1]["template_id"] == "tpl_002"
        assert usage[1]["usage_count"] == 3
        assert usage[2]["template_id"] == "tpl_003"
        assert usage[2]["usage_count"] == 1


class TestCacheStorageStats:
    """测试CacheStorage的统计功能"""

    def test_record_export_task(self, cache_storage):
        """测试记录导出任务"""
        result = cache_storage.record_export_task(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        
        assert result is True

    def test_get_export_stats(self, cache_storage):
        """测试获取导出统计"""
        # 记录任务
        cache_storage.record_export_task(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        
        stats = cache_storage.get_export_stats()
        
        assert stats["total_tasks"] == 1
        assert stats["success_tasks"] == 1
        assert stats["failed_tasks"] == 0

    def test_get_template_usage_stats(self, cache_storage):
        """测试获取模板使用统计"""
        # 记录任务
        cache_storage.record_export_task(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        
        usage = cache_storage.get_template_usage_stats()
        
        assert len(usage) == 1
        assert usage[0]["template_id"] == "tpl_001"
        assert usage[0]["usage_count"] == 1

    def test_reset_stats(self, cache_storage):
        """测试重置统计"""
        # 记录任务
        cache_storage.record_export_task(
            task_id="task_001",
            template_id="tpl_001",
            output_format="pdf",
            file_size=102400,
            pages=10,
            elapsed_ms=1500,
            success=True,
        )
        
        # 重置
        result = cache_storage.reset_stats()
        assert result is True
        
        # 验证已清空
        stats = cache_storage.get_export_stats()
        assert stats["total_tasks"] == 0

