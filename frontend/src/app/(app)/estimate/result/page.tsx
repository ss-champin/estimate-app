import { AppNav } from "@/components/layout/AppNav"
import { EstimateResult } from "@/components/estimate/EstimateResult"

export default function EstimateResultPage() {
  return (
    <div className="min-h-screen">
      <AppNav />
      <EstimateResult />
    </div>
  )
}
