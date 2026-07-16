import Link from "next/link"
import { SignIn, SignUp } from "@clerk/nextjs"
import { isClerkConfigured } from "@/lib/clerk-config"

export default async function AuthPage({ params }: { params: Promise<{ rest?: string[] }> }) {
  const { rest } = await params
  const isSignUp = rest?.includes("sign-up")

  if (!isClerkConfigured()) {
    return (
      <div className="min-h-screen bg-[var(--ink)] flex flex-col items-center justify-center gap-6 px-6">
        <div className="text-center text-white/80 text-[15px] max-w-md leading-relaxed">
          Clerk の Publishable Key が未設定、またはプレースホルダーのままです。
          <br />
          ローカルでは認証なしで開発できます。ダッシュボードへ進んでください。
        </div>
        <Link href="/dashboard" className="text-[var(--teal-l)] font-medium underline underline-offset-4">
          ダッシュボードへ
        </Link>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[var(--ink)] flex items-center justify-center">
      <div className="text-center mb-6 absolute top-10 left-1/2 -translate-x-1/2">
        <div className="flex items-center gap-2 justify-center">
          <div className="w-7 h-7 rounded-md bg-[var(--teal)] flex items-center justify-center">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M2 7h10M7 2l5 5-5 5"/>
            </svg>
          </div>
          <span className="font-mono text-lg font-medium text-white">EstiMate</span>
        </div>
      </div>
      {isSignUp
        ? <SignUp fallbackRedirectUrl="/dashboard" />
        : <SignIn fallbackRedirectUrl="/dashboard" />
      }
    </div>
  )
}
