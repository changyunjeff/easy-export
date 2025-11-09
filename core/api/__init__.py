from core.router.router_registry import router_registry, RouterType
from .v1 import (
    example_router,
    example_private_router,
    template_router,
    export_router,
    validate_router,
    stats_router,
)

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

# 注册模板管理路由
router_registry.add_router(
    router=template_router,
    router_type=RouterType.API | RouterType.PUBLIC,
    priority=20,
    name="templates",
    description="Template management API"
)

# 注册导出路由
router_registry.add_router(
    router=export_router,
    router_type=RouterType.API | RouterType.PUBLIC,
    priority=20,
    name="export",
    description="Export API"
)

# 注册校验路由
router_registry.add_router(
    router=validate_router,
    router_type=RouterType.API | RouterType.PUBLIC,
    priority=20,
    name="validate",
    description="Validation API"
)

# 注册统计路由
router_registry.add_router(
    router=stats_router,
    router_type=RouterType.API | RouterType.PUBLIC,
    priority=20,
    name="stats",
    description="Statistics API"
)
