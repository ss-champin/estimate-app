from __future__ import annotations

import logging
from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, settings
from app.core.database import _session_factory
from app.models.db import BillingPlan, PlanEnum, User

logger = logging.getLogger(__name__)


def normalize_checkout_price_id(raw: str | None) -> str:
    """.env の引用符・先頭 BOM・余分な空白を除いた Price ID 文字列。"""
    if raw is None:
        return ""
    t = str(raw).strip().lstrip("\ufeff").strip()
    if len(t) >= 2 and t[0] == t[-1] and t[0] in "'\"":
        t = t[1:-1].strip().lstrip("\ufeff").strip()
    return t


def _is_valid_checkout_price_id(raw: str | None) -> bool:
    """Checkout line_items 用。price_ のみ有効（prod_ や空は不可）。"""
    return bool(normalize_checkout_price_id(raw).startswith("price_"))


def _plan_slug(user: User) -> str:
    p = user.plan
    if isinstance(p, PlanEnum):
        return p.value
    return str(p)


async def resolve_estimate_plan_key(user: User, db: AsyncSession | None) -> str:
    """見積もり生成用プランキー。DB に billing_plans 行があれば estimate_plan_key を使う。"""
    slug = _plan_slug(user)
    if db is None:
        return slug
    try:
        row = await get_billing_plan_by_slug(db, slug)
        if row is not None and row.is_active:
            return (row.estimate_plan_key or slug).strip() or slug
    except Exception:
        logger.warning(
            "billing_plans から estimate_plan_key を読めませんでした（slug=%s）",
            slug,
            exc_info=True,
        )
    return slug


async def get_billing_plan_by_slug(db: AsyncSession, slug: str) -> BillingPlan | None:
    row = await db.execute(select(BillingPlan).where(BillingPlan.slug == slug))
    return row.scalar_one_or_none()


async def get_active_billing_plans_ordered(db: AsyncSession) -> Sequence[BillingPlan]:
    row = await db.execute(
        select(BillingPlan)
        .where(BillingPlan.is_active.is_(True))
        .order_by(BillingPlan.sort_order, BillingPlan.slug),
    )
    return row.scalars().all()


async def get_paid_stripe_price_id_for_checkout(db: AsyncSession) -> str:
    """
    有料プランの Stripe Price ID。
    有効な price_ を DB → .env の順で探す。
    DB に prod_ など誤値が残っていても、.env が price_ ならそちらを使う。
    """
    res = await db.execute(
        select(BillingPlan).where(
            BillingPlan.slug == PlanEnum.paid.value,
            BillingPlan.is_active.is_(True),
        ),
    )
    row = res.scalar_one_or_none()
    db_id = normalize_checkout_price_id(row.stripe_price_id if row else None)
    env_id = normalize_checkout_price_id(get_settings().STRIPE_PRICE_ID)

    if _is_valid_checkout_price_id(db_id):
        return db_id
    if _is_valid_checkout_price_id(env_id):
        if db_id:
            logger.warning(
                "billing_plans.stripe_price_id が Checkout 向けでない（%s…）ため "
                "STRIPE_PRICE_ID を使用します",
                db_id[:16],
            )
        return env_id
    return db_id or env_id


async def _sync_paid_stripe_price_from_settings(session: AsyncSession) -> None:
    """paid 行の stripe_price_id を .env で補完。誤った prod_ などは price_ の env で上書き。"""
    pid = normalize_checkout_price_id(get_settings().STRIPE_PRICE_ID)
    if not pid or not _is_valid_checkout_price_id(pid):
        return
    res = await session.execute(select(BillingPlan).where(BillingPlan.slug == PlanEnum.paid.value))
    row = res.scalar_one_or_none()
    if row is None:
        return
    cur = normalize_checkout_price_id(row.stripe_price_id)
    if not cur or cur.startswith("prod_") or not _is_valid_checkout_price_id(cur):
        row.stripe_price_id = pid


async def ensure_default_billing_plans() -> None:
    """空なら free/paid を投入。Paid の Stripe Price は .env から補完（DB 未設定時のみ）。"""
    if not settings.database_enabled:
        return
    try:
        async with _session_factory()() as session:
            n = await session.scalar(select(func.count()).select_from(BillingPlan))
            if n == 0:
                session.add_all(
                    [
                        BillingPlan(
                            slug=PlanEnum.free.value,
                            display_name="無料",
                            description="まずは試したい方向け",
                            stripe_price_id=None,
                            daily_request_limit=None,
                            monthly_request_limit=3,
                            estimate_plan_key=PlanEnum.free.value,
                            sort_order=0,
                        ),
                        BillingPlan(
                            slug=PlanEnum.paid.value,
                            display_name="Pro",
                            description="フル機能・高品質AI",
                            stripe_price_id=None,
                            daily_request_limit=10,
                            monthly_request_limit=30,
                            estimate_plan_key=PlanEnum.paid.value,
                            sort_order=10,
                        ),
                    ],
                )
            await _sync_paid_stripe_price_from_settings(session)
            await session.commit()
    except Exception as e:
        logger.warning("billing_plans の確認・シードに失敗しました: %s", e)
