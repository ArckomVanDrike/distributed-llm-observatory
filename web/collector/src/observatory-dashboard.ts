import {
  fetchAgentTestHistory,
} from './agent-test-history'

import type {
  AgentTestHistoryResponse,
} from './agent-test-history'

import {
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
