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
  created_at: string
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
