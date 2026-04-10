import { AppNav } from "@/components/layout/AppNav"
import Link from "next/link"
import { Button } from "@/components/ui"

export default async function EstimateViewPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  return (
    <div className="min-h-screen">
      <AppNav />
      <div className="max-w-[820px] mx-auto px-6 py-10">
        <div className="font-mono text-[11px] text-[var(--muted)] mb-2">// estimate/{id}</div>
        <h1 className="text-[22px] font-bold mb-6">保存済み見積もり</h1>
        <p className="text-[var(--muted)] text-[14px] mb-6">
          この画面は保存済み見積もりの詳細表示ページです。
          バックエンドとの連携後に実際の見積もりデータが表示されます。
        </p>
        <div className="flex gap-3">
          <Link href="/dashboard"><Button variant="outline">← 履歴に戻る</Button></Link>
          <Link href="/estimate/new"><Button variant="teal">+ 新規作成</Button></Link>
        </div>
      </div>
    </div>
  )
}
