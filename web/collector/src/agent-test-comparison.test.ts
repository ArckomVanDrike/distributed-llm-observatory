import {
  expect,
  it,
} from 'vitest'

import {
  compareTemporalAgentRuns,
} from './agent-test-comparison'

it('compares explicitly selected temporal Agent Lab runs', async () => {
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
        comparison_type: 'temporal',
        baseline_session_id:
          '00000000-0000-0000-0000-000000000201',
        candidate_session_id:
          '00000000-0000-0000-0000-000000000202',
        observer_id: 'observer-test',
        region_code: 'CL-Los-Lagos',
        baseline_started_at_utc:
          '2026-08-26T18:00:00+00:00',
        candidate_started_at_utc:
          '2026-08-26T19:00:00+00:00',
        changes: {
          total_tasks: 11,
          regressions: 1,
          improvements: 2,
          unchanged: 8,
          pass_rate_delta: 0.09,
          median_latency_ms_delta: -1.25,
          retry_delta: -1,
          human_intervention_delta: 0,
          task_changes: [
            {
              task_id: 'task-one',
              baseline_passed: false,
              candidate_passed: true,
              transition: 'fail-to-pass',
            },
          ],
        },
      }),
    }
  }

  const result = await compareTemporalAgentRuns(
    fakeFetch,
    {
      baselineSessionId:
        '00000000-0000-0000-0000-000000000201',
      candidateSessionId:
        '00000000-0000-0000-0000-000000000202',
    },
  )

  expect(calls).toEqual([
    {
      input: '/v1/agent-comparisons/temporal',
      init: {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          baseline_session_id:
            '00000000-0000-0000-0000-000000000201',
          candidate_session_id:
            '00000000-0000-0000-0000-000000000202',
        }),
      },
    },
  ])

  expect(result.comparison_type).toBe(
    'temporal',
  )
  expect(result.baseline_session_id).toBe(
    '00000000-0000-0000-0000-000000000201',
  )
  expect(result.candidate_session_id).toBe(
    '00000000-0000-0000-0000-000000000202',
  )
  expect(result.changes.improvements).toBe(2)
  expect(result.changes.regressions).toBe(1)
  expect(
    result.changes.median_latency_ms_delta,
  ).toBe(-1.25)
})


it('surfaces canonical temporal comparison rejection reasons', async () => {
  await expect(
    compareTemporalAgentRuns(
      async () => ({
        ok: false,
        status: 422,
        json: async () => ({
          error: 'comparison_rejected',
          message: (
            'Temporal comparison requires the candidate '
            + 'observation to occur after the baseline.'
          ),
        }),
      }),
      {
        baselineSessionId: 'baseline-id',
        candidateSessionId: 'candidate-id',
      },
    ),
  ).rejects.toThrow(
    'Temporal comparison requires the candidate observation to occur after the baseline.',
  )
})
