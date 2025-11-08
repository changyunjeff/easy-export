from core.router.router_registry import router_registry, RouterType
from .v1 import example_router

# 注册到全局路由注册器
router_registry.add_router(
    router=example_router,
    router_type=RouterType.API,
    priority=10,
    name="api",
    description="Unified API entrypoint"
)

