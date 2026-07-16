"use client"
import { useState, useRef, useEffect } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@clerk/nextjs"
import { useAuthMode } from "@/components/providers/AppProviders"
import { LOCAL_DEV_BEARER } from "@/lib/clerk-config"
import { toast } from "sonner"
import { Button, Input, Textarea } from "@/components/ui"
import { useEstimateStore } from "@/lib/store"
import { generateEstimate } from "@/lib/api"
import { cn } from "@/lib/utils"
import type { Complexity } from "@/types/estimate"

const TECH_STACKS = ["React","TypeScript","Next.js","Vue.js","Node.js","FastAPI","Python","AWS","Firebase","Supabase","PostgreSQL","Stripe連携","Flutter","React Native","Figmaデザイン"]

const COMPLEXITY: { value: Complexity; label: string; desc: string; hours: string }[] = [
  { value: "simple",   label: "シンプル",   desc: "LP・静的サイト・小改修", hours: "〜30h" },
  { value: "standard", label: "標準",       desc: "Webアプリ・API連携",     hours: "30〜80h" },
  { value: "complex",  label: "複雑",       desc: "大規模・設計込み",        hours: "80h〜" },
]

const GENERATE_STEPS = [
  "案件タイトル・内容を解析中",
  "技術スタックと難易度を解析中",
  "エンジニア相場データを参照中",
  "工程別工数を計算中",
  "見積もり金額を算出中",
  "クライアント返信文を生成中",
  "取引条件テンプレートを適用中",
]

type GetToken = () => Promise<string | null>

function EstimateFormInner({ getToken }: { getToken: GetToken }) {
  const router  = useRouter()
  const { request, setRequest, setResult, isGenerating, setGenerating, setGenerateStep, resetNewEstimateForm } = useEstimateStore()

  const [stacks,     setStacks]     = useState<string[]>([])
  const [cx,         setCx]         = useState<Complexity>("standard")
  const [customInput, setCustomInput] = useState("")
  const customInputRef = useRef<HTMLInputElement>(null)

  const resetLocalFormFields = () => {
    setStacks([])
    setCx("standard")
    setCustomInput("")
  }

  useEffect(() => {
    return () => {
      resetNewEstimateForm()
    }
  }, [resetNewEstimateForm])

  const toggleStack = (s: string) =>
    setStacks((p) => p.includes(s) ? p.filter((x) => x !== s) : [...p, s])

  const addCustomStack = () => {
    const val = customInput.trim()
    if (!val) return
    if (!stacks.includes(val)) setStacks((p) => [...p, val])
    setCustomInput("")
    customInputRef.current?.focus()
  }

  const runGenerate = async (job_title: string | undefined, job_description: string) => {
    setGenerating(true)
    let stepIdx = 0
    const stepTimer = setInterval(() => {
      setGenerateStep(GENERATE_STEPS[stepIdx % GENERATE_STEPS.length])
      stepIdx++
    }, 800)

    try {
      const token = await getToken()
      if (!token) throw new Error("認証エラー")

      const res = await generateEstimate({
        job_title:       job_title || undefined,
        job_description,
        tech_stack:      stacks,
        complexity:      cx,
        hourly_rate_min: Number(request.hourly_rate_min) || 0,
        hourly_rate_max: Number(request.hourly_rate_max) || 0,
        freelancer_name: request.freelancer_name || "フリーランサー",
      }, token)

      setResult(res.data, res.ai_provider, res.generated_at)
      clearInterval(stepTimer)
      resetNewEstimateForm()
      resetLocalFormFields()
      toast.success("✦ 見積もりを生成しました")
      router.push("/estimate/result")
    } catch (e: unknown) {
      clearInterval(stepTimer)
      setGenerating(false)
      const err = e as { message?: string; status?: number }
      if (err.status === 429) {
        toast.error("本日の生成回数上限に達しました。明日またご利用ください。")
      } else if (err.status === 503) {
        toast.error("AIモデルが混雑しています。しばらくしてから再試行してください。")
      } else {
        toast.error(err.message || "生成に失敗しました。もう一度お試しください。")
      }
    }
  }

  const handleGenerate = async () => {
    const desc = (request.job_description ?? "").trim()
    if (desc.length < 10) {
      toast.error("案件内容は10文字以上入力してください")
      return
    }
    const hmin = Number(request.hourly_rate_min) || 0
    const hmax = Number(request.hourly_rate_max) || 0
    if (hmin < 1 || hmax < 1) {
      toast.error("希望時給の下限・上限を入力してください（いずれも1円以上）")
      return
    }
    if (hmin > hmax) {
      toast.error("希望時給の下限が上限を超えています")
      return
    }
    const title = (request.job_title ?? "").trim()
    setRequest({ job_title: title || undefined, job_description: desc })
    await runGenerate(title || undefined, desc)
  }

  return (
    <div className="max-w-[740px] mx-auto px-6 py-10 afu">
      <div className="mb-7">
        <h1 className="font-display text-[1.65rem] md:text-[1.85rem] font-medium tracking-wide mb-1">見積もりを作成</h1>
        <p className="text-[14px] text-[var(--muted)]">案件タイトルと内容を入力してください</p>
      </div>

      <div className="mb-4">
        <label className="block text-[13px] font-medium mb-1.5">案件タイトル <span className="text-[var(--muted2)] font-normal text-[12px]">任意</span></label>
        <Input placeholder="例：ReactでのECサイトフロントエンド開発"
          value={request.job_title ?? ""}
          onChange={(e) => setRequest({ job_title: e.target.value })} />
      </div>
      <div className="mb-5">
        <label className="block text-[13px] font-medium mb-1.5">案件内容</label>
        <Textarea className="min-h-[160px]" placeholder="案件の詳細・要件・依頼内容などを貼り付けてください。"
          value={request.job_description ?? ""}
          onChange={(e) => setRequest({ job_description: e.target.value })} />
      </div>

      <div className="h-px bg-[var(--border)] my-6" />

      {/* Tech Stack */}
      <div className="mb-5">
        <label className="block text-[13px] font-medium mb-1">
          使用技術・スタック{" "}
          <span className="text-[var(--muted2)] font-normal text-[12px]">選択 or 自由入力（両方使えます）</span>
        </label>

        <div className="flex flex-wrap gap-1.5 mt-2">
          {TECH_STACKS.map((s) => (
            <button key={s} onClick={() => toggleStack(s)}
              className={cn("px-3 py-1.5 rounded border-[1.5px] text-[12px] font-medium font-mono transition-all",
                stacks.includes(s) ? "border-[var(--teal)] bg-[var(--teal-bg)] text-[var(--teal)]" : "border-[var(--border)] text-[var(--muted)] bg-white hover:border-[var(--teal)] hover:text-[var(--teal)]")}>
              {s}
            </button>
          ))}
        </div>

        <div className="flex gap-2 mt-2.5">
          <input
            ref={customInputRef}
            value={customInput}
            onChange={(e) => setCustomInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addCustomStack() } }}
            placeholder="上記にない技術を入力"
            className="flex-1 h-9 px-3 rounded-lg border-[1.5px] border-[var(--border)] bg-white text-[13px] font-mono placeholder:text-[var(--muted2)] focus:outline-none focus:border-[var(--teal)] transition-colors"
          />
          <button
            onClick={addCustomStack}
            disabled={!customInput.trim()}
            className="px-4 h-9 rounded-lg border-[1.5px] border-[var(--teal)] text-[var(--teal)] text-[12px] font-medium bg-[var(--teal-bg)] hover:bg-[var(--teal)] hover:text-white transition-all disabled:opacity-40 disabled:pointer-events-none">
            追加
          </button>
        </div>

        {stacks.filter((s) => !TECH_STACKS.includes(s)).length > 0 && (
          <div className="flex flex-wrap gap-1.5 mt-2">
            {stacks.filter((s) => !TECH_STACKS.includes(s)).map((s) => (
              <span key={s}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded border-[1.5px] border-[var(--teal)] bg-[var(--teal-bg)] text-[var(--teal)] text-[12px] font-medium font-mono">
                {s}
                <button onClick={() => toggleStack(s)} className="ml-0.5 leading-none hover:opacity-60 text-[14px]">×</button>
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="mb-5">
        <label className="block text-[13px] font-medium mb-1.5">案件の複雑度</label>
        <div className="grid grid-cols-3 gap-2">
          {COMPLEXITY.map((c) => (
            <button key={c.value} onClick={() => setCx(c.value)}
              className={cn("text-left border-[1.5px] rounded-xl px-4 py-3.5 transition-all",
                cx === c.value ? "border-[var(--teal)] bg-[var(--teal-bg)]" : "border-[var(--border)] bg-white hover:border-[var(--border2)]")}>
              <div className={cn("text-[14px] font-semibold mb-0.5", cx === c.value && "text-[var(--teal)]")}>{c.label}</div>
              <div className={cn("text-[11px] leading-[1.5]", cx === c.value ? "text-[var(--teal)] opacity-75" : "text-[var(--muted)]")}>
                {c.desc}<br />{c.hours}
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="mb-5">
        <label className="block text-[13px] font-medium mb-1.5">
          希望時給（税抜）<span className="text-[var(--muted2)] font-normal text-[12px]">必須 · レンジと内訳の計算に使います</span>
        </label>
        <div className="grid grid-cols-2 gap-2.5">
          <div>
            <Input mono placeholder="例：3,500" type="number" min={1} value={request.hourly_rate_min || ""} onChange={(e) => setRequest({ hourly_rate_min: Number(e.target.value) })} />
            <p className="text-[12px] text-[var(--muted)] mt-1">下限（円/h）</p>
          </div>
          <div>
            <Input mono placeholder="例：5,000" type="number" min={1} value={request.hourly_rate_max || ""} onChange={(e) => setRequest({ hourly_rate_max: Number(e.target.value) })} />
            <p className="text-[12px] text-[var(--muted)] mt-1">上限（円/h）</p>
          </div>
        </div>
      </div>

      <Button variant="teal" full onClick={handleGenerate} disabled={isGenerating}>
        {isGenerating ? (
          <><span className="w-2 h-2 rounded-full bg-white dot-1 inline-block"/><span className="w-2 h-2 rounded-full bg-white dot-2 inline-block"/><span className="w-2 h-2 rounded-full bg-white dot-3 inline-block"/></>
        ) : "✦ 見積もりを生成する"}
      </Button>
      <p className="text-[12px] text-[var(--muted)] text-center mt-2.5">生成には約5〜10秒かかります</p>
    </div>
  )
}

function EstimateFormWithClerk() {
  const { getToken } = useAuth()
  return <EstimateFormInner getToken={getToken} />
}

export function EstimateForm() {
  const mode = useAuthMode()
  if (mode === "dev") {
    return <EstimateFormInner getToken={async () => LOCAL_DEV_BEARER} />
  }
  return <EstimateFormWithClerk />
}
