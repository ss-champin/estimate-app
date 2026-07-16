"use client"
import { useState, useEffect } from "react"
import { useAuth } from "@clerk/nextjs"
import { useAuthMode } from "@/components/providers/AppProviders"
import { LOCAL_DEV_BEARER } from "@/lib/clerk-config"
import { Card } from "@/components/ui"
import { formatCurrency } from "@/lib/utils"
import { getEstimateHistory, getUsageStatus } from "@/lib/api"
import type { EstimateHistory, UsageStatus } from "@/types/estimate"

type GetToken = () => Promise<string | null>

function DashboardContent({ getToken }: { getToken: GetToken }) {
  const [history, setHistory] = useState<EstimateHistory[]>([])
  const [usage, setUsage] = useState<UsageStatus | undefined>(undefined)

  useEffect(() => {
    getToken().then((token) => {
      if (!token) return
      getEstimateHistory(token).then(setHistory).catch(() => {})
      getUsageStatus(token).then(setUsage).catch(() => {})
    })
  }, [getToken])

  const totalCount = history.length
  const avgAmount =
    totalCount > 0
      ? Math.round(history.reduce((s, h) => s + (h.amount_min + h.amount_max) / 2, 0) / totalCount)
      : 0

  const now = new Date()
  const thisMonthStr = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`
  const thisMonthCount = history.filter((h) => h.created_at.startsWith(thisMonthStr)).length

  return (
    <main className="flex-1 p-9 bg-[var(--cream)]">
      <div className="flex items-start justify-between mb-7">
        <div>
          <h1 className="text-[22px] font-bold tracking-[-0.3px]">見積もり履歴</h1>
          <p className="text-[13px] text-[var(--muted)] mt-1">
            {totalCount}件 · 今月{thisMonthCount}件作成
            {avgAmount > 0 && <> · 平均 {formatCurrency(avgAmount)}</>}
          </p>
        </div>
        <a href="/estimate/new" className="inline-flex items-center gap-1.5 bg-[var(--teal)] text-white px-4 py-2 rounded-lg text-[13px] font-medium hover:bg-[var(--teal-m)] transition-colors">
          + 新規作成
        </a>
      </div>

      <div className="grid grid-cols-3 gap-3 mb-5">
        {[
          { label: "// TOTAL", val: `${totalCount}件`, sub: "累計作成数" },
          { label: "// AVG AMOUNT", val: avgAmount > 0 ? formatCurrency(avgAmount) : "—", sub: "平均見積もり金額" },
          { label: "// THIS MONTH", val: `${thisMonthCount}件`, sub: "今月の作成数" },
        ].map((s) => (
          <div key={s.label} className="bg-white border border-[var(--border)] rounded-xl px-5 py-4">
            <div className="font-mono text-[10px] text-[var(--muted)] mb-1.5">{s.label}</div>
            <div className="text-[24px] font-bold tracking-[-0.5px]">{s.val}</div>
            <div className="text-[11px] text-[var(--muted)] mt-0.5">{s.sub}</div>
          </div>
        ))}
      </div>

      <Card>
        <div className="px-5 py-4 border-b border-[var(--border)] flex items-center justify-between">
          <h2 className="text-[15px] font-semibold">最近の見積もり</h2>
          <input type="text" placeholder="案件名で検索..." className="px-3 py-1.5 border-[1.5px] border-[var(--border)] rounded-lg text-[13px] outline-none w-[200px] focus:border-[var(--teal)]" />
        </div>
        <div className="overflow-auto">
          {history.length === 0 ? (
            <div className="px-5 py-10 text-center text-[13px] text-[var(--muted)]">
              まだ見積もりがありません。新規作成から始めましょう。
            </div>
          ) : (
            <table className="w-full border-collapse text-[13px]">
              <thead>
                <tr>
                  {["案件名", "見積もり金額", "工数", "作成日", ""].map((h) => (
                    <th key={h} className="text-left font-mono text-[10px] text-[var(--muted)] px-5 py-2.5 border-b border-[var(--border)] bg-[var(--cream)] font-medium">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.id} className="hover:bg-[var(--cream)] transition-colors border-b border-[var(--cream2)] last:border-0">
                    <td className="px-5 py-3.5 font-medium">{item.title}</td>
                    <td className="px-5 py-3.5 font-semibold font-mono text-[var(--ink)]">
                      {formatCurrency(item.amount_min)}〜
                    </td>
                    <td className="px-5 py-3.5 font-mono text-[12px] text-[var(--muted)]">
                      {item.hours_min}〜{item.hours_max}h
                    </td>
                    <td className="px-5 py-3.5 font-mono text-[12px] text-[var(--muted2)]">{item.created_at}</td>
                    <td className="px-5 py-3.5">
                      <a href={`/estimate/${item.id}`} className="inline-flex items-center px-3 py-1 text-[12px] border-[1.5px] border-[var(--border2)] rounded-md hover:border-[var(--ink)] hover:bg-white transition-all">
                        開く
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </Card>
    </main>
  )
}

function DashboardWithClerk() {
  const { getToken } = useAuth()
  return <DashboardContent getToken={getToken} />
}

export default function DashboardPage() {
  const mode = useAuthMode()
  if (mode === "dev") {
    return <DashboardContent getToken={async () => LOCAL_DEV_BEARER} />
  }
  return <DashboardWithClerk />
}
