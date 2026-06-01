import { motion } from 'framer-motion'
import { useRef, useState, useEffect } from 'react'
import { cn } from '@/lib/utils'

export function TabNav({
  tabs,
  activeTab,
  onChange,
}: {
  tabs: string[]
  activeTab: string
  onChange: (tab: string) => void
}) {
  const [indicatorStyle, setIndicatorStyle] = useState({ left: 0, width: 0 })
  const refs = useRef<(HTMLButtonElement | null)[]>([])

  useEffect(() => {
    const idx = tabs.indexOf(activeTab)
    const el = refs.current[idx]
    if (el) {
      setIndicatorStyle({ left: el.offsetLeft, width: el.offsetWidth })
    }
  }, [activeTab, tabs])

  return (
    <div className="relative flex gap-1 border-b border-border">
      {tabs.map((tab, i) => (
        <button
          key={tab}
          ref={(el) => { refs.current[i] = el }}
          onClick={() => onChange(tab)}
          className={cn(
            'relative px-4 py-2.5 text-sm font-medium transition-colors',
            activeTab === tab
              ? 'text-foreground'
              : 'text-muted-foreground hover:text-foreground',
          )}
        >
          {tab}
        </button>
      ))}
      <motion.div
        layoutId="tab-indicator"
        className="absolute bottom-0 h-0.5 bg-foreground"
        style={{ left: indicatorStyle.left, width: indicatorStyle.width }}
        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
      />
    </div>
  )
}
