import { useEffect, useState } from 'react'
import { animate, easeOut } from 'framer-motion'

export function AnimatedCounter({
  value,
  decimals = 0,
  prefix = '',
  suffix = '',
}: {
  value: number
  decimals?: number
  prefix?: string
  suffix?: string
}) {
  const [display, setDisplay] = useState(0)

  useEffect(() => {
    const controls = animate(0, value, {
      duration: 0.6,
      ease: easeOut,
      onUpdate: (v) => setDisplay(v),
    })
    return controls.stop
  }, [value])

  return (
    <span>
      {prefix}
      {display.toFixed(decimals)}
      {suffix}
    </span>
  )
}
