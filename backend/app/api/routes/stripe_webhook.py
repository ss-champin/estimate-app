import logging
import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db_optional
from app.models.db import Subscription

router = APIRouter(tags=["stripe"])
logger = logging.getLogger(__name__)

@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
    db: AsyncSession | None = Depends(get_db_optional),
):
    if db is None:
        logger.warning("データベース無効のため Stripe Webhook をスキップします")
        return {"received": False, "skipped": True, "reason": "database_disabled"}

    if not (settings.STRIPE_WEBHOOK_SECRET or "").strip():
        logger.warning("STRIPE_WEBHOOK_SECRET 未設定のため Webhook をスキップします（ローカル開発用）")
        return {"received": False, "skipped": True, "reason": "no_webhook_secret"}

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    match event["type"]:
        case "customer.subscription.created" | "customer.subscription.updated":
            sub = event["data"]["object"]
            await db.execute(update(Subscription).where(Subscription.stripe_subscription_id == sub["id"]).values(status=sub["status"]))
            await db.commit()
        case "customer.subscription.deleted":
            sub = event["data"]["object"]
            await db.execute(update(Subscription).where(Subscription.stripe_subscription_id == sub["id"]).values(status="canceled"))
            await db.commit()

    return {"received": True}
