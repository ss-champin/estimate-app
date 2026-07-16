import { auth } from "@clerk/nextjs/server"
import { redirect } from "next/navigation"
import { isClerkConfigured } from "@/lib/clerk-config"
import { AppShell } from "@/components/layout/AppShell"

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  if (isClerkConfigured()) {
    const { userId } = await auth()
    if (!userId) redirect("/auth")
  }
  return <AppShell>{children}</AppShell>
}
