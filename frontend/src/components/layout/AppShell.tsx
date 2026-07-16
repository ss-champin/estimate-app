"use client"
import { AppNav } from "./AppNav"
import { DashSidebar } from "./DashSidebar"
import { Footer } from "./Footer"

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex flex-col min-h-screen">
      <AppNav />
      <div className="flex flex-1">
        <DashSidebar />
        <div className="flex-1 min-w-0">{children}</div>
      </div>
      <Footer />
    </div>
  )
}
