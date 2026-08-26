import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  executeAgentTest,
} from './agent-test-flow'

describe('executeAgentTest', () => {
  it('transitions from running to success', async () => {
    const states: string[] = []

    const fakeRunAgentTest = async (
      _fetchImpl: typeof fetch,
      baseUrl: string,
    ) => {
      expect(baseUrl).toBe(
        'http://127.0.0.1:8000',
      )

      return {
        schema_version: '0.1' as const,
        status: 'completed' as const,
        started_at_utc:
          '2026-08-26T20:00:00+00:00',
        session_id:
          '11111111-1111-4111-8111-111111111111',
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
        median_latency_ms: 120,
        findings: [],
        recommendations: [],
      }
    }

    const result = await executeAgentTest({
      baseUrl: 'http://127.0.0.1:8000',
      fetchImpl: fetch,
      runAgentTestImpl: fakeRunAgentTest,
      onStateChange(state) {
        states.push(state)
      },
    })

    expect(states).toEqual([
      'running',
      'success',
    ])

    expect(result.target_id).toBe(
      'example-agent',
    )
  })

  it('transitions from running to failed when the bridge fails', async () => {
    const states: string[] = []

    const fakeRunAgentTest = async () => {
      throw new Error(
        'Agent Lab bridge request failed.',
      )
    }

    await expect(
      executeAgentTest({
        baseUrl: 'http://127.0.0.1:8000',
        fetchImpl: fetch,
        runAgentTestImpl: fakeRunAgentTest,
        onStateChange(state) {
          states.push(state)
        },
      }),
    ).rejects.toThrow(
      'Agent Lab bridge request failed.',
    )

    expect(states).toEqual([
      'running',
      'failed',
    ])
  })
})
