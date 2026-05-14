from __future__ import annotations

import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.db import PlanEnum, Subscription, SubscriptionStatusEnum, User
from app.services.billing_plans import (
    get_paid_stripe_price_id_for_checkout,
    normalize_checkout_price_id,
)
from app.services.rate_limiter import plan_str

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stripe"])


class CheckoutUrlResponse(BaseModel):
    url: str


class PortalUrlResponse(BaseModel):
    url: str


def _stripe_require_secret_key() -> None:
    s = get_settings()
    key = (s.STRIPE_SECRET_KEY or "").strip()
    if not key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="STRIPE_SECRET_KEY が未設定です",
        )
    stripe.api_key = key


def _validate_checkout_price_id(price_id: str) -> None:
    """Checkout の line_items には Price ID（price_）のみ有効。prod_ はよくある誤設定。"""
    pid = normalize_checkout_price_id(price_id)
    if pid.startswith("prod_"):
        logger.warning("Checkout: 無効な Stripe ID（商品 ID）が渡されました: %s…", pid[:20])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "設定されているのは Stripe の商品 ID（prod_…）です。"
                "Checkout では価格 ID（price_…）が必要です。"
                "Dashboard → 商品 → 価格の「API ID」の price_… を STRIPE_PRICE_ID または "
                "billing_plans.stripe_price_id に設定してください。"
            ),
        )
    if pid and not pid.startswith("price_"):
        logger.warning("Checkout: Price ID が price_ で始まりません: %s…", pid[:24])
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Stripe Price ID は通常 price_ で始まります。"
                "STRIPE_PRICE_ID / billing_plans.stripe_price_id を確認してください。"
            ),
        )


async def _stripe_subscription_price_id(db: AsyncSession) -> str:
    price = (await get_paid_stripe_price_id_for_checkout(db)).strip()
    if not price:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Stripe の Pro 用 Price ID が未設定です。billing_plans.stripe_price_id "
                "を設定するか、STRIPE_PRICE_ID を .env に設定してください。"
            ),
        )
    _validate_checkout_price_id(price)
    return price


@router.post("/stripe/checkout-session", response_model=CheckoutUrlResponse)
async def create_checkout_session(
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> CheckoutUrlResponse:
    """
    Stripe Checkout（サブスクリプション）を開始し、リダイレクト用 URL を返す。
    """
    _stripe_require_secret_key()
    s = get_settings()
    price_id = await _stripe_subscription_price_id(db)

    if plan_str(current_user) == PlanEnum.paid.value:
        res_sub = await db.execute(
            select(Subscription).where(Subscription.user_id == current_user.id),
        )
        sub = res_sub.scalar_one_or_none()
        if sub and sub.stripe_subscription_id and sub.status in (
            SubscriptionStatusEnum.active.value,
            SubscriptionStatusEnum.past_due.value,
        ):
            logger.warning(
                "Checkout 却下: 既にアクティブなサブスクあり user_id=%s sub_status=%s",
                current_user.id,
                sub.status,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "既に有料プランです。変更・解約は「請求・プラン管理」"
                    "（Stripe Customer Portal）から行ってください。"
                ),
            )

    res = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    sub = res.scalar_one_or_none()
    customer_id = sub.stripe_customer_id if sub else None

    try:
        if not customer_id:
            cust = stripe.Customer.create(
                email=current_user.email,
                metadata={"user_id": str(current_user.id)},
            )
            customer_id = cust["id"]
            if sub:
                sub.stripe_customer_id = customer_id
                await db.commit()
            else:
                db.add(
                    Subscription(
                        user_id=current_user.id,
                        stripe_customer_id=customer_id,
                        status=SubscriptionStatusEnum.canceled.value,
                    ),
                )
                await db.commit()

        base = s.FRONTEND_URL.rstrip("/")
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{base}/dashboard?checkout=success",
            cancel_url=f"{base}/pricing?checkout=cancel",
            metadata={"user_id": str(current_user.id)},
            subscription_data={"metadata": {"user_id": str(current_user.id)}},
            client_reference_id=str(current_user.id),
            allow_promotion_codes=True,
        )
    except stripe.error.StripeError as e:
        logger.exception("Stripe Checkout 作成に失敗")
        msg = getattr(e, "user_message", None) or str(e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=msg,
        ) from e

    url = getattr(session, "url", None) if session else None
    if not url:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Checkout URL を取得できませんでした",
        )
    return CheckoutUrlResponse(url=url)


@router.post("/stripe/portal-session", response_model=PortalUrlResponse)
async def create_portal_session(
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> PortalUrlResponse:
    """Stripe Customer Portal（プラン変更・解約・請求書）への URL を返す。"""
    _stripe_require_secret_key()
    s = get_settings()

    res = await db.execute(select(Subscription).where(Subscription.user_id == current_user.id))
    sub = res.scalar_one_or_none()
    customer_id = sub.stripe_customer_id if sub else None
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stripe の顧客がまだありません。先にチェックアウトで Pro に登録してください。",
        )

    try:
        portal = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{s.FRONTEND_URL.rstrip('/')}/settings",
        )
    except stripe.error.StripeError as e:
        logger.exception("Stripe Billing Portal 作成に失敗")
        msg = getattr(e, "user_message", None) or str(e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=msg,
        ) from e

    purl = getattr(portal, "url", None) if portal else None
    if not purl:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Portal URL を取得できませんでした",
        )
    return PortalUrlResponse(url=purl)
