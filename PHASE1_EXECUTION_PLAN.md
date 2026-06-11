# Phase 1 Execution Plan — Minimum Credible Product

> Based on: Target Vision Gap Audit
> Duration: ~6 weeks (one developer) or ~3 weeks (two developers)
> Goal: A production-grade Self-Healing CI/CD Agent that can detect real GitHub failures, investigate them autonomously, and display results live
> Constraint: No code generation in this document

---

## Part 1: Item-by-Item Specification

### Item 1: Google OAuth + User Accounts

**Objective:** Replace API-key-first authentication with Google OAuth. Every user must have a real identity.

#### Database Changes

| Table | Action | Columns |
|-------|--------|---------|
| `organizations` | **NEW** | `id`, `name`, `slug`, `created_at`, `updated_at` |
| `users` | **NEW** | `id`, `organization_id` (FK), `email`, `name`, `avatar_url`, `google_id`, `role` (`member`/`admin`/`owner`), `last_login_at`, `created_at`, `updated_at` |
| `sessions` | **NEW** | `id`, `user_id` (FK), `token` (JWT hash), `expires_at`, `created_at` |
| `api_keys` | **MODIFY** | Add `user_id` (FK, nullable) — associate machine keys with a user |

#### New Backend Files

| File | Purpose |
|------|---------|
| `app/auth/oauth.py` | OAuth client setup (Google), callback handler, token exchange |
| `app/auth/schemas/oauth.py` | Pydantic models for OAuth requests/responses |
| `app/auth/schemas/user.py` | Pydantic models for User CRUD |
| `app/api/oauth_router.py` | `GET /auth/oauth/google`, `GET /auth/oauth/google/callback`, `GET /auth/oauth/logout` |

#### Modified Backend Files

| File | Change |
|------|--------|
| `app/main.py` | Register `oauth_router`; update lifespan to create default org |
| `app/auth/dependencies.py` | Add `require_session` dependency (JWT validation); keep `require_authenticated` for API key fallback |
| `app/config/settings.py` | Add `google_client_id`, `google_client_secret`, `jwt_secret`, `jwt_ttl_seconds` |

#### Dependencies to Add

```
authlib>=1.3.0
python-jose[cryptography]>=3.3.0
```

#### New Frontend Files

| File | Purpose |
|------|---------|
| `pages/login.tsx` | **Rewrite.** Replace API key form with "Sign in with Google" button |
| `lib/auth.tsx` | **Modify.** Swap `login(key)` for `loginWithGoogle()` that stores JWT from OAuth callback |

#### Modified Frontend Files

| File | Change |
|------|--------|
| `lib/auth-context.ts` | Replace `apiKey` with `token`; replace `role` with user object; add `user`, `organization` |
| `lib/api.ts` | Change auth header from `X-API-Key` to `Authorization: Bearer <token>` |
| `components/layout.tsx` | Update user display in header show user name/avatar |
| `lib/types.ts` | Add `User`, `Organization`, `Session` types |

#### Risks

| Risk | Mitigation |
|------|------------|
| Google Cloud Console credentials not configured | Make OAuth optional; fall back to env-var bootstrap admin for setup |
| JWT secret rotation | Add `jwt_secret` to env; document rotation procedure |
| Session expiry UX | Auto-redirect to login with `redirect_uri` query param |

#### Dependencies

| Depends On | Why |
|------------|-----|
| Nothing | This is the foundation; everything depends on it |

---

### Item 2: GitHub OAuth + Repository Linking

**Objective:** Users connect their GitHub account to select repositories for monitoring.

#### Database Changes

| Table | Action | Columns |
|-------|--------|---------|
| `github_installations` | **NEW** | `id`, `user_id` (FK), `installation_id`, `account_login`, `account_type`, `account_avatar`, `repos_selected` (JSON), `permissions` (JSON), `access_token_expires_at`, `created_at`, `updated_at` |
| `repositories` | **MODIFY** | Add `github_installation_id` (FK), `organization_id` (FK), `is_active`, `last_workflow_status`, `last_workflow_run_at`, `health_score` |

#### New Backend Files

| File | Purpose |
|------|---------|
| `app/github/github_app.py` | GitHub App auth flow: JWT generation, installation token retrieval |
| `app/api/github_router.py` | `GET /github/auth`, `GET /github/auth/callback`, `GET /github/repositories`, `POST /github/repositories/sync`, `GET /github/repositories/{id}/workflows` |

#### Modified Backend Files

| File | Change |
|------|--------|
| `app/main.py` | Register `github_router` |
| `app/config/settings.py` | Add `github_app_id`, `github_app_private_key`, `github_app_webhook_secret` |
| `app/auth/dependencies.py` | Add `require_user` dependency that returns User object from session |
| `app/github/github_client.py` | Add method to create authenticated client from installation token |

#### New Frontend Files

| File | Purpose |
|------|---------|
| `components/RepoSelector.tsx` | Multi-select repository picker with search |
| `components/GitHubConnect.tsx` | GitHub connection status + "Connect" button |

#### Modified Frontend Files

| File | Change |
|------|--------|
| `pages/login.tsx` | Add "Connect GitHub" section after Google OAuth |
| `components/layout.tsx` | Add repository count to sidebar |
| `lib/api.ts` | Add `useGitHubRepositories()`, `useSyncRepositories()` hooks |

#### Risks

| Risk | Mitigation |
|------|------------|
| GitHub App not installed | Detect and show "Install GitHub App" button |
| Token expiry | Cache installation token; refresh when expired |
| User has no repos | Show empty state + "Install on more repos" button |

#### Dependencies

| Depends On | Why |
|------------|-----|
| Item 1 (Google OAuth) | GitHub account is linked to a User |
| Item 1 (Organization) | Repos belong to an org |

---

### Item 3: GitHub Webhooks

**Objective:** Receive real-time GitHub events when workflows run, complete, or fail.

#### Database Changes

| Table | Action | Columns |
|-------|--------|---------|
| `webhook_events` | **NEW** | `id`, `github_installation_id`, `event_type` (string), `action`, `payload` (JSON), `headers` (JSON), `processed`, `error`, `created_at`, `processed_at` |

#### New Backend Files

| File | Purpose |
|------|---------|
| `app/github/webhook.py` | Webhook signature verification, event dispatch |
| `app/github/event_handlers.py` | Handlers for `workflow_run`, `check_run`, `push` events |
| `app/api/webhook_router.py` | `POST /api/github/webhook` (no auth — uses HMAC signature) |

#### Modified Backend Files

| File | Change |
|------|--------|
| `app/main.py` | Register `webhook_router` before auth middleware |
| `app/config/settings.py` | Add `github_app_webhook_secret` (already exists in phase 1 item 2) |

#### Risks

| Risk | Mitigation |
|------|------------|
| Malicious webhooks | Verify HMAC-SHA256 signature before processing |
| Webhook flood | Rate-limit: debounce duplicate events within 5s window |
| GitHub API down | Queue events in `webhook_events` table; retry with backoff |
| Missing permissions | Validate GitHub App has `actions:read` on installation |

#### Dependencies

| Depends On | Why |
|------------|-----|
| Item 2 (GitHub OAuth) | Webhook is registered per GitHub App installation |
| Item 1 (Database) | Webhook events are persisted |

---

### Item 4: Real Repository Monitoring

**Objective:** Dashboard repositories tab shows real GitHub repos with live status.

#### Database Changes

| Table | Action | Columns |
|-------|--------|---------|
| `repositories` | **MODIFY** (continued) | Already modified in Item 2 |

#### New Backend Files

None. Extend existing `dashboard_router.py`.

#### Modified Backend Files

| File | Change |
|------|--------|
| `app/api/dashboard_router.py` | `GET /dashboard/repositories` now queries real repos from `repositories` table with join to `github_installations`; add `branch`, `workflow_status`, `last_run`, `failure_count`, `health_score` to response |
| `app/dashboard/metrics_collector.py` | **Update** `collect_repository_metrics()` to read from `repositories` + `failures` tables instead of only `RetryAttempt` |

#### New Frontend Files

| File | Purpose |
|------|---------|
| `components/RepoStatusBadge.tsx` | Workflow status indicator (passing/failing/unknown) |
| `components/RepoHealthBar.tsx` | Health score bar visualization |

#### Modified Frontend Files

| File | Change |
|------|--------|
| `pages/dashboard.tsx` | **Rewrite** `ReposTab` to display real repo data: name, branch, workflow status, last run, failure count, health score |
| `lib/types.ts` | Update `RepositoryInfo` to include `branch`, `workflow_status`, `last_run_at`, `failure_count`, `health_score` |

#### Risks

| Risk | Mitigation |
|------|------------|
| No repos connected | Show empty state with "Connect GitHub" CTA |
| Stale status | Update on each webhook event; show "last checked" timestamp |
| Health score is arbitrary | Start with simple heuristic: `(1 - failures/total_runs) * 100`; refine later |

#### Dependencies

| Depends On | Why |
|------------|-----|
| Item 2 (GitHub OAuth) | Repos come from GitHub App installation |
| Item 3 (Webhooks) | Status updates come from webhook events |

---

### Item 5: Failure Detection

**Objective:** When a workflow fails on GitHub, the system detects it automatically and creates an investigation.

#### Database Changes

| Table | Action | Columns |
|-------|--------|--------|
| `failures` | **MODIFY** | Add `github_installation_id`, `investigation_id` (FK, nullable), `organization_id` (FK) |

#### New Backend Files

| File | Purpose |
|------|---------|
| `app/workflows/detection_workflow.py` | Orchestrates: webhook event → create Failure → fetch logs → submit analysis task |

#### Modified Backend Files

| File | Change |
|------|--------|
| `app/github/event_handlers.py` | Handle `workflow_run.completed` with `conclusion=failure`: create Failure, call detection workflow |
| `app/github/github_client.py` | Add `get_workflow_run_logs()` method to fetch logs via GitHub API |
| `app/queue/handlers.py` | Add `register_handler("detection", handle_detection)` that wraps detection workflow |

#### Risks

| Risk | Mitigation |
|------|------------|
| Logs are too large | Stream and truncate at 1MB |
| Multiple failures for same run | Deduplicate by `(run_id, job_name)` |
| Network error fetching logs | Retry with exponential backoff; circuit breaker already exists |

#### Dependencies

| Depends On | Why |
|------------|-----|
| Item 3 (Webhooks) | Trigger for failure detection |
| Item 2 (GitHub client) | Fetching logs requires GitHub API |

---

### Item 6: Investigation Tracking

**Objective:** Every investigation step is recorded, visible, and live-tracked. Users see what the agent is doing at every stage.

#### Database Changes

| Table | Action | Columns |
|-------|--------|--------|
| `investigations` | **NEW** | `id`, `failure_id` (FK), `repository_id` (FK), `organization_id` (FK), `status` (detecting/analyzing/generating_fix/validating/reviewing/creating_pr/completed/failed), `root_cause`, `error_category`, `confidence`, `summary`, `created_at`, `updated_at`, `completed_at` |
| `investigation_stages` | **NEW** | `id`, `investigation_id` (FK), `stage` (string), `status` (pending/running/completed/failed), `started_at`, `completed_at`, `duration_ms`, `result` (JSON), `error` (text) |
| `investigation_evidence` | **NEW** | `id`, `investigation_stage_id` (FK), `type` (string), `source`, `content` (text), `confidence` (float), `created_at` |

#### New Backend Files

| File | Purpose |
|------|---------|
| `app/investigation/service.py` | CRUD for investigations, stages, evidence |
| `app/investigation/schemas.py` | Pydantic models for investigation API |
| `app/api/investigation_router.py` | `GET /investigations`, `GET /investigations/{id}`, `GET /investigations/{id}/stages`, `GET /investigations/{id}/evidence` |

#### Modified Backend Files

| File | Change |
|------|--------|
| `app/main.py` | Register `investigation_router` |
| `app/workflows/analysis_workflow.py` | Emit stage events (via SSE manager) as each stage completes; persist to `investigation_stages` |
| `app/workflows/fix_generation_workflow.py` | Same: emit stage events, persist |
| `app/workflows/validation_workflow.py` | Same |
| `app/workflows/review_workflow.py` | Same |
| `app/workflows/pr_workflow.py` | Same |

#### New Frontend Files

| File | Purpose |
|------|---------|
| `components/InvestigationPipeline.tsx` | 8-stage visual pipeline with SSE-driven progress, per-stage evidence, confidence trend |
| `components/InvestigationSidebar.tsx` | Active investigation list in sidebar |

#### Modified Frontend Files

| File | Change |
|------|--------|
| `pages/analysis.tsx` | **Rewrite.** Replace demo selector + 3-phase simulation with InvestigationPipeline component. Load data from API. Auto-navigate on webhook. |
| `components/layout.tsx` | Show active investigation count (real, not hardcoded `useState(3)`) |
| `lib/api.ts` | Add `useInvestigation(id)`, `useInvestigationList()` hooks |
| `lib/types.ts` | Add `Investigation`, `InvestigationStage`, `InvestigationEvidence` types |

#### Risks

| Risk | Mitigation |
|------|------------|
| Over-fetching on rapid stage transitions | Batch SSE events with 200ms debounce |
| Investigation never completes | Add timeout (30 min); mark as failed |
| Too many active investigations | Limit to 5 concurrent per repo; queue others |

#### Dependencies

| Depends On | Why |
|------------|-----|
| Item 5 (Failure Detection) | Investigations are created from failures |
| Item 7 (SSE) | Stage updates are pushed via SSE |

---

### Item 7: SSE Real-Time Updates

**Objective:** Every system event is pushed to connected clients in real time. No polling.

#### Database Changes

None.

#### New Backend Files

| File | Purpose |
|------|---------|
| `app/realtime/sse_manager.py` | `SSEManager` class with subscribe/unsubscribe/publish; `/events` SSE endpoint |
| `app/realtime/events.py` | Event type constants and payload schemas |

#### Modified Backend Files

| File | Change |
|------|--------|
| `app/main.py` | Initialize `SSEManager` as singleton; add `/events` endpoint (public, authenticated via query param token) |
| `app/workflows/*.py` (all 6) | After each stage: call `sse_manager.publish(channel, event_type, payload)` |
| `app/queue/worker.py` | Publish `task_status_changed` event on task state transitions |
| `app/github/event_handlers.py` | Publish `workflow_failed`, `workflow_passed` events |

#### New Frontend Files

| File | Purpose |
|------|---------|
| `hooks/useSSE.ts` | `useSSE(channel, token)` hook that creates EventSource, dispatches events, auto-reconnects |

#### Modified Frontend Files

| File | Change |
|------|--------|
| `lib/agent-context.tsx` | Remove manual decision triggers; subscribe to SSE events instead |
| `pages/dashboard.tsx` | Remove all `refetchInterval`; use SSE-driven `queryClient.invalidateQueries()` |
| `pages/analysis.tsx` | Subscribe to investigation-specific SSE channel for live stage updates |
| `pages/validation.tsx` | Subscribe to validation-specific SSE channel for live stage updates |
| `components/activity-feed.tsx` | Use SSE event stream instead of combined demo+live array |

#### Risks

| Risk | Mitigation |
|------|------------|
| SSE connection drops | Browser EventSource auto-reconnects; use `last-event-id` for missed events |
| Too many connections | One SSE connection per user; multiplex channels via query param |
| Memory from unclosed connections | Remove queues on disconnect; heartbeat timeout |
| Multi-process deployment | Use Redis pubsub to broadcast events across workers (Phase 2; in-process queues fine for single worker) |

#### Dependencies

| Depends On | Why |
|------------|-----|
| Item 1 (Auth) | SSE endpoint must authenticate users via JWT query param |

---

### Item 8: Demo Data Removal

**Objective:** All fake data, decorative components, and demo-only code is removed from the codebase.

#### No Database Changes

#### New Backend Files

None.

#### Modified Backend Files

None.

#### Files to Delete

| File | Reason |
|------|--------|
| `frontend/src/lib/demo-data.ts` | 836 lines of fake data |
| `frontend/src/lib/demo-candidates.ts` | Fake root cause candidates |
| `frontend/src/components/demo-banner.tsx` | Only existed because of demo data |
| `frontend/src/components/SelfHealingDemo.tsx` | Landing page demo player |
| `frontend/src/components/StarsBackground.tsx` | Decorative Three.js |
| `frontend/src/components/ParticleField.tsx` | Decorative |
| `frontend/src/components/AnimatedBackground.tsx` | Decorative per-page backgrounds |
| `frontend/src/components/3DBackground.tsx` | Decorative |
| `frontend/src/components/tilt-card.tsx` | Decorative hover effect |
| `frontend/src/components/AnimatedCounter.tsx` | Decorative number animation |
| `frontend/src/components/spotlight-card.tsx` | Decorative effect |

#### Modified Frontend Files

| File | Change |
|------|--------|
| `pages/dashboard.tsx` | Remove ALL `?? demoSummary` / `?? demoRepos` / `?? demoMetrics` fallbacks; remove `adjustedSummary`/`adjustedRepos`; remove import of all demo data; show error/empty state instead |
| `pages/analysis.tsx` | Remove `demoWorkflowLogsByType` import and usage; remove `handleLoadExample`; remove `demoCandidates` import |
| `pages/validation.tsx` | Remove demo data auto-load |
| `pages/admin-keys.tsx` | Replace `demoKeys` with real API calls |
| `pages/dashboard.tsx` | Remove `combinedActivities` mixing demo + live; use only SSE events |
| `pages/tasks.tsx` | Remove `demoTasks`; use `useTaskList()` |
| `pages/indexing.tsx` | Remove `demoIndexedRepos`; use API |
| `pages/retry.tsx` | Remove demo retry timeline |
| `pages/review.tsx` | Remove demo review scores |
| `pages/landing.tsx` | Remove `SelfHealingDemo` import; remove 3D backgrounds |
| `pages/login.tsx` | Remove `SelfHealingDemo`, `AnimatedBackground`, demo product content |
| `package.json` | Remove `@react-three/fiber`, `@react-three/drei`, `three` if no longer used |

#### Risks

| Risk | Mitigation |
|------|------------|
| Breaking existing frontend tests | Update test assertions to expect error/empty states instead of demo data |
| Removing Three.js breaks build | Check no remaining components import from three |
| Empty pages after removal | Ensure every page has proper error/empty/loading states before deleting fallbacks |

#### Dependencies

| Depends On | Why |
|------------|-----|
| Strengthens all other items | No hard dependency — can start immediately but must coordinate with API changes |

---

### Item 9: Admin Functionality

**Objective:** Admins can manage users, view platform health, and access admin-specific tools.

#### Database Changes

| Table | Action | Columns |
|-------|--------|--------|
| `users` | **MODIFY** (from Item 1) | `role` column values: `member`, `admin`, `owner` |

#### New Backend Files

| File | Purpose |
|------|---------|
| `app/api/admin_router.py` | `GET /admin/users`, `GET /admin/users/{id}`, `PATCH /admin/users/{id}/role`, `GET /admin/stats` (system health), `GET /admin/integrations` (integration status) |
| `app/admin/service.py` | Admin business logic (list users, update roles, compute system stats) |
| `app/admin/schemas.py` | Pydantic models for admin API |

#### Modified Backend Files

| File | Change |
|------|--------|
| `app/main.py` | Register `admin_router` with `require_role("admin")` guard |
| `app/auth/dependencies.py` | Ensure `require_role("admin")` works with JWT session (currently only works with API key) |

#### New Frontend Files

| File | Purpose |
|------|---------|
| `pages/admin/dashboard.tsx` | Admin overview: active users, investigations today, integration status, system health |
| `pages/admin/users.tsx` | User list with role management |
| `pages/admin/integrations.tsx` | Integration status (GitHub, future Slack) |
| `components/admin/Sidebar.tsx` | Admin-specific navigation |
| `components/admin/UserRow.tsx` | User table row with role dropdown |

#### Modified Frontend Files

| File | Change |
|------|--------|
| `components/layout.tsx` | Add "Admin" nav section when user.role === 'admin' |
| `lib/api.ts` | Add `useAdminUsers()`, `useAdminUpdateRole()`, `useAdminStats()`, `useAdminIntegrations()` |
| `lib/types.ts` | Add `AdminStats`, `AdminUser`, `IntegrationStatus` types |

#### Risks

| Risk | Mitigation |
|------|------------|
| First user needs admin access | Auto-assign `owner` role to first user in an org |
| Non-admin accessing admin routes | Backend `require_role("admin")` guard; frontend conditional rendering |
| Admin deletes all admins | Prevent removal of last owner |

#### Dependencies

| Depends On | Why |
|------------|-----|
| Item 1 (User accounts) | Admins are users with elevated role |
| Item 2 (GitHub OAuth) | Integration status depends on GitHub connection |

---

### Item 10: Audit Logging

**Objective:** All security-relevant actions are logged and viewable by admins.

#### Database Changes

| Table | Action | Columns |
|-------|--------|--------|
| `audit_logs` | **NEW** | `id`, `organization_id` (FK), `user_id` (FK, nullable), `action` (string), `resource_type` (string), `resource_id` (string, nullable), `details` (JSON), `ip_address`, `user_agent`, `created_at` |

#### New Backend Files

| File | Purpose |
|------|---------|
| `app/audit/service.py` | `log_action()` function, `get_audit_logs()` query |
| `app/audit/middleware.py` | FastAPI middleware to log authenticated requests |

#### Modified Backend Files

| File | Change |
|------|--------|
| `app/main.py` | Add audit middleware |
| `app/auth/dependencies.py` | Log login/logout/role-change events |
| `app/api/auth_router.py` | Log API key creation/revocation |
| `app/api/admin_router.py` | Log user role changes |
| `app/api/github_router.py` | Log GitHub connect/disconnect |

#### New Frontend Files

| File | Purpose |
|------|---------|
| `pages/admin/audit-log.tsx` | Audit log viewer with filters (action, user, date range) |
| `components/admin/AuditLogTable.tsx` | Paginated, filterable audit log table |

#### Modified Frontend Files

| File | Change |
|------|--------|
| `lib/api.ts` | Add `useAdminAuditLog()` hook |
| `lib/types.ts` | Add `AuditLogEntry` type |

#### Risks

| Risk | Mitigation |
|------|------------|
| Audit log grows unbounded | Add TTL index; auto-archive logs older than 90 days |
| Performance impact of logging | Use async writes to a separate log queue |
| PII in audit logs | Whitelist allowable detail fields; strip sensitive data |

#### Dependencies

| Depends On | Why |
|------------|-----|
| Item 1 (User accounts) | Audit logs reference users |
| Item 9 (Admin) | Audit log viewer is an admin feature |

---

## Part 2: Implementation Order

### Step 1: Database Foundation (Days 1-2)

**What:** Create all Phase 1 database models and run Alembic migrations.

**Tables created:**
- `organizations`
- `users`
- `sessions`
- `api_keys` (modify)
- `github_installations`
- `repositories` (modify)
- `webhook_events`
- `failures` (modify)
- `investigations`
- `investigation_stages`
- `investigation_evidence`
- `audit_logs`

**Why first:** Every other item depends on these models. Starting with a single migration avoids cascading schema changes.

**Output:** A single Alembic migration that creates/modifies all Phase 1 tables.

**Risk level:** LOW (additive schema changes; existing data unaffected)

### Step 2: Google OAuth + User Accounts (Days 3-6)

**What:** Backend OAuth integration, user CRUD, JWT session management.

**Sub-steps:**
- 2a: Add `authlib` + `python-jose` + config settings
- 2b: Implement `app/auth/oauth.py` — Google OAuth client, callback, token exchange
- 2c: Implement `app/api/oauth_router.py` — login, callback, logout, me endpoints
- 2d: Implement `app/auth/dependencies.py` — `require_session` (JWT), update `require_role`
- 2e: Bootstrap — first user to sign in becomes `owner` of a new org

**Why second:** This is the critical path bottleneck. Everything else requires user accounts.

**Parallel work possible:** Step 8 (demo data removal) can start day 1 independently.

**Risk level:** MEDIUM (Google OAuth config, credential management)

### Step 3: Google OAuth Frontend (Days 5-7, overlaps with Step 2e)

**What:** Rewrite login page, update auth context, swap API key for JWT.

**Sub-steps:**
- 3a: Rewrite `pages/login.tsx` — "Sign in with Google" button
- 3b: Modify `lib/auth-context.ts` — store JWT token; expose user object
- 3c: Modify `lib/api.ts` — change header to `Authorization: Bearer`
- 3d: Update `components/layout.tsx` — show user avatar/name

**Why here:** Cannot build Google OAuth UI before backend exists.

**Dependencies:** Step 2 complete.

**Risk level:** LOW (standard OAuth flow, well-documented)

### Step 4: SSE Real-Time System (Days 5-8, overlaps with Steps 2-3)

**What:** Build SSE infrastructure. Can start as soon as auth basics are in place.

**Sub-steps:**
- 4a: Implement `app/realtime/sse_manager.py` — SSEManager class
- 4b: Add `/events` SSE endpoint to `app/main.py` (authenticated via JWT query param)
- 4c: Implement `hooks/useSSE.ts` — EventSource wrapper with auto-reconnect
- 4d: Integrate SSE with `lib/agent-context.tsx` — subscribe to global channel

**Why parallel:** SSE depends only on auth being functional (JWT validation), which it is by Step 2c. No dependency on GitHub integration.

**Risk level:** LOW (well-understood pattern; FastAPI StreamingResponse)

### Step 5: GitHub OAuth + Repository Linking (Days 6-10)

**What:** GitHub App OAuth flow, repository selection.

**Sub-steps:**
- 5a: Implement `app/github/github_app.py` — GitHub App JWT + installation token
- 5b: Implement `app/api/github_router.py` — auth, callback, repos endpoint
- 5c: Implement `components/RepoSelector.tsx` + `GitHubConnect.tsx`
- 5d: Modify `pages/login.tsx` — add "Connect GitHub" section

**Why here:** Requires user accounts (Step 2) to link GitHub. Overlaps with SSE.

**Risk level:** MEDIUM (GitHub App registration, private key management)

### Step 6: GitHub Webhooks + Failure Detection (Days 9-13)

**What:** Webhook receiver, signature verification, event handling, auto-investigation creation.

**Sub-steps:**
- 6a: Implement `app/github/webhook.py` — HMAC verification, event dispatch
- 6b: Implement `app/api/webhook_router.py` — `POST /api/github/webhook`
- 6c: Implement `app/github/event_handlers.py` — `workflow_run.completed` handler
- 6d: Implement `app/workflows/detection_workflow.py` — create Failure, fetch logs, submit analysis
- 6e: Wire detection workflow → submit analysis task → SSE events

**Why here:** Requires GitHub OAuth (Step 5) for installation context.

**Risk level:** HIGH (first integration with live GitHub events; security-critical)

### Step 7: Real Repository Monitoring (Days 10-14, overlaps with Step 6)

**What:** Dashboard repositories tab shows real GitHub repos with live status.

**Sub-steps:**
- 7a: Update `app/api/dashboard_router.py` — query real repos with status
- 7b: Update `app/dashboard/metrics_collector.py` — use `repositories` + `failures` tables
- 7c: Rewrite `pages/dashboard.tsx` ReposTab — real data columns
- 7d: Implement `components/RepoStatusBadge.tsx`, `RepoHealthBar.tsx`

**Why parallel:** Repo listing depends on Step 5 (GitHub connected repos). Status updates come from Step 6 (webhooks).

**Risk level:** LOW (read-only; API query optimization)

### Step 8: Demo Data Removal (Days 1-14, can run entirely in parallel)

**What:** Delete all fake data files and decorative components. Update all pages to remove demo fallbacks.

**Sub-steps (parallel throughout Phase 1):**
- 8a (Day 1-2): Delete `demo-data.ts`, `demo-candidates.ts` — these are the source of all fake data
- 8b (Day 1-2): Delete all decorative components (StarsBackground, ParticleField, etc.)
- 8c (Day 3-10): Update each page to remove `?? demoX` fallbacks
- 8d (Day 5-14): Remove framer-motion transitions, tilt cards, animated counters
- 8e (Day 3-7): Remove `@react-three/fiber`, `three` from package.json

**Why parallel:** Zero dependencies on backend changes. Can be done incrementally.

**Risk level:** MEDIUM (coordination with other frontend changes; risk of breaking tests)

### Step 9: Investigation Tracking (Days 12-17)

**What:** Investigation DB models, API, frontend pipeline component.

**Sub-steps:**
- 9a: Implement `app/investigation/service.py` + `schemas.py`
- 9b: Implement `app/api/investigation_router.py`
- 9c: Modify all 6 workflows to emit stage events + persist to DB
- 9d: Implement `components/InvestigationPipeline.tsx` — 8-stage visual
- 9e: Rewrite `pages/analysis.tsx` to use InvestigationPipeline
- 9f: Add `components/InvestigationSidebar.tsx` — active investigations list

**Why here:** Requires Failure Detection (Step 6) to create investigations. Requires SSE (Step 4) for live updates.

**Risk level:** MEDIUM (complex frontend component; multiple workflow modifications)

### Step 10: Admin Functionality (Days 15-19)

**What:** Admin dashboard, user management, integration status.

**Sub-steps:**
- 10a: Implement `app/admin/service.py` + `schemas.py`
- 10b: Implement `app/api/admin_router.py`
- 10c: Implement `pages/admin/dashboard.tsx`, `pages/admin/users.tsx`, `pages/admin/integrations.tsx`
- 10d: Update `components/layout.tsx` — admin nav section
- 10e: Update `pages/admin-keys.tsx` — real API calls (or integrate into settings)

**Why here:** Requires user accounts (Step 2) and GitHub integration (Steps 5-6) for full admin experience.

**Risk level:** LOW (standard CRUD)

### Step 11: Audit Logging (Days 17-20)

**What:** Audit log model, middleware, frontend viewer.

**Sub-steps:**
- 11a: Implement `app/audit/service.py` + `app/audit/middleware.py`
- 11b: Add audit calls to auth, admin, and GitHub routers
- 11c: Implement `pages/admin/audit-log.tsx` + filterable table

**Why last:** Audit logging is a cross-cutting concern. Best implemented after all other systems are stable to capture all events.

**Risk level:** LOW (additive, non-breaking)

---

## Part 3: Dependency Graph

```
Step 1 (Database Foundation)
  ├─► Step 2 (Google OAuth Backend)
  │     ├─► Step 3 (Google OAuth Frontend)
  │     └─► Step 4 (SSE Backend + Frontend) ◄── can start after Step 2c
  │
  ├─► Step 8 (Demo Removal) ── can run entirely in parallel
  │
  └─► Step 5 (GitHub OAuth)
        ├─► Step 6 (Webhooks + Failure Detection)
        │     ├─► Step 7 (Repository Monitoring)
        │     └─► Step 9 (Investigation Tracking)
        │           └─► depends on Step 4 (SSE)
        │
        └─► Step 10 (Admin) ── depends on Steps 2, 5
              └─► Step 11 (Audit Logging)
```

### Critical Path (longest chain)

```
Step 1 (2 days) → Step 2 (4 days) → Step 5 (5 days) → Step 6 (4 days) → Step 9 (5 days) = 20 days
```

With overlap: Step 2→5 starts before Step 2 finishes (can start GitHub OAuth when user model is done, ~day 4).
With overlap: Step 6→9 starts before Step 6 finishes (can start investigation API when investigation model is done, ~day 11).

### Optimized Critical Path with Overlap

```
Day 1-2:   Step 1 (DB Foundation)
Day 3-6:   Step 2 (Google OAuth backend) — parallel: Step 8 (demo removal begins)
Day 5-7:   Step 3 (Google OAuth frontend) — parallel: Step 4 (SSE begins)
Day 6-10:  Step 5 (GitHub OAuth) — parallel: Step 8 continues
Day 9-13:  Step 6 (Webhooks + Detection) — parallel: Step 7 (Repo Monitoring begins day 10)
Day 12-17: Step 9 (Investigation Tracking) — parallel: Step 10 (Admin begins day 15)
Day 15-19: Step 10 (Admin)
Day 17-20: Step 11 (Audit Logging)
Day 1-14:  Step 8 (Demo Removal — finishes by day 14)
```

**Total elapsed: ~20 days (~4 weeks for one developer)**

### Parallel Tracks

| Track | Steps | Can Start |
|-------|-------|-----------|
| **A: Auth & Identity** | 1, 2, 3 | Day 1 |
| **B: Real-Time** | 4 (after Step 2c) | Day 5 |
| **C: GitHub Integration** | 5, 6, 7 | Day 6 |
| **D: Investigation** | 9 (after Steps 4, 6) | Day 12 |
| **E: Demo Removal** | 8 | Day 1 |
| **F: Admin & Audit** | 10, 11 (after Steps 2, 5) | Day 15 |

### Highest-Risk Tasks

| Task | Risk Level | Why | Mitigation |
|------|-----------|-----|------------|
| **Step 6: Webhooks** | HIGH | First production integration with live GitHub events; security-critical (signature verification) | Thorough testing with GitHub App webhook delivery history; log all events before processing |
| **Step 4: SSE** | MEDIUM | No existing real-time infrastructure; connection management | Start simple (one queue per user); no Redis pubsub until Phase 2 |
| **Step 9: Workflow modifications** | MEDIUM | Modifying 6 production workflows to emit SSE + persist stages | Add event emission as a decorator or context manager to avoid changing workflow logic |
| **Step 8: Demo removal** | MEDIUM | Coordinated deletion across 15+ files; risk of broken imports | Do incrementally: remove imports first, verify build, then delete files |

---

## Part 4: Definition of Done for Phase 1

### Authentication
- [ ] User can sign in with Google OAuth
- [ ] JWT session is created on sign-in (httpOnly cookie or localStorage)
- [ ] Session expires; user is redirected to login
- [ ] First user in an organization becomes `owner`
- [ ] API key auth still works for machine-to-machine (CI pipelines)
- [ ] `auth` and `dependencies` modules correctly resolve both JWT sessions and API keys

### GitHub Integration
- [ ] User can connect GitHub account via GitHub App OAuth
- [ ] User can select repositories to monitor
- [ ] GitHub App webhook is registered for each installation
- [ ] Webhook events are received, verified (HMAC), and logged

### Repository Monitoring
- [ ] Dashboard "Repositories" tab shows real connected repos
- [ ] Each repo shows: name, branch, workflow status, last run time, failure count
- [ ] Repo list updates when webhook events arrive (via SSE)
- [ ] Empty state shown when no repos connected

### Failure Detection
- [ ] `workflow_run.completed` with `conclusion=failure` automatically creates a `Failure` record
- [ ] Logs are fetched from GitHub API and stored
- [ ] Analysis task is submitted to the queue
- [ ] Duplicate failures for the same `(run_id, job_name)` are prevented

### Investigation Tracking
- [ ] Investigation is created for each detected failure
- [ ] Investigation has 8 stages: Detection, Log Collection, Root Cause Analysis, Fix Generation, Validation, Review, PR Creation, Completion
- [ ] Each stage has: status, start time, duration, result, evidence
- [ ] Frontend InvestigationPipeline component shows live stage progress via SSE
- [ ] Investigation history is searchable via API

### Real-Time Updates
- [ ] SSE endpoint is available at `/api/events`
- [ ] Frontend EventSource hook auto-connects and dispatches events
- [ ] Dashboard updates in real time without polling
- [ ] Investigation and validation pages update in real time
- [ ] Activity feed shows live events

### Demo Data Removal
- [ ] `demo-data.ts` file is deleted
- [ ] `demo-candidates.ts` file is deleted
- [ ] All 6 decorative components are deleted (StarsBackground, ParticleField, AnimatedBackground, 3DBackground, TiltCard, AnimatedCounter, SpotlightCard)
- [ ] `DemoBanner` and `SelfHealingDemo` are deleted
- [ ] No frontend page has a `?? demoX` fallback
- [ ] All pages show proper error/empty/loading states
- [ ] `@react-three/fiber`, `@react-three/drei`, `three` are removed from package.json
- [ ] frontend build succeeds with zero warnings

### Admin Functionality
- [ ] Admin user can navigate to an admin section
- [ ] Admin can view all users in the organization
- [ ] Admin can change user roles (member ↔ admin)
- [ ] Admin dashboard shows: active users, investigation count (today), integration status
- [ ] Non-admin users cannot access admin routes (backend + frontend guard)

### Audit Logging
- [ ] Every user login/logout is logged
- [ ] Every API key creation/revocation is logged
- [ ] Every user role change is logged
- [ ] Every GitHub connect/disconnect is logged
- [ ] Audit log is viewable by admins with filters (action, user, date range)
- [ ] Audit log auto-archives entries older than 90 days

### Testing
- [ ] All existing 59 frontend tests pass (updated for new auth/API behavior)
- [ ] All existing ~259 backend tests pass
- [ ] OAuth callback flow has integration test
- [ ] Webhook signature verification has unit test
- [ ] SSE event dispatch/receive has integration test
- [ ] Investigation stage persistence + retrieval has integration test
- [ ] Admin role restriction has integration test

### Deployment
- [ ] Google Cloud Console OAuth app is registered and documented
- [ ] GitHub App is registered and documented
- [ ] Required environment variables are documented in `.env.example`
- [ ] Database migration can be applied cleanly to a fresh SQLite database
- [ ] Frontend build produces a deployable `dist/` folder

### Product Experience
- [ ] End-to-end scenario works: user signs in → connects GitHub → webhook fires → investigation appears → stages progress live → validation completes → PR is ready
- [ ] User can see what the agent is doing at every stage
- [ ] User can see why the failure happened
- [ ] User knows what will happen next
- [ ] No fake data anywhere in the UI
- [ ] No decorative animations or 3D backgrounds
- [ ] The product feels operational, not like a demo

---

## Summary

| Metric | Value |
|--------|-------|
| **Total calendar time** | ~20 days (~4 weeks) |
| **Total engineering effort** | ~30-35 person-days |
| **New backend files** | ~15 |
| **Modified backend files** | ~20 |
| **New frontend files** | ~12 |
| **Modified frontend files** | ~15 |
| **Files deleted** | ~11 |
| **New DB tables** | 9 |
| **New API endpoints** | ~25 |
| **Highest-risk item** | Step 6 (GitHub Webhooks) |
| **Critical path length** | 20 days (can be compressed to 15 with 2 developers) |
| **Definition of Done items** | 47 checkboxes |
