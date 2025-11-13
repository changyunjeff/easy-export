"""
队列监控API接口

提供RocketMQ队列的实时监控和管理接口。
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, Optional
import logging

from core.rocketmq import get_rocketmq_manager, RocketMQException
from core.response import success_response, error_response
from core.utils import get_api_prefix

logger = logging.getLogger(__name__)

router = APIRouter(prefix=f"{get_api_prefix()}/queue", tags=["队列监控"])


@router.get("/status", summary="获取队列状态")
async def get_queue_status() -> Dict[str, Any]:
    """
    获取RocketMQ队列的实时状态信息
    
    Returns:
        队列状态信息，包括：
        - 连接状态
        - 消息统计
        - 消费者延迟
        - 组件状态
    """
    try:
        manager = get_rocketmq_manager()
        status = manager.get_queue_status()
        
        return success_response(
            data=status,
            message="获取队列状态成功"
        )
        
    except RocketMQException as e:
        logger.error(f"RocketMQ error getting queue status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RocketMQ错误: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error getting queue status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取队列状态失败: {str(e)}")


@router.get("/health", summary="队列健康检查")
async def get_queue_health() -> Dict[str, Any]:
    """
    检查RocketMQ队列的健康状态
    
    Returns:
        健康状态信息
    """
    try:
        manager = get_rocketmq_manager()
        
        if not manager._is_initialized:
            return error_response(
                message="RocketMQ未初始化",
                error_code="NOT_INITIALIZED"
            )
            
        is_healthy = manager.is_healthy()
        health_details = manager.monitor.get_health_status() if manager.monitor else {}
        
        return success_response(
            data={
                "healthy": is_healthy,
                "details": health_details
            },
            message="健康检查完成"
        )
        
    except RocketMQException as e:
        logger.error(f"RocketMQ error in health check: {str(e)}")
        return error_response(
            message=f"RocketMQ健康检查失败: {str(e)}",
            error_code="HEALTH_CHECK_FAILED"
        )
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return error_response(
            message=f"健康检查失败: {str(e)}",
            error_code="HEALTH_CHECK_ERROR"
        )


@router.get("/metrics", summary="获取性能指标")
async def get_queue_metrics() -> Dict[str, Any]:
    """
    获取RocketMQ队列的性能指标
    
    Returns:
        性能指标信息，包括：
        - 吞吐量统计
        - 延迟指标
        - 错误率
    """
    try:
        manager = get_rocketmq_manager()
        metrics = manager.get_performance_metrics()
        
        return success_response(
            data=metrics,
            message="获取性能指标成功"
        )
        
    except RocketMQException as e:
        logger.error(f"RocketMQ error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RocketMQ错误: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error getting metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")


@router.get("/monitoring/export", summary="导出监控数据")
async def export_monitoring_data() -> Dict[str, Any]:
    """
    导出完整的监控数据为JSON格式
    
    Returns:
        JSON格式的监控数据
    """
    try:
        manager = get_rocketmq_manager()
        monitoring_json = manager.export_monitoring_data()
        
        return success_response(
            data={
                "monitoring_data": monitoring_json,
                "export_time": manager.monitor.get_monitor_metrics().timestamp.isoformat()
            },
            message="导出监控数据成功"
        )
        
    except RocketMQException as e:
        logger.error(f"RocketMQ error exporting monitoring data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RocketMQ错误: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error exporting monitoring data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"导出监控数据失败: {str(e)}")


@router.post("/consumer/restart", summary="重启消费者")
async def restart_consumer() -> Dict[str, Any]:
    """
    重启RocketMQ消费者
    
    Returns:
        重启结果
    """
    try:
        manager = get_rocketmq_manager()
        manager.restart_consumer()
        
        return success_response(
            message="消费者重启成功"
        )
        
    except RocketMQException as e:
        logger.error(f"RocketMQ error restarting consumer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RocketMQ错误: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error restarting consumer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重启消费者失败: {str(e)}")


@router.post("/producer/restart", summary="重启生产者")
async def restart_producer() -> Dict[str, Any]:
    """
    重启RocketMQ生产者
    
    Returns:
        重启结果
    """
    try:
        manager = get_rocketmq_manager()
        manager.restart_producer()
        
        return success_response(
            message="生产者重启成功"
        )
        
    except RocketMQException as e:
        logger.error(f"RocketMQ error restarting producer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RocketMQ错误: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error restarting producer: {str(e)}")
        raise HTTPException(status_code=500, detail=f"重启生产者失败: {str(e)}")


@router.get("/consumer/lag", summary="获取消费者延迟")
async def get_consumer_lag() -> Dict[str, Any]:
    """
    获取消费者的延迟信息
    
    Returns:
        消费者延迟信息
    """
    try:
        manager = get_rocketmq_manager()
        
        if not manager.monitor:
            raise HTTPException(status_code=500, detail="监控器未初始化")
            
        connection_info = manager.connection.get_connection_info()
        consumer_lag = manager.monitor.get_consumer_lag(
            connection_info.consumer_group,
            connection_info.topic
        )
        total_lag = manager.monitor.get_total_lag(
            connection_info.consumer_group,
            connection_info.topic
        )
        
        return success_response(
            data={
                "consumer_group": connection_info.consumer_group,
                "topic": connection_info.topic,
                "queue_lag": consumer_lag,
                "total_lag": total_lag
            },
            message="获取消费者延迟成功"
        )
        
    except RocketMQException as e:
        logger.error(f"RocketMQ error getting consumer lag: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RocketMQ错误: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error getting consumer lag: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取消费者延迟失败: {str(e)}")


@router.get("/topic/stats", summary="获取主题统计")
async def get_topic_stats() -> Dict[str, Any]:
    """
    获取主题的统计信息
    
    Returns:
        主题统计信息
    """
    try:
        manager = get_rocketmq_manager()
        
        if not manager.monitor:
            raise HTTPException(status_code=500, detail="监控器未初始化")
            
        connection_info = manager.connection.get_connection_info()
        topic_stats = manager.monitor.get_topic_stats(connection_info.topic)
        
        return success_response(
            data={
                "topic": topic_stats.topic,
                "total_messages": topic_stats.total_messages,
                "total_queues": topic_stats.total_queues,
                "producer_count": topic_stats.producer_count,
                "consumer_groups": topic_stats.consumer_groups,
                "last_update": topic_stats.last_update.isoformat()
            },
            message="获取主题统计成功"
        )
        
    except RocketMQException as e:
        logger.error(f"RocketMQ error getting topic stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"RocketMQ错误: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error getting topic stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取主题统计失败: {str(e)}")
