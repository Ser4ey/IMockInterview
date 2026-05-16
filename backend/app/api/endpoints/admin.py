from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> Any:
    return {"status": "ok", "service": "IMock API"}
