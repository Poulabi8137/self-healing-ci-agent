# Production Audit & Migration Plan — Self-Healing CI Agent

> Prepared: June 2026
> Scope: Full-stack architecture, demo data elimination, product gaps, productionization roadmap

---

## Table of Contents

1. Architecture Audit
2. Demo Data Inventory
3. Product Gap Analysis
4. Authentication Migration Plan
5. GitHub Integration Plan
6. Slack Integration Plan
7. Splunk Integration Plan
8. Notification Architecture
9. Real-Time Architecture
10. Database Changes Required
11. UI/UX Redesign Plan
12. Page-by-Page Refactor Plan
13. Risk Analysis
14. Implementation Roadmap (Phase 1–5)

---

## 1. Architecture Audit

### 1.1 Current Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (React 19)                   │
│  Vite 8 · TypeScript 6 · Tailwind v4 · React Query 5    │
│  framer-motion · recharts · Three.js (@react-three)     │
├──────────────────────┬──────────────────────────────────┤
│  Auth: API key in    │  State: React Query (server) +   │
│  sessionStorage      │  useAgent() context (client)     │
│       ┌──────────────┴──────────────┐                   │
│       │    Vite proxy /api → :8000  │                   │
│       └──────────────┬──────────────┘                   │
├──────────────────────┴──────────────────────────────────┤
│                   BACKEND (FastAPI)                      │
│  Python 3.12 · SQLAlchemy · Alembic · loguru · httpx    │
├──────────────────────┬──────────────────────────────────┤
│  Auth: X-API-Key     │  DB: SQLite (dev) → PostgreSQL   │
│  header, SHA-256     │  (prod-ready schema)              │
│  hashing, RBAC       │                                   │
├──────────────────────┴──────────────────────────────────┤
│                    LAYER STACK                           │
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐               │
│  │Routers  │→ │Workflows │→ │  Agents  │               │
│  │(11)     │  │(6)       │  │(8)       │               │
│  └─────────┘  └──────────┘  └──────────┘               │
│       │            │              │                      │
│       ▼            ▼              ▼                      │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐               │
│  │LLM      │  │RAG       │  │GitHub    │               │
│  │Factory  │  │Pipeline  │  │Client    │               │
│  │(3prov.) │  │(FAISS)   │  │(httpx)   │               │
│  └─────────┘  └──────────┘  └──────────┘               │
│       │                                                 │
│       ▼                                                 │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐               │
│  │Queue    │  │Validator │  │Reviewers │               │
│  │(in-mem) │  │(3-stage) │  │(4 agents)│               │
│  └─────────┘  └──────────┘  └──────────┘               │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Frontend Framework

| Aspect | Current | Notes |
|--------|---------|-------|
| **Framework** | React 19 + Vite 8 | Modern, good choice |
| **Language** | TypeScript 6 | Latest |
| **Styling** | Tailwind CSS v4 | Current |
| **Routing** | React Router (implicit, via `<Link>`/`<Navigate>`) | No centralized route config |
| **Server State** | @tanstack/react-query v5 | Good, but unused for auth |
| **Client State** | React context (`useAgent`, `useAuth`) | AgentContext has decision engine |
| **Animation** | framer-motion + Three.js | Heavy for a CI tool |
| **Charts** | recharts | Adequate |
| **Testing** | vitest + testing-library (59 tests) | Good coverage for pages |

**Issues:**
- No centralized router config file — routes are scattered in sidebar (`layout.tsx`)
- React Query is used for API calls but frontend falls back to demo data on error
- 3D backgrounds (`StarsBackground`, `ParticleField`, `3DBackground`) add zero operational value
- `useAgent` context couples decision engine, activity feed, and UI state together

### 1.3 Backend Framework

| Aspect | Current | Notes |
|--------|---------|-------|
| **Framework** | FastAPI (single process) | Good foundation |
| **Language** | Python 3.12+ | Modern |
| **ORM** | SQLAlchemy 2.x | Good, with proper session mgmt |
| **Migrations** | Alembic | Initial schema exists |
| **Validation** | Pydantic v2 (via pydantic-settings) | Good |
| **Logging** | loguru with structured JSON | Production-ready |
| **Testing** | pytest (~259 tests) | Good coverage |
| **Rate Limiting** | Custom sliding window middleware | Basic but functional |
| **Circuit Breaker** | Custom state machine | Good for LLM/API resilience |

**Issues:**
- Single-process, no async worker pool beyond in-process asyncio tasks
- No health check endpoint beyond root `/`
- No structured error responses (mixed plain dict vs Pydantic models)
- No OpenAPI documentation customization
- Rate limiter is in-memory (not shared across processes)

### 1.4 Database

| Aspect | Current | Notes |
|--------|---------|-------|
| **Engine** | SQLite (file-based) | Dev only |
| **Target** | PostgreSQL-ready (no PG-specific features) | Good |
| **Schema** | 10 tables: Repository, Failure, Fix, RetryAttempt, ReviewResult, PRRecord, BenchmarkRun, RepositoryMetrics, WorkflowMetrics, Metric | Overlapping metric tables |
| **Auth tables** | ApiKey (in auth/models.py) | Separate from main models |
| **Cache** | In-memory TTL dict | Not distributed |

**Issues:**
- `Metric` and `RepositoryMetrics`/`WorkflowMetrics` overlap in purpose
- `BenchmarkRun` is barely used — likely dead code or demo-only
- No `Organizations` or `Users` table (required for OAuth)
- No `Notifications` table
- No `SlackIntegrations` or `SplunkIntegrations` table
- Alembic migration exists for initial schema only

### 1.5 Authentication

| Aspect | Current | Notes |
|--------|---------|-------|
| **Method** | X-API-Key header, SHA-256 hashed | Good for machine-to-machine |
| **RBAC** | candidate / recruiter / admin | Coarse |
| **Session** | sessionStorage (frontend), no backend session | Stateless |
| **Bootstrap** | `bootstrap_admin_key` env var | Admin provisioning done |
| **Rate Limit** | 30 req/min per key | Basic |

**Issues:**
- No OAuth (Google, GitHub) support at all
- No user registration flow
- No session management (sessionStorage only, no expiry)
- Frontend `auth-context.ts` has a `decodeRole` function that parses fake base64 tokens
- `demo-data.ts` has hardcoded demo API keys (lines 128–132)

### 1.6 API Architecture

| Router | Prefix | Auth | Status |
|--------|--------|------|--------|
| root | `/` | None | Health + version |
| auth | `/auth` | Optional | Key management |
| dashboard | `/dashboard` | Required | Summary, metrics, repos, charts |
| analysis | `/analysis` | Required | Debug endpoint |
| fix | `/fix` | Required | Fix generation |
| validation | `/validation` | Required | Validation pipeline |
| retry | `/retry` | Required | Retry workflow |
| review | `/review` | Required | Code review orchestration |
| pr | `/pr` | Required | PR creation |
| rag | `/rag` | Required | Index + retrieve |
| tasks | `/tasks` | Required | Task CRUD + status |

All endpoints are synchronous wrappers using `asyncio.to_thread()` for DB/blocking work.

### 1.7 Real-Time Architecture

**Current: None.** No WebSocket, no SSE, no polling in production code.

- Frontend React Query `refetchInterval` (30s for dashboard, 10s for tasks, 2s for running tasks) is the closest thing to real-time
- `websockets` is installed in the Python venv but unused in any app code
- The `RELEASE_NOTES.md` mentions WebSocket but there's no implementation

### 1.8 Queue Architecture

| Aspect | Current | Notes |
|--------|---------|-------|
| **Implementation** | In-process asyncio task queue | Not persistent |
| **Storage** | SQLite `Task` table | Stores state but worker is in-memory |
| **Workers** | Single event loop | No distribution |
| **Retry** | Max attempts configurable, exponential backoff | Good |
| **Handlers** | 7 registered: analysis, fix, validation, retry, review, pr_create, rag_index, rag_retrieve | Covers all workflows |

**Issues:**
- No persistent queue (Redis/RabbitMQ/SQS)
- Worker dies on process restart (pending tasks survive in DB but aren't re-queued)
- No task prioritization
- No worker pool (single-threaded processing)

### 1.9 Integration Architecture

| Integration | Current | Status |
|-------------|---------|--------|
| **GitHub** | REST client (httpx), branch/commit/PR operations | Functional but limited |
| **LLM** | DeepSeek (primary), Groq (secondary), OpenAI (stub) | Production-ready |
| **RAG** | FAISS vector store, sentence-transformers, per-repo indices | Functional |
| **Slack** | Not implemented | Missing |
| **Splunk** | Not implemented | Missing |
| **Email** | Not implemented | Missing |

---

## 2. Demo Data Inventory

Every location where fake/placeholder data exists, its impact, and replacement strategy.

### 2.1 Frontend Demo Data

#### `frontend/src/lib/demo-data.ts` (836 lines — entire file is fake)

| Lines | Item | Impact | Replacement Strategy |
|-------|------|--------|---------------------|
| 18–23 | `demoRepos`: 4 hardcoded repos | Dashboard shows fake repos instead of real ones | Delete; fetch from `/dashboard/repositories` API |
| 28–37 | `demoSummary`: Hardcoded health metrics | Overview tab shows fake numbers | Delete; use API response; compute from real data |
| 42–47 | `demoMetrics`: Hardcoded retry metrics | Recovery tab shows fake data | Delete; use API |
| 52–55 | `demoReviewScores`: Hardcoded scores | Health tab shows fake scores | Delete; use API |
| 57–60 | `demoValidationResults`: Pass/fail 85/15 | Validation tab shows fake | Delete; use API |
| 62–65 | `demoPRStatistics`: Auto 6 / Manual 4 | PR tab shows fake | Delete; use API |
| 67–73 | `getRandomOutcome()` / `weightedRandom()` | Functions that pretend to be random but always return first option | Delete |
| 84–123 | `demoActivities`: 28 hardcoded items | Activity feed shows fake events | Replace with live activity from API/WebSocket |
| 128–132 | `demoKeys`: 3 fake API keys | Settings page shows fake keys | Delete; use real API key data |
| 149–162 | `demoRetryTimeline`: 12 fake retries | Retry page shows fake timeline | Delete; fetch from API |
| 167–751 | 6 fake failures (logs, analysis, fix, validation) | Analysis/validation/fix pages show demo data | Delete; use real workflow data |
| 756–799 | `demoWorkflowLogsByType`: Maps failure types to fake data | Dropdown for selecting demo scenarios | Delete; remove demo mode entirely |
| 804–810 | Legacy aliases (`demoExampleRepo`, etc.) | Backward compat for removed code | Delete |
| 815–826 | `demoTasks`: 10 fake tasks | Tasks page shows fake tasks | Delete; use API |
| 831–836 | `demoIndexedRepos`: 4 fake repos | Indexing page shows fake repos | Delete; use API |

#### `frontend/src/lib/demo-candidates.ts` (entire file — fake RCA candidates)

| Lines | Item | Impact | Replacement Strategy |
|-------|------|--------|---------------------|
| All | Pre-baked root cause candidates with evidence | Analysis page shows fake options instead of real AI-generated ones | Delete; use real `useTriggerAnalysis` mutation results |

#### `frontend/src/pages/dashboard.tsx`

| Lines | Item | Impact | Replacement Strategy |
|-------|------|--------|---------------------|
| 150–151 | Filters demoActivities for failures/recoveries | Overview tab shows hardcoded events | Replace with API-based activity stream |
| 263–265 | Expands repo detail with demoActivities | Repo tab shows hardcoded events | Replace with API data |
| 456 | Filters demoActivities for PRs | PR tab shows fake PRs | Use API |
| 542–544 | Combines demoActivities + liveActivities | Feed shows fake events first | Remove demoActivities entirely |
| 553–561 | `adjustedSummary` — computes from `healthDelta` | Correct intent but overrides API data with derived values | Remove entirely; let API be source of truth |
| 563–570 | `adjustedRepos` — same pattern | Same issue | Remove |
| 629–634 | Falls back to `demoSummary`, `demoRepos`, etc. | All tabs show fake data when API fails | Show error state, not fake data |

#### `frontend/src/pages/analysis.tsx`

| Lines | Item | Impact |
|-------|------|--------|
| 2–4 | Imports `demoWorkflowLogsByType`, `demoCandidates` | Entire analysis demo mode |
| Various | `handleLoadExample` loads demo data | Demo scenario selector |
| Various | Uses `demoCandidates` when no real API response | Shows fake candidates |

#### `frontend/src/pages/validation.tsx`

| Lines | Item | Impact |
|-------|------|--------|
| Various | Uses `demoWorkflowLogsByType` for auto-loaded repo context | Validation shows demo data |

#### `frontend/src/pages/indexing.tsx`

| Lines | Item | Impact |
|-------|------|--------|
| Likely | Uses `demoIndexedRepos` | Fake indexing status |

#### `frontend/src/lib/agent-context.tsx`

| Lines | Item | Impact |
|-------|------|--------|
| Various | Decision engine creates fake decision records | Records have no backing in real data |

### 2.2 Backend Demo/Fake Data Patterns

#### `app/dashboard/charts.py`

| Lines | Item | Impact | Replacement |
|-------|------|--------|-------------|
| 52–56 | `get_review_scores_dataset()`: All 5 categories get the same score | Fake diversity in scores | Query real per-category reviews |
| 79–85 | `get_pr_statistics_dataset()`: Labels are "Simulated PRs" vs "Real PRs" | Always shows simulated as 0 | Remove; show real PR data only |

#### `app/dashboard/analytics_engine.py`

| Lines | Item | Impact | Replacement |
|-------|------|--------|-------------|
| 122–149 | `compute_retry_distribution()`: Returns empty dict on error | Silently fails, frontend shows nothing | Add error propagation |
| 153–175 | `compute_full_analytics()`: 30s cache | Delayed metrics | Acceptable for production, but should be configurable |

---

## 3. Product Gap Analysis

### 3.1 Authentication Gaps

| Requirement | Current | Gap | Priority |
|-------------|---------|-----|----------|
| Google OAuth | Not implemented | Full gap | P0 |
| GitHub OAuth | Not implemented | Full gap | P0 |
| Session management | sessionStorage only | No expiry, no refresh | P0 |
| User registration | Not implemented | Required for OAuth | P0 |
| RBAC refinement | 3 roles only | Needs org-scoped permissions | P1 |
| MFA | Not implemented | Future | P2 |

### 3.2 Repository Monitoring Gaps

| Requirement | Current | Gap | Priority |
|-------------|---------|-----|----------|
| Real GitHub repos | 4 hardcoded fake repos | Full gap | P0 |
| Branch display | Not available | Missing | P0 |
| Workflow status | Not displayed | Missing | P0 |
| Last run time | Not shown | Missing | P0 |
| Failure count | Fake numbers | Full gap | P0 |
| Health score | Not computed | Missing | P0 |
| Active investigation indicator | Not implemented | Missing | P0 |
| Auto-polling for new failures | Not implemented | Missing | P1 |

### 3.3 Investigation Gaps

| Requirement | Current | Gap | Priority |
|-------------|---------|-----|----------|
| Autonomous detection | Manual form submission | Full gap | P0 |
| 8-stage workflow display | 3 simplified phases | Partial | P0 |
| Progress indicators | Basic step counter | Partial | P0 |
| Evidence display | Fake evidence only | Full gap | P0 |
| Confidence changes | Fake values | Full gap | P0 |
| Real log collection | Form-based | Needs GitHub webhook | P0 |

### 3.4 Validation Pipeline Gaps

| Requirement | Current | Gap | Priority |
|-------------|---------|-----|----------|
| 6 validation stages | Static page with 2 tab sections | Full gap | P0 |
| Build Validation | Not as a visible stage | Missing | P1 |
| Unit Tests | Not as a visible stage | Missing | P1 |
| Integration Tests | Not as a visible stage | Missing | P1 |
| Security Scan | Not as a visible stage | Missing | P1 |
| Regression Analysis | Not as a visible stage | Missing | P1 |
| Stage status/duration/logs | Not available | Missing | P0 |

### 3.5 Analytics Gaps

| Requirement | Current | Gap | Priority |
|-------------|---------|-----|----------|
| MTTR | Not computed | Missing | P1 |
| Success Rate | Computed from RetryAttempt | Partial (needs better source) | P0 |
| Failure Rate | Same as above | Partial | P0 |
| Auto-Heal Rate | Not computed | Missing | P1 |
| Validation Accuracy | Computed from RetryAttempt | Partial | P1 |
| PR Acceptance Rate | Not computed | Missing | P1 |
| Repository Health Trends | Not computed | Missing | P1 |
| Failure Categories | Not computed | Missing | P1 |

### 3.6 Notification Gaps

| Requirement | Current | Gap | Priority |
|-------------|---------|-----|----------|
| Slack notifications | Not implemented | Full gap | P0 |
| Email notifications | Not implemented | Full gap | P1 |
| Splunk integration | Not implemented | Full gap | P1 |
| Success notifications | Not implemented | Full gap | P1 |
| Failure notifications | Not implemented | Full gap | P0 |
| Investigation updates | Not implemented | Full gap | P1 |
| PR notifications | Not implemented | Full gap | P1 |

### 3.7 Real-Time Gaps

| Requirement | Current | Gap | Priority |
|-------------|---------|-----|----------|
| WebSocket/SSE | Not implemented | Full gap | P0 |
| Live dashboard updates | 30s polling only | Partial | P0 |
| Live investigation updates | No real-time | Full gap | P0 |
| Live validation updates | No real-time | Full gap | P0 |
| Live task updates | 2–10s polling | Partial | P1 |
| Repository index events | No real-time | Full gap | P1 |

### 3.8 Settings Page Gap

| Requirement | Current | Gap | Priority |
|-------------|---------|-----|----------|
| Connected Accounts (Google) | Not implemented | Full gap | P0 |
| Connected Accounts (GitHub) | Not implemented | Full gap | P0 |
| Connected Accounts (Slack) | Not implemented | Full gap | P0 |
| Connected Accounts (Splunk) | Not implemented | Full gap | P1 |
| Notification config | Not implemented | Full gap | P0 |
| Repository rules/auto-fix policies | Not implemented | Full gap | P1 |
| Escalation rules | Not implemented | Full gap | P1 |
| Monitoring configuration | Not implemented | Full gap | P1 |

### 3.9 Task System Gaps

| Requirement | Current | Gap | Priority |
|-------------|---------|-----|----------|
| Real job tracking | 10 fake tasks | Full gap | P0 |
| Timestamps | Present in demo data | Partial | P0 |
| Progress | Not tracked | Full gap | P1 |
| ETA | Not computed | Full gap | P2 |
| Logs per task | Not implemented | Full gap | P1 |
| Priority | Not implemented | Full gap | P2 |

---

## 4. Authentication Migration Plan

### Phase 1: Add OAuth Infrastructure (Week 1–2)

**Backend changes:**

```python
# New: app/auth/oauth.py
from fastapi import APIRouter, HTTPException
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(name='google', ...)
oauth.register(name='github', ...)
```

Add to `requirements.txt`:
- `authlib`
- `python-jose` (JWT)
- `httpx-oauth` (or use authlib directly)

**New dependencies:**

| Package | Purpose |
|---------|---------|
| authlib | OAuth 2.0 client + server |
| python-jose | JWT token generation/validation |
| httpx-oauth | Alternative OAuth flow |

### Phase 2: New Database Models (Week 1–2)

```python
# New: app/database/oauth_models.py or add to models.py

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True)
    created_at = Column(DateTime, default=...)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    name = Column(String(255))
    avatar_url = Column(String(500))
    google_id = Column(String(255), unique=True, nullable=True)
    github_id = Column(String(255), unique=True, nullable=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    role = Column(String(50), default='member')  # member / admin / owner
    created_at = Column(DateTime, default=...)
    last_login_at = Column(DateTime, nullable=True)

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    token = Column(String(500), unique=True)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=...)
```

### Phase 3: Frontend Auth Flow (Week 2–3)

**New pages:**
- `/login` — OAuth login buttons (Google, GitHub)
- `/auth/callback` — OAuth callback handler
- `/auth/github/callback` — GitHub OAuth callback

**Remove:**
- `LoginForm` component (API key form)
- `auth-context.ts` `decodeRole` function
- `demo-data.ts` demo API keys
- API key login from auth provider

### Phase 4: Hybrid Auth (Week 3)

Keep API key auth for machine-to-machine (CI pipeline tokens). New flow:

```
User Login: Google OAuth (browser) → JWT session
Machine Auth: X-API-Key header (CI/CD) → unchanged
```

---

## 5. GitHub Integration Plan

### Current: REST client with personal access token

### Phase 1: GitHub App OAuth (Week 2–3)

**New model:**
```python
class GitHubInstallation(Base):
    __tablename__ = "github_installations"
    id = Column(Integer, primary_key=True)
    installation_id = Column(Integer, unique=True)
    account_login = Column(String(255))
    account_type = Column(String(50))  # User or Organization
    repos_selected = Column(Text)  # JSON array
    permissions = Column(Text)  # JSON
    access_token = Column(String(500))
    token_expires_at = Column(DateTime)
    created_at = Column(DateTime)
```

### Phase 2: Webhook Ingestion (Week 3–4)

**New endpoints:**
```
POST /api/github/webhook — Receive workflow_run, check_run events
```

**Handler flow:**
```
GitHub Webhook → Verify signature → Parse event type
  ├── workflow_run.completed (failure)
  │     → Create Failure record
  │     → Fetch logs
  │     → Submit analysis task
  │     → Send notification
  │     → Emit WebSocket event
  ├── check_run.completed
  │     → Update repository status
  └── push
        → Trigger re-indexing
```

### Phase 3: Repository Sync (Week 3–4)

**New endpoints:**
```
GET  /api/github/repositories — List connected repos
POST /api/github/sync — Sync all repositories from installations
GET  /api/github/repositories/{id}/workflows — List workflows
GET  /api/github/repositories/{id}/runs — List recent runs
```

---

## 6. Slack Integration Plan

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  GitHub     │────▶│  Backend     │────▶│  Slack API  │
│  Webhook    │     │  (FastAPI)   │     │  (httpx)    │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐
                    │  Notification│
                    │  Dispatcher  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Slack   │ │  Email   │ │  Splunk  │
        │  Channel │ │  SMTP    │ │  HEC     │
        └──────────┘ └──────────┘ └──────────┘
```

### New Models

```python
class SlackIntegration(Base):
    __tablename__ = "slack_integrations"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    team_name = Column(String(255))
    team_id = Column(String(255))
    access_token = Column(String(500))
    bot_user_id = Column(String(100))
    channels = Column(Text)  # JSON: [{id, name}]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime)

class NotificationChannel(Base):
    __tablename__ = "notification_channels"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    type = Column(String(50))  # slack / email / webhook
    config = Column(Text)  # JSON
    events = Column(Text)  # JSON: event type filter
    is_active = Column(Boolean, default=True)
```

### Events to Notify

```
workflow_failed        → channel + email
workflow_passed        → email (optional channel)
investigation_started  → channel
root_cause_found       → channel
fix_generated          → channel
validation_passed      → channel
validation_failed      → channel + email
pr_created             → channel
pr_merged              → channel
```

---

## 7. Splunk Integration Plan

### Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Backend    │────▶│  Splunk HEC  │────▶│  Splunk     │
│  Events     │     │  (HTTP)      │     │  Index      │
└─────────────┘     └──────────────┘     └─────────────┘
```

### New Module

```python
# app/integrations/splunk.py
class SplunkClient:
    def __init__(self, hec_url, hec_token):
        self.client = httpx.AsyncClient(...)
    
    async def send_event(self, event: dict, sourcetype: str):
        # POST to HEC endpoint
        pass

    async def send_failure(self, failure: Failure, analysis: dict):
        await self.send_event({
            "repository": failure.repository_name,
            "workflow": failure.workflow_name,
            "error": failure.error_message,
            "root_cause": analysis.get("root_cause"),
            "confidence": analysis.get("confidence"),
            "timestamp": failure.detected_at.isoformat(),
            "event_type": "ci_failure",
        }, sourcetype="ci_agent:failure")

    async def send_investigation(self, ...): ...
    async def send_validation(self, ...): ...
    async def send_agent_activity(self, ...): ...
```

### New Model

```python
class SplunkIntegration(Base):
    __tablename__ = "splunk_integrations"
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey('organizations.id'))
    hec_url = Column(String(500))
    hec_token = Column(String(500))
    index = Column(String(100))
    is_active = Column(Boolean, default=True)
```

### Sourcetypes

| Sourcetype | Data |
|------------|------|
| `ci_agent:failure` | CI/CD failure detected |
| `ci_agent:investigation` | Root cause analysis results |
| `ci_agent:validation` | Validation pipeline results |
| `ci_agent:agent_activity` | Agent decision records |
| `ci_agent:pr` | PR creation events |
| `ci_agent:metrics` | Operational metrics (MTTR, etc.) |

---

## 8. Notification Architecture

### New Module

```python
# app/notifications/dispatcher.py
class NotificationDispatcher:
    def __init__(self):
        self.channels = []
    
    def register(self, channel: NotificationChannel):
        self.channels.append(channel)
    
    async def dispatch(self, event: str, payload: dict):
        for channel in self.channels:
            if event in channel.events:
                await channel.send(payload)
```

### Email Notifications

```python
# app/notifications/email.py
class EmailNotifier:
    def __init__(self, smtp_host, smtp_port, username, password):
        ...
    
    async def send_failure_alert(self, to: str, failure: dict):
        """
        Subject: CI Failed: frontend-app (run #142)
        Body:
          Repository: frontend-app
          Workflow: CI
          Branch: main
          Commit: a1b2c3d
          Failure: Missing environment variable: API_KEY
          Investigation: https://app.example.com/analysis/42
        """
    
    async def send_success_notification(self, to: str, result: dict):
        """
        Subject: CI Passed: frontend-app (run #143)
        Body:
          Repository: frontend-app
          Workflow: CI
          Branch: main
          Commit: e4f5g6h
          Duration: 3m 12s
          Tests: 140 passed
        """
```

---

## 9. Real-Time Architecture

### Recommended: Server-Sent Events (SSE)

**Why SSE over WebSocket:**
- Simpler to implement (HTTP-only, no upgrade)
- Works natively with FastAPI StreamingResponse
- Automatic reconnection via EventSource API
- Unidirectional (server→client) — sufficient for dashboard
- No connection overhead of WebSocket for this use case

### Implementation

#### Backend: SSE Manager

```python
# app/realtime/sse_manager.py
import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

class SSEManager:
    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = {}
    
    def subscribe(self, channel: str) -> asyncio.Queue:
        if channel not in self._subscribers:
            self._subscribers[channel] = []
        queue = asyncio.Queue()
        self._subscribers[channel].append(queue)
        return queue
    
    def unsubscribe(self, channel: str, queue: asyncio.Queue):
        if channel in self._subscribers:
            self._subscribers[channel].remove(queue)
    
    async def publish(self, channel: str, event: str, data: dict):
        if channel in self._subscribers:
            for queue in self._subscribers[channel]:
                await queue.put({"event": event, "data": data})

sse_manager = SSEManager()

@router.get("/events")
async def sse_endpoint(request: Request):
    queue = sse_manager.subscribe("global")
    
    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"event: {msg['event']}\ndata: {json.dumps(msg['data'])}\n\n"
                except asyncio.TimeoutError:
                    yield f"event: heartbeat\ndata: \n\n"
        finally:
            sse_manager.unsubscribe("global", queue)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
```

#### Events

| Event | Channel | Payload |
|-------|---------|---------|
| `workflow_started` | global/org | {repo, workflow, run_id} |
| `workflow_failed` | global/org | {repo, workflow, run_id, error} |
| `investigation_started` | repo:{name} | {run_id} |
| `root_cause_found` | repo:{name} | {run_id, root_cause, confidence} |
| `fix_generated` | repo:{name} | {run_id, summary, confidence} |
| `validation_started` | repo:{name} | {run_id, stages: [...]} |
| `validation_stage_complete` | repo:{name} | {stage, status, duration} |
| `validation_complete` | repo:{name} | {status, confidence} |
| `pr_created` | global/org | {repo, pr_number, title} |
| `pr_merged` | global/org | {repo, pr_number} |
| `task_completed` | org:{org_id} | {task_id, type, status} |
| `repository_indexed` | org:{org_id} | {repo, files, chunks} |

#### Frontend: EventSource Hook

```typescript
// frontend/src/hooks/useSSE.ts
export function useSSE() {
  const { data, setData } = useAgent()
  
  useEffect(() => {
    const token = getAuthToken()
    const eventSource = new EventSource(`/api/events?token=${token}`)
    
    eventSource.addEventListener('workflow_failed', (e) => {
      const payload = JSON.parse(e.data)
      // Update dashboard, trigger notification, etc.
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    })
    
    eventSource.addEventListener('investigation_started', (e) => {
      // Show real-time investigation progress
    })
    
    return () => eventSource.close()
  }, [])
}
```

#### Removal of Polling

Once SSE is in place, remove:
- `refetchInterval: 30_000` from dashboard queries
- `refetchInterval: 10_000` from task list
- `refetchInterval: 2_000` from running task polling

---

## 10. Database Changes Required

### New Tables

| Table | Purpose | Phase |
|-------|---------|-------|
| `organizations` | Multi-tenant orgs | 1 |
| `users` | User accounts (OAuth) | 1 |
| `sessions` | JWT session tracking | 1 |
| `github_installations` | GitHub App installations | 2 |
| `slack_integrations` | Slack workspace connections | 3 |
| `splunk_integrations` | Splunk HEC configuration | 4 |
| `notification_channels` | Notification routing rules | 3 |
| `notification_log` | Notification delivery history | 3 |
| `webhook_events` | Incoming webhook event log | 2 |
| `investigation_stages` | Individual stage progress | 2 |

### Modified Tables

| Table | Change | Phase |
|-------|--------|-------|
| `repositories` | Add `organization_id`, `github_installation_id`, `last_workflow_status` | 2 |
| `failures` | Add `organization_id`, `github_run_id` | 2 |
| `tasks` | Add `organization_id`, `priority`, `progress`, `eta_seconds` | 2 |
| `api_keys` | Add `user_id` FK, remove `role` (derive from org role) | 1 |

### Schema Migration Strategy

- Use Alembic autogenerate for new tables
- Manual migration scripts for existing data
- Backfill organization_id with a default org for existing data
- Deploy with zero-downtime: add columns as nullable first, backfill, then set NOT NULL

---

## 11. UI/UX Redesign Plan

### Design Principles

1. **Operational clarity** — Every element serves a purpose; no decorative flourishes
2. **Event-driven** — UI updates in response to real events, not timers
3. **Progressive disclosure** — Show summary first, expand for details
4. **Agent transparency** — User always knows what the AI is doing and why
5. **Enterprise credibility** — Borrow from Datadog, Sentry, Linear, Vercel

### What to Remove

| Component | File | Reason | Replace With |
|-----------|------|--------|-------------|
| `StarsBackground` | components/StarsBackground.tsx | Decorative, no operational value | Remove entirely |
| `ParticleField` | components/ParticleField.tsx | Decorative | Remove entirely |
| `AnimatedBackground` | components/AnimatedBackground.tsx | Decorative variants per page | Remove entirely |
| `3DBackground` | components/3DBackground.tsx | Three.js for zero value | Remove entirely |
| `TiltCard` | components/tilt-card.tsx | Decorative hover effect | Remove; use flat GlassCard |
| `AnimatedCounter` | components/AnimatedCounter.tsx | Decorative animation | Use plain text numbers |
| `framer-motion` on page transitions | Various pages | Added latency to navigation | Use CSS transitions or remove |

### What to Keep

| Component | File | Reason |
|-----------|------|--------|
| `GlassCard` | components/GlassCard.tsx | Clean card UI |
| `TabNav` | components/tab-nav.tsx | Functional navigation |
| `MetricCard` | components/metric-card.tsx | Operational metric display |
| `ActivityFeed` | components/activity-feed.tsx | Core activity stream |
| `BranchHistory` | components/branch-history.tsx | Decision tree visualization |
| `DecisionTimeline` | components/decision-timeline.tsx | Agent reasoning trail |
| `PipelineVisualization` | components/PipelineVisualization.tsx | Pipeline graph |
| `StatusBadge` | components/status-badge.tsx | Status indicators |
| `StaggerGrid` | components/stagger-grid.tsx | Layout grid |
| `EmptyState` | components/empty-state.tsx | Useful placeholder |
| `ErrorBanner` | components/error-banner.tsx | Error states |
| `LoadingSpinner` | components/LoadingSpinner.tsx | Loading state |

### New Components Needed

| Component | Purpose | Priority |
|-----------|---------|----------|
| `InvestigationPipeline` | 8-stage investigation progress with per-stage status/duration/logs | P0 |
| `ValidationPipeline` | 6-stage validation pipeline with status/duration/logs per stage | P0 |
| `RealTimeStatus` | Global status bar showing live agent activity | P0 |
| `NotificationConfig` | Slack/email notification settings form | P1 |
| `RepoSelector` | GitHub repository multi-select | P0 |
| `OAuthButtons` | Google/GitHub OAuth sign-in buttons | P0 |
| `WorkflowTimeline` | Timeline of workflow runs per repo | P1 |
| `MetricsChart` | Real metrics (MTTR, success rate trends) | P1 |
| `TaskProgress` | Task progress with ETA and logs | P1 |
| `AgentReasoning` | Expandable agent reasoning panel | P1 |

### Visual Style Changes

| Current | Target |
|---------|--------|
| Dark gradient backgrounds | Flat dark (#0d1117-inspired) |
| Decorative 3D elements | Clean data visualizations |
| Animated entry effects | Instant rendering |
| Fade transitions | Instant page navigation |
| Tilt cards | Flat cards |
| Decorative borders | Functional borders (status-colored) |
| Sparkle icons | Functional icons (status, severity, type) |

---

## 12. Page-by-Page Refactor Plan

### 12.1 Login Page (`login.tsx`)

**Current:** API key form + decorative product showcase + SelfHealingDemo component + AnimatedBackground

**Target:**
- Google OAuth button
- GitHub OAuth button
- Clean centered layout (no demo, no 3D)
- Optional "I have an API key" expandable section for CI token auth

**Remove:**
- `LoginForm` component (API key form as primary)
- `SelfHealingDemo` component
- `AnimatedBackground`
- framer-motion variants
- GitHub icon decoration (keep actual GitHub OAuth button)

### 12.2 Dashboard / Overview (`dashboard.tsx`)

**Current:** 6 tabs, fake data fallbacks, multiple decorative components, combined live+fake activity feed

**Target:**
- Remove all `demo*` fallbacks — show error state when API fails
- Remove `adjustedSummary`/`adjustedRepos` — API is source of truth
- Replace demo activity filter with real API-based activity endpoint
- Integrate SSE for live updates
- Remove `PipelineVisualization` `autoRun` — show real pipeline
- Remove `TiltCard`, `AnimatedBackground`
- Remove `AnimatedCounter` wave effects

**SSE integration:**
```typescript
// Replace React Query polling with SSE-driven invalidation
const eventSource = new EventSource('/api/events')
eventSource.addEventListener('dashboard_update', () => {
  queryClient.invalidateQueries({ queryKey: ['dashboard'] })
})
```

### 12.3 Analysis Page (`analysis.tsx`)

**Current:** Form-based submission, demo scenario selector, 3-phase investigation with auto-advance, fake candidates

**Target:**
- Remove demo scenario selector (dropdown with 6 failures)
- Remove `demoWorkflowLogsByType` and `demoCandidates` imports
- Remove `handleLoadExample` — real data only
- Replace 3 phases with 8-stage Investigation Pipeline component
- Add SSE-driven progress updates per stage
- Add real evidence display (from API response)
- Add confidence graph across stages
- Auto-load when failure is clicked from dashboard (via URL params or state)

### 12.4 Validation Page (`validation.tsx`)

**Current:** Static pass/fail display, health impact computation, decision breakdown card

**Target:**
- Replace static result with 6-stage Validation Pipeline component
- Each stage shows: status, duration, logs (expandable), result
- SSE-driven stage completion updates
- Real confidence scoring per stage (not computed from fake healthDelta)
- Add "rerun validation" button linked to API

### 12.5 Settings Page (`settings.tsx` — NEW)

**Current:** Does not exist (no settings page found)

**Target:**
```typescript
// Connected Accounts section
- Google: Connect / Disconnect (shows email when connected)
- GitHub: Connect / Disconnect (shows installations)
- Slack: Add to Slack button → channel selector
- Splunk: HEC URL + token form

// Notifications section
- Email notifications toggle (per event type)
- Slack channel selector (per event type)
- Teams (future-ready placeholder)

// Repository Rules section
- Auto-fix: enable/disable per repo
- Auto-PR: enable/disable per repo
- Escalation: threshold config
- Monitoring interval config
```

### 12.6 Tasks Page (`tasks.tsx`)

**Current:** Uses `demoTasks` for fake data

**Target:**
- Remove `demoTasks` — use `useTaskList()` API
- Add real-time progress via SSE
- Add task detail view with logs
- Add ETA/progress bar per task
- Add retry action for failed tasks

### 12.7 Indexing Page (`indexing.tsx`)

**Current:** Likely uses `demoIndexedRepos`

**Target:**
- Remove `demoIndexedRepos` — use `useIndexStatus` API
- Add trigger re-index button
- Show real indexing progress
- Show file count, chunk count, last indexed time

### 12.8 PR Page (`pr.tsx`), Review Page (`review.tsx`), Retry Page (`retry.tsx`)

**Current:** Each has demo/mock data patterns

**Target for all:**
- Remove all demo data fallbacks
- Use real API endpoints
- Add SSE-driven updates for in-progress operations
- Add error handling for failed operations

---

## 13. Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| OAuth integration breaks existing auth | Medium | High | Keep API key auth as fallback; feature flag OAuth |
| Demo data removal breaks tests | High | Medium | Update test assertions to use mock API responses |
| SQLite → PostgreSQL migration breaks queries | Low | High | Test all queries against PG in staging before prod |
| SSE deployment requires sticky sessions/Redis pubsub | Medium | Medium | Use Redis pubsub for multi-process SSE propagation |
| LLM providers (DeepSeek/Groq) become unavailable | Low | High | Circuit breaker already implemented; fallback to cached response |
| GitHub API rate limiting on webhook processing | Medium | Medium | Implement webhook queue with 5s debounce per repo |
| User adoption drops without OAuth | High | High | Highest priority — OAuth is P0 |
| Removing 3D/decorative components takes time | Low | Low | Straightforward deletion; no functional impact |
| Frontend bundle size increases with SSE library | Low | Low | Native EventSource — no library needed |
| Notification spam from frequent events | Medium | Low | Rate-limit notifications; per-event-type configurable throttling |

---

## 14. Implementation Roadmap

### Phase 1: Foundation (Weeks 1–4) — P0 Items

**Goal:** Viable production authentication, real repositories from GitHub, basic real-time

| Week | Backend | Frontend |
|------|---------|----------|
| 1 | OAuth models (User, Org, Session), Google OAuth endpoints, GitHub OAuth endpoints | Remove API key login; add OAuth buttons |
| 2 | JWT session management, hybrid auth (OAuth + API keys), rate limiter per-user | New login page, OAuth callback handlers, session storage |
| 3 | GitHub App webhook ingestion (workflow_run.completed), failure auto-detection, log fetching | Repository page with real repos from API, SSE hook |
| 4 | SSE manager, event publishing from workflows, dashboard event stream | Real-time dashboard updates, remove all polling |

**Deliverables:**
- Users can sign in with Google/GitHub
- GitHub repositories auto-sync on installation
- Dashboard shows real repos with live workflow status
- SSE replaces React Query polling

### Phase 2: Autonomous Investigation (Weeks 5–8)

**Goal:** Real failure detection triggers auto-investigation with visible progress

| Week | Backend | Frontend |
|------|---------|----------|
| 5 | GitHub webhook → auto-submit analysis task, investigation stage tracking model | Investigation Pipeline component (8 stages) |
| 6 | Stage-level SSE events from workflows, real evidence collection | Analysis page shows real-stage progress via SSE |
| 7 | Fix generation workflow improvements, patch validation integration | Fix display with real patch diff, confidence score |
| 8 | Validation pipeline stage tracking, SSE events per stage | Validation Pipeline component (6 stages) |

**Deliverables:**
- CI failure auto-triggers investigation
- User sees live investigation progress (8 stages)
- Root cause, evidence, and confidence shown per stage
- Fix and validation pipeline visible

### Phase 3: Notifications & Settings (Weeks 9–12)

**Goal:** Slack integration, email notifications, full settings page

| Week | Backend | Frontend |
|------|---------|----------|
| 9 | Slack OAuth, channel selection, message formatting | Settings page: Connected accounts section |
| 10 | Notification dispatcher, email SMTP integration, notification log | Settings: Notification config |
| 11 | Repository rules, auto-fix policies, escalation config | Settings: Repository rules |
| 12 | Splunk HEC integration, event sourcetypes | Settings: Splunk config (admin) |

**Deliverables:**
- Slack notifications for all CI events
- Email notifications for failures + successes
- Full settings page with connected accounts
- Splunk integration for observability

### Phase 4: Analytics & Polish (Weeks 13–16)

**Goal:** Real operational metrics, remove all demo/fake data, UI refinement

| Week | Backend | Frontend |
|------|---------|----------|
| 13 | MTTR computation, auto-heal rate, failure categories | Analytics tab with real metrics, trend charts |
| 14 | PR acceptance rate tracking, repository health trends | Dashboard KPI cards with real data |
| 15 | Remove all demo-data.ts usage, harden error handling | UI audit: remove decorative components, add clean operational UI |
| 16 | Benchmark and load testing, documentation | Final UI polish, accessibility audit |

**Deliverables:**
- All demo data eliminated
- Real analytics metrics
- Clean, operational UI
- Production-ready performance

### Phase 5: Scale & Enterprise (Weeks 17–20)

**Goal:** Multi-tenant, PostgreSQL migration, worker queue

| Week | Backend | Frontend |
|------|---------|----------|
| 17 | PostgreSQL migration (SQLite→PG), org-scoped isolation | Multi-org context switcher |
| 18 | Redis-backed task queue (replaces in-memory), worker pool | Task system with real ETA/progress |
| 19 | Rate limiter with Redis (replaces in-memory), distributed SSE via Redis pubsub | Feature flags per org |
| 20 | Load testing (1000 concurrent workflows), final security audit | Final accessibility and performance optimization |

**Deliverables:**
- PostgreSQL production database
- Redis-backed persistent queue
- Multi-tenant support
- Distributed, scalable architecture

### Effort Estimate

| Phase | Backend (person-weeks) | Frontend (person-weeks) | Total |
|-------|----------------------|------------------------|-------|
| 1: Foundation | 4 | 3 | 7 |
| 2: Autonomous Investigation | 4 | 3 | 7 |
| 3: Notifications & Settings | 3 | 3 | 6 |
| 4: Analytics & Polish | 2 | 3 | 5 |
| 5: Scale & Enterprise | 4 | 2 | 6 |
| **Total** | **17** | **14** | **31** |

---

## Summary of Critical Actions (Next Week)

1. **Add OAuth models** (User, Organization, Session) — unblocks everything
2. **Remove API key login as primary** — replace with OAuth buttons
3. **Add GitHub App webhook endpoint** — enables auto-detection of failures
4. **Implement SSE manager** — foundation for all real-time features
5. **Delete demo-data.ts** — forces all pages to use real API data

These five actions alone transform the project from a demo to a real product. Everything else builds on this foundation.
