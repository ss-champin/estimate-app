import json

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from svix.webhooks import Webhook, WebhookVerificationError

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db_optional
from app.models.db import User
from app.services.rate_limiter import plan_str

router = APIRouter(tags=["users"])


class UserResponse(BaseModel):
    id: str
    email: str
    plan: str


@router.get("/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        plan=plan_str(current_user),
    )


def _parse_clerk_webhook_event(payload: dict) -> tuple[str, dict]:
    event_type = str(payload.get("type", "") or "")
    data = payload.get("data")
    if not isinstance(data, dict):
        return event_type, {}
    return event_type, data


@router.post("/clerk/webhook")
async def clerk_webhook(
    request: Request,
    db: AsyncSession | None = Depends(get_db_optional),
) -> dict[str, bool | str]:
    if db is None:
        return {"received": True, "skipped": True, "reason": "database_disabled"}

    body_bytes = await request.body()
    s = get_settings()
    secret = (s.CLERK_WEBHOOK_SECRET or "").strip()
    if secret:
        try:
            payload = Webhook(secret).verify(
                body_bytes,
                {
                    "svix-id": request.headers.get("svix-id", ""),
                    "svix-timestamp": request.headers.get("svix-timestamp", ""),
                    "svix-signature": request.headers.get("svix-signature", ""),
                },
            )
        except WebhookVerificationError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid webhook signature",
            ) from e
    else:
        if not s.is_local:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="CLERK_WEBHOOK_SECRET が未設定です（本番では必須）",
            )
        try:
            payload = json.loads(body_bytes.decode("utf-8"))
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON",
            ) from e

    if not isinstance(payload, dict):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid payload")

    event_type, data = _parse_clerk_webhook_event(payload)

    match event_type:
        case "user.created":
            clerk_id = data.get("id")
            if not clerk_id:
                return {"received": True, "skipped": True, "reason": "missing_user_id"}
            emails = data.get("email_addresses") or []
            email = None
            if emails and isinstance(emails, list) and isinstance(emails[0], dict):
                email = emails[0].get("email_address")
            if not email or not isinstance(email, str):
                email = f"{clerk_id}@users.clerk.placeholder"
            if len(email) > 255:
                email = email[:255]
            result = await db.execute(select(User).where(User.clerk_id == clerk_id))
            existing = result.scalar_one_or_none()
            if not existing:
                db.add(User(clerk_id=clerk_id, email=email, plan="free"))
                await db.commit()
        case "user.deleted":
            clerk_id = data.get("id")
            if clerk_id:
                await db.execute(delete(User).where(User.clerk_id == clerk_id))
                await db.commit()
    return {"received": True}
