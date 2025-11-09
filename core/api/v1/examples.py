from fastapi import APIRouter

from core.response import HttpResponse, Ok
from core.utils import get_api_prefix

example_router = APIRouter(prefix=f"{get_api_prefix()}/examples", tags=["examples"])

@example_router.get("/health", response_model=HttpResponse)
async def example_health():
    return Ok()

example_private_router = APIRouter(prefix=f"{get_api_prefix()}/examples", tags=["examples"])

@example_private_router.get("/health-private", response_model=HttpResponse)
async def example_private_health():
    return Ok()
