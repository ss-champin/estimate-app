"use client"
import { useState, useEffect, use } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@clerk/nextjs"
import { useAuthMode } from "@/components/providers/AppProviders"
import { LOCAL_DEV_BEARER } from "@/lib/clerk-config"
import { Button } from "@/components/ui"
import { EstimateResultContent } from "@/components/estimate/EstimateResultContent"
import { getEstimateById } from "@/lib/api"
import type { EstimateDetail } from "@/types/estimate"

type GetToken = () => Promise<string | null>

function EstimateDetailContent({ getToken, id }: { getToken: GetToken; id: string }) {
  const router = useRouter()
  const [detail, setDetail] = useState<EstimateDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    getToken().then((token) => {
      if (!token) return
      getEstimateById(id, token)
        .then(setDetail)
        .catch((e) => {
          setError(e?.status === 404 ? "見積もりが見つかりません" : "データの取得に失敗しました")
        })
    })
  }, [getToken, id])

  if (error) {
    return (
      <div className="max-w-[640px] mx-auto px-6 py-20 text-center">
        <p className="text-[var(--muted)] mb-6 text-[15px]">{error}</p>
        <Button variant="outline" onClick={() => router.push("/dashboard")}>← 履歴に戻る</Button>
      </div>
    )
  }

  if (!detail) {
    return (
      <div className="max-w-[640px] mx-auto px-6 py-20 text-center">
        <p className="text-[13px] text-[var(--muted2)]">読み込み中...</p>
      </div>
    )
  }

  return (
    <EstimateResultContent
      result={detail.result}
      aiProvider={detail.ai_provider}
      generatedAt={detail.created_at}
      actions={
        <>
          <Button
            variant="outline"
            className="rounded-xl py-3.5 border-[var(--border2)]"
            onClick={() => router.push("/dashboard")}
          >
            ← 履歴に戻る
          </Button>
          <Button
            variant="ghost"
            className="rounded-xl py-3.5"
            onClick={() => router.push("/estimate/new")}
          >
            + 新規作成
          </Button>
        </>
      }
    />
  )
}

function EstimateDetailWithClerk({ id }: { id: string }) {
  const { getToken } = useAuth()
  return <EstimateDetailContent getToken={getToken} id={id} />
}

export default function EstimateViewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const mode = useAuthMode()
  if (mode === "dev") {
    return <EstimateDetailContent getToken={async () => LOCAL_DEV_BEARER} id={id} />
  }
  return <EstimateDetailWithClerk id={id} />
}
