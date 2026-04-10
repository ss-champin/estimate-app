import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_current_user, get_current_user_with_limit
from app.core.database import get_db_optional
from app.models.db import User
from app.models.estimate import EstimateAPIResponse, EstimateRequest
from app.services.estimate_service import generate_estimate
from app.core.config import settings
from app.services.rate_limiter import UsageStatus, get_usage_status, plan_str

logger = logging.getLogger(__name__)
router = APIRouter(tags=["estimate"])
limiter = Limiter(key_func=get_remote_address)

# ローカルでは SlowAPI の IP 制限を緩め、連打テストで 429 にならないようにする
_GENERATE_RATE = "2000/minute" if settings.is_local else "10/minute"


@router.post("/estimate/generate", response_model=EstimateAPIResponse)
@limiter.limit(_GENERATE_RATE)
async def generate_estimate_endpoint(
    request: Request, body: EstimateRequest, current_user: User = Depends(get_current_user_with_limit)
) -> EstimateAPIResponse:
    plan = plan_str(current_user)
    jt = (body.job_title or "").replace("\n", " ").strip()
    jt_prev = jt or "（未指定）"
    logger.info(
        "\n".join(
            [
                "┌─ POST /api/estimate/generate ──── ⓪ 受信リクエスト ───────────────",
                f"│  [ユーザー]     clerk_id={current_user.clerk_id}  db_id={current_user.id}",
                f"│  [プラン]       {plan}",
                f"│  [複雑度]       {body.complexity.value}",
                f"│  [案件タイトル] {jt_prev}",
                f"│  [本文文字数]   {len(body.job_description or '')}文字",
                "└────────────────────────────────────────────────────────────────",
            ]
        )
    )
    try:
        return await generate_estimate(body, user_plan=plan)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        logger.exception("見積もり生成エラー")
        if settings.is_local:
            raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}") from e
        raise HTTPException(status_code=500, detail="見積もりの生成中にエラーが発生しました") from e


class UsageResponse(BaseModel):
    plan: str
    daily_used: int
    daily_limit: int | None
    monthly_used: int
    monthly_limit: int
    daily_remaining: int | None
    monthly_remaining: int


@router.get("/estimate/usage", response_model=UsageResponse)
async def get_usage_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession | None = Depends(get_db_optional),
) -> UsageResponse:
    s = await get_usage_status(current_user, db)
    return UsageResponse(
        plan=s.plan,
        daily_used=s.daily_used,
        daily_limit=s.daily_limit,
        monthly_used=s.monthly_used,
        monthly_limit=s.monthly_limit,
        daily_remaining=s.daily_remaining,
        monthly_remaining=s.monthly_remaining,
    )
