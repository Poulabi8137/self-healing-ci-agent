export interface DashboardSummary {
  system_health: {
    total_workflow_runs: number
    overall_success_rate: number
    average_retries_per_run: number
  }
  confidence: {
    overall_confidence: number
  }
}

export interface DashboardMetrics {
  workflow_metrics?: {
    total_retries: number
  }
  average_retries?: number
}

export interface RepositoryInfo {
  repository_name: string
  total_runs: number
  success_rate: number
  avg_confidence: number
}

export interface ReviewScores {
  categories: string[]
  scores: number[]
}

export interface ValidationResults {
  labels: string[]
  values: number[]
}

export interface PRStatistics {
  labels: string[]
  values: number[]
}

export interface AnalysisResult {
  root_cause: string
  error_category: string
  confidence: number
  affected_files: string[]
}

export interface FixResult {
  fix_summary: string
  assumptions: string[]
  patch: string
}

export interface ValidationCheckResult {
  validation: {
    syntax_errors: unknown[]
    build_checks: unknown[]
    failed_tests: unknown[]
    validation_status: string
  }
  fix_proposal: {
    confidence: number
  }
}

export interface AuthMeResponse {
  key_prefix: string
  name: string
  role: 'candidate' | 'recruiter' | 'admin'
  created: string
  lastUsed: string | null
}

export interface TaskSubmitResponse {
  task_id: number
  status: string
}

export interface TaskStatusResponse {
  id: number
  type: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  payload: Record<string, unknown>
  result?: Record<string, unknown>
  created_at: string
  updated_at: string
}

export type ActivityType = 'workflow_run' | 'failure_detected' | 'fix_generated' | 'pr_created' | 'validation_passed' | 'validation_failed' | 'retry_attempted' | 'auto_resolved' | 'human_resolved' | 'decision_made' | 'strategy_selected' | 'hypothesis_evaluated' | 'confidence_changed' | 'reassessment' | 'escalation' | 'health_impact'

export interface ActivityItem {
  id: number
  type: ActivityType
  repo: string
  message: string
  timestamp: string
  status: 'success' | 'failure' | 'pending' | 'info'
}

export interface IndexStatusResponse {
  status: string
  indexed_files: number
  last_indexed: string | null
}

export interface TriggerResponse {
  status: string
  message: string
  task_id?: number
}

export interface PRCreateResponse extends TriggerResponse {
  pr_url?: string
  pr_number?: number
}

export interface AnalysisTriggerResponse {
  status: string
  result: AnalysisResult
}

export interface FixTriggerResponse {
  status: string
  result: FixResult
}

export interface ValidationTriggerResponse {
  status: string
  result: ValidationCheckResult
}

// Decision Engine Types
export interface Evidence {
  source: string
  detail: string
  weight: number
}

export interface RootCauseCandidate {
  root_cause: string
  error_category: string
  confidence: number
  affected_files: string[]
  evidence: Evidence[]
  reasoning: string
  score: number
}

export interface StrategyEvaluation {
  fix_summary: string
  assumptions: string[]
  patch: string
  strategy_score: number
  success_probability: number
  risk_level: 'low' | 'medium' | 'high'
  estimated_execution_time: string
  reasoning: string
}

export interface DecisionRecord {
  id: string
  type: 'hypothesis_evaluation' | 'strategy_selection' | 'validation_outcome' | 'reassessment' | 'health_impact'
  context: string
  outcome: string
  confidence_before: number
  confidence_after: number
  rationale: string
  evidence_used: string[]
  timestamp: string
}

export interface SseEvent {
  id: number
  investigation_id: number | null
  event_type: string
  data: Record<string, unknown>
  created_at: string
}

export interface RepositoryStatus {
  full_name: string
  is_active: boolean
  health_status: string
  last_workflow_status: string | null
  failure_count: number
  last_workflow_run_at: string | null
}

export interface BranchNode {
  id: string
  label: string
  type: 'root_cause' | 'strategy' | 'validation' | 'resolution' | 'failure'
  outcome?: string
  children: BranchNode[]
  decision?: DecisionRecord
  status: 'active' | 'completed' | 'failed'
}

// Analytics Types
export interface MTTRData {
  global_mttr_seconds: number
  global_mttr_formatted: string
  total_resolved: number
  per_repository: Record<string, {
    seconds: number
    formatted: string
    investigations_count: number
  }>
}

export interface SuccessRateData {
  global_success_rate: number
  total_investigations: number
  successful_investigations: number
  per_repository: Record<string, {
    rate: number
    total: number
    successful: number
  }>
}

export interface FailureRateData {
  global_failure_rate: number
  total_failures: number
  total_executions: number
  per_repository: Record<string, { failures: number }>
}

export interface AutoHealRateData {
  global_auto_heal_rate: number
  prs_created: number
  failures_detected: number
  per_repository: Record<string, unknown>
}

export interface ValidationAccuracyData {
  overall_accuracy: number
  total_validations: number
  passed_validations: number
  per_type: Record<string, {
    accuracy: number
    total: number
    passed: number
  }>
}

export interface PRAcceptanceRateData {
  global_pr_acceptance_rate: number
  total_prs: number
  merged_prs: number
  per_repository: Record<string, unknown>
}

export interface RepositoryHealthData {
  formula: string
  per_repository: Record<string, {
    score: number
    recent_failures: number
    passed_validations: number
    auto_healed: number
    unresolved_investigations: number
  }>
}

export interface FailureCategoriesData {
  categories: Record<string, number>
  total: number
  breakdown: Record<string, {
    count: number
    percentage: number
  }>
}

export interface AnalyticsOverview {
  mttr: MTTRData
  success_rate: SuccessRateData
  failure_rate: FailureRateData
  auto_heal_rate: AutoHealRateData
  validation_accuracy: ValidationAccuracyData
  pr_acceptance_rate: PRAcceptanceRateData
  repository_health: RepositoryHealthData
  failure_categories: FailureCategoriesData
}
