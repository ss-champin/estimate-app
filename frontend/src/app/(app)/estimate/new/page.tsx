import { AppNav } from "@/components/layout/AppNav"
import { EstimateForm } from "@/components/estimate/EstimateForm"
import { GeneratingOverlay } from "@/components/estimate/GeneratingOverlay"

export default function EstimateNewPage() {
  return (
    <div className="min-h-screen">
      <AppNav />
      <GeneratingOverlay />
      <EstimateForm />
    </div>
  )
}
