import os
from logging.config import fileConfig
from pathlib import Path
from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

app_env  = os.getenv("APP_ENV", "local")
env_file = Path(__file__).parent.parent / f".env.{app_env}"
if env_file.exists():
    load_dotenv(env_file, override=True)
    print(f"📄 {env_file.name} を読み込みました")
else:
    load_dotenv(Path(__file__).parent.parent / ".env", override=True)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

db_url = os.getenv("DATABASE_URL", "")
db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
config.set_main_option("sqlalchemy.url", db_url)

from app.models.base import Base  # noqa: E402
from app.models.db import ApiUsage, BillingPlan, Subscription, User  # noqa: E402, F401
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
