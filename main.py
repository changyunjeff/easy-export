from __future__ import annotations

import os
import logging
from contextlib import asynccontextmanager

from core import get_config, setup_routers
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.middlewares import LoggingMiddleware
from core.utils import is_debug
from core.workers import worker_count
from dotenv import load_dotenv


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 生命周期钩子
    - yield 之前：应用启动时执行（初始化资源）
    - yield 之后：应用关闭时执行（清理资源）
    """
    config = get_config()
    logger = logging.getLogger(__name__)
    
    # ========== 启动阶段：初始化资源 ==========
    logger.info("Starting application initialization...")
    
    # 阶段 1: 初始化 Redis（如果启用）或使用内存存储回退
    redis_config = getattr(config, "redis", None)
    if redis_config and getattr(redis_config, "enabled", False):
        try:
            from core.redis import init_redis, is_using_memory_store
            init_redis(
                host=redis_config.host,
                port=redis_config.port,
                db=redis_config.db,
                password=redis_config.password,
                decode_responses=redis_config.decode_responses,
                max_connections=redis_config.max_connections,
                socket_connect_timeout=redis_config.socket_connect_timeout,
                socket_timeout=redis_config.socket_timeout,
                fallback_to_memory=True,  # 启用自动回退到内存存储
            )
            if is_using_memory_store():
                logger.warning("Redis connection failed, using in-memory storage (non-persistent)")
            else:
                logger.info("Redis initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis: {e}. Using in-memory storage as fallback.")
    else:
        # 如果配置中未启用 Redis，直接使用内存存储
        try:
            from core.redis import init_memory_store
            init_memory_store()
            logger.info("Redis not enabled in config, using in-memory storage (non-persistent)")
        except Exception as e:
            logger.warning(f"Failed to initialize in-memory storage: {e}")
    
    # 阶段 2: 初始化 Email 服务（如果启用）
    email_config = getattr(config, "email", None)
    if email_config and getattr(email_config, "enabled", False):
        try:
            from core.email import init_email, get_email_client
            smtp_config = getattr(email_config, "smtp", None)
            if smtp_config:
                template_dir = getattr(smtp_config, "template_dir", None)
                success = init_email(
                    host=smtp_config.host,
                    port=smtp_config.port,
                    user=smtp_config.user,
                    password=os.getenv("SMTP_PASSWORD"),
                    tls=smtp_config.tls,
                )
                if success:
                    # 初始化邮件客户端（用于模板支持）
                    if template_dir:
                        get_email_client(template_dir=template_dir)
                    logger.info("Email service initialized successfully")
                else:
                    logger.warning("Email service initialization failed")
            else:
                logger.warning("Email service enabled but SMTP config is missing")
        except Exception as e:
            logger.warning(f"Failed to initialize Email service: {e}")
    
    logger.info("Application initialization completed")
    
    # 应用运行中...
    yield
    
    # ========== 关闭阶段：清理资源 ==========
    logger.info("Starting application shutdown...")
    
    # 清理 Email 服务
    try:
        from core.email import close_email
        close_email()
        logger.info("Email service closed")
    except Exception as e:
        logger.warning(f"Error closing Email service: {e}")
    
    # 清理 Redis 连接
    try:
        from core.redis import close_redis
        close_redis()
        logger.info("Redis connection closed")
    except Exception as e:
        logger.warning(f"Error closing Redis connection: {e}")
    
    logger.info("Application shutdown completed")


def create_app() -> FastAPI:
    config = get_config()
    logger = logging.getLogger(__name__)

    # 根据配置初始化日志（需要在其他初始化之前完成）
    try:
        from core.logging import setup_logging
        setup_logging(getattr(config, "logging", None))
    except Exception as e:
        # 兜底：最简日志配置，避免启动失败
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

    contact_payload = None
    if getattr(config.app, "contact", None):
        if isinstance(config.app.contact, str):
            contact_payload = {"email": config.app.contact}
        elif isinstance(config.app.contact, dict):
            contact_payload = config.app.contact

    app = FastAPI(
        title=config.app.title,
        description=config.app.description,
        version=config.app.version,
        contact=contact_payload,
        lifespan=lifespan,  # 使用生命周期钩子
    )

    # 配置 CORS 中间件（如果启用）
    api_config = getattr(config, "api", None)
    if api_config and api_config.cors and api_config.cors.enabled:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=api_config.cors.allow_origins,
            allow_credentials=api_config.cors.allow_credentials,
            allow_methods=["*"],
            allow_headers=api_config.cors.allow_headers,
            expose_headers=api_config.cors.expose_headers,
            max_age=api_config.cors.max_age,
        )
        logger.info(f"CORS middleware enabled with origins: {api_config.cors.allow_origins}")

    # 添加日志中间件
    app.add_middleware(LoggingMiddleware)

    # mount static files
    static_dir = "static"
    if not os.path.exists(static_dir):
        os.makedirs(static_dir)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    # end mount

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    setup_routers(app)

    return app

if __name__ == "__main__":
    load_dotenv()
    import uvicorn
    cfg = get_config()
    # 确保子进程/重载时日志也已配置
    try:
        from core.logging import setup_logging
        setup_logging(getattr(cfg, "logging", None))
    except Exception:
        pass
    uvicorn.run(
        "main:create_app",
        host=cfg.app.host,
        port=cfg.app.port,
        reload=is_debug(cfg.app.mode), # based on mode, if in dev mode, reload
        factory=True,
        workers=worker_count(),         # will not work in dev mode
        log_config=None,  # 禁用 uvicorn 的默认日志配置，使用我们自己的日志配置
    )
