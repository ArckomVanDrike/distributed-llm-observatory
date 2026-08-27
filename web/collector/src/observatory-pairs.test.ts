import {
  expect,
  it,
} from 'vitest'

import {
  fetchGeographicObservationPairs,
  fetchTemporalObservationPairs,
} from './observatory-pairs'

it('loads temporal observation pairs without selecting a comparison', async () => {
  const calls: Array<{
    input: string
    init?: RequestInit
  }> = []

  const fakeFetch = async (
    input: string,
    init?: RequestInit,
  ) => {
    calls.push({
      input,
      init,
    })

    return {
      ok: true,
      status: 200,
      json: async () => ({
        schema_version: '0.1',
        pair_type: 'temporal',
        pairs: [
          {
            baseline_session_id:
              '00000000-0000-0000-0000-000000000301',
            candidate_session_id:
              '00000000-0000-0000-0000-000000000302',
            baseline_started_at_utc:
              '2026-08-26T18:00:00+00:00',
            candidate_started_at_utc:
              '2026-08-26T19:00:00+00:00',
            baseline_observer_id:
              'observer-test',
            candidate_observer_id:
              'observer-test',
            baseline_region_code:
              'CL-Los-Lagos',
            candidate_region_code:
              'CL-Los-Lagos',
            comparable: true,
            reasons: [],
          },
        ],
      }),
    }
  }

  const result = await fetchTemporalObservationPairs(
    fakeFetch,
  )

  expect(calls).toEqual([
    {
      input:
        '/v1/agent-observation-pairs/temporal',
      init: {
        method: 'GET',
        headers: {
          Accept: 'application/json',
        },
      },
    },
  ])

  expect(result.schema_version).toBe('0.1')
  expect(result.pair_type).toBe('temporal')
  expect(result.pairs).toHaveLength(1)

  expect(result.pairs[0].comparable).toBe(true)
  expect(result.pairs[0].reasons).toEqual([])

  expect(
    Object.prototype.hasOwnProperty.call(
      result,
      'latest',
    ),
  ).toBe(false)

  expect(
    Object.prototype.hasOwnProperty.call(
      result,
      'baseline',
    ),
  ).toBe(false)

  expect(
    Object.prototype.hasOwnProperty.call(
      result,
      'candidate',
    ),
  ).toBe(false)
})


it('loads geographic observation pairs with explicit max skew', async () => {
  const calls: Array<{
    input: string
    init?: RequestInit
  }> = []

  const fakeFetch = async (
    input: string,
    init?: RequestInit,
  ) => {
    calls.push({
      input,
      init,
    })

    return {
      ok: true,
      status: 200,
      json: async () => ({
        schema_version: '0.1',
        pair_type: 'geographic',
        max_observation_skew_seconds: 600,
        pairs: [
          {
            baseline_session_id:
              '00000000-0000-0000-0000-000000000401',
            candidate_session_id:
              '00000000-0000-0000-0000-000000000402',
            baseline_started_at_utc:
              '2026-08-26T18:00:00+00:00',
            candidate_started_at_utc:
              '2026-08-26T18:05:00+00:00',
            baseline_observer_id:
              'observer-los-lagos',
            candidate_observer_id:
              'observer-aysen',
            baseline_region_code:
              'CL-Los-Lagos',
            candidate_region_code:
              'CL-Aysen',
            comparable: true,
            reasons: [],
          },
        ],
      }),
    }
  }

  const result = await fetchGeographicObservationPairs(
    fakeFetch,
    {
      maxObservationSkewSeconds: 600,
    },
  )

  expect(calls).toEqual([
    {
      input: (
        '/v1/agent-observation-pairs/geographic'
        + '?max_observation_skew_seconds=600'
      ),
      init: {
        method: 'GET',
        headers: {
          Accept: 'application/json',
        },
      },
    },
  ])

  expect(result.schema_version).toBe('0.1')
  expect(result.pair_type).toBe('geographic')
  expect(
    result.max_observation_skew_seconds,
  ).toBe(600)

  expect(result.pairs).toHaveLength(1)
  expect(result.pairs[0].comparable).toBe(true)
})
