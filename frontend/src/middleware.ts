import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server"
import { NextResponse } from "next/server"

const isPublic = createRouteMatcher(["/", "/auth(.*)", "/pricing"])

const pk = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.trim() ?? ""
const clerkConfigured = (pk.startsWith("pk_test_") || pk.startsWith("pk_live_")) && pk.length >= 20

export default clerkConfigured
  ? clerkMiddleware(async (auth, req) => {
      if (!isPublic(req)) await auth.protect()
    })
  : function middleware() {
      return NextResponse.next()
    }

export const config = {
  matcher: ["/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)", "/(api|trpc)(.*)"],
}
