# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Multi-language validation support (JavaScript, Go, Rust, Java) — *planned*
- Webhook-based CI integration (GitHub Actions, GitLab CI, Jenkins) — *planned*
- Slack/Teams notification channels — *planned*
- PostgreSQL production database support — *planned*
- Kubernetes Helm chart deployment manifests — *planned*

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


