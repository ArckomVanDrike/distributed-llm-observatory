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
      'data-agent-starter-goal="knowledge_rag"',
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

  it('renders an adaptive question', () => {
    const html = renderAgentStarterPage({
      state: 'question',
      goal: 'coding',
      evidence: [],
      error: null,
      questionSet: {
        schema_version: '0.1',
        goal: 'coding',
        questions: [
          {
            schema_version: '0.1',
            key: 'offline_required',
            goal: 'coding',
            prompt:
              'Must the agent be able to operate offline?',
            kind: 'boolean',
            reason:
              'Offline operation can exclude architectures requiring network connectivity.',
          },
        ],
      },
    })

    expect(html).toContain(
      'Must the agent be able to operate offline?',
    )
    expect(html).toContain(
      'Why DLLO asks this',
    )
    expect(html).toContain(
      'data-agent-starter-answer="true"',
    )
    expect(html).toContain(
      'data-agent-starter-answer="false"',
    )
    expect(html).toContain(
      'data-agent-starter-answer="unknown"',
    )
    expect(html).toContain(
      'Unknown answers are not treated as false.',
    )
  })

  it('renders questionnaire completion separately from final recommendation', () => {
    const html = renderAgentStarterPage({
      state: 'complete',
      goal: 'coding',
      evidence: [
        {
          key: 'offline_required',
          source: 'declared',
          value: true,
        },
      ],
      questionSet: {
        schema_version: '0.1',
        goal: 'coding',
        questions: [],
      },
      error: null,
    })

    expect(html).toContain(
      'The adaptive questionnaire is complete.',
    )
    expect(html).toContain(
      'next wizard stage',
    )
    expect(html).not.toContain(
      'Recommended architecture',
    )
  })
})
