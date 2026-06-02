import { useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useAuth, LoginForm } from '../lib/auth'
import { AnimatedBackground } from '@/components/AnimatedBackground'
import { SelfHealingDemo } from '@/components/SelfHealingDemo'
import { containerCinematic, itemVariants } from '@/lib/motion'

function LoginContent() {
  return (
    <div className="w-full max-w-sm">
      <motion.div variants={itemVariants} className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-blue-500 to-violet-600 shadow-lg shadow-blue-500/15">
          <svg className="h-5 w-5 text-white" viewBox="0 0 24 24" fill="currentColor"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>
        </div>
        <h1 className="text-lg font-semibold tracking-tight text-zinc-100">
          Self-Healing CI Agent
        </h1>
        <p className="mt-1 text-sm text-zinc-500">
          Sign in with your API key to continue.
        </p>
      </motion.div>
      <motion.div variants={itemVariants} className="rounded-xl border border-[#1f1f23] bg-[#121216]/80 p-6 backdrop-blur-xl">
        <LoginForm />
      </motion.div>
    </div>
  )
}

function ProductContent() {
  return (
    <div className="mx-auto max-w-xl">
      <motion.div variants={itemVariants}>
        <div className="mb-5 inline-flex items-center gap-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/8 px-3 py-1">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          <span className="text-[11px] font-medium text-emerald-400/80 tracking-wider uppercase">CI/CD Agent</span>
        </div>
        <h2 className="text-3xl font-semibold tracking-tight text-zinc-100 leading-[1.12]">
          CI failures resolved<br />
          <span className="text-zinc-500">before you notice them.</span>
        </h2>
        <p className="mt-4 text-sm leading-relaxed text-zinc-400 max-w-lg">
          Your CI pipeline failed. The agent detected the issue, analyzed the logs,
          generated a fix, and created a pull request &mdash; in seconds.
        </p>
      </motion.div>

      <motion.div variants={itemVariants} className="mt-16">
        <div className="mb-4 flex items-center gap-2">
          <span className="text-[11px] font-medium text-zinc-600 tracking-wider uppercase">Watch the agent in action</span>
          <div className="h-px flex-1 bg-[#1f1f23]" />
        </div>
        <div className="rounded-xl border border-[#1f1f23] bg-[#121216]/40 p-5">
          <SelfHealingDemo autoPlay />
        </div>
      </motion.div>
    </div>
  )
}

export default function LoginPage() {
  const { isAuthenticated } = useAuth()

  useEffect(() => {
    if (!document.documentElement.classList.contains('dark')) {
      document.documentElement.classList.add('dark')
    }
  }, [])

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return (
    <main className="relative flex min-h-screen flex-col bg-[#070708] lg:flex-row overflow-hidden">
      <AnimatedBackground variant="login" />
      <div className="pointer-events-none fixed inset-0 opacity-[0.02]"
        style={{
          backgroundImage: `linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)`,
          backgroundSize: '48px 48px',
        }}
      />
      <section className="order-last flex-1 px-6 py-16 lg:order-first lg:px-16 lg:py-24 relative z-10">
        <motion.div
          variants={containerCinematic}
          initial="hidden"
          animate="visible"
        >
          <ProductContent />
        </motion.div>
      </section>
      <aside className="order-first flex w-full items-center justify-center border-[#1f1f23] bg-[#0a0a0c]/60 px-6 py-16 lg:order-last lg:w-[480px] lg:min-h-screen lg:border-l lg:py-0 backdrop-blur-sm relative z-10">
        <motion.div
          variants={containerCinematic}
          initial="hidden"
          animate="visible"
        >
          <LoginContent />
        </motion.div>
      </aside>
    </main>
  )
}
