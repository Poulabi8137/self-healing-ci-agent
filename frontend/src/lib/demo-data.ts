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
} from './types'

export const demoSummary: DashboardSummary = {
  system_health: {
    total_workflow_runs: 30,
    overall_success_rate: 70.0,
    average_retries_per_run: 0.4,
  },
  confidence: {
    overall_confidence: 0.85,
  },
}

export const demoMetrics: DashboardMetrics = {
  workflow_metrics: {
    total_retries: 12,
  },
  average_retries: 0.4,
}

export const demoRepos: RepositoryInfo[] = [
  { repository_name: 'frontend-app', total_runs: 12, success_rate: 75.0, avg_confidence: 0.88 },
  { repository_name: 'api-service', total_runs: 8, success_rate: 62.5, avg_confidence: 0.82 },
  { repository_name: 'infra-modules', total_runs: 6, success_rate: 83.3, avg_confidence: 0.91 },
  { repository_name: 'mobile-sdk', total_runs: 4, success_rate: 50.0, avg_confidence: 0.75 },
]

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
  values: [8, 2],
}

export const demoTasks: TaskStatusResponse[] = [
  { id: 1, type: 'Index repository', status: 'completed', payload: { repo: 'frontend-app' }, result: { files: 2847, chunks: 12400 }, created_at: '2026-06-01T10:00:00Z', updated_at: '2026-06-01T10:02:30Z' },
  { id: 2, type: 'Analyze failure', status: 'completed', payload: { repo: 'frontend-app', run_id: 8 }, result: { root_cause: 'Missing environment variable: API_KEY' }, created_at: '2026-06-02T08:15:00Z', updated_at: '2026-06-02T08:15:45Z' },
  { id: 3, type: 'Generate fix', status: 'completed', payload: { repo: 'api-service', run_id: 6 }, result: { patch: 'Changed token refresh interval' }, created_at: '2026-06-02T09:30:00Z', updated_at: '2026-06-02T09:31:20Z' },
  { id: 4, type: 'Create PR', status: 'running', payload: { repo: 'frontend-app', fix_id: 3 }, result: {}, created_at: '2026-06-02T10:00:00Z', updated_at: '2026-06-02T10:00:30Z' },
  { id: 5, type: 'Validate fix', status: 'pending', payload: { repo: 'mobile-sdk', fix_id: 4 }, result: {}, created_at: '2026-06-02T10:05:00Z', updated_at: '2026-06-02T10:05:00Z' },
  { id: 6, type: 'Analyze failure', status: 'completed', payload: { repo: 'infra-modules', run_id: 5 }, result: { root_cause: 'Missing Terraform variable' }, created_at: '2026-06-01T14:00:00Z', updated_at: '2026-06-01T14:00:35Z' },
  { id: 7, type: 'Generate fix', status: 'failed', payload: { repo: 'mobile-sdk', run_id: 3 }, result: { error: 'CocoaPods lockfile conflict' }, created_at: '2026-06-01T16:00:00Z', updated_at: '2026-06-01T16:01:10Z' },
]

export const demoExampleRepo = 'frontend-app'

export const demoExampleLogs = `$ npm run test:ci

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

FAIL  src/integration/auth-flow.test.ts
  ● Auth Flow > should complete login flow
    
    Error: connect ECONNREFUSED 127.0.0.1:3001
    
    > 42 |   const response = await fetch(API_BASE + '/auth/login', {
        |                            ^
      43 |     method: 'POST',
    
      at AuthFlow.login (src/integration/auth-flow.test.ts:42:28)

Tests: 2 failed, 138 passed (140 total)
Test Suites: 2 failed, 18 passed (20 total)
Snapshots: 0 total
Time: 4.235s`

export const demoAnalysisResult: AnalysisResult = {
  root_cause: 'The API_KEY environment variable is not set in the test environment. The ApiService.getApiKey() method throws when the variable is missing, but during CI tests the .env.test file does not include it. Additionally, the integration test environment is not running the mock server on port 3001.',
  error_category: 'config_error',
  confidence: 0.94,
  affected_files: [
    'src/services/api.ts',
    '.env.test',
    'docker-compose.ci.yml',
  ],
}

export const demoFixResult: FixResult = {
  fix_summary: 'Made API_KEY optional during test runs by adding NODE_ENV check. Created .env.test file with demo key. Added test mock server to CI docker-compose.',
  assumptions: [
    'The test environment should use a mock API key',
    'Production deployments always have API_KEY set via secrets manager',
    'The mock server image is available in the CI registry',
  ],
  patch: `diff --git a/.env.test b/.env.test
new file mode 100644
index 0000000..e69de29
--- /dev/null
+++ b/.env.test
@@ -0,0 +1 @@
+API_KEY=demo-test-key-abc123

diff --git a/src/services/api.ts b/src/services/api.ts
index a1b2c3d..e4f5g6h 100644
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
 }

diff --git a/docker-compose.ci.yml b/docker-compose.ci.yml
index 0000000..b1c2d3e
--- /dev/null
+++ b/docker-compose.ci.yml
@@ -0,0 +1,8 @@
+version: '3.8'
+services:
+  mock-server:
+    image: test/mock-server:latest
+    ports:
+      - "3001:3001"
+    environment:
+      - MOCK_MODE=ci`,
}

export const demoValidationResult: ValidationCheckResult = {
  validation: {
    syntax_errors: [],
    build_checks: [],
    failed_tests: [],
    validation_status: 'passed',
  },
  fix_proposal: {
    confidence: 0.96,
  },
}

export const demoPRUrl = 'https://github.com/my-org/frontend-app/pull/124'
export const demoPRNumber = 124

export const demoWorkflowLogsByType: Record<string, { repo: string; logs: string }> = {
  'Missing environment variable': {
    repo: 'frontend-app',
    logs: demoExampleLogs,
  },
  'Dependency version conflict': {
    repo: 'frontend-app',
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
npm ERR! peer lodash@"^4.17.20" from @types/lodash@4.17.0
npm ERR! node_modules/@types/lodash
npm ERR!   dev @types/lodash@"^4.17.0" from the root project
npm ERR!
npm ERR! Fix the upstream dependency conflict.`,
  },
  'TypeScript type mismatch': {
    repo: 'api-service',
    logs: `$ npx tsc --noEmit

src/services/user.service.ts:42:5 - error TS2322: Type 'User | null' is not assignable to type 'User'.
  Type 'null' is not assignable to type 'User'.

42     const user = await this.repository.findById(id)
       ~~~~

src/services/user.service.ts:45:9 - error TS18048: 'user' is possibly 'null'.

45     if (user.role === 'admin') {
           ~~~~

Found 2 errors.`,
  },
  'Docker build failure': {
    repo: 'api-service',
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
  },
  'Failing unit test': {
    repo: 'mobile-sdk',
    logs: `$ xcodebuild test -scheme MobileSDK -destination 'platform=iOS Simulator'

▸ Testing MobileSDKTests
▸ SessionManagerTests
  ✓ testSessionCreation
  ✓ testTokenRefresh
  ✗ testConcurrentSessions (0.042s)
    XCTAssertEqual failed: ("3") is not equal to ("2")
    SessionManager created 3 concurrent sessions instead of the expected 2
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
  },
}
