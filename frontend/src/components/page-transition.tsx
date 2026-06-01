import { motion } from 'framer-motion'
import type { ReactNode } from 'react'
import { pageVariants, safeTransition, duration } from '@/lib/motion'

export function PageTransition({ children }: { children: ReactNode }) {
  return (
    <motion.div
      variants={pageVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      transition={safeTransition({ duration: duration.slow, ease: [0.16, 1, 0.3, 1] })}
    >
      {children}
    </motion.div>
  )
}
