import {
  fetchAgentTestHistory,
} from './agent-test-history'

import type {
  AgentTestHistoryResponse,
} from './agent-test-history'

import {
  fetchGeographicObservationPairs,
  fetchTemporalObservationPairs,
} from './observatory-pairs'

import type {
  TemporalObservationPairsResponse,
} from './observatory-pairs'

import type {
  AgentTestFetch,
} from './agent-test-bridge'

export type ObservatoryDashboardData = {
  history: AgentTestHistoryResponse
  temporalPairs: TemporalObservationPairsResponse
}

export async function loadObservatoryDashboard(
  fetchImpl: AgentTestFetch,
): Promise<ObservatoryDashboardData> {
  const history = await fetchAgentTestHistory(
    fetchImpl,
  )

  const temporalPairs =
    await fetchTemporalObservationPairs(
      fetchImpl,
    )

  return {
    history,
    temporalPairs,
  }
}


export function parseGeographicMaxSkewInput(
  value: string,
): number | null {
  const normalized = value.trim()

  if (normalized === '') {
    return null
  }

  const parsed = Number(normalized)

  if (
    !Number.isFinite(parsed)
    || parsed < 0
  ) {
    return null
  }

  return parsed
}


export async function discoverObservatoryGeographicPairs(
  fetchImpl: AgentTestFetch,
  maxSkewInput: string,
) {
  const maxObservationSkewSeconds =
    parseGeographicMaxSkewInput(
      maxSkewInput,
    )

  if (maxObservationSkewSeconds === null) {
    throw new Error(
      'Maximum observation skew is required.',
    )
  }

  return fetchGeographicObservationPairs(
    fetchImpl,
    {
      maxObservationSkewSeconds,
    },
  )
}
