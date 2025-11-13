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


def success_response(data: Optional[dict] = None, message: str = "success") -> dict:
    """创建成功响应"""
    response = {
        "code": 0,
        "msg": message
    }
    if data is not None:
        response["data"] = data
    return response


def error_response(message: str = "error", error_code: Optional[str] = None, data: Optional[dict] = None) -> dict:
    """创建错误响应"""
    response = {
        "code": 7,
        "msg": message
    }
    if error_code:
        response["error_code"] = error_code
    if data is not None:
        response["data"] = data
    return response
