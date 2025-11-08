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
