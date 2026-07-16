from __future__ import annotations

import logging
import os as _os
import sys
import traceback
import types as _types

# --- Cloudflare Workers: inject vars/secrets into os.environ BEFORE settings load ---
# workers.env is available at module level in the CF runtime.
# In non-CF environments this import fails and we fall through silently.
try:
    from workers import env as _cf_env  # type: ignore[import-untyped]

    _CF_ENV_KEYS = (
        "APP_ENV", "CLERK_SECRET_KEY", "CLERK_JWT_PUBLIC_KEY",
        "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_ID", "FRONTEND_URL", "ALLOWED_ORIGINS",
    )
    for _k in _CF_ENV_KEYS:
        _v = getattr(_cf_env, _k, None)
        if _v is not None:
            _os.environ[_k] = str(_v)
except Exception:  # noqa: BLE001
    pass

# In Cloudflare Workers, app/* is bundled directly at the module root (not inside an
# 'app/' subdirectory). Inject a virtual 'app' package so absolute imports work.
if "app" not in sys.modules:
    _app_mod = _types.ModuleType("app")
    _app_mod.__path__ = [_os.path.dirname(_os.path.abspath(__file__))]
    _app_mod.__package__ = "app"
    sys.modules["app"] = _app_mod

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


# Cloudflare Python Workers entry point.
# `workers` and `asgi` are pre-installed in the Cloudflare Pyodide runtime.
# The try/except makes the file importable in normal Python environments too.
try:
    import asgi as _asgi
    from workers import WorkerEntrypoint

    _CF_ENV_KEYS = (
        "APP_ENV", "CLERK_SECRET_KEY", "CLERK_JWT_PUBLIC_KEY",
        "GEMINI_API_KEY", "ANTHROPIC_API_KEY", "STRIPE_SECRET_KEY",
        "STRIPE_WEBHOOK_SECRET", "STRIPE_PRICE_ID", "FRONTEND_URL", "ALLOWED_ORIGINS",
    )
    _cf_env_initialized = False

    class Default(WorkerEntrypoint):
        async def fetch(self, request):
            global _cf_env_initialized
            if not _cf_env_initialized:
                import os as _os
                from app.core.config import get_settings
                for key in _CF_ENV_KEYS:
                    val = getattr(self.env, key, None)
                    if val is not None:
                        _os.environ[key] = str(val)
                get_settings.cache_clear()
                _cf_env_initialized = True
            return await _asgi.fetch(app, request, self.env)

except ImportError:
    pass
