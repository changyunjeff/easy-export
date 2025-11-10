"""
限流中间件白盒测试
测试限流中间件的所有功能，包括：
- 启用/禁用状态
- IP获取逻辑
- 限流检查逻辑（分钟/小时/天）
- 超过限制时的行为
- 响应头信息
- Redis错误处理
"""
from __future__ import annotations

import pytest
import time
from unittest.mock import MagicMock, AsyncMock, patch, Mock
from fastapi import Request, HTTPException, status
from fastapi.responses import Response

from core.middlewares.rate_limit import RateLimitMiddleware
from core.schemas.configs import RateLimitConfig
from core.schemas import GlobalConfig


class TestRateLimitMiddleware:
    """限流中间件测试类"""
    
    @pytest.fixture
    def mock_app(self):
        """创建模拟的FastAPI应用"""
        app = MagicMock()
        return app
    
    @pytest.fixture
    def mock_redis_client(self):
        """创建模拟的Redis客户端"""
        redis_client = MagicMock()
        redis_client.incr = MagicMock(return_value=1)
        redis_client.expire = MagicMock(return_value=True)
        redis_client.ttl = MagicMock(return_value=60)
        return redis_client
    
    @pytest.fixture
    def rate_limit_config_enabled(self):
        """创建启用的限流配置"""
        return RateLimitConfig(
            enabled=True,
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=1000,
            key_prefix="test_rate_limit"
        )
    
    @pytest.fixture
    def rate_limit_config_disabled(self):
        """创建禁用的限流配置"""
        return RateLimitConfig(
            enabled=False,
            requests_per_minute=10,
            requests_per_hour=100,
            requests_per_day=1000
        )
    
    @pytest.fixture
    def mock_config_enabled(self, rate_limit_config_enabled):
        """创建包含启用限流配置的全局配置"""
        config = MagicMock(spec=GlobalConfig)
        config.rate_limit = rate_limit_config_enabled
        return config
    
    @pytest.fixture
    def mock_config_disabled(self, rate_limit_config_disabled):
        """创建包含禁用限流配置的全局配置"""
        config = MagicMock(spec=GlobalConfig)
        config.rate_limit = rate_limit_config_disabled
        return config
    
    @pytest.fixture
    def mock_request(self):
        """创建模拟的Request对象"""
        request = MagicMock(spec=Request)
        request.client = MagicMock()
        request.client.host = "127.0.0.1"
        request.headers = {}
        return request
    
    @pytest.fixture
    def mock_call_next(self):
        """创建模拟的call_next函数"""
        async def call_next(request):
            return Response(content="OK", status_code=200)
        return call_next
    
    # ==================== 初始化测试 ====================
    
    def test_init_enabled(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试启用状态下的初始化"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                assert middleware.enabled is True
                assert middleware.requests_per_minute == 10
                assert middleware.requests_per_hour == 100
                assert middleware.requests_per_day == 1000
                assert middleware.key_prefix == "test_rate_limit"
    
    def test_init_disabled(self, mock_app, mock_config_disabled):
        """测试禁用状态下的初始化"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_disabled):
            middleware = RateLimitMiddleware(mock_app)
            assert middleware.enabled is False
    
    def test_init_no_config(self, mock_app):
        """测试没有配置时的初始化"""
        config = MagicMock(spec=GlobalConfig)
        config.rate_limit = None
        with patch('core.middlewares.rate_limit.get_config', return_value=config):
            middleware = RateLimitMiddleware(mock_app)
            # rate_limit_config为None时，enabled可能是None或False，但应该被评估为False
            assert not middleware.enabled
    
    # ==================== IP获取测试 ====================
    
    def test_get_client_ip_from_client(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试从request.client获取IP"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                request = MagicMock(spec=Request)
                request.client = MagicMock()
                request.client.host = "192.168.1.1"
                request.headers = {}
                
                ip = middleware._get_client_ip(request)
                assert ip == "192.168.1.1"
    
    def test_get_client_ip_from_x_forwarded_for(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试从X-Forwarded-For头获取IP"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                request = MagicMock(spec=Request)
                request.client = MagicMock()
                request.client.host = "192.168.1.1"
                request.headers = {"X-Forwarded-For": "10.0.0.1, 10.0.0.2"}
                
                ip = middleware._get_client_ip(request)
                assert ip == "10.0.0.1"
    
    def test_get_client_ip_from_x_real_ip(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试从X-Real-IP头获取IP"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                request = MagicMock(spec=Request)
                request.client = MagicMock()
                request.client.host = "192.168.1.1"
                request.headers = {"X-Real-IP": "10.0.0.1"}
                
                ip = middleware._get_client_ip(request)
                assert ip == "10.0.0.1"
    
    def test_get_client_ip_unknown(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试无法获取IP时返回unknown"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                request = MagicMock(spec=Request)
                request.client = None
                request.headers = {}
                
                ip = middleware._get_client_ip(request)
                assert ip == "unknown"
    
    # ==================== 限流检查测试 ====================
    
    def test_check_rate_limit_under_limit(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试未超过限制的情况"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                mock_redis_client.incr.return_value = 5
                mock_redis_client.ttl.return_value = 30
                
                allowed, count, ttl = middleware._check_rate_limit("127.0.0.1", "minute", 10, 60)
                
                assert allowed is True
                assert count == 5
                assert ttl == 30
                mock_redis_client.incr.assert_called_once()
                # 当计数为5时，不是新键，所以expire不会被调用
                mock_redis_client.expire.assert_not_called()
    
    def test_check_rate_limit_at_limit(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试刚好达到限制的情况"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                mock_redis_client.incr.return_value = 10
                mock_redis_client.ttl.return_value = 30
                
                allowed, count, ttl = middleware._check_rate_limit("127.0.0.1", "minute", 10, 60)
                
                assert allowed is True
                assert count == 10
                assert ttl == 30
                # 当计数为10时，不是新键，所以expire不会被调用
                mock_redis_client.expire.assert_not_called()
    
    def test_check_rate_limit_over_limit(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试超过限制的情况"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                mock_redis_client.incr.return_value = 11
                mock_redis_client.ttl.return_value = 30
                
                allowed, count, ttl = middleware._check_rate_limit("127.0.0.1", "minute", 10, 60)
                
                assert allowed is False
                assert count == 11
                assert ttl == 30
    
    def test_check_rate_limit_new_key(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试新键的创建和过期时间设置"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                mock_redis_client.incr.return_value = 1
                mock_redis_client.ttl.return_value = 60
                
                allowed, count, ttl = middleware._check_rate_limit("127.0.0.1", "minute", 10, 60)
                
                assert allowed is True
                assert count == 1
                # 验证expire被调用
                mock_redis_client.expire.assert_called_once()
    
    def test_check_rate_limit_redis_error(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试Redis错误时的处理"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                mock_redis_client.incr.side_effect = Exception("Redis error")
                
                allowed, count, ttl = middleware._check_rate_limit("127.0.0.1", "minute", 10, 60)
                
                # 发生错误时应该允许请求通过
                assert allowed is True
                assert count == 0
                assert ttl == 0
    
    # ==================== 中间件分发测试 ====================
    
    @pytest.mark.asyncio
    async def test_dispatch_disabled(self, mock_app, mock_config_disabled, mock_request, mock_call_next):
        """测试禁用状态下直接通过请求"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_disabled):
            middleware = RateLimitMiddleware(mock_app)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            assert response.status_code == 200
            assert response.body == b"OK"
    
    @pytest.mark.asyncio
    async def test_dispatch_under_all_limits(self, mock_app, mock_config_enabled, mock_redis_client, 
                                            mock_request, mock_call_next):
        """测试所有限制都未超过时正常处理请求"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                mock_redis_client.incr.return_value = 5
                mock_redis_client.ttl.return_value = 30
                
                response = await middleware.dispatch(mock_request, mock_call_next)
                
                assert response.status_code == 200
                assert "X-RateLimit-Limit-Minute" in response.headers
                assert "X-RateLimit-Remaining-Minute" in response.headers
                assert response.headers["X-RateLimit-Limit-Minute"] == "10"
                assert response.headers["X-RateLimit-Remaining-Minute"] == "5"
    
    @pytest.mark.asyncio
    async def test_dispatch_exceed_minute_limit(self, mock_app, mock_config_enabled, mock_redis_client,
                                               mock_request, mock_call_next):
        """测试超过分钟限制时抛出429错误"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                
                # 第一次调用返回正常值，后续调用返回超过限制的值
                def incr_side_effect(key):
                    if "minute" in key:
                        return 11  # 超过限制
                    return 5
                
                mock_redis_client.incr.side_effect = incr_side_effect
                mock_redis_client.ttl.return_value = 30
                
                with pytest.raises(HTTPException) as exc_info:
                    await middleware.dispatch(mock_request, mock_call_next)
                
                assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                assert "Retry-After" in exc_info.value.headers
                assert exc_info.value.headers["Retry-After"] == "30"
    
    @pytest.mark.asyncio
    async def test_dispatch_exceed_hour_limit(self, mock_app, mock_config_enabled, mock_redis_client,
                                             mock_request, mock_call_next):
        """测试超过小时限制时抛出429错误"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                
                def incr_side_effect(key):
                    if "hour" in key:
                        return 101  # 超过限制
                    return 5
                
                mock_redis_client.incr.side_effect = incr_side_effect
                mock_redis_client.ttl.return_value = 1800
                
                with pytest.raises(HTTPException) as exc_info:
                    await middleware.dispatch(mock_request, mock_call_next)
                
                assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                assert "hour" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_dispatch_exceed_day_limit(self, mock_app, mock_config_enabled, mock_redis_client,
                                           mock_request, mock_call_next):
        """测试超过天限制时抛出429错误"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                
                def incr_side_effect(key):
                    if "day" in key:
                        return 1001  # 超过限制
                    return 5
                
                mock_redis_client.incr.side_effect = incr_side_effect
                mock_redis_client.ttl.return_value = 3600
                
                with pytest.raises(HTTPException) as exc_info:
                    await middleware.dispatch(mock_request, mock_call_next)
                
                assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                assert "day" in exc_info.value.detail.lower()
    
    @pytest.mark.asyncio
    async def test_dispatch_response_headers(self, mock_app, mock_config_enabled, mock_redis_client,
                                           mock_request, mock_call_next):
        """测试响应头中的限流信息"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                mock_redis_client.incr.return_value = 3
                mock_redis_client.ttl.return_value = 30
                
                response = await middleware.dispatch(mock_request, mock_call_next)
                
                # 检查所有限流相关的响应头
                assert response.headers["X-RateLimit-Limit-Minute"] == "10"
                assert response.headers["X-RateLimit-Limit-Hour"] == "100"
                assert response.headers["X-RateLimit-Limit-Day"] == "1000"
                assert response.headers["X-RateLimit-Remaining-Minute"] == "7"
                assert response.headers["X-RateLimit-Remaining-Hour"] == "97"
                assert response.headers["X-RateLimit-Remaining-Day"] == "997"
    
    @pytest.mark.asyncio
    async def test_dispatch_negative_remaining(self, mock_app, mock_config_enabled, mock_redis_client,
                                              mock_request, mock_call_next):
        """测试剩余数量为负数时应该返回0"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                # 设置计数超过限制（虽然不应该发生，但测试边界情况）
                mock_redis_client.incr.return_value = 15
                mock_redis_client.ttl.return_value = 30
                
                # 由于计数超过限制，应该抛出异常
                with pytest.raises(HTTPException):
                    await middleware.dispatch(mock_request, mock_call_next)
    
    # ==================== 集成测试 ====================
    
    @pytest.mark.asyncio
    async def test_multiple_requests_increment_count(self, mock_app, mock_config_enabled, mock_redis_client,
                                                    mock_request, mock_call_next):
        """测试多次请求时计数递增"""
        with patch('core.middlewares.rate_limit.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.rate_limit.RedisClient', return_value=mock_redis_client):
                middleware = RateLimitMiddleware(mock_app)
                
                # 模拟多次请求，计数递增
                call_count = [0]
                def incr_side_effect(key):
                    call_count[0] += 1
                    return call_count[0]
                
                mock_redis_client.incr.side_effect = incr_side_effect
                mock_redis_client.ttl.return_value = 30
                
                # 前10次请求应该成功
                for i in range(10):
                    response = await middleware.dispatch(mock_request, mock_call_next)
                    assert response.status_code == 200
                
                # 重置计数器
                call_count[0] = 0
                mock_redis_client.incr.side_effect = lambda key: 11
                
                # 第11次请求应该被拒绝
                with pytest.raises(HTTPException) as exc_info:
                    await middleware.dispatch(mock_request, mock_call_next)
                
                assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS

