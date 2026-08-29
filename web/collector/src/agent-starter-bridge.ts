export type AgentStarterGoal =
  | 'personal'
  | 'knowledge_rag'
  | 'coding'
  | 'automation'
  | 'voice'

export type AgentStarterEvidenceSource =
  | 'declared'
  | 'unknown'

export interface AgentStarterEvidenceInput {
  key: string
  source: AgentStarterEvidenceSource
  value: boolean | null
  reason?: string
}

export interface AgentStarterIntakeRequest {
  goal: AgentStarterGoal
  evidence: AgentStarterEvidenceInput[]
  hardware_profile: null
  execution_environment: null
}

export interface AgentStarterQuestion {
  schema_version: '0.1'
  key: string
  goal: AgentStarterGoal
  prompt: string
  kind: 'boolean'
  reason: string
}

export interface AgentStarterQuestionSet {
  schema_version: '0.1'
  goal: AgentStarterGoal
  questions: AgentStarterQuestion[]
}

export interface AgentStarterFetchResponse {
  ok: boolean
  status: number
  json(): Promise<unknown>
}

export type AgentStarterFetch = (
  input: string,
  init: {
    method: string
    headers: Record<string, string>
    body: string
  },
) => Promise<AgentStarterFetchResponse>

const AGENT_STARTER_GOALS =
  new Set<AgentStarterGoal>([
    'personal',
    'knowledge_rag',
    'coding',
    'automation',
    'voice',
  ])

export function isAgentStarterGoal(
  value: string,
): value is AgentStarterGoal {
  return AGENT_STARTER_GOALS.has(
    value as AgentStarterGoal,
  )
}

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === 'object'
    && value !== null
    && !Array.isArray(value)
  )
}

function parseQuestion(
  value: unknown,
): AgentStarterQuestion {
  if (!isRecord(value)) {
    throw new Error(
      'Invalid Agent Starter question.',
    )
  }

  const {
    schema_version: schemaVersion,
    key,
    goal,
    prompt,
    kind,
    reason,
  } = value

  if (
    schemaVersion !== '0.1'
    || typeof key !== 'string'
    || key.length === 0
    || typeof goal !== 'string'
    || !isAgentStarterGoal(goal)
    || typeof prompt !== 'string'
    || prompt.length === 0
    || kind !== 'boolean'
    || typeof reason !== 'string'
    || reason.length === 0
  ) {
    throw new Error(
      'Invalid Agent Starter question.',
    )
  }

  return {
    schema_version: '0.1',
    key,
    goal,
    prompt,
    kind: 'boolean',
    reason,
  }
}

export function parseAgentStarterQuestionSet(
  value: unknown,
): AgentStarterQuestionSet {
  if (!isRecord(value)) {
    throw new Error(
      'Invalid Agent Starter questionnaire response.',
    )
  }

  const {
    schema_version: schemaVersion,
    goal,
    questions,
  } = value

  if (
    schemaVersion !== '0.1'
    || typeof goal !== 'string'
    || !isAgentStarterGoal(goal)
    || !Array.isArray(questions)
  ) {
    throw new Error(
      'Invalid Agent Starter questionnaire response.',
    )
  }

  const parsedQuestions =
    questions.map(parseQuestion)

  if (
    parsedQuestions.some(
      (question) => question.goal !== goal,
    )
  ) {
    throw new Error(
      'Agent Starter questionnaire contains a mismatched goal.',
    )
  }

  return {
    schema_version: '0.1',
    goal,
    questions: parsedQuestions,
  }
}

export async function fetchAgentStarterQuestions(
  fetchImpl: AgentStarterFetch,
  intake: AgentStarterIntakeRequest,
): Promise<AgentStarterQuestionSet> {
  const response = await fetchImpl(
    '/v1/agent-starter/questions',
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(intake),
    },
  )

  if (!response.ok) {
    throw new Error(
      `Agent Starter questionnaire request failed with HTTP ${response.status}.`,
    )
  }

  return parseAgentStarterQuestionSet(
    await response.json(),
  )
}
