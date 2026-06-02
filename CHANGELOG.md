# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Multi-language validation support (JavaScript, Go, Rust, Java)
- Webhook-based CI integration (GitHub Actions, GitLab CI, Jenkins)
- Slack/Teams notification channels
- PostgreSQL production database support
- Kubernetes Helm chart deployment manifests

---

## [1.0.0] — 2026-06-02

### Added

#### Frontend: React SPA (11 pages)
- React 19 + TypeScript 6 + Vite 8 + Tailwind CSS v4 production build
- 9 code-split lazy routes (440 KB main chunk, parallel-loadable)
- Framer Motion animations: spring transitions, stagger grids, AnimatePresence page transitions
- Recharts visualizations: radar, area, bar, line, pie/donut, scatter, treemap charts
- Animated SVG ring meters with stroke-dasharray animation
- Animated counters with spring physics
- SpotlightCard and TiltCard interactive components
- Command palette (Ctrl+K) with keyboard-driven navigation
- WCAG AA accessibility: 60+ ARIA attributes, focus traps, keyboard shortcuts (G+letter navigation)
- Error boundaries with toast notifications (sonner)
- Real-time API polling (10s tasks, 30s dashboard) via TanStack React Query

#### Pages
- **Landing** — Parallax hero, feature cards with stagger-in animation, animated CTA
- **Login** — API key authentication with auto-redirect and form validation
- **Dashboard** — 6-tab navigation, 4 metric cards, success/failure bar chart, activity trend area chart, activity feed sidebar, skeleton loaders
- **Analysis** — Form + results split pane, code block display, assumptions list, error classification
- **Validation** — 3 validation category cards (syntax, build, test) with overall status
- **Retry** — Interactive expandable timeline, donut chart, failure reason breakdown, metric cards
- **Review** — Radar chart, animated ring meter (92%), score distribution bar chart, multi-line trend chart, recent reviews list
- **Pull Request** — Form with dry-run toggle, file changes list (A/M/D indicators), branch details
- **Indexing** — Repository indexing form, 4-card metric strip, recent indexes list
- **Tasks** — Real task polling (10s), expandable task cards, animated progress bars, metric cards
- **Admin Keys** — Full CRUD (create/delete), role assignment dropdown, copy-to-clipboard, role-colored icons

#### Backend Enhancements
- Groq LLM provider support (deepseek-r1-distill-llama-70b)
- Additional LLM provider abstraction layer
- Enhanced error classification categories

#### Testing
- 60 frontend tests (Vitest + React Testing Library + @testing-library/user-event)
- 15 frontend test files covering all 11 pages, shared components, hooks, auth
- Accessibility tests for ARIA attributes and keyboard navigation

#### Documentation & Repository
- Full ARCHITECTURE.md with Mermaid component tree, frontend/backend diagrams, request flow
- GitHub issue templates (bug report, feature request)
- GitHub pull request template
- SECURITY.md with vulnerability reporting policy
- CODE_OF_CONDUCT.md (Contributor Covenant v2.1)
- .gitattributes for cross-platform line endings
- README hero screenshot, badges, feature grid, quick start, demo section

### Security

- SessionStorage for auth tokens (no localStorage)
- Role icons and visual role indicators on admin keys page
- Form validation on all user inputs

### Performance

- Code-split routing: 9 lazy-loaded chunks loaded on demand
- React Query stale-while-revalidate with 30s staleTime
- Parallel data fetching on dashboard (Promise.all for 4 chart endpoints)
- Optimized bundle with vite build (tree-shaking, minification, CSS extraction)

---

## [0.1.0] — 2026-06-01

### Added

#### Core AI Pipeline
- Repository-aware RAG indexing with FAISS vector embeddings and Sentence Transformers
- AI-driven root cause analysis via Debug Agent with error classification (syntax, dependency, test, runtime, build)
- LangChain-powered fix generation with structured unified diff patches
- Multi-stage validation pipeline: Python AST syntax checks → project structure validation → pytest execution
- Autonomous retry loop with escalating fix strategies (3 attempts default)
- Multi-agent review system with 4 specialized reviewers (Security, Performance, Quality, Coverage)
- Pull request automation: branch creation, commit generation, and PR creation with dry-run safety mode

#### API & Backend
- RESTful API with 20 endpoints across 8 route modules
- Interactive Swagger/OpenAPI documentation at `/docs`
- API key authentication with SHA-256 key hashing and role-based access control (candidate, recruiter, admin)
- Background task queue with persistent SQLite storage and retry logic
- Sliding-window rate limiter with per-endpoint configurable limits (5–30 req/min)
- Request body size limits enforced via Pydantic Field validators
- CORS middleware with environment-based origin configuration

#### Deployment & Infrastructure
- Multi-stage Dockerfile (python:3.12-slim, 264 MB final image)
- Docker Compose with Caddy reverse proxy, HTTPS-ready configuration, and secure headers
- gunicorn + uvicorn workers with configurable worker count via `WORKERS` env var
- GitHub Actions CI pipeline (lint + test on every push)
- `.dockerignore` for optimized builds
- Health check endpoint with database initialization verification

#### Security & Reliability
- Circuit breaker pattern for DeepSeek and GitHub API clients (configurable threshold, recovery timeout, half-open max requests)
- Exponential backoff with jitter for all retry operations
- Startup validation of required secrets (DeepSeek API key, GitHub token)
- Global exception handler with sanitized 500 responses and request ID tracking
- Structured JSON logging with Loguru (rotation, compression, retention)
- Request ID propagation through middleware with `X-Request-ID` response header
- Bootstrap admin key initialization via environment variable

#### Frontend
- Streamlit dashboard with live benchmark metrics across 6 dimensions
- System overview, repository analytics, retry analytics, validation analytics, review analytics, PR analytics

#### Documentation
- README with problem statement, solution, architecture, installation, API overview, testing, benchmark dashboard
- Architecture documentation with detailed component diagrams and data flow
- API reference with complete request/response JSON examples
- Workflows documentation with Mermaid flowcharts
- Production readiness audit across 9 dimensions
- Performance audit with bottleneck analysis and optimization recommendations
- Blocker resolution documentation (auth, task queue, database migrations)
- SVG architecture and workflow diagrams

#### Testing
- 256 passing tests (pytest + pytest-asyncio)
- Test coverage: auth (31 tests), hardening (9 tests), circuit breaker (10 tests), retry utils (9 tests), all 6 workflows, 8 agents, 9 API routers, 5 dashboard modules, all validators, all prompts, all GitHub integrations

### Security

- API key authentication with `secrets.token_urlsafe(32)` generation and SHA-256 hashing
- Role-based access control enforced on all 6 workflow routers
- Rate limiting on all POST, auth, AI-heavy, and task endpoints
- Request body limits on all string fields (repository names, logs, key names)
- Sanitized error responses — no internal details leaked to clients
- Circuit breaker prevents cascading failures from external API outages
- CORS restricted to configured origins in production mode
- Startup validation of critical secrets
- Secure HTTP headers via Caddy reverse proxy (X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Permissions-Policy)

### Performance

- `asyncio.to_thread()` for non-blocking database lookups in auth dependency
- Exponential backoff with jitter for retry operations
- Configurable worker count for horizontal scaling
- Connection pooling support for PostgreSQL migration path
- FAISS vector search for sub-millisecond RAG context retrieval

### Fixed

- Logger sink destruction bug — `get_logger()` no longer removes sinks on every call
- Middleware registration order — middleware defined after `app = FastAPI()`
- CORS configuration — `allow_credentials` set to `False` for wildcard origin
- Global exception handler — returns JSON instead of HTML tracebacks
- Dashboard router error handling — all 8 endpoints wrapped in try/except
- `CHUNK_SIZE`/`CHUNK_OVERLAP` defaults aligned between code and documentation
- Bootstrap admin key generation — uses configured key value instead of random
- Auth dependency blocking — `get_current_user()` and `optional_user()` wrapped with `asyncio.to_thread()`


