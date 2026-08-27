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


it('renders an empty Agent Lab run history state', () => {
  const html = renderAgentTestPage({
    state: 'disconnected',
    baseUrl: 'http://127.0.0.1:8000',
    history: {
      schema_version: '0.1',
      runs: [],
    },
  })

  expect(html).toContain(
    'data-agent-test-history="empty"',
  )
  expect(html).toContain('Run History')
  expect(html).toContain(
    'No saved agent runs yet.',
  )
  expect(html).toContain(
    'Completed Agent Lab observations will appear here after a test.',
  )
})


it('renders saved Agent Lab runs without choosing comparison roles', () => {
  const html = renderAgentTestPage({
    state: 'disconnected',
    baseUrl: 'http://127.0.0.1:8000',
    history: {
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
          observer_id: 'observer-one',
          region_code: 'CL-Los-Lagos',
          observatory: {
            provenance_complete: true,
            temporal_eligible: true,
            geographic_eligible: true,
            reasons: [],
          },
          total_tasks: 11,
          passed_tasks: 10,
          failed_tasks: 1,
          pass_rate: 10 / 11,
          median_latency_ms: 4.25,
        },
        {
          session_id:
            '00000000-0000-0000-0000-000000000102',
          started_at_utc:
            '2026-08-26T19:00:00+00:00',
          target_id: 'example-agent',
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
          median_latency_ms: 3.5,
        },
      ],
    },
  })

  expect(html).toContain(
    'data-agent-test-history="ready"',
  )

  expect(html).toContain(
    '00000000-0000-0000-0000-000000000101',
  )
  expect(html).toContain(
    '00000000-0000-0000-0000-000000000102',
  )

  expect(html).toContain('example-agent')
  expect(html).toContain(
    'Observed from CL-Los-Lagos',
  )
  expect(html).toContain('10 / 11')
  expect(html).toContain('11 / 11')
  expect(html).toContain('90.9%')
  expect(html).toContain('100%')
  expect(html).toContain('4.25 ms')
  expect(html).toContain('3.5 ms')

  const earlier = html.indexOf(
    '00000000-0000-0000-0000-000000000101',
  )
  const later = html.indexOf(
    '00000000-0000-0000-0000-000000000102',
  )

  expect(earlier).toBeGreaterThan(-1)
  expect(later).toBeGreaterThan(earlier)

  expect(html).not.toContain(
    'data-observation-role="baseline"',
  )
  expect(html).not.toContain(
    'data-observation-role="candidate"',
  )
})


it('renders explicitly selected baseline and candidate runs', () => {
  const history = {
    schema_version: '0.1' as const,
    runs: [
      {
        session_id: 'baseline-session',
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
        passed_tasks: 10,
        failed_tasks: 1,
        pass_rate: 10 / 11,
        median_latency_ms: 4.2,
      },
      {
        session_id: 'candidate-session',
        started_at_utc:
          '2026-08-26T19:00:00+00:00',
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
        median_latency_ms: 3.1,
      },
    ],
  }

  const html = renderAgentTestPage({
    state: 'disconnected',
    baseUrl: 'http://127.0.0.1:8000',
    history,
    baselineSessionId: 'baseline-session',
    candidateSessionId: 'candidate-session',
  })

  expect(html).toContain(
    'data-observation-role="baseline"',
  )
  expect(html).toContain(
    'data-observation-role="candidate"',
  )

  expect(html).toContain('Baseline')
  expect(html).toContain('Candidate')

  expect(html).toContain(
    'id="compare-agent-runs"',
  )
  expect(html).toContain(
    'Compare selected runs',
  )
})


it('renders observed changes for an explicit temporal comparison', () => {
  const html = renderAgentTestPage({
    state: 'disconnected',
    baseUrl: 'http://127.0.0.1:8000',
    comparison: {
      schema_version: '0.1',
      comparison_type: 'temporal',
      baseline_session_id: 'baseline-session',
      candidate_session_id: 'candidate-session',
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
            task_id: 'task-improved',
            baseline_passed: false,
            candidate_passed: true,
            transition: 'fail-to-pass',
          },
          {
            task_id: 'task-regressed',
            baseline_passed: true,
            candidate_passed: false,
            transition: 'pass-to-fail',
          },
        ],
      },
    },
  })

  expect(html).toContain(
    'data-agent-comparison="temporal"',
  )
  expect(html).toContain('Observed Changes')
  expect(html).toContain('Temporal comparison')

  expect(html).toContain('baseline-session')
  expect(html).toContain('candidate-session')

  expect(html).toContain(
    'Observed from CL-Los-Lagos',
  )

  expect(html).toContain('Regressions')
  expect(html).toContain('Improvements')
  expect(html).toContain('Unchanged')

  expect(html).toContain('+9')
  expect(html).toContain('-1.25 ms')
  expect(html).toContain('task-improved')
  expect(html).toContain('task-regressed')
  expect(html).toContain('Fail → Pass')
  expect(html).toContain('Pass → Fail')

  expect(html).not.toContain(
    'better than baseline',
  )
  expect(html).not.toContain(
    'worse than baseline',
  )
})


it('preserves unavailable comparison deltas as n/a', () => {
  const html = renderAgentTestPage({
    state: 'disconnected',
    baseUrl: 'http://127.0.0.1:8000',
    comparison: {
      schema_version: '0.1',
      comparison_type: 'temporal',
      baseline_session_id: 'baseline-session',
      candidate_session_id: 'candidate-session',
      observer_id: 'observer-test',
      region_code: 'CL-Los-Lagos',
      baseline_started_at_utc:
        '2026-08-26T18:00:00+00:00',
      candidate_started_at_utc:
        '2026-08-26T19:00:00+00:00',
      changes: {
        total_tasks: 0,
        regressions: 0,
        improvements: 0,
        unchanged: 0,
        pass_rate_delta: null,
        median_latency_ms_delta: null,
        retry_delta: 0,
        human_intervention_delta: 0,
        task_changes: [],
      },
    },
  })

  expect(html).toContain('Pass rate Δ')
  expect(html).toContain('Median latency Δ')

  expect(
    html.match(/<strong>n\/a<\/strong>/g),
  ).toHaveLength(2)

  expect(html).not.toContain('0 pp')
})


it('renders a rejected temporal comparison without hiding the reason', () => {
  const html = renderAgentTestPage({
    state: 'disconnected',
    baseUrl: 'http://127.0.0.1:8000',
    comparisonError:
      'Temporal comparison requires the candidate observation to occur after the baseline.',
  })

  expect(html).toContain(
    'data-agent-comparison="rejected"',
  )
  expect(html).toContain(
    'Comparison rejected',
  )
  expect(html).toContain(
    'Temporal comparison requires the candidate observation to occur after the baseline.',
  )

  expect(html).not.toContain(
    'Observed Changes',
  )
})
