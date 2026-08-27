import {
  expect,
  it,
} from 'vitest'

import {
  renderObservatoryPage,
} from './observatory-page'

it('renders Observatory counts from observed runs and temporal pairs', () => {
  const html = renderObservatoryPage({
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
        {
          session_id: 'run-2',
          started_at_utc:
            '2026-08-26T19:00:00+00:00',
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
          passed_tasks: 10,
          failed_tasks: 1,
          pass_rate: 10 / 11,
          median_latency_ms: 4.1,
        },
        {
          session_id: 'run-3',
          started_at_utc:
            '2026-08-26T20:00:00+00:00',
          target_id: 'agent-b',
          suite_id: 'agent-protocol-core',
          suite_version: '1.0',
          observer_id: 'observer-two',
          region_code: 'CL-Aysen',
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
          median_latency_ms: 2.9,
        },
      ],
    },
    temporalPairs: {
      schema_version: '0.1',
      pair_type: 'temporal',
      pairs: [
        {
          baseline_session_id: 'run-1',
          candidate_session_id: 'run-2',
          baseline_started_at_utc:
            '2026-08-26T18:00:00+00:00',
          candidate_started_at_utc:
            '2026-08-26T19:00:00+00:00',
          baseline_observer_id: 'observer-one',
          candidate_observer_id: 'observer-one',
          baseline_region_code: 'CL-Los-Lagos',
          candidate_region_code: 'CL-Los-Lagos',
          comparable: true,
          reasons: [],
        },
        {
          baseline_session_id: 'run-1',
          candidate_session_id: 'run-3',
          baseline_started_at_utc:
            '2026-08-26T18:00:00+00:00',
          candidate_started_at_utc:
            '2026-08-26T20:00:00+00:00',
          baseline_observer_id: 'observer-one',
          candidate_observer_id: 'observer-two',
          baseline_region_code: 'CL-Los-Lagos',
          candidate_region_code: 'CL-Aysen',
          comparable: false,
          reasons: [
            'Temporal comparison requires the same region_code.',
          ],
        },
      ],
    },
    geographicPairs: null,
    geographicMaxSkewInput: '',
    error: null,
  })

  expect(html).toContain(
    'Distributed LLM Observatory',
  )

  expect(html).toContain(
    'data-observatory-hero-visual',
  )

  expect(html).toContain(
    'data-observatory-globe-points',
  )

  expect(html).toMatch(
    /<strong>3<\/strong>\s*<span>observations<\/span>/,
  )

  expect(html).toMatch(
    /<strong>2<\/strong>\s*<span>targets<\/span>/,
  )

  expect(html).toMatch(
    /<strong>2<\/strong>\s*<span>observed regions<\/span>/,
  )

  expect(html).toContain('Temporal')
  expect(html).toMatch(
    /<strong>2<\/strong> pairs/,
  )

  expect(html).toMatch(
    /<strong>1<\/strong> comparable/,
  )

  expect(html).toMatch(
    /<strong>1<\/strong> rejected/,
  )

  expect(html).toContain(
    'Maximum observation skew required',
  )

  expect(html).toContain(
    'Recent observations',
  )

  expect(html).toContain(
    'data-observatory-icon="observations"',
  )

  expect(html).toContain(
    'data-observatory-icon="targets"',
  )

  expect(html).toContain(
    'data-observatory-icon="regions"',
  )

  expect(html).toContain(
    'data-observatory-icon="temporal"',
  )

  expect(html).toContain(
    'data-observatory-icon="geographic"',
  )

  expect(html).toContain(
    'data-observatory-icon="history"',
  )

  expect(html).toContain(
    'agent-a',
  )

  expect(html).toContain(
    'Observed from CL-Los-Lagos',
  )

  expect(html).toContain(
    'Observed from CL-Aysen',
  )

  expect(html).toContain(
    '26 Aug 2026',
  )

  expect(html).toContain(
    '20:00:00 UTC',
  )

  expect(html).toContain(
    '2.90 ms',
  )

  expect(html).not.toContain(
    '2026-08-26T20:00:00+00:00</dd>',
  )

  expect(html).not.toContain(
    'Serving from',
  )

  expect(
    html.indexOf('2026-08-26T20:00:00+00:00'),
  ).toBeLessThan(
    html.indexOf('2026-08-26T19:00:00+00:00'),
  )

  expect(
    html.indexOf('2026-08-26T19:00:00+00:00'),
  ).toBeLessThan(
    html.indexOf('2026-08-26T18:00:00+00:00'),
  )

  expect(html).not.toContain(
    'globally better',
  )
})
