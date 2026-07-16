#!/usr/bin/env bash
# estimate-app/worker/scripts/set-secrets.sh
# Cloudflare Workers のシークレットを設定するスクリプト
# 実行前に backend/.env.production の値を確認してください
set -e

WORKER_NAME="estimate-app-backend"

echo "=== $WORKER_NAME シークレット設定 ==="

secrets=(
  CLERK_SECRET_KEY
  CLERK_JWT_PUBLIC_KEY
  GEMINI_API_KEY
  ANTHROPIC_API_KEY
  FRONTEND_URL
)

for key in "${secrets[@]}"; do
  echo ""
  echo "→ $key を入力してください（Enter で確定）:"
  pnpm exec wrangler secret put "$key" --name "$WORKER_NAME"
done

echo ""
echo "✅ シークレット設定完了"
