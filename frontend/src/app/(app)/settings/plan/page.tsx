"use client"
import { useState, useEffect } from "react"
import { useAuth } from "@clerk/nextjs"
import { useAuthMode } from "@/components/providers/AppProviders"
import { LOCAL_DEV_BEARER } from "@/lib/clerk-config"
import { Card, CardBody, Button } from "@/components/ui"
import Link from "next/link"
import { getUsageStatus } from "@/lib/api"
import type { UsageStatus } from "@/types/estimate"

const PLAN_LABELS = { free: "無料プラン", paid: "✦ Proプラン" } as const

type GetToken = () => Promise<string | null>

function PlanContent({ getToken }: { getToken: GetToken }) {
  const [usage, setUsage] = useState<UsageStatus | undefined>(undefined)

  useEffect(() => {
    getToken().then((token) => {
      if (!token) return
      getUsageStatus(token).then(setUsage).catch(() => {})
    })
  }, [getToken])

  const monthlyPct = usage
    ? Math.round((usage.monthly_used / usage.monthly_limit) * 100)
    : 0

  return (
    <main className="flex-1 p-9 bg-[var(--cream)]">
      <h1 className="text-[22px] font-bold mb-6">プラン管理</h1>
      <div className="max-w-[560px]">
        <Card>
          <CardBody>
            <div className="font-mono text-[10px] text-[var(--muted)] mb-1">現在のプラン</div>
            <div className="text-[20px] font-bold text-[var(--teal)] mb-5">
              {PLAN_LABELS[usage?.plan ?? "free"]}
            </div>

            <div className="bg-[var(--cream)] rounded-xl p-4 mb-5">
              <div className="flex justify-between text-[13px] mb-2">
                <span className="text-[var(--muted)]">今月の使用状況</span>
                <span className="font-mono font-medium">
                  {usage?.monthly_used ?? 0} / {usage?.monthly_limit ?? 3} 回
                </span>
              </div>
              <div className="h-1.5 bg-[var(--border)] rounded-full overflow-hidden">
                <div className="h-full bg-[var(--teal)] rounded-full transition-all" style={{ width: `${monthlyPct}%` }} />
              </div>
              {usage?.daily_limit && (
                <div className="mt-3">
                  <div className="flex justify-between text-[13px] mb-2">
                    <span className="text-[var(--muted)]">本日の使用状況</span>
                    <span className="font-mono font-medium">
                      {usage.daily_used} / {usage.daily_limit} 回
                    </span>
                  </div>
                  <div className="h-1.5 bg-[var(--border)] rounded-full overflow-hidden">
                    <div className="h-full bg-[var(--teal)] rounded-full transition-all"
                      style={{ width: `${Math.round((usage.daily_used / usage.daily_limit) * 100)}%` }} />
                  </div>
                </div>
              )}
            </div>

            <div className="flex gap-3">
              {usage?.plan === "paid" && (
                <Button variant="outline" className="text-[var(--red)] border-[var(--red)] hover:bg-[var(--red-bg)]">
                  プランをキャンセル
                </Button>
              )}
              <Link href="/pricing">
                <Button variant="ghost">プラン詳細を見る</Button>
              </Link>
            </div>
          </CardBody>
        </Card>
      </div>
    </main>
  )
}

function PlanWithClerk() {
  const { getToken } = useAuth()
  return <PlanContent getToken={getToken} />
}

export default function PlanPage() {
  const mode = useAuthMode()
  if (mode === "dev") {
    return <PlanContent getToken={async () => LOCAL_DEV_BEARER} />
  }
  return <PlanWithClerk />
}
