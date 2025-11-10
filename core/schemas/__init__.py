from __future__ import annotations

from pydantic import BaseModel
from typing import Optional

from .configs import (
    AppConfig, LoggingConfig, RedisConfig, APIConfig, CORSConfig, 
    EmailConfig, SMTPConfig, RateLimitConfig, DDoSProtectionConfig
)


class GlobalConfig(BaseModel):
    app: AppConfig
    logging: Optional[LoggingConfig] = None
    redis: Optional[RedisConfig] = None
    api: Optional[APIConfig] = None
    email: Optional[EmailConfig] = None
    rate_limit: Optional[RateLimitConfig] = None
    ddos_protection: Optional[DDoSProtectionConfig] = None

__all__ = [
    'GlobalConfig', 'AppConfig', 'LoggingConfig', 'RedisConfig', 
    'APIConfig', 'CORSConfig', 'EmailConfig', 'SMTPConfig',
    'RateLimitConfig', 'DDoSProtectionConfig'
]
