import type { Metadata } from "next"
import { Toaster } from "@/components/ui/Toaster"
import { AppProviders } from "@/components/providers/AppProviders"
import "./globals.css"

export const metadata: Metadata = {
  title: "EstiMate — エンジニア向け見積もり自動生成",
  description: "案件タイトルと依頼内容を入力するだけで、AIがエンジニア相場に基づいた見積もりと返信文を即座に生成。",
  metadataBase: new URL(process.env.NEXT_PUBLIC_APP_URL ?? "http://localhost:3000"),
  openGraph: {
    title: "EstiMate — エンジニア向け見積もり自動生成",
    description: "タイトルと内容を入れるだけで見積もり完成。安売りをなくすAIツール。",
    type: "website",
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ja">
      <body>
        <AppProviders>
          {children}
          <Toaster />
        </AppProviders>
      </body>
    </html>
  )
}
