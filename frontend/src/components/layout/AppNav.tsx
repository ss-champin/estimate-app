"use client"
import Link from "next/link"
import { SignedIn, SignedOut, UserButton } from "@clerk/nextjs"
import { Button } from "@/components/ui"
import { useAuthMode } from "@/components/providers/AppProviders"

export function AppNav() {
  const mode = useAuthMode()
  const isDevAuth = mode === "dev"

  return (
    <header className="sticky top-0 z-50 bg-[rgba(247,246,242,0.94)] backdrop-blur-md border-b border-[var(--border)] h-[58px] px-10 flex items-center justify-between">
      <Link href="/" className="flex items-center gap-2">
        <div className="w-[26px] h-[26px] rounded-md bg-[var(--teal)] flex items-center justify-center">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 7h10M7 2l5 5-5 5"/></svg>
        </div>
        <span className="font-mono text-[17px] font-medium text-[var(--ink)] tracking-tight">EstiMate</span>
      </Link>
      <div className="flex items-center gap-3">
        {isDevAuth ? (
          <>
            <span className="font-mono text-[10px] text-[var(--muted)] border border-[var(--border)] rounded px-2 py-0.5">dev（Clerkなし）</span>
            <Link href="/estimate/new"><Button variant="teal" size="sm">見積もりを作る →</Button></Link>
            <Link href="/dashboard"><Button variant="ghost" size="sm">ダッシュボード</Button></Link>
          </>
        ) : (
          <>
            <SignedIn>
              <Link href="/estimate/new"><Button variant="teal" size="sm">見積もりを作る →</Button></Link>
              <UserButton afterSignOutUrl="/" />
            </SignedIn>
            <SignedOut>
              <Link href="/auth"><Button variant="ghost" size="sm">ログイン</Button></Link>
              <Link href="/auth"><Button variant="teal" size="sm">無料で始める</Button></Link>
            </SignedOut>
          </>
        )}
      </div>
    </header>
  )
}
