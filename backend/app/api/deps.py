from __future__ import annotations

import uuid

from fastapi import Depends, Header, HTTPException, Request, status

from app.core.config import get_settings
from app.models.db import User
from app.services.rate_limiter import check_and_increment

LOCAL_DEV_USER_ID = "00000000000040008000000000000001"
LOCAL_DEV_CLERK_ID = "local_dev_user"


def _synthetic_local_dev_user() -> User:
    return User(id=LOCAL_DEV_USER_ID, clerk_id=LOCAL_DEV_CLERK_ID, plan="free")


def _synthetic_user_for_clerk(clerk_id: str) -> User:
    return User(
        id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"esti:clerk:{clerk_id}")).replace("-", ""),
        clerk_id=clerk_id,
        plan="free",
    )


def _has_usable_clerk_jwt_public_key() -> bool:
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
    return len(body) >= 80


def _local_auth_bypass_enabled() -> bool:
    s = get_settings()
    if not s.is_local:
        return False
    if s.LOCAL_DEV_AUTH_BYPASS:
        return True
    return not _has_usable_clerk_jwt_public_key()


def get_d1(request: Request) -> object:
    """D1 バインディングを返す。CF Workers 環境以外では None。"""
    return getattr(request.state, "db", None)


async def _get_or_create_user(clerk_id: str, db: object) -> User:
    """D1 から clerk_id でユーザーを取得。存在しなければ作成して返す。"""
    row = await db.prepare(  # type: ignore[attr-defined]
        "SELECT id, clerk_id, plan FROM users WHERE clerk_id = ?"
    ).bind(clerk_id).first()
    if row:
        return User(id=row["id"], clerk_id=row["clerk_id"], plan=row["plan"] or "free")

    new_id = str(uuid.uuid4()).replace("-", "")
    placeholder_email = f"{clerk_id[:64]}@users.clerk.placeholder"
    await db.prepare(  # type: ignore[attr-defined]
        "INSERT OR IGNORE INTO users (id, clerk_id, email, plan) VALUES (?, ?, ?, 'free')"
    ).bind(new_id, clerk_id, placeholder_email).run()

    row = await db.prepare(  # type: ignore[attr-defined]
        "SELECT id, clerk_id, plan FROM users WHERE clerk_id = ?"
    ).bind(clerk_id).first()
    return User(id=row["id"], clerk_id=row["clerk_id"], plan=row["plan"] or "free")


def _verify_clerk_token(token: str) -> str:
    from jose import JWTError, jwt

    raw = (get_settings().CLERK_JWT_PUBLIC_KEY or "").strip()
    key = raw.replace("\\n", "\n")
    if not key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="CLERK_JWT_PUBLIC_KEY が未設定です。",
        )
    try:
        payload = jwt.decode(token, key, algorithms=["RS256"], options={"verify_aud": False})
        clerk_id = payload.get("sub", "")
        if not clerk_id:
            raise JWTError("sub missing")
        return clerk_id
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {e}"
        ) from e


async def get_current_user(
    request: Request,
    authorization: str | None = Header(default=None),
    db: object = Depends(get_d1),  # noqa: B008
) -> User:
    if _local_auth_bypass_enabled():
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization: Bearer local-dev を付与してください",
            )
        if db is not None:
            return await _get_or_create_user(LOCAL_DEV_CLERK_ID, db)
        return _synthetic_local_dev_user()

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authorization header"
        )
    token = authorization.removeprefix("Bearer ").strip()
    clerk_id = _verify_clerk_token(token)

    if db is not None:
        return await _get_or_create_user(clerk_id, db)
    return _synthetic_user_for_clerk(clerk_id)


async def get_current_user_with_limit(
    user: User = Depends(get_current_user),  # noqa: B008
    db: object = Depends(get_d1),  # noqa: B008
) -> User:
    await check_and_increment(user, db)
    return user
