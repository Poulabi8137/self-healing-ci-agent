// ── Root Cause Candidates (for decision engine evaluation) ──

export interface RootCauseCandidateDef {
  root_cause: string
  error_category: string
  base_confidence: number
  affected_files: string[]
  evidence_sources: string[]
}

export interface StrategyCandidateDef {
  fix_summary: string
  assumptions: string[]
  patch: string
  params: {
    simplicity: number
    coverage: number
    compatibility: number
  }
}

export interface FailureTypeCandidates {
  repo: string
  logs: string
  rootCauseCandidates: RootCauseCandidateDef[]
  strategyCandidates: StrategyCandidateDef[]
}

// ── Evidence sources per error category ──

const EVIDENCE_SOURCES_MAP: Record<string, string[]> = {
  config_error: ['build_logs', 'historical_pattern', 'error_frequency'],
  dependency_error: ['build_logs', 'stack_trace', 'historical_pattern', 'error_frequency'],
  type_error: ['build_logs', 'stack_trace', 'error_frequency'],
  build_error: ['build_logs', 'stack_trace', 'historical_pattern'],
  test_failure: ['build_logs', 'stack_trace', 'historical_pattern', 'error_frequency'],
  infrastructure_error: ['build_logs', 'historical_pattern', 'error_frequency'],
}

// ── Candidate Definitions ──

export const demoRootCauseCandidates: Record<string, RootCauseCandidateDef[]> = {
  'Missing environment variable': [
    {
      root_cause: 'The API_KEY environment variable is not set in the test environment. ApiService.getApiKey() throws when the variable is missing, but .env.test does not include it. The CI runner lacks the secret mapping for test jobs.',
      error_category: 'config_error',
      base_confidence: 0.94,
      affected_files: ['src/services/api.ts', '.env.test', '.github/workflows/ci.yml'],
      evidence_sources: EVIDENCE_SOURCES_MAP.config_error,
    },
    {
      root_cause: 'Missing API_KEY in test environment causing authentication failures with external services. The CI pipeline does not inject test credentials for API calls.',
      error_category: 'config_error',
      base_confidence: 0.89,
      affected_files: ['src/services/api.ts', 'src/services/auth.ts', '.github/workflows/ci.yml'],
      evidence_sources: ['build_logs', 'historical_pattern'],
    },
  ],
  'Dependency version conflict': [
    {
      root_cause: '@types/lodash@4.17.0 requires lodash@4.17.20 as a peer dependency, but the root project specifies lodash@^4.17.21 which resolved to 4.17.21. npm ERESOLVE cannot find a compatible version satisfying both constraints.',
      error_category: 'dependency_error',
      base_confidence: 0.91,
      affected_files: ['package.json'],
      evidence_sources: EVIDENCE_SOURCES_MAP.dependency_error,
    },
    {
      root_cause: 'The lockfile is out of date with package.json. Running npm install introduced lodash@4.17.21 while @types/lodash requires 4.17.20, causing an unresolvable dependency tree conflict.',
      error_category: 'dependency_error',
      base_confidence: 0.88,
      affected_files: ['package.json', 'package-lock.json'],
      evidence_sources: ['build_logs', 'stack_trace'],
    },
  ],
  'TypeScript type mismatch': [
    {
      root_cause: 'TypeScript strict mode catches missing null checks. repository.findById() returns User | null, but the code assigns to User without narrowing. The role check at line 45 also fails because user may be null.',
      error_category: 'type_error',
      base_confidence: 0.97,
      affected_files: ['src/services/user.service.ts'],
      evidence_sources: EVIDENCE_SOURCES_MAP.type_error,
    },
    {
      root_cause: 'The repository.findById method signature was changed to return User | null but the caller at user.service.ts was not updated. TypeScript strict null checks flag the assignment without proper narrowing.',
      error_category: 'type_error',
      base_confidence: 0.93,
      affected_files: ['src/services/user.service.ts', 'src/repositories/user.repository.ts'],
      evidence_sources: ['stack_trace', 'error_frequency'],
    },
  ],
  'Docker build failure': [
    {
      root_cause: '@prisma/client is listed in devDependencies but not in dependencies. During docker build, npm ci installs only dependencies (not devDependencies) when NODE_ENV=production, causing the import to fail at build time.',
      error_category: 'build_error',
      base_confidence: 0.95,
      affected_files: ['package.json', 'Dockerfile'],
      evidence_sources: EVIDENCE_SOURCES_MAP.build_error,
    },
    {
      root_cause: 'The Dockerfile uses a multi-stage build but the node_modules from npm install are not copied to the production stage. @prisma/client is generated during build but the generated client files are missing from the final image.',
      error_category: 'build_error',
      base_confidence: 0.9,
      affected_files: ['Dockerfile', 'package.json'],
      evidence_sources: ['build_logs', 'stack_trace'],
    },
  ],
  'Failing unit test': [
    {
      root_cause: 'SessionManager creates a third session when a race condition occurs in the session creation lock. NetworkManager lacks a retry mechanism for timeout errors — the URLSession timeout fires but the retry logic is not invoked.',
      error_category: 'test_failure',
      base_confidence: 0.89,
      affected_files: ['Sources/SessionManager.swift', 'Sources/NetworkManager.swift'],
      evidence_sources: EVIDENCE_SOURCES_MAP.test_failure,
    },
    {
      root_cause: 'testConcurrentSessions fails because the session counter is incremented before the lock is acquired, causing a race window. testRequestTimeout fails because the URLSession timeout fires before the retry logic is triggered, indicating incorrect delegate method override.',
      error_category: 'test_failure',
      base_confidence: 0.85,
      affected_files: ['Sources/SessionManager.swift', 'Sources/NetworkManager.swift'],
      evidence_sources: ['stack_trace', 'historical_pattern'],
    },
  ],
  'Terraform state lock': [
    {
      root_cause: 'The S3 backend is configured without DynamoDB state locking. When two CI runners attempt to plan simultaneously, the second one fails because the state file is locked by the first operation. The DynamoDB table either does not exist or lacks the correct partition key schema.',
      error_category: 'infrastructure_error',
      base_confidence: 0.93,
      affected_files: ['backend.tf', 'provider.tf'],
      evidence_sources: EVIDENCE_SOURCES_MAP.infrastructure_error,
    },
    {
      root_cause: 'The IAM role used by the CI runner does not have dynamodb:PutItem permission on the state lock table. The DynamoDB table exists but the conditional check fails because the role lacks write access.',
      error_category: 'infrastructure_error',
      base_confidence: 0.87,
      affected_files: ['backend.tf', 'iam-policy.tf'],
      evidence_sources: ['build_logs', 'error_frequency'],
    },
  ],
}

// ── Strategy Candidates (for decision engine evaluation) ──

export const demoStrategyCandidates: Record<string, StrategyCandidateDef[]> = {
  'Missing environment variable': [
    {
      fix_summary: 'Made API_KEY optional during test runs by adding NODE_ENV check. Created .env.test with demo key. Added secrets mapping to CI workflow.',
      assumptions: ['Test environment should use a mock API key', 'Production always sets API_KEY via secrets manager'],
      patch: `diff --git a/.env.test b/.env.test
new file mode 100644
--- /dev/null
+++ b/.env.test
@@ -0,0 +1 @@
+API_KEY=demo-test-key-abc123`,
      params: { simplicity: 0.7, coverage: 0.8, compatibility: 0.9 },
    },
    {
      fix_summary: 'Updated CI workflow to inject API_KEY from GitHub secrets into test jobs. Added fallback logic in ApiService to return a test key when running in CI without requiring NODE_ENV check.',
      assumptions: ['API_KEY secret is configured in GitHub Actions', 'CI workflow has permission to access secrets'],
      patch: `diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml`,
      params: { simplicity: 0.5, coverage: 0.7, compatibility: 0.8 },
    },
  ],
  'Dependency version conflict': [
    {
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
      params: { simplicity: 0.6, coverage: 0.7, compatibility: 0.6 },
    },
    {
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
      params: { simplicity: 0.9, coverage: 0.5, compatibility: 0.8 },
    },
  ],
  'TypeScript type mismatch': [
    {
      fix_summary: 'Added null check guard clause after findById(). Early return when user is null preserves the existing control flow.',
      assumptions: ['Callers handle the early return correctly', 'Null state represents "not found" which is a valid business case'],
      patch: `diff --git a/src/services/user.service.ts b/src/services/user.service.ts`,
      params: { simplicity: 0.8, coverage: 0.6, compatibility: 0.9 },
    },
    {
      fix_summary: 'Updated repository.findById return type to be non-nullable by throwing from the repository layer instead of the service layer. This keeps the null check closer to the data source.',
      assumptions: ['Repository can access the error context', 'Service layer should not handle "not found" cases'],
      patch: `diff --git a/src/repositories/user.repository.ts b/src/repositories/user.repository.ts`,
      params: { simplicity: 0.4, coverage: 0.8, compatibility: 0.7 },
    },
  ],
  'Docker build failure': [
    {
      fix_summary: 'Moved @prisma/client from devDependencies to dependencies. Also added prisma generate step before build in Dockerfile to ensure client is generated.',
      assumptions: ['Prisma client binary is compatible with node:18-alpine', 'Build cache layer ordering is preserved'],
      patch: `diff --git a/Dockerfile b/Dockerfile`,
      params: { simplicity: 0.6, coverage: 0.8, compatibility: 0.7 },
    },
    {
      fix_summary: 'Changed Dockerfile to use npm ci without --only=production so devDependencies are installed during build. Then run prisma generate before the build step.',
      assumptions: ['Installing devDependencies in build stage does not increase image size', 'Dev dependencies are safe to install in CI'],
      patch: `diff --git a/Dockerfile b/Dockerfile`,
      params: { simplicity: 0.5, coverage: 0.6, compatibility: 0.5 },
    },
  ],
  'Failing unit test': [
    {
      fix_summary: 'Added os_unfair_lock to SessionManager for thread-safe session creation. Implemented retryWithDelay on NetworkManager timeout errors using a simple exponential backoff.',
      assumptions: ['iOS 15+ supports os_unfair_lock', 'Retry delay of 0.5s is acceptable for timeout recovery'],
      patch: `diff --git a/Sources/SessionManager.swift b/Sources/SessionManager.swift`,
      params: { simplicity: 0.5, coverage: 0.8, compatibility: 0.8 },
    },
    {
      fix_summary: 'Refactored SessionManager to use actor isolation instead of manual locking. Updated NetworkManager to use async/await with Task.sleep for retry delay, ensuring proper timeout handling.',
      assumptions: ['Swift 5.5+ concurrency features are available', 'Actor isolation resolves the race condition without explicit locking'],
      patch: `diff --git a/Sources/SessionManager.swift b/Sources/SessionManager.swift`,
      params: { simplicity: 0.3, coverage: 0.7, compatibility: 0.9 },
    },
  ],
  'Terraform state lock': [
    {
      fix_summary: 'Added DynamoDB state locking configuration to the S3 backend. Created the DynamoDB table with LockID as the partition key. Added retry logic for state lock acquisition.',
      assumptions: ['DynamoDB table exists in the same region as the S3 bucket', 'IAM role has dynamodb:PutItem and dynamodb:DeleteItem permissions'],
      patch: `diff --git a/backend.tf b/backend.tf`,
      params: { simplicity: 0.4, coverage: 0.9, compatibility: 0.8 },
    },
    {
      fix_summary: 'Added retry logic in CI workflow to handle state lock contention. Configured terraform plan to wait and retry if the state lock is held by another process.',
      assumptions: ['State lock timeouts are temporary', 'Retry with backoff resolves most contention scenarios without changing backend config'],
      patch: `diff --git a/.github/workflows/terraform.yml b/.github/workflows/terraform.yml`,
      params: { simplicity: 0.8, coverage: 0.4, compatibility: 0.9 },
    },
  ],
}
