from __future__ import annotations
import logging
from datetime import datetime, timezone
import httpx
from pydantic_ai import ModelRetry
from app.models.estimate import (
    BreakdownItem,
    Condition,
    ConditionType,
    EstimateDeps,
    EstimateAPIResponse,
    EstimateOutput,
    EstimateRequest,
)
from app.services.ai.agent import get_estimate_agent, get_model_name

logger = logging.getLogger(__name__)

WARN_NO_AI_KEY = (
    "AI APIキー（GEMINI_API_KEY / GOOGLE_API_KEY など）が未設定のため、"
    "サンプル見積もりを表示しています。`.env.local` にキーを設定すると実際のAI生成が有効になります。"
)

# システムプロンプトの「絶対最低ライン」に合わせる（円/h）
ABSOLUTE_MIN_RATE = 2500


def normalize_estimate_amounts(output: EstimateOutput, req: EstimateRequest) -> None:
    """
    希望時給の下限・上限と工程別工数から金額を整合させる。
    - 提案レンジ: amount_min = 下限時給×合計工数、amount_max = 上限時給×合計工数
    - 内訳テーブルは「上限時給」を単価に適用（最高側の見積もり）。小計合計 = amount_max
    """
    if not output.breakdown:
        return
    rmin = req.hourly_rate_min
    rmax = req.hourly_rate_max
    fixed: list[BreakdownItem] = []
    for b in output.breakdown:
        sub = b.hours * rmax
        fixed.append(
            BreakdownItem(
                phase=b.phase,
                hours=b.hours,
                rate=rmax,
                subtotal=sub,
                note=b.note,
            )
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
    output.amount_ceiling = int(rmax * sum_h * 1.2)
    if output.amount_ceiling < output.amount_max:
        output.amount_ceiling = max(int(output.amount_max * 1.12), output.amount_max + 1)

    if rmin < ABSOLUTE_MIN_RATE:
        output.warnings.append(
            f"希望時給の下限（¥{rmin:,}/h）が目安の絶対下限（¥{ABSOLUTE_MIN_RATE:,}/h）を下回ります。"
        )


def _mock_estimate_response(req: EstimateRequest) -> EstimateAPIResponse:
    name = req.freelancer_name or "フリーランサー"
    rmin, rmax = req.hourly_rate_min, req.hourly_rate_max
    out = EstimateOutput(
        amount_min=1,
        amount_max=1,
        amount_floor=1,
        amount_ceiling=1,
        hours_min=1,
        hours_max=1,
        deadline_days_min=10,
        deadline_days_max=14,
        hourly_rate_used=rmax,
        applied_hourly_min=rmin,
        applied_hourly_max=rmax,
        difficulty=req.complexity,
        difficulty_reason="（デモ）APIキー未設定のためテンプレート値です",
        breakdown=[
            BreakdownItem(phase="要件整理・設計", hours=5, rate=rmax, subtotal=5 * rmax, note="ヒアリング・画面遷移"),
            BreakdownItem(phase="実装", hours=22, rate=rmax, subtotal=22 * rmax, note="コア機能"),
            BreakdownItem(phase="テスト・デバッグ", hours=5, rate=rmax, subtotal=5 * rmax, note="結合・修正"),
            BreakdownItem(phase="修正バッファ", hours=4, rate=rmax, subtotal=4 * rmax, note="仕様微調整"),
        ],
        reply_message=(
            f"はじめまして、{name}です。\n"
            "ご依頼内容を拝見し、おおむね〇〇時間〜〇〇時間程度、"
            "ご予算〇〇万円前後でお受けできる見込みです（※デモ文面）。\n"
            "詳細はお打ち合わせですり合わせさせてください。"
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
        success=True,
        data=out,
        ai_provider="mock-offline",
        generated_at=datetime.now(timezone.utc).isoformat(),
    )


COMPLEXITY_LABEL = {
    "simple": "シンプル（LP・静的・小改修）",
    "standard": "標準（Webアプリ・API連携）",
    "complex": "複雑（大規模・設計から）",
}


def _log_preview(text: str | None, max_len: int | None = None) -> str:
    """max_len=None なら全文表示（ログに省略なし）。"""
    if not text or not text.strip():
        return "（なし）"
    one_line = " ".join(text.strip().split())
    if max_len is None or len(one_line) <= max_len:
        return one_line
    return one_line[: max_len - 1] + "…"


def _log_estimate_input_context(
    *,
    source: str,
    user_plan: str,
    req: EstimateRequest,
    tech: str,
    rate_label: str,
    job_body_chars: int,
    prompt_chars: int,
    ai_provider: str,
) -> None:
    desc = req.job_description or ""
    lines = [
        "┌─ 見積もり生成リクエスト ─── ① AIへの入力内容 ─────────────────────",
        f"│  [モデル]       {ai_provider}  (プラン: {user_plan})",
        f"│  [名前]         {req.freelancer_name or '（未指定）'}",
        f"│  [複雑度]       {COMPLEXITY_LABEL.get(req.complexity.value, req.complexity.value)}",
        f"│  [技術スタック] {tech}",
        f"│  [希望時給]     {rate_label}",
        f"│  [案件タイトル] {_log_preview(req.job_title)}",
        f"│  [案件本文]     {len(desc)}文字  全文→「{_log_preview(desc)}」",
        f"│  [入力経路]     ユーザー入力の job_title / job_description のみ",
        f"│  [プロンプト計] {prompt_chars}文字  (案件部分 {job_body_chars}文字)",
        f"│  [source]       {source}",
        "└────────────────────────────────────────────────────────────────",
    ]
    logger.info("\n".join(lines))


def _log_estimate_output_summary(
    *,
    source: str,
    user_plan: str,
    ai_provider: str,
    output: EstimateOutput,
) -> None:
    phases = "  /  ".join(
        f"{b.phase}（{b.hours}h, ¥{b.subtotal:,}）" for b in output.breakdown
    )
    warn_lines = (
        "\n".join(f"│    ⚠ {w}" for w in output.warnings) if output.warnings else "│    なし"
    )
    lines = [
        "└─ 見積もり生成完了 ──────── ② APIレスポンス (data) の内容 ──────────",
        f"│  [モデル]       {ai_provider}  (プラン: {user_plan})",
        f"│  [金額レンジ]   ¥{output.amount_min:,} 〜 ¥{output.amount_max:,}",
        f"│  [下限/上限]    フロア ¥{output.amount_floor:,} ／ シーリング ¥{output.amount_ceiling:,}",
        f"│  [工数]         {output.hours_min}h 〜 {output.hours_max}h",
        f"│  [使用時給]     ¥{output.hourly_rate_used:,}/h",
        f"│  [難易度]       {output.difficulty.value}  理由→「{_log_preview(output.difficulty_reason)}」",
        f"│  [工程内訳]     {phases}",
        f"│  [返信文全文]   「{_log_preview(output.reply_message)}」",
        f"│  [warnings]",
        warn_lines,
        f"│  [source]       {source}",
        "└────────────────────────────────────────────────────────────────",
    ]
    logger.info("\n".join(lines))


async def generate_estimate(req: EstimateRequest, user_plan: str = "free") -> EstimateAPIResponse:
    agent = get_estimate_agent(user_plan)
    if agent is None:
        logger.warning(
            "Gemini エージェントが使えません。backend/.env.local の GEMINI_API_KEY と "
            "サーバー再起動を確認してください（mock 見積もりを返します）。"
        )
        tech = "、".join(req.tech_stack) if req.tech_stack else "不明（AIが推定）"
        rate = (
            f"時給 {req.hourly_rate_min:,}〜{req.hourly_rate_max:,}円"
            if req.hourly_rate_min > 0 and req.hourly_rate_max > 0
            else f"時給 {req.hourly_rate_min:,}円以上"
            if req.hourly_rate_min > 0
            else "未指定"
        )
        _log_estimate_input_context(
            source="mock-offline（キーなし・テンプレ応答）",
            user_plan=user_plan,
            req=req,
            tech=tech,
            rate_label=rate,
            job_body_chars=len(req.job_description or ""),
            prompt_chars=0,
            ai_provider="mock-offline",
        )
        mock = _mock_estimate_response(req)
        _log_estimate_output_summary(
            source="mock-offline（キーなし・テンプレ応答）",
            user_plan=user_plan,
            ai_provider="mock-offline",
            output=mock.data,
        )
        return mock

    tech = "、".join(req.tech_stack) if req.tech_stack else "不明（AIが推定）"
    rate = (
        f"時給 {req.hourly_rate_min:,}〜{req.hourly_rate_max:,}円"
        if req.hourly_rate_min > 0 and req.hourly_rate_max > 0
        else f"時給 {req.hourly_rate_min:,}円以上"
        if req.hourly_rate_min > 0
        else "未指定"
    )

    job_body = req.job_description or "（未指定）"

    complexity_value = req.complexity.value
    complexity_label = COMPLEXITY_LABEL.get(complexity_value, complexity_value)
    prompt = f"""以下の案件情報をもとに見積もりを生成してください。

## 案件基本情報
- 複雑度（ユーザー指定・必ずこの値を difficulty に使うこと）: {complexity_label}（値: {complexity_value}）
- 使用技術: {tech}
- 希望時給: {rate}
- フリーランサー名: {req.freelancer_name}

## 案件タイトル
{req.job_title or "（未指定）"}

## 案件内容
{job_body}

## 希望時給（ユーザー入力・税抜）
- 下限: {req.hourly_rate_min:,} 円/h ／ 上限: {req.hourly_rate_max:,} 円/h
- 提案金額のレンジはサーバーで「下限×合計工数〜上限×合計工数」に揃えます。breakdown の rate/subtotal は後から上書きされるため、**工程ごとの工数（hours）と工程名・note**を重視してください。

## 指示
1. 上記「案件タイトル」「案件内容」のみを根拠に見積もりを作成してください
2. difficulty フィールドは必ず「{complexity_value}」にすること（ユーザー指定を優先）
3. 案件内容を読んで「{complexity_value}」と実態が乖離していると感じたら warnings に警告を追記すること
4. conditions は revision/delivery/spec_change/payment/copyright の5種類を必ず含めてください
5. reply_message は「{req.freelancer_name}」を名乗る自然な日本語で作成し、金額は希望時給の範囲と工数に沿う旨を述べてください
6. breakdown は4工程。各 phase の hours は正の整数。rate と subtotal は仮値でよい（サーバーで希望上限時給に基づき再計算されます）
""".strip()

    provider = get_model_name(user_plan)
    _log_estimate_input_context(
        source="ai_generate（プロンプト投入）",
        user_plan=user_plan,
        req=req,
        tech=tech,
        rate_label=rate,
        job_body_chars=len(job_body),
        prompt_chars=len(prompt),
        ai_provider=provider,
    )

    async with httpx.AsyncClient() as http_client:
        deps = EstimateDeps(
            http_client=http_client,
            freelancer_name=req.freelancer_name,
            user_plan=user_plan,
        )
        try:
            result = await agent.run(prompt, deps=deps)
            output = result.output
        except ModelRetry as e:
            logger.error("Agent最大リトライ超過: %s", e)
            raise ValueError("AIの出力を解析できませんでした。再試行してください。") from e

    normalize_estimate_amounts(output, req)

    _log_estimate_output_summary(
        source="ai_generate（成功）",
        user_plan=user_plan,
        ai_provider=provider,
        output=output,
    )

    return EstimateAPIResponse(
        success=True,
        data=output,
        ai_provider=provider,
        generated_at=datetime.now(timezone.utc).isoformat(),
    )
