/**
 * Clerk の Publishable Key が実際に設定されているか。
 * プレースホルダー（pk_test_ のみ等）は未設定とみなす。
 */
export function isClerkConfigured(): boolean {
  const key = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.trim() ?? ""
  return (key.startsWith("pk_test_") || key.startsWith("pk_live_")) && key.length >= 20
}

/** バックエンドのローカル開発用 Bearer（Clerk 未設定時と揃える） */
export const LOCAL_DEV_BEARER = "local-dev"
