"use client"
import { useEstimateStore } from "@/lib/store"

export function GeneratingOverlay() {
  const { isGenerating, generateStep } = useEstimateStore()
  if (!isGenerating) return null

  return (
    <div className="fixed inset-0 z-[500] bg-[rgba(247,246,242,0.92)] backdrop-blur-md flex flex-col items-center justify-center gap-5">
      <div className="flex gap-2.5">
        <span className="w-2.5 h-2.5 rounded-full bg-[var(--teal)] dot-1 inline-block"/>
        <span className="w-2.5 h-2.5 rounded-full bg-[var(--teal)] dot-2 inline-block"/>
        <span className="w-2.5 h-2.5 rounded-full bg-[var(--teal)] dot-3 inline-block"/>
      </div>
      <div className="text-[15px] text-[var(--muted)] font-medium">AIが見積もりを生成しています...</div>
      <div className="font-mono text-[12px] text-[var(--muted2)] transition-all min-h-[18px]">{generateStep}</div>
    </div>
  )
}
