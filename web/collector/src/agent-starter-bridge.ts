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

export type AgentStarterDeviceClass =
  | 'desktop'
  | 'laptop'
  | 'phone'
  | 'tablet'
  | 'unknown'

export type AgentStarterExecutionPlatform =
  | 'linux'
  | 'windows'
  | 'macos'
  | 'android'
  | 'ios'
  | 'unknown'

export type AgentStarterExecutionInterface =
  | 'native'
  | 'browser'
  | 'unknown'

export interface AgentStarterHardwareProfileInput {
  device_class: AgentStarterDeviceClass
  source: 'manual' | 'browser_limited'
  total_memory_bytes: number | null
  limitations: string[]
}

export interface AgentStarterExecutionEnvironmentInput {
  platform: AgentStarterExecutionPlatform
  interface: AgentStarterExecutionInterface
  available_runtimes: string[] | null
  accelerator_access: 'unknown'
  filesystem_access: 'unknown'
  limitations: string[]
}

export interface AgentStarterIntakeRequest {
  goal: AgentStarterGoal
  evidence: AgentStarterEvidenceInput[]
  hardware_profile:
    AgentStarterHardwareProfileInput | null
  execution_environment:
    AgentStarterExecutionEnvironmentInput | null
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


export interface AgentStarterCatalogEntryView {
  identifier: string
  vendor: string
  family: string
  version: string
}

export interface AgentStarterStackComponentView {
  componentType: string
  matchedEntries: AgentStarterCatalogEntryView[]
  constrainedEntries: AgentStarterCatalogEntryView[]
  indeterminateEntries: AgentStarterCatalogEntryView[]
  notRecommendedEntries: AgentStarterCatalogEntryView[]
  constraintExcludedEntries:
    AgentStarterCatalogEntryView[]
  selectedEntry: AgentStarterCatalogEntryView | null
}

export interface AgentStarterCandidateView {
  architectureId: string
  verdict: string
  why: string[]
  whyNot: string[]
  components: AgentStarterStackComponentView[]
}

export interface AgentStarterRecommendation {
  schema_version: '0.1'
  catalogSnapshotId: string

  recommendedArchitectureIds: string[]
  alternativeArchitectureIds: string[]
  possibleButNotRecommendedArchitectureIds: string[]
  notRecommendedArchitectureIds: string[]

  candidates: AgentStarterCandidateView[]

  blockerKeys: string[]
  unknownEvidenceKeys: string[]
}

function parseStringArray(
  value: unknown,
  errorMessage: string,
): string[] {
  if (
    !Array.isArray(value)
    || value.some(
      (item) => typeof item !== 'string',
    )
  ) {
    throw new Error(errorMessage)
  }

  return value as string[]
}

function parseCatalogEntry(
  value: unknown,
): AgentStarterCatalogEntryView {
  if (!isRecord(value)) {
    throw new Error(
      'Invalid Agent Starter catalog entry.',
    )
  }

  const {
    identifier,
    vendor,
    family,
    version,
  } = value

  if (
    typeof identifier !== 'string'
    || typeof vendor !== 'string'
    || typeof family !== 'string'
    || typeof version !== 'string'
  ) {
    throw new Error(
      'Invalid Agent Starter catalog entry.',
    )
  }

  return {
    identifier,
    vendor,
    family,
    version,
  }
}

function parseCatalogEntries(
  value: unknown,
): AgentStarterCatalogEntryView[] {
  if (!Array.isArray(value)) {
    throw new Error(
      'Invalid Agent Starter catalog entry list.',
    )
  }

  return value.map(parseCatalogEntry)
}

function parseStackComponent(
  value: unknown,
): AgentStarterStackComponentView {
  if (!isRecord(value)) {
    throw new Error(
      'Invalid Agent Starter stack component.',
    )
  }

  const requirement = value.requirement

  if (
    !isRecord(requirement)
    || typeof requirement.component_type !== 'string'
  ) {
    throw new Error(
      'Invalid Agent Starter stack requirement.',
    )
  }

  const selectedRaw = value.selected_entry

  let selectedEntry:
    AgentStarterCatalogEntryView | null = null

  if (selectedRaw !== null) {
    selectedEntry = parseCatalogEntry(
      selectedRaw,
    )
  }

  return {
    componentType: requirement.component_type,
    matchedEntries:
      parseCatalogEntries(
        value.matched_entries,
      ),
    constrainedEntries:
      parseCatalogEntries(
        value.constrained_entries,
      ),
    indeterminateEntries:
      parseCatalogEntries(
        value.indeterminate_entries,
      ),
    notRecommendedEntries:
      parseCatalogEntries(
        value.not_recommended_entries,
      ),
    constraintExcludedEntries:
      parseCatalogEntries(
        value.constraint_excluded_entries,
      ),
    selectedEntry,
  }
}

function parseCandidate(
  value: unknown,
): AgentStarterCandidateView {
  if (!isRecord(value)) {
    throw new Error(
      'Invalid Agent Starter candidate explanation.',
    )
  }

  const assessment = value.assessment
  const stack = value.concrete_stack

  if (
    !isRecord(assessment)
    || typeof assessment.architecture_id !== 'string'
    || typeof assessment.recommendation !== 'string'
    || !isRecord(stack)
    || !Array.isArray(stack.components)
  ) {
    throw new Error(
      'Invalid Agent Starter candidate explanation.',
    )
  }

  return {
    architectureId:
      assessment.architecture_id,
    verdict:
      assessment.recommendation,
    why: parseStringArray(
      value.why,
      'Invalid Agent Starter why explanation.',
    ),
    whyNot: parseStringArray(
      value.why_not,
      'Invalid Agent Starter why-not explanation.',
    ),
    components:
      stack.components.map(
        parseStackComponent,
      ),
  }
}

function parseKeyProjection(
  value: unknown,
  errorMessage: string,
): string[] {
  if (!Array.isArray(value)) {
    throw new Error(errorMessage)
  }

  return value.map((item) => {
    if (
      !isRecord(item)
      || typeof item.key !== 'string'
    ) {
      throw new Error(errorMessage)
    }

    return item.key
  })
}

export function parseAgentStarterRecommendation(
  value: unknown,
): AgentStarterRecommendation {
  if (!isRecord(value)) {
    throw new Error(
      'Invalid Agent Starter recommendation response.',
    )
  }

  const context = value.context

  if (!isRecord(context)) {
    throw new Error(
      'Invalid Agent Starter recommendation context.',
    )
  }

  const snapshot =
    context.catalog_snapshot

  if (
    !isRecord(snapshot)
    || typeof snapshot.snapshot_id !== 'string'
  ) {
    throw new Error(
      'Invalid Agent Starter catalog provenance.',
    )
  }

  if (
    value.schema_version !== '0.1'
    || !Array.isArray(
      value.candidate_explanations,
    )
  ) {
    throw new Error(
      'Invalid Agent Starter recommendation response.',
    )
  }

  return {
    schema_version: '0.1',

    catalogSnapshotId:
      snapshot.snapshot_id,

    recommendedArchitectureIds:
      parseStringArray(
        value.recommended_architecture_ids,
        'Invalid recommended architecture list.',
      ),

    alternativeArchitectureIds:
      parseStringArray(
        value.alternative_architecture_ids,
        'Invalid alternative architecture list.',
      ),

    possibleButNotRecommendedArchitectureIds:
      parseStringArray(
        value
          .possible_but_not_recommended_architecture_ids,
        'Invalid possible-but-not-recommended list.',
      ),

    notRecommendedArchitectureIds:
      parseStringArray(
        value.not_recommended_architecture_ids,
        'Invalid not-recommended architecture list.',
      ),

    candidates:
      value.candidate_explanations.map(
        parseCandidate,
      ),

    blockerKeys:
      parseKeyProjection(
        value.blockers,
        'Invalid Agent Starter blocker projection.',
      ),

    unknownEvidenceKeys:
      parseKeyProjection(
        value.unknown_evidence,
        'Invalid Agent Starter unknown evidence projection.',
      ),
  }
}

export async function fetchAgentStarterRecommendation(
  fetchImpl: AgentStarterFetch,
  intake: AgentStarterIntakeRequest,
): Promise<AgentStarterRecommendation> {
  const response = await fetchImpl(
    '/v1/agent-starter/recommend',
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
      `Agent Starter recommendation request failed with HTTP ${response.status}.`,
    )
  }

  return parseAgentStarterRecommendation(
    await response.json(),
  )
}


export interface AgentStarterRuntimeOptions {
  schema_version: '0.1'
  catalogSnapshotId: string
  runtimes: string[]
}

export type AgentStarterReadFetch = (
  input: string,
) => Promise<AgentStarterFetchResponse>

export function parseAgentStarterRuntimeOptions(
  value: unknown,
): AgentStarterRuntimeOptions {
  if (!isRecord(value)) {
    throw new Error(
      'Invalid Agent Starter runtime options response.',
    )
  }

  if (
    value.schema_version !== '0.1'
    || typeof value.catalog_snapshot_id !== 'string'
    || !Array.isArray(value.runtimes)
    || value.runtimes.some(
      (runtime) => (
        typeof runtime !== 'string'
        || runtime.length === 0
      ),
    )
  ) {
    throw new Error(
      'Invalid Agent Starter runtime options response.',
    )
  }

  const runtimes =
    value.runtimes as string[]

  if (
    new Set(runtimes).size
    !== runtimes.length
  ) {
    throw new Error(
      'Agent Starter runtime options contain duplicates.',
    )
  }

  return {
    schema_version: '0.1',
    catalogSnapshotId:
      value.catalog_snapshot_id,
    runtimes: [...runtimes],
  }
}

export async function fetchAgentStarterRuntimeOptions(
  fetchImpl: AgentStarterReadFetch,
): Promise<AgentStarterRuntimeOptions> {
  const response = await fetchImpl(
    '/v1/agent-starter/runtime-options',
  )

  if (!response.ok) {
    throw new Error(
      `Agent Starter runtime options request failed with HTTP ${response.status}.`,
    )
  }

  return parseAgentStarterRuntimeOptions(
    await response.json(),
  )
}
