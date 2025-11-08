from pydantic import BaseModel

from .configs import AppConfig


class GlobalConfig(BaseModel):
    app: AppConfig

__all__ = ['GlobalConfig']
