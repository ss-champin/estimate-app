"use client"

import { useState } from "react"
import { useAuth } from "@clerk/nextjs"
import { toast } from "sonner"
import { useAuthMode } from "@/components/providers/AppProviders"
import { createPortalSession } from "@/lib/api"
import { LOCAL_DEV_BEARER } from "@/lib/clerk-config"
import { Button } from "@/components/ui"

function detailMessage(err: unknown): string {
  if (err && typeof err === "object" && "detail" in err) {
    const d = (err as { detail: unknown }).detail
    if (typeof d === "string") return d
  }
  if (err instanceof Error) return err.message
  return "請求ポータルを開けませんでした"
}

function ManageBillingButtonDev() {
  const [loading, setLoading] = useState(false)

  const onClick = async () => {
    setLoading(true)
    try {
      const { url } = await createPortalSession(LOCAL_DEV_BEARER)
      window.location.href = url
    } catch (e: unknown) {
      toast.error(detailMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Button type="button" variant="outline" size="sm" disabled={loading} onClick={() => void onClick()}>
      {loading ? "開いています…" : "請求・プラン管理（Stripe）"}
    </Button>
  )
}

function ManageBillingButtonClerk() {
  const { getToken } = useAuth()
  const [loading, setLoading] = useState(false)

  const onClick = async () => {
    setLoading(true)
    try {
      const token = await getToken()
      if (!token) {
        toast.error("ログインが必要です")
        return
      }
      const { url } = await createPortalSession(token)
      window.location.href = url
    } catch (e: unknown) {
      toast.error(detailMessage(e))
    } finally {
      setLoading(false)
    }
  }

  return (
    <Button type="button" variant="outline" size="sm" disabled={loading} onClick={() => void onClick()}>
      {loading ? "開いています…" : "請求・プラン管理（Stripe）"}
    </Button>
  )
}

export function ManageBillingButton() {
  const mode = useAuthMode()
  if (mode === "dev") {
    return <ManageBillingButtonDev />
  }
  return <ManageBillingButtonClerk />
}
