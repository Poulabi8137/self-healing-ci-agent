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

export interface BranchNode {
  id: string
  label: string
  type: 'root_cause' | 'strategy' | 'validation' | 'resolution' | 'failure'
  outcome?: string
  children: BranchNode[]
  decision?: DecisionRecord
  status: 'active' | 'completed' | 'failed'
}
