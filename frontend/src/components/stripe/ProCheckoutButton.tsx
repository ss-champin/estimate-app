"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@clerk/nextjs"
import { toast } from "sonner"
import { useAuthMode } from "@/components/providers/AppProviders"
import { createCheckoutSession } from "@/lib/api"
import { LOCAL_DEV_BEARER } from "@/lib/clerk-config"
import { Button } from "@/components/ui"

type Props = {
  children: React.ReactNode
  full?: boolean
  variant?: "ink" | "teal" | "outline" | "ghost"
  className?: string
}

function detailMessage(err: unknown): string {
  if (err && typeof err === "object" && "detail" in err) {
    const d = (err as { detail: unknown }).detail
    if (typeof d === "string") return d
    if (Array.isArray(d) && d[0] && typeof d[0] === "object" && "msg" in d[0]) {
      return String((d[0] as { msg: string }).msg)
    }
  }
  if (err instanceof Error) return err.message
  return "決済の開始に失敗しました"
}

/** Clerk 未設定の dev モードでは useAuth を呼ばない（Provider 外で落ちるのを防ぐ） */
function ProCheckoutButtonDev({
  children,
  full,
  variant = "teal",
  className,
}: Props) {
  const [loading, setLoading] = useState(false)

  const onClick = async () => {
    setLoading(true)
    try {
      const { url } = await createCheckoutSession(LOCAL_DEV_BEARER)
      window.location.href = url
    } catch (e: unknown) {
      toast.error(detailMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Button
      type="button"
      variant={variant}
      full={full}
      className={className}
      disabled={loading}
      onClick={() => void onClick()}
    >
      {loading ? "処理中…" : children}
    </Button>
  )
}

function ProCheckoutButtonClerk({ children, full, variant = "teal", className }: Props) {
  const { getToken } = useAuth()
  const router = useRouter()
  const [loading, setLoading] = useState(false)

  const onClick = async () => {
    setLoading(true)
    try {
      const token = await getToken()
      if (!token) {
        toast.info("ログインが必要です")
        router.push("/auth")
        return
      }
      const { url } = await createCheckoutSession(token)
      window.location.href = url
    } catch (e: unknown) {
      toast.error(detailMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Button
      type="button"
      variant={variant}
      full={full}
      className={className}
      disabled={loading}
      onClick={() => void onClick()}
    >
      {loading ? "処理中…" : children}
    </Button>
  )
}

export function ProCheckoutButton(props: Props) {
  const mode = useAuthMode()
  if (mode === "dev") {
    return <ProCheckoutButtonDev {...props} />
  }
  return <ProCheckoutButtonClerk {...props} />
}
