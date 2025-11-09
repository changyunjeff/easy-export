"""
图表生成器模块
负责图表生成（折线图、柱状图、饼图等）、图表缓存管理、图表样式配置
"""

import logging
from typing import List, Dict, Any, Optional
import hashlib
import json

from core.storage import CacheStorage

logger = logging.getLogger(__name__)


class ChartGenerator:
    """
    图表生成器类
    负责图表生成、图表缓存管理等
    """
    
    def __init__(self, cache_storage: Optional[CacheStorage] = None):
        """
        初始化图表生成器
        
        Args:
            cache_storage: 缓存存储实例，如果为 None 则创建新实例
        """
        from core.storage import CacheStorage
        self.cache_storage = cache_storage or CacheStorage()
        logger.info("Chart generator initialized")
    
    def generate_line_chart(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> bytes:
        """
        生成折线图
        
        Args:
            data: 图表数据（字典列表）
            config: 图表配置（标题、坐标轴、颜色等）
            
        Returns:
            图表图片内容（字节，PNG格式）
            
        Raises:
            NotImplementedError: 功能未实现
        """
        raise NotImplementedError("折线图生成功能待实现")
    
    def generate_bar_chart(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> bytes:
        """
        生成柱状图
        
        Args:
            data: 图表数据（字典列表）
            config: 图表配置（标题、坐标轴、颜色等）
            
        Returns:
            图表图片内容（字节，PNG格式）
            
        Raises:
            NotImplementedError: 功能未实现
        """
        raise NotImplementedError("柱状图生成功能待实现")
    
    def generate_pie_chart(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> bytes:
        """
        生成饼图
        
        Args:
            data: 图表数据（字典列表）
            config: 图表配置（标题、颜色等）
            
        Returns:
            图表图片内容（字节，PNG格式）
            
        Raises:
            NotImplementedError: 功能未实现
        """
        raise NotImplementedError("饼图生成功能待实现")
    
    def get_cached_chart(self, data_hash: str) -> Optional[bytes]:
        """
        获取缓存的图表
        
        Args:
            data_hash: 数据哈希值
            
        Returns:
            图表内容（字节），如果不存在则返回 None
        """
        return self.cache_storage.get_cached_chart(data_hash)
    
    def cache_chart(
        self,
        data_hash: str,
        chart: bytes,
        ttl: int = 3600,
    ) -> bool:
        """
        缓存图表
        
        Args:
            data_hash: 数据哈希值
            chart: 图表内容（字节）
            ttl: 缓存过期时间（秒），默认1小时
            
        Returns:
            是否缓存成功
        """
        return self.cache_storage.cache_chart(data_hash, chart, ttl)
    
    def calculate_data_hash(
        self,
        data: List[Dict[str, Any]],
        config: Dict[str, Any],
    ) -> str:
        """
        计算数据哈希值（用于缓存）
        
        Args:
            data: 图表数据
            config: 图表配置
            
        Returns:
            数据哈希值
        """
        # 将数据和配置序列化为JSON字符串，然后计算哈希
        combined = {
            "data": data,
            "config": config,
        }
        json_str = json.dumps(combined, sort_keys=True, ensure_ascii=False)
        hash_obj = hashlib.sha256(json_str.encode("utf-8"))
        return hash_obj.hexdigest()

