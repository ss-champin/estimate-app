import logging
import sys
import traceback
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.responses import Response

from app.api.deps import _local_auth_bypass_enabled
from app.api.routes import estimate, health, stripe_webhook, users
from app.core.config import apply_ai_keys_to_environ, settings
from app.core.database import ensure_local_dev_schema

limiter = Limiter(key_func=get_remote_address)
logger = logging.getLogger("app.main")


def _configure_app_logging() -> None:
    """
    uvicorn 既定の LOGGING_CONFIG は uvicorn.* だけにハンドラがある。
    app 配下の logger は root（既定 WARNING）に届き INFO が出ないため、ここで app ツリー用に出す。

    見積もりなど: app.api.routes.estimate / app.services.estimate_service
    """
    root = logging.getLogger("app")
    root.setLevel(logging.INFO)
    if root.handlers:
        return
    h = logging.StreamHandler(sys.stderr)
    h.setLevel(logging.INFO)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    root.addHandler(h)
    root.propagate = False


_configure_app_logging()


def rate_limit_exceeded_handler(request: Request, exc: Exception) -> Response:
    """FastAPI の ExceptionHandler は exc を Exception とみなすためラップする。"""
    return _rate_limit_exceeded_handler(request, cast(RateLimitExceeded, exc))


def _cors_headers_for_request(request: Request) -> dict[str, str]:
    """500 など未処理例外時もブラウザが CORS エラーにならないよう付与する。"""
    origin = request.headers.get("origin")
    if not origin:
        return {}
    allowed = list(settings.ALLOWED_ORIGINS)
    if settings.is_local:
        for o in ("http://localhost:3000", "http://127.0.0.1:3000"):
            if o not in allowed:
                allowed.append(o)
    if origin in allowed or (settings.is_local and ("localhost" in origin or "127.0.0.1" in origin)):
        return {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Credentials": "true",
        }
    return {}


def _validate_clerk_webhook_when_db() -> None:
    """
    DB 利用かつ Clerk で API 認証するときは Webhook と CLERK_WEBHOOK_SECRET 必須。
    （Clerk で user.created / user.deleted を /api/clerk/webhook に送る前提）
    ローカル「Clerk なし・Bearer local-dev」のみ省略可。
    """
    if not settings.database_enabled:
        return
    if _local_auth_bypass_enabled():
        logger.info(
            "ローカル開発（Clerk JWT 無効）: CLERK_WEBHOOK_SECRET なしで起動します"
        )
        return
    if not (settings.CLERK_WEBHOOK_SECRET or "").strip():
        raise RuntimeError(
            "PostgreSQL 利用かつ Clerk 認証が有効なため CLERK_WEBHOOK_SECRET は必須です。"
            "Clerk Dashboard → Webhooks に https://<APIベースURL>/api/clerk/webhook を登録し、"
            "user.created と user.deleted を購読し、"
            "Signing secret（whsec_…）を .env に設定してください。"
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    apply_ai_keys_to_environ()
    if not settings.database_enabled:
        logger.info(
            "DB 無効（DATABASE_URL 空または USE_DATABASE=false）。"
            "永続化・利用回数の DB 記録は行いません。"
            "PostgreSQL を使う場合は DATABASE_URL を設定し USE_DATABASE=auto（既定）に戻してください。"
        )
    if not settings.is_local and not settings.database_enabled:
        raise RuntimeError(
            "本番では DATABASE_URL が必須です。USE_DATABASE を確認するか PostgreSQL の URL を設定してください。"
        )
    _validate_clerk_webhook_when_db()
    await ensure_local_dev_schema()
    yield

app = FastAPI(
    title="EstiMate API", version="1.0.0", lifespan=lifespan,
    docs_url="/docs" if settings.is_local else None,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

_cors_allow = list(settings.ALLOWED_ORIGINS)
if settings.is_local:
    for o in ("http://localhost:3000", "http://127.0.0.1:3000"):
        if o not in _cors_allow:
            _cors_allow.append(o)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_allow,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def unhandled_exception_cors(request: Request, call_next):
    """CORSMiddleware が効かない未処理例外レスポンスにも CORS を付ける。"""
    try:
        return await call_next(request)
    except Exception:
        traceback.print_exc()
        detail = "Internal server error" if not settings.is_local else "サーバーでエラーが発生しました（詳細はターミナルログを参照）"
        return JSONResponse(
            status_code=500,
            content={"detail": detail},
            headers=_cors_headers_for_request(request),
        )
app.include_router(health.router)
app.include_router(estimate.router,       prefix="/api")
app.include_router(users.router,          prefix="/api")
app.include_router(stripe_webhook.router, prefix="/api")
