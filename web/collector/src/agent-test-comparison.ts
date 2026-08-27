import type {
  AgentTestFetch,
} from './agent-test-bridge'

export type AgentTaskComparisonTransition =
  | 'unchanged-pass'
  | 'pass-to-fail'
  | 'fail-to-pass'
  | 'unchanged-fail'

export type AgentTaskComparisonChange = {
  task_id: string
  baseline_passed: boolean
  candidate_passed: boolean
  transition: AgentTaskComparisonTransition
}

export type AgentRunComparisonChanges = {
  total_tasks: number
  regressions: number
  improvements: number
  unchanged: number
  pass_rate_delta: number | null
  median_latency_ms_delta: number | null
  retry_delta: number
  human_intervention_delta: number
  task_changes: AgentTaskComparisonChange[]
}

export type AgentTemporalComparisonResponse = {
  schema_version: '0.1'
  comparison_type: 'temporal'
  baseline_session_id: string
  candidate_session_id: string
  observer_id: string
  region_code: string
  baseline_started_at_utc: string
  candidate_started_at_utc: string
  changes: AgentRunComparisonChanges
}

export type CompareTemporalAgentRunsInput = {
  baselineSessionId: string
  candidateSessionId: string
}

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === 'object'
    && value !== null
    && !Array.isArray(value)
  )
}

function isNullableNumber(
  value: unknown,
): value is number | null {
  return (
    value === null
    || typeof value === 'number'
  )
}

function isTransition(
  value: unknown,
): value is AgentTaskComparisonTransition {
  return (
    value === 'unchanged-pass'
    || value === 'pass-to-fail'
    || value === 'fail-to-pass'
    || value === 'unchanged-fail'
  )
}

function isTaskChange(
  value: unknown,
): value is AgentTaskComparisonChange {
  if (!isRecord(value)) {
    return false
  }

  return (
    typeof value.task_id === 'string'
    && typeof value.baseline_passed === 'boolean'
    && typeof value.candidate_passed === 'boolean'
    && isTransition(value.transition)
  )
}

function isChanges(
  value: unknown,
): value is AgentRunComparisonChanges {
  if (!isRecord(value)) {
    return false
  }

  return (
    typeof value.total_tasks === 'number'
    && typeof value.regressions === 'number'
    && typeof value.improvements === 'number'
    && typeof value.unchanged === 'number'
    && isNullableNumber(value.pass_rate_delta)
    && isNullableNumber(
      value.median_latency_ms_delta,
    )
    && typeof value.retry_delta === 'number'
    && typeof value.human_intervention_delta
      === 'number'
    && Array.isArray(value.task_changes)
    && value.task_changes.every(isTaskChange)
  )
}

function parseTemporalComparison(
  value: unknown,
): AgentTemporalComparisonResponse {
  if (!isRecord(value)) {
    throw new Error(
      'Invalid Agent Lab comparison payload.',
    )
  }

  if (
    value.schema_version !== '0.1'
    || value.comparison_type !== 'temporal'
    || typeof value.baseline_session_id !== 'string'
    || typeof value.candidate_session_id !== 'string'
    || typeof value.observer_id !== 'string'
    || typeof value.region_code !== 'string'
    || typeof value.baseline_started_at_utc !== 'string'
    || typeof value.candidate_started_at_utc !== 'string'
    || !isChanges(value.changes)
  ) {
    throw new Error(
      'Invalid Agent Lab comparison payload.',
    )
  }

  return value as AgentTemporalComparisonResponse
}

export async function compareTemporalAgentRuns(
  fetchImpl: AgentTestFetch,
  input: CompareTemporalAgentRunsInput,
): Promise<AgentTemporalComparisonResponse> {
  const response = await fetchImpl(
    '/v1/agent-comparisons/temporal',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        baseline_session_id:
          input.baselineSessionId,
        candidate_session_id:
          input.candidateSessionId,
      }),
    },
  )

  if (!response.ok) {
    let message =
      `Agent Lab comparison request failed with HTTP ${response.status}.`

    try {
      const payload = await response.json()

      if (
        isRecord(payload)
        && typeof payload.message === 'string'
        && payload.message.trim() !== ''
      ) {
        message = payload.message
      }
    } catch {
      // Keep the HTTP fallback for invalid bodies.
    }

    throw new Error(message)
  }

  const payload = await response.json()

  return parseTemporalComparison(payload)
}


export type AgentGeographicComparisonResponse = {
  schema_version: '0.1'
  comparison_type: 'geographic'
  baseline_session_id: string
  candidate_session_id: string
  baseline_observer_id: string
  candidate_observer_id: string
  baseline_region_code: string
  candidate_region_code: string
  baseline_started_at_utc: string
  candidate_started_at_utc: string
  observation_skew_seconds: number
  max_observation_skew_seconds: number
  changes: AgentRunComparisonChanges
}

export type CompareGeographicAgentRunsInput = {
  baselineSessionId: string
  candidateSessionId: string
  maxObservationSkewSeconds: number
}

function parseGeographicComparison(
  value: unknown,
): AgentGeographicComparisonResponse {
  if (!isRecord(value)) {
    throw new Error(
      'Invalid Agent Lab comparison payload.',
    )
  }

  if (
    value.schema_version !== '0.1'
    || value.comparison_type !== 'geographic'
    || typeof value.baseline_session_id !== 'string'
    || typeof value.candidate_session_id !== 'string'
    || typeof value.baseline_observer_id !== 'string'
    || typeof value.candidate_observer_id !== 'string'
    || typeof value.baseline_region_code !== 'string'
    || typeof value.candidate_region_code !== 'string'
    || typeof value.baseline_started_at_utc !== 'string'
    || typeof value.candidate_started_at_utc !== 'string'
    || typeof value.observation_skew_seconds !== 'number'
    || typeof value.max_observation_skew_seconds !== 'number'
    || !isChanges(value.changes)
  ) {
    throw new Error(
      'Invalid Agent Lab comparison payload.',
    )
  }

  return value as AgentGeographicComparisonResponse
}

export async function compareGeographicAgentRuns(
  fetchImpl: AgentTestFetch,
  input: CompareGeographicAgentRunsInput,
): Promise<AgentGeographicComparisonResponse> {
  const response = await fetchImpl(
    '/v1/agent-comparisons/geographic',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        baseline_session_id:
          input.baselineSessionId,
        candidate_session_id:
          input.candidateSessionId,
        max_observation_skew_seconds:
          input.maxObservationSkewSeconds,
      }),
    },
  )

  if (!response.ok) {
    let message =
      `Agent Lab comparison request failed with HTTP ${response.status}.`

    try {
      const payload = await response.json()

      if (
        isRecord(payload)
        && typeof payload.message === 'string'
        && payload.message.trim() !== ''
      ) {
        message = payload.message
      }
    } catch {
      // Keep the HTTP fallback for invalid bodies.
    }

    throw new Error(message)
  }

  const payload = await response.json()

  return parseGeographicComparison(payload)
}
