import type { RepositoryInfo } from './types'

// ── Decision Types ────────────────────────────────────────────

export interface Evidence {
  source: string
  detail: string
  weight: number // 0-1 how strongly this evidence points to this conclusion
}

export interface RootCauseCandidate {
  root_cause: string
  error_category: string
  confidence: number
  affected_files: string[]
  evidence: Evidence[]
  reasoning: string
  score: number // aggregate score from evaluation
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

// ── Helpers ───────────────────────────────────────────────────

interface HealthParams {
  risk_level: 'low' | 'medium' | 'high'
  repo_health: number
  affected_files_count: number
  historical_success_rate: number
}

interface StrategyParams {
  simplicity: number
  coverage: number
  compatibility: number
}

// ── Decision Engine ───────────────────────────────────────────

export class DecisionEngine {
  private decisions: DecisionRecord[] = []
  private branches: BranchNode[] = []

  /**
   * Evaluate root cause candidates and rank them based on evidence, confidence, and context.
   */
  evaluateRootCauses(
    candidates: Array<{
      root_cause: string
      error_category: string
      base_confidence: number
      affected_files: string[]
      evidence_sources: string[]
    }>,
    repoHealth: number,
    historicalSuccessRate: number
  ): RootCauseCandidate[] {
    return candidates.map((c) => {
      const evidence: Evidence[] = c.evidence_sources.map((source) => ({
        source,
        detail: this.getEvidenceDetail(source, c.error_category),
        weight: this.calculateEvidenceWeight(source, c.error_category),
      }))

      const evidenceScore = evidence.reduce((sum, e) => sum + e.weight, 0) / evidence.length
      const fileComplexity = Math.min(c.affected_files.length / 5, 1)
      const healthFactor = repoHealth / 100
      const historyFactor = historicalSuccessRate / 100

      const score =
        c.base_confidence * 0.4 +
        evidenceScore * 0.3 +
        healthFactor * 0.15 +
        historyFactor * 0.15

      const confidence = Math.min(0.99, score - fileComplexity * 0.05)

      const reasoning = this.buildReasoning(c, evidence, confidence)

      return {
        root_cause: c.root_cause,
        error_category: c.error_category,
        confidence: Math.round(confidence * 100) / 100,
        affected_files: c.affected_files,
        evidence,
        reasoning,
        score: Math.round(score * 100) / 100,
      }
    }).sort((a, b) => b.score - a.score)
  }

  /**
   * Evaluate fix strategies and score them based on effectiveness, risk, and context.
   */
  evaluateStrategies(
    _rootCause: RootCauseCandidate,
    strategies: Array<{
      fix_summary: string
      assumptions: string[]
      patch: string
      params: StrategyParams
    }>,
    health: HealthParams
  ): StrategyEvaluation[] {
    return strategies.map((s) => {
      const simplicityScore = s.params.simplicity
      const coverageScore = s.params.coverage
      const compatibilityScore = s.params.compatibility
      const riskPenalty = health.risk_level === 'high' ? 0.15 : health.risk_level === 'medium' ? 0.08 : 0
      const healthBoost = health.repo_health / 100 * 0.1
      const filePenalty = Math.min(health.affected_files_count / 10, 0.2)
      const historyBoost = health.historical_success_rate / 100 * 0.1

      const rawScore =
        simplicityScore * 0.25 +
        coverageScore * 0.35 +
        compatibilityScore * 0.2 -
        riskPenalty +
        healthBoost -
        filePenalty +
        historyBoost

      const strategy_score = Math.max(0, Math.min(1, rawScore))
      const success_probability = Math.max(0.05, Math.min(0.99, rawScore + 0.1))
      const risk_level: 'low' | 'medium' | 'high' =
        rawScore > 0.7 ? 'low' : rawScore > 0.4 ? 'medium' : 'high'

      const estimated_minutes = Math.round(
        3 + (1 - simplicityScore) * 5 + (risk_level === 'high' ? 5 : 0)
      )
      const estimated_execution_time = `${estimated_minutes}m`

      // Build reasoning based on which factors influenced the score most
      const factors: string[] = []
      if (simplicityScore > 0.7) factors.push('simple implementation')
      if (coverageScore > 0.7) factors.push('comprehensive coverage')
      if (compatibilityScore > 0.7) factors.push('high compatibility')
      if (riskPenalty > 0 && health.risk_level === 'high') factors.push('adjusted for high risk environment')

      const reasoning = `Strategy score ${(strategy_score * 100).toFixed(0)}%: ${factors.join(', ') || 'balanced approach'}. ` +
        `Estimated success probability ${(success_probability * 100).toFixed(0)}% based on ${health.affected_files_count} affected files ` +
        `and repository health at ${health.repo_health.toFixed(0)}%.`

      return {
        fix_summary: s.fix_summary,
        assumptions: s.assumptions,
        patch: s.patch,
        strategy_score: Math.round(strategy_score * 100) / 100,
        success_probability: Math.round(success_probability * 100) / 100,
        risk_level,
        estimated_execution_time,
        reasoning,
      }
    }).sort((a, b) => b.strategy_score - a.strategy_score)
  }

  /**
   * Determine validation outcome using conditions, not randomness.
   */
  evaluateValidation(
    strategy: StrategyEvaluation,
    rootCause: RootCauseCandidate,
    repoHealth: number,
    previousAttempts: number
  ): { passed: boolean; failure_reason?: string; confidence_impact: number } {
    const baseChance = strategy.success_probability
    const healthFactor = repoHealth / 100 * 0.1
    const learningFactor = Math.min(previousAttempts * 0.05, 0.2)
    const complexityPenalty = Math.min(rootCause.affected_files.length * 0.02, 0.1)
    const confidenceBoost = rootCause.confidence * 0.1

    const effectiveChance = baseChance + healthFactor + learningFactor - complexityPenalty + confidenceBoost

    const passed = effectiveChance >= 0.65
    const confidence_impact = passed ? 0.05 : -0.15

    let failure_reason: string | undefined
    if (!passed) {
      const reasons = [
        `Test execution failed — ${strategy.risk_level === 'high' ? 'high complexity strategy needs refinement' : 'edge case not covered'}`,
        `Build check failed — ${rootCause.affected_files.length} affected files require additional validation`,
        `Integration test failure — compatibility issue with existing codebase at health ${repoHealth.toFixed(0)}%`,
      ]
      const idx = Math.floor(effectiveChance * 10) % reasons.length
      failure_reason = reasons[idx]
    }

    return { passed, failure_reason, confidence_impact }
  }

  /**
   * Reassess after failure: reduce confidence, re-rank hypotheses, select new strategy.
   */
  reassessAfterFailure(
    previousRootCause: RootCauseCandidate,
    previousStrategy: StrategyEvaluation,
    failureReason: string,
    allCandidates: RootCauseCandidate[],
    _repoHealth: RepositoryHealth
  ): {
    updatedCandidates: RootCauseCandidate[]
    selectedStrategy: StrategyEvaluation | null
    learning: string
  } {
    // Reduce confidence in the failed hypothesis
    const updatedCandidates = allCandidates.map((c) => {
      if (c.root_cause === previousRootCause.root_cause) {
        return {
          ...c,
          confidence: Math.max(0.1, c.confidence - 0.15),
          evidence: [
            ...c.evidence,
            { source: 'failure_analysis', detail: failureReason, weight: 0.3 },
          ],
          reasoning: c.reasoning + ` (reassessed: confidence reduced after validation failure: ${failureReason})`,
          score: Math.max(0, c.score - 0.15),
        }
      }
      // Boost confidence in alternative hypotheses
      return {
        ...c,
        confidence: Math.min(0.95, c.confidence + 0.1),
        score: Math.min(1, c.score + 0.1),
      }
    }).sort((a, b) => b.score - a.score)

    const learning = `Validation of "${previousStrategy.fix_summary.substring(0, 60)}..." failed: ${failureReason}. ` +
      `Confidence in "${previousRootCause.root_cause.substring(0, 60)}..." reduced from ` +
      `${(previousRootCause.confidence * 100).toFixed(0)}% to ${(updatedCandidates[0].confidence * 100).toFixed(0)}%. ` +
      `Re-ranking hypotheses — best candidate now: "${updatedCandidates[0].error_category}" ` +
      `with confidence ${(updatedCandidates[0].confidence * 100).toFixed(0)}%.`

    // No strategy selected yet — caller will call evaluateStrategies with the new top candidate
    return { updatedCandidates, selectedStrategy: null, learning }
  }

  /**
   * Calculate health impact based on outcome.
   */
  calculateHealthImpact(
    repo: RepositoryInfo,
    outcome: 'success' | 'failure',
    _confidence: number
  ): { health_delta: number; risk_delta: number; confidence_delta: number } {
    if (outcome === 'success') {
      return {
        health_delta: Math.min(5, Math.round((1 - repo.success_rate / 100) * 3 * 10) / 10),
        risk_delta: -0.05,
        confidence_delta: 0.03,
      }
    } else {
      return {
        health_delta: -Math.min(8, Math.round((repo.success_rate / 100) * 5 * 10) / 10),
        risk_delta: 0.08,
        confidence_delta: -0.05,
      }
    }
  }

  /**
   * Record a decision for the decision history.
   */
  recordDecision(
    type: DecisionRecord['type'],
    context: string,
    outcome: string,
    confidence_before: number,
    confidence_after: number,
    rationale: string,
    evidence_used: string[]
  ): DecisionRecord {
    const decision: DecisionRecord = {
      id: `dec-${this.decisions.length + 1}`,
      type,
      context,
      outcome,
      confidence_before: Math.round(confidence_before * 100) / 100,
      confidence_after: Math.round(confidence_after * 100) / 100,
      rationale,
      evidence_used,
      timestamp: new Date().toISOString(),
    }
    this.decisions.push(decision)
    return decision
  }

  /**
   * Add a branch node to the decision tree.
   */
  addBranchNode(
    parentId: string | null,
    label: string,
    type: BranchNode['type'],
    outcome?: string,
    decision?: DecisionRecord
  ): BranchNode {
    const node: BranchNode = {
      id: `branch-${this.branches.length + 1}-${Date.now()}`,
      label,
      type,
      outcome,
      children: [],
      decision,
      status: type === 'failure' ? 'failed' : type === 'resolution' ? 'completed' : 'active',
    }

    if (parentId) {
      const parent = this.findBranchNode(parentId)
      if (parent) {
        parent.children.push(node)
      }
    } else {
      this.branches.push(node)
    }

    return node
  }

  getDecisions(): DecisionRecord[] {
    return [...this.decisions]
  }

  getBranches(): BranchNode[] {
    return [...this.branches]
  }

  // ── Private Helpers ─────────────────────────────────────────

  private findBranchNode(id: string): BranchNode | undefined {
    const search = (nodes: BranchNode[]): BranchNode | undefined => {
      for (const node of nodes) {
        if (node.id === id) return node
        const found = search(node.children)
        if (found) return found
      }
      return undefined
    }
    return search(this.branches)
  }

  private getEvidenceDetail(source: string, category: string): string {
    const details: Record<string, Record<string, string>> = {
      'build_logs': {
        config_error: 'CI config references missing environment variable',
        dependency_error: 'npm ERESOLVE detected in build output',
        type_error: 'TypeScript compiler errors found in build logs',
        build_error: 'Docker build step failed with non-zero exit code',
        test_failure: 'Test runner exited with test failures',
        infrastructure_error: 'Terraform state lock error in plan output',
      },
      'stack_trace': {
        type_error: 'Stack trace points to type narrowing failure',
        build_error: 'Stack trace shows module resolution failure',
        test_failure: 'Stack trace shows assertion failure location',
      },
      'historical_pattern': {
        config_error: 'Similar config error resolved 2 times in last month',
        dependency_error: 'Dependency conflict pattern matches 3 previous incidents',
        type_error: 'Type error pattern matches common migration issue',
        build_error: 'Build failure pattern matches known Docker caching issue',
        test_failure: 'Test flakiness pattern matches 2 previous incidents',
        infrastructure_error: 'Infrastructure error pattern matches 1 previous incident',
      },
      'error_frequency': {
        config_error: 'Error occurs in 30% of test runs',
        dependency_error: 'Error occurs on every npm install',
        type_error: 'Error occurs on every tsc run',
        build_error: 'Error occurs in 50% of Docker builds',
        test_failure: 'Error occurs intermittently in CI',
        infrastructure_error: 'Error occurs during concurrent CI runs',
      },
    }
    return details[source]?.[category] || `Evidence from ${source}`
  }

  private calculateEvidenceWeight(source: string, _category: string): number {
    const baseWeights: Record<string, number> = {
      build_logs: 0.8,
      stack_trace: 0.9,
      historical_pattern: 0.6,
      error_frequency: 0.5,
    }
    return baseWeights[source] || 0.5
  }

  private buildReasoning(
    candidate: { root_cause: string; error_category: string; base_confidence: number; affected_files: string[] },
    evidence: Evidence[],
    confidence: number
  ): string {
    const topEvidence = evidence.slice(0, 2).map((e) => e.detail)
    return `Root cause identified as "${candidate.error_category}" with ${(confidence * 100).toFixed(0)}% confidence. ` +
      `Key evidence: ${topEvidence.join('; ')}. ` +
      `${candidate.affected_files.length} affected files identified. ` +
      `Base confidence ${(candidate.base_confidence * 100).toFixed(0)}% adjusted for repository health and historical patterns.`
  }
}

export interface RepositoryHealth {
  risk_level: 'low' | 'medium' | 'high'
  repo_health: number
  affected_files_count: number
  historical_success_rate: number
}

// Singleton instance
let engineInstance: DecisionEngine | null = null

export function getDecisionEngine(): DecisionEngine {
  if (!engineInstance) {
    engineInstance = new DecisionEngine()
  }
  return engineInstance
}

// Reset for testing
export function resetDecisionEngine(): void {
  engineInstance = null
}
