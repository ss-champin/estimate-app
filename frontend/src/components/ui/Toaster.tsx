"use client"
import { Toaster as Sonner } from "sonner"

export function Toaster() {
  return (
    <Sonner
      position="bottom-right"
      toastOptions={{
        style: { fontFamily: "'Outfit', sans-serif", fontSize: "13px", borderRadius: "10px" },
        className: "border border-[var(--border)]",
      }}
    />
  )
}
