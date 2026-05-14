import asyncio
import logging
from collections.abc import AsyncGenerator
from functools import lru_cache

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings

logger = logging.getLogger(__name__)

_DB_UNAVAILABLE_DETAIL = (
    "データベースに接続できません。"
    "PostgreSQL を起動してください（例: Docker Compose の DB）、"
    "または DATABASE_URL が正しいか確認してください。"
)


def _is_db_connection_error(exc: BaseException) -> bool:
    """起動していない DB・接続拒否など、一時的な接続失敗を判定する。"""
    if isinstance(exc, OperationalError):
        return True
    if isinstance(exc, OSError):
        # ConnectionRefusedError, ネットワーク一時エラー等
        return True
    orig = getattr(exc, "orig", None)
    if isinstance(orig, OSError):
        return True
    cause = exc.__cause__
    if isinstance(cause, OSError):
        return True
    return False


def _raise_db_unavailable(exc: BaseException) -> None:
    logger.warning("DB 接続エラー: %s", exc)
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail=_DB_UNAVAILABLE_DETAIL,
    ) from exc


@lru_cache
def _engine() -> AsyncEngine:
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
def _session_factory() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(_engine(), expire_on_commit=False)


async def get_db_optional() -> AsyncGenerator[AsyncSession | None, None]:
    """DB 無効時は None を1回 yield（認証・レート制限のメモリモード用）。"""
    if not settings.database_enabled:
        yield None
        return
    try:
        async with _session_factory()() as session:
            yield session
    except Exception as e:
        if _is_db_connection_error(e):
            _raise_db_unavailable(e)
        raise


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """DB 必須のルート用。無効時は 503。"""
    if not settings.database_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "データベースが無効です。"
                "DATABASE_URL を設定するか USE_DATABASE を見直してください。"
            ),
        )
    try:
        async with _session_factory()() as session:
            yield session
    except Exception as e:
        if _is_db_connection_error(e):
            _raise_db_unavailable(e)
        raise


async def database_reachable(ping_timeout_sec: float = 2.0) -> bool:
    """設定上 DB 有効のとき、SELECT 1 で到達性だけ確認する。"""
    if not settings.database_enabled:
        return False
    try:
        engine = _engine()

        async def _ping() -> None:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        await asyncio.wait_for(_ping(), timeout=ping_timeout_sec)
        return True
    except Exception as e:
        # /health の定期確認で接続拒否が起きうるためスタックトレースは出さない
        logger.warning("DB ヘルスチェック: 接続に失敗しました（%s）", e)
        return False


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
