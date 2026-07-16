from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import httpx
from pydantic import BaseModel, Field, field_validator, model_validator


class Complexity(str, Enum):
    simple = "simple"
    standard = "standard"
    complex = "complex"


class ConditionType(str, Enum):
    revision = "revision"
    delivery = "delivery"
    spec_change = "spec_change"
    payment = "payment"
    copyright = "copyright"


class EstimateRequest(BaseModel):
    job_title: str | None = Field(None)
    job_description: str = Field(..., min_length=10)
    tech_stack: list[str] = Field(default_factory=list)
    complexity: Complexity = Field(Complexity.standard)
    hourly_rate_min: int = Field(..., ge=1, description="希望時給の下限（円/h）")
    hourly_rate_max: int = Field(..., ge=1, description="希望時給の上限（円/h）")
    freelancer_name: str = Field("フリーランサー")

    @field_validator("job_description")
    @classmethod
    def strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("案件内容を入力してください")
        return v

    @model_validator(mode="after")
    def hourly_range_order(self) -> EstimateRequest:
        if self.hourly_rate_min > self.hourly_rate_max:
            raise ValueError("希望時給の下限が上限を超えています")
        return self


@dataclass
class EstimateDeps:
    http_client: httpx.AsyncClient
    freelancer_name: str
    user_plan: str = "free"


class BreakdownItem(BaseModel):
    phase: str = Field(...)
    hours: int = Field(..., gt=0)
    rate: int = Field(..., gt=0)
    subtotal: int = Field(..., gt=0)
    note: str = Field("")


class Condition(BaseModel):
    type: ConditionType = Field(...)
    text: str = Field(...)


class EstimateOutput(BaseModel):
    amount_min: int = Field(..., gt=0)
    amount_max: int = Field(..., gt=0)
    amount_floor: int = Field(..., gt=0)
    amount_ceiling: int = Field(..., gt=0)
    hours_min: int = Field(..., gt=0)
    hours_max: int = Field(..., gt=0)
    deadline_days_min: int = Field(..., gt=0)
    deadline_days_max: int = Field(..., gt=0)
    hourly_rate_used: int = Field(
        ..., gt=0, description="内訳に用いた単価（希望時給の上限・円/h）"
    )
    applied_hourly_min: int = Field(..., gt=0, description="提案下限の計算に使った時給（円/h）")
    applied_hourly_max: int = Field(..., gt=0, description="提案上限・内訳に使った時給（円/h）")
    difficulty: Complexity = Field(...)
    difficulty_reason: str = Field(...)
    breakdown: list[BreakdownItem] = Field(..., min_length=1)
    reply_message: str = Field(...)
    conditions: list[Condition] = Field(..., min_length=5)
    warnings: list[str] = Field(default_factory=list)


class EstimateAPIResponse(BaseModel):
    success: bool = True
    data: EstimateOutput
    ai_provider: str
    generated_at: str
