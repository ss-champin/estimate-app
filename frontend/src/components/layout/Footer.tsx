import Link from "next/link"

export function Footer() {
  return (
    <footer className="border-t border-[var(--border)] py-4 px-6 flex justify-center gap-6">
      <Link href="/terms" className="text-[12px] text-[var(--muted)] hover:text-[var(--ink)] transition-colors">
        利用規約
      </Link>
      <Link href="/privacy" className="text-[12px] text-[var(--muted)] hover:text-[var(--ink)] transition-colors">
        プライバシーポリシー
      </Link>
      <a
        href="https://libernate.app/tokushoho/"
        target="_blank"
        rel="noopener noreferrer"
        className="text-[12px] text-[var(--muted)] hover:text-[var(--ink)] transition-colors"
      >
        特定商取引法に基づく表記
      </a>
    </footer>
  )
}
