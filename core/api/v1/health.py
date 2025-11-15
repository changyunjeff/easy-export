"""
健康检查接口
提供应用整体健康检查功能
"""

from fastapi import APIRouter
from typing import Dict, Any
import logging
import os
import shutil
import time
from datetime import datetime

from core.response import success_response, error_response
from core.utils import get_api_prefix
from core.redis import get_redis_client
from core.rocketmq import get_rocketmq_manager
from core.config import get_config

logger = logging.getLogger(__name__)

health_router = APIRouter(
    prefix=f"{get_api_prefix()}/health",
    tags=["health"],
)


@health_router.get("", summary="应用健康检查")
async def health_check() -> Dict[str, Any]:
    """
    检查应用整体健康状态
    
    检查项包括：
    - Redis连接状态
    - RocketMQ队列状态
    - 文件系统可写性
    - 系统资源状态
    
    Returns:
        健康状态信息
    """
    start_time = time.time()
    health_status = {
        "healthy": True,
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # 1. 检查Redis连接
    redis_healthy = await _check_redis()
    health_status["checks"]["redis"] = redis_healthy
    if not redis_healthy["healthy"]:
        health_status["healthy"] = False
    
    # 2. 检查RocketMQ队列
    queue_healthy = await _check_queue()
    health_status["checks"]["queue"] = queue_healthy
    if not queue_healthy["healthy"]:
        health_status["healthy"] = False
    
    # 3. 检查文件系统
    fs_healthy = await _check_filesystem()
    health_status["checks"]["filesystem"] = fs_healthy
    if not fs_healthy["healthy"]:
        health_status["healthy"] = False
    
    # 4. 计算响应时间
    elapsed_ms = (time.time() - start_time) * 1000
    health_status["response_time_ms"] = round(elapsed_ms, 2)
    
    if health_status["healthy"]:
        return success_response(
            data=health_status,
            message="应用健康检查通过"
        )
    else:
        return error_response(
            message="应用健康检查失败，部分组件不可用",
            error_code="UNHEALTHY",
            data=health_status
        )


async def _check_redis() -> Dict[str, Any]:
    """检查Redis连接状态"""
    try:
        redis_client = get_redis_client()
        if not redis_client:
            return {
                "healthy": False,
                "message": "Redis客户端未初始化（使用内存存储降级）",
                "degraded": True
            }
        
        # 尝试ping Redis
        result = await redis_client.ping()
        if result:
            return {
                "healthy": True,
                "message": "Redis连接正常",
                "type": "redis"
            }
        else:
            return {
                "healthy": False,
                "message": "Redis ping失败",
                "type": "redis"
            }
            
    except Exception as e:
        logger.error(f"Redis health check failed: {str(e)}")
        return {
            "healthy": False,
            "message": f"Redis检查失败: {str(e)}",
            "type": "redis",
            "error": str(e)
        }


async def _check_queue() -> Dict[str, Any]:
    """检查RocketMQ队列状态"""
    try:
        manager = get_rocketmq_manager()
        if not manager or not manager._is_initialized:
            return {
                "healthy": False,
                "message": "RocketMQ未初始化（使用内存队列降级）",
                "degraded": True
            }
        
        # 检查队列是否健康
        is_healthy = manager.is_healthy()
        if is_healthy:
            return {
                "healthy": True,
                "message": "RocketMQ队列正常",
                "type": "rocketmq"
            }
        else:
            return {
                "healthy": False,
                "message": "RocketMQ队列不健康",
                "type": "rocketmq"
            }
            
    except Exception as e:
        logger.error(f"Queue health check failed: {str(e)}")
        return {
            "healthy": False,
            "message": f"队列检查失败: {str(e)}",
            "type": "rocketmq",
            "error": str(e)
        }


async def _check_filesystem() -> Dict[str, Any]:
    """检查文件系统可写性"""
    try:
        # 获取输出目录
        cfg = get_config()
        output_dir = getattr(cfg.file_storage, "output_dir", "static/outputs")
        
        # 确保目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        # 尝试写入测试文件
        test_file = os.path.join(output_dir, ".health_check_test")
        try:
            with open(test_file, "w") as f:
                f.write("health check test")
            
            # 读取验证
            with open(test_file, "r") as f:
                content = f.read()
            
            # 删除测试文件
            os.remove(test_file)
            
            if content == "health check test":
                # 获取磁盘空间信息（跨平台）
                usage = shutil.disk_usage(output_dir)
                free_space_gb = usage.free / (1024 ** 3)
                
                return {
                    "healthy": True,
                    "message": "文件系统可写",
                    "output_dir": output_dir,
                    "free_space_gb": round(free_space_gb, 2)
                }
            else:
                return {
                    "healthy": False,
                    "message": "文件系统读写验证失败",
                    "output_dir": output_dir
                }
                
        except IOError as e:
            return {
                "healthy": False,
                "message": f"文件系统写入失败: {str(e)}",
                "output_dir": output_dir,
                "error": str(e)
            }
            
    except Exception as e:
        logger.error(f"Filesystem health check failed: {str(e)}")
        return {
            "healthy": False,
            "message": f"文件系统检查失败: {str(e)}",
            "error": str(e)
        }


@health_router.get("/live", summary="存活检查")
async def liveness_check() -> Dict[str, Any]:
    """
    Kubernetes存活检查端点
    仅检查应用是否在运行，不检查依赖服务
    
    Returns:
        简单的存活状态
    """
    return success_response(
        data={
            "status": "alive",
            "timestamp": datetime.now().isoformat()
        },
        message="应用正在运行"
    )


@health_router.get("/ready", summary="就绪检查")
async def readiness_check() -> Dict[str, Any]:
    """
    Kubernetes就绪检查端点
    检查应用是否准备好接收流量
    
    Returns:
        就绪状态信息
    """
    # 执行基本的健康检查
    health_result = await health_check()
    
    if health_result.get("code") == 0:  # code == 0 means healthy
        return success_response(
            data={
                "status": "ready",
                "timestamp": datetime.now().isoformat()
            },
            message="应用已就绪"
        )
    else:
        # 允许降级模式（Redis或RocketMQ不可用时仍然可以服务）
        checks = health_result.get("data", {}).get("checks", {})
        degraded = any(
            check.get("degraded", False)
            for check in checks.values()
        )
        
        if degraded:
            return success_response(
                data={
                    "status": "ready",
                    "mode": "degraded",
                    "timestamp": datetime.now().isoformat(),
                    "message": "应用运行在降级模式"
                },
                message="应用已就绪（降级模式）"
            )
        else:
            return error_response(
                message="应用未就绪",
                error_code="NOT_READY",
                data={
                    "status": "not_ready",
                    "timestamp": datetime.now().isoformat()
                }
            )

