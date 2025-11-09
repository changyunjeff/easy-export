from __future__ import annotations

import os
import logging

from core import get_config, setup_routers
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from core.middlewares import LoggingMiddleware
from core.utils import is_debug
from core.workers import worker_count
from dotenv import load_dotenv


def create_app() -> FastAPI:
    config = get_config()
    logger = logging.getLogger(__name__)

    # 根据配置初始化日志
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

    # 根据配置初始化 Redis（如果启用）或使用内存存储回退
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
            # 即使异常，init_redis 也会回退到内存存储（已在 init_redis 内部处理）
            # 如果 init_redis 已经回退，这里不需要再次调用
    else:
        # 如果配置中未启用 Redis，直接使用内存存储
        try:
            from core.redis import init_memory_store
            init_memory_store()
            logger.info("Redis not enabled in config, using in-memory storage (non-persistent)")
        except Exception as e:
            logger.warning(f"Failed to initialize in-memory storage: {e}")

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
    )
