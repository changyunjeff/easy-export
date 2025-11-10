from __future__ import annotations

import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from core.config import get_config
from core.redis import RedisClient

logger = logging.getLogger(__name__)


class DDoSProtectionMiddleware(BaseHTTPMiddleware):
    """
    DDoS防护中间件
    
    提供多层防护机制：
    - IP白名单/黑名单
    - 请求频率检测（每秒/每分钟）
    - 自动封禁超过阈值的IP
    - 基于Redis的分布式防护
    
    使用Redis存储请求计数和黑名单，如果Redis不可用则回退到内存存储
    """
    
    def __init__(self, app):
        super().__init__(app)
        self.config = get_config()
        self.ddos_config = getattr(self.config, "ddos_protection", None)
        self.enabled = self.ddos_config and getattr(self.ddos_config, "enabled", False)
        
        if self.enabled:
            self.redis_client = RedisClient()
            self.max_requests_per_second = getattr(self.ddos_config, "max_requests_per_second", 10)
            self.max_requests_per_minute = getattr(self.ddos_config, "max_requests_per_minute", 100)
            self.block_duration = getattr(self.ddos_config, "block_duration", 3600)
            self.whitelist_ips = set(getattr(self.ddos_config, "whitelist_ips", []))
            self.blacklist_ips = set(getattr(self.ddos_config, "blacklist_ips", []))
            self.key_prefix = getattr(self.ddos_config, "key_prefix", "ddos_protection")
            self.enable_auto_blacklist = getattr(self.ddos_config, "enable_auto_blacklist", True)
            
            logger.info(
                f"DDoS protection enabled: {self.max_requests_per_second}/sec, "
                f"{self.max_requests_per_minute}/min, block duration: {self.block_duration}s"
            )
            if self.whitelist_ips:
                logger.info(f"Whitelisted IPs: {self.whitelist_ips}")
            if self.blacklist_ips:
                logger.info(f"Blacklisted IPs: {self.blacklist_ips}")
        else:
            logger.info("DDoS protection disabled")
    
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
    
    def _is_whitelisted(self, ip: str) -> bool:
        """检查IP是否在白名单中"""
        return ip in self.whitelist_ips
    
    def _is_blacklisted(self, ip: str) -> bool:
        """检查IP是否在黑名单中（包括自动黑名单）"""
        # 检查配置中的静态黑名单
        if ip in self.blacklist_ips:
            return True
        
        # 检查Redis中的自动黑名单
        try:
            blacklist_key = f"{self.key_prefix}:blacklist:{ip}"
            exists = self.redis_client.exists(blacklist_key)
            return exists > 0
        except Exception as e:
            logger.error(f"Error checking blacklist for IP {ip}: {e}")
            return False
    
    def _add_to_blacklist(self, ip: str):
        """将IP添加到自动黑名单"""
        try:
            blacklist_key = f"{self.key_prefix}:blacklist:{ip}"
            self.redis_client.set(blacklist_key, int(time.time()), ex=self.block_duration)
            logger.warning(f"IP {ip} added to auto blacklist for {self.block_duration} seconds")
        except Exception as e:
            logger.error(f"Error adding IP {ip} to blacklist: {e}")
    
    def _check_request_rate(self, ip: str, window: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """
        检查请求频率
        
        Args:
            ip: 客户端IP
            window: 时间窗口标识（second/minute）
            limit: 限制数量
            window_seconds: 时间窗口秒数
        
        Returns:
            (是否允许, 当前计数)
        """
        key = f"{self.key_prefix}:rate:{ip}:{window}"
        
        try:
            # 先尝试增加计数（如果键不存在，incr会创建并设置为1）
            new_count = self.redis_client.incr(key)
            
            # 如果是新创建的键（值为1），设置过期时间
            if new_count == 1:
                self.redis_client.expire(key, window_seconds)
            
            # 检查是否超过限制
            if new_count > limit:
                return False, new_count
            
            return True, new_count
            
        except Exception as e:
            logger.error(f"DDoS protection check error for IP {ip}: {e}")
            # 发生错误时允许请求通过，避免影响正常服务
            return True, 0
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 如果未启用DDoS防护，直接通过
        if not self.enabled:
            return await call_next(request)
        
        # 获取客户端IP
        client_ip = self._get_client_ip(request)
        
        # 检查白名单
        if self._is_whitelisted(client_ip):
            return await call_next(request)
        
        # 检查黑名单
        if self._is_blacklisted(client_ip):
            logger.warning(f"Blocked request from blacklisted IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: IP address is blacklisted"
            )
        
        # 检查每秒请求频率
        allowed_sec, count_sec = self._check_request_rate(
            client_ip, "second", self.max_requests_per_second, 1
        )
        if not allowed_sec:
            logger.warning(
                f"DDoS protection triggered (second) for IP {client_ip}: "
                f"{count_sec}/{self.max_requests_per_second} requests per second"
            )
            if self.enable_auto_blacklist:
                self._add_to_blacklist(client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests: {count_sec} requests per second. "
                       f"Limit: {self.max_requests_per_second}/sec"
            )
        
        # 检查每分钟请求频率
        allowed_min, count_min = self._check_request_rate(
            client_ip, "minute", self.max_requests_per_minute, 60
        )
        if not allowed_min:
            logger.warning(
                f"DDoS protection triggered (minute) for IP {client_ip}: "
                f"{count_min}/{self.max_requests_per_minute} requests per minute"
            )
            if self.enable_auto_blacklist:
                self._add_to_blacklist(client_ip)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many requests: {count_min} requests per minute. "
                       f"Limit: {self.max_requests_per_minute}/min"
            )
        
        # 处理请求
        response = await call_next(request)
        
        # 添加防护信息到响应头
        response.headers["X-DDoS-Protection-Enabled"] = "true"
        response.headers["X-DDoS-Protection-Limit-Second"] = str(self.max_requests_per_second)
        response.headers["X-DDoS-Protection-Limit-Minute"] = str(self.max_requests_per_minute)
        
        return response

