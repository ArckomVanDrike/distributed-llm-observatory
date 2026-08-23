import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  buildPublicAssignment,
} from './public-assignment'

describe('buildPublicAssignment', () => {
  it('builds an unscheduled public ChatGPT probe', () => {
    const probe = buildPublicAssignment(
      'coding-001',
      'chatgpt',
    )

    expect(probe).toEqual({
      platform: 'chatgpt',
      pageHostname: 'chatgpt.com',
      benchmarkVersion: '0.1',
      promptId: 'coding-001',
      promptText:
        'Write a Python function named deduplicate_preserve_order(values) that returns a new list with duplicate elements removed while preserving the order of first occurrence. Do not modify the input list. Include the function implementation and a brief explanation of its time complexity.',
      scheduledAtUtc: null,
      measurementMode: 'consumer-ui-manual-v0.1',
      responseCaptureEnabled: false,
    })
  })

  it('returns null for an unknown prompt id', () => {
    expect(
      buildPublicAssignment(
        'unknown-001',
        'chatgpt',
      ),
    ).toBeNull()
  })

  it('maps supported provider hostnames', () => {
    expect(
      buildPublicAssignment(
        'reasoning-001',
        'claude',
      )?.pageHostname,
    ).toBe('claude.ai')

    expect(
      buildPublicAssignment(
        'reasoning-001',
        'gemini',
      )?.pageHostname,
    ).toBe('gemini.google.com')
  })
})
