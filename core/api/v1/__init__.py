# 导入路由模块，触发自动注册
from .examples import example_router, example_private_router
from .templates import template_router
from .export import export_router
from .validate import validate_router
from .stats import stats_router

__all__ = [
    "example_router",
    "example_private_router",
    "template_router",
    "export_router",
    "validate_router",
    "stats_router",
]
