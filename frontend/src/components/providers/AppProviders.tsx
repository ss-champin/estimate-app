"use client"

import { createContext, useContext, type ReactNode } from "react"
import { ClerkProvider } from "@clerk/nextjs"
import { isClerkConfigured } from "@/lib/clerk-config"

type AuthMode = "clerk" | "dev"

const AuthModeContext = createContext<AuthMode>("clerk")

export function useAuthMode(): AuthMode {
  return useContext(AuthModeContext)
}

const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY?.trim() ?? ""

const signInUrl = process.env.NEXT_PUBLIC_CLERK_SIGN_IN_URL?.trim() || "/auth"
const signUpUrl = process.env.NEXT_PUBLIC_CLERK_SIGN_UP_URL?.trim() || "/auth"

export function AppProviders({ children }: { children: ReactNode }) {
  if (isClerkConfigured()) {
    return (
      <AuthModeContext.Provider value="clerk">
        <ClerkProvider
          publishableKey={publishableKey}
          signInUrl={signInUrl}
          signUpUrl={signUpUrl}
        >
          {children}
        </ClerkProvider>
      </AuthModeContext.Provider>
    )
  }
  return <AuthModeContext.Provider value="dev">{children}</AuthModeContext.Provider>
}
