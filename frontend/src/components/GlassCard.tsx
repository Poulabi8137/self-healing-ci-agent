import { motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { glassCardVariants } from '@/lib/motion'

interface GlassCardProps {
  children: ReactNode
  className?: string
  hover?: boolean
  glow?: 'blue' | 'emerald' | 'violet' | 'none'
}

export function GlassCard({ children, className = '', hover = true, glow = 'none' }: GlassCardProps) {
  const glowColors: Record<string, string> = {
    blue: 'before:bg-blue-500/5',
    emerald: 'before:bg-emerald-500/5',
    violet: 'before:bg-violet-500/5',
    none: '',
  }

  return (
    <motion.div
      variants={glassCardVariants}
      initial="hidden"
      animate="visible"
      whileHover={hover ? 'hover' : undefined}
      className={`relative overflow-hidden rounded-xl border border-[#1f1f23] bg-[#121216]/80 backdrop-blur-xl ${glowColors[glow]} ${className}`}
    >
      {glow !== 'none' && (
        <div className={`pointer-events-none absolute -inset-px rounded-xl opacity-0 transition-opacity duration-500 group-hover:opacity-100 ${glow === 'blue' ? 'shadow-[inset_0_0_20px_rgba(59,130,246,0.05)]' : ''} ${glow === 'emerald' ? 'shadow-[inset_0_0_20px_rgba(16,185,129,0.05)]' : ''} ${glow === 'violet' ? 'shadow-[inset_0_0_20px_rgba(139,92,246,0.05)]' : ''}`} />
      )}
      {children}
    </motion.div>
  )
}
