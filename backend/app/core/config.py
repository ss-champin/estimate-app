import json
import os
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class Settings:
    APP_ENV: str = "local"
    CLERK_SECRET_KEY: str = ""
    CLERK_JWT_PUBLIC_KEY: str = ""
    GEMINI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_ID: str = ""
    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: list[str] = field(default_factory=lambda: ["http://localhost:3000"])
    LOCAL_DEV_AUTH_BYPASS: bool = False

    @property
    def is_local(self) -> bool:
        return self.APP_ENV in ("local", "", "development")


@lru_cache
def get_settings() -> Settings:
    origins_raw = os.environ.get("ALLOWED_ORIGINS", "")
    if origins_raw.startswith("["):
        origins = json.loads(origins_raw)
    elif origins_raw:
        origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
    else:
        origins = [os.environ.get("FRONTEND_URL", "http://localhost:3000")]

    return Settings(
        APP_ENV=os.environ.get("APP_ENV", "local"),
        CLERK_SECRET_KEY=os.environ.get("CLERK_SECRET_KEY", ""),
        CLERK_JWT_PUBLIC_KEY=os.environ.get("CLERK_JWT_PUBLIC_KEY", ""),
        GEMINI_API_KEY=os.environ.get("GEMINI_API_KEY", ""),
        ANTHROPIC_API_KEY=os.environ.get("ANTHROPIC_API_KEY", ""),
        STRIPE_SECRET_KEY=os.environ.get("STRIPE_SECRET_KEY", ""),
        STRIPE_WEBHOOK_SECRET=os.environ.get("STRIPE_WEBHOOK_SECRET", ""),
        STRIPE_PRICE_ID=os.environ.get("STRIPE_PRICE_ID", ""),
        FRONTEND_URL=os.environ.get("FRONTEND_URL", "http://localhost:3000"),
        ALLOWED_ORIGINS=origins,
        LOCAL_DEV_AUTH_BYPASS=os.environ.get("LOCAL_DEV_AUTH_BYPASS", "false").lower()
        in ("1", "true", "yes"),
    )


settings = get_settings()
