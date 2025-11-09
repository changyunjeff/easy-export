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


class RedisConfig(BaseModel):
    enabled: bool = Field(default=False, description="Enable Redis connection")
    host: str = Field(default="localhost", description="Redis server host")
    port: int = Field(default=6379, description="Redis server port")
    db: int = Field(default=0, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    decode_responses: bool = Field(default=True, description="Automatically decode responses to strings")
    max_connections: int = Field(default=50, description="Maximum number of connections in the pool")
    socket_connect_timeout: int = Field(default=5, description="Socket connection timeout in seconds")
    socket_timeout: int = Field(default=5, description="Socket timeout in seconds")


class CORSConfig(BaseModel):
    enabled: bool = Field(default=False, description="Enable CORS middleware")
    allow_origins: list[str] = Field(default_factory=list, description="List of allowed origins")
    allow_headers: list[str] = Field(default_factory=lambda: ["Content-Type"], description="List of allowed headers")
    allow_credentials: bool = Field(default=False, description="Allow credentials in CORS requests")
    expose_headers: list[str] = Field(default_factory=list, description="List of exposed headers")
    max_age: int = Field(default=600, description="Max age for CORS preflight requests in seconds")


class APIConfig(BaseModel):
    prefix: str = Field(default="/api/v1", description="API route prefix")
    cors: Optional[CORSConfig] = Field(default=None, description="CORS configuration")