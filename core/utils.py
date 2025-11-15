from __future__ import annotations

import os
import re
from datetime import timedelta
from typing import Optional


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
    default_prefix = "/api/v1"
    
    try:
        from core.config import get_config
        config = get_config()
        api_config = getattr(config, "api", None)
        if api_config:
            prefix = getattr(api_config, "prefix", None)
            # 确保 prefix 是非空字符串并且以 '/' 开头
            if prefix and isinstance(prefix, str) and prefix.strip():
                prefix = prefix.strip()
                if not prefix.startswith('/'):
                    prefix = '/' + prefix
                return prefix
    except Exception:
        # 如果配置未加载或出错，返回默认值
        pass
    
    return default_prefix


def parse_time_string(time_str: str) -> timedelta:
    """
    解析人类可读的时间字符串，转换为 timedelta 对象
    
    支持的时间单位：
    - s, sec, second, seconds: 秒
    - m, min, minute, minutes: 分钟
    - h, hour, hours: 小时
    - d, day, days: 天
    - w, week, weeks: 周
    
    Args:
        time_str: 时间字符串，例如 "30m", "2h", "7d", "1w"
    
    Returns:
        timedelta: 对应的时间差对象
    
    Examples:
        >>> parse_time_string("30m")
        timedelta(minutes=30)
        >>> parse_time_string("2h")
        timedelta(hours=2)
        >>> parse_time_string("7d")
        timedelta(days=7)
        >>> parse_time_string("1w")
        timedelta(days=7)
    """
    if not time_str:
        raise ValueError("时间字符串不能为空")
    
    # 正则表达式匹配数字和单位
    pattern = r'^(\d+)\s*([a-zA-Z]+)$'
    match = re.match(pattern, time_str.strip())
    
    if not match:
        raise ValueError(f"无效的时间格式: {time_str}")
    
    value = int(match.group(1))
    unit = match.group(2).lower()
    
    # 单位映射
    unit_map = {
        's': 'seconds',
        'sec': 'seconds',
        'second': 'seconds',
        'seconds': 'seconds',
        'm': 'minutes',
        'min': 'minutes',
        'minute': 'minutes',
        'minutes': 'minutes',
        'h': 'hours',
        'hour': 'hours',
        'hours': 'hours',
        'd': 'days',
        'day': 'days',
        'days': 'days',
        'w': 'weeks',
        'week': 'weeks',
        'weeks': 'weeks',
    }
    
    unit_key = unit_map.get(unit)
    if not unit_key:
        raise ValueError(f"不支持的时间单位: {unit}")
    
    # 创建 timedelta
    kwargs = {unit_key: value}
    return timedelta(**kwargs)


def format_time_delta(delta: timedelta) -> str:
    """
    将 timedelta 对象格式化为人类可读的时间字符串
    
    Args:
        delta: timedelta 对象
    
    Returns:
        str: 人类可读的时间字符串，例如 "30分钟", "2小时", "7天"
    
    Examples:
        >>> format_time_delta(timedelta(minutes=30))
        "30分钟"
        >>> format_time_delta(timedelta(hours=2))
        "2小时"
        >>> format_time_delta(timedelta(days=7))
        "7天"
    """
    total_seconds = int(delta.total_seconds())
    
    if total_seconds < 60:
        return f"{total_seconds}秒"
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f"{minutes}分钟"
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f"{hours}小时"
    elif total_seconds < 604800:
        days = total_seconds // 86400
        return f"{days}天"
    else:
        weeks = total_seconds // 604800
        return f"{weeks}周"