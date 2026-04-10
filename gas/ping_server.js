/**
 * Fly.io スリープ防止スクリプト
 *
 * 設定手順:
 * 1. https://script.google.com にアクセス
 * 2. 新しいプロジェクトを作成してこのコードを貼り付け
 * 3. BACKEND_URL を実際のFly.io URLに変更
 * 4. 「トリガー」→「トリガーを追加」→ pingServer を10分ごとに実行
 */

const BACKEND_URL = "https://estimate-backend.fly.dev"

function pingServer() {
  try {
    const response = UrlFetchApp.fetch(`${BACKEND_URL}/health`, {
      method: "GET",
      muteHttpExceptions: true,
    })
    const code = response.getResponseCode()
    if (code === 200) {
      console.log(`✅ Ping成功: ${new Date().toLocaleString("ja-JP")}`)
    } else {
      console.warn(`⚠️ ステータスコード異常: ${code}`)
    }
  } catch (error) {
    console.error(`❌ Ping失敗: ${error}`)
  }
}
