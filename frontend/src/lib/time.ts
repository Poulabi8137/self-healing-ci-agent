export function timeAgo(date: Date | string): string {
  const now = Date.now()
  const past = typeof date === 'string' ? new Date(date).getTime() : date.getTime()
  const diffMs = now - past
  const diffSec = Math.floor(diffMs / 1000)

  if (diffSec < 10) return 'just now'
  if (diffSec < 60) return `${diffSec}s ago`
  const diffMin = Math.floor(diffSec / 60)
  if (diffMin < 60) return `${diffMin}m ago`
  const diffHr = Math.floor(diffMin / 60)
  if (diffHr < 24) return `${diffHr}h ago`
  const diffDay = Math.floor(diffHr / 24)
  if (diffDay < 7) return `${diffDay}d ago`
  return new Date(past).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
