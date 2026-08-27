import {
  expect,
  it,
} from 'vitest'

import {
  discoverObservatoryGeographicPairs,
  loadObservatoryDashboard,
  parseGeographicMaxSkewInput,
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


it('keeps zero geographic skew distinct from empty input', () => {
  expect(
    parseGeographicMaxSkewInput('0'),
  ).toBe(0)

  expect(
    parseGeographicMaxSkewInput(''),
  ).toBeNull()

  expect(
    parseGeographicMaxSkewInput('   '),
  ).toBeNull()
})


it('rejects invalid geographic skew input locally', () => {
  expect(
    parseGeographicMaxSkewInput('banana'),
  ).toBeNull()

  expect(
    parseGeographicMaxSkewInput('-1'),
  ).toBeNull()
})


it('discovers geographic pairs only from explicit valid skew', async () => {
  const calls: string[] = []

  const fakeFetch = async (
    input: string,
  ) => {
    calls.push(input)

    return {
      ok: true,
      status: 200,
      json: async () => ({
        schema_version: '0.1',
        pair_type: 'geographic',
        max_observation_skew_seconds: 0,
        pairs: [],
      }),
    }
  }

  const result =
    await discoverObservatoryGeographicPairs(
      fakeFetch,
      '0',
    )

  expect(calls).toEqual([
    (
      '/v1/agent-observation-pairs/geographic'
      + '?max_observation_skew_seconds=0'
    ),
  ])

  expect(
    result.max_observation_skew_seconds,
  ).toBe(0)
})


it('does not request geographic pairs from invalid skew input', async () => {
  const calls: string[] = []

  const fakeFetch = async (
    input: string,
  ) => {
    calls.push(input)

    throw new Error(
      `Unexpected request: ${input}`,
    )
  }

  await expect(
    discoverObservatoryGeographicPairs(
      fakeFetch,
      '',
    ),
  ).rejects.toThrow(
    'Maximum observation skew is required.',
  )

  await expect(
    discoverObservatoryGeographicPairs(
      fakeFetch,
      '-1',
    ),
  ).rejects.toThrow(
    'Maximum observation skew is required.',
  )

  expect(calls).toEqual([])
})
