import { auth } from "@clerk/nextjs/server"
import { redirect } from "next/navigation"
import { isClerkConfigured } from "@/lib/clerk-config"

export default async function AppLayout({ children }: { children: React.ReactNode }) {
  if (!isClerkConfigured()) {
    return <>{children}</>
  }
  const { userId } = await auth()
  if (!userId) redirect("/auth")
  return <>{children}</>
}
