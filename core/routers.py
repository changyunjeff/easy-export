from fastapi import FastAPI
from core.router import router_registry, RouterType
from core.router import PrefixValidator, AdminRouteValidator
from core.config import get_config


def setup_routers(app: FastAPI):
    """
    注册所有路由到FastAPI应用
    
    使用全局单例路由注册器，支持：
    - 路由类型分类
    - 优先级排序
    - 验证阶段
    """
    # 导入统一路由聚合模块，触发路由注册到全局注册器
    import core.api  # noqa: F401
    
    # 从配置中获取 API prefix
    config = get_config()
    api_config = getattr(config, "api", None)
    api_prefix = "/api"  # 默认值
    if api_config and api_config.prefix:
        # 提取基础前缀（例如 "/api/v1" -> "/api"）
        parts = [p for p in api_config.prefix.split("/") if p]
        if len(parts) >= 1:
            api_prefix = f"/{parts[0]}"
    
    # 配置验证器（可选）
    # 为API类型路由添加前缀验证
    router_registry.register_validator(
        RouterType.API,
        PrefixValidator(required_prefix=api_prefix)
    )
    
    # 为管理员路由添加安全验证
    router_registry.register_validator(
        RouterType.ADMIN,
        AdminRouteValidator()
    )
    
    # 注册所有路由
    stats = router_registry.register_all(app)
    
    return stats
