from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from fastapi import HTTPException, status

from app.core.config import get_settings
from app.models.db import User


@dataclass(frozen=True)
class PlanLimits:
    daily_limit: int | None
    monthly_limit: int


LIMITS: dict[str, PlanLimits] = {
    "free": PlanLimits(daily_limit=None, monthly_limit=3),
    "paid": PlanLimits(daily_limit=10, monthly_limit=30),
}


def plan_str(user: User) -> str:
    return user.plan if user.plan in LIMITS else "free"


def _today_jst() -> date:
    return (datetime.now(UTC) + timedelta(hours=9)).date()


async def _get_daily_count(user_id: str, target_date: date, db) -> int:
    row = await db.prepare(
        "SELECT count FROM api_usage WHERE user_id = ? AND usage_date = ?"
    ).bind(user_id, target_date.isoformat()).first()
    return row["count"] if row else 0


async def _get_monthly_count(user_id: str, start: date, end: date, db) -> int:
    row = await db.prepare(
        "SELECT SUM(count) as total FROM api_usage WHERE user_id = ? AND usage_date >= ? AND usage_date <= ?"
    ).bind(user_id, start.isoformat(), end.isoformat()).first()
    return int(row["total"] or 0) if row else 0


async def _increment(user_id: str, target_date: date, db) -> None:
    new_id = str(uuid.uuid4()).replace("-", "")
    await db.prepare(
        """INSERT INTO api_usage (id, user_id, usage_date, count) VALUES (?, ?, ?, 1)
           ON CONFLICT(user_id, usage_date) DO UPDATE SET count = count + 1"""
    ).bind(new_id, user_id, target_date.isoformat()).run()


async def check_and_increment(user: User, db) -> None:
    s = get_settings()
    if db is None:
        if not s.is_local:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="データベースが無効です。D1 バインディングを確認してください。",
            )
        return

    limits = LIMITS[plan_str(user)]
    today = _today_jst()
    month_start = today.replace(day=1)

    if not s.is_local:
        daily_used = await _get_daily_count(user.id, today, db)
        if limits.daily_limit is not None and daily_used >= limits.daily_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "daily_limit_exceeded",
                    "message": f"本日の生成回数が上限（{limits.daily_limit}回/日）に達しました。",
                    "limit": limits.daily_limit,
                    "used": daily_used,
                    "resets": "tomorrow",
                },
            )
        monthly_used = await _get_monthly_count(user.id, month_start, today, db)
        if monthly_used >= limits.monthly_limit:
            upgrade_msg = (
                "有料プランにアップグレードすると30回/月ご利用いただけます。"
                if plan_str(user) == "free"
                else "来月1日にリセットされます。"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "monthly_limit_exceeded",
                    "message": f"今月の生成回数が上限（{limits.monthly_limit}回/月）に達しました。{upgrade_msg}",
                    "limit": limits.monthly_limit,
                    "used": monthly_used,
                    "resets": "next_month",
                },
            )

    await _increment(user.id, today, db)


@dataclass
class UsageStatus:
    plan: str
    daily_used: int
    daily_limit: int | None
    monthly_used: int
    monthly_limit: int
    daily_remaining: int | None
    monthly_remaining: int


async def get_usage_status(user: User, db) -> UsageStatus:
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
    daily_used = await _get_daily_count(user.id, today, db)
    monthly_used = await _get_monthly_count(user.id, today.replace(day=1), today, db)
    return UsageStatus(
        plan=plan_str(user),
        daily_used=daily_used,
        daily_limit=limits.daily_limit,
        monthly_used=monthly_used,
        monthly_limit=limits.monthly_limit,
        daily_remaining=max(0, limits.daily_limit - daily_used) if limits.daily_limit else None,
        monthly_remaining=max(0, limits.monthly_limit - monthly_used),
    )
