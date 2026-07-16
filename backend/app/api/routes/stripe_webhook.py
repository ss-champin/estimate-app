from __future__ import annotations

import logging

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request

from app.api.deps import get_d1
from app.core.config import settings

router = APIRouter(tags=["stripe"])
logger = logging.getLogger(__name__)


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
    db=Depends(get_d1),
) -> dict:
    if db is None:
        return {"received": False, "skipped": True, "reason": "database_disabled"}

    if not (settings.STRIPE_WEBHOOK_SECRET or "").strip():
        return {"received": False, "skipped": True, "reason": "no_webhook_secret"}

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(payload, stripe_signature, settings.STRIPE_WEBHOOK_SECRET)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload") from e
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature") from e

    match event["type"]:
        case "customer.subscription.created" | "customer.subscription.updated":
            sub = event["data"]["object"]
            customer_id = sub.get("customer")
            status_val = sub["status"]
            plan = "paid" if status_val == "active" else "free"
            if customer_id:
                await db.prepare(
                    "UPDATE subscriptions SET status = ? WHERE stripe_customer_id = ?"
                ).bind(status_val, customer_id).run()
                if plan == "paid":
                    row = await db.prepare(
                        "SELECT user_id FROM subscriptions WHERE stripe_customer_id = ?"
                    ).bind(customer_id).first()
                    if row:
                        await db.prepare(
                            "UPDATE users SET plan = ? WHERE id = ?"
                        ).bind(plan, row["user_id"]).run()

        case "customer.subscription.deleted":
            sub = event["data"]["object"]
            customer_id = sub.get("customer")
            if customer_id:
                await db.prepare(
                    "UPDATE subscriptions SET status = 'canceled' WHERE stripe_customer_id = ?"
                ).bind(customer_id).run()
                row = await db.prepare(
                    "SELECT user_id FROM subscriptions WHERE stripe_customer_id = ?"
                ).bind(customer_id).first()
                if row:
                    await db.prepare(
                        "UPDATE users SET plan = 'free' WHERE id = ?"
                    ).bind(row["user_id"]).run()

    return {"received": True}
