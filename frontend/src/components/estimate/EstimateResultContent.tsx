"use client"
import { useState } from "react"
import { Badge } from "@/components/ui"
import { formatCurrency } from "@/lib/utils"
import { cn } from "@/lib/utils"
import type { EstimateOutput } from "@/types/estimate"

const CONDITION_LABEL: Record<string, string> = {
  revision: "修正",
  delivery: "納品",
  spec_change: "仕様変更",
  payment: "お支払い",
  copyright: "著作権",
}

function SectionTitle({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <h2 className={cn("font-display text-[1.35rem] md:text-[1.5rem] font-medium text-[var(--ink)] tracking-wide", className)}>
      {children}
    </h2>
  )
}

interface Props {
  result: EstimateOutput
  aiProvider: string
  generatedAt: string
  actions?: React.ReactNode
}

export function EstimateResultContent({ result, aiProvider, generatedAt, actions }: Props) {
  const [copied, setCopied] = useState(false)

  const copyMessage = () => {
    navigator.clipboard.writeText(result.reply_message).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2500)
    })
  }

  const copyFull = () => {
    const text = [
      `見積もり: ${formatCurrency(result.amount_min)}〜${formatCurrency(result.amount_max)}`,
      `工数: ${result.hours_min}〜${result.hours_max}h`,
      `納期: ${result.deadline_days_min}〜${result.deadline_days_max}日`,
      "",
      result.reply_message,
    ].join("\n")
    navigator.clipboard.writeText(text)
  }

  const isGemini = aiProvider.includes("gemini")
  const diffLabel =
    result.difficulty === "simple" ? "シンプル" : result.difficulty === "standard" ? "標準〜やや複雑" : "複雑"

  const breakdownHoursTotal = result.breakdown.reduce((s, b) => s + b.hours, 0)
  const breakdownSubtotalTotal = result.breakdown.reduce((s, b) => s + b.subtotal, 0)
  const sameHoursRange = result.hours_min === result.hours_max
  const sameAmountRange = result.amount_min === result.amount_max

  return (
    <div className="max-w-[640px] mx-auto px-6 sm:px-8 py-12 md:py-16 pb-24">
      {result.warnings.length > 0 &&
        result.warnings.map((w, i) => (
          <div
            key={i}
            className="mb-10 pl-4 border-l-[3px] border-[#D4A574] bg-[var(--amber-bg)]/80 py-3 pr-4 text-[14px] text-[var(--amber)] leading-relaxed rounded-r-lg"
          >
            {w}
          </div>
        ))}

      <header className="mb-12 md:mb-14">
        <time className="block text-[13px] text-[var(--muted2)] mb-3 tabular-nums">
          {new Date(generatedAt).toLocaleString("ja-JP", { dateStyle: "medium", timeStyle: "short" })}
        </time>
        <SectionTitle>見積もりの概要</SectionTitle>
        <p className="mt-4 text-[15px] text-[var(--muted)] leading-[1.85] max-w-[34em]">
          入力いただいた案件内容に基づく目安です。金額・日数は交渉や仕様の確定で変わります。
        </p>
      </header>

      <section className="mb-14 md:mb-16 relative">
        <div className="absolute left-0 top-1 bottom-1 w-[2px] bg-gradient-to-b from-[var(--teal)]/50 to-[var(--teal)]/10 rounded-full" aria-hidden />
        <div className="pl-7">
          <p className="text-[12px] tracking-widest text-[var(--muted2)] uppercase mb-2">提案レンジ（税抜・目安）</p>
          <p className="font-display text-[clamp(1.75rem,6vw,2.5rem)] text-[var(--teal)] font-medium leading-tight tracking-tight">
            {sameAmountRange ? (
              formatCurrency(result.amount_min)
            ) : (
              <>
                {formatCurrency(result.amount_min)}
                <span className="text-[var(--muted2)] font-sans text-[0.55em] font-normal mx-2">〜</span>
                {formatCurrency(result.amount_max)}
              </>
            )}
          </p>
          <p className="text-[12px] text-[var(--muted2)] mt-3 leading-relaxed">
            提案の下限・上限は、入力した希望時給の下限・上限に合計工数（{breakdownHoursTotal}h）をそれぞれ乗じた金額です。
          </p>
          <p className="text-[12px] text-[var(--muted2)] mt-2 leading-relaxed">
            下記「工程別の内訳」は希望時給の上限（{formatCurrency(result.applied_hourly_max)}/h）を単価とした場合の積み上げで、小計の合計（{formatCurrency(breakdownSubtotalTotal)}）は提案レンジの上限側と一致します。
          </p>
          <p className="text-[12px] text-[var(--muted2)] mt-2 leading-relaxed">
            参考：目安の絶対下限 {formatCurrency(result.amount_floor)}
            （合計{breakdownHoursTotal}h×2,500円/h）· 強気ライン {formatCurrency(result.amount_ceiling)}
            （上限側の約120%を目安に調整した値）
          </p>
        </div>
      </section>

      <dl className="space-y-8 mb-16 pb-16 border-b border-[var(--border)]/80">
        <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-1 sm:gap-8">
          <dt className="text-[13px] text-[var(--muted)] shrink-0 w-28">作業工数</dt>
          <dd className="text-[15px] text-[var(--ink)] leading-relaxed flex-1">
            {sameHoursRange ? `${result.hours_min}h` : `${result.hours_min}h 〜 ${result.hours_max}h`}
            <span className="block sm:inline sm:ml-2 text-[13px] text-[var(--muted)] font-normal">
              （希望時給 {formatCurrency(result.applied_hourly_min)}〜{formatCurrency(result.applied_hourly_max)}/h をこの工数に適用）
            </span>
          </dd>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-1 sm:gap-8">
          <dt className="text-[13px] text-[var(--muted)] shrink-0 w-28">納期の目安</dt>
          <dd className="text-[15px] text-[var(--ink)] leading-relaxed flex-1">
            {result.deadline_days_min} 〜 {result.deadline_days_max} 日
            <span className="block sm:inline sm:ml-2 text-[13px] text-[var(--muted)] font-normal">修正・バッファ込みのイメージ</span>
          </dd>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-1 sm:gap-8">
          <dt className="text-[13px] text-[var(--muted)] shrink-0 w-28">難易度</dt>
          <dd className="text-[15px] text-[var(--ink)] leading-relaxed flex-1">
            <span className="font-medium">{diffLabel}</span>
            {result.difficulty_reason && (
              <p className="mt-2 text-[13px] text-[var(--muted)] leading-[1.75]">{result.difficulty_reason}</p>
            )}
          </dd>
        </div>
      </dl>

      <section className="mb-14">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
          <div>
            <SectionTitle className="mb-0">工程別の内訳</SectionTitle>
            <p className="text-[13px] text-[var(--muted)] mt-2 leading-relaxed">
              単価は希望時給の上限（{formatCurrency(result.hourly_rate_used)}/h）を適用した場合の見積もりです。
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              const txt = result.breakdown
                .map((b) => `${b.phase}  ${b.hours}h × ${formatCurrency(b.rate)} → ${formatCurrency(b.subtotal)}`)
                .join("\n")
              navigator.clipboard.writeText(txt)
            }}
            className="text-[13px] text-[var(--teal)] underline underline-offset-4 decoration-[var(--teal)]/40 hover:decoration-[var(--teal)] self-start sm:self-auto"
          >
            表をコピー
          </button>
        </div>
        <div className="overflow-x-auto -mx-1">
          <table className="w-full text-[14px] border-collapse">
            <thead>
              <tr className="border-b border-[var(--border2)]">
                <th className="text-left font-normal text-[var(--muted)] py-3 pr-4">工程</th>
                <th className="text-right font-normal text-[var(--muted)] py-3 px-2 whitespace-nowrap">工数</th>
                <th className="text-right font-normal text-[var(--muted)] py-3 px-2 whitespace-nowrap">単価</th>
                <th className="text-right font-normal text-[var(--muted)] py-3 pl-2 whitespace-nowrap">小計</th>
              </tr>
            </thead>
            <tbody>
              {result.breakdown.map((b, i) => (
                <tr key={i} className="border-b border-[var(--cream3)]/60 last:border-0">
                  <td className="py-4 pr-4 align-top">
                    <span className="text-[var(--ink)]">{b.phase}</span>
                    {b.note && <p className="text-[12px] text-[var(--muted)] mt-1 leading-relaxed">{b.note}</p>}
                  </td>
                  <td className="py-4 text-right tabular-nums text-[var(--ink)]">{b.hours}h</td>
                  <td className="py-4 text-right tabular-nums text-[var(--muted)]">{formatCurrency(b.rate)}</td>
                  <td className="py-4 text-right tabular-nums font-medium text-[var(--ink)]">{formatCurrency(b.subtotal)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr className="border-t-2 border-[var(--border)]">
                <td className="py-3.5 pr-4 font-medium text-[var(--ink)]">合計</td>
                <td className="py-3.5 text-right tabular-nums font-medium text-[var(--ink)]">{breakdownHoursTotal}h</td>
                <td className="py-3.5 text-right text-[var(--muted2)] text-[12px]">—</td>
                <td className="py-3.5 text-right tabular-nums font-semibold text-[var(--teal)]">
                  {formatCurrency(breakdownSubtotalTotal)}
                </td>
              </tr>
            </tfoot>
          </table>
        </div>
      </section>

      <section className="mb-14">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
          <SectionTitle className="mb-0">クライアントへの返信文</SectionTitle>
          <button
            type="button"
            onClick={copyMessage}
            className="inline-flex items-center justify-center rounded-lg bg-[var(--teal)] text-white text-[14px] px-5 py-2.5 font-medium hover:bg-[var(--teal-m)] transition-colors self-start sm:self-auto"
          >
            {copied ? "コピーしました" : "コピーする"}
          </button>
        </div>
        <div
          className="rounded-2xl bg-[#FDFCF9] px-6 py-7 md:px-8 md:py-8 text-[15px] leading-[2] text-[var(--ink2)] whitespace-pre-wrap shadow-[inset_0_1px_0_rgba(255,255,255,0.9),0_1px_2px_rgba(12,15,10,0.04)] border border-[var(--cream3)]"
        >
          {result.reply_message}
        </div>
      </section>

      <section className="mb-12">
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
          <SectionTitle className="mb-0">取引条件のたたき</SectionTitle>
          <button
            type="button"
            onClick={() => navigator.clipboard.writeText(result.conditions.map((c) => `・${c.text}`).join("\n"))}
            className="text-[13px] text-[var(--teal)] underline underline-offset-4 decoration-[var(--teal)]/40 hover:decoration-[var(--teal)] self-start sm:self-auto"
          >
            一覧をコピー
          </button>
        </div>
        <ul className="space-y-0 divide-y divide-[var(--border)]/90 border-t border-b border-[var(--border)]/90">
          {result.conditions.map((c, i) => (
            <li key={i} className="flex gap-4 py-4 first:pt-4 last:pb-4">
              <span className="text-[11px] text-[var(--muted2)] w-14 shrink-0 pt-0.5 tabular-nums">
                {CONDITION_LABEL[c.type] ?? "項目"}
              </span>
              <span className="text-[14px] leading-[1.75] text-[var(--ink)]">{c.text}</span>
            </li>
          ))}
        </ul>
      </section>

      <footer className="pt-2 pb-8">
        <p className="text-[12px] text-[var(--muted2)] leading-relaxed mb-1">
          生成: <Badge variant={isGemini ? "gray" : "teal"}>{aiProvider}</Badge>
        </p>
        <div className="flex flex-wrap gap-x-4 gap-y-2 mt-6">
          <button
            type="button"
            onClick={copyFull}
            className="text-[13px] text-[var(--muted)] hover:text-[var(--ink)] underline underline-offset-4 decoration-[var(--border2)]"
          >
            このページの要約をコピー
          </button>
        </div>
      </footer>

      {actions && (
        <div className="flex flex-col sm:flex-row gap-3 pt-8 mt-2 border-t border-[var(--border)]/80">
          {actions}
        </div>
      )}
    </div>
  )
}
