import { AppNav } from "@/components/layout/AppNav"
import { Footer } from "@/components/layout/Footer"

const SECTIONS = [
  {
    title: "1. 収集する情報",
    body: `本サービスでは、以下の情報を収集します。

・アカウント登録時のメールアドレスおよび認証情報
・本サービスの利用状況（見積もりの生成回数、生成日時）
・有料プランご利用の場合の決済に必要な情報（カード情報は当社のサーバーには保存されません）`,
  },
  {
    title: "2. 情報の利用目的",
    body: `収集した情報は、本サービスの提供・運営・改善およびサポート対応のみに使用します。取得した個人情報は、上記の目的以外には一切使用しません。`,
  },
  {
    title: "3. 第三者への提供",
    body: `当社は、以下の場合を除き、ユーザーの個人情報を第三者に提供しません。

・ユーザーの同意がある場合
・法令に基づく場合
・人の生命・身体・財産の保護に必要な場合`,
  },
  {
    title: "4. データの保存・管理",
    body: `ユーザーデータは適切なセキュリティ対策を施したサーバーで管理します。生成した見積もりデータは有料プランではサービス内で閲覧できます。

アカウントを削除した場合、関連するデータは当社の定める期間内に削除されます。`,
  },
  {
    title: "5. Cookieの利用",
    body: `本サービスでは、認証状態の維持のためにCookieおよびローカルストレージを利用しています。ブラウザの設定によりCookieを無効にした場合、一部の機能が正しく動作しないことがあります。`,
  },
  {
    title: "6. ユーザーの権利",
    body: `ユーザーは、自身の個人情報について、開示・訂正・削除を請求することができます。請求はサービス内の設定画面またはメールにてお問い合わせください。`,
  },
  {
    title: "7. プライバシーポリシーの変更",
    body: `当社は、必要に応じて本プライバシーポリシーを変更することがあります。変更後のポリシーは本ページに掲載します。重要な変更がある場合は、サービス内またはメールにてお知らせします。`,
  },
]

export default function PrivacyPage() {
  return (
    <div className="min-h-screen flex flex-col">
      <AppNav />

      <main className="flex-1 max-w-[760px] mx-auto w-full px-6 py-16">
        <div className="mb-10">
          <p className="font-mono text-[11px] text-[var(--muted2)] tracking-[0.15em] mb-3">// PRIVACY</p>
          <h1 className="text-[2rem] font-semibold text-[var(--ink)] mb-2">プライバシーポリシー</h1>
          <p className="text-[13px] text-[var(--muted)]">最終更新日：2026年7月17日</p>
        </div>

        <p className="text-[14px] text-[var(--muted)] leading-[1.9] mb-10">
          libernate.app（以下「当社」）は、EstiMate（以下「本サービス」）において取得するユーザーの個人情報の取り扱いについて、以下のとおりプライバシーポリシーを定めます。
        </p>

        <div className="flex flex-col gap-8">
          {SECTIONS.map((s) => (
            <section key={s.title}>
              <h2 className="text-[16px] font-semibold text-[var(--ink)] mb-3">{s.title}</h2>
              <p className="text-[14px] text-[var(--muted)] leading-[1.9] whitespace-pre-line">{s.body}</p>
            </section>
          ))}
        </div>

      </main>

      <Footer />
    </div>
  )
}
