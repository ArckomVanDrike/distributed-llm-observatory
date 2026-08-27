import {
  expect,
  it,
} from 'vitest'

import {
  fetchAgentTestHistory,
} from './agent-test-history'

it('loads Agent Lab run history without selecting a run', async () => {
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
        runs: [
          {
            session_id:
              '00000000-0000-0000-0000-000000000101',
            started_at_utc:
              '2026-08-26T18:00:00+00:00',
            target_id: 'example-agent',
            suite_id: 'agent-protocol-core',
            suite_version: '1.0',
            observer_id: 'observer-test',
            region_code: 'CL-Los-Lagos',
            observatory: {
              provenance_complete: true,
              temporal_eligible: true,
              geographic_eligible: true,
              reasons: [],
            },
            total_tasks: 11,
            passed_tasks: 11,
            failed_tasks: 0,
            pass_rate: 1,
            median_latency_ms: 3.2,
          },
        ],
      }),
    }
  }

  const history = await fetchAgentTestHistory(
    fakeFetch,
  )

  expect(calls).toEqual([
    {
      input: '/v1/agent-tests',
      init: {
        method: 'GET',
        headers: {
          Accept: 'application/json',
        },
      },
    },
  ])

  expect(history.schema_version).toBe('0.1')
  expect(history.runs).toHaveLength(1)

  expect(history.runs[0].session_id).toBe(
    '00000000-0000-0000-0000-000000000101',
  )
  expect(history.runs[0].target_id).toBe(
    'example-agent',
  )
  expect(history.runs[0].pass_rate).toBe(1)

  expect(
    Object.prototype.hasOwnProperty.call(
      history,
      'latest',
    ),
  ).toBe(false)

  expect(
    Object.prototype.hasOwnProperty.call(
      history,
      'baseline',
    ),
  ).toBe(false)

  expect(
    Object.prototype.hasOwnProperty.call(
      history,
      'candidate',
    ),
  ).toBe(false)
})
