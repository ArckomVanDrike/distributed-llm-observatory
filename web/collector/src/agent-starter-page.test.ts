import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  renderAgentStarterPage,
} from './agent-starter-page'

describe('renderAgentStarterPage', () => {
  it('presents Agent Starter as an available workflow', () => {
    const html = renderAgentStarterPage()

    expect(html).toContain('Agent Starter')
    expect(html).toContain('Core v1 complete')
    expect(html).toContain(
      'Build an agent for',
    )

    expect(html).not.toContain(
      'Public interface in development',
    )
  })

  it('presents all supported Agent Starter goals', () => {
    const html = renderAgentStarterPage()

    expect(html).toContain('Coding')
    expect(html).toContain('Knowledge / RAG')
    expect(html).toContain('Automation')
    expect(html).toContain('Voice')
    expect(html).toContain('Personal Assistant')

    expect(html).toContain(
      'data-agent-starter-goal="coding"',
    )
    expect(html).toContain(
      'data-agent-starter-goal="knowledge-rag"',
    )
    expect(html).toContain(
      'data-agent-starter-goal="automation"',
    )
    expect(html).toContain(
      'data-agent-starter-goal="voice"',
    )
    expect(html).toContain(
      'data-agent-starter-goal="personal"',
    )
  })

  it('explains the evidence-backed decision workflow', () => {
    const html = renderAgentStarterPage()

    expect(html).toContain('Goal')
    expect(html).toContain('Constraints')
    expect(html).toContain('Environment')
    expect(html).toContain('Recommendation')

    expect(html).toContain('Explicit evidence')
    expect(html).toContain('Hard constraints')
    expect(html).toContain(
      'Unknown stays unknown',
    )
  })

  it('exposes the goal selection as step one', () => {
    const html = renderAgentStarterPage()

    expect(html).toContain('Step 1 · Goal')
    expect(html).toContain(
      'What do you want to build?',
    )
  })
})
