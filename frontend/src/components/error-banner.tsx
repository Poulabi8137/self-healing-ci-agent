import { AlertCircle } from 'lucide-react'
import { useState } from 'react'

export function ErrorBanner({
  message,
  requestId,
  onRetry,
}: {
  message: string
  requestId?: string
  onRetry?: () => void
}) {
  const [showDetails, setShowDetails] = useState(false)

  return (
    <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-4">
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-500" />
        <div className="flex-1">
          <p className="text-sm font-medium text-red-500">{message}</p>
          {requestId && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="mt-1 text-xs text-red-400/70 hover:text-red-400"
            >
              {showDetails ? 'Hide details' : 'Show details'}
            </button>
          )}
          {requestId && showDetails && (
            <code className="mt-1 block text-xs text-red-400/50">req_{requestId}</code>
          )}
        </div>
        {onRetry && (
          <button
            onClick={onRetry}
            className="shrink-0 rounded-lg border border-red-500/30 px-4 py-1.5 text-xs font-medium text-red-500 hover:bg-red-500/10"
          >
            Try Again
          </button>
        )}
      </div>
    </div>
  )
}
