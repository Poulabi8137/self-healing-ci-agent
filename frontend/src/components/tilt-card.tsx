import { useMotionValue, useSpring, useTransform, motion } from 'framer-motion'
import { useRef, useState, useEffect, type ReactNode } from 'react'

export function TiltCard({ children, className = '' }: { children: ReactNode; className?: string }) {
  const ref = useRef<HTMLDivElement>(null)
  const [canTilt, setCanTilt] = useState(false)
  const x = useMotionValue(0.5)
  const y = useMotionValue(0.5)
  const rotateX = useSpring(useTransform(y, [0, 1], [4, -4]), { stiffness: 300, damping: 30 })
  const rotateY = useSpring(useTransform(x, [0, 1], [-4, 4]), { stiffness: 300, damping: 30 })

  useEffect(() => {
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    const desktop = window.matchMedia('(pointer: fine) and (min-width: 768px)').matches
    setCanTilt(desktop && !reduced)
  }, [])

  function handleMouse(e: React.MouseEvent) {
    if (!canTilt || !ref.current) return
    const rect = ref.current.getBoundingClientRect()
    x.set((e.clientX - rect.left) / rect.width)
    y.set((e.clientY - rect.top) / rect.height)
  }

  function handleLeave() {
    if (!canTilt) return
    x.set(0.5)
    y.set(0.5)
  }

  return (
    <motion.div
      ref={ref}
      onMouseMove={handleMouse}
      onMouseLeave={handleLeave}
      style={{ perspective: 1000, rotateX, rotateY }}
      className={className}
    >
      {children}
    </motion.div>
  )
}
