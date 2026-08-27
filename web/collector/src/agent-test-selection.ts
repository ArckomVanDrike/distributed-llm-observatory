export type AgentComparisonRole =
  | 'baseline'
  | 'candidate'

export type AgentComparisonSelection = {
  baselineSessionId: string | null
  candidateSessionId: string | null
}

export function selectAgentComparisonRole(
  selection: AgentComparisonSelection,
  role: AgentComparisonRole,
  sessionId: string,
): AgentComparisonSelection {
  if (role === 'baseline') {
    return {
      baselineSessionId: sessionId,
      candidateSessionId:
        selection.candidateSessionId === sessionId
          ? null
          : selection.candidateSessionId,
    }
  }

  return {
    baselineSessionId:
      selection.baselineSessionId === sessionId
        ? null
        : selection.baselineSessionId,
    candidateSessionId: sessionId,
  }
}
