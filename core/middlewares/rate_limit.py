from __future__ import annotations

import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import get_config
from core.redis import RedisClient

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    限流中间件
    
    基于滑动窗口算法实现限流，支持：
    - 每分钟请求数限制
    - 每小时请求数限制
    - 每天请求数限制
    
    使用Redis存储限流计数，如果Redis不可用则回退到内存存储
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.config = get_config()
        self.rate_limit_config = getattr(self.config, "rate_limit", None)
        self.enabled = self.rate_limit_config and getattr(self.rate_limit_config, "enabled", False)
        
        if self.enabled:
            self.redis_client = RedisClient()
            self.requests_per_minute = getattr(self.rate_limit_config, "requests_per_minute", 60)
            self.requests_per_hour = getattr(self.rate_limit_config, "requests_per_hour", 1000)
            self.requests_per_day = getattr(self.rate_limit_config, "requests_per_day", 10000)
            self.key_prefix = getattr(self.rate_limit_config, "key_prefix", "rate_limit")
            logger.info(
                f"Rate limiting enabled: {self.requests_per_minute}/min, "
                f"{self.requests_per_hour}/hour, {self.requests_per_day}/day"
            )
        else:
            logger.info("Rate limiting disabled")
    
    def _get_client_ip(self, request: Request) -> str:
        """获取客户端IP地址"""
        # 检查代理头
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # X-Forwarded-For可能包含多个IP，取第一个
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _check_rate_limit(self, ip: str, window: str, limit: int, window_seconds: int) -> tuple[bool, int, int]:
        """
        检查是否超过限流阈值
        
        Args:
            ip: 客户端IP
            window: 时间窗口标识（minute/hour/day）
            limit: 限制数量
            window_seconds: 时间窗口秒数
        
        Returns:
            (是否允许, 当前计数, 剩余时间)
        """
        key = f"{self.key_prefix}:{ip}:{window}"
        
        try:
            # 先尝试增加计数（如果键不存在，incr会创建并设置为1）
            new_count = self.redis_client.incr(key)
            
            # 如果是新创建的键（值为1），设置过期时间
            if new_count == 1:
                self.redis_client.expire(key, window_seconds)
            
            # 检查是否超过限制
            if new_count > limit:
                ttl = self.redis_client.ttl(key)
                return False, new_count, max(0, ttl)
            
            return True, new_count, max(0, self.redis_client.ttl(key))
            
        except Exception as e:
            logger.error(f"Rate limit check error for IP {ip}: {e}")
            # 发生错误时允许请求通过，避免影响正常服务
            return True, 0, 0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 如果未启用限流，直接通过
        if not self.enabled:
            return await call_next(request)
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 检查白名单（如果有）
        # 这里可以扩展支持IP白名单
        
        # 检查每分钟限制
        allowed_min, count_min, ttl_min = self._check_rate_limit(
            client_ip, "minute", self.requests_per_minute, 60
        )
        if not allowed_min:
            logger.warning(
                f"Rate limit exceeded (minute) for IP {client_ip}: "
                f"{count_min}/{self.requests_per_minute}, retry after {ttl_min}s"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {count_min} requests in the last minute. "
                       f"Limit: {self.requests_per_minute}/min. Retry after {ttl_min} seconds.",
                headers={"Retry-After": str(ttl_min), "X-RateLimit-Limit": str(self.requests_per_minute)}
            )
        
        # 检查每小时限制
        allowed_hour, count_hour, ttl_hour = self._check_rate_limit(
            client_ip, "hour", self.requests_per_hour, 3600
        )
        if not allowed_hour:
            logger.warning(
                f"Rate limit exceeded (hour) for IP {client_ip}: "
                f"{count_hour}/{self.requests_per_hour}, retry after {ttl_hour}s"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {count_hour} requests in the last hour. "
                       f"Limit: {self.requests_per_hour}/hour. Retry after {ttl_hour} seconds.",
                headers={"Retry-After": str(ttl_hour), "X-RateLimit-Limit": str(self.requests_per_hour)}
            )
        
        # 检查每天限制
        allowed_day, count_day, ttl_day = self._check_rate_limit(
            client_ip, "day", self.requests_per_day, 86400
        )
        if not allowed_day:
            logger.warning(
                f"Rate limit exceeded (day) for IP {client_ip}: "
                f"{count_day}/{self.requests_per_day}, retry after {ttl_day}s"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {count_day} requests in the last day. "
                       f"Limit: {self.requests_per_day}/day. Retry after {ttl_day} seconds.",
                headers={"Retry-After": str(ttl_day), "X-RateLimit-Limit": str(self.requests_per_day)}
            )
        
        # 处理请求
        response = await call_next(request)
        
        # 添加限流信息到响应头
        response.headers["X-RateLimit-Limit-Minute"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Limit-Hour"] = str(self.requests_per_hour)
        response.headers["X-RateLimit-Limit-Day"] = str(self.requests_per_day)
        response.headers["X-RateLimit-Remaining-Minute"] = str(max(0, self.requests_per_minute - count_min))
        response.headers["X-RateLimit-Remaining-Hour"] = str(max(0, self.requests_per_hour - count_hour))
        response.headers["X-RateLimit-Remaining-Day"] = str(max(0, self.requests_per_day - count_day))
        
        return response

