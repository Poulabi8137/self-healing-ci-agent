# Target Vision Gap Audit

> Based on: Project Understanding Report
> Objective: Identify the shortest path from current state to production-grade Self-Healing CI/CD Agent
> Constraint: Maximize reuse — do not rewrite what already works

---

## 1. Reuse vs Rebuild Matrix

### Authentication

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| API key auth (machine-to-machine) | SHA-256 hashed, RBAC, `ApiKey` table, 3 auth endpoints | **REUSE AS-IS** | Correct architecture for CI pipeline tokens; keep for machine auth |
| Frontend auth context | `auth-context.ts` with `login/logout/isAuthenticated` | **REUSE WITH MODIFICATIONS** | Keep the interface; swap API-key login for OAuth under the hood |
| Frontend login page | `login.tsx` with API key form + demo content | **REBUILD** | Replace form with OAuth buttons; remove all demo content |

**New code needed:**
- OAuth client integration (`authlib`)
- `User`, `Organization`, `Session` tables
- OAuth callback endpoints (`/auth/google`, `/auth/github/callback`)
- JWT session management
- Frontend OAuth flow (no more `sessionStorage` key storage)

### GitHub Integration

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| GitHub REST client | `github_client.py` with `get_repo`, `get_workflows`, `create_pr`, etc. | **REUSE AS-IS** | Working HTTP client with circuit breaker and auth |
| Branch management | `branch_manager.py` | **REUSE AS-IS** | Working branch generation and creation |
| Commit management | `commit_manager.py` | **REUSE AS-IS** | Working commit creation |
| Patch applier | `patch_applier.py` | **REUSE AS-IS** | Working diff simulation |
| PR generator | `pr_generator.py` (LLM-powered) | **REUSE AS-IS** | Working PR content generation |
| PR service | `pr_service.py` (orchestration) | **REUSE AS-IS** | Working end-to-end PR flow |

**New code needed:**
- GitHub App OAuth flow (`/auth/github/install`)
- GitHub webhook receiver endpoint (`POST /api/github/webhook`)
- Webhook signature verification
- Webhook event handlers (workflow_run, check_run, push)
- `GitHubInstallation` model for multi-repo management

### RAG System

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| Repo loader | `repo_loader.py` | **REUSE AS-IS** | Working git clone and file extraction |
| Chunking | `chunking.py` (RecursiveCharacterTextSplitter) | **REUSE AS-IS** | Working text splitting |
| Embedding | `embedding.py` (sentence-transformers) | **REUSE AS-IS** | Working embedding service |
| Vector store | FAISS (per-repo indices) | **REUSE AS-IS** | Working vector storage and retrieval |
| Retriever | `retriever.py` | **REUSE AS-IS** | Working semantic search |
| Indexing pipeline | `indexing_pipeline.py` | **REUSE AS-IS** | Working end-to-end indexing |

**Notes:** None needed. RAG is the most production-ready subsystem.

### Analysis Engine

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| Log parser | `parsers/log_parser.py` | **REUSE AS-IS** | Working structured log parsing |
| Error classifier | `parsers/error_classifier.py` | **REUSE AS-IS** | Working error categorization |
| Debug agent | `agents/debug_agent.py` | **REUSE AS-IS** | Working RAG-enhanced analysis |
| Analysis workflow | `workflows/analysis_workflow.py` | **REUSE AS-IS** | Working orchestration |

**Notes:** None. Analysis engine is production-ready. Only missing piece is frontend display.

### Fix Generation

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| Fix agent | `agents/fix_agent.py` | **REUSE AS-IS** | Working LLM-based fix generation |
| Fix generation workflow | `workflows/fix_generation_workflow.py` | **REUSE AS-IS** | Working orchestration |

**Notes:** None. Fix generation is production-ready.

### Validation Engine

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| Syntax validator | `validation/syntax_validator.py` | **REUSE AS-IS** | Working ast.parse validation |
| Build validator | `validation/build_validator.py` | **REUSE AS-IS** | Working build check |
| Test runner | `validation/test_runner.py` | **REUSE AS-IS** | Working pytest subprocess runner |
| Validator orchestrator | `validation/validator_orchestrator.py` | **REUSE AS-IS** | Working multi-stage orchestration |
| Validation service | `validation/validation_service.py` | **REUSE AS-IS** | Working combine + report |

**Notes:** Validation engine is production-ready but limited to 3 stages. Security scan is missing but can be added as a new validator module without changing existing ones.

### Review Engine

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| Security reviewer | `agents/security_reviewer.py` | **REUSE AS-IS** | Working LLM-based review |
| Performance reviewer | `agents/performance_reviewer.py` | **REUSE AS-IS** | Working |
| Quality reviewer | `agents/quality_reviewer.py` | **REUSE AS-IS** | Working |
| Coverage reviewer | `agents/coverage_reviewer.py` | **REUSE AS-IS** | Working |
| Review orchestrator | `agents/review_orchestrator.py` | **REUSE AS-IS** | Working 4-agent parallel review |

**Notes:** None. Review engine is production-ready.

### PR Creation

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| PR service | `github/pr_service.py` | **REUSE AS-IS** | Working end-to-end with dry_run/approved flags |
| PR workflow | `workflows/pr_workflow.py` | **REUSE AS-IS** | Working orchestration |

**Notes:** None. PR creation is production-ready.

### Queue System

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| Task model | `queue/models.py` | **REUSE AS-IS** | Proper SQLAlchemy model with status/attempts/error tracking |
| Worker loop | `queue/worker.py` | **REUSE WITH MODIFICATIONS** | Works but in-process; needs Redis for production |
| Task handlers | `queue/handlers.py` (7 handlers) | **REUSE AS-IS** | Proper registration pattern |

**Modifications needed:**
- Replace in-process asyncio loop with Redis-backed queue (RQ/Celery/arq)
- Add re-queue logic for pending tasks on startup
- Add handler for new webhook-driven tasks

### Database Schema

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| Repository model | `database/models.py` | **REUSE WITH MODIFICATIONS** | Add organization_id, github_installation_id, last_workflow_status |
| Failure model | `database/models.py` | **REUSE AS-IS** | Works for failure storage |
| Fix model | `database/models.py` | **REUSE AS-IS** | Works for fix storage |
| RetryAttempt model | `database/models.py` | **REUSE AS-IS** | Works for validation tracking (misnamed but functional) |
| ReviewResult model | `database/models.py` | **REUSE AS-IS** | Works for review storage |
| PRRecord model | `database/models.py` | **REUSE AS-IS** | Works for PR tracking |
| RepositoryMetrics model | `database/models.py` | **REUSE AS-IS** | Works for per-repo metrics |
| WorkflowMetrics model | `database/models.py` | **REUSE AS-IS** | Works for workflow metrics |
| BenchmarkRun model | `database/models.py` | **KEEP (optional)** | Useful for benchmarking but not critical |
| Metric model | `database/models.py` | **KEEP (optional)** | Overlaps with RepositoryMetrics/WorkflowMetrics |
| ApiKey model | `auth/models.py` | **REUSE AS-IS** | Works for machine auth |

**New tables needed:**
- `users` — User accounts (OAuth)
- `organizations` — Multi-tenant orgs
- `sessions` — JWT session tracking
- `github_installations` — GitHub App installations
- `investigation_events` — Per-stage investigation tracking
- `notification_channels` — Notification routing

### API Layer

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| Root router | `api/router.py` | **REUSE AS-IS** | Working health/version |
| Auth router | `api/auth_router.py` | **REUSE AS-IS** | Working key management; add OAuth alongside |
| Analysis router | `api/analysis_router.py` | **REUSE AS-IS** | Working analysis endpoint |
| Fix router | `api/fix_router.py` | **REUSE AS-IS** | Working fix endpoint |
| Validation router | `api/validation_router.py` | **REUSE AS-IS** | Working validation endpoint |
| Retry router | `api/retry_router.py` | **REUSE AS-IS** | Working retry endpoint |
| Review router | `api/review_router.py` | **REUSE AS-IS** | Working review endpoint |
| PR router | `api/pr_router.py` | **REUSE AS-IS** | Working PR endpoint |
| Dashboard router | `api/dashboard_router.py` | **REUSE AS-IS** | Working dashboard endpoints |
| Tasks router | `api/tasks_router.py` | **REUSE AS-IS** | Working task endpoints |
| RAG router | `api/rag_router.py` | **REUSE AS-IS** | Working RAG endpoints |

**New endpoints needed:**
- `POST /api/github/webhook` — Webhook receiver
- `GET /api/auth/oauth/{provider}` — OAuth initiation
- `GET /api/auth/oauth/{provider}/callback` — OAuth callback
- `GET /api/events` — SSE endpoint
- `GET /api/admin/users` — User management (admin)
- `GET /api/admin/audit-log` — Audit log (admin)
- `POST /api/notifications/test` — Notification test endpoint

### Frontend Architecture

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| React + Vite + TypeScript | `frontend/` | **REUSE AS-IS** | Modern stack, good tooling |
| React Query hooks | `lib/api.ts` | **REUSE AS-IS** | Proper API layer with auth headers |
| Auth context | `lib/auth-context.ts` | **REUSE WITH MODIFICATIONS** | Keep interface; swap API key for JWT token |
| Agent context | `lib/agent-context.tsx` | **REUSE WITH MODIFICATIONS** | Keep decision engine; integrate with SSE instead of manual triggers |
| Activity feed | `components/activity-feed.tsx` | **REUSE AS-IS** | Working component |
| Branch history | `components/branch-history.tsx` | **REUSE AS-IS** | Working tree visualization |
| Decision timeline | `components/decision-timeline.tsx` | **REUSE AS-IS** | Working decision log |
| Pipeline visualization | `components/PipelineVisualization.tsx` | **REUSE AS-IS** | Working pipeline graph |
| Tab nav | `components/tab-nav.tsx` | **REUSE AS-IS** | Working navigation |
| Metric card | `components/metric-card.tsx` | **REUSE AS-IS** | Working metric display |
| Glass card | `components/GlassCard.tsx` | **REUSE AS-IS** | Working card component |
| Loading spinner | `components/LoadingSpinner.tsx` | **REUSE AS-IS** | Working loading state |
| Empty state | `components/empty-state.tsx` | **REUSE AS-IS** | Working empty state |
| Status badge | `components/status-badge.tsx` | **REUSE AS-IS** | Working status indicator |

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| StarsBackground | `components/StarsBackground.tsx` | **DELETE** | Decorative Three.js with zero operational value |
| ParticleField | `components/ParticleField.tsx` | **DELETE** | Decorative |
| AnimatedBackground | `components/AnimatedBackground.tsx` | **DELETE** | Decorative variants per page |
| 3DBackground | `components/3DBackground.tsx` | **DELETE** | Decorative |
| TiltCard | `components/tilt-card.tsx` | **DELETE** | Decorative hover effect |
| AnimatedCounter | `components/AnimatedCounter.tsx` | **DELETE** | Decorative number animation |
| SpotlightCard | `components/spotlight-card.tsx` | **DELETE** | Decorative effect |
| DemoBanner | `components/demo-banner.tsx` | **DELETE** | Only exists because of demo data |
| SelfHealingDemo | `components/SelfHealingDemo.tsx` | **DELETE** | Demo-only component |

### Dashboard

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| Dashboard page | `pages/dashboard.tsx` | **REBUILD** | Heavily coupled to demo data; all 6 tabs have fake fallbacks |
| Overview tab | `pages/dashboard.tsx` | **REWRITE** | Remove AgentImpact fake calculations; show real metrics |
| Repositories tab | `pages/dashboard.tsx` | **REWRITE** | Replace with real GitHub repositories |
| Recovery tab | `pages/dashboard.tsx` | **KEEP STRUCTURE** | Replace fake metrics with real retry data |
| Validation tab | `pages/dashboard.tsx` | **KEEP STRUCTURE** | Replace fake validation data with real |
| Health tab | `pages/dashboard.tsx` | **KEEP STRUCTURE** | Replace fake review scores with real |
| Pull Requests tab | `pages/dashboard.tsx` | **KEEP STRUCTURE** | Replace fake PR data with real |

### Admin System

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| Admin keys page | `pages/admin-keys.tsx` | **REWRITE** | Uses `demoKeys`; create/delete is local state only |
| Admin key API | `api/auth_router.py` | **REUSE AS-IS** | Working CRUD for API keys |

**New code needed:**
- `pages/admin.tsx` — Admin dashboard with user management, audit logs, system health
- `api/admin_router.py` — Admin-specific endpoints

### Logging

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| loguru setup | `utils/logger.py` | **REUSE AS-IS** | Working structured logging |
| Request tracing middleware | `main.py:91-111` | **REUSE AS-IS** | Working request ID tracing |

**New code needed:**
- None for logging itself. Splunk HEC client is separate (observability).

### Observability

| Component | Current | Action | Reasoning |
|-----------|---------|--------|-----------|
| Health endpoint | `api/router.py` | **REUSE AS-IS** | Working |
| Metrics collection | `dashboard/metrics_collector.py` | **REUSE AS-IS** | Working SQL aggregate queries |
| Analytics computation | `dashboard/analytics_engine.py` | **REUSE AS-IS** | Working cached analytics |

**New code needed:**
- `app/integrations/splunk.py` — HEC client
- `app/realtime/sse_manager.py` — SSE event system

---

## 2. Demo Data Eradication Plan

### DELETE (remove entirely, no replacement needed)

| File | Lines | Purpose | Reason |
|------|-------|---------|--------|
| `frontend/src/lib/demo-data.ts` | 1–836 | ALL fake data — repos, activities, failures, tasks, keys | Entire file is fake |
| `frontend/src/lib/demo-candidates.ts` | 1–end | Fake root cause candidates | Entire file is fake |
| `frontend/src/components/demo-banner.tsx` | All | "Demo" banner | Only exists because of demo data |
| `frontend/src/components/SelfHealingDemo.tsx` | All | Landing page demo player | Demo-only |
| `frontend/src/components/StarsBackground.tsx` | All | Decorative Three.js | No operational value |
| `frontend/src/components/ParticleField.tsx` | All | Decorative | No operational value |
| `frontend/src/components/AnimatedBackground.tsx` | All | Decorative per-page backgrounds | No operational value |
| `frontend/src/components/3DBackground.tsx` | All | Decorative Three.js | No operational value |
| `frontend/src/components/tilt-card.tsx` | All | Decorative hover effect | No operational value |
| `frontend/src/components/AnimatedCounter.tsx` | All | Decorative number animation | No operational value |
| `frontend/src/components/spotlight-card.tsx` | All | Decorative effect | No operational value |

### REPLACE (remove fake, connect to real API)

| File | What | Fake Data | Real Source | Strategy |
|------|------|-----------|-------------|----------|
| `pages/dashboard.tsx` | All `demoSummary`, `demoMetrics`, etc. fallbacks | 4 fake repos, fake metrics | API endpoints (`/dashboard/summary`, `/dashboard/repositories`, etc.) | Remove all `?? demoX` fallbacks; show error state when API fails |
| `pages/dashboard.tsx` | `adjustedSummary` / `adjustedRepos` | Derived from `healthDelta` (itself derived from fake validation) | API is source of truth | Remove entirely |
| `pages/analysis.tsx` | `demoWorkflowLogsByType` dropdown | 6 pre-baked failures | Real investigation results from webhook | Remove demo selector; auto-load from webhook event |
| `pages/analysis.tsx` | `demoCandidates` import | Fake root cause candidates | From API response | Remove import; use real `analysisMutation.data` |
| `pages/validation.tsx` | Demo data auto-load | Fake validation context | Real validation pipeline results | Remove; use API response |
| `pages/admin-keys.tsx` | `demoKeys` | 3 fake API keys | API `GET /auth/keys` | Replace with real API calls |
| `pages/admin-keys.tsx` | Local state create/delete | Creates fake keys in memory | API `POST /auth/keys`, `DELETE /auth/keys/{id}` | Replace with real mutations |
| `pages/dashboard.tsx` | `demoActivities` filtered | 28 fake activity items | Real activity from SSE + API | Remove; use live SSE stream |
| `pages/tasks.tsx` | `demoTasks` | 10 fake tasks | API `GET /tasks` | Remove; use `useTaskList()` |
| `pages/indexing.tsx` | `demoIndexedRepos` | 4 fake indexed repos | API `GET /rag/index/status` | Remove; use real status |

### KEEP (real functionality, no changes needed)

| File | Purpose |
|------|---------|
| `lib/api.ts` | React Query hooks; all point to real API |
| `lib/auth-context.ts` | Auth state management (interface) |
| `lib/agent-context.tsx` | Decision engine, activity tracking |
| `lib/types.ts` | TypeScript types |
| All components listed as REUSE AS-IS above | Working UI components |

---

## 3. Target Vision Gap Analysis

### Authentication Gaps

| Capability | Current State | Gap SeverITY | Implementation Complexity | Dependencies |
|-----------|---------------|-------------|--------------------------|--------------|
| Google OAuth | Not implemented | **CRITICAL** | Medium (3-5 days) | `authlib`, Google Cloud Console credentials |
| GitHub OAuth | Not implemented | **CRITICAL** | Medium (3-5 days) | `authlib`, GitHub App registration |
| User accounts | No Users table | **CRITICAL** | Low (models + migration) | None |
| Session management | sessionStorage only | **HIGH** | Low (JWT in httpOnly cookie) | `python-jose` |
| Organization support | No org table | **MEDIUM** | Low | Users table first |

### GitHub Integration Gaps

| Capability | Current State | Gap SeverITY | Implementation Complexity | Dependencies |
|-----------|---------------|-------------|--------------------------|--------------|
| GitHub App OAuth | Not implemented | **CRITICAL** | Medium (3-5 days) | GitHub App registration |
| Repository selection | Not implemented | **CRITICAL** | Medium (2-3 days) | GitHub App OAuth |
| Webhook receiver | Not implemented | **CRITICAL** | Low (1-2 days) | Router + signature verification |
| Workflow monitoring | Not implemented | **CRITICAL** | Low | Webhook receiver |
| Failure detection | Manual form only | **CRITICAL** | Low | Webhook → workflow_run.completed handler |
| Automated log collection | Form-pasted logs | **CRITICAL** | Low | Webhook → GitHub API log fetch |
| Repository sync endpoint | Not implemented | **MEDIUM** | Low (1 day) | GitHub App installation |

### Investigation Gaps

| Capability | Current State | Gap SeverITY | Implementation Complexity | Dependencies |
|-----------|---------------|-------------|--------------------------|--------------|
| Auto-investigation on failure | Manual trigger | **CRITICAL** | Low | Webhook + task submission |
| 8-stage progress display | 3-phase simplified | **HIGH** | Medium (3-5 days) | SSE for real-time updates |
| Per-stage evidence display | Fake evidence | **HIGH** | Low | Real data from API |
| Investigation tracking model | Not implemented | **MEDIUM** | Low (1 day) | New DB model |
| Investigation history endpoint | Not implemented | **MEDIUM** | Low | Investigation model |

### Validation Gaps

| Capability | Current State | Gap SeverITY | Implementation Complexity | Dependencies |
|-----------|---------------|-------------|--------------------------|--------------|
| 6-stage visual pipeline | Static pass/fail | **HIGH** | Medium (3-5 days) | SSE |
| Stage duration + logs | Not displayed | **MEDIUM** | Low (frontend component) | Backend returns stage data |
| Security scan stage | Missing | **MEDIUM** | Low (new validator module) | None |

### Notification Gaps

| Capability | Current State | Gap SeverITY | Implementation Complexity | Dependencies |
|-----------|---------------|-------------|--------------------------|--------------|
| Slack notifications | Not implemented | **HIGH** | Medium (3-5 days) | Slack App registration |
| Email notifications | Not implemented | **MEDIUM** | Medium (2-3 days) | SMTP config |
| Notification dispatcher | Not implemented | **HIGH** | Low (1 day) | None |
| Notification configuration UI | Not implemented | **MEDIUM** | Medium (2-3 days) | Settings page |

### Real-Time Gaps

| Capability | Current State | Gap SeverITY | Implementation Complexity | Dependencies |
|-----------|---------------|-------------|--------------------------|--------------|
| SSE endpoint | Not implemented | **CRITICAL** | Low (1-2 days) | FastAPI `StreamingResponse` + `asyncio.Queue` |
| Live investigation updates | Not possible | **HIGH** | Low | SSE endpoint + frontend `EventSource` |
| Live dashboard | 30s polling | **HIGH** | Low | SSE endpoint |
| Live activity stream | Fake activities | **HIGH** | Low | SSE endpoint |

### Admin Gaps

| Capability | Current State | Gap SeverITY | Implementation Complexity | Dependencies |
|-----------|---------------|-------------|--------------------------|--------------|
| Admin dashboard | Not implemented | **MEDIUM** | Medium (2-3 days) | Admin endpoints |
| User management | Not implemented | **MEDIUM** | Medium (2-3 days) | Users table |
| Audit logging | Not implemented | **MEDIUM** | Low (1-2 days) | Audit log table |
| System health monitoring | Not implemented | **LOW** | Low (1 day) | None |

### Observability Gaps

| Capability | Current State | Gap SeverITY | Implementation Complexity | Dependencies |
|-----------|---------------|-------------|--------------------------|--------------|
| Splunk HEC integration | Not implemented | **LOW** | Medium (2-3 days) | Splunk instance |
| Investigation event storage | Not implemented | **MEDIUM** | Low (1 day) | Event model |
| Searchable investigation history | Not implemented | **MEDIUM** | Low (1 day) | Event model + search endpoint |

---

## 4. Product Credibility Audit

### HIGH Impact Issues (makes the product feel fake to every user)

| Issue | Location | Why It Hurts Credibility |
|-------|----------|------------------------|
| **Demo scenario dropdown** | `pages/analysis.tsx` — 6 pre-baked failures | Users immediately see the product is a simulation, not a real agent |
| **Hardcoded repositories** | `demo-data.ts:18-23` — 4 fake repos | The core promise is "monitor your repos"; showing fake ones breaks trust immediately |
| **Demo login keys in UI** | `demo-data.ts:128-132` — 3 fake API keys in settings | Suggests the entire auth system is a facade |
| **Activity feed mixed with fake** | `pages/dashboard.tsx:542-544` | Users see events for repositories they don't own |
| **Fake validation outcomes** | `demo-data.ts:67-73` — `getRandomOutcome()` always returns `true` | The entire validation system is a mock; no real decisions are made |
| **API key as only login method** | `pages/login.tsx` | No real identity; feels like a dev tool, not a production platform |

### MEDIUM Impact Issues

| Issue | Location | Why It Hurts Credibility |
|-------|----------|------------------------|
| **Fake "auto-resolved" metric** | `pages/dashboard.tsx:66-73` | Agent Impact section derives fake numbers from fake data; users recognize fabricated KPIs |
| **AdjustedSummary/AdjustedRepos** | `pages/dashboard.tsx:553-570` | Overrides real data with derived values from a `healthDelta` that starts at 0 |
| **Admin keys page is entirely fake** | `pages/admin-keys.tsx:84-93` | Create/delete operations only modify local state; no API calls |
| **Empty dashboard cards** | `pages/dashboard.tsx` multiple tabs | "No data" states when real data should exist |
| **Simulated retry timeline** | `demo-data.ts:149-162` | 12 fake retry attempts with fake statuses |
| **Demo banner** | `components/demo-banner.tsx` | Explicitly labels the product as a demo |

### LOW Impact Issues

| Issue | Location | Why It Hurts Credibility |
|-------|----------|------------------------|
| **3D backgrounds** | Multiple Three.js components | Suggests the team focused on visuals instead of real product |
| **Tilt cards** | `tilt-card.tsx` | Novelty effect; undermines enterprise credibility |
| **Animated page transitions** | framer-motion in every page | Adds latency; feels like a portfolio project |
| **Animated counter waves** | `AnimatedCounter.tsx` | Decorative; no operational information |
| **Fake review scores** | `dashboard/charts.py:52-56` | All 5 categories return the same score |
| **Simulated PRs vs Real PRs chart** | `dashboard/charts.py:79-85` | Always shows 0 for both categories |

---

## 5. UI/UX Transformation Plan

### Dashboard

| Element | Action | Rationale |
|---------|--------|-----------|
| All `demo*` fallbacks | **Remove** | Show error/empty state when API fails — never fake data |
| `adjustedSummary`/`adjustedRepos` | **Remove** | API is source of truth |
| `AgentImpact` card | **Rewrite** | Derive from real metrics, not fake calculations |
| 3D/particle backgrounds | **Remove** | No operational value |
| TiltCard wrappers | **Remove** | Replace with flat GlassCard |
| framer-motion page transitions | **Remove** | Use CSS transitions; reduce latency |
| AnimatedCounter | **Remove** | Use plain text numbers |
| Demo activity feed | **Replace** | SSE-driven live activity stream |
| 30s polling | **Replace** | SSE-driven invalidation |
| Sidebar demo badge counts | **Remove** | Replace with real counts from API |
| Repos tab | **Rewrite** | Show real GitHub repos with branch/workflow/status columns |

**Remaining:** TabNav, MetricCard, GlassCard, ActivityFeed, BranchHistory, DecisionTimeline, PipelineVisualization, EmptyState, ErrorBanner

### Analysis Page

| Element | Action | Rationale |
|---------|--------|-----------|
| Demo scenario dropdown | **Remove** | No demo mode |
| HandleLoadExample | **Remove** | Only existed for demo scenarios |
| demoCandidates import | **Remove** | Use real API response |
| 3-phase investigation | **Replace** | 8-stage Investigation Pipeline component |
| Auto-advance timers | **Remove** | SSE-driven real progress |
| Fake evidence cards | **Replace** | Real evidence from API |

**Remaining:** Form for manual investigation if needed, but primary path is webhook-driven. New `InvestigationPipeline` component needed.

### Validation Page

| Element | Action | Rationale |
|---------|--------|-----------|
| Static pass/fail | **Replace** | 6-stage Validation Pipeline component |
| Demo data auto-load | **Remove** | Real data from investigation context |
| Health impact/computed deltas | **Remove** | Real validation results from API |

**Remaining:** Structure for displaying results. New `ValidationPipeline` component needed.

### Landing/Login Page

| Element | Action | Rationale |
|---------|--------|-----------|
| API key form | **Remove** | Replace with Google + GitHub OAuth buttons |
| SelfHealingDemo component | **Remove** | Demo-only player |
| AnimatedBackground | **Remove** | Decorative |
| framer-motion variants | **Remove** | No benefit for auth pages |
| Product showcase section | **Reduce** | Keep minimal value prop; no demo animation |

### Settings Page (currently non-existent)

| Element | Action | Rationale |
|---------|--------|-----------|
| Old admin-keys.tsx | **Replace** | Becomes a tab under real Settings page |
| Connected Accounts | **New** | Google, GitHub, Slack connection status |
| Notification Config | **New** | Email, Slack event toggles |
| Repository Rules | **New** | Auto-fix policies per repo |

### Retry, Review, PR, Indexing, Tasks Pages

| Element | Action | Rationale |
|---------|--------|-----------|
| All demo data fallbacks | **Remove** | Use real API data |
| Decorative components | **Remove** | Same as dashboard |
| framer-motion transitions | **Remove** | Same as dashboard |

---

## 6. Minimum Credible Product (MCP) Definition

The smallest version that genuinely qualifies as a Self-Healing CI/CD Agent.

### REQUIRED Features

| # | Feature | Why It's Required | Backend Status | Frontend Status |
|---|---------|------------------|----------------|-----------------|
| 1 | **Google OAuth sign-in** | Users need real identities; API keys are not acceptable for a production product | Missing | Missing |
| 2 | **GitHub OAuth + repo selection** | Core product promise is monitoring YOUR repositories | Missing | Missing |
| 3 | **GitHub webhook receiver** | Automated failure detection is the trigger for everything the agent does | Missing | Missing |
| 4 | **Auto-investigation on failure** | Product must react autonomously, not wait for manual form submission | Backend works; needs webhook trigger | Missing (new InvestigationPipeline component) |
| 5 | **SSE real-time updates** | Users need to see live progress; polling is not acceptable for an "active agent" | Missing | Missing |
| 6 | **Investigation progress display** | Users must see what the agent is doing, what it found, and what happens next | Backend works; frontend shows 3 fake phases | Needs rewrite (8-stage pipeline) |
| 7 | **Validation pipeline display** | Users must see validation stages, results, and evidence | Backend works (3 stages); frontend shows static pass/fail | Needs rewrite (6-stage pipeline) |
| 8 | **PR creation (real GitHub)** | The agent must be able to create real PRs | Works (dry_run + approved flags) | Works via API |
| 9 | **Slack failure notifications** | Users need to know when things break; Slack is the standard | Missing | Missing |
| 10 | **Eliminate ALL demo data** | Fake data destroys credibility; users must see their real data | N/A | 10+ files to delete/replace |

### REQUIRED Backend Systems

| System | Status | Work Needed |
|--------|--------|-------------|
| LLM-powered analysis engine | ✅ Exists | None |
| Fix generation | ✅ Exists | None |
| Validation service | ✅ Exists | None |
| Review orchestration | ✅ Exists | None |
| PR creation | ✅ Exists | None |
| RAG indexing | ✅ Exists | None |
| Task queue | ✅ Exists | Minor (Redis for production) |
| Rate limiting | ✅ Exists | None |
| Circuit breaker | ✅ Exists | None |
| Structured logging | ✅ Exists | None |
| GitHub REST client | ✅ Exists | None |
| **OAuth + User management** | ❌ Missing | New |
| **Webhook receiver** | ❌ Missing | New |
| **SSE manager** | ❌ Missing | New |
| **Notification dispatcher** | ❌ Missing | New |

### REQUIRED Frontend Systems

| System | Status | Work Needed |
|--------|--------|-------------|
| React + Vite + TypeScript | ✅ Exists | None |
| React Query API layer | ✅ Exists | None |
| Auth context | ✅ Exists | Minor (swap API key for JWT) |
| Activity feed component | ✅ Exists | Remove demo data |
| Branch history component | ✅ Exists | None |
| Decision timeline | ✅ Exists | None |
| Pipeline visualization | ✅ Exists | None |
| Metric card | ✅ Exists | None |
| Tab nav | ✅ Exists | None |
| Empty state | ✅ Exists | None |
| Error banner | ✅ Exists | None |
| Status badge | ✅ Exists | None |
| **OAuth login page** | ❌ Missing | New |
| **Investigation Pipeline component** | ❌ Missing | New |
| **Validation Pipeline component** | ❌ Missing | New |
| **SSE hook** | ❌ Missing | New |
| **Settings page** | ❌ Missing | New |

### OPTIONAL (can be deferred)

| Feature | When to Add |
|---------|-------------|
| Email notifications | Phase 2 |
| Splunk integration | Phase 2 |
| Admin dashboard | Phase 2 |
| User management | Phase 2 |
| Audit logging | Phase 2 |
| Multi-tenant organizations | Phase 3 |
| PostgreSQL migration | Phase 3 |
| Redis-backed queue | Phase 3 |
| Automated re-indexing | Phase 2 |
| Security scan validation stage | Phase 2 |
| Failure category analytics | Phase 2 |
| MTTR computation | Phase 2 |
| Repository health trends | Phase 2 |

---

## 7. Top 10 Implementation Priorities

Ranked by: contribution to Minimum Credible Product ÷ engineering effort

| Rank | Priority | Effort | Impact | Description |
|------|----------|--------|--------|-------------|
| 1 | **OAuth + User accounts** | 5 days | **CRITICAL** | Google OAuth sign-in, JWT sessions, Users/Orgs tables. Unlocks real identity for every user. Without this, nothing else matters — users cannot have accounts. |
| 2 | **GitHub App + Webhooks** | 5 days | **CRITICAL** | GitHub OAuth, App installation, webhook receiver for `workflow_run.completed`. Unlocks automated failure detection — the agent's trigger. |
| 3 | **SSE real-time system** | 2 days | **CRITICAL** | Backend SSE endpoint with `asyncio.Queue` per channel, frontend `EventSource` hook. Replaces all polling; enables live investigation/validation display. |
| 4 | **Demo data eradication** | 2 days | **CRITICAL** | Delete `demo-data.ts`, `demo-candidates.ts`, all decorative components. Update all pages to show error/empty state instead of fake data. |
| 5 | **Investigation Pipeline component** | 3 days | **HIGH** | 8-stage visual pipeline with SSE-driven progress. Replaces 3-phase simulation. Users see live investigation stages, evidence, confidence changes. |
| 6 | **Validation Pipeline component** | 2 days | **HIGH** | 6-stage visual pipeline with SSE-driven stage completion. Replaces static pass/fail. Users see build/unit/integration/security progress. |
| 7 | **Slack notifications** | 3 days | **HIGH** | Slack OAuth, message formatting for workflow_failed/investigation_started/fix_generated/pr_created. Users get notified without watching the dashboard. |
| 8 | **Settings page** | 3 days | **HIGH** | Connected accounts (Google, GitHub, Slack), notification preferences, repository rules. Replaces `admin-keys.tsx` with real settings. |
| 9 | **Webhook → auto-investigation flow** | 2 days | **HIGH** | Wire webhook event → create Failure → submit investigation task → emit SSE events. Closes the loop from failure to analysis. |
| 10 | **GitHub repo sync + display** | 2 days | **MEDIUM** | `GET /api/github/repositories` endpoint, frontend repository tab shows real repos with status/health. Replace 4 fake repos. |

### Total MCP Effort: ~29 days (6 weeks for one developer)

All 10 priorities can be built in parallel where dependencies allow.

---

## 8. Recommended Implementation Order

### Week 1-2: Identity & Connectivity (Priorities 1-2)

```
Day 1-3: User model, Organization model, Session model, migration
Day 3-5: Google OAuth endpoints, JWT session management
Day 5-7: GitHub OAuth, GitHub App installation flow
Day 7-10: Webhook receiver, signature verification, event handlers
```

**Milestone:** User can sign in with Google, connect GitHub repos, and the system receives webhooks.

### Week 3: Real-Time & Credibility (Priorities 3-4)

```
Day 1-2: SSE manager, event publishing from workflows
Day 2-3: Frontend EventSource hook, replace React Query polling
Day 3-5: Delete ALL demo data files, remove decorative components
Day 5-6: Update all pages to show error/empty states instead of fake fallbacks
```

**Milestone:** Dashboard shows real data (or empty states), updates in real time.

### Week 4-5: Agent Visibility (Priorities 5-6)

```
Day 1-3: InvestigationPipeline component (8 stages, SSE-driven)
Day 3-5: ValidationPipeline component (6 stages, SSE-driven)
Day 5-6: Wire webhook → auto-investigation → SSE events → UI updates
Day 6-8: Wire investigation → fix → validation → PR → SSE events → UI updates
```

**Milestone:** End-to-end autonomous flow works: webhook → investigation → validation → PR, visible live in UI.

### Week 6: Notifications & Settings (Priorities 7-8)

```
Day 1-2: Slack OAuth, notification dispatcher
Day 2-3: Slack message formatting (workflow_failed, investigation_started, etc.)
Day 3-4: Settings page (connected accounts, notifications, repo rules)
Day 4-5: Replace admin-keys.tsx with real API calls in settings
```

**Milestone:** Users receive Slack notifications; settings page is functional.

### Week 7: Polish & Hardening (Priorities 9-10)

```
Day 1-2: Queue hardening (re-queue pending tasks on startup)
Day 2-3: Investigation/validation event logging to DB
Day 3-4: GitHub repo sync endpoint + frontend display
Day 4-5: Error handling audit, empty states, loading states
```

**Milestone:** Minimum Credible Product is complete.

---

## Summary

The shortest path from current state to Minimum Credible Product is **~6 weeks** and requires:

| Category | Work |
|----------|------|
| **Backend new code** | OAuth (User/Org/Session models + endpoints), webhook receiver, SSE manager, notification dispatcher, Slack integration |
| **Backend reuse** | Everything in agents/, workflows/, validation/, github/, rag/, queue/, parsers/, llm/ — zero changes needed |
| **Frontend new code** | OAuth login page, InvestigationPipeline component, ValidationPipeline component, SSE hook, Settings page |
| **Frontend reuse** | React Query hooks, auth context, activity feed, branch history, decision timeline, pipeline viz, metric card, tab nav |
| **Frontend deletion** | demo-data.ts, demo-candidates.ts, StarsBackground, ParticleField, AnimatedBackground, 3DBackground, TiltCard, AnimatedCounter, SpotlightCard, DemoBanner, SelfHealingDemo |
| **Config/ops** | Google Cloud Console OAuth app, GitHub App registration, Slack App registration |

**The agent backend is already production-ready.** The product feels like a demo because:
1. No real user identity (API keys only)
2. No real repository connectivity (no webhooks)
3. No real-time feedback (no SSE)
4. Frontend is wrapped in demo data and decorative visuals

Remove those four blockers and the existing agent machinery is immediately visible as a genuine autonomous engineering platform.
