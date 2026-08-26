export type AgentTestObservatory = {
  provenance_complete: boolean
  temporal_eligible: boolean
  geographic_eligible: boolean
  reasons: string[]
}

export type AgentTestBridgeResponse = {
  schema_version: '0.1'
  status: 'completed'
  started_at_utc: string
  session_id: string
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
  findings: string[]
  recommendations: string[]
}

export type AgentTestFetchResponse = {
  ok: boolean
  status: number
  json(): Promise<unknown>
}

export type AgentTestFetch = (
  input: string,
  init?: RequestInit,
) => Promise<AgentTestFetchResponse>

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

function parseAgentTestResponse(
  value: unknown,
): AgentTestBridgeResponse {
  if (!isRecord(value)) {
    throw new Error(
      'Invalid Agent Lab bridge payload.',
    )
  }

  if (
    value.schema_version !== '0.1'
    || value.status !== 'completed'
    || typeof value.started_at_utc !== 'string'
    || typeof value.session_id !== 'string'
    || typeof value.target_id !== 'string'
    || typeof value.suite_id !== 'string'
    || typeof value.suite_version !== 'string'
    || !isNullableString(value.observer_id)
    || !isNullableString(value.region_code)
    || !isObservatory(value.observatory)
    || typeof value.total_tasks !== 'number'
    || typeof value.passed_tasks !== 'number'
    || typeof value.failed_tasks !== 'number'
    || !isNullableNumber(value.pass_rate)
    || !isNullableNumber(value.median_latency_ms)
    || !isStringArray(value.findings)
    || !isStringArray(value.recommendations)
  ) {
    throw new Error(
      'Invalid Agent Lab bridge payload.',
    )
  }

  return value as AgentTestBridgeResponse
}

export async function runAgentTest(
  fetchImpl: AgentTestFetch,
  baseUrl: string,
): Promise<AgentTestBridgeResponse> {
  const response = await fetchImpl(
    '/v1/agent-tests',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify({
        base_url: baseUrl,
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      `Agent Lab bridge request failed with HTTP ${response.status}.`,
    )
  }

  const payload = await response.json()

  return parseAgentTestResponse(payload)
}
