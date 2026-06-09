import { createContext, useContext, useState, useCallback, type ReactNode } from 'react'
import type { DecisionRecord } from './types'

export type AgentColor = 'emerald' | 'amber' | 'blue' | 'violet' | 'zinc' | 'red' | 'orange' | 'purple' | 'cyan'

export type AgentMode =
  | 'monitoring'
  | 'investigating'
  | 'evaluating_hypotheses'
  | 'comparing_strategies'
  | 'calculating_confidence'
  | 'selecting_remediation_path'
  | 'generating_fix'
  | 'validating'
  | 'validated_pass'
  | 'validated_fail'
  | 'reassessing_after_failure'
  | 'retrying'
  | 'escalating_intervention'
  | 'deciding_next'

export interface AgentState {
  label: string
  context?: string
  color: AgentColor
  mode?: AgentMode
  decision?: string
  rationale?: string
}

interface AgentContextType {
  state: AgentState
  setState: (state: AgentState) => void
  setMode: (mode: AgentMode, label: string, context?: string) => void
  setDecision: (decision: string, rationale: string) => void
  recordDecision: (record: DecisionRecord) => void
  decisions: DecisionRecord[]
  recentActivities: Array<{ type: string; message: string; status: string; timestamp: string }>
  appendActivity: (activity: { type: string; message: string; status: string }) => void
  healthDelta: number
  setHealthDelta: (delta: number) => void
}

const AgentContext = createContext<AgentContextType | null>(null)

const DEFAULT: AgentState = { label: 'Monitoring', color: 'emerald', mode: 'monitoring' }

function now(): string {
  return new Date().toISOString()
}

const MODE_COLORS: Record<string, AgentColor> = {
  monitoring: 'emerald',
  investigating: 'amber',
  evaluating_hypotheses: 'purple',
  comparing_strategies: 'violet',
  calculating_confidence: 'cyan',
  selecting_remediation_path: 'blue',
  generating_fix: 'blue',
  validating: 'violet',
  validated_pass: 'emerald',
  validated_fail: 'red',
  reassessing_after_failure: 'orange',
  retrying: 'amber',
  escalating_intervention: 'red',
  deciding_next: 'orange',
}

export function AgentProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AgentState>(DEFAULT)
  const [decisions, setDecisions] = useState<DecisionRecord[]>([])
  const [activities, setActivities] = useState<Array<{ type: string; message: string; status: string; timestamp: string }>>([])
  const [healthDelta, setHealthDelta] = useState(0)

  const setMode = useCallback((mode: AgentMode, label: string, context?: string) => {
    setState({
      label,
      context,
      color: MODE_COLORS[mode] || 'zinc',
      mode,
    })
  }, [])

  const setDecision = useCallback((decision: string, rationale: string) => {
    setState((prev) => ({
      ...prev,
      decision,
      rationale,
      mode: 'deciding_next',
    }))
  }, [])

  const recordDecision = useCallback((record: DecisionRecord) => {
    setDecisions((prev) => [...prev, record])
    const activityTypeMap: Record<string, string> = {
      hypothesis_evaluation: 'hypothesis_evaluated',
      strategy_selection: 'strategy_selected',
      validation_outcome: record.outcome === 'Validation passed' ? 'validation_passed' : 'validation_failed',
      reassessment: 'reassessment',
      health_impact: 'health_impact',
    }
    const activityType = activityTypeMap[record.type] ?? 'decision_made'
    const messageMap: Record<string, string> = {
      hypothesis_evaluation: `Evaluated root cause: ${record.outcome}`,
      strategy_selection: `Selected strategy: ${record.outcome}`,
      validation_outcome: record.outcome,
      reassessment: `Reassessed: ${record.outcome.substring(0, 100)}`,
      health_impact: `Health impact: ${record.outcome}`,
    }
    const message = messageMap[record.type] ?? record.outcome
    setActivities((prev) => [
      {
        type: activityType,
        message,
        status: record.type === 'reassessment' ? 'failure' : 'success',
        timestamp: now(),
      },
      ...prev,
    ].slice(0, 30))
  }, [])

  const appendActivity = useCallback((activity: { type: string; message: string; status: string }) => {
    setActivities((prev) => [
      { ...activity, timestamp: now() },
      ...prev,
    ].slice(0, 30))
  }, [])

  return (
    <AgentContext.Provider value={{
      state,
      setState,
      setMode,
      setDecision,
      recordDecision,
      decisions,
      recentActivities: activities,
      appendActivity,
      healthDelta,
      setHealthDelta,
    }}>
      {children}
    </AgentContext.Provider>
  )
}

export function useAgent() {
  const ctx = useContext(AgentContext)
  if (!ctx) throw new Error('useAgent must be used within AgentProvider')
  return ctx
}
