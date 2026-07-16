# Cloudflare 完全無料化 移行計画

**目標**: PostgreSQL (Neon) + Containers → D1 + Python Workers + Pages に移行し、コスト $0 を実現する

**想定作業時間**: 半日〜1日

---

## 現状 → 目標

```
現状                              目標
──────────────────────────────    ──────────────────────────────
Next.js   → CF Workers (OpenNext) Next.js   → CF Pages (無料)
FastAPI   → CF Containers (有料)  FastAPI   → CF Python Workers (無料)
PostgreSQL  (Neon)                D1 (estimate-cf と統合)
D1          (estimate-cf)         D1 (そのまま)
```

---

## 変更ファイル一覧

| ファイル | 変更内容 |
|---|---|
| `estimate-cf/worker/migrations/` | users / api_usage テーブルを D1 に追加 |
| `estimate-cf/worker/wrangler.jsonc` | — (変更なし) |
| `estimate-app/worker/wrangler.jsonc` | D1 バインディング追加・DATABASE_URL 削除 |
| `estimate-app/worker/src/index.ts` | DATABASE_URL を envVars から削除 |
| `estimate-app/backend/app/api/deps.py` | SQLAlchemy → D1 バインディング |
| `estimate-app/backend/app/services/rate_limiter.py` | SQLAlchemy → D1 バインディング |
| `estimate-app/backend/app/services/ai/agent.py` | pydantic-ai → httpx 直接呼び出し（要確認） |
| `estimate-app/backend/app/core/database.py` | 削除 |
| `estimate-app/backend/app/models/db.py` | SQLAlchemy ORM → 軽量 dataclass |
| `estimate-app/backend/pyproject.toml` | asyncpg / SQLAlchemy / alembic / uvicorn 削除 |
| `estimate-app/backend/app/main.py` | ASGI ハンドラ形式に変更 |
| `estimate-app/frontend/wrangler.toml` | Workers → Pages 設定に変更 |
| `estimate-app/frontend/package.json` | @opennextjs/cloudflare → @cloudflare/next-on-pages |
| `estimate-app/mise.toml` | deploy タスク更新 |
| `estimate-app/worker/scripts/set-secrets.sh` | DATABASE_URL 行を削除 |

---

## チェックリスト

### Phase 0｜事前確認（作業前に必ず実施）

- [x] **0-1** `pydantic-ai` → **非対応**。httpx 直接呼び出しに置換済み
- [x] **0-2** `python-jose[cryptography]` → **そのまま使用**（CF が cryptography を同梱）
- [x] **0-3** `slowapi` → **削除**（Workers にはメモリ永続なし、CF 側で制限）
- [x] **0-4** D1 スキーマ確認 → 既存テーブル（users / api_usage）をそのまま使用

---

### Phase 1｜D1 スキーマ拡張

**目的**: users / api_usage テーブルを estimate-cf の D1 に追加する

- [x] **1-1** D1 migration ファイル不要（既存 0001_init_schema.sql に users / api_usage テーブルが存在）
  - パス: `estimate-cf/worker/migrations/0002_add_users.sql`
  - 内容:
    ```sql
    CREATE TABLE IF NOT EXISTS users (
      id         TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
      clerk_id   TEXT NOT NULL UNIQUE,
      plan       TEXT NOT NULL DEFAULT 'free',
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS api_usage (
      id         TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(16)))),
      clerk_id   TEXT NOT NULL,
      usage_date TEXT NOT NULL,
      count      INTEGER NOT NULL DEFAULT 0,
      UNIQUE(clerk_id, usage_date)
    );
    ```

- [x] **1-2** ローカルで D1 migration 確認（estimate-cf setup 時に適用済み）
- [x] **1-3** D1 に users / api_usage テーブルが存在することを確認

---

### Phase 2｜バックエンド DB 層の書き直し

**目的**: SQLAlchemy を D1 バインディングに置き換える

- [x] **2-1** `worker/wrangler.jsonc` に D1 バインディングを追加（Python Workers 設定に全面変更）
- [x] **2-2** `worker/src/index.ts` を削除（Python Workers では不要）
- [x] **2-3** `backend/app/models/db.py` を dataclass に書き直し
- [x] **2-4** `backend/app/api/deps.py` を D1 版に書き直し（INSERT OR IGNORE + SELECT）
- [x] **2-5** `backend/app/services/rate_limiter.py` を D1 版に書き直し
- [x] **2-6** `backend/app/core/database.py` を空にした（削除済み同等）
- [x] **2-7** `backend/app/api/routes/estimate.py` から `AsyncSession` 依存を削除
- [x] **2-8** `backend/app/main.py` で D1 バインディングを middleware で注入
- [ ] **2-9** ローカルで動作確認（wrangler dev でテスト）

---

### Phase 3｜Python Workers 対応

**目的**: Container を不要にして Python Workers で FastAPI を動かす

- [x] **3-1** `pydantic-ai` は Python Workers 非対応 → httpx 直接呼び出しに変更
- [x] **3-1a** `backend/app/services/ai/agent.py` を httpx ベースに書き直し（Gemini JSON mode + Claude tool_use）
- [x] **3-2** `backend/pyproject.toml` から不要な依存を削除（6 パッケージのみに絞り込み）
- [x] **3-3** `backend/app/core/config.py` を pure os.environ の dataclass に変更
- [x] **3-4** `backend/app/main.py` を Python Workers 対応 ASGI ハンドラに変更
- [x] **3-5** `worker/wrangler.jsonc` を Python Workers 設定に変更（compatibility_flags + D1 binding）
- [x] **3-6** `worker/scripts/set-secrets.sh` から `DATABASE_URL` を削除
- [ ] **3-7** Python Workers でローカル動作確認
  ```bash
  cd estimate-app/worker
  pnpm exec wrangler dev
  ```

---

### Phase 4｜フロントエンド → Cloudflare Workers（現状維持）

**調査結果**: `@cloudflare/next-on-pages` は Next.js 15.5.2 までしか対応しておらず、**このプロジェクトは Next.js 16.2.10 を使用**しているため移行不可。  
また Cloudflare Pages の動的コンテンツも Workers Free Tier と同じ 100K リクエスト/日の制限があるため、`@opennextjs/cloudflare` + Workers のままで十分無料枠に収まる。

- [x] **4-1** `@cloudflare/next-on-pages` は使用不可（deprecated + Next.js 16 非対応）と確認。`@opennextjs/cloudflare@1.20.1` を維持
- [x] **4-2** `frontend/wrangler.toml` は現状の Workers 設定のまま（変更なし）
- [x] **4-3** `open-next.config.ts` は `defineCloudflareConfig()` で設定済み（変更なし）
- [x] **4-4** ローカルビルド確認 → `OpenNext build complete.` ✓（`middleware.ts` は `proxy.ts` 非対応のため現状維持）

---

### Phase 5｜本番デプロイ

- [ ] **5-1** D1 本番 migration 実行 + estimate-cf をシンプルな Worker に更新してデプロイ
  ```bash
  cd estimate-app
  mise run deploy:cf
  ```
  > estimate-cf は Container 依存を除去し、D1 migration 管理専用の軽量 Worker に変更済み

- [ ] **5-2** バックエンド（Python Workers）をデプロイ
  ```bash
  mise run deploy:backend
  ```

- [ ] **5-3** `FRONTEND_URL` シークレットを設定（初回デプロイ前）
  ```bash
  cd estimate-app/worker
  bash scripts/set-secrets.sh
  ```

- [ ] **5-4** フロントエンド（Workers + OpenNext）をデプロイ
  ```bash
  # STEP: .env.production に NEXT_PUBLIC_API_URL を設定してから実行
  cd estimate-app && mise run deploy:frontend
  ```

- [ ] **5-5** 本番でエンドツーエンド動作確認
  - [ ] ログイン（Clerk）
  - [ ] 見積もり生成
  - [ ] 履歴一覧・詳細
  - [ ] 利用回数カウント
  - [ ] 月次リセット確認（不要。ロジックで計算）

---

### Phase 6｜クリーンアップ

- [ ] **6-1** Neon (PostgreSQL) のプロジェクトを削除（不要になったため）
- [ ] **6-2** `backend/migrations/` (alembic) ディレクトリを削除
- [ ] **6-3** `backend/.env.local` から `DATABASE_URL` を削除
- [ ] **6-4** `README.md` の技術スタック表を更新（Neon → D1、Containers → Python Workers）
- [ ] **6-5** `DEPLOY.md` の手順を更新

---

## リスクと対策

| リスク | 対策 |
|---|---|
| `pydantic-ai` が Python Workers 非対応 | httpx で Gemini/Claude を直接呼ぶ（実装量 +2〜3時間） |
| `python-jose` が非対応 | `PyJWT` + `cryptography`（CF サポート済み）に切り替え |
| D1 の SQLite 構文が PostgreSQL と差異 | `INSERT OR IGNORE`、`datetime('now')` など SQLite 方言で記述 |
| Python Workers のコールドスタート遅延 | 許容範囲（Containers より速い見込み） |
| Stripe Webhook が Python Workers 非対応 | `stripe` パッケージを `httpx` 直接呼び出しに変更 |

---

## 進め方

作業は **Phase 0 → 1 → 2 → 3 → 4 → 5** の順に進めてください。  
Phase 0 の確認結果で Phase 3 の作業量が決まるため、**0 を先に終わらせること**が重要です。

準備ができたら「Phase 0 から始める」と声をかけてください。
