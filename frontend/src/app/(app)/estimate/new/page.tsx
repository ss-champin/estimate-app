import { EstimateForm } from "@/components/estimate/EstimateForm"
import { GeneratingOverlay } from "@/components/estimate/GeneratingOverlay"

export default function EstimateNewPage() {
  return (
    <>
      <GeneratingOverlay />
      <EstimateForm />
    </>
  )
}
