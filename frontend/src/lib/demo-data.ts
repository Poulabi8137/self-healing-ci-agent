import type {
  DashboardSummary,
  DashboardMetrics,
  RepositoryInfo,
  ReviewScores,
  ValidationResults,
  PRStatistics,
  TaskStatusResponse,
  AnalysisResult,
  FixResult,
  ValidationCheckResult,
  ActivityItem,
} from './types'

// ============================================================
// 4 Repositories — fixed health stats, evolved by outcomes
// ============================================================
export const demoRepos: RepositoryInfo[] = [
  { repository_name: 'frontend-app', total_runs: 15, success_rate: 73.3, avg_confidence: 0.86 },
  { repository_name: 'api-service', total_runs: 12, success_rate: 66.7, avg_confidence: 0.82 },
  { repository_name: 'infra-modules', total_runs: 8, success_rate: 87.5, avg_confidence: 0.93 },
  { repository_name: 'mobile-sdk', total_runs: 6, success_rate: 50.0, avg_confidence: 0.73 },
]

// ============================================================
// Dashboard Summary — consistent with 41 runs, 70.7% success
// ============================================================
export const demoSummary: DashboardSummary = {
  system_health: {
    total_workflow_runs: 41,
    overall_success_rate: 70.7,
    average_retries_per_run: 0.29,
  },
  confidence: {
    overall_confidence: 0.84,
  },
}

// ============================================================
// Dashboard Metrics — consistent: 12 failures, 12 retries
// ============================================================
export const demoMetrics: DashboardMetrics = {
  workflow_metrics: {
    total_retries: 12,
  },
  average_retries: 0.29,
}

// ============================================================
// Charts
// ============================================================
export const demoReviewScores: ReviewScores = {
  categories: ['Security', 'Performance', 'Quality', 'Coverage'],
  scores: [92, 85, 90, 78],
}

export const demoValidationResults: ValidationResults = {
  labels: ['Passed', 'Failed'],
  values: [85, 15],
}

export const demoPRStatistics: PRStatistics = {
  labels: ['Auto-generated', 'Manual'],
  values: [6, 4],
}

function getRandomOutcome(_prob: number): boolean {
  return true
}

function weightedRandom<T>(options: Array<{ item: T; weight: number }>): T {
  return options[0].item
}

// ============================================================
// Activity Feed — 28 items, spanning 7 days
// ============================================================
function hoursAgo(h: number): string {
  const d = new Date()
  d.setHours(d.getHours() - h)
  return d.toISOString()
}

export const demoActivities: ActivityItem[] = (() => {
  const base: ActivityItem[] = [
    { id: 1, type: 'workflow_run', repo: 'frontend-app', message: 'CI run #142 passed (3m 12s)', timestamp: hoursAgo(0.5), status: 'success' },
    { id: 2, type: 'pr_created', repo: 'frontend-app', message: 'PR #131: Fix token refresh interval', timestamp: hoursAgo(1), status: 'success' },
    { id: 3, type: 'validation_passed', repo: 'api-service', message: 'Patch v7 passed all 3 validation stages', timestamp: hoursAgo(1.5), status: 'success' },
    { id: 4, type: 'retry_attempted', repo: 'api-service', message: 'Retry #2 for CI run #89 — attempting escalated fix', timestamp: hoursAgo(2), status: 'pending' },
    { id: 5, type: 'failure_detected', repo: 'api-service', message: 'CI run #89 failed — Docker build exited with code 1', timestamp: hoursAgo(2.5), status: 'failure' },
    { id: 6, type: 'auto_resolved', repo: 'frontend-app', message: 'Run #138 failure auto-resolved after retry #2', timestamp: hoursAgo(3), status: 'success' },
    { id: 7, type: 'workflow_run', repo: 'infra-modules', message: 'CI run #47 passed (1m 48s)', timestamp: hoursAgo(3.5), status: 'success' },
    { id: 8, type: 'fix_generated', repo: 'api-service', message: 'Fix generated for run #89 — added missing @prisma/client to dependencies', timestamp: hoursAgo(4), status: 'success' },
    { id: 9, type: 'failure_detected', repo: 'mobile-sdk', message: 'CI run #23 failed — 2 test assertions failed', timestamp: hoursAgo(5), status: 'failure' },
    { id: 10, type: 'pr_created', repo: 'infra-modules', message: 'PR #12: Pin Terraform AWS provider to v5.0', timestamp: hoursAgo(6), status: 'success' },
    { id: 11, type: 'workflow_run', repo: 'frontend-app', message: 'CI run #141 passed (2m 55s)', timestamp: hoursAgo(7), status: 'success' },
    { id: 12, type: 'auto_resolved', repo: 'api-service', message: 'Run #86 auto-resolved — dependency conflict fixed', timestamp: hoursAgo(8), status: 'success' },
    { id: 13, type: 'failure_detected', repo: 'frontend-app', message: 'CI run #140 failed — API_KEY missing in test env', timestamp: hoursAgo(10), status: 'failure' },
    { id: 14, type: 'validation_failed', repo: 'mobile-sdk', message: 'Patch v3 failed build check — CocoaPods lockfile mismatch', timestamp: hoursAgo(12), status: 'failure' },
    { id: 15, type: 'fix_generated', repo: 'frontend-app', message: 'Fix for run #140 — added .env.test with demo key', timestamp: hoursAgo(13), status: 'success' },
    { id: 16, type: 'workflow_run', repo: 'api-service', message: 'CI run #88 passed (2m 11s)', timestamp: hoursAgo(14), status: 'success' },
    { id: 17, type: 'pr_created', repo: 'api-service', message: 'PR #67: Fix TypeScript strict errors in user service', timestamp: hoursAgo(16), status: 'success' },
    { id: 18, type: 'retry_attempted', repo: 'mobile-sdk', message: 'Retry #1 for run #23 — adjusting test timeout', timestamp: hoursAgo(18), status: 'pending' },
    { id: 19, type: 'human_resolved', repo: 'mobile-sdk', message: 'Run #22 required manual intervention — Xcode version mismatch', timestamp: hoursAgo(20), status: 'info' },
    { id: 20, type: 'workflow_run', repo: 'frontend-app', message: 'CI run #139 failed — TypeScript build error', timestamp: hoursAgo(22), status: 'failure' },
    { id: 21, type: 'auto_resolved', repo: 'frontend-app', message: 'Run #135 auto-resolved — added NODE_ENV check', timestamp: hoursAgo(24), status: 'success' },
    { id: 22, type: 'workflow_run', repo: 'infra-modules', message: 'CI run #46 passed (2m 03s)', timestamp: hoursAgo(30), status: 'success' },
    { id: 23, type: 'pr_created', repo: 'mobile-sdk', message: 'PR #19: Increase test timeout for concurrent sessions', timestamp: hoursAgo(36), status: 'success' },
    { id: 24, type: 'retry_attempted', repo: 'api-service', message: 'Retry #1 for run #86 — pinning lodash to compatible version', timestamp: hoursAgo(48), status: 'info' },
    { id: 25, type: 'failure_detected', repo: 'infra-modules', message: 'CI run #45 failed — Terraform state lock timeout', timestamp: hoursAgo(60), status: 'failure' },
    { id: 26, type: 'fix_generated', repo: 'infra-modules', message: 'Fix for run #45 — added DynamoDB state locking config', timestamp: hoursAgo(72), status: 'success' },
    { id: 27, type: 'workflow_run', repo: 'mobile-sdk', message: 'CI run #22 failed — 2 test assertions failed', timestamp: hoursAgo(84), status: 'failure' },
    { id: 28, type: 'auto_resolved', repo: 'infra-modules', message: 'Run #45 auto-resolved — Terraform state lock resolved', timestamp: hoursAgo(96), status: 'success' },
  ]
  // Randomly toggle some validation outcomes to show branching
  if (getRandomOutcome(0.5)) {
    base[2] = { ...base[2], type: 'validation_failed', status: 'failure', message: 'Patch v7 failed build check — incorrect import path' }
  }
  if (getRandomOutcome(0.4)) {
    base[7] = { ...base[7], type: 'failure_detected', status: 'failure', message: 'Fix for run #89 caused dependency cycle — rolling back' }
  }
  return base
})()

// ============================================================
// Demo API Keys (pre-seeded)
// ============================================================
export const demoKeys: { prefix: string; name: string; role: string; created: string; lastUsed: string | null }[] = [
  { prefix: 'ci_agent_sk_a1b2c3d4', name: 'CI Pipeline Token', role: 'recruiter', created: '2026-05-28', lastUsed: '2026-06-02' },
  { prefix: 'ci_agent_sk_e5f6g7h8', name: 'Demo Access Key', role: 'candidate', created: '2026-06-01', lastUsed: null },
  { prefix: 'ci_agent_sk_i9j0k1l2', name: 'Production Admin Key', role: 'admin', created: '2026-05-15', lastUsed: '2026-06-02' },
]

// ============================================================
// Retry Timeline Data — 12 retries across 6 workflow runs
// ============================================================
export interface RetryAttempt {
  id: number
  runId: number
  repo: string
  attempt: number
  status: 'resolved' | 'failed' | 'running'
  duration_seconds: number
  error_type: string
  fix_strategy: string
  timestamp: string
}

export const demoRetryTimeline: RetryAttempt[] = [
  { id: 1, runId: 140, repo: 'frontend-app', attempt: 1, status: 'failed', duration_seconds: 45, error_type: 'Missing environment variable', fix_strategy: 'Added NODE_ENV fallback', timestamp: hoursAgo(10) },
  { id: 2, runId: 140, repo: 'frontend-app', attempt: 2, status: 'resolved', duration_seconds: 38, error_type: 'Missing environment variable', fix_strategy: 'Created .env.test with mock API key', timestamp: hoursAgo(9.8) },
  { id: 3, runId: 89, repo: 'api-service', attempt: 1, status: 'failed', duration_seconds: 52, error_type: 'Docker build failure', fix_strategy: 'Installed @prisma/client in build stage', timestamp: hoursAgo(2.5) },
  { id: 4, runId: 89, repo: 'api-service', attempt: 2, status: 'resolved', duration_seconds: 41, error_type: 'Docker build failure', fix_strategy: 'Added prisma generate to Dockerfile', timestamp: hoursAgo(2.3) },
  { id: 5, runId: 86, repo: 'api-service', attempt: 1, status: 'failed', duration_seconds: 33, error_type: 'Dependency version conflict', fix_strategy: 'Pinned lodash to compatible range', timestamp: hoursAgo(48) },
  { id: 6, runId: 86, repo: 'api-service', attempt: 2, status: 'resolved', duration_seconds: 29, error_type: 'Dependency version conflict', fix_strategy: 'Added overrides in package.json', timestamp: hoursAgo(47.8) },
  { id: 7, runId: 23, repo: 'mobile-sdk', attempt: 1, status: 'failed', duration_seconds: 67, error_type: 'Failing unit test', fix_strategy: 'Increased test timeout to 5s', timestamp: hoursAgo(18) },
  { id: 8, runId: 23, repo: 'mobile-sdk', attempt: 2, status: 'failed', duration_seconds: 72, error_type: 'Failing unit test', fix_strategy: 'Fixed concurrent session counter', timestamp: hoursAgo(17.5) },
  { id: 9, runId: 23, repo: 'mobile-sdk', attempt: 3, status: 'running', duration_seconds: 0, error_type: 'Failing unit test', fix_strategy: 'Rewrote session locking mechanism', timestamp: hoursAgo(17) },
  { id: 10, runId: 139, repo: 'frontend-app', attempt: 1, status: 'resolved', duration_seconds: 28, error_type: 'TypeScript type mismatch', fix_strategy: 'Added null check guard clauses', timestamp: hoursAgo(22) },
  { id: 11, runId: 45, repo: 'infra-modules', attempt: 1, status: 'resolved', duration_seconds: 55, error_type: 'Terraform state lock', fix_strategy: 'Configured DynamoDB state locking', timestamp: hoursAgo(60) },
  { id: 12, runId: 22, repo: 'mobile-sdk', attempt: 1, status: 'failed', duration_seconds: 44, error_type: 'Failing unit test', fix_strategy: 'Adjusted async wait expectations', timestamp: hoursAgo(84) },
]

// ============================================================
// 6 Failure Investigations — each has logs, analysis, fix, result
// ============================================================

// --- Failure 1: Missing environment variable ---
export const failureMissingEnvVar: { logs: string; analysis: AnalysisResult; fix: FixResult; validation: ValidationCheckResult } = {
  logs: `$ npm run test:ci

> frontend-app@1.0.0 test:ci
> jest --ci --coverage

PASS  src/components/Button.test.tsx
PASS  src/utils/format.test.ts
PASS  src/hooks/useAuth.test.ts
FAIL  src/services/api.test.ts
  ● API Service > should fetch user data

    expect(received).resolves.toEqual(expected)

    Error: Missing environment variable: API_KEY

      14 |   const apiKey = process.env.API_KEY
    > 15 |   if (!apiKey) {
         |       ^
      16 |     throw new Error('Missing environment variable: API_KEY')
      17 |   }
      18 |   return apiKey

      at getApiKey (src/services/api.ts:15:19)

Tests: 1 failed, 139 passed (140 total)
Test Suites: 1 failed, 19 passed (20 total)`,
   analysis: weightedRandom([
     {
       item: {
         root_cause: 'The API_KEY environment variable is not set in the test environment. ApiService.getApiKey() throws when the variable is missing, but .env.test does not include it. The CI runner lacks the secret mapping for test jobs.',
         error_category: 'config_error',
         confidence: 0.94,
         affected_files: ['src/services/api.ts', '.env.test', '.github/workflows/ci.yml'],
       },
       weight: 7
     },
     {
       item: {
         root_cause: 'Missing API_KEY in test environment causing authentication failures with external services. The CI pipeline does not inject test credentials for API calls.',
         error_category: 'config_error',
         confidence: 0.89,
         affected_files: ['src/services/api.ts', 'src/services/auth.ts', '.github/workflows/ci.yml'],
       },
       weight: 3
     }
   ]),
   fix: weightedRandom([
     {
       item: {
         fix_summary: 'Made API_KEY optional during test runs by adding NODE_ENV check. Created .env.test with demo key. Added secrets mapping to CI workflow.',
         assumptions: ['Test environment should use a mock API key', 'Production always sets API_KEY via secrets manager'],
         patch: `diff --git a/.env.test b/.env.test
new file mode 100644
--- /dev/null
+++ b/.env.test
@@ -0,0 +1 @@
+API_KEY=demo-test-key-abc123

diff --git a/src/services/api.ts b/src/services/api.ts
--- a/src/services/api.ts
+++ b/src/services/api.ts
@@ -12,7 +12,7 @@ export class ApiService {
   private getApiKey(): string {
     const apiKey = process.env.API_KEY
-    if (!apiKey) {
+    if (!apiKey && process.env.NODE_ENV !== 'test') {
       throw new Error('Missing environment variable: API_KEY')
     }
     return apiKey ?? 'test-key'
   }
 }`,
       },
       weight: 6
     },
     {
       item: {
         fix_summary: 'Updated CI workflow to inject API_KEY from GitHub secrets into test jobs. Added fallback logic in ApiService to return a test key when running in CI without requiring NODE_ENV check.',
         assumptions: ['API_KEY secret is configured in GitHub Actions', 'CI workflow has permission to access secrets'],
         patch: `diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -15,4 +15,5 @@ jobs:
     - run: npm ci
+    - run: echo "API_KEY=$\{{ secrets.API_KEY }}" >> .env
     - run: npm test`,
       },
       weight: 4
     }
   ]),
   validation: getRandomOutcome(0.7) 
     ? {
         validation: { syntax_errors: [], build_checks: [], failed_tests: [], validation_status: 'passed' },
         fix_proposal: { confidence: 0.96 },
       }
     : {
         validation: { 
           syntax_errors: [], 
           build_checks: [], 
           failed_tests: [{ test: 'src/services/api.test.ts', reason: 'API_KEY still undefined in test' }], 
           validation_status: 'failed' 
         },
         fix_proposal: { confidence: 0.65 },
       },
}

// --- Failure 2: Dependency version conflict ---
export const failureDependencyConflict: { logs: string; analysis: AnalysisResult; fix: FixResult; validation: ValidationCheckResult } = {
  logs: `$ npm ci

npm ERR! code ERESOLVE
npm ERR! ERESOLVE unable to resolve dependency tree
npm ERR!
npm ERR! While resolving: frontend-app@1.0.0
npm ERR! Found: lodash@4.17.21
npm ERR! node_modules/lodash
npm ERR!   lodash@"^4.17.21" from the root project
npm ERR!
npm ERR! Could not resolve dependency:
npm ERR! peer lodash@"4.17.20" from @types/lodash@4.17.0
npm ERR! node_modules/@types/lodash
npm ERR!   dev @types/lodash@"^4.17.0" from the root project
npm ERR!
npm ERR! Fix the upstream dependency conflict.`,
   analysis: weightedRandom([
     {
       item: {
         root_cause: '@types/lodash@4.17.0 requires lodash@4.17.20 as a peer dependency, but the root project specifies lodash@^4.17.21 which resolved to 4.17.21. npm ERESOLVE cannot find a compatible version satisfying both constraints.',
         error_category: 'dependency_error',
         confidence: 0.91,
         affected_files: ['package.json'],
       },
       weight: 6
     },
     {
       item: {
         root_cause: 'The lockfile is out of date with package.json. Running npm install introduced lodash@4.17.21 while @types/lodash requires 4.17.20, causing an unresolvable dependency tree conflict.',
         error_category: 'dependency_error',
         confidence: 0.88,
         affected_files: ['package.json', 'package-lock.json'],
       },
       weight: 4
     }
   ]),
   fix: weightedRandom([
     {
       item: {
         fix_summary: 'Added overrides in package.json to force lodash@4.17.20 for all sub-dependencies. Ran npm dedupe to flatten the tree.',
         assumptions: ['lodash@4.17.20 is backward compatible with the application code', 'All tests pass with the pinned version'],
         patch: `diff --git a/package.json b/package.json
--- a/package.json
+++ b/package.json
@@ -20,4 +20,9 @@
   "devDependencies": {
     "@types/lodash": "^4.17.0"
+  },
+  "overrides": {
+    "lodash": "4.17.20",
+    "@types/lodash": {
+      "lodash": "4.17.20"
+    }
   }
 }`,
       },
       weight: 7
     },
     {
       item: {
         fix_summary: 'Resolved dependency conflict by updating @types/lodash to ^4.17.1 which supports lodash@4.17.21. This removes the need for overrides.',
         assumptions: ['@types/lodash@4.17.1 is backward compatible', 'No other dependencies require lodash@4.17.20'],
         patch: `diff --git a/package.json b/package.json
--- a/package.json
+++ b/package.json
@@ -5,7 +5,7 @@
   "devDependencies": {
-    "@types/lodash": "^4.17.0"
+    "@types/lodash": "^4.17.1"
   }
 }`,
       },
       weight: 3
     }
   ]),
   validation: getRandomOutcome(0.6) 
     ? {
         validation: { syntax_errors: [], build_checks: [], failed_tests: [], validation_status: 'passed' },
         fix_proposal: { confidence: 0.93 },
       }
     : {
         validation: { 
           syntax_errors: [], 
           build_checks: [{ file: 'package.json', reason: 'lodash version mismatch' }], 
           failed_tests: [], 
           validation_status: 'failed' 
         },
         fix_proposal: { confidence: 0.7 },
       },
}

// --- Failure 3: TypeScript type mismatch ---
export const failureTypeMismatch: { logs: string; analysis: AnalysisResult; fix: FixResult; validation: ValidationCheckResult } = {
  logs: `$ npx tsc --noEmit

src/services/user.service.ts:42:5 - error TS2322: Type 'User | null' is not assignable to type 'User'.
  Type 'null' is not assignable to type 'User'.

42     const user = await this.repository.findById(id)
       ~~~~

src/services/user.service.ts:45:9 - error TS18048: 'user' is possibly 'null'.

45     if (user.role === 'admin') {
            ~~~~

Found 2 errors.`,
   analysis: weightedRandom([
     {
       item: {
         root_cause: 'TypeScript strict mode catches missing null checks. repository.findById() returns User | null, but the code assigns to User without narrowing. The role check at line 45 also fails because user may be null.',
         error_category: 'type_error',
         confidence: 0.97,
         affected_files: ['src/services/user.service.ts'],
       },
       weight: 7
     },
     {
       item: {
         root_cause: 'The repository.findById method signature was changed to return User | null but the caller at user.service.ts was not updated. TypeScript strict null checks flag the assignment without proper narrowing.',
         error_category: 'type_error',
         confidence: 0.93,
         affected_files: ['src/services/user.service.ts', 'src/repositories/user.repository.ts'],
       },
       weight: 3
     }
   ]),
   fix: weightedRandom([
     {
       item: {
         fix_summary: 'Added null check guard clause after findById(). Early return when user is null preserves the existing control flow.',
         assumptions: ['Callers handle the early return correctly', 'Null state represents "not found" which is a valid business case'],
         patch: `diff --git a/src/services/user.service.ts b/src/services/user.service.ts
--- a/src/services/user.service.ts
+++ b/src/services/user.service.ts
@@ -39,9 +39,12 @@ export class UserService {
 
   async getUserRole(id: string): Promise<string> {
     const user = await this.repository.findById(id)
+    if (!user) {
+      throw new NotFoundError('User not found')
+    }
 
-    if (user.role === 'admin') {
+    if (user.role === 'admin') {
       return 'administrator'
     }
     return user.role
   }`,
       },
       weight: 8
     },
     {
       item: {
         fix_summary: 'Updated repository.findById return type to be non-nullable by throwing from the repository layer instead of the service layer. This keeps the null check closer to the data source.',
         assumptions: ['Repository can access the error context', 'Service layer should not handle "not found" cases'],
         patch: `diff --git a/src/repositories/user.repository.ts b/src/repositories/user.repository.ts
--- a/src/repositories/user.repository.ts
+++ b/src/repositories/user.repository.ts
@@ -10,5 +10,7 @@ export class UserRepository {
   async findById(id: string): Promise<User> {
     const user = await this.db.users.findUnique({ where: { id } })
+    if (!user) {
+      throw new NotFoundError('User not found')
+    }
     return user
   }`,
       },
       weight: 2
     }
   ]),
   validation: getRandomOutcome(0.8) 
     ? {
         validation: { syntax_errors: [], build_checks: [], failed_tests: [], validation_status: 'passed' },
         fix_proposal: { confidence: 0.97 },
       }
     : {
         validation: { 
           syntax_errors: [], 
           build_checks: [], 
           failed_tests: [{ test: 'src/services/user.service.test.ts', reason: 'null check edge case' }], 
           validation_status: 'failed' 
         },
         fix_proposal: { confidence: 0.75 },
       },
}

// --- Failure 4: Docker build failure ---
export const failureDockerBuild: { logs: string; analysis: AnalysisResult; fix: FixResult; validation: ValidationCheckResult } = {
  logs: `$ docker build -t api-service:latest .

[1/5] FROM node:18-alpine@sha256:abc123
[2/5] COPY package*.json ./
[3/5] RUN npm ci
[4/5] COPY . .
[5/5] RUN npm run build
--
 > [5/5] RUN npm run build:
0.401 > api-service@1.0.0 build
0.401 > tsc && vite build
0.902 src/config/database.ts:12:22
0.902 ERROR: Cannot find module '@prisma/client'
0.902   10 | import { PrismaClient } from '@prisma/client'
           |          ^^^^^^^^^^^^^^^^
1.203 npm ERR! code ELIFECYCLE

Docker build failed with exit code 1`,
   analysis: weightedRandom([
     {
       item: {
         root_cause: '@prisma/client is listed in devDependencies but not in dependencies. During docker build, npm ci installs only dependencies (not devDependencies) when NODE_ENV=production, causing the import to fail at build time.',
         error_category: 'build_error',
         confidence: 0.95,
         affected_files: ['package.json', 'Dockerfile'],
       },
       weight: 6
     },
     {
       item: {
         root_cause: 'The Dockerfile uses a multi-stage build but the node_modules from npm install are not copied to the production stage. @prisma/client is generated during build but the generated client files are missing from the final image.',
         error_category: 'build_error',
         confidence: 0.9,
         affected_files: ['Dockerfile', 'package.json'],
       },
       weight: 4
     }
   ]),
   fix: weightedRandom([
     {
       item: {
         fix_summary: 'Moved @prisma/client from devDependencies to dependencies. Also added prisma generate step before build in Dockerfile to ensure client is generated.',
         assumptions: ['Prisma client binary is compatible with node:18-alpine', 'Build cache layer ordering is preserved'],
         patch: `diff --git a/Dockerfile b/Dockerfile
--- a/Dockerfile
+++ b/Dockerfile
@@ -8,6 +8,7 @@ COPY package*.json ./
 RUN npm ci --only=production
 COPY --from=builder /app/dist ./dist
+COPY --from=builder /app/node_modules/.prisma ./node_modules/.prisma
 CMD ["node", "dist/index.js"]
 
 FROM base AS builder
 COPY . .
+RUN npx prisma generate
 RUN npm run build`,
       },
       weight: 6
     },
     {
       item: {
         fix_summary: 'Changed Dockerfile to use npm ci without --only=production so devDependencies are installed during build. Then run prisma generate before the build step.',
         assumptions: ['Installing devDependencies in build stage does not increase image size', 'Dev dependencies are safe to install in CI'],
         patch: `diff --git a/Dockerfile b/Dockerfile
--- a/Dockerfile
+++ b/Dockerfile
@@ -5,7 +5,7 @@ COPY package*.json ./
-RUN npm ci --only=production
+RUN npm ci
 COPY . .
+RUN npx prisma generate
 RUN npm run build`,
       },
       weight: 4
     }
   ]),
   validation: getRandomOutcome(0.75) 
     ? {
         validation: { syntax_errors: [], build_checks: [], failed_tests: [], validation_status: 'passed' },
         fix_proposal: { confidence: 0.94 },
       }
     : {
         validation: { 
           syntax_errors: [], 
           build_checks: [{ file: 'Dockerfile', reason: 'prisma generate step missing' }], 
           failed_tests: [], 
           validation_status: 'failed' 
         },
         fix_proposal: { confidence: 0.7 },
       },
}

// --- Failure 5: Failing unit test (iOS) ---
export const failureUnitTest: { logs: string; analysis: AnalysisResult; fix: FixResult; validation: ValidationCheckResult } = {
  logs: `$ xcodebuild test -scheme MobileSDK -destination 'platform=iOS Simulator'

▸ Testing MobileSDKTests
▸ SessionManagerTests
  ✓ testSessionCreation
  ✓ testTokenRefresh
  ✗ testConcurrentSessions (0.042s)
    XCTAssertEqual failed: ("3") is not equal to ("2")
    SessionManager created 3 concurrent sessions instead of expected 2
    at SessionManagerTests.swift:84
  ✓ testSessionExpiry

▸ NetworkManagerTests
  ✓ testRequestSuccess
  ✓ testRequestRetry
  ✗ testRequestTimeout (0.031s)
    XCTAssertEqual failed: ("timeout") is not equal to ("retry")
    NetworkManager did not retry on timeout
    at NetworkManagerTests.swift:156

Test Suite 'MobileSDKTests' failed:
  Executed 6 tests (4 passed, 2 failed)`,
   analysis: weightedRandom([
     {
       item: {
         root_cause: 'SessionManager creates a third session when a race condition occurs in the session creation lock. NetworkManager lacks a retry mechanism for timeout errors — the URLSession timeout fires but the retry logic is not invoked.',
         error_category: 'test_failure',
         confidence: 0.89,
         affected_files: ['Sources/SessionManager.swift', 'Sources/NetworkManager.swift'],
       },
       weight: 6
     },
     {
       item: {
         root_cause: 'testConcurrentSessions fails because the session counter is incremented before the lock is acquired, causing a race window. testRequestTimeout fails because the URLSession timeout fires before the retry logic is triggered, indicating incorrect delegate method override.',
         error_category: 'test_failure',
         confidence: 0.85,
         affected_files: ['Sources/SessionManager.swift', 'Sources/NetworkManager.swift'],
       },
       weight: 4
     }
   ]),
   fix: weightedRandom([
     {
       item: {
         fix_summary: 'Added os_unfair_lock to SessionManager for thread-safe session creation. Implemented retryWithDelay on NetworkManager timeout errors using a simple exponential backoff.',
         assumptions: ['iOS 15+ supports os_unfair_lock', 'Retry delay of 0.5s is acceptable for timeout recovery'],
         patch: `diff --git a/Sources/SessionManager.swift b/Sources/SessionManager.swift
--- a/Sources/SessionManager.swift
+++ b/Sources/SessionManager.swift
@@ -1,5 +1,6 @@
 import Foundation
+import os
 
 class SessionManager {
     private var sessions: [String: Session] = [:]
+    private let lock = OSAllocatedUnfairLock()
     
     func createSession(for user: String) -> Session {
+        lock.lock()
+        defer { lock.unlock() }
         guard sessions.count < maxConcurrentSessions else {
             throw SessionError.limitExceeded
         }`,
       },
       weight: 7
     },
     {
       item: {
         fix_summary: 'Refactored SessionManager to use actor isolation instead of manual locking. Updated NetworkManager to use async/await with Task.sleep for retry delay, ensuring proper timeout handling.',
         assumptions: ['Swift 5.5+ concurrency features are available', 'Actor isolation resolves the race condition without explicit locking'],
         patch: `diff --git a/Sources/SessionManager.swift b/Sources/SessionManager.swift
--- a/Sources/SessionManager.swift
+++ b/Sources/SessionManager.swift
@@ -1,5 +1,5 @@
 import Foundation
 
-class SessionManager {
+actor SessionManager {
     private var sessions: [String: Session] = [:]
     
     func createSession(for user: String) -> Session {`,
       },
       weight: 3
     }
   ]),
   validation: getRandomOutcome(0.7) 
     ? {
         validation: { syntax_errors: [], build_checks: [], failed_tests: [], validation_status: 'passed' },
         fix_proposal: { confidence: 0.88 },
       }
     : {
         validation: { 
           syntax_errors: [], 
           build_checks: [], 
           failed_tests: [{ test: 'SessionManagerTests.testConcurrentSessions', reason: 'race condition still present' }], 
           validation_status: 'failed' 
         },
         fix_proposal: { confidence: 0.6 },
       },
}

// --- Failure 6: Terraform state lock ---
export const failureTerraformState: { logs: string; analysis: AnalysisResult; fix: FixResult; validation: ValidationCheckResult } = {
  logs: `$ terraform plan

Initializing the backend...

Error: Error acquiring the state lock

Error message: operation error DynamoDB: PutItem, https response error
StatusCode: 400, RequestID: abc123, ConditionalCheckFailedException:
The conditional request failed

Lock Info:
  ID:         abc123
  Path:       terraform-state/infra-modules/terraform.tfstate
  Operation:  plan
  Who:        runner@github-actions
  Version:    1.6.0
  Created:    2026-06-01 14:22:31.847159 +0000 UTC

Terraform acquires a state lock to protect against concurrent modifications.`,
   analysis: weightedRandom([
     {
       item: {
         root_cause: 'The S3 backend is configured without DynamoDB state locking. When two CI runners attempt to plan simultaneously, the second one fails because the state file is locked by the first operation. The DynamoDB table either does not exist or lacks the correct partition key schema.',
         error_category: 'infrastructure_error',
         confidence: 0.93,
         affected_files: ['backend.tf', 'provider.tf'],
       },
       weight: 7
     },
     {
       item: {
         root_cause: 'The IAM role used by the CI runner does not have dynamodb:PutItem permission on the state lock table. The DynamoDB table exists but the conditional check fails because the role lacks write access.',
         error_category: 'infrastructure_error',
         confidence: 0.87,
         affected_files: ['backend.tf', 'iam-policy.tf'],
       },
       weight: 3
     }
   ]),
   fix: weightedRandom([
     {
       item: {
         fix_summary: 'Added DynamoDB state locking configuration to the S3 backend. Created the DynamoDB table with LockID as the partition key. Added retry logic for state lock acquisition.',
         assumptions: ['DynamoDB table exists in the same region as the S3 bucket', 'IAM role has dynamodb:PutItem and dynamodb:DeleteItem permissions'],
         patch: `diff --git a/backend.tf b/backend.tf
--- a/backend.tf
+++ b/backend.tf
@@ -3,4 +3,6 @@ terraform {
     bucket  = "infra-modules-terraform-state"
     key     = "terraform.tfstate"
     region  = "us-east-1"
+    dynamodb_table = "infra-modules-state-lock"
+    encrypt = true
   }
 }`,
       },
       weight: 8
     },
     {
       item: {
         fix_summary: 'Added retry logic in CI workflow to handle state lock contention. Configured terraform plan to wait and retry if the state lock is held by another process.',
         assumptions: ['State lock timeouts are temporary', 'Retry with backoff resolves most contention scenarios without changing backend config'],
         patch: `diff --git a/.github/workflows/terraform.yml b/.github/workflows/terraform.yml
--- a/.github/workflows/terraform.yml
+++ b/.github/workflows/terraform.yml
@@ -10,4 +10,5 @@ jobs:
     - run: terraform init
+    - run: for i in 1 2 3 4 5; do terraform plan && break || sleep $((i * 5)); done
     - run: terraform apply -auto-approve`,
       },
       weight: 2
     }
   ]),
   validation: getRandomOutcome(0.8) 
     ? {
         validation: { syntax_errors: [], build_checks: [], failed_tests: [], validation_status: 'passed' },
         fix_proposal: { confidence: 0.91 },
       }
     : {
         validation: { 
           syntax_errors: [], 
           build_checks: [{ file: 'backend.tf', reason: 'DynamoDB table reference incorrect' }], 
           failed_tests: [], 
           validation_status: 'failed' 
         },
         fix_proposal: { confidence: 0.7 },
       },
}

// ============================================================
// Example dropdown — maps failure type names to their data
// ============================================================
export const demoWorkflowLogsByType: Record<string, { repo: string; logs: string; analysis: AnalysisResult; fix: FixResult; validation: ValidationCheckResult }> = {
  'Missing environment variable': {
    repo: 'frontend-app',
    logs: failureMissingEnvVar.logs,
    analysis: failureMissingEnvVar.analysis,
    fix: failureMissingEnvVar.fix,
    validation: failureMissingEnvVar.validation,
  },
  'Dependency version conflict': {
    repo: 'frontend-app',
    logs: failureDependencyConflict.logs,
    analysis: failureDependencyConflict.analysis,
    fix: failureDependencyConflict.fix,
    validation: failureDependencyConflict.validation,
  },
  'TypeScript type mismatch': {
    repo: 'api-service',
    logs: failureTypeMismatch.logs,
    analysis: failureTypeMismatch.analysis,
    fix: failureTypeMismatch.fix,
    validation: failureTypeMismatch.validation,
  },
  'Docker build failure': {
    repo: 'api-service',
    logs: failureDockerBuild.logs,
    analysis: failureDockerBuild.analysis,
    fix: failureDockerBuild.fix,
    validation: failureDockerBuild.validation,
  },
  'Failing unit test': {
    repo: 'mobile-sdk',
    logs: failureUnitTest.logs,
    analysis: failureUnitTest.analysis,
    fix: failureUnitTest.fix,
    validation: failureUnitTest.validation,
  },
  'Terraform state lock': {
    repo: 'infra-modules',
    logs: failureTerraformState.logs,
    analysis: failureTerraformState.analysis,
    fix: failureTerraformState.fix,
    validation: failureTerraformState.validation,
  },
}

// ============================================================
// Legacy aliases for backward compatibility
// ============================================================
export const demoExampleRepo = 'frontend-app'
export const demoExampleLogs = failureMissingEnvVar.logs
export const demoAnalysisResult = failureMissingEnvVar.analysis
export const demoFixResult = failureMissingEnvVar.fix
export const demoValidationResult = failureMissingEnvVar.validation
export const demoPRUrl = ''
export const demoPRNumber = 131

// ============================================================
// Tasks
// ============================================================
export const demoTasks: TaskStatusResponse[] = [
  { id: 1, type: 'Index repository', status: 'completed', payload: { repo: 'frontend-app' }, result: { files: 2847, chunks: 12400 }, created_at: hoursAgo(96), updated_at: hoursAgo(95.9) },
  { id: 2, type: 'Analyze failure', status: 'completed', payload: { repo: 'frontend-app', run_id: 140 }, result: { root_cause: 'Missing environment variable: API_KEY', category: 'config_error' }, created_at: hoursAgo(10), updated_at: hoursAgo(9.98) },
  { id: 3, type: 'Generate fix', status: 'completed', payload: { repo: 'api-service', run_id: 89 }, result: { patch: 'Added @prisma/client to dependencies' }, created_at: hoursAgo(4), updated_at: hoursAgo(3.97) },
  { id: 4, type: 'Create PR', status: 'running', payload: { repo: 'frontend-app', fix_id: 3, branch: 'fix/api-key-test-env' }, result: {}, created_at: hoursAgo(1.5), updated_at: hoursAgo(1.5) },
  { id: 5, type: 'Validate fix', status: 'pending', payload: { repo: 'mobile-sdk', fix_id: 4 }, result: {}, created_at: hoursAgo(1), updated_at: hoursAgo(1) },
  { id: 6, type: 'Analyze failure', status: 'completed', payload: { repo: 'infra-modules', run_id: 45 }, result: { root_cause: 'DynamoDB state lock missing', category: 'infrastructure_error' }, created_at: hoursAgo(72), updated_at: hoursAgo(71.98) },
  { id: 7, type: 'Generate fix', status: 'completed', payload: { repo: 'mobile-sdk', run_id: 23 }, result: { patch: 'Added os_unfair_lock to SessionManager' }, created_at: hoursAgo(17), updated_at: hoursAgo(16.95) },
  { id: 8, type: 'Retry workflow', status: 'failed', payload: { repo: 'mobile-sdk', run_id: 23, attempt: 3 }, result: { error: 'CocoaPods lockfile conflict — manual resolution required' }, created_at: hoursAgo(16), updated_at: hoursAgo(15.95) },
  { id: 9, type: 'Index repository', status: 'completed', payload: { repo: 'api-service' }, result: { files: 1853, chunks: 8900 }, created_at: hoursAgo(48), updated_at: hoursAgo(47.95) },
  { id: 10, type: 'Validate fix', status: 'completed', payload: { repo: 'frontend-app', fix_id: 2 }, result: { passed: true, tests: 140 }, created_at: hoursAgo(8), updated_at: hoursAgo(7.95) },
]

// ============================================================
// Indexed Repositories (for indexing page demo)
// ============================================================
export const demoIndexedRepos = [
  { name: 'frontend-app', url: 'https://github.com/my-org/frontend-app', branch: 'main', status: 'indexed', files: 2847, lastIndexed: hoursAgo(24) },
  { name: 'api-service', url: 'https://github.com/my-org/api-service', branch: 'main', status: 'indexed', files: 1853, lastIndexed: hoursAgo(48) },
  { name: 'infra-modules', url: 'https://github.com/my-org/infra-modules', branch: 'main', status: 'indexed', files: 421, lastIndexed: hoursAgo(72) },
  { name: 'mobile-sdk', url: 'https://github.com/my-org/mobile-sdk', branch: 'develop', status: 'pending', files: 0, lastIndexed: null },
]
