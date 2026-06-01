import { useNavigate } from 'react-router-dom'
import { motion, useScroll, useTransform } from 'framer-motion'
import { useRef } from 'react'
import { useAuth } from '@/lib/auth'
import { springBouncy, springSnappy, stagger, easeOut } from '@/lib/motion'

const containerVariants = {
  hidden: {},
  visible: {
    transition: { staggerChildren: stagger.slow },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: easeOut },
  },
}

export default function Landing() {
  const navigate = useNavigate()
  const { isDark, toggleDark } = useAuth()
  const heroRef = useRef<HTMLDivElement>(null)
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ['start start', 'end start'],
  })
  const heroY = useTransform(scrollYProgress, [0, 1], [0, 150])
  const heroOpacity = useTransform(scrollYProgress, [0, 0.8], [1, 0])

  return (
    <div className="min-h-screen bg-background text-foreground">
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.4, ease: easeOut }}
        className="fixed top-0 z-50 flex h-16 w-full items-center justify-between border-b border-border bg-background/80 px-6 backdrop-blur-sm"
      >
        <div className="flex items-center gap-3">
          <motion.div
            initial={{ rotate: -10, scale: 0 }}
            animate={{ rotate: 0, scale: 1 }}
            transition={{ type: 'spring', stiffness: 400, damping: 20 }}
            className="h-7 w-7 rounded bg-primary"
          />
          <span className="text-sm font-semibold">CI/CD Agent</span>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={toggleDark}
            className="rounded-md px-3 py-1.5 text-sm text-muted-foreground hover:bg-accent"
          >
            {isDark ? 'Light' : 'Dark'}
          </button>
          <motion.button
            onClick={() => navigate('/login')}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="rounded-md bg-primary px-4 py-1.5 text-sm font-medium text-primary-foreground hover:opacity-90"
          >
            Sign In
          </motion.button>
        </div>
      </motion.header>

      <section ref={heroRef} className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden px-6 pt-16 text-center">
        <motion.div
          style={{ y: heroY, opacity: heroOpacity }}
          className="mx-auto max-w-3xl"
        >
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1, duration: 0.4 }}
            className="mb-6 inline-flex items-center gap-2 rounded-full border border-border px-4 py-1.5 text-xs text-muted-foreground"
          >
            <motion.span
              animate={{ scale: [1, 1.3, 1] }}
              transition={{ repeat: Infinity, duration: 2 }}
              className="h-1.5 w-1.5 rounded-full bg-emerald-500"
            />
            Self-Healing CI/CD Agent v0.1.0
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="text-5xl font-bold tracking-tight sm:text-6xl"
          >
            Autonomous CI/CD{' '}
            <span className="text-muted-foreground">Failure Resolution</span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 0.5 }}
            className="mt-6 text-lg leading-relaxed text-muted-foreground"
          >
            An intelligent agent that analyzes build failures, generates fixes,
            validates patches, and creates pull requests — automatically.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4, duration: 0.5 }}
            className="mt-10 flex items-center justify-center gap-4"
          >
            <motion.button
              onClick={() => navigate('/login')}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              transition={springSnappy}
              className="rounded-lg bg-primary px-6 py-2.5 text-sm font-medium text-primary-foreground shadow-sm hover:opacity-90"
            >
              Get Started
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              transition={springSnappy}
              onClick={() => window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })}
              className="rounded-lg border border-border px-6 py-2.5 text-sm font-medium text-foreground hover:bg-accent"
            >
              Learn More
            </motion.button>
          </motion.div>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="mt-20 grid w-full max-w-5xl gap-6 sm:grid-cols-3"
        >
          {[
            { title: 'Analyze', desc: 'Deep analysis with RAG-grounded context retrieval' },
            { title: 'Fix', desc: 'AI-powered fix generation with multi-agent review' },
            { title: 'Deploy', desc: 'Automated PR creation with validation pipeline' },
          ].map((item) => (
            <motion.div
              key={item.title}
              variants={itemVariants}
              whileHover={{ y: -4, transition: springBouncy }}
              className="rounded-xl border border-border bg-card p-6 text-left"
            >
              <motion.div
                whileHover={{ rotate: 5 }}
                className="mb-3 h-8 w-8 rounded-lg bg-accent"
              />
              <h3 className="mb-1 font-semibold">{item.title}</h3>
              <p className="text-sm text-muted-foreground">{item.desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      <motion.footer
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        className="border-t border-border px-6 py-8 text-center text-sm text-muted-foreground"
      >
        Self-Healing AI CI/CD Agent &mdash; Built with FastAPI, React &amp; Groq
      </motion.footer>
    </div>
  )
}
