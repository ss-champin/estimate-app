import logging
import uuid
from datetime import UTC, datetime
from typing import Any

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_optional
from app.models.db import Subscription
from app.services.stripe_sync import (
    mark_subscription_canceled_by_stripe_id,
    sync_subscription_row_and_user_plan,
)

router = APIRouter(tags=["stripe"])
logger = logging.getLogger(__name__)


def _stripe_get(obj: object, key: str, default: Any = None) -> Any:
    """dict と stripe.StripeObject の両方からキーを読む（.get は StripeObject で使えない）。"""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    try:
        return obj[key]
    except (KeyError, TypeError):
        return default


def _stripe_customer_id(cust: object) -> str | None:
    if cust is None:
        return None
    if isinstance(cust, str):
        return cust
    if isinstance(cust, dict):
        v = cust.get("id")
        return v if isinstance(v, str) else None
    cid = _stripe_get(cust, "id")
    return cid if isinstance(cid, str) else None


async def _handle_subscription_event(db: AsyncSession, sub_obj: object) -> None:
    sid = _stripe_get(sub_obj, "id")
    if not sid:
        return
    meta = _stripe_get(sub_obj, "metadata") or {}
    uid_s = _stripe_get(meta, "user_id")
    user_id = uuid.UUID(uid_s) if uid_s else None
    cust_id = _stripe_customer_id(_stripe_get(sub_obj, "customer"))
    period_ts = _stripe_get(sub_obj, "current_period_end")
    period_end = datetime.fromtimestamp(period_ts, tz=UTC) if period_ts else None

    if user_id is None:
        res = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == sid),
        )
        rec = res.scalar_one_or_none()
        if rec is None:
            logger.warning("Stripe subscription イベント: user を特定できません sub=%s", sid)
            return
        user_id = rec.user_id

    await sync_subscription_row_and_user_plan(
        db,
        user_id=user_id,
        stripe_customer_id=cust_id,
        stripe_subscription_id=sid,
        stripe_status=_stripe_get(sub_obj, "status") or "",
        current_period_end=period_end,
    )


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(default=None, alias="stripe-signature"),
    db: AsyncSession | None = Depends(get_db_optional),  # noqa: B008
) -> dict[str, bool | str]:
    if db is None:
        logger.warning("データベース無効のため Stripe Webhook をスキップします")
        return {"received": False, "skipped": True, "reason": "database_disabled"}

    if not (settings.STRIPE_WEBHOOK_SECRET or "").strip():
        logger.warning(
            "STRIPE_WEBHOOK_SECRET 未設定のため Webhook をスキップします（ローカル開発用）",
        )
        return {"received": False, "skipped": True, "reason": "no_webhook_secret"}

    if not stripe_signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    payload = await request.body()
    try:
        event = stripe.Webhook.construct_event(
            payload,
            stripe_signature,
            settings.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload") from None
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature") from None

    match event["type"]:
        case "checkout.session.completed":
            sess = event["data"]["object"]
            if _stripe_get(sess, "mode") == "subscription":
                meta = _stripe_get(sess, "metadata") or {}
                uid_s = _stripe_get(meta, "user_id")
                sub_id = _stripe_get(sess, "subscription")
                cust_raw = _stripe_get(sess, "customer")
                if uid_s and sub_id:
                    key = (settings.STRIPE_SECRET_KEY or "").strip()
                    if key:
                        stripe.api_key = key
                        try:
                            sub_resource = stripe.Subscription.retrieve(sub_id)
                        except stripe.error.StripeError:
                            logger.exception(
                                "checkout.session.completed: Subscription.retrieve 失敗（"
                                "customer.subscription.* で再同期される場合があります）",
                            )
                        else:
                            pe = _stripe_get(sub_resource, "current_period_end")
                            period_end = (
                                datetime.fromtimestamp(int(pe), tz=UTC) if pe is not None else None
                            )
                            await sync_subscription_row_and_user_plan(
                                db,
                                user_id=uuid.UUID(uid_s),
                                stripe_customer_id=_stripe_customer_id(cust_raw),
                                stripe_subscription_id=sub_id,
                                stripe_status=_stripe_get(sub_resource, "status") or "",
                                current_period_end=period_end,
                            )
                    else:
                        logger.warning(
                            "STRIPE_SECRET_KEY 未設定のため "
                            "checkout.session.completed を同期できません",
                        )
        case "customer.subscription.created" | "customer.subscription.updated":
            await _handle_subscription_event(db, event["data"]["object"])
        case "customer.subscription.deleted":
            sub = event["data"]["object"]
            await mark_subscription_canceled_by_stripe_id(db, sub["id"])

    return {"received": True}
