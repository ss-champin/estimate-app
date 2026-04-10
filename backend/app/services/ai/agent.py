from __future__ import annotations
import logging
import os
import threading
from pydantic_ai import Agent
from pydantic_ai.output import NativeOutput
from app.models.estimate import EstimateDeps, EstimateOutput

logger = logging.getLogger(__name__)

MODEL_FREE = "google-gla:gemini-2.5-flash-lite"
MODEL_PAID = "anthropic:claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """
あなたはフリーランスエンジニア専門の見積もりアドバイザーAIです。

## 役割
ユーザーが入力した案件タイトル・案件内容を分析し、
エンジニアが適正価格で受注できるよう、見積もり金額・工数・返信文・取引条件を生成します。

## エンジニア相場（日本・2025年）

### 技術スタック別 時給目安
- HTML/CSS/jQuery のみ: 2,000〜3,000円/h
- React/Vue（フロントのみ）: 3,000〜5,000円/h
- TypeScript 使用: +500〜1,000円/h
- Next.js/Nuxt（フルスタック）: 4,000〜6,000円/h
- バックエンド（FastAPI/Django）: 3,500〜5,500円/h
- AWS/インフラ: 5,000〜8,000円/h
- Stripe連携: +10,000〜30,000円（固定）
- スマホアプリ: 5,000〜8,000円/h

### 複雑度別工数目安
- simple: 5〜30h
- standard: 30〜80h
- complex: 80h〜

## 工程分解ルール（必ず4工程）
1. 要件整理・設計: 全体の10〜15%
2. 実装: 全体の55〜65%
3. テスト・デバッグ: 全体の15〜20%
4. 修正バッファ: 全体の10〜15%

## 金額・内訳（サーバーで確定。AIは工数の配分を担当）
- ユーザーが入力した希望時給の下限・上限（円/h）と、breakdown の各工程の hours から、サーバーが次を計算する:
  - 提案レンジ（税抜）の下限 = 希望時給下限 × 合計工数、上限 = 希望時給上限 × 合計工数
  - 工程別内訳の単価・小計は「希望時給の上限」を単価に適用した場合（小計合計 = 上限側の提案額）
- breakdown は必ず4工程。hours は正の整数。rate/subtotal は仮値でよい（上書きされる）。

## 複雑度（difficulty）の扱いルール【最重要】
- ユーザーが指定した complexity を最優先で採用し、difficulty フィールドに必ずその値をセットすること。
- ただし案件内容を読んだ結果、ユーザー指定の複雑度と実態が異なると判断した場合は、
  difficulty はユーザー指定のまま維持しつつ、warnings に以下の形式で1件追加すること:
  「⚠ ご指定の複雑度は「{ユーザー指定}」ですが、案件内容から判断すると「{AI推定}」に近い可能性があります。
     工数・金額が想定と異なる場合は複雑度を変更して再生成することをご検討ください。（理由: {簡潔な根拠}）」
- 複雑度が一致していると判断した場合は warnings に複雑度に関する記述は不要。

## conditions は必ず5種類含める
revision / delivery / spec_change / payment / copyright
""".strip()


_agent_lock = threading.Lock()
_agent_free: Agent[EstimateDeps, EstimateOutput] | None = None
_agent_paid: Agent[EstimateDeps, EstimateOutput] | None = None
_agents_initialized = False


def _ensure_google_env() -> None:
    from app.core.config import apply_ai_keys_to_environ

    apply_ai_keys_to_environ()


def _google_key_available() -> bool:
    _ensure_google_env()
    return bool((os.getenv("GOOGLE_API_KEY") or "").strip())


def _anthropic_key_available() -> bool:
    return bool((os.getenv("ANTHROPIC_API_KEY") or "").strip())


def _make_agent(model: str) -> Agent[EstimateDeps, EstimateOutput]:
    # Google/Gemini は NativeOutput と function tools の併用不可のため、
    # 案件本文はプロンプトに含めて渡す（pydantic_ai UserError 回避）。
    return Agent(
        model=model,
        deps_type=EstimateDeps,
        output_type=NativeOutput(EstimateOutput),
        system_prompt=SYSTEM_PROMPT,
    )


def _init_agents_if_needed() -> None:
    global _agent_free, _agent_paid, _agents_initialized
    with _agent_lock:
        if _agents_initialized:
            return
        _ensure_google_env()
        _agents_initialized = True
        if _google_key_available():
            try:
                _agent_free = _make_agent(MODEL_FREE)
            except Exception as e:
                logger.warning("無料枠AIエージェントの初期化に失敗しました（キー未設定の可能性）: %s", e)
        if _anthropic_key_available():
            try:
                _agent_paid = _make_agent(MODEL_PAID)
            except Exception as e:
                logger.warning("有料枠AIエージェントの初期化に失敗しました: %s", e)


def ai_agents_available() -> bool:
    _init_agents_if_needed()
    return _agent_free is not None


def get_estimate_agent(user_plan: str = "free") -> Agent[EstimateDeps, EstimateOutput] | None:
    _init_agents_if_needed()
    if _agent_free is None:
        return None
    is_local = os.getenv("APP_ENV", "local") == "local"
    if is_local or user_plan != "paid":
        return _agent_free
    if _agent_paid is not None:
        return _agent_paid
    return _agent_free


def get_model_name(user_plan: str = "free") -> str:
    _init_agents_if_needed()
    if _agent_free is None:
        return "mock-offline"
    is_local = os.getenv("APP_ENV", "local") == "local"
    if is_local or user_plan != "paid":
        return "gemini-2.5-flash-lite"
    if _agent_paid is not None:
        return "claude-haiku-4-5"
    return "gemini-2.5-flash-lite"
