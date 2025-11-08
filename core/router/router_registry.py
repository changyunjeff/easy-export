"""
全局单例路由注册器
负责管理项目中所有路由的注册，支持路由类型、优先级和验证阶段
"""
from enum import Enum
from typing import Optional, Callable, Dict, List, Any, Tuple
from dataclasses import dataclass, field
from threading import Lock
from fastapi import APIRouter, FastAPI


class RouterType(str, Enum):
    """路由类型枚举"""
    PUBLIC = "public"          # 公开路由，无需认证
    PRIVATE = "private"        # 私有路由，需要认证
    ADMIN = "admin"            # 管理员路由，需要管理员权限
    INTERNAL = "internal"      # 内部路由，仅内部服务调用
    API = "api"                # API路由
    WEBHOOK = "webhook"        # Webhook路由


@dataclass
class RouterMetadata:
    """路由元数据"""
    router: APIRouter
    router_type: RouterType
    priority: int = 100  # 优先级，数字越小优先级越高
    name: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    dependencies: Optional[List[Any]] = None
    enabled: bool = True  # 是否启用
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据


class RouterValidator:
    """路由验证器基类"""
    
    def validate(self, metadata: RouterMetadata) -> Tuple[bool, Optional[str]]:
        """
        验证路由是否可以通过注册
        
        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        return True, None


class RouterRegistry:
    """
    全局单例路由注册器
    
    特性：
    1. 单例模式，确保全局唯一
    2. 支持多种路由类型，不同类型可配置不同的验证器
    3. 支持优先级排序，高优先级路由先注册
    4. 支持验证阶段，路由需通过验证才能注册
    """
    
    _instance: Optional['RouterRegistry'] = None
    _lock: Lock = Lock()
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化注册器"""
        if self._initialized:
            return
        
        self._routers: List[RouterMetadata] = []
        self._validators: Dict[RouterType, List[RouterValidator]] = {}
        self._type_handlers: Dict[RouterType, Callable[[RouterMetadata, FastAPI], None]] = {}
        self._registered_count = 0
        self._skipped_count = 0
        self._failed_count = 0
        # Idempotency tracking
        self._validator_class_names: Dict[RouterType, set[str]] = {}
        self._added_router_keys: set[str] = set()
        self._added_router_ids: set[int] = set()
        self._initialized = True
        
        # 注册默认类型处理器
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """注册默认的类型处理器"""
        # 默认处理器：直接注册路由
        default_handler = lambda metadata, app: app.include_router(metadata.router)
        
        for router_type in RouterType:
            self._type_handlers[router_type] = default_handler
    
    def register_validator(self, router_type: RouterType, validator: RouterValidator):
        """
        为特定路由类型注册验证器
        
        Args:
            router_type: 路由类型
            validator: 验证器实例
        """
        if router_type not in self._validators:
            self._validators[router_type] = []
        if router_type not in self._validator_class_names:
            self._validator_class_names[router_type] = set()

        class_name = validator.__class__.__name__
        if class_name in self._validator_class_names[router_type]:
            print(f"⏭️  验证器已存在，跳过: {router_type.value} -> {class_name}")
            return

        self._validators[router_type].append(validator)
        self._validator_class_names[router_type].add(class_name)
        print(f"✅ 注册验证器: {router_type.value} -> {class_name}")
    
    def register_type_handler(
        self, 
        router_type: RouterType, 
        handler: Callable[[RouterMetadata, FastAPI], None]
    ):
        """
        为特定路由类型注册处理器
        
        Args:
            router_type: 路由类型
            handler: 处理器函数，接收 (metadata, app) 参数
        """
        self._type_handlers[router_type] = handler
        print(f"✅ 注册类型处理器: {router_type.value} -> {handler.__name__}")
    
    def add_router(
        self,
        router: APIRouter,
        router_type: RouterType = RouterType.PUBLIC,
        priority: int = 100,
        name: Optional[str] = None,
        description: Optional[str] = None,
        enabled: bool = True,
        **metadata
    ) -> bool:
        """
        添加路由到注册队列（尚未注册到FastAPI应用）
        
        Args:
            router: FastAPI路由对象
            router_type: 路由类型
            priority: 优先级，数字越小优先级越高
            name: 路由名称
            description: 路由描述
            enabled: 是否启用
            **metadata: 额外元数据
            
        Returns:
            bool: 是否成功添加到队列
        """
        # 去重键：优先使用对象id，其次使用 name|prefix 组合
        dedupe_id = id(router)
        dedupe_key = f"{(name or router.prefix or 'unnamed')}|{getattr(router, 'prefix', '')}"

        if dedupe_id in self._added_router_ids or dedupe_key in self._added_router_keys:
            print(f"⏭️  重复路由，跳过添加: {dedupe_key}")
            return False

        router_metadata = RouterMetadata(
            router=router,
            router_type=router_type,
            priority=priority,
            name=name or router.prefix or "unnamed",
            description=description,
            enabled=enabled,
            metadata=metadata
        )
        
        self._added_router_ids.add(dedupe_id)
        self._added_router_keys.add(dedupe_key)
        self._routers.append(router_metadata)
        print(f"📝 路由已添加到注册队列: {router_metadata.name} (类型: {router_type.value}, 优先级: {priority})")
        return True
    
    def _validate_router(self, metadata: RouterMetadata) -> Tuple[bool, Optional[str]]:
        """
        验证路由是否可以通过注册
        
        Args:
            metadata: 路由元数据
            
        Returns:
            (is_valid, error_message): 验证结果和错误信息
        """
        # 检查是否启用
        if not metadata.enabled:
            return False, "路由已禁用"
        
        # 获取该类型的验证器
        validators = self._validators.get(metadata.router_type, [])
        
        # 执行所有验证器
        for validator in validators:
            is_valid, error_msg = validator.validate(metadata)
            if not is_valid:
                return False, error_msg
        
        return True, None
    
    def _register_router(self, metadata: RouterMetadata, app: FastAPI) -> bool:
        """
        注册单个路由到FastAPI应用
        
        Args:
            metadata: 路由元数据
            app: FastAPI应用实例
            
        Returns:
            bool: 是否注册成功
        """
        # 验证路由
        is_valid, error_msg = self._validate_router(metadata)
        if not is_valid:
            print(f"❌ 路由验证失败: {metadata.name} - {error_msg}")
            self._failed_count += 1
            return False
        
        # 获取类型处理器
        handler = self._type_handlers.get(metadata.router_type)
        if handler is None:
            print(f"⚠️  未找到类型处理器: {metadata.router_type.value}，使用默认处理器")
            handler = self._type_handlers.get(RouterType.PUBLIC)
        
        try:
            # 执行类型特定的注册逻辑
            handler(metadata, app)
            print(f"✅ 路由注册成功: {metadata.name} (类型: {metadata.router_type.value}, 优先级: {metadata.priority})")
            self._registered_count += 1
            return True
        except Exception as e:
            print(f"❌ 路由注册异常: {metadata.name} - {str(e)}")
            self._failed_count += 1
            return False
    
    def register_all(self, app: FastAPI) -> Dict[str, int]:
        """
        将所有路由注册到FastAPI应用
        
        按照优先级排序，高优先级（数字小）先注册
        
        Args:
            app: FastAPI应用实例
            
        Returns:
            Dict: 注册统计信息
        """
        print("\n" + "="*60)
        print("🚀 开始注册路由...")
        print("="*60)
        
        # 重置计数器
        self._registered_count = 0
        self._skipped_count = 0
        self._failed_count = 0
        
        # 按优先级排序（优先级数字越小，优先级越高）
        sorted_routers = sorted(self._routers, key=lambda x: (x.priority, x.name))
        
        # 注册所有路由
        for metadata in sorted_routers:
            if not metadata.enabled:
                print(f"⏭️  跳过已禁用的路由: {metadata.name}")
                self._skipped_count += 1
                continue
            
            self._register_router(metadata, app)
        
        # 打印统计信息
        print("="*60)
        print(f"📊 路由注册统计:")
        print(f"   ✅ 成功注册: {self._registered_count}")
        print(f"   ⏭️  跳过: {self._skipped_count}")
        print(f"   ❌ 失败: {self._failed_count}")
        print(f"   📝 总计: {len(self._routers)}")
        print("="*60 + "\n")
        
        return {
            "registered": self._registered_count,
            "skipped": self._skipped_count,
            "failed": self._failed_count,
            "total": len(self._routers)
        }
    
    def clear(self):
        """清空所有已注册的路由（用于测试）"""
        self._routers.clear()
        self._registered_count = 0
        self._skipped_count = 0
        self._failed_count = 0
        print("🗑️  已清空所有路由")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取注册器统计信息"""
        return {
            "total_routers": len(self._routers),
            "registered": self._registered_count,
            "skipped": self._skipped_count,
            "failed": self._failed_count,
            "by_type": {
                router_type.value: sum(1 for r in self._routers if r.router_type == router_type)
                for router_type in RouterType
            }
        }


# 全局单例实例
router_registry = RouterRegistry()

