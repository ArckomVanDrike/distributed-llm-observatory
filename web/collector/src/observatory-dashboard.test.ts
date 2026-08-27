import {
  expect,
  it,
} from 'vitest'

import {
  loadObservatoryDashboard,
} from './observatory-dashboard'

it('loads history and temporal pairs without geographic discovery', async () => {
  const calls: string[] = []

  const fakeFetch = async (
    input: string,
  ) => {
    calls.push(input)

    if (input === '/v1/agent-tests') {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          schema_version: '0.1',
          runs: [],
        }),
      }
    }

    if (
      input
      === '/v1/agent-observation-pairs/temporal'
    ) {
      return {
        ok: true,
        status: 200,
        json: async () => ({
          schema_version: '0.1',
          pair_type: 'temporal',
          pairs: [],
        }),
      }
    }

    throw new Error(
      `Unexpected request: ${input}`,
    )
  }

  const result =
    await loadObservatoryDashboard(
      fakeFetch,
    )

  expect(calls).toEqual([
    '/v1/agent-tests',
    '/v1/agent-observation-pairs/temporal',
  ])

  expect(result.history).toEqual({
    schema_version: '0.1',
    runs: [],
  })

  expect(result.temporalPairs).toEqual({
    schema_version: '0.1',
    pair_type: 'temporal',
    pairs: [],
  })

  expect(
    calls.some(
      (call) => call.includes(
        '/geographic',
      ),
    ),
  ).toBe(false)
})
