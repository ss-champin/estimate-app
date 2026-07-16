"use client"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui"
import { useEstimateStore } from "@/lib/store"
import { EstimateResultContent } from "./EstimateResultContent"

export function EstimateResult() {
  const router = useRouter()
  const { result, aiProvider, generatedAt, clearResult } = useEstimateStore()

  if (!result) {
    return (
      <div className="max-w-lg mx-auto px-6 py-20 text-center">
        <p className="text-[var(--muted)] mb-6 text-[15px] leading-relaxed">まだ見積もり結果がありません。フォームから作成してください。</p>
        <Button variant="teal" onClick={() => router.push("/estimate/new")}>見積もりを作る</Button>
      </div>
    )
  }

  return (
    <EstimateResultContent
      result={result}
      aiProvider={aiProvider}
      generatedAt={generatedAt}
      actions={
        <>
          <Button
            variant="outline"
            className="rounded-xl py-3.5 border-[var(--border2)]"
            onClick={() => {
              clearResult()
              router.push("/estimate/new")
            }}
          >
            別の案件を見積もる
          </Button>
          <Button variant="ghost" className="rounded-xl py-3.5" onClick={() => router.push("/dashboard")}>
            ダッシュボードへ
          </Button>
        </>
      }
    />
  )
}
