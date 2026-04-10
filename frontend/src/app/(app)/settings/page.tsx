import { AppNav } from "@/components/layout/AppNav"
import { DashSidebar } from "@/components/layout/DashSidebar"
import { UserProfile } from "@clerk/nextjs"
import { isClerkConfigured } from "@/lib/clerk-config"

export default function SettingsPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <AppNav />
      <div className="flex flex-1">
        <DashSidebar />
        <main className="flex-1 p-9 bg-[var(--cream)]">
          <h1 className="text-[22px] font-bold mb-6">設定</h1>
          {isClerkConfigured() ? (
            <UserProfile routing="hash" />
          ) : (
            <p className="text-[14px] text-[var(--muted)] max-w-lg leading-relaxed">
              Clerk 未設定の開発モードではアカウント管理 UI は利用できません。本番相当の動作には
              <code className="mx-1 font-mono text-[12px]">NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY</code>
              を設定してください。
            </p>
          )}
        </main>
      </div>
    </div>
  )
}
