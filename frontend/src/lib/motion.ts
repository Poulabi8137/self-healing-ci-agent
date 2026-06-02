export const duration = {
  fast: 0.15,
  normal: 0.25,
  slow: 0.35,
  reveal: 0.5,
}

export const ease = [0.25, 0.1, 0.25, 1] as const
export const easeOut = [0.16, 1, 0.3, 1] as const
export const easeIn = [0.4, 0, 1, 1] as const

export const spring = {
  type: 'spring' as const,
  stiffness: 300,
  damping: 30,
}

export const springSnappy = {
  type: 'spring' as const,
  stiffness: 500,
  damping: 35,
}

export const springBouncy = {
  type: 'spring' as const,
  stiffness: 400,
  damping: 20,
}

export const stagger = {
  fast: 0.03,
  normal: 0.05,
  slow: 0.08,
}

export const prefersReducedMotion =
  typeof window !== 'undefined'
    ? window.matchMedia('(prefers-reduced-motion: reduce)').matches
    : false

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const safeTransition = (t: Record<string, any>) =>
  prefersReducedMotion ? { duration: 0 } : t

export const pageVariants = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, scale: 0.98 },
}

export const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: stagger.normal },
  },
}

export const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: easeOut },
  },
}

export const tabContentVariants = {
  initial: { opacity: 0, x: 8 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -8 },
}
