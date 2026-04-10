from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.models.db import ApiUsage, PlanEnum, User


@dataclass(frozen=True)
class PlanLimits:
    daily_limit:   int | None
    monthly_limit: int


LIMITS: dict[str, PlanLimits] = {
    PlanEnum.free.value: PlanLimits(daily_limit=None, monthly_limit=3),
    PlanEnum.paid.value: PlanLimits(daily_limit=10,   monthly_limit=30),
}


def plan_str(user: User) -> str:
    """SQLAlchemy の Enum 列は PlanEnum インスタンスで返ることがあり、LIMITS の str キーと不一致になるのを防ぐ。"""
    p = user.plan
    if isinstance(p, PlanEnum):
        return p.value
    return str(p)


async def check_and_increment(user: User, db: AsyncSession | None) -> None:
    s = get_settings()
    if db is None:
        if not s.is_local:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="データベースが無効のため、本番相当の利用制限を適用できません。DATABASE_URL を設定してください。",
            )
        # ローカルかつ DB なし: 永続化しない（開発用）
        return

    limits    = LIMITS[plan_str(user)]
    today_jst = _today_jst()
    month_start = today_jst.replace(day=1)

    # 本番相当の回数制限は APP_ENV!=local のときのみ（無料月3回などでローカルが即 429 になるのを防ぐ）
    if not s.is_local:
        today_count = await _get_daily_count(user.id, today_jst, db)
        if limits.daily_limit is not None and today_count >= limits.daily_limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={
                "error": "daily_limit_exceeded",
                "message": f"本日の生成回数が上限（{limits.daily_limit}回/日）に達しました。明日またご利用ください。",
                "limit": limits.daily_limit, "used": today_count, "resets": "tomorrow",
            })

        monthly_count = await _get_monthly_count(user.id, month_start, today_jst, db)
        if monthly_count >= limits.monthly_limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail={
                "error": "monthly_limit_exceeded",
                "message": f"今月の生成回数が上限（{limits.monthly_limit}回/月）に達しました。" + ("有料プランにアップグレードすると30回/月ご利用いただけます。" if plan_str(user) == PlanEnum.free.value else "来月1日にリセットされます。"),
                "limit": limits.monthly_limit, "used": monthly_count, "resets": "next_month",
            })

    await _increment(user.id, today_jst, db)


@dataclass
class UsageStatus:
    plan: str; daily_used: int; daily_limit: int | None
    monthly_used: int; monthly_limit: int
    daily_remaining: int | None; monthly_remaining: int


async def get_usage_status(user: User, db: AsyncSession | None) -> UsageStatus:
    limits = LIMITS[plan_str(user)]
    if db is None:
        return UsageStatus(
            plan=plan_str(user),
            daily_used=0,
            daily_limit=limits.daily_limit,
            monthly_used=0,
            monthly_limit=limits.monthly_limit,
            daily_remaining=limits.daily_limit,
            monthly_remaining=limits.monthly_limit,
        )
    today = _today_jst()
    daily_used   = await _get_daily_count(user.id, today, db)
    monthly_used = await _get_monthly_count(user.id, today.replace(day=1), today, db)
    return UsageStatus(
        plan=plan_str(user), daily_used=daily_used, daily_limit=limits.daily_limit,
        monthly_used=monthly_used, monthly_limit=limits.monthly_limit,
        daily_remaining=max(0, limits.daily_limit - daily_used) if limits.daily_limit else None,
        monthly_remaining=max(0, limits.monthly_limit - monthly_used),
    )


def _today_jst() -> date:
    return (datetime.now(timezone.utc) + timedelta(hours=9)).date()


async def _get_daily_count(user_id, target_date: date, db: AsyncSession) -> int:
    row = await db.execute(select(ApiUsage.count).where(ApiUsage.user_id == user_id, ApiUsage.usage_date == target_date))
    return row.scalar_one_or_none() or 0


async def _get_monthly_count(user_id, start: date, end: date, db: AsyncSession) -> int:
    row = await db.execute(select(func.coalesce(func.sum(ApiUsage.count), 0)).where(ApiUsage.user_id == user_id, ApiUsage.usage_date >= start, ApiUsage.usage_date <= end))
    return int(row.scalar_one())


async def _increment(user_id, target_date: date, db: AsyncSession) -> None:
    from sqlalchemy.dialects.postgresql import insert
    stmt = insert(ApiUsage).values(user_id=user_id, usage_date=target_date, count=1).on_conflict_do_update(constraint="uq_api_usage_user_date", set_={"count": ApiUsage.count + 1})
    await db.execute(stmt)
    await db.commit()
