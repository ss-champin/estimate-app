import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV:              str       = "local"
    DATABASE_URL:         str       = ""
    # auto: DATABASE_URL が空なら DB 無効（開発を DB なしで回す）。true/false で明示。
    # 本番では DATABASE_URL を必ず設定すること。
    USE_DATABASE:         str       = "auto"
    CLERK_SECRET_KEY:     str       = ""
    CLERK_JWT_PUBLIC_KEY: str       = ""
    STRIPE_SECRET_KEY:    str       = ""
    STRIPE_WEBHOOK_SECRET:str       = ""
    STRIPE_PRICE_ID:      str       = ""
    FRONTEND_URL:         str       = "http://localhost:3000"
    ALLOWED_ORIGINS:      list[str] = ["http://localhost:3000"]
    AI_PROVIDER:          str       = "gemini"
    GEMINI_API_KEY:       str       = ""
    # 任意。AI Studio のキーは GEMINI と同一でよい。誤った GOOGLE だけがあると SDK がそちらを優先して失敗しうる
    GOOGLE_API_KEY:       str       = ""
    ANTHROPIC_API_KEY:    str       = ""
    OPENAI_API_KEY:       str       = ""
    # ローカルで true のとき、CLERK_JWT_PUBLIC_KEY があっても常に local-dev 認証（キーなし開発用）
    LOCAL_DEV_AUTH_BYPASS: bool = False

    # env は get_settings 内で load_dotenv する。ここで env_file を指定すると二重読込になる。
    model_config = SettingsConfigDict(env_file=None, env_file_encoding="utf-8", extra="ignore")

    @property
    def is_local(self) -> bool:
        return self.APP_ENV == "local"

    @property
    def database_enabled(self) -> bool:
        """PostgreSQL を使うか。USE_DATABASE=auto のときは DATABASE_URL があれば有効。"""
        flag = (self.USE_DATABASE or "auto").strip().lower()
        if flag in ("0", "false", "no", "off"):
            return False
        if flag in ("1", "true", "yes", "on"):
            return bool((self.DATABASE_URL or "").strip())
        return bool((self.DATABASE_URL or "").strip())


@lru_cache
def get_settings() -> Settings:
    env = os.getenv("APP_ENV", "local")
    load_dotenv(f".env.{env}", encoding="utf-8")
    return Settings()


def apply_ai_keys_to_environ() -> None:
    """
    pydantic-settings は .env を読んでも os.environ に載せない。
    google-genai は GOOGLE_API_KEY と GEMINI の両方があると GOOGLE を優先するため、
    AI Studio のキーは GEMINI_API_KEY があるとき常に GOOGLE_API_KEY へ同一値を上書きする。
    """
    s = get_settings()
    gem = (s.GEMINI_API_KEY or "").strip()
    goog = (s.GOOGLE_API_KEY or "").strip()
    if gem:
        os.environ["GEMINI_API_KEY"] = gem
        os.environ["GOOGLE_API_KEY"] = gem
    elif goog:
        os.environ["GOOGLE_API_KEY"] = goog
    ant = (s.ANTHROPIC_API_KEY or "").strip()
    if ant:
        os.environ.setdefault("ANTHROPIC_API_KEY", ant)


settings = get_settings()
