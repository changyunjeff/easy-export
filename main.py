from __future__ import annotations

import os
import logging

from core import get_config, setup_routers
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.middlewares import LoggingMiddleware
from core.utils import is_debug
from core.workers import worker_count
from dotenv import load_dotenv


def create_app() -> FastAPI:
    config = get_config()

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
