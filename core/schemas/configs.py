from pydantic import BaseModel, Field
from typing import Optional


class AppConfig(BaseModel):
    title: Optional[str] = Field(default="easy_export", description="title of the app")
    port: int = Field(default=8000, description="port to run the server on")
    host: str = Field(default="0.0.0.0", description="host to run the server on")
    description: Optional[str] = Field(default=None, description="description of the app")
    version: Optional[str] = Field(default=None, description="version of the app")
    contact: Optional[dict] = Field(default=None, description="contact of the app")
    mode: Optional[str] = Field(default="dev", description="mode of the app")


class LoggingConfig(BaseModel):
    level: str = Field(default="INFO", description="Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL")
    console_enabled: bool = Field(default=True, description="Enable console logging")
    log_path: Optional[str] = Field(default=None, description="General application log file path")
    access_log_path: Optional[str] = Field(default=None, description="Access log file path")
    error_log_path: Optional[str] = Field(default=None, description="Error log file path")