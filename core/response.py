from pydantic import BaseModel, Field
from typing import Optional


class HttpResponse(BaseModel):
    code: int = Field(default=0)
    msg: str = Field(default="success")

class Ok(HttpResponse):
    code: int = 0
    msg: str = "success"

class OkWithDetail(HttpResponse):
    code: int = 0
    msg: str = "success"
    data: dict = Field(default_factory=dict)

class UnAuth(HttpResponse):
    code: int = 401
    msg: str = "unauthorized"

class Error(HttpResponse):
    code: int = 7
    msg: str = "error"

class ErrorWithDetail(HttpResponse):
    code: int = 7
    msg: str = "error"
    data: dict = Field(default_factory=dict)
