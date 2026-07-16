from __future__ import annotations

import json
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user, get_current_user_with_limit, get_d1
from app.models.db import User
from app.models.estimate import EstimateAPIResponse, EstimateRequest
from app.services.estimate_service import generate_estimate
from app.services.rate_limiter import UsageStatus, get_usage_status, plan_str

logger = logging.getLogger(__name__)
router = APIRouter(tags=["estimate"])


async def _save_estimate(
    result: EstimateAPIResponse,
    body: EstimateRequest,
    user: User,
    db: object,
) -> None:
    if db is None:
        return
    try:
        new_id = str(uuid.uuid4()).replace("-", "")
        await db.prepare(  # type: ignore[attr-defined]
            """INSERT INTO estimates (
                id, user_id, job_title, job_description, tech_stack, complexity,
                hourly_rate_min, hourly_rate_max, freelancer_name,
                ai_provider, amount_min, amount_max, hours_min, hours_max,
                difficulty, result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
        ).bind(
            new_id,
            user.id,
            body.job_title or "",
            body.job_description,
            json.dumps(body.tech_stack, ensure_ascii=False),
            body.complexity.value,
            body.hourly_rate_min,
            body.hourly_rate_max,
            body.freelancer_name or "フリーランサー",
            result.ai_provider,
            result.data.amount_min,
            result.data.amount_max,
            result.data.hours_min,
            result.data.hours_max,
            result.data.difficulty.value,
            json.dumps(result.data.model_dump(), ensure_ascii=False),
        ).run()
    except Exception as e:
        logger.warning("D1への見積もり保存に失敗: %s", e)


@router.post("/estimate/generate", response_model=EstimateAPIResponse)
async def generate_estimate_endpoint(
    body: EstimateRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user_with_limit),  # noqa: B008
    db: object = Depends(get_d1),  # noqa: B008
) -> EstimateAPIResponse:
    try:
        result = await generate_estimate(body, user_plan=plan_str(current_user))
        background_tasks.add_task(_save_estimate, result, body, current_user, db)
        return result
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except Exception as e:
        e_str = str(e)
        if "503" in e_str or "UNAVAILABLE" in e_str or "overloaded" in e_str.lower():
            raise HTTPException(
                status_code=503,
                detail="AIモデルが混雑しています。しばらくしてから再試行してください。",
            ) from e
        logger.exception("見積もり生成エラー")
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
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: object = Depends(get_d1),  # noqa: B008
) -> UsageResponse:
    s: UsageStatus = await get_usage_status(current_user, db)
    return UsageResponse(
        plan=s.plan,
        daily_used=s.daily_used,
        daily_limit=s.daily_limit,
        monthly_used=s.monthly_used,
        monthly_limit=s.monthly_limit,
        daily_remaining=s.daily_remaining,
        monthly_remaining=s.monthly_remaining,
    )


class EstimateHistoryItem(BaseModel):
    id: str
    title: str
    amount_min: int
    amount_max: int
    hours_min: int
    hours_max: int
    ai_provider: str
    created_at: str


class EstimateDetailResponse(BaseModel):
    id: str
    title: str
    ai_provider: str
    created_at: str
    result: dict


@router.get("/estimates/{estimate_id}", response_model=EstimateDetailResponse)
async def get_estimate_detail_endpoint(
    estimate_id: str,
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: object = Depends(get_d1),  # noqa: B008
) -> EstimateDetailResponse:
    if db is None:
        raise HTTPException(status_code=503, detail="データベースが無効です")
    try:
        row = await db.prepare(  # type: ignore[attr-defined]
            "SELECT id, job_title, ai_provider, created_at, result_json FROM estimates WHERE id = ? AND user_id = ?"
        ).bind(estimate_id, current_user.id).first()
    except Exception as e:
        logger.warning("D1からの見積もり詳細取得に失敗: %s", e)
        raise HTTPException(status_code=503, detail="データの取得に失敗しました") from e
    if not row:
        raise HTTPException(status_code=404, detail="見積もりが見つかりません")
    return EstimateDetailResponse(
        id=row["id"],
        title=row.get("job_title") or "（タイトルなし）",
        ai_provider=row["ai_provider"],
        created_at=row["created_at"],
        result=json.loads(row.get("result_json") or "{}"),
    )


@router.get("/estimates", response_model=list[EstimateHistoryItem])
async def list_estimates_endpoint(
    current_user: User = Depends(get_current_user),  # noqa: B008
    db: object = Depends(get_d1),  # noqa: B008
) -> list[EstimateHistoryItem]:
    if db is None:
        return []
    try:
        result = await db.prepare(  # type: ignore[attr-defined]
            """SELECT id, job_title, ai_provider, amount_min, amount_max,
                      hours_min, hours_max, created_at
               FROM estimates WHERE user_id = ? ORDER BY created_at DESC"""
        ).bind(current_user.id).all()
        rows = result.results if result else []
    except Exception as e:
        logger.warning("D1からの履歴取得に失敗: %s", e)
        return []
    return [
        EstimateHistoryItem(
            id=r["id"],
            title=r.get("job_title") or "（タイトルなし）",
            amount_min=r["amount_min"],
            amount_max=r["amount_max"],
            hours_min=r["hours_min"],
            hours_max=r["hours_max"],
            ai_provider=r["ai_provider"],
            created_at=str(r["created_at"])[:10],
        )
        for r in rows
    ]
