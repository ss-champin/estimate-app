from __future__ import annotations

import logging
import sys
import traceback

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import estimate, health, stripe_webhook, users
from app.core.config import settings

logger = logging.getLogger("app.main")


def _configure_logging() -> None:
    root = logging.getLogger("app")
    root.setLevel(logging.INFO)
    if root.handlers:
        return
    h = logging.StreamHandler(sys.stderr)
    h.setLevel(logging.INFO)
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    root.addHandler(h)
    root.propagate = False


_configure_logging()

app = FastAPI(
    title="EstiMate API",
    version="1.0.0",
    docs_url="/docs" if settings.is_local else None,
)

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
async def inject_cf_bindings(request: Request, call_next):
    """CF Workers の D1 バインディングを request.state.db に注入する。"""
    env = request.scope.get("env")
    request.state.db = getattr(env, "DB", None) if env else None
    try:
        return await call_next(request)
    except Exception:
        traceback.print_exc()
        origin = request.headers.get("origin", "")
        headers = {}
        if origin and (settings.is_local or origin in settings.ALLOWED_ORIGINS):
            headers = {
                "Access-Control-Allow-Origin": origin,
                "Access-Control-Allow-Credentials": "true",
            }
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error"}, headers=headers
        )


app.include_router(health.router)
app.include_router(estimate.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(stripe_webhook.router, prefix="/api")
