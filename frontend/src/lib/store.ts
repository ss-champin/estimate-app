import { create } from "zustand"
import type { EstimateOutput, EstimateRequest } from "@/types/estimate"

interface EstimateStore {
  // 入力フォームの状態
  request:    Partial<EstimateRequest>
  setRequest: (req: Partial<EstimateRequest>) => void
  resetRequest: () => void
  /** 見積もり作成フォームの入力・生成中UIを初期化（生成結果は保持） */
  resetNewEstimateForm: () => void

  // 生成結果
  result:     EstimateOutput | null
  aiProvider: string
  generatedAt: string
  setResult:  (result: EstimateOutput, provider: string, at: string) => void
  clearResult: () => void

  // UI状態
  isGenerating: boolean
  setGenerating: (v: boolean) => void
  generateStep:  string
  setGenerateStep: (s: string) => void
}

const DEFAULT_REQUEST: Partial<EstimateRequest> = {
  job_title:         undefined,
  tech_stack:        [],
  complexity:        "standard",
  hourly_rate_min:   0,
  hourly_rate_max:   0,
  freelancer_name:   "",
  job_description:   "",
}

export const useEstimateStore = create<EstimateStore>((set) => ({
  request:         { ...DEFAULT_REQUEST },
  setRequest:      (req) => set((s) => ({ request: { ...s.request, ...req } })),
  resetRequest:    () => set({ request: { ...DEFAULT_REQUEST } }),
  resetNewEstimateForm: () =>
    set({
      request: { ...DEFAULT_REQUEST },
      isGenerating: false,
      generateStep: "",
    }),

  result:          null,
  aiProvider:      "",
  generatedAt:     "",
  setResult:       (result, aiProvider, generatedAt) => set({ result, aiProvider, generatedAt }),
  clearResult:     () => set({ result: null }),

  isGenerating:    false,
  setGenerating:   (v) => set({ isGenerating: v }),
  generateStep:    "",
  setGenerateStep: (s) => set({ generateStep: s }),
}))
