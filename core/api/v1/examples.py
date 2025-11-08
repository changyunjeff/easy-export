from fastapi import APIRouter

from core.response import HttpResponse, Ok

example_router = APIRouter(prefix="/api/v1/examples", tags=["examples"])

@example_router.get("/health", response_model=HttpResponse)
async def example_health():
    return Ok()