import {
  expect,
  it,
} from 'vitest'

import {
  compareGeographicAgentRuns,
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


it('compares explicitly selected geographic Agent Lab runs', async () => {
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
        comparison_type: 'geographic',
        baseline_session_id:
          '00000000-0000-0000-0000-000000000301',
        candidate_session_id:
          '00000000-0000-0000-0000-000000000302',
        baseline_observer_id:
          'observer-los-lagos',
        candidate_observer_id:
          'observer-aysen',
        baseline_region_code:
          'CL-Los-Lagos',
        candidate_region_code:
          'CL-Aysen',
        baseline_started_at_utc:
          '2026-08-26T18:00:00+00:00',
        candidate_started_at_utc:
          '2026-08-26T18:05:00+00:00',
        observation_skew_seconds: 300,
        max_observation_skew_seconds: 600,
        changes: {
          total_tasks: 11,
          regressions: 1,
          improvements: 2,
          unchanged: 8,
          pass_rate_delta: 0.09,
          median_latency_ms_delta: -1.25,
          retry_delta: -1,
          human_intervention_delta: 0,
          task_changes: [],
        },
      }),
    }
  }

  const result = await compareGeographicAgentRuns(
    fakeFetch,
    {
      baselineSessionId:
        '00000000-0000-0000-0000-000000000301',
      candidateSessionId:
        '00000000-0000-0000-0000-000000000302',
      maxObservationSkewSeconds: 600,
    },
  )

  expect(calls).toEqual([
    {
      input: '/v1/agent-comparisons/geographic',
      init: {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Accept: 'application/json',
        },
        body: JSON.stringify({
          baseline_session_id:
            '00000000-0000-0000-0000-000000000301',
          candidate_session_id:
            '00000000-0000-0000-0000-000000000302',
          max_observation_skew_seconds: 600,
        }),
      },
    },
  ])

  expect(result.comparison_type).toBe(
    'geographic',
  )

  expect(result.baseline_region_code).toBe(
    'CL-Los-Lagos',
  )
  expect(result.candidate_region_code).toBe(
    'CL-Aysen',
  )

  expect(result.observation_skew_seconds).toBe(
    300,
  )
  expect(
    result.max_observation_skew_seconds,
  ).toBe(600)
})


it('preserves an explicit zero geographic max skew', async () => {
  let requestBody: string | undefined

  const result = await compareGeographicAgentRuns(
    async (
      _input: string,
      init?: RequestInit,
    ) => {
      requestBody =
        typeof init?.body === 'string'
          ? init.body
          : undefined

      return {
        ok: true,
        status: 200,
        json: async () => ({
          schema_version: '0.1',
          comparison_type: 'geographic',
          baseline_session_id: 'baseline-id',
          candidate_session_id: 'candidate-id',
          baseline_observer_id: 'observer-one',
          candidate_observer_id: 'observer-two',
          baseline_region_code: 'CL-Los-Lagos',
          candidate_region_code: 'CL-Aysen',
          baseline_started_at_utc:
            '2026-08-26T18:00:00+00:00',
          candidate_started_at_utc:
            '2026-08-26T18:00:00+00:00',
          observation_skew_seconds: 0,
          max_observation_skew_seconds: 0,
          changes: {
            total_tasks: 11,
            regressions: 0,
            improvements: 0,
            unchanged: 11,
            pass_rate_delta: 0,
            median_latency_ms_delta: 0,
            retry_delta: 0,
            human_intervention_delta: 0,
            task_changes: [],
          },
        }),
      }
    },
    {
      baselineSessionId: 'baseline-id',
      candidateSessionId: 'candidate-id',
      maxObservationSkewSeconds: 0,
    },
  )

  expect(
    JSON.parse(requestBody ?? '{}'),
  ).toEqual({
    baseline_session_id: 'baseline-id',
    candidate_session_id: 'candidate-id',
    max_observation_skew_seconds: 0,
  })

  expect(
    result.max_observation_skew_seconds,
  ).toBe(0)
})


it('surfaces canonical geographic comparison rejection reasons', async () => {
  await expect(
    compareGeographicAgentRuns(
      async () => ({
        ok: false,
        status: 422,
        json: async () => ({
          error: 'comparison_rejected',
          message: (
            'Geographic comparison observation skew '
            + 'exceeds max_observation_skew.'
          ),
        }),
      }),
      {
        baselineSessionId: 'baseline-id',
        candidateSessionId: 'candidate-id',
        maxObservationSkewSeconds: 600,
      },
    ),
  ).rejects.toThrow(
    'Geographic comparison observation skew exceeds max_observation_skew.',
  )
})
