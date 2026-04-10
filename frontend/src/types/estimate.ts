export type Complexity = "simple" | "standard" | "complex"
export type Plan       = "free" | "paid"

export interface EstimateRequest {
  job_title?:      string
  job_description: string
  tech_stack:      string[]
  complexity:      Complexity
  hourly_rate_min: number
  hourly_rate_max: number
  freelancer_name: string
}

export interface BreakdownItem {
  phase:    string
  hours:    number
  rate:     number
  subtotal: number
  note:     string
}

export type ConditionType = "revision"|"delivery"|"spec_change"|"payment"|"copyright"

export interface Condition {
  type: ConditionType
  text: string
}

export interface EstimateOutput {
  amount_min: number; amount_max: number; amount_floor: number; amount_ceiling: number
  hours_min: number; hours_max: number
  deadline_days_min: number; deadline_days_max: number
  hourly_rate_used: number
  applied_hourly_min: number
  applied_hourly_max: number
  difficulty: Complexity; difficulty_reason: string
  breakdown: BreakdownItem[]
  reply_message: string
  conditions: Condition[]
  warnings: string[]
}

export interface EstimateAPIResponse {
  success: boolean; data: EstimateOutput; ai_provider: string; generated_at: string
}

export interface UsageStatus {
  plan: Plan
  daily_used: number; daily_limit: number | null
  monthly_used: number; monthly_limit: number
  daily_remaining: number | null; monthly_remaining: number
}

export interface EstimateHistory {
  id: string
  title: string
  amount_min: number
  amount_max: number
  hours_min: number
  hours_max: number
  ai_provider: string
  created_at: string
}
