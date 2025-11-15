"""
健康检查API测试
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
import os
import tempfile


@pytest.fixture
def client():
    """创建测试客户端"""
    from main import create_app
    app = create_app()
    return TestClient(app)


class TestHealthAPI:
    """健康检查API测试类"""
    
    def test_liveness_check(self, client):
        """测试存活检查端点"""
        response = client.get("/api/v1/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0  # 0 means success
        assert data["data"]["status"] == "alive"
        assert "timestamp" in data["data"]
    
    def test_health_check_all_healthy(self, client):
        """测试所有组件健康的情况"""
        with patch("core.api.v1.health._check_redis", new_callable=AsyncMock) as mock_redis, \
             patch("core.api.v1.health._check_queue", new_callable=AsyncMock) as mock_queue, \
             patch("core.api.v1.health._check_filesystem", new_callable=AsyncMock) as mock_fs:
            
            # 模拟所有组件健康
            mock_redis.return_value = {
                "healthy": True,
                "message": "Redis连接正常",
                "type": "redis"
            }
            mock_queue.return_value = {
                "healthy": True,
                "message": "RocketMQ队列正常",
                "type": "rocketmq"
            }
            mock_fs.return_value = {
                "healthy": True,
                "message": "文件系统可写",
                "output_dir": "static/outputs",
                "free_space_gb": 10.5
            }
            
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0  # 0 means success
            assert data["data"]["healthy"] is True
            assert "checks" in data["data"]
            assert "redis" in data["data"]["checks"]
            assert "queue" in data["data"]["checks"]
            assert "filesystem" in data["data"]["checks"]
            assert "response_time_ms" in data["data"]
    
    def test_health_check_redis_unhealthy(self, client):
        """测试Redis不健康的情况"""
        with patch("core.api.v1.health._check_redis", new_callable=AsyncMock) as mock_redis, \
             patch("core.api.v1.health._check_queue", new_callable=AsyncMock) as mock_queue, \
             patch("core.api.v1.health._check_filesystem", new_callable=AsyncMock) as mock_fs:
            
            # 模拟Redis不健康
            mock_redis.return_value = {
                "healthy": False,
                "message": "Redis连接失败",
                "type": "redis",
                "error": "Connection refused"
            }
            mock_queue.return_value = {
                "healthy": True,
                "message": "RocketMQ队列正常",
                "type": "rocketmq"
            }
            mock_fs.return_value = {
                "healthy": True,
                "message": "文件系统可写",
                "output_dir": "static/outputs"
            }
            
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] != 0  # non-0 means error
            assert data["data"]["healthy"] is False
            assert data["data"]["checks"]["redis"]["healthy"] is False
    
    def test_health_check_queue_unhealthy(self, client):
        """测试RocketMQ不健康的情况"""
        with patch("core.api.v1.health._check_redis", new_callable=AsyncMock) as mock_redis, \
             patch("core.api.v1.health._check_queue", new_callable=AsyncMock) as mock_queue, \
             patch("core.api.v1.health._check_filesystem", new_callable=AsyncMock) as mock_fs:
            
            # 模拟RocketMQ不健康
            mock_redis.return_value = {
                "healthy": True,
                "message": "Redis连接正常",
                "type": "redis"
            }
            mock_queue.return_value = {
                "healthy": False,
                "message": "RocketMQ队列不健康",
                "type": "rocketmq"
            }
            mock_fs.return_value = {
                "healthy": True,
                "message": "文件系统可写",
                "output_dir": "static/outputs"
            }
            
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] != 0  # non-0 means error
            assert data["data"]["healthy"] is False
            assert data["data"]["checks"]["queue"]["healthy"] is False
    
    def test_health_check_filesystem_unhealthy(self, client):
        """测试文件系统不健康的情况"""
        with patch("core.api.v1.health._check_redis", new_callable=AsyncMock) as mock_redis, \
             patch("core.api.v1.health._check_queue", new_callable=AsyncMock) as mock_queue, \
             patch("core.api.v1.health._check_filesystem", new_callable=AsyncMock) as mock_fs:
            
            # 模拟文件系统不健康
            mock_redis.return_value = {
                "healthy": True,
                "message": "Redis连接正常",
                "type": "redis"
            }
            mock_queue.return_value = {
                "healthy": True,
                "message": "RocketMQ队列正常",
                "type": "rocketmq"
            }
            mock_fs.return_value = {
                "healthy": False,
                "message": "文件系统写入失败",
                "output_dir": "static/outputs",
                "error": "Permission denied"
            }
            
            response = client.get("/api/v1/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] != 0  # non-0 means error
            assert data["data"]["healthy"] is False
            assert data["data"]["checks"]["filesystem"]["healthy"] is False
    
    def test_readiness_check_ready(self, client):
        """测试就绪检查 - 应用已就绪"""
        with patch("core.api.v1.health._check_redis", new_callable=AsyncMock) as mock_redis, \
             patch("core.api.v1.health._check_queue", new_callable=AsyncMock) as mock_queue, \
             patch("core.api.v1.health._check_filesystem", new_callable=AsyncMock) as mock_fs:
            
            # 模拟所有组件健康
            mock_redis.return_value = {
                "healthy": True,
                "message": "Redis连接正常",
                "type": "redis"
            }
            mock_queue.return_value = {
                "healthy": True,
                "message": "RocketMQ队列正常",
                "type": "rocketmq"
            }
            mock_fs.return_value = {
                "healthy": True,
                "message": "文件系统可写",
                "output_dir": "static/outputs"
            }
            
            response = client.get("/api/v1/health/ready")
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0  # 0 means success
            assert data["data"]["status"] == "ready"
    
    def test_readiness_check_degraded(self, client):
        """测试就绪检查 - 降级模式"""
        with patch("core.api.v1.health._check_redis", new_callable=AsyncMock) as mock_redis, \
             patch("core.api.v1.health._check_queue", new_callable=AsyncMock) as mock_queue, \
             patch("core.api.v1.health._check_filesystem", new_callable=AsyncMock) as mock_fs:
            
            # 模拟Redis降级
            mock_redis.return_value = {
                "healthy": False,
                "message": "Redis客户端未初始化（使用内存存储降级）",
                "degraded": True
            }
            mock_queue.return_value = {
                "healthy": True,
                "message": "RocketMQ队列正常",
                "type": "rocketmq"
            }
            mock_fs.return_value = {
                "healthy": True,
                "message": "文件系统可写",
                "output_dir": "static/outputs"
            }
            
            response = client.get("/api/v1/health/ready")
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0  # 0 means success (degraded mode is still ready)
            assert data["data"]["status"] == "ready"
            assert data["data"]["mode"] == "degraded"
    
    def test_readiness_check_not_ready(self, client):
        """测试就绪检查 - 应用未就绪"""
        with patch("core.api.v1.health._check_redis", new_callable=AsyncMock) as mock_redis, \
             patch("core.api.v1.health._check_queue", new_callable=AsyncMock) as mock_queue, \
             patch("core.api.v1.health._check_filesystem", new_callable=AsyncMock) as mock_fs:
            
            # 模拟文件系统不可用（非降级）
            mock_redis.return_value = {
                "healthy": True,
                "message": "Redis连接正常",
                "type": "redis"
            }
            mock_queue.return_value = {
                "healthy": True,
                "message": "RocketMQ队列正常",
                "type": "rocketmq"
            }
            mock_fs.return_value = {
                "healthy": False,
                "message": "文件系统写入失败",
                "output_dir": "static/outputs",
                "error": "Permission denied"
            }
            
            response = client.get("/api/v1/health/ready")
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] != 0  # non-0 means error
            assert data["data"]["status"] == "not_ready"


class TestHealthCheckFunctions:
    """健康检查辅助函数测试类"""
    
    @pytest.mark.asyncio
    async def test_check_redis_success(self):
        """测试Redis检查成功"""
        from core.api.v1.health import _check_redis
        
        with patch("core.api.v1.health.get_redis_client") as mock_get_client:
            # 模拟Redis客户端
            mock_client = MagicMock()
            mock_client.ping = AsyncMock(return_value=True)
            mock_get_client.return_value = mock_client
            
            result = await _check_redis()
            
            assert result["healthy"] is True
            assert result["message"] == "Redis连接正常"
            assert result["type"] == "redis"
    
    @pytest.mark.asyncio
    async def test_check_redis_not_initialized(self):
        """测试Redis未初始化（降级模式）"""
        from core.api.v1.health import _check_redis
        
        with patch("core.api.v1.health.get_redis_client") as mock_get_client:
            # 模拟Redis客户端未初始化
            mock_get_client.return_value = None
            
            result = await _check_redis()
            
            assert result["healthy"] is False
            assert result["degraded"] is True
            assert "降级" in result["message"]
    
    @pytest.mark.asyncio
    async def test_check_redis_ping_failed(self):
        """测试Redis ping失败"""
        from core.api.v1.health import _check_redis
        
        with patch("core.api.v1.health.get_redis_client") as mock_get_client:
            # 模拟Redis ping失败
            mock_client = MagicMock()
            mock_client.ping = AsyncMock(return_value=False)
            mock_get_client.return_value = mock_client
            
            result = await _check_redis()
            
            assert result["healthy"] is False
            assert "ping失败" in result["message"]
    
    @pytest.mark.asyncio
    async def test_check_redis_exception(self):
        """测试Redis检查异常"""
        from core.api.v1.health import _check_redis
        
        with patch("core.api.v1.health.get_redis_client") as mock_get_client:
            # 模拟Redis异常
            mock_client = MagicMock()
            mock_client.ping = AsyncMock(side_effect=Exception("Connection error"))
            mock_get_client.return_value = mock_client
            
            result = await _check_redis()
            
            assert result["healthy"] is False
            assert "error" in result
    
    @pytest.mark.asyncio
    async def test_check_queue_success(self):
        """测试队列检查成功"""
        from core.api.v1.health import _check_queue
        
        with patch("core.api.v1.health.get_rocketmq_manager") as mock_get_manager:
            # 模拟RocketMQ管理器
            mock_manager = MagicMock()
            mock_manager._is_initialized = True
            mock_manager.is_healthy.return_value = True
            mock_get_manager.return_value = mock_manager
            
            result = await _check_queue()
            
            assert result["healthy"] is True
            assert result["message"] == "RocketMQ队列正常"
            assert result["type"] == "rocketmq"
    
    @pytest.mark.asyncio
    async def test_check_queue_not_initialized(self):
        """测试队列未初始化（降级模式）"""
        from core.api.v1.health import _check_queue
        
        with patch("core.api.v1.health.get_rocketmq_manager") as mock_get_manager:
            # 模拟RocketMQ未初始化
            mock_manager = MagicMock()
            mock_manager._is_initialized = False
            mock_get_manager.return_value = mock_manager
            
            result = await _check_queue()
            
            assert result["healthy"] is False
            assert result["degraded"] is True
            assert "降级" in result["message"]
    
    @pytest.mark.asyncio
    async def test_check_queue_unhealthy(self):
        """测试队列不健康"""
        from core.api.v1.health import _check_queue
        
        with patch("core.api.v1.health.get_rocketmq_manager") as mock_get_manager:
            # 模拟RocketMQ不健康
            mock_manager = MagicMock()
            mock_manager._is_initialized = True
            mock_manager.is_healthy.return_value = False
            mock_get_manager.return_value = mock_manager
            
            result = await _check_queue()
            
            assert result["healthy"] is False
            assert "不健康" in result["message"]
    
    @pytest.mark.asyncio
    async def test_check_filesystem_success(self):
        """测试文件系统检查成功"""
        from core.api.v1.health import _check_filesystem
        
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("core.api.v1.health.get_config") as mock_get_config:
                # 模拟配置
                mock_config = MagicMock()
                mock_storage = MagicMock()
                mock_storage.output_dir = temp_dir
                mock_config.file_storage = mock_storage
                mock_get_config.return_value = mock_config
                
                result = await _check_filesystem()
                
                assert result["healthy"] is True
                assert result["message"] == "文件系统可写"
                assert "free_space_gb" in result
    
    @pytest.mark.asyncio
    async def test_check_filesystem_write_failed(self):
        """测试文件系统写入失败"""
        from core.api.v1.health import _check_filesystem
        
        with patch("core.api.v1.health.get_config") as mock_get_config, \
             patch("builtins.open", side_effect=IOError("Permission denied")):
            # 模拟配置
            mock_config = MagicMock()
            mock_storage = MagicMock()
            mock_storage.output_dir = "/invalid/path"
            mock_config.file_storage = mock_storage
            mock_get_config.return_value = mock_config
            
            # 确保目录存在（但不能写入）
            with patch("os.makedirs"):
                result = await _check_filesystem()
            
            assert result["healthy"] is False
            assert "写入失败" in result["message"]

