import type {
  AgentTestFetch,
} from './agent-test-bridge'

export type ObservatoryObservationPair = {
  baseline_session_id: string
  candidate_session_id: string
  baseline_started_at_utc: string
  candidate_started_at_utc: string
  baseline_observer_id: string | null
  candidate_observer_id: string | null
  baseline_region_code: string | null
  candidate_region_code: string | null
  comparable: boolean
  reasons: string[]
}

export type TemporalObservationPairsResponse = {
  schema_version: '0.1'
  pair_type: 'temporal'
  pairs: ObservatoryObservationPair[]
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

function isNullableString(
  value: unknown,
): value is string | null {
  return (
    value === null
    || typeof value === 'string'
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

function isObservationPair(
  value: unknown,
): value is ObservatoryObservationPair {
  if (!isRecord(value)) {
    return false
  }

  return (
    typeof value.baseline_session_id === 'string'
    && typeof value.candidate_session_id === 'string'
    && typeof value.baseline_started_at_utc === 'string'
    && typeof value.candidate_started_at_utc === 'string'
    && isNullableString(
      value.baseline_observer_id,
    )
    && isNullableString(
      value.candidate_observer_id,
    )
    && isNullableString(
      value.baseline_region_code,
    )
    && isNullableString(
      value.candidate_region_code,
    )
    && typeof value.comparable === 'boolean'
    && isStringArray(value.reasons)
  )
}

function parseTemporalObservationPairs(
  value: unknown,
): TemporalObservationPairsResponse {
  if (
    !isRecord(value)
    || value.schema_version !== '0.1'
    || value.pair_type !== 'temporal'
    || !Array.isArray(value.pairs)
    || !value.pairs.every(isObservationPair)
  ) {
    throw new Error(
      'Invalid Observatory temporal pair payload.',
    )
  }

  return value as TemporalObservationPairsResponse
}

export async function fetchTemporalObservationPairs(
  fetchImpl: AgentTestFetch,
): Promise<TemporalObservationPairsResponse> {
  const response = await fetchImpl(
    '/v1/agent-observation-pairs/temporal',
    {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    },
  )

  if (!response.ok) {
    throw new Error(
      `Observatory temporal pair request failed with HTTP ${response.status}.`,
    )
  }

  const payload = await response.json()

  return parseTemporalObservationPairs(payload)
}


export type GeographicObservationPairsResponse = {
  schema_version: '0.1'
  pair_type: 'geographic'
  max_observation_skew_seconds: number
  pairs: ObservatoryObservationPair[]
}

export type FetchGeographicObservationPairsInput = {
  maxObservationSkewSeconds: number
}

function parseGeographicObservationPairs(
  value: unknown,
): GeographicObservationPairsResponse {
  if (
    !isRecord(value)
    || value.schema_version !== '0.1'
    || value.pair_type !== 'geographic'
    || typeof value.max_observation_skew_seconds
      !== 'number'
    || !Array.isArray(value.pairs)
    || !value.pairs.every(isObservationPair)
  ) {
    throw new Error(
      'Invalid Observatory geographic pair payload.',
    )
  }

  return value as GeographicObservationPairsResponse
}

export async function fetchGeographicObservationPairs(
  fetchImpl: AgentTestFetch,
  input: FetchGeographicObservationPairsInput,
): Promise<GeographicObservationPairsResponse> {
  const response = await fetchImpl(
    (
      '/v1/agent-observation-pairs/geographic'
      + '?max_observation_skew_seconds='
      + encodeURIComponent(
        String(input.maxObservationSkewSeconds),
      )
    ),
    {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    },
  )

  if (!response.ok) {
    let message =
      `Observatory geographic pair request failed with HTTP ${response.status}.`

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

  return parseGeographicObservationPairs(payload)
}
