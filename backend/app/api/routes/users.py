from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user, get_d1
from app.models.db import User
from app.services.rate_limiter import plan_str

router = APIRouter(tags=["users"])


class UserResponse(BaseModel):
    id: str
    email: str
    plan: str


@router.get("/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=current_user.id, email=current_user.email, plan=plan_str(current_user))


class ClerkWebhookPayload(BaseModel):
    type: str
    data: dict


@router.post("/clerk/webhook")
async def clerk_webhook(payload: ClerkWebhookPayload, db=Depends(get_d1)) -> dict:
    if db is None:
        return {"received": True, "skipped": True, "reason": "database_disabled"}

    match payload.type:
        case "user.created":
            clerk_id = payload.data["id"]
            email = payload.data["email_addresses"][0]["email_address"]
            new_id = str(uuid.uuid4()).replace("-", "")
            await db.prepare(
                "INSERT OR IGNORE INTO users (id, clerk_id, email, plan) VALUES (?, ?, ?, 'free')"
            ).bind(new_id, clerk_id, email).run()
        case "user.deleted":
            clerk_id = payload.data["id"]
            await db.prepare("DELETE FROM users WHERE clerk_id = ?").bind(clerk_id).run()

    return {"received": True}
