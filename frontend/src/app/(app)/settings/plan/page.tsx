import { AppNav } from "@/components/layout/AppNav"
import { DashSidebar } from "@/components/layout/DashSidebar"
import { Card, CardBody, Button } from "@/components/ui"
import Link from "next/link"

export default function PlanPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <AppNav />
      <div className="flex flex-1">
        <DashSidebar />
        <main className="flex-1 p-9 bg-[var(--cream)]">
          <h1 className="text-[22px] font-bold mb-6">プラン管理</h1>
          <div className="max-w-[560px]">
            <Card>
              <CardBody>
                <div className="font-mono text-[10px] text-[var(--muted)] mb-1">現在のプラン</div>
                <div className="text-[20px] font-bold text-[var(--teal)] mb-1">✦ Proプラン</div>
                <div className="text-[13px] text-[var(--muted)] mb-5">次回更新日: 2026年4月28日</div>

                <div className="bg-[var(--cream)] rounded-xl p-4 mb-5">
                  <div className="flex justify-between text-[13px] mb-2">
                    <span className="text-[var(--muted)]">今月の使用状況</span>
                    <span className="font-mono font-medium">8 / 30 回</span>
                  </div>
                  <div className="h-1.5 bg-[var(--border)] rounded-full overflow-hidden">
                    <div className="h-full bg-[var(--teal)] rounded-full" style={{ width: "27%" }} />
                  </div>
                </div>

                <div className="flex gap-3">
                  <Button variant="outline" className="text-[var(--red)] border-[var(--red)] hover:bg-[var(--red-bg)]">
                    プランをキャンセル
                  </Button>
                  <Link href="/pricing">
                    <Button variant="ghost">プラン詳細を見る</Button>
                  </Link>
                </div>
              </CardBody>
            </Card>
          </div>
        </main>
      </div>
    </div>
  )
}
