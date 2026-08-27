import type {
  AgentTestFetch,
  AgentTestObservatory,
} from './agent-test-bridge'

export type AgentTestHistoryRun = {
  session_id: string
  started_at_utc: string
  target_id: string
  suite_id: string
  suite_version: string
  observer_id: string | null
  region_code: string | null
  observatory: AgentTestObservatory
  total_tasks: number
  passed_tasks: number
  failed_tasks: number
  pass_rate: number | null
  median_latency_ms: number | null
}

export type AgentTestHistoryResponse = {
  schema_version: '0.1'
  runs: AgentTestHistoryRun[]
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

function isStringArray(
  value: unknown,
): value is string[] {
  return (
    Array.isArray(value)
    && value.every(
      (item) => typeof item === 'string',
    )
  )
}

function isNullableString(
  value: unknown,
): value is string | null {
  return (
    value === null
    || typeof value === 'string'
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

function isObservatory(
  value: unknown,
): value is AgentTestObservatory {
  if (!isRecord(value)) {
    return false
  }

  return (
    typeof value.provenance_complete === 'boolean'
    && typeof value.temporal_eligible === 'boolean'
    && typeof value.geographic_eligible === 'boolean'
    && isStringArray(value.reasons)
  )
}

function isHistoryRun(
  value: unknown,
): value is AgentTestHistoryRun {
  if (!isRecord(value)) {
    return false
  }

  return (
    typeof value.session_id === 'string'
    && typeof value.started_at_utc === 'string'
    && typeof value.target_id === 'string'
    && typeof value.suite_id === 'string'
    && typeof value.suite_version === 'string'
    && isNullableString(value.observer_id)
    && isNullableString(value.region_code)
    && isObservatory(value.observatory)
    && typeof value.total_tasks === 'number'
    && typeof value.passed_tasks === 'number'
    && typeof value.failed_tasks === 'number'
    && isNullableNumber(value.pass_rate)
    && isNullableNumber(value.median_latency_ms)
  )
}

function parseAgentTestHistory(
  value: unknown,
): AgentTestHistoryResponse {
  if (
    !isRecord(value)
    || value.schema_version !== '0.1'
    || !Array.isArray(value.runs)
    || !value.runs.every(isHistoryRun)
  ) {
    throw new Error(
      'Invalid Agent Lab history payload.',
    )
  }

  return value as AgentTestHistoryResponse
}

export async function fetchAgentTestHistory(
  fetchImpl: AgentTestFetch,
): Promise<AgentTestHistoryResponse> {
  const response = await fetchImpl(
    '/v1/agent-tests',
    {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    },
  )

  if (!response.ok) {
    throw new Error(
      `Agent Lab history request failed with HTTP ${response.status}.`,
    )
  }

  const payload = await response.json()

  return parseAgentTestHistory(payload)
}
