"""
路由验证器实现
提供各种路由验证逻辑
"""
from typing import Optional, Tuple
from core.router.router_registry import RouterValidator, RouterMetadata, RouterType


class PrefixValidator(RouterValidator):
    """前缀验证器：确保路由有正确的前缀"""
    
    def __init__(self, required_prefix: Optional[str] = None):
        """
        Args:
            required_prefix: 必需的前缀，如果为None则不检查
        """
        self.required_prefix = required_prefix
    
    def validate(self, metadata: RouterMetadata) -> Tuple[bool, Optional[str]]:
        if self.required_prefix is None:
            return True, None
        
        router = metadata.router
        if not router.prefix or not router.prefix.startswith(self.required_prefix):
            return False, f"路由前缀必须以 '{self.required_prefix}' 开头"
        
        return True, None


class TagValidator(RouterValidator):
    """标签验证器：确保路由有必需的标签"""
    
    def __init__(self, required_tags: list[str]):
        """
        Args:
            required_tags: 必需的标签列表
        """
        self.required_tags = required_tags
    
    def validate(self, metadata: RouterMetadata) -> Tuple[bool, Optional[str]]:
        router = metadata.router
        router_tags = set(router.tags or [])
        required_tags = set(self.required_tags)
        
        if not required_tags.issubset(router_tags):
            missing = required_tags - router_tags
            return False, f"路由缺少必需的标签: {', '.join(missing)}"
        
        return True, None


class AdminRouteValidator(RouterValidator):
    """管理员路由验证器：确保管理员路由有安全配置"""
    
    def validate(self, metadata: RouterMetadata) -> Tuple[bool, Optional[str]]:
        if metadata.router_type != RouterType.ADMIN:
            return True, None
        
        router = metadata.router
        # 检查是否有依赖项（通常用于认证）
        if not router.dependencies:
            return False, "管理员路由必须配置认证依赖项"
        
        return True, None


class MetadataValidator(RouterValidator):
    """元数据验证器：检查路由元数据是否符合要求"""
    
    def __init__(self, required_keys: list[str]):
        """
        Args:
            required_keys: 必需的元数据键列表
        """
        self.required_keys = required_keys
    
    def validate(self, metadata: RouterMetadata) -> Tuple[bool, Optional[str]]:
        missing_keys = [key for key in self.required_keys if key not in metadata.metadata]
        if missing_keys:
            return False, f"路由缺少必需的元数据: {', '.join(missing_keys)}"
        
        return True, None

