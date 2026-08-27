import {
  expect,
  it,
} from 'vitest'

import {
  selectAgentComparisonRole,
} from './agent-test-selection'

import type {
  AgentComparisonSelection,
} from './agent-test-selection'

it('keeps Agent Lab comparison roles explicit and distinct', () => {
  let selection: AgentComparisonSelection = {
    baselineSessionId: null,
    candidateSessionId: null,
  }

  selection = selectAgentComparisonRole(
    selection,
    'baseline',
    'run-a',
  )

  expect(selection).toEqual({
    baselineSessionId: 'run-a',
    candidateSessionId: null,
  })

  selection = selectAgentComparisonRole(
    selection,
    'candidate',
    'run-b',
  )

  expect(selection).toEqual({
    baselineSessionId: 'run-a',
    candidateSessionId: 'run-b',
  })

  selection = selectAgentComparisonRole(
    selection,
    'candidate',
    'run-a',
  )

  expect(selection).toEqual({
    baselineSessionId: null,
    candidateSessionId: 'run-a',
  })

  selection = selectAgentComparisonRole(
    selection,
    'baseline',
    'run-a',
  )

  expect(selection).toEqual({
    baselineSessionId: 'run-a',
    candidateSessionId: null,
  })
})
