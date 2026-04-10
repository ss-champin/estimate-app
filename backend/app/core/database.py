import logging
from functools import lru_cache
from typing import AsyncGenerator
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.core.config import settings

logger = logging.getLogger(__name__)


@lru_cache
def _engine():
    if not settings.database_enabled:
        raise RuntimeError("database is disabled (USE_DATABASE / DATABASE_URL)")
    url = (settings.DATABASE_URL or "").strip()
    if not url:
        raise RuntimeError("DATABASE_URL is empty while database is enabled")
    return create_async_engine(
        url,
        echo=settings.is_local,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
    )


@lru_cache
def _session_factory():
    return async_sessionmaker(_engine(), expire_on_commit=False)


async def get_db_optional() -> AsyncGenerator[AsyncSession | None, None]:
    """DB 無効時は None を1回 yield（認証・レート制限のメモリモード用）。"""
    if not settings.database_enabled:
        yield None
        return
    async with _session_factory()() as session:
        yield session


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """DB 必須のルート用。無効時は 503。"""
    if not settings.database_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="データベースが無効です。DATABASE_URL を設定するか USE_DATABASE を見直してください。",
        )
    async with _session_factory()() as session:
        yield session


async def ensure_local_dev_schema() -> None:
    """
    APP_ENV=local かつ DB に接続できるとき、未マイグレーションでも ORM 定義からテーブルを作成する。
    （`alembic upgrade head` を忘れていても `users` などが無い 500 を防ぐ）
    """
    if not settings.is_local or not settings.database_enabled:
        return
    try:
        import app.models.db  # noqa: F401 — User / Subscription / ApiUsage を metadata に登録
        from app.models.base import Base

        engine = _engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("ローカル開発用: DB テーブルを確認・作成しました（未作成の場合のみ）")
    except Exception as e:
        logger.warning("ローカルDBの自動スキーマ作成に失敗しました（PostgreSQL 未起動など）: %s", e)
