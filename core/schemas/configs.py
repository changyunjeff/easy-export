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


class SMTPConfig(BaseModel):
    host: str = Field(default="smtp.gmail.com", description="SMTP server host")
    port: int = Field(default=587, description="SMTP server port")
    user: str = Field(default="", description="SMTP username/email")
    tls: bool = Field(default=True, description="Enable TLS encryption")
    template_dir: Optional[str] = Field(default=None, description="Email template directory path")


class EmailConfig(BaseModel):
    enabled: bool = Field(default=False, description="Enable email service")
    smtp: Optional[SMTPConfig] = Field(default=None, description="SMTP configuration")


class RateLimitConfig(BaseModel):
    enabled: bool = Field(default=False, description="Enable rate limiting")
    requests_per_minute: int = Field(default=60, description="Maximum requests per minute per IP")
    requests_per_hour: int = Field(default=1000, description="Maximum requests per hour per IP")
    requests_per_day: int = Field(default=10000, description="Maximum requests per day per IP")
    burst_size: int = Field(default=10, description="Burst size for token bucket algorithm")
    key_prefix: str = Field(default="rate_limit", description="Redis key prefix for rate limiting")


class DDoSProtectionConfig(BaseModel):
    enabled: bool = Field(default=False, description="Enable DDoS protection")
    max_requests_per_second: int = Field(default=10, description="Maximum requests per second per IP")
    max_requests_per_minute: int = Field(default=100, description="Maximum requests per minute per IP")
    block_duration: int = Field(default=3600, description="Block duration in seconds when threshold exceeded")
    whitelist_ips: list[str] = Field(default_factory=list, description="List of whitelisted IP addresses")
    blacklist_ips: list[str] = Field(default_factory=list, description="List of blacklisted IP addresses")
    key_prefix: str = Field(default="ddos_protection", description="Redis key prefix for DDoS protection")
    enable_auto_blacklist: bool = Field(default=True, description="Automatically blacklist IPs exceeding threshold")


class RocketMQConfig(BaseModel):
    enabled: bool = Field(default=False, description="Enable RocketMQ message queue")
    name_server: str = Field(default="localhost:9876", description="RocketMQ NameServer address")
    producer_group: str = Field(default="export_producer_group", description="Producer group name")
    consumer_group: str = Field(default="export_consumer_group", description="Consumer group name")
    topic: str = Field(default="export_tasks", description="Topic name for export tasks")
    tag: str = Field(default="*", description="Message tag filter")
    max_message_size: int = Field(default=4194304, description="Maximum message size in bytes (4MB)")
    send_timeout: int = Field(default=3000, description="Send message timeout in milliseconds")
    retry_times: int = Field(default=3, description="Retry times when send message failed")
    consumer_thread_min: int = Field(default=1, description="Minimum consumer thread count")
    consumer_thread_max: int = Field(default=5, description="Maximum consumer thread count")
    consume_message_batch_max_size: int = Field(default=1, description="Maximum batch size for consuming messages")
    pull_batch_size: int = Field(default=32, description="Pull batch size")
    pull_interval: int = Field(default=0, description="Pull interval in milliseconds")
    consume_timeout: int = Field(default=15, description="Consume timeout in minutes")
    max_reconsume_times: int = Field(default=16, description="Maximum reconsume times")
    suspend_current_queue_time: int = Field(default=1000, description="Suspend current queue time in milliseconds")
    access_key: Optional[str] = Field(default=None, description="Access key for authentication")
    secret_key: Optional[str] = Field(default=None, description="Secret key for authentication")
    security_token: Optional[str] = Field(default=None, description="Security token for authentication")
    namespace: Optional[str] = Field(default=None, description="Namespace for message isolation")