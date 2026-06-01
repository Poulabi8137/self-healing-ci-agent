import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useAuth } from './auth'

const API_BASE = '/api'

export class ApiError extends Error {
  status: number
  body: unknown

  constructor(status: number, body: unknown) {
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
    throw new ApiError(401, await res.json().catch(() => null))
  }

  if (!res.ok) {
    throw new ApiError(res.status, await res.json().catch(() => null))
  }

  return res.json()
}

// ========================
// Dashboard Queries
// ========================

export function useDashboardSummary() {
  const { apiKey } = useAuth()
  return useQuery<Record<string, unknown>>({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => fetchJson('/dashboard/summary', getKey(apiKey)),
    enabled: !!apiKey,
    refetchInterval: 30_000,
  })
}

export function useDashboardMetrics() {
  const { apiKey } = useAuth()
  return useQuery<Record<string, unknown>>({
    queryKey: ['dashboard', 'metrics'],
    queryFn: () => fetchJson('/dashboard/metrics', getKey(apiKey)),
    enabled: !!apiKey,
    refetchInterval: 30_000,
  })
}

export function useDashboardRepositories() {
  const { apiKey } = useAuth()
  return useQuery<Record<string, unknown>[]>({
    queryKey: ['dashboard', 'repositories'],
    queryFn: () => fetchJson('/dashboard/repositories', getKey(apiKey)),
    enabled: !!apiKey,
    refetchInterval: 30_000,
  })
}

export function useChartData(endpoint: string) {
  const { apiKey } = useAuth()
  return useQuery<Record<string, unknown>>({
    queryKey: ['dashboard', 'charts', endpoint],
    queryFn: () => fetchJson(`/dashboard/charts/${endpoint}`, getKey(apiKey)),
    enabled: !!apiKey,
    refetchInterval: 30_000,
  })
}

// ========================
// Analysis Mutations
// ========================

export function useTriggerAnalysis() {
  const { apiKey } = useAuth()
  const queryClient = useQueryClient()
  return useMutation<Record<string, unknown>, Error, { repository_name: string; logs: string }>({
    mutationFn: (data) =>
      fetchJson('/analysis/debug', getKey(apiKey), {
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
  return useMutation<Record<string, unknown>, Error, { repository_name: string; logs: string }>({
    mutationFn: (data) =>
      fetchJson('/fix/generate', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

// ========================
// Validation Mutation
// ========================

export function useTriggerValidation() {
  const { apiKey } = useAuth()
  return useMutation<Record<string, unknown>, Error, { repository_name: string; logs: string }>({
    mutationFn: (data) =>
      fetchJson('/validation/run', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

// ========================
// Retry Mutation
// ========================

export function useTriggerRetry() {
  const { apiKey } = useAuth()
  return useMutation<Record<string, unknown>, Error, { repository_name: string; logs: string }>({
    mutationFn: (data) =>
      fetchJson('/retry/run', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

// ========================
// Review Mutation
// ========================

export function useTriggerReview() {
  const { apiKey } = useAuth()
  return useMutation<Record<string, unknown>, Error, { repository_name: string; logs: string }>({
    mutationFn: (data) =>
      fetchJson('/review/run', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

// ========================
// PR Mutation
// ========================

export function useTriggerPR() {
  const { apiKey } = useAuth()
  return useMutation<Record<string, unknown>, Error, { repository_name: string; logs: string; dry_run: boolean; approved: boolean }>({
    mutationFn: (data) =>
      fetchJson('/pr/create', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

// ========================
// Indexing Mutations
// ========================

export function useTriggerIndex() {
  const { apiKey } = useAuth()
  return useMutation<Record<string, unknown>, Error, { repo_url: string; branch?: string | null }>({
    mutationFn: (data) =>
      fetchJson('/rag/index', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

export function useIndexStatus(repoName: string) {
  const { apiKey } = useAuth()
  return useQuery<Record<string, unknown>>({
    queryKey: ['rag', 'index', repoName],
    queryFn: () => fetchJson(`/rag/index/${repoName}/status`, getKey(apiKey)),
    enabled: !!apiKey && !!repoName,
  })
}

// ========================
// Task Queries
// ========================

export function useSubmitTask() {
  const { apiKey } = useAuth()
  return useMutation<Record<string, unknown>, Error, { type: string; payload: Record<string, unknown> }>({
    mutationFn: (data) =>
      fetchJson('/tasks/submit', getKey(apiKey), {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  })
}

export function useTaskStatus(taskId: number | null) {
  const { apiKey } = useAuth()
  return useQuery<Record<string, unknown>>({
    queryKey: ['tasks', taskId],
    queryFn: () => fetchJson(`/tasks/${taskId}`, getKey(apiKey)),
    enabled: !!apiKey && taskId !== null,
    refetchInterval: (query) => {
      const s = query.state.data?.status
      return s === 'pending' || s === 'running' ? 2000 : false
    },
  })
}

export function useTaskList() {
  const { apiKey } = useAuth()
  return useQuery<Record<string, unknown>[]>({
    queryKey: ['tasks'],
    queryFn: () => fetchJson('/tasks/', getKey(apiKey)),
    enabled: !!apiKey,
    refetchInterval: 10_000,
  })
}

// ========================
// Auth Queries
// ========================

export function useAuthMe() {
  const { apiKey } = useAuth()
  return useQuery<Record<string, unknown>>({
    queryKey: ['auth', 'me'],
    queryFn: () => fetchJson('/auth/me', getKey(apiKey)),
    enabled: !!apiKey,
  })
}
