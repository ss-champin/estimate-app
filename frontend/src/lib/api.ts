import type { EstimateAPIResponse, EstimateRequest, UsageStatus, EstimateHistory } from "@/types/estimate"

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"

async function req<T>(path: string, init: RequestInit = {}, token?: string): Promise<T> {
  const headers: Record<string,string> = { "Content-Type": "application/json", ...(init.headers as Record<string,string>) }
  if (token) headers["Authorization"] = `Bearer ${token}`
  const res = await fetch(`${BASE}${path}`, { ...init, headers })
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw { status: res.status, ...e } }
  return res.json() as Promise<T>
}

export const generateEstimate = (body: EstimateRequest, token: string) =>
  req<EstimateAPIResponse>("/api/estimate/generate", { method: "POST", body: JSON.stringify(body) }, token)

export const getUsageStatus = (token: string) =>
  req<UsageStatus>("/api/estimate/usage", {}, token)

export const getEstimateHistory = (token: string) =>
  req<EstimateHistory[]>("/api/estimates", {}, token)
