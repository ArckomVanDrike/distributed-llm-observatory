import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  runAgentTest,
} from './agent-test-bridge'

describe('runAgentTest', () => {
  it('posts the local agent endpoint to the Agent Lab bridge', async () => {
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
        status: 201,
        async json() {
          return {
            schema_version: '0.1',
            status: 'completed',
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
            passed_tasks: 9,
            failed_tasks: 2,
            pass_rate: 9 / 11,
            median_latency_ms: 125.5,
            findings: [
              'Two benchmark tasks did not pass.',
            ],
            recommendations: [
              'Review the failed task evidence.',
            ],
          }
        },
      }
    }

    const result = await runAgentTest(
      fakeFetch,
      'http://127.0.0.1:8000',
    )

    expect(calls).toHaveLength(1)

    expect(calls[0].input).toBe(
      '/v1/agent-tests',
    )

    expect(calls[0].init?.method).toBe('POST')

    expect(calls[0].init?.headers).toEqual({
      'Content-Type': 'application/json',
      Accept: 'application/json',
    })

    expect(
      JSON.parse(
        String(calls[0].init?.body),
      ),
    ).toEqual({
      base_url: 'http://127.0.0.1:8000',
    })

    expect(result.status).toBe('completed')
    expect(result.target_id).toBe('example-agent')
    expect(result.total_tasks).toBe(11)
    expect(result.passed_tasks).toBe(9)

    expect(
      result.observatory.temporal_eligible,
    ).toBe(true)
  })
})


it('rejects Agent Lab bridge HTTP errors', async () => {
  const fakeFetch = async () => ({
    ok: false,
    status: 500,
    async json() {
      return {
        error: 'agent_test_failed',
      }
    },
  })

  await expect(
    runAgentTest(
      fakeFetch,
      'http://127.0.0.1:8000',
    ),
  ).rejects.toThrow(
    'Agent Lab bridge request failed with HTTP 500.',
  )
})


it('rejects malformed Agent Lab bridge payloads', async () => {
  const fakeFetch = async () => ({
    ok: true,
    status: 201,
    async json() {
      return {
        schema_version: '0.1',
        status: 'completed',
        target_id: 'example-agent',
      }
    },
  })

  await expect(
    runAgentTest(
      fakeFetch,
      'http://127.0.0.1:8000',
    ),
  ).rejects.toThrow(
    'Invalid Agent Lab bridge payload.',
  )
})


it('surfaces controlled Agent Lab bridge error messages', async () => {
  await expect(
    runAgentTest(
      async () => ({
        ok: false,
        status: 500,
        json: async () => ({
          error: 'agent_test_failed',
          message: 'Unable to load agent manifest.',
        }),
      }),
      'http://127.0.0.1:8000',
    ),
  ).rejects.toThrow(
    'Unable to load agent manifest.',
  )
})
