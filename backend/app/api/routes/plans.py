from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db_optional
from app.services.billing_plans import get_active_billing_plans_ordered

router = APIRouter(tags=["plans"])


class PlanPublic(BaseModel):
    slug: str
    display_name: str
    description: str | None
    daily_request_limit: int | None
    monthly_request_limit: int
    estimate_plan_key: str
    sort_order: int


def _default_plans_response() -> list[PlanPublic]:
    """DB 無効時のフォールバック（マーケ／フロントが期待する形）。"""
    return [
        PlanPublic(
            slug="free",
            display_name="無料",
            description="まずは試したい方向け",
            daily_request_limit=None,
            monthly_request_limit=3,
            estimate_plan_key="free",
            sort_order=0,
        ),
        PlanPublic(
            slug="paid",
            display_name="Pro",
            description="フル機能・高品質AI",
            daily_request_limit=10,
            monthly_request_limit=30,
            estimate_plan_key="paid",
            sort_order=10,
        ),
    ]


@router.get("/plans", response_model=list[PlanPublic])
async def list_plans(
    db: AsyncSession | None = Depends(get_db_optional),  # noqa: B008
) -> list[PlanPublic]:
    if db is None:
        return _default_plans_response()
    rows = await get_active_billing_plans_ordered(db)
    if not rows:
        return _default_plans_response()
    return [
        PlanPublic(
            slug=p.slug,
            display_name=p.display_name,
            description=p.description,
            daily_request_limit=p.daily_request_limit,
            monthly_request_limit=p.monthly_request_limit,
            estimate_plan_key=p.estimate_plan_key,
            sort_order=p.sort_order,
        )
        for p in rows
    ]
