from __future__ import annotations

import logging
from datetime import UTC, datetime

from app.models.estimate import (
    BreakdownItem,
    Condition,
    ConditionType,
    EstimateAPIResponse,
    EstimateOutput,
    EstimateRequest,
)
from app.services.ai.agent import (
    SYSTEM_PROMPT,  # noqa: F401 — re-export for tests
    ai_agents_available,
    call_claude,
    call_gemini,
    get_model_name,
)

logger = logging.getLogger(__name__)

WARN_NO_AI_KEY = (
    "AI APIキー（GEMINI_API_KEY など）が未設定のため、"
    "サンプル見積もりを表示しています。キーを設定すると実際のAI生成が有効になります。"
)

ABSOLUTE_MIN_RATE = 2500

COMPLEXITY_LABEL = {
    "simple": "シンプル（LP・静的・小改修）",
    "standard": "標準（Webアプリ・API連携）",
    "complex": "複雑（大規模・設計から）",
}


def normalize_estimate_amounts(output: EstimateOutput, req: EstimateRequest) -> None:
    if not output.breakdown:
        return
    rmin = req.hourly_rate_min
    rmax = req.hourly_rate_max
    fixed: list[BreakdownItem] = []
    for b in output.breakdown:
        fixed.append(
            BreakdownItem(phase=b.phase, hours=b.hours, rate=rmax, subtotal=b.hours * rmax, note=b.note)
        )
    output.breakdown = fixed
    sum_h = sum(b.hours for b in fixed)
    output.hours_min = sum_h
    output.hours_max = sum_h
    output.amount_min = rmin * sum_h
    output.amount_max = rmax * sum_h
    output.hourly_rate_used = rmax
    output.applied_hourly_min = rmin
    output.applied_hourly_max = rmax
    output.amount_floor = ABSOLUTE_MIN_RATE * sum_h
    output.amount_ceiling = max(int(rmax * sum_h * 1.2), output.amount_max + 1)
    if rmin < ABSOLUTE_MIN_RATE:
        output.warnings.append(
            f"希望時給の下限（¥{rmin:,}/h）が目安の絶対下限（¥{ABSOLUTE_MIN_RATE:,}/h）を下回ります。"
        )


def _mock_estimate_response(req: EstimateRequest) -> EstimateAPIResponse:
    name = req.freelancer_name or "フリーランサー"
    rmin, rmax = req.hourly_rate_min, req.hourly_rate_max
    out = EstimateOutput(
        amount_min=1, amount_max=1, amount_floor=1, amount_ceiling=1,
        hours_min=1, hours_max=1, deadline_days_min=10, deadline_days_max=14,
        hourly_rate_used=rmax, applied_hourly_min=rmin, applied_hourly_max=rmax,
        difficulty=req.complexity, difficulty_reason="（デモ）APIキー未設定のためテンプレート値です",
        breakdown=[
            BreakdownItem(phase="要件整理・設計", hours=5, rate=rmax, subtotal=5 * rmax, note="ヒアリング・画面遷移"),
            BreakdownItem(phase="実装", hours=22, rate=rmax, subtotal=22 * rmax, note="コア機能"),
            BreakdownItem(phase="テスト・デバッグ", hours=5, rate=rmax, subtotal=5 * rmax, note="結合・修正"),
            BreakdownItem(phase="修正バッファ", hours=4, rate=rmax, subtotal=4 * rmax, note="仕様微調整"),
        ],
        reply_message=(
            f"はじめまして、{name}です。\n"
            "ご依頼内容を拝見し、おおむね〇〇時間〜〇〇時間程度、"
            "ご予算〇〇万円前後でお受けできる見込みです（※デモ文面）。"
        ),
        conditions=[
            Condition(type=ConditionType.revision, text="修正は契約範囲内で2回まで。それ以降は別途お見積り"),
            Condition(type=ConditionType.delivery, text="マイルストーンごとに確認をお願いします"),
            Condition(type=ConditionType.spec_change, text="仕様追加は都度見積もり・スケジュール調整"),
            Condition(type=ConditionType.payment, text="着手金50%・納品時50%を想定"),
            Condition(type=ConditionType.copyright, text="成果物の著作権は支払完了後に譲渡"),
        ],
        warnings=[WARN_NO_AI_KEY],
    )
    normalize_estimate_amounts(out, req)
    return EstimateAPIResponse(
        success=True, data=out, ai_provider="mock-offline",
        generated_at=datetime.now(UTC).isoformat(),
    )


def _build_prompt(req: EstimateRequest) -> str:
    tech = "、".join(req.tech_stack) if req.tech_stack else "不明（AIが推定）"
    rate = (
        f"時給 {req.hourly_rate_min:,}〜{req.hourly_rate_max:,}円"
        if req.hourly_rate_min > 0 and req.hourly_rate_max > 0
        else f"時給 {req.hourly_rate_min:,}円以上"
    )
    cv = req.complexity.value
    cl = COMPLEXITY_LABEL.get(cv, cv)
    return f"""以下の案件情報をもとに見積もりを生成してください。

## 案件基本情報
- 複雑度（ユーザー指定・必ずこの値を difficulty に使うこと）: {cl}（値: {cv}）
- 使用技術: {tech}
- 希望時給: {rate}
- フリーランサー名: {req.freelancer_name}

## 案件タイトル
{req.job_title or "（未指定）"}

## 案件内容
{req.job_description or "（未指定）"}

## 指示
1. 上記「案件タイトル」「案件内容」のみを根拠に見積もりを作成してください
2. difficulty フィールドは必ず「{cv}」にすること（ユーザー指定を優先）
3. 案件内容を読んで「{cv}」と実態が乖離していると感じたら warnings に警告を追記すること
4. conditions は revision/delivery/spec_change/payment/copyright の5種類を必ず含めてください
5. reply_message は「{req.freelancer_name}」を名乗る自然な日本語で作成してください
6. breakdown は4工程。各 phase の hours は正の整数。rate と subtotal は仮値でよい

## 出力形式（JSON）
EstimateOutput スキーマに従った JSON を出力してください。
amount_min/max/floor/ceiling/hourly_rate_used/applied_hourly_min/applied_hourly_max は
サーバーで再計算するため仮値（1）でよいです。hours_min/hours_max も breakdown から算出します。
""".strip()


async def generate_estimate(req: EstimateRequest, user_plan: str = "free") -> EstimateAPIResponse:
    if not ai_agents_available():
        logger.warning("GEMINI_API_KEY 未設定 → mock 見積もりを返します")
        return _mock_estimate_response(req)

    provider = get_model_name(user_plan)
    prompt = _build_prompt(req)
    logger.info("AI 生成開始: provider=%s plan=%s", provider, user_plan)

    try:
        if provider == "claude-haiku-4-5-20251001":
            output = await call_claude(prompt)
        else:
            output = await call_gemini(prompt)
    except Exception as e:
        e_str = str(e)
        if "503" in e_str or "UNAVAILABLE" in e_str or "overloaded" in e_str.lower():
            raise
        logger.exception("AI 生成エラー")
        raise ValueError(f"AIの出力を解析できませんでした: {e}") from e

    normalize_estimate_amounts(output, req)
    logger.info(
        "AI 生成完了: amount=%d〜%d hours=%d",
        output.amount_min, output.amount_max, output.hours_min,
    )
    return EstimateAPIResponse(
        success=True, data=output, ai_provider=provider,
        generated_at=datetime.now(UTC).isoformat(),
    )
