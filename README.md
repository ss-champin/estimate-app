# EstiMate

> エンジニア向け見積もり自動生成サービス
> ココナラ・ランサーズの案件URLを貼るだけで、AIがエンジニア相場に基づいた見積もりと返信文を即座に生成。

## 技術スタック

| レイヤー       | 技術                         | 備考              |
|------------|----------------------------|-----------------|
| Frontend   | Next.js 15 + TypeScript    | Vercel デプロイ     |
| Backend    | FastAPI + Python 3.12      | Fly.io デプロイ     |
| 認証         | Clerk                      | SSO・5万MAUまで無料  |
| DB（ユーザー）   | Neon (PostgreSQL)          | 20プロジェクトまで無料   |
| DB（見積もり）   | Cloudflare D1 (SQLite)     | CF Worker にバインド |
| AI Worker  | Cloudflare Workers + Containers | FastAPI コンテナを管理 |
| AI（開発）     | Gemini 2.5 Flash-Lite      | 無料枠・無料ユーザーも使用   |
| AI（本番）     | Claude Haiku 4.5           | 有料ユーザーのみ        |
| 決済         | Stripe                     |                 |
| バージョン管理    | mise                       |                 |

## 料金モデル

| プラン | 料金     | 生成上限       | AI           |
|-----|--------|------------|--------------|
| 無料  | ¥0     | 月3回        | Gemini       |
| Pro | ¥500/月 | 1日10回・月30回 | Claude Haiku |

---

## 🚀 クイックスタート

### 1. 前提ツールのインストール

```bash
# mise（バージョン管理 + タスクランナー）
curl https://mise.run | sh
echo 'eval "$(~/.local/bin/mise activate zsh)"' >> ~/.zshrc
source ~/.zshrc

# Docker（ローカルPostgreSQL + CF Worker コンテナ用）
# 選択肢A: Docker Desktop（推奨）
#   https://www.docker.com/products/docker-desktop/
# 選択肢B: Colima（軽量・無料）
brew install colima docker && colima start
```

> `mise run db:up` と `mise run dev:cf` は **Docker Desktop → Colima の順で自動検出**します。
> Colima を使う場合は `mise run dev` の前に `colima start` が必要です。

### 2. ツールのインストール

```bash
cd estimate-app

# Python 3.12 / Node 22 / uv / pnpm / ruff を一括インストール
mise install
```

### 3. 全環境セットアップ

```bash
# 依存関係インストール + .env ファイル作成 + D1 migration を一括実行
mise run setup
```

`setup` が行うこと：

| サブタスク | 内容 |
|----------|------|
| `setup:backend`  | `uv sync` + `backend/.env.local` テンプレート作成 |
| `setup:frontend` | `pnpm install` + `frontend/.env.local` テンプレート作成 |
| `setup:e2e`      | Playwright インストール |
| `setup:cf`       | CF Worker の `pnpm install` + D1 ローカル migration |

### 4. 環境変数の設定

```bash
# バックエンド（estimate-app）
vi backend/.env.local

# フロントエンド
vi frontend/.env.local
```

**必要なキー：**

| キー | 取得先 |
|-----|--------|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) → API Keys（無料） |
| `CLERK_SECRET_KEY` / `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | [dashboard.clerk.com](https://dashboard.clerk.com) → API Keys |
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `STRIPE_SECRET_KEY` など | [dashboard.stripe.com](https://dashboard.stripe.com) |

> **Clerk なし・AI キーなし**でも起動できます。その場合は `Authorization: Bearer local-dev` でバイパスされ、Gemini なしでは見積もり生成のみ失敗します。

### 5. ローカルDB起動 & マイグレーション

```bash
# Docker でPostgreSQL起動
mise run db:up

# PostgreSQL マイグレーション
mise run migrate
```

### 6. 開発サーバー起動

```bash
# フロントエンド・バックエンド・CF Worker を同時起動
mise run dev
```

| サービス | URL |
|--------|-----|
| Frontend | http://localhost:3000 |
| Backend (Swagger) | http://localhost:8000/docs |
| CF Worker | http://localhost:8787 |

> **CF Worker の初回起動は 20〜30 秒かかります**（Docker コンテナのコールドスタート）。
> 最初の `/health` リクエストで 503 が返るのは正常です。待ってから再アクセスしてください。

---

## タスク一覧

```bash
mise tasks                           # 全タスク確認

# セットアップ
mise run setup                       # 全環境を一括セットアップ
mise run setup:cf                    # CF Worker のみセットアップ

# 開発
mise run dev                         # 全サービス同時起動
mise run dev:backend                 # バックエンドのみ
mise run dev:frontend                # フロントエンドのみ
mise run dev:cf                      # CF Worker のみ

# PostgreSQL
mise run db:up                       # ローカルDB起動
mise run db:down                     # ローカルDB停止
mise run db:reset                    # DB完全リセット
mise run migrate                     # マイグレーション（ローカル）
APP_ENV=production mise run migrate  # マイグレーション（本番）

# D1（Cloudflare）
mise run d1:migrate:local            # D1 ローカル migration
mise run d1:migrate:remote           # D1 本番 migration

# 品質チェック
mise run check                       # Lint + Format + 型チェック
mise run check:fix                   # 自動修正
mise run test                        # 全テスト実行

# その他
mise run clean                       # キャッシュ削除
mise run reset                       # クリーン → 再セットアップ
mise run deploy                      # 本番デプロイ
```

---

## ディレクトリ構成

```
estimate/
├── estimate-app/                    # ← このディレクトリ（mise.toml の場所）
│   ├── README.md
│   ├── mise.toml                    # タスクランナー（CF Worker も管理）
│   ├── docker-compose.yml           # ローカルPostgreSQL
│   ├── backend/                     # FastAPI
│   │   ├── pyproject.toml
│   │   ├── .env.example
│   │   └── app/
│   │       ├── main.py
│   │       ├── api/                 # エンドポイント・認証
│   │       ├── models/              # Pydantic + SQLAlchemy
│   │       └── services/            # AI生成・レート制限
│   ├── frontend/                    # Next.js
│   │   ├── .env.local.example
│   │   └── src/
│   │       ├── app/                 # App Router（dashboard・estimate）
│   │       ├── components/          # UIコンポーネント
│   │       └── lib/                 # API クライアント・store
│   └── e2e/                         # Playwright
│
└── estimate-cf/                     # CF Worker（mise.toml から参照）
    ├── README.md                    # CF Worker の詳細説明
    ├── backend/                     # FastAPI（Docker コンテナ）
    │   └── app/main.py              # /estimates CRUD
    └── worker/                      # Cloudflare Worker (TypeScript)
        ├── wrangler.jsonc
        ├── .dev.vars                # ローカル開発用の環境変数
        ├── migrations/              # D1 スキーマ
        └── src/index.ts             # ルーター + D1 プロキシ
```
