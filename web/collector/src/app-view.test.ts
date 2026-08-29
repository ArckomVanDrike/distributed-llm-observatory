import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  renderAppView,
} from './app-view'

describe('renderAppView', () => {
  it('renders the Consumer Probe route', () => {
    const html = renderAppView(
      'consumer-probe',
      '<div id="probe">probe</div>',
    )

    expect(html).toContain('Collector')
    expect(html).toContain(
      '<div id="probe">probe</div>',
    )
  })

  it('renders the Agent Lab route inside the DLLO shell', () => {
    const html = renderAppView(
      'agent-lab',
      '',
    )

    expect(html).toContain('Agent Lab')
    expect(html).toContain('Test Your Agent')
    expect(html).toContain(
      'data-route="agent-lab" aria-current="page"',
    )
  })

  it('renders Test Your Agent inside the DLLO shell', () => {
    const html = renderAppView(
      'agent-lab-test',
      '',
    )

    expect(html).toContain('Test Your Agent')
    expect(html).toContain(
      'http://127.0.0.1:8000',
    )
    expect(html).toContain(
      'data-route="agent-lab-test" aria-current="page"',
    )
  })

  it('renders the Observatory landing route', () => {
    const html = renderAppView(
      'observatory',
      '',
    )

    expect(html).toContain('Observatory')
    expect(html).toContain(
      'Distributed LLM Observatory',
    )
  })

  it('renders Agent Starter core status and supported goals', () => {
    const html = renderAppView(
      'agent-lab-starter',
      '',
    )

    expect(html).toContain('Agent Starter')
    expect(html).toContain('Core v1 complete')
    expect(html).toContain(
      'Public interface in development',
    )

    expect(html).toContain('Coding')
    expect(html).toContain('Knowledge / RAG')
    expect(html).toContain('Automation')
    expect(html).toContain('Voice')
    expect(html).toContain('Personal Assistant')
  })
})


it('renders Test Your Agent from external state', () => {
  const html = renderAppView(
    'agent-lab-test',
    '',
    {
      agentTest: {
        state: 'running',
        baseUrl: 'http://127.0.0.1:9000',
      },
    },
  )

  expect(html).toContain('Test running')
  expect(html).toContain(
    'data-agent-test-state="running"',
  )
  expect(html).toContain(
    'http://127.0.0.1:9000',
  )
  expect(html).toContain('Running test...')
})


it('renders Observatory from external dashboard state', () => {
  const html = renderAppView(
    'observatory',
    '',
    {
      observatory: {
        state: 'ready',
        history: {
          schema_version: '0.1',
          runs: [
            {
              session_id: 'run-1',
              started_at_utc:
                '2026-08-26T18:00:00+00:00',
              target_id: 'agent-a',
              suite_id: 'agent-protocol-core',
              suite_version: '1.0',
              observer_id: 'observer-one',
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
        },
        temporalPairs: {
          schema_version: '0.1',
          pair_type: 'temporal',
          pairs: [],
        },
        geographicPairs: null,
        geographicMaxSkewInput: '',
        error: null,
      },
    },
  )

  expect(html).toMatch(
    /<strong>1<\/strong>\s*<span>observations<\/span>/,
  )

  expect(html).toContain(
    'Maximum observation skew required',
  )
})
