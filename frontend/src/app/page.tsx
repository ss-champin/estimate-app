import Link from "next/link"
import { AppNav } from "@/components/layout/AppNav"
import { Button } from "@/components/ui"
import { cn } from "@/lib/utils"

const features = [
  { icon: "📝", title: "テキストをAI解析", desc: "案件タイトルと本文を貼るだけ。要件の粒度・難易度のたたきを読み取り、見積もりの土台を作ります。" },
  { icon: "💰", title: "相場ベース金額算出", desc: "エンジニア特化の相場データで、工程別に工数を分解して適正金額を提示。" },
  { icon: "⏱", title: "工数・納期の自動算出", desc: "何時間かかるか、何日で納品できるかを自動計算。無理な受注を防ぐ。" },
  { icon: "✉️", title: "返信メッセージ生成", desc: "クライアントへのDM返信文を自動生成。コピーしてそのまま送れる。" },
  { icon: "📋", title: "条件・注意事項", desc: "修正回数・著作権・追加料金の条件文をトラブル防止テンプレで自動挿入。" },
  { icon: "✨", title: "手元の情報だけでOK", desc: "依頼ページからコピーした文章をそのまま貼り付け。形式は問いません。" },
]

const steps = [
  { num: "01", title: "案件を入力", desc: "タイトル（任意）と本文を貼り付け。依頼内容をそのままコピペしてOK" },
  { num: "02", title: "技術を選ぶ", desc: "使用技術スタックと案件の複雑度を選択（AIが自動判定もしてくれる）" },
  { num: "03", title: "AIが生成", desc: "エンジニア相場データをもとに見積もり・工数・返信文・取引条件を自動生成" },
  { num: "04", title: "コピーして送信", desc: "生成された返信メッセージをそのままDMに貼り付けて送るだけ" },
]

export default function LandingPage() {
  return (
    <main>
      <AppNav />

      {/* ── Hero ── */}
      <section className="bg-[var(--ink)] relative overflow-hidden min-h-[580px] flex items-center">
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(ellipse 50% 70% at 82% 38%, rgba(18,160,144,0.14) 0%, transparent 55%), radial-gradient(ellipse 30% 50% at 12% 72%, rgba(18,160,144,0.05) 0%, transparent 48%)",
          }}
        />
        <div className="absolute inset-0 opacity-[0.022] hero-grid-bg" />

        <div className="relative max-w-[1100px] mx-auto px-10 py-20 grid grid-cols-1 lg:grid-cols-[1fr_400px] gap-14 lg:gap-16 items-center">
          <div className="afu">
            <div className="inline-block text-[12px] text-[var(--teal-l)]/90 mb-7 tracking-[0.12em] border-b border-[var(--teal-l)]/25 pb-1">
              フリーランスエンジニア向け
            </div>
            <h1 className="font-display text-[clamp(2rem,4.8vw,3.15rem)] font-medium text-white leading-[1.35] tracking-wide mb-6">
              タイトルと内容を
              <br />
              入れるだけ
              <br />
              <span className="text-[var(--teal-l)]">見積もり完成。</span>
            </h1>
            <p className="text-white/48 text-[16px] leading-[1.9] mb-10 font-light max-w-[28em]">
              依頼文をコピペするだけ。エンジニア相場を踏まえた
              <br className="hidden sm:block" />
              金額の目安と、送れる文面までまとめて用意します。
            </p>
            <div className="flex flex-wrap gap-4 items-center">
              <Link href="/estimate/new">
                <Button variant="teal" className="px-8 py-3.5 text-[15px] rounded-xl shadow-none">
                  無料で見積もりを作る
                </Button>
              </Link>
              <Link href="/pricing">
                <span className="text-white/38 text-sm hover:text-white/55 transition-colors border-b border-white/20 pb-0.5">
                  料金を見る
                </span>
              </Link>
            </div>
          </div>

          <div className="afu2 bg-white/[0.035] border border-white/[0.08] rounded-[1.35rem] overflow-hidden shadow-[0_24px_48px_rgba(0,0,0,0.25)]">
            <div className="bg-black/20 px-4 py-3 border-b border-white/[0.06] flex items-center gap-2">
              <div className="flex gap-[5px] opacity-90">
                <div className="w-[9px] h-[9px] rounded-full bg-[#FF5F57]/90" />
                <div className="w-[9px] h-[9px] rounded-full bg-[#FEBC2E]/90" />
                <div className="w-[9px] h-[9px] rounded-full bg-[#28C840]/90" />
              </div>
              <span className="text-[11px] text-white/28 ml-1 tracking-wide">下書き</span>
            </div>
            <div className="p-5 sm:p-6">
              <div className="mb-4">
                <div className="text-[11px] text-white/32 mb-2 tracking-wide">案件タイトル</div>
                <div className="bg-white/[0.05] border border-white/[0.07] rounded-lg px-3.5 py-2.5 text-[13px] text-white/60 leading-snug">
                  React での管理画面開発のご依頼
                </div>
              </div>
              <div className="mb-5">
                <div className="text-[11px] text-white/32 mb-2 tracking-wide">案件内容</div>
                <div className="bg-white/[0.05] border border-white/[0.07] rounded-lg px-3.5 py-3 min-h-[76px] text-[12px] text-white/38 leading-relaxed">
                  既存の仕様書に基づき、CRUD・権限・CSV出力までを想定しています。期日は◯月上旬…
                </div>
              </div>
              <div className="flex flex-col gap-2.5">
                {[
                  ["推奨見積もり", "¥148,000〜¥185,000", true],
                  ["作業工数", "約 40〜50h"],
                  ["推奨納期", "10〜14日"],
                  ["難易度", "標準〜やや複雑"],
                ].map(([k, v, accent]) => (
                  <div
                    key={String(k)}
                    className="flex items-center justify-between px-3.5 py-2.5 bg-white/[0.03] border border-white/[0.05] rounded-lg"
                  >
                    <span className="text-[12px] text-white/38">{k}</span>
                    <span
                      className={`text-[14px] ${accent ? "text-[var(--teal-l)] font-medium" : "text-white/80"}`}
                    >
                      {v}
                    </span>
                  </div>
                ))}
              </div>
              <p className="text-[11px] text-white/22 mt-4 text-center tracking-widest">⋯ 返信文を準備中</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="max-w-[920px] mx-auto px-10 py-[88px]">
        <p className="text-[12px] text-[var(--muted2)] tracking-[0.2em] mb-3">使い方</p>
        <h2 className="font-display text-[clamp(1.65rem,3vw,2.15rem)] font-medium text-[var(--ink)] leading-snug tracking-wide mb-14 md:mb-16">
          四つのステップ
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 md:gap-6 items-stretch">
          {steps.map((s) => (
            <div
              key={s.num}
              className="flex h-full flex-col rounded-[1.25rem] border border-[var(--border)] bg-white px-6 py-7 md:px-7 md:py-8 shadow-[0_1px_0_rgba(12,15,10,0.04)]"
            >
              <div className="font-display text-[2rem] text-[var(--teal)]/85 font-medium leading-none mb-4 tabular-nums">{s.num}</div>
              <h3 className="text-[16px] font-semibold text-[var(--ink)] mb-3 tracking-tight">{s.title}</h3>
              <p className="text-[14px] text-[var(--muted)] leading-[1.8] flex-1">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ── */}
      <section className="max-w-[1000px] mx-auto px-10 pb-[88px]">
        <div className="h-px bg-gradient-to-r from-transparent via-[var(--border)] to-transparent mb-14" />
        <p className="text-[12px] text-[var(--muted2)] tracking-[0.2em] mb-3">できること</p>
        <h2 className="font-display text-[clamp(1.65rem,3vw,2.15rem)] font-medium text-[var(--ink)] leading-tight tracking-wide mb-12 md:mb-14">
          安売りを減らすための機能
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 md:gap-6">
          {features.map((f, i) => (
            <div
              key={f.title}
              className={cn(
                "rounded-[1.25rem] p-7 md:p-8 border transition-shadow duration-300",
                i % 3 === 1 ? "bg-[#FAFAF8] border-[var(--border)]/90 shadow-[0_2px_24px_rgba(12,15,10,0.04)]" : "bg-white border-[var(--border)] shadow-[0_1px_0_rgba(12,15,10,0.03)]",
              )}
            >
              <div className="text-[1.35rem] mb-4 opacity-90">{f.icon}</div>
              <h3 className="text-[15px] font-semibold text-[var(--ink)] mb-2 tracking-tight">{f.title}</h3>
              <p className="text-[14px] text-[var(--muted)] leading-[1.8]">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="bg-[var(--ink)] py-[80px] px-10 text-center">
        <p className="text-[12px] text-[rgba(18,160,144,0.55)] tracking-[0.18em] mb-4">はじめる</p>
        <h2 className="font-display text-[clamp(1.75rem,3.2vw,2.35rem)] font-medium text-white mb-3 tracking-wide">もう安売りしない。</h2>
        <p className="text-white/38 text-[15px] mb-10 max-w-md mx-auto leading-relaxed">まずは無料で、自分の案件に当てはめてみてください。</p>
        <Link href="/estimate/new">
          <Button variant="teal" className="px-10 py-3.5 text-[15px] rounded-xl shadow-none">
            無料で見積もりを作る
          </Button>
        </Link>
        <p className="text-[11px] text-white/18 mt-8 tracking-wide">月500円のPro · 14日間お試し · いつでも解約可</p>
      </section>
    </main>
  )
}
