from core.router.router_registry import router_registry, RouterType
from .v1 import example_router, example_private_router

# 注册到全局路由注册器
router_registry.add_router(
    router=example_router,
    router_type=RouterType.API | RouterType.PUBLIC,
    priority=10,
    name="example",
    description="Unified API entrypoint"
)

router_registry.add_router(
    router=example_private_router,
    router_type=RouterType.API | RouterType.PRIVATE,
    priority=10,
    name="example-private",
    description="Private API routes"
)
