from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db_optional
from app.models.db import User
from app.api.deps import get_current_user
from app.services.rate_limiter import plan_str

router = APIRouter(tags=["users"])

class UserResponse(BaseModel):
    id: str; email: str; plan: str

@router.get("/users/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse(id=str(current_user.id), email=current_user.email, plan=plan_str(current_user))

class ClerkWebhookPayload(BaseModel):
    type: str; data: dict

@router.post("/clerk/webhook")
async def clerk_webhook(payload: ClerkWebhookPayload, db: AsyncSession | None = Depends(get_db_optional)):
    if db is None:
        return {"received": True, "skipped": True, "reason": "database_disabled"}

    match payload.type:
        case "user.created":
            clerk_id = payload.data["id"]
            email    = payload.data["email_addresses"][0]["email_address"]
            existing = (await db.execute(select(User).where(User.clerk_id == clerk_id))).scalar_one_or_none()
            if not existing:
                db.add(User(clerk_id=clerk_id, email=email, plan="free"))
                await db.commit()
        case "user.deleted":
            user = (await db.execute(select(User).where(User.clerk_id == payload.data["id"]))).scalar_one_or_none()
            if user:
                await db.delete(user)
                await db.commit()
    return {"received": True}
