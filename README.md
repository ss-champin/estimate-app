# EstiMate

> エンジニア向け見積もり自動生成サービス
> ココナラ・ランサーズの案件URLを貼るだけで、AIがエンジニア相場に基づいた見積もりと返信文を即座に生成。

## 技術スタック


| レイヤー     | 技術                      | 備考            |
| -------- | ----------------------- | ------------- |
| Frontend | Next.js 15 + TypeScript | Vercel デプロイ   |
| Backend  | FastAPI + Python 3.12   | Fly.io デプロイ   |
| 認証       | Clerk                   | SSO・5万MAUまで無料 |
| DB       | Neon (PostgreSQL)       | 20プロジェクトまで無料  |
| AI（開発）   | Gemini 2.5 Flash-Lite   | 無料枠・無料ユーザーも使用 |
| AI（本番）   | Claude Haiku 4.5        | 有料ユーザーのみ      |
| 決済       | Stripe                  |               |
| バージョン管理  | mise                    |               |


## 料金モデル


| プラン | 料金     | 生成上限       | AI           |
| --- | ------ | ---------- | ------------ |
| 無料  | ¥0     | 月3回        | Gemini       |
| Pro | ¥500/月 | 1日10回・月30回 | Claude Haiku |


## 🚀 クイックスタート（ZIP解凍後）

### 1. 前提ツールのインストール

```bash
# mise をインストール（初回のみ）
curl https://mise.run | sh　　　→　　brew install mise
echo 'eval "$(~/.local/bin/mise activate zsh)"' >> ~/.zshrc
source ~/.zshrc

# Docker Desktop はローカル PostgreSQL を使う場合のみ（`mise run dev` 単体では不要）
```

### 2. 全環境セットアップ

```bash
cd estimate-app

# Python 3.12 / Node 20 / uv / pnpm / ruff を一括インストール
mise install

# 依存関係インストール + .env ファイル作成
mise run setup
```

### 3. 環境変数の設定

```bash
# バックエンド
cp backend/.env.example backend/.env.local
# → backend/.env.local を編集してAPIキーを設定

# フロントエンド
cp frontend/.env.local.example frontend/.env.local
# → frontend/.env.local を編集してClerkキーを設定
```

**取得が必要なキー：**

- **Clerk**: [Dashboard](https://dashboard.clerk.com) → **Publishable key**（フロント）・**Secret key**（バックエンド任意）・**JWT public key**（API でトークン検証に必須）・必要なら **JWT の `iss`**（`CLERK_JWT_ISSUER`）・**Webhooks** で `https://<APIホスト>/api/clerk/webhook` と **Signing secret**（`CLERK_WEBHOOK_SECRET`、本番は必須）
- **Gemini**: [https://aistudio.google.com](https://aistudio.google.com) → API Keys（開発用・無料）
- **Anthropic**: [https://console.anthropic.com](https://console.anthropic.com) → API Keys（本番用）
- **Stripe**: [https://dashboard.stripe.com](https://dashboard.stripe.com) → Developers → API Keys

### 4. ローカルDB（任意）

`DATABASE_URL` を空のままなら DB なしで開発できます。

PostgreSQL を使う場合は Docker で起動し、マイグレーションを実行します。

```bash
mise run db:up
mise run migrate
```

### 5. 開発サーバー起動

```bash
# フロントエンド + バックエンド（Docker / DB 不要）
mise run dev

# DB コンテナも一緒に立ち上げてから開発する場合
mise run dev:with-db

# → Frontend: http://localhost:3000
# → Backend:  http://localhost:8000/docs（Swagger UI）
```

## タスク一覧

```bash
mise tasks                           # 全タスク確認
mise run setup                       # 全環境セットアップ
mise run dev                         # 開発サーバー起動（DB 不要）
mise run dev:with-db                  # Docker PostgreSQL 起動 → 開発サーバー
mise run db:up                       # ローカルDB起動
mise run db:down                     # ローカルDB停止
mise run migrate                     # マイグレーション（ローカル）
APP_ENV=production mise run migrate  # マイグレーション（本番）
mise run test                        # 全テスト実行
mise run check                       # Lint + Format + 型チェック
mise run check:fix                   # 自動修正
mise run clean                       # キャッシュ削除
mise run reset                       # クリーン → 再セットアップ
mise run deploy                      # 本番デプロイ
mise run logs:backend                # Fly.io ログ確認
```

## ディレクトリ構成

```
estimate-app/
├── README.md
├── mise.toml                    # タスクランナー
├── docker-compose.yml           # ローカルPostgreSQL
├── .gitignore
├── .github/workflows/ci.yml     # CI/CD
├── backend/                     # FastAPI
│   ├── pyproject.toml           # uv・ruff・ty設定
│   ├── fly.toml                 # Fly.io設定
│   ├── Dockerfile
│   ├── .env.example             # 環境変数テンプレート
│   ├── alembic.ini
│   ├── alembic/                 # DBマイグレーション
│   └── app/
│       ├── main.py
│       ├── core/                # 設定・DB
│       ├── api/                 # エンドポイント・依存関係
│       ├── models/              # Pydantic + SQLAlchemy
│       └── services/            # ビジネスロジック・AI
├── frontend/                    # Next.js
│   ├── package.json
│   ├── .env.local.example       # 環境変数テンプレート
│   └── src/
│       ├── app/                 # App Router
│       ├── components/          # UIコンポーネント
│       ├── lib/                 # API・utils・store
│       └── types/               # TypeScript型定義
├── e2e/                         # Playwright E2E
└── gas/                         # Fly.ioスリープ防止スクリプト
```

