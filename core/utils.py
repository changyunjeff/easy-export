from __future__ import annotations

import os


def is_debug(mode: str | None = None):
    """
    If the mode is set to development, return True; otherwise, return False.
    """
    if mode is not None:
        return mode == "dev" or mode == "development"
    env = os.getenv("ENV", "dev").lower()
    return env == "dev" or env == "development"


def get_api_prefix() -> str:
    """
    从配置中获取 API prefix
    
    Returns:
        str: API prefix，例如 "/api/v1"，如果配置不存在则返回默认值 "/api/v1"
    """
    try:
        from core.config import get_config
        config = get_config()
        api_config = getattr(config, "api", None)
        if api_config and api_config.prefix:
            return api_config.prefix
    except Exception:
        # 如果配置未加载或出错，返回默认值
        pass
    return "/api/v1"