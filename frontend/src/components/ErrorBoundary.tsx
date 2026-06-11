import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('ErrorBoundary caught:', error, info)
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div className="min-h-screen bg-[#06060e] dot-bg flex items-center justify-center">
          <div className="glass-card max-w-md mx-4 text-center">
            <span className="text-3xl mb-3 block">&#x26A0;</span>
            <h2 className="text-lg font-heading font-bold text-gray-200 mb-2">
              Something went wrong
            </h2>
            <p className="text-sm text-gray-400 mb-4 font-mono break-words">
              {this.state.error?.message || 'Unexpected error'}
            </p>
            <button
              onClick={() => window.location.reload()}
              className="btn-primary text-sm"
            >
              Reload page
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
