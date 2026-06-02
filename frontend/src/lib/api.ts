import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from './auth-context'
import type {
  DashboardSummary,
  DashboardMetrics,
  RepositoryInfo,
  ReviewScores,
  ValidationResults,
  PRStatistics,
  AuthMeResponse,
  TaskSubmitResponse,
  TaskStatusResponse,
  IndexStatusResponse,
  TriggerResponse,
  PRCreateResponse,
} from './types'

const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

export class ApiError extends Error {
  status: number
  body: Record<string, unknown>

  constructor(status: number, body: Record<string, unknown>) {
    super(`API error: ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.body = body
  }
}

function getKey(apiKey: string | null) {
  return apiKey ?? ''
}

async function fetchJson<T>(
  path: string,
  apiKey: string,
  options?: RequestInit,
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(apiKey ? { 'X-API-Key': apiKey } : {}),
      ...options?.headers,
    },
  })

  if (res.status === 401) {
    throw new ApiError(401, await res.json().catch(() => ({})))
  }

  if (!res.ok) {
    throw new ApiError(res.status, await res.json().catch(() => ({})))
  }

  return res.json() as Promise<T>
}

export function useDashboardSummary() {
  const { apiKey } = useAuth()
  return useQuery<DashboardSummary>({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => fetchJson<DashboardSummary>('/dashboard/summary', getKey(apiKey)),
    enabled: !!apiKey,
    refetchInterval: 30_000,
  })
}

export function useDashboardMetrics() {
  const { apiKey } = useAuth()
  return useQuery<DashboardMetrics>({
    queryKey: ['dashboard', 'metrics'],
    queryFn: () => fetchJson<DashboardMetrics>('/dashboard/metrics', getKey(apiKey)),
    enabled: !!apiKey,
    refetchInterval: 30_000,
  })
}

export function useDashboardRepositories() {
  const { apiKey } = useAuth()
  return useQuery<RepositoryInfo[]>({
    queryKey: ['dashboard', 'repositories'],
    queryFn: () => fetchJson<RepositoryInfo[]>('/dashboard/repositories', getKey(apiKey)),
    enabled: !!apiKey,
    refetchInterval: 30_000,
  })
}

export function useChartData<T>(endpoint: string) {
  const { apiKey } = useAuth()
  return useQuery<T>({
    queryKey: ['dashboard', 'charts', endpoint],
    queryFn: () => fetchJson<T>(`/dashboard/charts/${endpoint}`, getKey(apiKey)),
    enabled: !!apiKey,
    refetchInterval: 30_000,
  })
}

export function useReviewScores() {
  return useChartData<ReviewScores>('review-scores')
}

export function useValidationResults() {
  return useChartData<ValidationResults>('validation-results')
}

export function usePRStatistics() {
  return useChartData<PRStatistics>('pr-statistics')
}

export function useTriggerAnalysis() {
  const { apiKey } = useAuth()
  const queryClient = useQueryClient()
  return useMutation<TriggerResponse, Error, { repository_name: string; logs: string }>({
    mutationFn: (data) =>
      fetchJson<TriggerResponse>('/analysis/debug', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useTriggerFix() {
  const { apiKey } = useAuth()
  return useMutation<TriggerResponse, Error, { repository_name: string; logs: string }>({
    mutationFn: (data) =>
      fetchJson<TriggerResponse>('/fix/generate', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

export function useTriggerValidation() {
  const { apiKey } = useAuth()
  return useMutation<TriggerResponse, Error, { repository_name: string; logs: string }>({
    mutationFn: (data) =>
      fetchJson<TriggerResponse>('/validation/run', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

export function useTriggerRetry() {
  const { apiKey } = useAuth()
  return useMutation<TriggerResponse, Error, { repository_name: string; logs: string }>({
    mutationFn: (data) =>
      fetchJson<TriggerResponse>('/retry/run', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

export function useTriggerReview() {
  const { apiKey } = useAuth()
  return useMutation<TriggerResponse, Error, { repository_name: string; logs: string }>({
    mutationFn: (data) =>
      fetchJson<TriggerResponse>('/review/run', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

export function useTriggerPR() {
  const { apiKey } = useAuth()
  return useMutation<PRCreateResponse, Error, { repository_name: string; logs: string; dry_run: boolean; approved: boolean }>({
    mutationFn: (data) =>
      fetchJson<PRCreateResponse>('/pr/create', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

export function useTriggerIndex() {
  const { apiKey } = useAuth()
  return useMutation<TriggerResponse, Error, { repo_url: string; branch?: string | null }>({
    mutationFn: (data) =>
      fetchJson<TriggerResponse>('/rag/index', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

export function useIndexStatus(repoName: string) {
  const { apiKey } = useAuth()
  return useQuery<IndexStatusResponse>({
    queryKey: ['rag', 'index', repoName],
    queryFn: () => fetchJson<IndexStatusResponse>(`/rag/index/${repoName}/status`, getKey(apiKey)),
    enabled: !!apiKey && !!repoName,
  })
}

export function useSubmitTask() {
  const { apiKey } = useAuth()
  return useMutation<TaskSubmitResponse, Error, { type: string; payload: Record<string, unknown> }>({
    mutationFn: (data) =>
      fetchJson<TaskSubmitResponse>('/tasks/submit', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

export function useTaskStatus(taskId: number | null) {
  const { apiKey } = useAuth()
  return useQuery<TaskStatusResponse>({
    queryKey: ['tasks', taskId],
    queryFn: () => fetchJson<TaskStatusResponse>(`/tasks/${taskId}`, getKey(apiKey)),
    enabled: !!apiKey && taskId !== null,
    refetchInterval: (query) => {
      const s = query.state.data?.status
      return s === 'pending' || s === 'running' ? 2000 : false
    },
  })
}

export function useTaskList() {
  const { apiKey } = useAuth()
  return useQuery<TaskStatusResponse[]>({
    queryKey: ['tasks'],
    queryFn: () => fetchJson<TaskStatusResponse[]>('/tasks/', getKey(apiKey)),
    enabled: !!apiKey,
    refetchInterval: 10_000,
  })
}

export function useAuthMe() {
  const { apiKey } = useAuth()
  return useQuery<AuthMeResponse>({
    queryKey: ['auth', 'me'],
    queryFn: () => fetchJson<AuthMeResponse>('/auth/me', getKey(apiKey)),
    enabled: !!apiKey,
  })
}
