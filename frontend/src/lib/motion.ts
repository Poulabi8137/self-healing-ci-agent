export const duration = {
  fast: 0.15,
  normal: 0.25,
  slow: 0.35,
  reveal: 0.5,
}

export const ease = [0.25, 0.1, 0.25, 1] as const
export const easeOut = [0.16, 1, 0.3, 1] as const
export const easeIn = [0.4, 0, 1, 1] as const
export const cinematic = [0.22, 1, 0.36, 1] as const

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

export const springGentle = {
  type: 'spring' as const,
  stiffness: 200,
  damping: 25,
}

export const stagger = {
  fast: 0.03,
  normal: 0.05,
  slow: 0.08,
  cinematic: 0.12,
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

export const pageTransition = {
  type: 'tween' as const,
  duration: 0.4,
  ease: cinematic,
}

export const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: stagger.normal },
  },
}

export const containerCinematic = {
  hidden: {},
  visible: {
    transition: { staggerChildren: stagger.cinematic },
  },
}

export const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: cinematic },
  },
}

export const itemFadeLeft = {
  hidden: { opacity: 0, x: -20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.4, ease: cinematic },
  },
}

export const itemFadeRight = {
  hidden: { opacity: 0, x: 20 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.4, ease: cinematic },
  },
}

export const itemScale = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.4, ease: cinematic },
  },
}

export const tabContentVariants = {
  initial: { opacity: 0, x: 8 },
  animate: { opacity: 1, x: 0 },
  exit: { opacity: 0, x: -8 },
}

export const pipelineNodeVariant = (i: number) => ({
  hidden: { opacity: 0, y: 16, scale: 0.9 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: { duration: 0.5, delay: i * 0.1, ease: cinematic },
  },
})

export const glassCardVariants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: cinematic },
  },
  hover: {
    y: -2,
    transition: { duration: 0.2, ease: cinematic },
  },
}

export const glowVariants = {
  initial: { opacity: 0, scale: 0.8 },
  animate: {
    opacity: [0.4, 0.6, 0.4],
    scale: [1, 1.05, 1],
    transition: {
      duration: 4,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
}

export const successSequence = {
  hidden: { pathLength: 0, opacity: 0 },
  visible: {
    pathLength: 1,
    opacity: 1,
    transition: { duration: 0.6, ease: cinematic },
  },
}
