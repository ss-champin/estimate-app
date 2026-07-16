from __future__ import annotations

import json
import logging
import os

import httpx

from app.models.estimate import EstimateOutput

logger = logging.getLogger(__name__)

MODEL_FREE = "gemini-2.5-flash-lite"
MODEL_PAID = "claude-haiku-4-5-20251001"

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


def gemini_key() -> str:
    return os.environ.get("GEMINI_API_KEY", "")


def anthropic_key() -> str:
    return os.environ.get("ANTHROPIC_API_KEY", "")


def get_model_name(user_plan: str = "free") -> str:
    is_local = os.environ.get("APP_ENV", "local") == "local"
    if is_local or user_plan != "paid" or not anthropic_key():
        return MODEL_FREE
    return MODEL_PAID


def ai_agents_available() -> bool:
    return bool(gemini_key())


async def call_gemini(prompt: str) -> EstimateOutput:
    api_key = gemini_key()
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.5-flash-lite:generateContent?key={api_key}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.3,
        },
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()

    candidates = data.get("candidates", [])
    if not candidates:
        raise ValueError(f"Gemini レスポンスに candidates がありません: {data}")
    text = candidates[0]["content"]["parts"][0]["text"]
    return EstimateOutput.model_validate(json.loads(text))


async def call_claude(prompt: str) -> EstimateOutput:
    api_key = anthropic_key()
    schema = EstimateOutput.model_json_schema()
    payload = {
        "model": MODEL_PAID,
        "max_tokens": 4096,
        "system": SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": prompt}],
        "tools": [
            {
                "name": "create_estimate",
                "description": "見積もりデータを構造化して返す",
                "input_schema": schema,
            }
        ],
        "tool_choice": {"type": "tool", "name": "create_estimate"},
    }
    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()

    tool_block = next((b for b in data.get("content", []) if b.get("type") == "tool_use"), None)
    if not tool_block:
        raise ValueError(f"Claude レスポンスに tool_use ブロックがありません: {data}")
    return EstimateOutput.model_validate(tool_block["input"])
