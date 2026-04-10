"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import type { UsageStatus } from "@/types/estimate"

const PLAN_LABELS = { free: "無料プラン", paid: "✦ Pro プラン" } as const

function SideItem({ href, icon, label, count, active }: { href: string; icon: string; label: string; count?: number; active?: boolean }) {
  return (
    <Link href={href} className={cn("flex items-center gap-2.5 px-2.5 py-2 rounded-md text-[13px] transition-all", active ? "bg-[rgba(29,197,176,0.12)] text-[var(--teal-l)] font-medium" : "text-white/40 hover:bg-white/5 hover:text-white/75")}>
      <span className="w-4 text-center text-base">{icon}</span>
      <span className="flex-1">{label}</span>
      {count !== undefined && <span className="font-mono text-[11px] bg-white/8 text-white/35 px-2 py-0.5 rounded-full">{count}</span>}
    </Link>
  )
}

export function DashSidebar({ usage }: { usage?: UsageStatus }) {
  const path = usePathname()
  const dailyPct  = usage?.daily_limit  ? (usage.daily_used  / usage.daily_limit)  * 100 : 0
  const monthlyPct= (usage?.monthly_used ?? 0) / (usage?.monthly_limit ?? 30) * 100

  return (
    <aside className="w-[220px] bg-[var(--ink2)] flex flex-col gap-0.5 px-3 py-6 min-h-full border-r border-white/5">
      <SideItem href="/dashboard"    icon="📄" label="見積もり履歴" count={12} active={path === "/dashboard"} />
      <SideItem href="/estimate/new" icon="➕" label="新規作成" />
      <div className="font-mono text-[9px] text-white/20 px-2.5 py-2 mt-2 tracking-widest">// ACCOUNT</div>
      <SideItem href="/settings" icon="⚙️" label="設定" />
      <SideItem href="/settings/plan" icon="💳" label="プラン管理" />

      {/* Usage */}
      <div className="mt-auto pt-4 px-2.5 py-3.5 bg-white/4 rounded-xl border border-white/5">
        <div className="font-mono text-[9px] text-white/25 mb-1">現在のプラン</div>
        <div className="text-[13px] font-semibold text-[var(--teal-l)] mb-3">{PLAN_LABELS[usage?.plan ?? "free"]}</div>
        {usage?.daily_limit && (
          <>
            <div className="font-mono text-[9px] text-white/25 mb-1">今日: {usage.daily_used}/{usage.daily_limit} 回</div>
            <div className="h-[3px] bg-white/10 rounded-full mb-3 overflow-hidden">
              <div className="h-full bg-[var(--teal)] rounded-full transition-all" style={{ width: `${dailyPct}%` }} />
            </div>
          </>
        )}
        <div className="font-mono text-[9px] text-white/25 mb-1">今月: {usage?.monthly_used ?? 0}/{usage?.monthly_limit ?? 3} 回</div>
        <div className="h-[3px] bg-white/10 rounded-full overflow-hidden">
          <div className={cn("h-full rounded-full transition-all", monthlyPct > 80 ? "bg-[var(--amber)]" : "bg-[var(--teal)]")} style={{ width: `${monthlyPct}%` }} />
        </div>
      </div>
    </aside>
  )
}
