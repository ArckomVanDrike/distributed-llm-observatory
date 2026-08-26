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
