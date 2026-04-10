import uuid

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.database import get_db_optional
from app.models.db import PlanEnum, User
from app.services.rate_limiter import check_and_increment

LOCAL_DEV_CLERK_ID = "local_dev_user"
LOCAL_DEV_EMAIL = "dev@local.invalid"
# フロントの LOCAL_DEV_BEARER と一致させる
DEV_BEARER_TOKEN = "local-dev"

# DB なしモード用（永続化しない・固定 ID）
LOCAL_DEV_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")


def _synthetic_local_dev_user() -> User:
    return User(
        id=LOCAL_DEV_USER_ID,
        clerk_id=LOCAL_DEV_CLERK_ID,
        email=LOCAL_DEV_EMAIL,
        plan=PlanEnum.free,
    )


def _synthetic_user_for_clerk(clerk_id: str) -> User:
    return User(
        id=uuid.uuid5(uuid.NAMESPACE_URL, f"esti:clerk:{clerk_id}"),
        clerk_id=clerk_id,
        email=f"{clerk_id[:64]}@users.clerk.placeholder",
        plan=PlanEnum.free,
    )


def _has_usable_clerk_jwt_public_key() -> bool:
    """
    実際に JWT 検証に使える PEM か。
    .env.example のプレースホルダー（... 付き）や短い断片は「未設定」と同じ扱いにする。
    """
    raw = (get_settings().CLERK_JWT_PUBLIC_KEY or "").strip()
    if not raw:
        return False
    pem = raw.replace("\\n", "\n").strip()
    if "..." in pem:
        return False
    if "BEGIN" not in pem or "END" not in pem or "PUBLIC KEY" not in pem:
        return False
    body = (
        pem.replace("-----BEGIN PUBLIC KEY-----", "")
        .replace("-----END PUBLIC KEY-----", "")
        .replace("-----BEGIN RSA PUBLIC KEY-----", "")
        .replace("-----END RSA PUBLIC KEY-----", "")
        .strip()
    )
    if len(body) < 80:
        return False
    return True


def _local_auth_bypass_enabled() -> bool:
    s = get_settings()
    if not s.is_local:
        return False
    if s.LOCAL_DEV_AUTH_BYPASS:
        return True
    return not _has_usable_clerk_jwt_public_key()


async def _get_or_create_local_dev_user(db: AsyncSession) -> User:
    row = await db.execute(select(User).where(User.clerk_id == LOCAL_DEV_CLERK_ID))
    user = row.scalar_one_or_none()
    if user is None:
        user = User(clerk_id=LOCAL_DEV_CLERK_ID, email=LOCAL_DEV_EMAIL, plan="free")
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession | None = Depends(get_db_optional),
) -> User:
    if _local_auth_bypass_enabled():
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="ローカル開発（Clerk未設定）: Authorization: Bearer local-dev を付与してください",
            )
        token = authorization.removeprefix("Bearer ").strip()
        if token == DEV_BEARER_TOKEN:
            if db is not None:
                return await _get_or_create_local_dev_user(db)
            return _synthetic_local_dev_user()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid local dev token")

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ").strip()
    clerk_id = _verify_clerk_token(token)
    if db is not None:
        row = await db.execute(select(User).where(User.clerk_id == clerk_id))
        user = row.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user
    return _synthetic_user_for_clerk(clerk_id)


def _clerk_jwt_pem() -> str:
    """.env の PEM は \\n エスケープのことがある。pydantic は os.environ に載せないため get_settings() を使う。"""
    raw = (get_settings().CLERK_JWT_PUBLIC_KEY or "").strip()
    if not raw:
        return ""
    return raw.replace("\\n", "\n")


def _verify_clerk_token(token: str) -> str:
    from jose import JWTError, jwt

    key = _clerk_jwt_pem()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CLERK_JWT_PUBLIC_KEY が未設定です。backend/.env.local に設定するか、ローカルではキーを空にして Bearer local-dev を使ってください。",
        )
    try:
        payload = jwt.decode(token, key, algorithms=["RS256"], options={"verify_aud": False})
        clerk_id = payload.get("sub", "")
        if not clerk_id:
            raise JWTError("sub missing")
        return clerk_id
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}") from e


async def get_current_user_with_limit(
    user: User = Depends(get_current_user),
    db: AsyncSession | None = Depends(get_db_optional),
) -> User:
    await check_and_increment(user, db)
    return user
