"""
RocketMQ队列监控API最小化测试

测试RocketMQ队列监控API的基本路由功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient

from core.rocketmq.manager import RocketMQManager
from core.rocketmq.exceptions import RocketMQException
from core.response import success_response, error_response


# 创建简化的路由用于测试
def create_test_router():
    """创建测试用的简化路由"""
    router = APIRouter(prefix="/api/v1/queue", tags=["队列监控"])
    
    @router.get("/status")
    async def get_queue_status():
        """获取队列状态"""
        try:
            from core.rocketmq import get_rocketmq_manager
            manager = get_rocketmq_manager()
            status = manager.get_queue_status()
            return success_response(data=status, message="获取队列状态成功")
        except RocketMQException as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"RocketMQ错误: {str(e)}")
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"获取队列状态失败: {str(e)}")
    
    @router.get("/health")
    async def get_queue_health():
        """队列健康检查"""
        try:
            from core.rocketmq import get_rocketmq_manager
            manager = get_rocketmq_manager()
            
            if not manager._is_initialized:
                return success_response(
                    data={"healthy": False, "message": "RocketMQ manager not initialized"},
                    message="队列健康检查完成"
                )
            
            healthy = manager.is_healthy()
            health_data = {"healthy": healthy}
            
            if manager.monitor:
                health_status = manager.monitor.get_health_status()
                health_data.update(health_status)
            
            return success_response(data=health_data, message="队列健康检查完成")
        except RocketMQException as e:
            health_data = {"healthy": False, "error": str(e)}
            return success_response(data=health_data, message="队列健康检查完成")
        except Exception as e:
            health_data = {"healthy": False, "error": str(e)}
            return success_response(data=health_data, message="队列健康检查完成")
    
    @router.post("/consumer/restart")
    async def restart_consumer():
        """重启消费者"""
        try:
            from core.rocketmq import get_rocketmq_manager
            manager = get_rocketmq_manager()
            manager.restart_consumer()
            return success_response(message="消费者重启成功")
        except RocketMQException as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"RocketMQ错误: {str(e)}")
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"重启消费者失败: {str(e)}")
    
    return router


class TestQueueAPIMinimal:
    """队列监控API最小化测试类"""
    
    @pytest.fixture
    def app(self):
        """创建FastAPI应用"""
        app = FastAPI()
        router = create_test_router()
        app.include_router(router)
        return app
    
    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_manager(self):
        """模拟RocketMQ管理器"""
        manager = Mock(spec=RocketMQManager)
        manager._is_initialized = True
        return manager
    
    def test_get_queue_status_success(self, client, mock_manager):
        """测试获取队列状态成功"""
        expected_status = {
            "topic": "test_topic",
            "health": {"healthy": True}
        }
        mock_manager.get_queue_status.return_value = expected_status

        with patch('core.rocketmq.get_rocketmq_manager', return_value=mock_manager):
            response = client.get("/api/v1/queue/status")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"] == expected_status
            
    def test_get_queue_status_exception(self, client, mock_manager):
        """测试获取队列状态异常"""
        mock_manager.get_queue_status.side_effect = RocketMQException("RocketMQ error")

        with patch('core.rocketmq.get_rocketmq_manager', return_value=mock_manager):
            response = client.get("/api/v1/queue/status")

            assert response.status_code == 500
            data = response.json()
            assert "RocketMQ error" in data["detail"]
            
    def test_get_queue_health_success(self, client, mock_manager):
        """测试队列健康检查成功"""
        mock_manager._is_initialized = True
        mock_manager.is_healthy.return_value = True
        mock_manager.monitor = Mock()
        mock_manager.monitor.get_health_status.return_value = {
            "connection_status": True,
            "total_lag": 0
        }

        with patch('core.rocketmq.get_rocketmq_manager', return_value=mock_manager):
            response = client.get("/api/v1/queue/health")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["healthy"] is True
            assert data["data"]["connection_status"] is True
            
    def test_get_queue_health_not_initialized(self, client, mock_manager):
        """测试队列健康检查未初始化"""
        mock_manager._is_initialized = False

        with patch('core.rocketmq.get_rocketmq_manager', return_value=mock_manager):
            response = client.get("/api/v1/queue/health")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert data["data"]["healthy"] is False
            assert "not initialized" in data["data"]["message"]
            
    def test_restart_consumer_success(self, client, mock_manager):
        """测试重启消费者成功"""
        with patch('core.rocketmq.get_rocketmq_manager', return_value=mock_manager):
            response = client.post("/api/v1/queue/consumer/restart")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 0
            assert "重启成功" in data["msg"]
            mock_manager.restart_consumer.assert_called_once()
            
    def test_restart_consumer_exception(self, client, mock_manager):
        """测试重启消费者异常"""
        mock_manager.restart_consumer.side_effect = RocketMQException("Restart error")

        with patch('core.rocketmq.get_rocketmq_manager', return_value=mock_manager):
            response = client.post("/api/v1/queue/consumer/restart")

            assert response.status_code == 500
            data = response.json()
            assert "Restart error" in data["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
