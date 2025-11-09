from __future__ import annotations

from pydantic import BaseModel
from typing import Optional

from .configs import AppConfig, LoggingConfig


class GlobalConfig(BaseModel):
    app: AppConfig
    logging: Optional[LoggingConfig] = None

__all__ = ['GlobalConfig', 'AppConfig', 'LoggingConfig']
