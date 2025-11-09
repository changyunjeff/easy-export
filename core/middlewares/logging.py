from __future__ import annotations

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# 日志记录器
app_logger = logging.getLogger(__name__)
access_logger = logging.getLogger("access")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    
    在请求处理前后记录日志，包括：
    - 请求方法、路径、客户端IP
    - 请求处理时间
    - 响应状态码
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 记录请求开始时间
        start_time = time.time()
        
        # 获取客户端IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 获取请求信息
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        
        # 记录请求开始日志（接入 access 记录器）
        access_logger.info(
            f"📥 请求开始 - {method} {path}"
            f"{'?' + query_params if query_params else ''} | "
            f"客户端IP: {client_ip}"
        )
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录响应日志（接入 access 记录器）
            access_logger.info(
                f"📤 请求完成 - {method} {path} | "
                f"状态码: {response.status_code} | "
                f"处理时间: {process_time:.3f}s | "
                f"客户端IP: {client_ip}"
            )
            
            # 添加处理时间到响应头（可选）
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录错误日志（应用日志记录器）
            app_logger.error(
                f"❌ 请求异常 - {method} {path} | "
                f"错误: {str(e)} | "
                f"处理时间: {process_time:.3f}s | "
                f"客户端IP: {client_ip}",
                exc_info=True
            )
            
            # 重新抛出异常，让FastAPI处理
            raise
        
