import { describe, expect, it } from 'vitest'

import {
  assignmentFromBridgeResponse,
  fetchBridgeAssignment,
} from './bridge'
import type {
  BridgeNextResponse,
} from './bridge'

describe('assignmentFromBridgeResponse', () => {
  it('maps a due bridge item to a Collector assignment', () => {
    const response: BridgeNextResponse = {
      schema_version: '0.1',
      status: 'due',
      now_utc: '2026-08-21T12:01:10Z',
      schedule_date: '2026-08-21',
      observer_id: 'observer-test',
      platform: 'chatgpt',
      benchmark_version: '0.1',
      completed_today: 0,
      item: {
        scheduled_at_utc:
          '2026-08-21T12:00:00Z',
        prompt_id: 'reasoning-001',
        category: 'reasoning',
        prompt: 'Test reasoning prompt',
        overdue_by_ms: 70000,
      },
    }

    const assignment =
      assignmentFromBridgeResponse(response)

    expect(assignment).not.toBeNull()
    expect(assignment?.status).toBe('due')
    expect(assignment?.category).toBe('reasoning')
    expect(assignment?.probe).toEqual({
      platform: 'chatgpt',
      pageHostname: 'chatgpt.com',
      benchmarkVersion: '0.1',
      promptId: 'reasoning-001',
      promptText: 'Test reasoning prompt',
      scheduledAtUtc:
        '2026-08-21T12:00:00Z',
      measurementMode:
        'consumer-ui-manual-v0.1',
      responseCaptureEnabled: false,
    })
  })
})

describe('assignmentFromBridgeResponse status handling', () => {
  it('maps an upcoming bridge item', () => {
    const response: BridgeNextResponse = {
      schema_version: '0.1',
      status: 'upcoming',
      now_utc: '2026-08-21T11:55:00Z',
      schedule_date: '2026-08-21',
      observer_id: 'observer-test',
      platform: 'claude',
      benchmark_version: '0.1',
      completed_today: 2,
      item: {
        scheduled_at_utc:
          '2026-08-21T12:00:00Z',
        prompt_id: 'writing-001',
        category: 'writing',
        prompt: 'Test writing prompt',
        starts_in_ms: 300000,
      },
    }

    const assignment =
      assignmentFromBridgeResponse(response)

    expect(assignment?.status).toBe('upcoming')
    expect(assignment?.probe.platform).toBe('claude')
    expect(assignment?.probe.pageHostname).toBe(
      'claude.ai',
    )
    expect(assignment?.probe.promptId).toBe(
      'writing-001',
    )
  })

  it('returns null when the bridge has no assignment', () => {
    const response: BridgeNextResponse = {
      schema_version: '0.1',
      status: 'none',
      now_utc: '2026-08-21T23:00:00Z',
      schedule_date: '2026-08-21',
      observer_id: 'observer-test',
      platform: 'gemini',
      benchmark_version: '0.1',
      completed_today: 6,
      item: null,
    }

    expect(
      assignmentFromBridgeResponse(response),
    ).toBeNull()
  })
})

describe('fetchBridgeAssignment', () => {
  it('loads the next assignment from the same-origin bridge', async () => {
    const fetchCalls: string[] = []

    const fakeFetch = async (
      input: string,
    ) => {
      fetchCalls.push(input)

      return {
        ok: true,
        status: 200,
        async json() {
          return {
            schema_version: '0.1',
            status: 'due',
            now_utc: '2026-08-21T12:01:10Z',
            schedule_date: '2026-08-21',
            observer_id: 'observer-test',
            platform: 'chatgpt',
            benchmark_version: '0.1',
            completed_today: 0,
            item: {
              scheduled_at_utc:
                '2026-08-21T12:00:00Z',
              prompt_id: 'reasoning-001',
              category: 'reasoning',
              prompt: 'Test reasoning prompt',
              overdue_by_ms: 70000,
            },
          }
        },
      }
    }

    const assignment =
      await fetchBridgeAssignment(fakeFetch)

    expect(fetchCalls).toEqual(['/v1/next'])
    expect(assignment?.status).toBe('due')
    expect(assignment?.probe.promptId).toBe(
      'reasoning-001',
    )
  })
})

describe('fetchBridgeAssignment runtime validation', () => {
  it('rejects an invalid bridge payload', async () => {
    const fakeFetch = async (_input: string) => ({
      ok: true,
      status: 200,
      async json(): Promise<unknown> {
        return {
          schema_version: '0.1',
          status: 'due',
          now_utc: '2026-08-21T12:01:10Z',
          schedule_date: '2026-08-21',
          observer_id: 'observer-test',
          platform: 'unknown-platform',
          benchmark_version: '0.1',
          completed_today: 0,
          item: {
            scheduled_at_utc:
              '2026-08-21T12:00:00Z',
            prompt_id: 'reasoning-001',
            category: 'reasoning',
            prompt: 'Test reasoning prompt',
            overdue_by_ms: 70000,
          },
        }
      },
    })

    await expect(
      fetchBridgeAssignment(fakeFetch),
    ).rejects.toThrow(
      'Invalid DLLO bridge payload.',
    )
  })
})
