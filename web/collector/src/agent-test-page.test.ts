import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  renderAgentTestPage,
} from './agent-test-page'

describe('renderAgentTestPage', () => {
  it('renders the disconnected Test Your Agent state', () => {
    const html = renderAgentTestPage({
      state: 'disconnected',
      baseUrl: 'http://127.0.0.1:8000',
    })

    expect(html).toContain('Test Your Agent')
    expect(html).toContain('Agent Protocol Core 1.0')
    expect(html).toContain('Local SUT Protocol')
    expect(html).toContain('http://127.0.0.1:8000')
    expect(html).toContain('no-agent.webp')
    expect(html).toContain('Run Agent Test')
  })

  it.each([
    ['disconnected', 'no-agent.webp'],
    ['running', 'benchmark-lab.webp'],
    ['success', 'experiment-complete.webp'],
    ['failed', 'experiment-failed.webp'],
  ] as const)(
    'uses the correct visual for %s state',
    (state, expectedVisual) => {
      const html = renderAgentTestPage({
        state,
        baseUrl: 'http://127.0.0.1:8000',
      })

      expect(html).toContain(expectedVisual)
    },
  )

  it('explains observer-owned evaluation', () => {
    const html = renderAgentTestPage({
      state: 'disconnected',
      baseUrl: 'http://127.0.0.1:8000',
    })

    expect(html).toContain('observer-owned evidence')
    expect(html).toContain('technical report')
  })
})


it('renders the completed Agent Lab technical summary', () => {
  const html = renderAgentTestPage({
    state: 'success',
    baseUrl: 'http://127.0.0.1:8000',
    result: {
      schema_version: '0.1',
      status: 'completed',
      started_at_utc:
        '2026-08-26T22:12:00+00:00',
      session_id:
        '11111111-1111-4111-8111-111111111111',
      target_id:
        'dllo-reference-protocol-agent',
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
      median_latency_ms: 6.5,
      findings: [
        'All benchmark tasks passed.',
      ],
      recommendations: [
        'Repeat observations over time.',
      ],
    },
  })

  expect(html).toContain(
    'dllo-reference-protocol-agent',
  )
  expect(html).toContain('11 / 11')
  expect(html).toContain('100%')
  expect(html).toContain('6.5 ms')
  expect(html).toContain('observer-test')
  expect(html).toContain(
    'Observed from CL-Los-Lagos',
  )
  expect(html).toContain(
    'Temporal eligible',
  )
  expect(html).toContain(
    'Geographic eligible',
  )
  expect(html).toContain(
    'All benchmark tasks passed.',
  )
  expect(html).toContain(
    'Repeat observations over time.',
  )
})


it('renders the DLLO running indicator while the agent test runs', () => {
  const html = renderAgentTestPage({
    state: 'running',
    baseUrl: 'http://127.0.0.1:8000',
  })

  expect(html).toContain(
    'data-agent-test-loader="running"',
  )
  expect(html).toContain(
    'Running Agent Protocol',
  )
  expect(html).toContain(
    'Collecting observer-owned evidence',
  )
})


it('renders an actionable failure message for a failed agent test', () => {
  const html = renderAgentTestPage({
    state: 'failed',
    baseUrl: 'http://127.0.0.1:8000',
    error: 'Unable to load agent manifest.',
  })

  expect(html).toContain(
    'data-agent-test-error="failed"',
  )
  expect(html).toContain(
    'Unable to load agent manifest.',
  )
  expect(html).toContain(
    'http://127.0.0.1:8000',
  )
  expect(html).toContain(
    'Retry Agent Test',
  )
})
