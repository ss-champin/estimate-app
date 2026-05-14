import Link from "next/link"
import { AppNav } from "@/components/layout/AppNav"
import { ProCheckoutButton } from "@/components/stripe/ProCheckoutButton"
import { Button } from "@/components/ui"
import { cn } from "@/lib/utils"

const PLANS = [
  {
    key: "free", badge: "FREE", name: "無料プラン", desc: "まずは試してみたい方に",
    price: "¥0", unit: "/ 月",
    features: [
      { yes: true,  text: "案件タイトル・内容から見積もり生成" },
      { yes: true,  text: "月3回まで生成可能" },
      { yes: true,  text: "返信メッセージ自動生成" },
      { yes: true,  text: "取引条件テンプレ" },
      { yes: false, text: "見積もり履歴の保存" },
      { yes: false, text: "PDF出力" },
      { yes: false, text: "月30回生成" },
    ],
    aiNote: "Gemini AIで生成（高品質）",
    cta: "無料で始める", ctaHref: "/auth", featured: false,
  },
  {
    key: "pro", badge: "PRO ✦ おすすめ", name: "Proプラン", desc: "ガンガン使いたいエンジニアに",
    price: "¥500", unit: "/ 月（税込）",
    features: [
      { yes: true, text: "URLまたはテキストで見積もり生成" },
      { yes: true, text: "1日10回・月30回まで生成" },
      { yes: true, text: "返信メッセージ自動生成" },
      { yes: true, text: "取引条件テンプレ" },
      { yes: true, text: "見積もり履歴の保存・管理" },
      { yes: true, text: "PDF出力" },
      { yes: true, text: "Claude Haiku（最高品質AIで生成）" },
    ],
    aiNote: "Claude Haiku AIで生成（最高品質）",
    cta: "14日間無料で試す →", ctaHref: "/auth", featured: true,
  },
]

const FAQS = [
  { q: "無料プランと有料プランでAIの品質は違いますか？", a: "はい。無料プランはGemini 2.5 Flash-Lite、有料プランはClaude Haiku 4.5を使用します。有料プランの方が日本語の自然さと見積もり精度が向上します。" },
  { q: "案件ページのどこを貼ればいいですか？", a: "依頼タイトルと本文が分かる範囲を、そのままフォームに貼り付けてください。形式は問いません。" },
  { q: "いつでもキャンセルできますか？", a: "はい、いつでもキャンセル可能です。キャンセルすると次回更新日から無料プランに移行します。" },
  { q: "生成した見積もりはどのくらい保存されますか？", a: "有料プランでは見積もり履歴を無制限に保存できます。無料プランは生成結果をコピーして別途保存してください。" },
]

export default function PricingPage() {
  return (
    <div className="min-h-screen">
      <AppNav />

      {/* Hero */}
      <div className="bg-[var(--ink)] py-20 px-10 text-center">
        <div className="font-mono text-[11px] text-[rgba(18,160,144,0.6)] tracking-[1px] mb-3">// PRICING</div>
        <h1 className="text-[44px] font-black text-white mb-2.5 tracking-[-1px]">シンプルな料金体系</h1>
        <p className="text-white/45 text-[16px]">まず無料で試して、気に入ったら月500円で全機能を解放。</p>
      </div>

      {/* Plans */}
      <div className="max-w-[860px] mx-auto px-6 py-16">
        <div className="grid grid-cols-2 gap-5 mb-16">
          {PLANS.map((plan) => (
            <div key={plan.key}
              className={cn("border-[1.5px] rounded-2xl p-9 transition-all",
                plan.featured
                  ? "border-[var(--teal)] shadow-[0_0_0_4px_rgba(13,124,110,0.07)]"
                  : "border-[var(--border)] bg-white")}>
              <div className={cn("inline-block font-mono text-[11px] px-2.5 py-1 rounded mb-4",
                plan.featured ? "bg-[var(--teal-bg)] text-[var(--teal)]" : "bg-[var(--cream2)] text-[var(--muted)]")}>
                {plan.badge}
              </div>
              <h2 className="text-[22px] font-bold mb-1">{plan.name}</h2>
              <p className="text-[13px] text-[var(--muted)] mb-5">{plan.desc}</p>
              <div className="text-[48px] font-black tracking-[-1px] leading-none mb-1">
                {plan.price}<span className="text-[16px] font-normal text-[var(--muted)]">{plan.unit}</span>
              </div>
              <ul className="my-6 flex flex-col gap-3">
                {plan.features.map((f, i) => (
                  <li key={i} className={cn("flex items-center gap-2.5 text-[14px]", !f.yes && "text-[var(--muted2)]")}>
                    <span className={cn("w-4 h-4 rounded-full flex-shrink-0 border-[3px]",
                      f.yes ? "border-[var(--green)] bg-[var(--green-bg)]" : "border-[var(--border2)] bg-[var(--cream2)]")} />
                    {f.text}
                  </li>
                ))}
              </ul>
              {plan.key === "pro" ? (
                <ProCheckoutButton full variant="teal">
                  {plan.cta}
                </ProCheckoutButton>
              ) : (
                <Link href={plan.ctaHref ?? "/auth"}>
                  <Button variant={plan.featured ? "teal" : "outline"} full>
                    {plan.cta}
                  </Button>
                </Link>
              )}
              <p className="text-center text-[12px] text-[var(--muted2)] mt-2.5">{plan.aiNote}</p>
            </div>
          ))}
        </div>

        {/* Trust */}
        <div className="text-center font-mono text-[12px] text-[var(--muted)] mb-16">
          // クレジットカード不要 · いつでもキャンセル可 · 14日間無料トライアル
        </div>

        {/* FAQ */}
        <div>
          <h2 className="text-[22px] font-bold mb-6">よくある質問</h2>
          <div className="flex flex-col gap-3">
            {FAQS.map((f, i) => (
              <div key={i} className="bg-white border border-[var(--border)] rounded-xl px-6 py-5">
                <div className="font-semibold text-[14px] mb-2">{f.q}</div>
                <div className="text-[13px] text-[var(--muted)] leading-[1.7]">{f.a}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
