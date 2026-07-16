# EstiMate — Cloudflare デプロイ手順書

デプロイ対象は以下の 3 つです（すべて Cloudflare 無料枠で動作）。

| サービス | Cloudflare 製品 | ディレクトリ |
|---|---|---|
| estimate-cf (D1 + AI Worker) | Workers + D1 | `../estimate-cf/worker/` |
| バックエンド (FastAPI) | Python Workers + D1 | `worker/` |
| フロントエンド (Next.js) | Workers (OpenNext) | `frontend/` |

---

## 前提条件

### 必要なツール

wrangler は各 Worker ディレクトリにローカルインストール済みのため、グローバルインストール不要です。

```bash
# Cloudflare にログイン（estimate-app/worker から実行）
cd estimate-app/worker
pnpm exec wrangler login
```

### 外部サービス

| サービス | 用途 | 取得先 |
|---|---|---|
| Clerk | 認証 | [dashboard.clerk.com](https://dashboard.clerk.com) |
| Gemini API | AI（無料ユーザー） | [aistudio.google.com](https://aistudio.google.com) |
| Anthropic API | AI（Pro ユーザー） | [console.anthropic.com](https://console.anthropic.com) |

---

## STEP 1｜初回のみ：バックエンド シークレット設定

バックエンド Python Worker に機密の環境変数を登録します。**初回デプロイ前に必ず実施してください。**

```bash
cd estimate-app/worker
bash scripts/set-secrets.sh
```

以下の順番で値の入力を求められます。

| シークレット名 | 取得場所 | 例 |
|---|---|---|
| `CLERK_SECRET_KEY` | Clerk Dashboard → API Keys | `sk_live_xxx` |
| `CLERK_JWT_PUBLIC_KEY` | Clerk Dashboard → API Keys → JWT Public Key | `-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----` |
| `GEMINI_API_KEY` | Google AI Studio → Get API key | `AIza...` |
| `ANTHROPIC_API_KEY` | Anthropic Console → API Keys | `sk-ant-...` |
| `FRONTEND_URL` | フロントエンドのデプロイ後 URL | `https://estimate-frontend.<account>.workers.dev` |

> **TIPS**: `FRONTEND_URL` はデプロイ後に判明するため、最初は仮の値を入れて先にデプロイし、
> URL 確定後に再設定でも構いません。  
> 再設定は `pnpm exec wrangler secret put FRONTEND_URL --name estimate-app-backend` で可能です。

---

## STEP 2｜初回のみ：フロントエンド 環境変数設定

`NEXT_PUBLIC_*` 変数はビルド時に JS に埋め込まれるため、**Cloudflare Workers のシークレットではなくビルド環境に設定します。**

```bash
cp estimate-app/frontend/.env.local.example estimate-app/frontend/.env.production
vi estimate-app/frontend/.env.production
```

`.env.production` の内容：

```env
# Clerk 本番キー（Clerk Dashboard → API Keys）
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_live_xxx
CLERK_SECRET_KEY=sk_live_xxx

# Clerk リダイレクト
NEXT_PUBLIC_CLERK_SIGN_IN_URL=/auth
NEXT_PUBLIC_CLERK_SIGN_UP_URL=/auth/sign-up
NEXT_PUBLIC_CLERK_SIGN_IN_FALLBACK_REDIRECT_URL=/dashboard
NEXT_PUBLIC_CLERK_SIGN_UP_FALLBACK_REDIRECT_URL=/dashboard

# バックエンド API URL（STEP 3-2 のデプロイ後に判明）
NEXT_PUBLIC_API_URL=https://estimate-app-backend.<account>.workers.dev

# アプリ URL（フロントエンドのデプロイ後に判明）
NEXT_PUBLIC_APP_URL=https://estimate-frontend.<account>.workers.dev
```

---

## STEP 3｜デプロイ実行

すべての初回設定が終わったら、以下のコマンドを順番に実行します。

```bash
cd estimate-app
```

### 3-1. estimate-cf（D1 + AI Worker）

```bash
mise run deploy:cf
```

内部で実行されること：
1. `pnpm d1:migrate:remote` — D1 の本番 migration（schema 適用）
2. `pnpm exec wrangler deploy` — Worker のデプロイ

完了後、ターミナルに表示される URL をメモしてください。

### 3-2. バックエンド（FastAPI on Python Workers）

```bash
mise run deploy:backend
```

内部で実行されること：
1. `pnpm install` — 依存関係インストール
2. `pnpm exec wrangler deploy` — Python Worker のデプロイ

完了後、表示される URL（`https://estimate-app-backend.xxx.workers.dev`）をメモしてください。  
→ フロントエンドの `NEXT_PUBLIC_API_URL` に設定します。

### 3-3. フロントエンド（Next.js on Workers）

```bash
mise run deploy:frontend
```

内部で実行されること：
1. `opennextjs-cloudflare build` — Cloudflare 向けビルド（`.open-next/` 生成）
2. `pnpm exec wrangler deploy` — Workers へのデプロイ

完了後、表示される URL（`https://estimate-frontend.xxx.workers.dev`）が本番 URL です。

---

## まとめて実行

上記 3-1〜3-3 を一括実行することもできます。

```bash
cd estimate-app
mise run deploy
```

---

## デプロイ後：URL を確定してシークレット更新

各 URL が確定したら、以下のシークレットを更新してください。

```bash
# フロントエンド URL をバックエンドに設定（CORS 許可のため）
echo "https://estimate-frontend.<account>.workers.dev" | \
  pnpm exec wrangler secret put FRONTEND_URL --name estimate-app-backend

# NEXT_PUBLIC_API_URL を .env.production に書き直して再デプロイ
vi estimate-app/frontend/.env.production
cd estimate-app && mise run deploy:frontend
```

---

## 2 回目以降のデプロイ

コードを変更したら、該当するサービスだけ再デプロイします。

```bash
cd estimate-app

mise run deploy:cf        # estimate-cf のみ
mise run deploy:backend   # バックエンドのみ
mise run deploy:frontend  # フロントエンドのみ
mise run deploy           # 全部
```

> フロントエンドはビルド時に環境変数が埋め込まれるため、  
> バックエンド URL が変わった場合は `.env.production` を更新してから再デプロイしてください。

---

## シークレットの確認・追加設定

```bash
# 登録済みシークレット一覧
pnpm exec wrangler secret list --name estimate-app-backend

# 個別シークレット更新
pnpm exec wrangler secret put <KEY_NAME> --name estimate-app-backend

# Stripe 決済を有効にする場合（任意）
pnpm exec wrangler secret put STRIPE_SECRET_KEY --name estimate-app-backend
pnpm exec wrangler secret put STRIPE_WEBHOOK_SECRET --name estimate-app-backend
pnpm exec wrangler secret put STRIPE_PRICE_ID --name estimate-app-backend
```

---

## トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| バックエンドが 500 を返す | D1 migration 未実施 | `mise run deploy:cf` で migration を再実行 |
| バックエンドが 503 を返す（DB無効） | D1 バインディング設定ミス | `worker/wrangler.jsonc` の `database_id` を確認 |
| フロントエンドで Clerk エラー | `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` が test キー | `.env.production` を本番キーに変更して再デプロイ |
| estimate-cf が 500 を返す | D1 migration 未実施 | `cd estimate-cf/worker && pnpm d1:migrate:remote` |
| CORS エラー | `FRONTEND_URL` 未設定 | バックエンドシークレット `FRONTEND_URL` を更新 |
| 見積もり一覧が空 | D1 schema の `estimates` テーブル未作成 | `mise run deploy:cf`（migration 再実行） |
