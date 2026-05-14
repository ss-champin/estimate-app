# Stripe 連携手順書（サンドボックス → 本番）

このドキュメントは、Stripe の **テスト環境（サンドボックス／テストモード）**で安全に検証し、その後 **本番（実決済）**へ移行するまでの流れをまとめたものです。  
**実際の資金移動はテストモードでは発生しません。**

---

## Stripe が案内する流れとの対応

| Stripe 上の段階 | 概要 |
|-----------------|------|
| **1. 設定する** | テストモードで API・商品・Webhook などを設定する（本書「フェーズ A」） |
| **2. 本番環境に切り替える** | 事業者確認（**KYB**／本人・法人確認）を完了し、本番利用を有効にする（本書「フェーズ B」） |
| **3. 決済を受け付ける** | 本番用のキー・料金 ID・Webhook を設定し、実決済を受ける（本書「フェーズ C」） |

---

## 前提（このリポジトリ）

- バックエンドは FastAPI。**Webhook エンドポイント**: `{APIのベースURL}/api/stripe/webhook`
- 環境変数（`backend/.env.local` など）は `backend/.env.example` を参照
- **課金開始**: アプリは `POST /api/stripe/checkout-session` で Stripe Checkout に誘導します（`STRIPE_PRICE_ID` が Pro 用の **定期課金 Price** であること）。
- **プラン管理**: `POST /api/stripe/portal-session` で Stripe Customer Portal を開きます。Dashboard の **Settings → Billing → Customer portal** で機能を有効化してください。
- Webhook では次のイベントを処理します。ダッシュボードの購読に含めてください  
  - `checkout.session.completed`（Checkout 完了時に DB へ反映）  
  - `customer.subscription.created`  
  - `customer.subscription.updated`  
  - `customer.subscription.deleted`

---

## フェーズ A — サンドボックス（テストモード）で始める

### A-1. アカウントとテストモード

1. [Stripe に登録](https://dashboard.stripe.com/register)し、ダッシュボードにログインする  
2. 右上の **「テストモード」** が **オン** になっていることを確認する（オフの場合はオンにする）

### A-2. API キーを取得する

1. **Developers → API keys** を開く  
2. **Secret key**（`sk_test_...`）をコピーする  
3. `backend/.env.local` に設定する:

   ```env
   STRIPE_SECRET_KEY=sk_test_...
   ```

> **注意:** テストモードのキーは `sk_test_`、本番は `sk_live_` です。混在させないでください。

### A-3. 商品と料金（Price）を作成する

1. **Product catalog → Products → Add product**  
2. 名前（例: `EstiMate Pro`）を入力  
3. **Pricing** で **Recurring（継続課金）**、請求サイクル（例: 月額）と金額を設定  
4. 保存後、**Price ID**（`price_...`）をコピーする  
5. `backend/.env.local` に設定する:

   ```env
   STRIPE_PRICE_ID=price_...
   ```

### A-4. Webhook（テスト）の設定

**必要か？** **ローカル（A-4）… 必須ではありません。** `STRIPE_WEBHOOK_SECRET` を空のままにすると、このリポジトリでは Webhook 処理をスキップします（決済画面の試行以前の開発や、Checkout 未接続段階では省略可）。  
ただし **サブスク状態を DB の `subscriptions` と同期する動き**は Webhook 前提の実装なので、**課金〜解約まで End-to-End で試すなら CLI か ngrok のどちらかを用意する**のがよいです。

**本番では必須？** **Webhook のエンドポイント登録と `STRIPE_WEBHOOK_SECRET` の設定は、実運用では事実上必須**としてください。Stripe がカード決済そのものを「Webhook なしで禁止」するわけではありませんが、**更新・解約・支払い失敗**などはイベントで届くのが普通で、このアプリもそれで DB を更新します。本番で secret を空にすると処理がスキップされ、**契約状態と DB がずれたまま**になりやすいです。

---

Stripe からローカル PC へ直接届かないため、次のいずれかで行います。

**方法①: Stripe CLI（ローカル開発向け）**

1. [Stripe CLI](https://docs.stripe.com/stripe-cli) をインストール  
2. `stripe login` でダッシュボードと連携  
3. バックエンドを起動したうえで、例:

   ```bash
   stripe listen --forward-to localhost:8000/api/stripe/webhook
   ```

4. 表示される **Webhook signing secret**（`whsec_...`）を `backend/.env.local` の `STRIPE_WEBHOOK_SECRET` に貼る（CLI が出す **一時的な** secret です）

**方法②: テスト用に公開 URL（ngrok 等）を当てる**

1. 一時的な `https://....` を API の `8000` などに転送  
2. **Developers → Webhooks → Add endpoint**  
3. URL: `https://<公開URL>/api/stripe/webhook`  
4. イベント: **`checkout.session.completed`** と **`customer.subscription.*`**（created / updated / deleted）  
5. **Signing secret** を `STRIPE_WEBHOOK_SECRET` に設定

> 本リポジトリでは **`STRIPE_WEBHOOK_SECRET` が空**のとき、開発用に Webhook 検証をスキップする動作になります。**本番では必ず設定**してください。

### A-5. サブスクリプション連携（アプリ側）の確認

- 決済セッションや Checkout の作成 API を実装・接続している場合、**テストカード**で E2E を確認します  
- 代表例（テストモード）: 番号 `4242 4242 4242 4242`、有効期限は未来日、CVC 任意の3桁など（[テストカード一覧](https://docs.stripe.com/testing)）

### A-6. データベース

- サブスク状態を永続化する場合は **PostgreSQL を起動**し、`mise run migrate` などでスキーマを揃えてから Webhook で `subscriptions` テーブルが更新される流れを確認します

---

## フェーズ B — 本番環境に切り替える（KYB）

1. Stripe ダッシュボードで **本番利用**のための案内に従い、**事業情報・本人確認（KYB／KYC）** を完了する  
2. 国・業種・口座などの提出内容は、実態と一致させる  
3. Stripe から **承認・有効化**の通知が来るまで、本番の実決済は行わない  
4. ダッシュボードで **「テストモード」をオフ**にすると **本番モード**の各種設定画面になる（**ライブのキー・商品はテストと別**です）

---

## フェーズ C — 本番で決済を受け付ける

テストで動いた内容を **本番用にコピー**します（自動ではマージされないため、**本番で再取得・再作成**が必要です）。

### C-1. 本番の API キー

1. **テストモードをオフ**にする  
2. **Developers → API keys** で **Secret key**（`sk_live_...`）を取得  
3. デプロイ先の環境変数（例: Fly.io の secrets）に `STRIPE_SECRET_KEY` として設定  
4. **`APP_ENV=production`** など、本番用の `.env` ルールに合わせる（このリポジトリの運用に従う）

### C-2. 本番の Price ID

1. **本番モード**で **Product / Price を再作成**するか、テストと同じ構成で本番用の Price を用意  
2. 本番の **`price_...`** を `STRIPE_PRICE_ID` に設定（テストの ID は本番では使えません）

### C-3. 本番 Webhook

1. **Developers → Webhooks** で **本番モード**の Endpoint を追加  
2. URL: `https://<本番APIホスト>/api/stripe/webhook`  
3. 購読イベント: **`checkout.session.completed`** および `customer.subscription.created` / `updated` / `deleted`  
4. **Signing secret**（`whsec_...`）を本番の `STRIPE_WEBHOOK_SECRET` に設定

### C-4. フロントエンド・その他

- Checkout / Elements を使う場合は、**本番の Publishable key**（`pk_live_...`）をフロントの環境変数に設定  
- `FRONTEND_URL`・`ALLOWED_ORIGINS` を本番ドメインに合わせる（`backend/.env.example` 参照）

### C-5. 本番前チェックリスト

- [ ] `sk_live_` / `pk_live_` / 本番 `price_` / 本番 `whsec_` がデプロイ環境に入っている  
- [ ] 本番 Webhook の **Recent deliveries** で 2xx を確認  
- [ ] 少額の実決済でキャンセル・返金フローまで運用イメージを固める  

---

## トラブル時の確認ポイント

| 症状 | 確認すること |
|------|----------------|
| Webhook が 400（Invalid signature） | `STRIPE_WEBHOOK_SECRET` が **その Endpoint のものと一致しているか**（テスト用 CLI secret とダッシュボード secret を混同していないか） |
| DB が更新されない | PostgreSQL が有効か、`DATABASE_URL` とマイグレーション、`subscriptions` に `stripe_subscription_id` が入っているか |
| テストと本番で挙動が違う | キー・Price ID・Webhook が **モードごとに別**であることを再確認 |

---

## 参考リンク

- [Stripe テストモード](https://docs.stripe.com/test-mode)  
- [テストカード](https://docs.stripe.com/testing)  
- [Stripe CLI](https://docs.stripe.com/stripe-cli)  
- [Webhooks](https://docs.stripe.com/webhooks)
