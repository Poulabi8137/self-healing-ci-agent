# Phase 1 Design Review — Complexity Reduction Analysis

> Evaluate the Phase 1 Execution Plan for unnecessary complexity.
> Constraint: No rewrites, no new audits — only validate that the plan is not over-engineered.

---

## 1. Database Schema — Merge Analysis

### Investigation Stages + Evidence → JSON Column

**Proposed tables:**
- `investigations` (id, failure_id, repository_id, organization_id, status, ...)
- `investigation_stages` (id, investigation_id, stage, status, started_at, completed_at, duration_ms, result, error)
- `investigation_evidence` (id, investigation_stage_id, type, source, content, confidence)

**Verdict: OVER-ENGINEERED. Merge into a single JSON column.**

**Rationale:**
- Phase 1 does not need to query "all investigations that failed at stage X" or "find all evidence of type Y across investigations"
- Phase 1 needs to display a single investigation with its 8 stages and their evidence — the stages are always read together
- A JSON column with the full stage array eliminates 2 tables, 2 routers, 2 services, and all join queries
- The stage schema is fixed (8 known stages) — no ad-hoc querying needed
- PostgreSQL and SQLite both support JSON querying if analytics is needed later

**Replacement schema:**

```sql
CREATE TABLE investigations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    failure_id INTEGER NOT NULL REFERENCES failures(id),
    repository_id INTEGER NOT NULL REFERENCES repositories(id),
    status TEXT NOT NULL DEFAULT 'detecting',
    root_cause TEXT,
    error_category TEXT,
    confidence REAL,
    summary TEXT,
    -- JSON array of stage objects, each with nested evidence
    stages TEXT NOT NULL DEFAULT '[]',
    -- Top-level convenience fields (denormalized from latest stage)
    current_stage TEXT,
    current_stage_status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
```

Each stage object in the JSON array:
```json
{
  "id": "detection",
  "label": "Failure Detection",
  "status": "completed",
  "started_at": "...",
  "completed_at": "...",
  "duration_ms": 1500,
  "result": {},
  "error": null,
  "evidence": [
    {"type": "log_snippet", "source": "github_actions", "content": "...", "confidence": 0.95}
  ]
}
```

**What this eliminates:**
- 2 database tables
- `app/investigation/service.py` (separate CRUD for stages/evidence)
- `app/investigation/schemas.py` (stage/evidence schemas)
- Join queries in API layer
- Frontend service layer for stages/evidence

**What we lose:** Ability to query evidence types across investigations. **Not needed in Phase 1.**

### Organizations

**Proposed:** `organizations` table, org_id FK on users, repositories, investigations, failures, audit_logs. First user auto-creates org.

**Verdict: DEFER to Phase 2. Remove all organization references from Phase 1.**

**Rationale:**
- Phase 1 is a single-tenant deployment. Multi-tenancy adds complexity everywhere: every query must filter by org_id, every API must check org access, every UI element must consider org context
- No Phase 1 feature requires org boundaries — users don't collaborate across orgs yet
- The auto-org-creation logic is itself complexity (name? slug? what if first user signs in twice?)
- Simple alternative: the deployment itself is the "org." First user becomes admin. No org table.

**Simplified approach:**
- `users.role` = `admin` or `member`
- First user to sign in via Google OAuth gets `role = 'admin'`
- No `organizations` table
- No `organization_id` columns
- All data belongs to the single deployment

**What this eliminates:**
- 1 database table
- Organization creation logic in bootstrap
- organization_id FK on at least 5 tables
- org_id filter in every API query
- Org context in frontend state
- Org switcher UI component

**What we lose:** Multi-tenant isolation, separate org billing, org-level config. **Not needed in Phase 1.**

### Audit Logs

**Proposed:** `audit_logs` table with organization_id, user_id, action, resource_type, resource_id, details, ip_address, user_agent, created_at.

**Verdict: KEEP but simplify.** Remove `organization_id` (no orgs). Remove `ip_address` and `user_agent` (will always be the same deployment; network-level info adds complexity without value in Phase 1).

**Simplified:**

```sql
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES users(id),
    action TEXT NOT NULL,
    resource_type TEXT NOT NULL,
    resource_id TEXT,
    details TEXT,  -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. Session Architecture — Three Options Compared

### Option A: JWT-only (httpOnly cookie)

| Aspect | Detail |
|--------|--------|
| Storage | httpOnly cookie (not accessible to JS) |
| Expiry | 24 hours |
| Revocation | None (or add in-memory blocklist checked on each request) |
| DB queries | Zero per request |
| CSRF | No need — cookie is set by backend, not JS |
| XSS | Token not accessible to JS |
| Complexity | Minimal |

### Option B: JWT + Refresh Token

| Aspect | Detail |
|--------|--------|
| Storage | Access token in memory, refresh token in httpOnly cookie |
| Expiry | Access: 15min, Refresh: 7 days |
| Revocation | Revoke refresh token from DB |
| DB queries | One per refresh (~every 15 min per user) |
| Complexity | Medium (token rotation logic, concurrent refresh handling) |

### Option C: Database-backed Sessions

| Aspect | Detail |
|--------|--------|
| Storage | Session ID in httpOnly cookie |
| Expiry | Configurable (e.g., 24h inactivity) |
| Revocation | Delete session row — instant |
| DB queries | One per request |
| Complexity | Low (no JWT library needed) |

### Verdict: OPTION A (JWT-only with httpOnly cookie) — simplest production-safe approach

**Why not Option B:** Refresh tokens add a second token lifecycle, race conditions on concurrent refreshes, and storage complexity. The benefit (session duration > 24h) is not needed for Phase 1 — CI tool users check in periodically; 24h sessions are fine.

**Why not Option C:** DB query on every request adds latency and load. For a CI tool with moderate traffic this is acceptable, but JWT eliminates the query with minimal trade-off. The only advantage of DB sessions (instant revocation) can be approximated in Option A with a small in-memory blocklist that's checked before JWT validation.

**If revocation is needed:** Add a 10-line in-memory set `revoked_tokens = set()` with a `before_request` middleware check. Clean expired entries on a timer. This covers the "admin revoked session" case without a DB table.

**Simplified session model — nothing to store in DB:**

```python
# app/auth/jwt.py (new file, replaces sessions table)
def create_token(user_id: int) -> str: ...
def verify_token(token: str) -> dict: ...  # returns user payload or raises
```

**What this eliminates:**
- `sessions` database table entirely
- Session CRUD service
- Session cleanup background job
- Session expiry middleware complexity
- Session serialization/deserialization overhead

---

## 3. SSE Architecture — WebSocket Comparison

### Phase 1 Requirements

| Requirement | Direction | Frequency |
|-------------|-----------|-----------|
| Investigation stage update | Server → Client | ~1 per stage (8 total per investigation) |
| Dashboard metric invalidation | Server → Client | On event |
| Activity stream event | Server → Client | On event |
| Workflow status change | Server → Client | On webhook |
| Repository status update | Server → Client | On webhook |

**None require client → server messaging.** All communication is unidirectional from backend to frontend.

### SSE vs WebSocket

| Factor | SSE | WebSocket | Verdict |
|--------|-----|-----------|---------|
| **Direction** | Server→Client only | Bidirectional | SSE matches Phase 1 needs exactly |
| **Browser support** | Native EventSource, auto-reconnect | Native WebSocket, manual reconnect | SSE wins |
| **Throughput** | Sufficient for 1-10 events/sec | 1000+ events/sec | SSE sufficient |
| **Complexity** | FastAPI StreamingResponse + asyncio.Queue | WebSocket endpoint + connection manager | SSE simpler |
| **Proxy compatibility** | HTTP/1.1, HTTP/2 | Requires upgrade header; broken by some proxies | SSE wins |
| **Library** | None needed | `websockets` (already in venv) | SSE simpler |
| **Auto-reconnect** | Built-in (EventSource) | Must implement manually | SSE wins |
| **Last-event-id** | Built-in | Must implement manually | SSE wins |

### Verdict: SSE is CORRECT for Phase 1. WebSocket would be over-engineering.

**One enhancement needed:** The SSE manager must support per-user channels (not just global). Each user should only receive events for their investigations/repos. Add a simple channel map:

```python
channels: dict[str, dict[str, list[asyncio.Queue]]] = {
    "user:42": {"investigation:7": [queue1, queue2], "global": [queue3]},
    "user:17": {"investigation:12": [queue4]},
}
```

---

## 4. GitHub Integration — Minimum Viable Architecture

### Required: Automated Failure Detection

To automatically detect a GitHub Actions workflow failure, the system needs:

1. **Receive an event** when a workflow completes with failure
2. **Know which repo** the failure belongs to
3. **Fetch the logs** for analysis
4. **Trigger the investigation pipeline**

### Options for Event Reception

| Option | Receive Events | Works Without Polling | Production-Grade | Complexity |
|--------|---------------|----------------------|------------------|------------|
| **A. GitHub App + Webhooks** | Yes — push-based | Yes | Yes | Medium |
| **B. GitHub Personal Access Token + Polling** | No — periodic API calls | No | No | Low |
| **C. GitHub Actions `workflow_run` webhook (manual config)** | Yes — push-based | Yes | Fragile | Low |

### Verdict: OPTION A (GitHub App + Webhooks) is the minimum for Phase 1.

**Why not Option B:** Polling fails the product vision of "autonomous real-time detection." Worst case: 60s delay before detecting a failure. Also requires users to create and manage tokens — not production-grade.

**Why not Option C:** Requires every user to manually configure a webhook in every repo. Not a product experience — it's a workaround. The product must handle webhook registration automatically.

### What can be simplified in the GitHub integration

**Defer to Phase 2:**
- `POST /github/repositories/sync` endpoint (manual sync; webhook events will keep things current in Phase 1)
- Multiple GitHub organizations per user (one installation is enough for Phase 1)
- Repository health score computation (show simple status for now)

**Keep in Phase 1:**
- GitHub App OAuth installation flow
- Webhook receiver with HMAC verification
- `workflow_run.completed` event handler
- Log fetching via GitHub API
- Auto-submit to analysis workflow

This is already the minimum. No further simplification possible without breaking the core product promise.

---

## 5. Webhook → Analysis Flow — Reduce Redundancy

**Proposed flow:** Webhook event → create Failure → submit detection task → detection workflow creates Investigation → submit analysis task

**Question:** Is the `detection_workflow.py` necessary, or can the webhook handler directly submit the analysis task?

**Analysis:**
- The detection workflow does: create Failure → fetch logs → submit analysis
- The webhook handler already receives the event and has the run_id
- Fetching logs takes time (network call to GitHub API) — this is the only reason to use a task

**Simplification:** Skip the detection workflow. Have the webhook handler:
1. Create `Failure` record synchronously
2. Create `Investigation` record with empty stages
3. Submit a single "investigate" task to the queue
4. The task handler: fetch logs → run analysis → update investigation stages

**What this eliminates:**
- `app/workflows/detection_workflow.py` file
- `register_handler("detection")` in queue handlers
- One extra task submission per failure
- One extra task state transition

**Why it's safe:** The webhook handler is lightweight (DB writes only). The heavy work (log fetching, LLM analysis) happens in the queue task.

---

## 6. Admin — Can it be simpler?

**Proposed:**
- `app/api/admin_router.py` with users, stats, integrations endpoints
- `pages/admin/dashboard.tsx`, `pages/admin/users.tsx`, `pages/admin/integrations.tsx`
- `components/admin/Sidebar.tsx`, `components/admin/UserRow.tsx`

**Verdict: KEEP the admin endpoints, SIMPLIFY the frontend.**

The admin backend is essential — need role management, user listing, stats. But the frontend can be simpler:

- **Admin dashboard** = a single page with stats cards (active users, investigations today, system health). No separate sub-pages needed for Phase 1.
- **User management** = a table on the admin page. Inline role editing (dropdown next to each user). No separate page.
- **Integration status** = a section on the admin page. Two lines: "GitHub: Connected" / "Not connected".

**Simplified frontend:** One file `pages/admin.tsx` instead of three files + two components.

**What this eliminates:**
- `pages/admin/dashboard.tsx`
- `pages/admin/users.tsx`
- `pages/admin/integrations.tsx`
- `components/admin/Sidebar.tsx`
- `components/admin/UserRow.tsx`
- `components/admin/AuditLogTable.tsx`

---

## 7. Final Simplified Table Summary

### Phase 1 Tables (Before → After)

| Proposed Table | Verdict | Final Table |
|----------------|---------|-------------|
| `organizations` | **DEFER** | — |
| `users` | KEEP | `users` |
| `sessions` | **REMOVE** (use JWT-only) | — |
| `api_keys` | KEEP (modify: add `user_id` FK) | `api_keys` + user_id |
| `github_installations` | KEEP | `github_installations` |
| `repositories` | KEEP (modify: add columns) | `repositories` + fields |
| `webhook_events` | KEEP | `webhook_events` |
| `failures` | KEEP (modify: add columns) | `failures` + fields |
| `investigations` | KEEP | `investigations` |
| `investigation_stages` | **MERGE** into investigations.stages (JSON) | — |
| `investigation_evidence` | **MERGE** into investigations.stages[].evidence (JSON) | — |
| `audit_logs` | KEEP (simplified: no org_id, ip, user_agent) | `audit_logs` (slim) |

**9 tables → 6 tables.**

---

## 8. Approved, Simplified, Deferred

### Approved As-Is

| Component | Why |
|-----------|-----|
| Google OAuth backend | Required for user identity |
| GitHub App OAuth + Webhooks | Minimum for automated failure detection |
| SSE real-time system | Correct architecture; WebSocket adds no value |
| JWT session management | httpOnly cookie, 24h expiry, no DB storage |
| Investigation API + frontend component | Core product experience |
| Activity feed from SSE | Core product experience |
| Demo data removal | Required for credibility |
| Audit logging (simplified) | Required for admin trust |

### Simplified

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| `investigation_stages` table | Separate table | JSON column on `investigations` | 2 tables, 2 services, 2 routers eliminated |
| `investigation_evidence` table | Separate table | Nested JSON in stages[].evidence | (same as above) |
| `sessions` table | DB-backed sessions | JWT-only (no storage) | 1 table, session service eliminated |
| Webhook→analysis flow | Detection workflow + analysis task | Single "investigate" task | 1 workflow file eliminated |
| Admin frontend | 3 pages + 2 components | 1 page with sections | 5 files eliminated |
| Audit log schema | 9 columns | 6 columns (no org_id, ip, user_agent) | Simplified schema |

### Deferred to Phase 2

| Component | Reason |
|-----------|--------|
| `organizations` table | Single-tenant is sufficient for Phase 1 |
| Organization context in UI | No multi-user collaboration needed yet |
| Repository health score computation | Good to have, not blocking MCP |
| Manual repository sync endpoint | Webhooks keep data current; sync can wait |
| Multiple GitHub orgs per user | One installation is sufficient for Phase 1 |
| Redis-backed queue | In-process queue is fine for single-worker deployment |
| Redis pubsub for SSE | In-process queues are fine for single-worker deployment |

---

## 9. Final Phase 1 Architecture (Simplified)

```
                           ┌────────────────┐
                           │   Google OAuth │
                           │   (Login)      │
                           └───────┬────────┘
                                   │ identity
                                   ▼
┌──────────────┐        ┌──────────────────┐        ┌────────────────┐
│   Browser    │◄──────►│   FastAPI        │◄──────►│   GitHub App   │
│   (React)    │  SSE   │   (Backend)      │Webhook │   Webhooks     │
│              │◄───────│                  │◄───────│                │
│  • Dashboard │        │  ┌────────────┐  │        └────────────────┘
│  • Analysis  │        │  │ JWT Auth   │  │
│  • Admin     │        │  │ Middleware │  │        ┌────────────────┐
│  • Settings  │        │  └────────────┘  │        │   GitHub API   │
│              │        │  ┌────────────┐  │◄──────►│   (Log Fetch)  │
└──────────────┘        │  │ SSE        │  │        └────────────────┘
                        │  │ Manager    │  │
                        │  └────────────┘  │        ┌────────────────┐
                        │  ┌────────────┐  │        │   LLM (DeepSeek│
                        │  │ Queue      │  │◄──────►│   /Groq)       │
                        │  │ (in-proc)  │  │        └────────────────┘
                        │  └────────────┘  │
                        │  ┌────────────┐  │        ┌────────────────┐
                        │  │ SQLite DB  │  │        │   FAISS RAG    │
                        │  │ (6 tables) │  │◄──────►│   (Per-repo)   │
                        │  └────────────┘  │        └────────────────┘
                        └──────────────────┘
```

### Database (6 tables, no migrations after Phase 1 start)

```
users              audit_logs            github_installations
├─ id (PK)         ├─ id (PK)            ├─ id (PK)
├─ google_id       ├─ user_id (FK)       ├─ user_id (FK)
├─ email           ├─ action             ├─ installation_id
├─ name            ├─ resource_type      ├─ account_login
├─ avatar_url      ├─ resource_id        ├─ access_token
├─ role            ├─ details (JSON)     ├─ token_expires_at
├─ last_login_at   └─ created_at         └─ created_at

api_keys           failures              investigations
├─ id (PK)         ├─ id (PK)            ├─ id (PK)
├─ user_id (FK)    ├─ github_install..  ├─ failure_id (FK)
├─ key_hash        ├─ repository_id      ├─ repository_id
├─ name            ├─ run_id             ├─ status
├─ role            ├─ job_name           ├─ root_cause
├─ is_active       ├─ error_message      ├─ confidence
└─ created_at      ├─ error_logs         ├─ stages (JSON)
                   ├─ status              ├─ current_stage
                   ├─ detected_at         ├─ current_stage_status
                   ├─ resolved_at         └─ completed_at
                   └─ investigation_id


repositories
├─ id (PK)
├─ github_installation_id (FK)
├─ name
├─ full_name
├─ url
├─ default_branch
├─ is_active
├─ last_workflow_status
├─ last_workflow_run_at
├─ failure_count
└─ is_indexed

webhook_events (logging only — can be pruned)
├─ id (PK)
├─ github_installation_id
├─ event_type
├─ action
├─ payload (JSON)
├─ processed
└─ created_at
```

---

## 10. Summary of Complexity Reduction

| Metric | Original Plan | Simplified | Reduction |
|--------|-------------|------------|-----------|
| Database tables | 12 | 7 | **42%** |
| New backend files | ~15 | ~10 | **33%** |
| New frontend files | ~12 | ~7 | **42%** |
| Files to delete | ~11 | ~11 | 0% (same) |
| API endpoints | ~25 | ~18 | **28%** |
| JWT session storage | DB table | None | **100%** |
| Stage/evidence storage | 2 tables | 1 JSON column | **100%** |
| Organization complexity | Full multi-tenant | None | **100%** |
| Developer time saved | — | — | **~4 days** |
| Total Phase 1 effort | ~30-35 days | ~26-31 days | **~13%** |
| Risk | — | Lower | Fewer moving parts |

### Bottom line

The original plan was solid but had 3 areas of over-engineering: organizations (deferred), session table (unnecessary with JWT), and stage/evidence tables (unnecessary with JSON). Removing these reduces tables by 42%, files by ~33%, and saves ~4 days while maintaining the same product functionality.
