"use client"
import { Component, type ReactNode } from "react"
import { Button } from "@/components/ui"

interface Props { children: ReactNode }
interface State { hasError: boolean; message: string }

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: "" }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="max-w-[560px] mx-auto px-6 py-20 text-center">
          <div className="text-4xl mb-4">⚠️</div>
          <h2 className="text-[18px] font-bold mb-2">エラーが発生しました</h2>
          <p className="text-[13px] text-[var(--muted)] mb-6">{this.state.message}</p>
          <Button variant="teal" onClick={() => this.setState({ hasError: false, message: "" })}>
            再試行
          </Button>
        </div>
      )
    }
    return this.props.children
  }
}
