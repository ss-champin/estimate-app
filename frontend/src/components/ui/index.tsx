"use client"
import { cn } from "@/lib/utils"
import type { ButtonHTMLAttributes, InputHTMLAttributes, TextareaHTMLAttributes, HTMLAttributes } from "react"

interface BtnProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "ink"|"teal"|"outline"|"ghost"; size?: "xs"|"sm"|"md"; full?: boolean
}
export function Button({ variant="ink", size="md", full, className, children, ...p }: BtnProps) {
  const base = "inline-flex items-center gap-1.5 font-medium rounded-lg transition-all cursor-pointer select-none disabled:opacity-50 disabled:pointer-events-none"
  const v = {
    ink:     "bg-[var(--ink)] text-white hover:bg-[var(--ink2)] hover:-translate-y-px shadow-sm",
    teal:    "bg-[var(--teal)] text-white hover:bg-[var(--teal-m)] hover:-translate-y-px hover:shadow-[0_4px_16px_rgba(13,124,110,0.3)]",
    outline: "bg-transparent border-[1.5px] border-[var(--border2)] text-[var(--ink)] hover:border-[var(--ink)] hover:bg-white",
    ghost:   "bg-transparent text-[var(--muted)] hover:bg-[var(--cream2)] hover:text-[var(--ink)]",
  }
  const s = { xs:"px-2.5 py-1 text-xs", sm:"px-3.5 py-1.5 text-[13px]", md:"px-5 py-2.5 text-sm" }
  return <button className={cn(base, v[variant], s[size], full && "w-full justify-center py-3.5 text-[15px] rounded-xl", className)} {...p}>{children}</button>
}

interface InputProps extends InputHTMLAttributes<HTMLInputElement> { mono?: boolean }
export function Input({ mono, className, ...p }: InputProps) {
  return <input className={cn("w-full px-3.5 py-2.5 border-[1.5px] border-[var(--border)] rounded-lg bg-white text-sm text-[var(--ink)] outline-none transition-all placeholder:text-[var(--muted2)] focus:border-[var(--teal)] focus:shadow-[0_0_0_3px_rgba(13,124,110,0.1)]", mono && "font-mono text-[13px]", className)} {...p}/>
}

export function Textarea({ className, ...p }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn("w-full px-3.5 py-2.5 border-[1.5px] border-[var(--border)] rounded-lg bg-white text-sm text-[var(--ink)] outline-none transition-all placeholder:text-[var(--muted2)] resize-y min-h-[120px] leading-relaxed focus:border-[var(--teal)] focus:shadow-[0_0_0_3px_rgba(13,124,110,0.1)]", className)} {...p}/>
}

export function Card({ className, children, ...p }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("bg-white border border-[var(--border)] rounded-2xl overflow-hidden", className)} {...p}>{children}</div>
}
export function CardHeader({ className, children, ...p }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("px-5 py-4 border-b border-[var(--border)] flex items-center justify-between", className)} {...p}>{children}</div>
}
export function CardBody({ className, children, ...p }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-5", className)} {...p}>{children}</div>
}

type BadgeVariant = "teal"|"amber"|"red"|"gray"|"green"
export function Badge({ variant="gray", className, children }: { variant?: BadgeVariant; className?: string; children: React.ReactNode }) {
  const v: Record<BadgeVariant,string> = { teal:"bg-[var(--teal-bg)] text-[var(--teal)]", amber:"bg-[var(--amber-bg)] text-[var(--amber)]", red:"bg-[var(--red-bg)] text-[var(--red)]", green:"bg-[var(--green-bg)] text-[var(--green)]", gray:"bg-[var(--cream2)] text-[var(--muted)]" }
  return <span className={cn("inline-block font-mono text-[11px] px-2 py-0.5 rounded", v[variant], className)}>{children}</span>
}

export function MonoLabel({ children, className }: { children: React.ReactNode; className?: string }) {
  return <div className={cn("font-mono text-[10px] text-[var(--muted)] uppercase tracking-wider mb-2", className)}>{children}</div>
}
