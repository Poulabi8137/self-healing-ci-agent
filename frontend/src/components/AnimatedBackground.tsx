import { motion } from 'framer-motion'

interface AnimatedBackgroundProps {
  variant?: 'login' | 'dashboard' | 'minimal'
}

export function AnimatedBackground({ variant = 'minimal' }: AnimatedBackgroundProps) {
  if (variant === 'minimal') {
    return (
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 h-[500px] w-[500px] rounded-full bg-blue-500/3 blur-[150px]" />
        <div className="absolute -bottom-40 -right-40 h-[400px] w-[400px] rounded-full bg-violet-500/3 blur-[150px]" />
      </div>
    )
  }

  if (variant === 'login') {
    return (
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <motion.div
          animate={{ opacity: [0.3, 0.5, 0.3], scale: [1, 1.05, 1] }}
          transition={{ duration: 8, repeat: Infinity, ease: 'easeInOut' }}
          className="absolute -top-60 -left-60 h-[600px] w-[600px] rounded-full bg-blue-500/8 blur-[200px]"
        />
        <motion.div
          animate={{ opacity: [0.2, 0.4, 0.2], scale: [1.05, 1, 1.05] }}
          transition={{ duration: 10, repeat: Infinity, ease: 'easeInOut', delay: 1 }}
          className="absolute -bottom-40 -right-40 h-[500px] w-[500px] rounded-full bg-violet-500/8 blur-[200px]"
        />
        <motion.div
          animate={{ opacity: [0.1, 0.25, 0.1] }}
          transition={{ duration: 6, repeat: Infinity, ease: 'easeInOut', delay: 2 }}
          className="absolute top-1/4 left-1/2 h-[300px] w-[300px] -translate-x-1/2 rounded-full bg-indigo-500/5 blur-[150px]"
        />
      </div>
    )
  }

  if (variant === 'dashboard') {
    return (
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/4 h-[400px] w-[400px] rounded-full bg-blue-500/3 blur-[120px]" />
        <div className="absolute top-1/3 -right-20 h-[300px] w-[300px] rounded-full bg-violet-500/3 blur-[120px]" />
        <div className="absolute -bottom-20 left-1/3 h-[250px] w-[250px] rounded-full bg-emerald-500/3 blur-[120px]" />
      </div>
    )
  }

  return null
}
