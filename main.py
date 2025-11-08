from __future__ import annotations

import os

from core import get_config, setup_routers
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.utils import is_debug
from core.workers import worker_count
from dotenv import load_dotenv


def create_app() -> FastAPI:
    config = get_config()

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
    uvicorn.run(
        "main:create_app",
        host=cfg.app.host,
        port=cfg.app.port,
        reload=is_debug(cfg.app.mode), # based on mode, if in dev mode, reload
        factory=True,
        workers=worker_count(),         # will not work in dev mode
    )
