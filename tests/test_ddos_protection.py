"""
DDoS防护中间件白盒测试
测试DDoS防护中间件的所有功能，包括：
- 启用/禁用状态
- IP获取逻辑
- 白名单/黑名单功能
- 请求频率检测（每秒/每分钟）
- 自动黑名单功能
- 响应头信息
- Redis错误处理
"""
from __future__ import annotations

import pytest
import time
from unittest.mock import MagicMock, AsyncMock, patch, Mock
from fastapi import Request, HTTPException, status
from fastapi.responses import Response

from core.middlewares.ddos_protection import DDoSProtectionMiddleware
from core.schemas.configs import DDoSProtectionConfig
from core.schemas import GlobalConfig


class TestDDoSProtectionMiddleware:
    """DDoS防护中间件测试类"""
    
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
        redis_client.exists = MagicMock(return_value=0)
        redis_client.set = MagicMock(return_value=True)
        redis_client.ttl = MagicMock(return_value=60)
        return redis_client
    
    @pytest.fixture
    def ddos_config_enabled(self):
        """创建启用的DDoS防护配置"""
        return DDoSProtectionConfig(
            enabled=True,
            max_requests_per_second=5,
            max_requests_per_minute=50,
            block_duration=3600,
            whitelist_ips=["10.0.0.1"],
            blacklist_ips=["192.168.1.100"],
            key_prefix="test_ddos",
            enable_auto_blacklist=True
        )
    
    @pytest.fixture
    def ddos_config_disabled(self):
        """创建禁用的DDoS防护配置"""
        return DDoSProtectionConfig(
            enabled=False,
            max_requests_per_second=5,
            max_requests_per_minute=50
        )
    
    @pytest.fixture
    def mock_config_enabled(self, ddos_config_enabled):
        """创建包含启用DDoS防护配置的全局配置"""
        config = MagicMock(spec=GlobalConfig)
        config.ddos_protection = ddos_config_enabled
        return config
    
    @pytest.fixture
    def mock_config_disabled(self, ddos_config_disabled):
        """创建包含禁用DDoS防护配置的全局配置"""
        config = MagicMock(spec=GlobalConfig)
        config.ddos_protection = ddos_config_disabled
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
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                assert middleware.enabled is True
                assert middleware.max_requests_per_second == 5
                assert middleware.max_requests_per_minute == 50
                assert middleware.block_duration == 3600
                assert "10.0.0.1" in middleware.whitelist_ips
                assert "192.168.1.100" in middleware.blacklist_ips
                assert middleware.key_prefix == "test_ddos"
                assert middleware.enable_auto_blacklist is True
    
    def test_init_disabled(self, mock_app, mock_config_disabled):
        """测试禁用状态下的初始化"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_disabled):
            middleware = DDoSProtectionMiddleware(mock_app)
            assert middleware.enabled is False
    
    def test_init_no_config(self, mock_app):
        """测试没有配置时的初始化"""
        config = MagicMock(spec=GlobalConfig)
        config.ddos_protection = None
        with patch('core.middlewares.ddos_protection.get_config', return_value=config):
            middleware = DDoSProtectionMiddleware(mock_app)
            # ddos_protection为None时，enabled可能是None或False，但应该被评估为False
            assert not middleware.enabled
    
    # ==================== IP获取测试 ====================
    
    def test_get_client_ip_from_client(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试从request.client获取IP"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                request = MagicMock(spec=Request)
                request.client = MagicMock()
                request.client.host = "192.168.1.1"
                request.headers = {}
                
                ip = middleware._get_client_ip(request)
                assert ip == "192.168.1.1"
    
    def test_get_client_ip_from_x_forwarded_for(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试从X-Forwarded-For头获取IP"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                request = MagicMock(spec=Request)
                request.client = MagicMock()
                request.client.host = "192.168.1.1"
                request.headers = {"X-Forwarded-For": "10.0.0.1, 10.0.0.2"}
                
                ip = middleware._get_client_ip(request)
                assert ip == "10.0.0.1"
    
    def test_get_client_ip_from_x_real_ip(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试从X-Real-IP头获取IP"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                request = MagicMock(spec=Request)
                request.client = MagicMock()
                request.client.host = "192.168.1.1"
                request.headers = {"X-Real-IP": "10.0.0.1"}
                
                ip = middleware._get_client_ip(request)
                assert ip == "10.0.0.1"
    
    # ==================== 白名单测试 ====================
    
    def test_is_whitelisted_true(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试IP在白名单中"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                assert middleware._is_whitelisted("10.0.0.1") is True
    
    def test_is_whitelisted_false(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试IP不在白名单中"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                assert middleware._is_whitelisted("127.0.0.1") is False
    
    @pytest.mark.asyncio
    async def test_dispatch_whitelisted_ip(self, mock_app, mock_config_enabled, mock_redis_client,
                                         mock_call_next):
        """测试白名单IP直接通过"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                request = MagicMock(spec=Request)
                request.client = MagicMock()
                request.client.host = "10.0.0.1"
                request.headers = {}
                
                response = await middleware.dispatch(request, mock_call_next)
                
                assert response.status_code == 200
                # 白名单IP不应该调用incr
                assert mock_redis_client.incr.call_count == 0
    
    # ==================== 黑名单测试 ====================
    
    def test_is_blacklisted_static(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试静态黑名单"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                assert middleware._is_blacklisted("192.168.1.100") is True
    
    def test_is_blacklisted_auto(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试自动黑名单"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                mock_redis_client.exists.return_value = 1  # 存在于自动黑名单
                
                assert middleware._is_blacklisted("127.0.0.1") is True
                mock_redis_client.exists.assert_called_once()
    
    def test_is_blacklisted_not_blacklisted(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试IP不在黑名单中"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                mock_redis_client.exists.return_value = 0
                
                assert middleware._is_blacklisted("127.0.0.1") is False
    
    def test_is_blacklisted_redis_error(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试检查黑名单时Redis错误"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                mock_redis_client.exists.side_effect = Exception("Redis error")
                
                # 发生错误时应该返回False（允许请求）
                assert middleware._is_blacklisted("127.0.0.1") is False
    
    @pytest.mark.asyncio
    async def test_dispatch_blacklisted_ip(self, mock_app, mock_config_enabled, mock_redis_client,
                                          mock_call_next):
        """测试黑名单IP被拒绝"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                request = MagicMock(spec=Request)
                request.client = MagicMock()
                request.client.host = "192.168.1.100"
                request.headers = {}
                
                with pytest.raises(HTTPException) as exc_info:
                    await middleware.dispatch(request, mock_call_next)
                
                assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
                assert "blacklisted" in exc_info.value.detail.lower()
    
    # ==================== 自动黑名单测试 ====================
    
    def test_add_to_blacklist(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试添加IP到自动黑名单"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                with patch('time.time', return_value=1234567890):
                    middleware = DDoSProtectionMiddleware(mock_app)
                    middleware._add_to_blacklist("127.0.0.1")
                    
                    mock_redis_client.set.assert_called_once()
                    call_args = mock_redis_client.set.call_args
                    assert "blacklist" in call_args[0][0]
                    assert call_args[1]["ex"] == 3600
    
    def test_add_to_blacklist_redis_error(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试添加黑名单时Redis错误"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                mock_redis_client.set.side_effect = Exception("Redis error")
                
                # 不应该抛出异常，只记录错误
                middleware._add_to_blacklist("127.0.0.1")
    
    # ==================== 请求频率检测测试 ====================
    
    def test_check_request_rate_under_limit(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试未超过限制的情况"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                mock_redis_client.incr.return_value = 3
                
                allowed, count = middleware._check_request_rate("127.0.0.1", "second", 5, 1)
                
                assert allowed is True
                assert count == 3
                mock_redis_client.incr.assert_called_once()
                # 当计数为3时，不是新键，所以expire不会被调用
                mock_redis_client.expire.assert_not_called()
    
    def test_check_request_rate_at_limit(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试刚好达到限制的情况"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                mock_redis_client.incr.return_value = 5
                
                allowed, count = middleware._check_request_rate("127.0.0.1", "second", 5, 1)
                
                assert allowed is True
                assert count == 5
                # 当计数为5时，不是新键，所以expire不会被调用
                mock_redis_client.expire.assert_not_called()
    
    def test_check_request_rate_over_limit(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试超过限制的情况"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                mock_redis_client.incr.return_value = 6
                
                allowed, count = middleware._check_request_rate("127.0.0.1", "second", 5, 1)
                
                assert allowed is False
                assert count == 6
    
    def test_check_request_rate_redis_error(self, mock_app, mock_config_enabled, mock_redis_client):
        """测试Redis错误时的处理"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                mock_redis_client.incr.side_effect = Exception("Redis error")
                
                allowed, count = middleware._check_request_rate("127.0.0.1", "second", 5, 1)
                
                # 发生错误时应该允许请求通过
                assert allowed is True
                assert count == 0
    
    # ==================== 中间件分发测试 ====================
    
    @pytest.mark.asyncio
    async def test_dispatch_disabled(self, mock_app, mock_config_disabled, mock_request, mock_call_next):
        """测试禁用状态下直接通过请求"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_disabled):
            middleware = DDoSProtectionMiddleware(mock_app)
            
            response = await middleware.dispatch(mock_request, mock_call_next)
            
            assert response.status_code == 200
            assert response.body == b"OK"
    
    @pytest.mark.asyncio
    async def test_dispatch_under_all_limits(self, mock_app, mock_config_enabled, mock_redis_client,
                                            mock_request, mock_call_next):
        """测试所有限制都未超过时正常处理请求"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                mock_redis_client.incr.return_value = 3
                
                response = await middleware.dispatch(mock_request, mock_call_next)
                
                assert response.status_code == 200
                assert "X-DDoS-Protection-Enabled" in response.headers
                assert response.headers["X-DDoS-Protection-Enabled"] == "true"
    
    @pytest.mark.asyncio
    async def test_dispatch_exceed_second_limit(self, mock_app, mock_config_enabled, mock_redis_client,
                                              mock_request, mock_call_next):
        """测试超过每秒限制时抛出429错误并添加到黑名单"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                
                def incr_side_effect(key):
                    if "second" in key:
                        return 6  # 超过限制
                    return 3
                
                mock_redis_client.incr.side_effect = incr_side_effect
                
                with pytest.raises(HTTPException) as exc_info:
                    await middleware.dispatch(mock_request, mock_call_next)
                
                assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                assert "second" in exc_info.value.detail.lower()
                # 验证自动添加到黑名单
                assert mock_redis_client.set.call_count > 0
    
    @pytest.mark.asyncio
    async def test_dispatch_exceed_minute_limit(self, mock_app, mock_config_enabled, mock_redis_client,
                                              mock_request, mock_call_next):
        """测试超过每分钟限制时抛出429错误并添加到黑名单"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                
                def incr_side_effect(key):
                    if "minute" in key:
                        return 51  # 超过限制
                    return 3
                
                mock_redis_client.incr.side_effect = incr_side_effect
                
                with pytest.raises(HTTPException) as exc_info:
                    await middleware.dispatch(mock_request, mock_call_next)
                
                assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
                assert "minute" in exc_info.value.detail.lower()
                # 验证自动添加到黑名单
                assert mock_redis_client.set.call_count > 0
    
    @pytest.mark.asyncio
    async def test_dispatch_auto_blacklist_disabled(self, mock_app, mock_config_enabled, mock_redis_client,
                                                   mock_request, mock_call_next):
        """测试禁用自动黑名单时不添加到黑名单"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                middleware.enable_auto_blacklist = False
                
                def incr_side_effect(key):
                    if "second" in key:
                        return 6  # 超过限制
                    return 3
                
                mock_redis_client.incr.side_effect = incr_side_effect
                
                with pytest.raises(HTTPException):
                    await middleware.dispatch(mock_request, mock_call_next)
                
                # 不应该调用set添加到黑名单
                assert mock_redis_client.set.call_count == 0
    
    @pytest.mark.asyncio
    async def test_dispatch_response_headers(self, mock_app, mock_config_enabled, mock_redis_client,
                                           mock_request, mock_call_next):
        """测试响应头中的防护信息"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                mock_redis_client.incr.return_value = 3
                
                response = await middleware.dispatch(mock_request, mock_call_next)
                
                # 检查所有防护相关的响应头
                assert response.headers["X-DDoS-Protection-Enabled"] == "true"
                assert response.headers["X-DDoS-Protection-Limit-Second"] == "5"
                assert response.headers["X-DDoS-Protection-Limit-Minute"] == "50"
    
    # ==================== 集成测试 ====================
    
    @pytest.mark.asyncio
    async def test_multiple_requests_increment_count(self, mock_app, mock_config_enabled, mock_redis_client,
                                                    mock_request, mock_call_next):
        """测试多次请求时计数递增"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                
                # 模拟多次请求，计数递增
                call_count = [0]
                def incr_side_effect(key):
                    call_count[0] += 1
                    return call_count[0]
                
                mock_redis_client.incr.side_effect = incr_side_effect
                
                # 前5次请求应该成功
                for i in range(5):
                    response = await middleware.dispatch(mock_request, mock_call_next)
                    assert response.status_code == 200
                
                # 重置计数器
                call_count[0] = 0
                mock_redis_client.incr.side_effect = lambda key: 6 if "second" in key else 3
                
                # 第6次请求应该被拒绝
                with pytest.raises(HTTPException) as exc_info:
                    await middleware.dispatch(mock_request, mock_call_next)
                
                assert exc_info.value.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    
    @pytest.mark.asyncio
    async def test_blacklisted_then_whitelisted(self, mock_app, mock_config_enabled, mock_redis_client,
                                               mock_call_next):
        """测试先被加入黑名单，然后通过白名单绕过"""
        with patch('core.middlewares.ddos_protection.get_config', return_value=mock_config_enabled):
            with patch('core.middlewares.ddos_protection.RedisClient', return_value=mock_redis_client):
                middleware = DDoSProtectionMiddleware(mock_app)
                
                # 模拟IP在自动黑名单中
                mock_redis_client.exists.return_value = 1
                request = MagicMock(spec=Request)
                request.client = MagicMock()
                request.client.host = "10.0.0.1"  # 白名单IP
                request.headers = {}
                
                # 白名单IP应该直接通过，即使也在黑名单中
                # 但根据代码逻辑，白名单检查在黑名单之前，所以应该通过
                response = await middleware.dispatch(request, mock_call_next)
                assert response.status_code == 200

