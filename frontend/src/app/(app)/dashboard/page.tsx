import { AppNav } from "@/components/layout/AppNav"
import { DashSidebar } from "@/components/layout/DashSidebar"
import { Card } from "@/components/ui"
import { formatCurrency } from "@/lib/utils"

const MOCK_HISTORY = [
  { id: "1", title: "ReactでのECサイトフロントエンド開発", amount_min: 148000, amount_max: 185000, hours_min: 40, hours_max: 50, ai_provider: "claude-haiku-4-5", created_at: "2026-03-28" },
  { id: "2", title: "Next.js管理画面の設計・開発", amount_min: 220000, amount_max: 280000, hours_min: 55, hours_max: 70, ai_provider: "claude-haiku-4-5", created_at: "2026-03-24" },
  { id: "3", title: "APIサーバー（FastAPI）の構築", amount_min: 95000, amount_max: 120000, hours_min: 25, hours_max: 35, ai_provider: "gemini-2.5-flash-lite", created_at: "2026-03-20" },
  { id: "4", title: "Shopifyカスタムテーマ開発", amount_min: 78000, amount_max: 95000, hours_min: 20, hours_max: 28, ai_provider: "claude-haiku-4-5", created_at: "2026-03-15" },
]

const MOCK_USAGE = { plan: "paid" as const, daily_used: 2, daily_limit: 10, monthly_used: 8, monthly_limit: 30, daily_remaining: 8, monthly_remaining: 22 }

export default async function DashboardPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <AppNav />
      <div className="flex flex-1">
        <DashSidebar usage={MOCK_USAGE} />
        <main className="flex-1 p-9 bg-[var(--cream)]">
          {/* Header */}
          <div className="flex items-start justify-between mb-7">
            <div>
              <h1 className="text-[22px] font-bold tracking-[-0.3px]">見積もり履歴</h1>
              <p className="text-[13px] text-[var(--muted)] mt-1">
                {MOCK_HISTORY.length}件 · 今月4件作成 · 平均{" "}
                {formatCurrency(Math.round(MOCK_HISTORY.reduce((s, h) => s + (h.amount_min + h.amount_max) / 2, 0) / MOCK_HISTORY.length))}
              </p>
            </div>
            <a href="/estimate/new" className="inline-flex items-center gap-1.5 bg-[var(--teal)] text-white px-4 py-2 rounded-lg text-[13px] font-medium hover:bg-[var(--teal-m)] transition-colors">
              + 新規作成
            </a>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-3 gap-3 mb-5">
            {[
              { label: "// TOTAL", val: `${MOCK_HISTORY.length}件`, sub: "累計作成数" },
              { label: "// AVG AMOUNT", val: formatCurrency(162000), sub: "平均見積もり金額" },
              { label: "// THIS MONTH", val: "4件", sub: "今月の作成数" },
            ].map((s) => (
              <div key={s.label} className="bg-white border border-[var(--border)] rounded-xl px-5 py-4">
                <div className="font-mono text-[10px] text-[var(--muted)] mb-1.5">{s.label}</div>
                <div className="text-[24px] font-bold tracking-[-0.5px]">{s.val}</div>
                <div className="text-[11px] text-[var(--muted)] mt-0.5">{s.sub}</div>
              </div>
            ))}
          </div>

          {/* History Table */}
          <Card>
            <div className="px-5 py-4 border-b border-[var(--border)] flex items-center justify-between">
              <h2 className="text-[15px] font-semibold">最近の見積もり</h2>
              <input type="text" placeholder="案件名で検索..." className="px-3 py-1.5 border-[1.5px] border-[var(--border)] rounded-lg text-[13px] outline-none w-[200px] focus:border-[var(--teal)]" />
            </div>
            <div className="overflow-auto">
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
                  {MOCK_HISTORY.map((item) => (
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
            </div>
          </Card>
        </main>
      </div>
    </div>
  )
}
