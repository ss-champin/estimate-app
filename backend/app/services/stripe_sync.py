from __future__ import annotations

import logging
import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db import PlanEnum, Subscription, SubscriptionStatusEnum, User

logger = logging.getLogger(__name__)


def map_stripe_subscription_status(stripe_status: str) -> str:
    s = (stripe_status or "").lower()
    if s in ("active", "trialing"):
        return SubscriptionStatusEnum.active.value
    if s == "past_due":
        return SubscriptionStatusEnum.past_due.value
    return SubscriptionStatusEnum.canceled.value


def stripe_subscription_grants_paid(stripe_status: str) -> bool:
    return (stripe_status or "").lower() in ("active", "trialing")


async def sync_subscription_row_and_user_plan(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    stripe_customer_id: str | None,
    stripe_subscription_id: str,
    stripe_status: str,
    current_period_end: datetime | None,
) -> None:
    local_status = map_stripe_subscription_status(stripe_status)
    paid = stripe_subscription_grants_paid(stripe_status)

    res = await db.execute(select(Subscription).where(Subscription.user_id == user_id))
    sub_row = res.scalar_one_or_none()

    if sub_row is None:
        sub_row = Subscription(
            user_id=user_id,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            status=local_status,
            current_period_end=current_period_end,
        )
        db.add(sub_row)
    else:
        if stripe_customer_id:
            sub_row.stripe_customer_id = stripe_customer_id
        sub_row.stripe_subscription_id = stripe_subscription_id
        sub_row.status = local_status
        sub_row.current_period_end = current_period_end

    plan_value = PlanEnum.paid.value if paid else PlanEnum.free.value
    await db.execute(update(User).where(User.id == user_id).values(plan=plan_value))
    await db.commit()


async def mark_subscription_canceled_by_stripe_id(
    db: AsyncSession,
    stripe_subscription_id: str,
) -> None:
    res = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id),
    )
    rec = res.scalar_one_or_none()
    if rec is None:
        logger.warning(
            "Stripe Webhook: subscriptions 行が見つかりません (stripe_subscription_id=%s)",
            stripe_subscription_id,
        )
        return
    rec.status = SubscriptionStatusEnum.canceled.value
    await db.execute(update(User).where(User.id == rec.user_id).values(plan=PlanEnum.free.value))
    await db.commit()
