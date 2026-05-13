import os

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.database import database_reachable

router = APIRouter(tags=["health"])


class DatabaseStatus(BaseModel):
    """enabled: DB 利用設定。reachable: 有効時のみ接続可否（無効時は API 上 null）。"""

    enabled: bool
    reachable: bool | None = Field(
        description="DB 有効時のみ true/false。無効時は null（Docker / Neon 未使用モード）。",
    )


class HealthResponse(BaseModel):
    status: str
    environment: str
    database: DatabaseStatus


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    if settings.database_enabled:
        ok = await database_reachable()
        db = DatabaseStatus(enabled=True, reachable=ok)
    else:
        db = DatabaseStatus(enabled=False, reachable=None)
    return HealthResponse(
        status="ok",
        environment=os.getenv("APP_ENV", "local"),
        database=db,
    )
