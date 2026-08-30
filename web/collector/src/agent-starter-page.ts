import codingIcon from './assets/agent-starter/icons/agent-starter-coding.webp'
import knowledgeRagIcon from './assets/agent-starter/icons/agent-starter-knowledge-rag.webp'
import automationIcon from './assets/agent-starter/icons/agent-starter-automation.webp'
import voiceIcon from './assets/agent-starter/icons/agent-starter-voice.webp'
import personalAssistantIcon from './assets/agent-starter/icons/agent-starter-personal-assistant.webp'

import type {
  AgentStarterDeviceClass,
  AgentStarterEvidenceInput,
  AgentStarterExecutionInterface,
  AgentStarterExecutionPlatform,
  AgentStarterGoal,
  AgentStarterQuestionSet,
  AgentStarterRecommendation,
  AgentStarterCatalogEntryView,
  AgentStarterCandidateView,
} from './agent-starter-bridge'

export type AgentStarterPageState =
  | 'landing'
  | 'loading'
  | 'question'
  | 'complete'
  | 'recommending'
  | 'result'
  | 'error'

export interface AgentStarterPageOptions {
  state: AgentStarterPageState
  goal: AgentStarterGoal | null
  evidence: AgentStarterEvidenceInput[]
  questionSet: AgentStarterQuestionSet | null
  error: string | null
  environment?: AgentStarterEnvironmentDraft
  recommendation?: AgentStarterRecommendation | null
  runtimeOptions?: string[]
  runtimeOptionsError?: string | null
}

export interface AgentStarterEnvironmentDraft {
  deviceClass: AgentStarterDeviceClass
  platform: AgentStarterExecutionPlatform
  interface: AgentStarterExecutionInterface
  memoryGiB: string
  runtimes: string[] | null
}

export function createAgentStarterEnvironmentDraft():
  AgentStarterEnvironmentDraft {
  return {
    deviceClass: 'unknown',
    platform: 'unknown',
    interface: 'unknown',
    memoryGiB: '',
    runtimes: null,
  }
}

const AGENT_STARTER_GOALS = [
  {
    id: 'coding',
    icon: codingIcon,
    title: 'Coding',
    description:
      'Build an agent that can understand code, work with repositories, and optionally execute development tasks.',
  },
  {
    id: 'knowledge_rag',
    icon: knowledgeRagIcon,
    title: 'Knowledge / RAG',
    description:
      'Build an agent around documents, retrieval, citations, and controlled knowledge sources.',
  },
  {
    id: 'automation',
    icon: automationIcon,
    title: 'Automation',
    description:
      'Design an agent for workflows, tools, approvals, and repeatable operational tasks.',
  },
  {
    id: 'voice',
    icon: voiceIcon,
    title: 'Voice',
    description:
      'Build a voice-capable agent with audio, realtime, locality, and interaction requirements.',
  },
  {
    id: 'personal',
    icon: personalAssistantIcon,
    title: 'Personal Assistant',
    description:
      'Design an assistant with memory, proactive behavior, and user-controlled capabilities.',
  },
] as const

const DEFAULT_OPTIONS: AgentStarterPageOptions = {
  state: 'landing',
  goal: null,
  evidence: [],
  questionSet: null,
  error: null,
}

function escapeHtml(
  value: string,
): string {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;')
}

function labelForGoal(
  goal: AgentStarterGoal,
): string {
  switch (goal) {
    case 'coding':
      return 'Coding'
    case 'knowledge_rag':
      return 'Knowledge / RAG'
    case 'automation':
      return 'Automation'
    case 'voice':
      return 'Voice'
    case 'personal':
      return 'Personal Assistant'
  }
}

function renderGoalCards(): string {
  return AGENT_STARTER_GOALS
    .map(
      (goal) => `
        <button
          class="agent-starter-goal-card"
          type="button"
          data-agent-starter-goal="${goal.id}"
        >
          <span
            class="agent-starter-goal-mark"
            aria-hidden="true"
          >
            <img
              src="${goal.icon}"
              alt=""
              loading="lazy"
              decoding="async"
            >
          </span>

          <span class="agent-starter-goal-copy">
            <strong>${goal.title}</strong>
            <span>${goal.description}</span>
          </span>

          <span
            class="agent-starter-goal-arrow"
            aria-hidden="true"
          >
            →
          </span>
        </button>
      `,
    )
    .join('')
}

function renderLanding(): string {
  return `
    <section class="agent-starter-hero">
      <div class="agent-starter-hero-copy">
        <p class="hero-label">
          Agent Lab / Agent Starter
        </p>

        <p class="section-label">
          Core v1 complete
        </p>

        <h1>
          Build an agent for
          your actual environment.
        </h1>

        <p class="hero-copy">
          Tell DLLO what you want to build.
          Agent Starter combines your goals,
          constraints, preferences, and observed
          execution environment to produce
          evidence-backed architecture and
          stack recommendations.
        </p>

        <div
          class="agent-starter-principles"
          aria-label="Agent Starter principles"
        >
          <span>Explicit evidence</span>
          <span>Hard constraints</span>
          <span>Unknown stays unknown</span>
        </div>
      </div>

      <aside
        class="agent-starter-overview"
        aria-label="Agent Starter workflow"
      >
        <p class="section-label">
          How it works
        </p>

        <ol class="agent-starter-steps">
          <li>
            <span>01</span>
            <div>
              <strong>Goal</strong>
              <small>What do you want to build?</small>
            </div>
          </li>

          <li>
            <span>02</span>
            <div>
              <strong>Constraints</strong>
              <small>Privacy, cost, locality and behavior.</small>
            </div>
          </li>

          <li>
            <span>03</span>
            <div>
              <strong>Environment</strong>
              <small>Hardware, platform and runtime evidence.</small>
            </div>
          </li>

          <li>
            <span>04</span>
            <div>
              <strong>Recommendation</strong>
              <small>Architecture, stack, why and why not.</small>
            </div>
          </li>
        </ol>
      </aside>
    </section>

    <section
      class="agent-starter-goal-section"
      aria-labelledby="agent-starter-goal-heading"
    >
      <div class="agent-starter-section-heading">
        <div>
          <p class="section-label">
            Start here
          </p>

          <h2 id="agent-starter-goal-heading">
            What do you want to build?
          </h2>

          <p>
            Choose a goal. The next questions adapt
            to what is actually relevant to that agent.
          </p>
        </div>

        <span class="agent-starter-step-badge">
          Step 1 · Goal
        </span>
      </div>

      <div class="agent-starter-goal-grid">
        ${renderGoalCards()}
      </div>
    </section>

    <section class="agent-starter-method">
      <p class="section-label">
        Evidence before assumptions
      </p>

      <div class="agent-starter-method-grid">
        <article>
          <strong>Observe</strong>
          <p>
            Use declared and observable evidence about
            the target environment.
          </p>
        </article>

        <article>
          <strong>Constrain</strong>
          <p>
            Preserve privacy, offline, cost, and other
            hard requirements during selection.
          </p>
        </article>

        <article>
          <strong>Compare</strong>
          <p>
            Keep compatible, excluded, not recommended,
            and indeterminate candidates distinct.
          </p>
        </article>

        <article>
          <strong>Explain</strong>
          <p>
            Show why a recommendation was produced
            instead of hiding the decision path.
          </p>
        </article>
      </div>
    </section>
  `
}

function renderWizardHeader(
  goal: AgentStarterGoal,
  answered: number,
  stepLabel = 'Step 2 · Requirements',
): string {
  return `
    <header class="agent-starter-wizard-header">
      <div>
        <p class="hero-label">
          Agent Lab / Agent Starter
        </p>

        <p class="section-label">
          ${labelForGoal(goal)}
        </p>

        <h1>Configure your agent.</h1>
      </div>

      <div class="agent-starter-wizard-meta">
        <span>${escapeHtml(stepLabel)}</span>
        <small>
          ${answered} answer${answered === 1 ? '' : 's'} recorded
        </small>
      </div>
    </header>
  `
}

function renderLoading(
  options: AgentStarterPageOptions,
): string {
  if (options.goal === null) {
    return renderLanding()
  }

  return `
    ${renderWizardHeader(
      options.goal,
      options.evidence.length,
    )}

    <section
      class="agent-starter-question-panel"
      aria-live="polite"
    >
      <p class="section-label">
        Analysing requirements
      </p>

      <h2>Finding the next relevant question…</h2>

      <p>
        DLLO is recalculating the questionnaire from
        the evidence recorded so far.
      </p>
    </section>
  `
}

function renderQuestion(
  options: AgentStarterPageOptions,
): string {
  if (
    options.goal === null
    || options.questionSet === null
    || options.questionSet.questions.length === 0
  ) {
    return renderLoading(options)
  }

  const question =
    options.questionSet.questions[0]

  return `
    ${renderWizardHeader(
      options.goal,
      options.evidence.length,
    )}

    <section
      class="agent-starter-question-panel"
      aria-labelledby="agent-starter-question"
    >
      <p class="section-label">
        Adaptive questionnaire
      </p>

      <h2 id="agent-starter-question">
        ${escapeHtml(question.prompt)}
      </h2>

      <div class="agent-starter-question-reason">
        <strong>Why DLLO asks this</strong>
        <p>${escapeHtml(question.reason)}</p>
      </div>

      <div
        class="agent-starter-answer-grid"
        aria-label="Answer"
      >
        <button
          type="button"
          data-agent-starter-answer="true"
          data-agent-starter-question-key="${escapeHtml(
            question.key,
          )}"
        >
          <strong>Yes</strong>
          <span>This requirement applies.</span>
        </button>

        <button
          type="button"
          data-agent-starter-answer="false"
          data-agent-starter-question-key="${escapeHtml(
            question.key,
          )}"
        >
          <strong>No</strong>
          <span>This requirement does not apply.</span>
        </button>

        <button
          type="button"
          data-agent-starter-answer="unknown"
          data-agent-starter-question-key="${escapeHtml(
            question.key,
          )}"
        >
          <strong>I don't know</strong>
          <span>
            Keep this evidence explicitly unknown.
          </span>
        </button>
      </div>

      <footer class="agent-starter-question-footer">
        <button
          type="button"
          class="secondary-button"
          data-agent-starter-change-goal
        >
          ← Change goal
        </button>

        <p>
          Unknown answers are not treated as false.
        </p>
      </footer>
    </section>
  `
}

function selectedOption(
  value: string,
  current: string,
): string {
  return value === current
    ? ' selected'
    : ''
}

function renderComplete(
  options: AgentStarterPageOptions,
): string {
  if (options.goal === null) {
    return renderLanding()
  }

  const environment =
    options.environment
    ?? createAgentStarterEnvironmentDraft()

  const errorMessage =
    options.error === null
      ? ''
      : `
        <div
          class="agent-starter-environment-error"
          role="alert"
        >
          ${escapeHtml(options.error)}
        </div>
      `

  return `
    ${renderWizardHeader(
      options.goal,
      options.evidence.length,
      'Step 3 · Environment',
    )}

    <section
      class="agent-starter-environment-panel"
      aria-labelledby="agent-starter-environment-heading"
    >
      <div class="agent-starter-environment-intro">
        <p class="section-label">
          Requirements captured
        </p>

        <h2 id="agent-starter-environment-heading">
          Where will this agent run?
        </h2>

        <p>
          The adaptive questionnaire is complete.
          The next wizard stage captures only the
          execution evidence you actually know.
          Missing information remains unknown.
        </p>
      </div>

      ${errorMessage}

      <div class="agent-starter-environment-grid">
        <label>
          <span>Device class</span>
          <select id="agent-starter-device-class">
            <option
              value="unknown"${selectedOption(
                'unknown',
                environment.deviceClass,
              )}
            >
              I don't know
            </option>
            <option
              value="desktop"${selectedOption(
                'desktop',
                environment.deviceClass,
              )}
            >
              Desktop
            </option>
            <option
              value="laptop"${selectedOption(
                'laptop',
                environment.deviceClass,
              )}
            >
              Laptop
            </option>
            <option
              value="phone"${selectedOption(
                'phone',
                environment.deviceClass,
              )}
            >
              Phone
            </option>
            <option
              value="tablet"${selectedOption(
                'tablet',
                environment.deviceClass,
              )}
            >
              Tablet
            </option>
          </select>
        </label>

        <label>
          <span>Operating platform</span>
          <select id="agent-starter-platform">
            <option
              value="unknown"${selectedOption(
                'unknown',
                environment.platform,
              )}
            >
              I don't know
            </option>
            <option
              value="linux"${selectedOption(
                'linux',
                environment.platform,
              )}
            >
              Linux
            </option>
            <option
              value="windows"${selectedOption(
                'windows',
                environment.platform,
              )}
            >
              Windows
            </option>
            <option
              value="macos"${selectedOption(
                'macos',
                environment.platform,
              )}
            >
              macOS
            </option>
            <option
              value="android"${selectedOption(
                'android',
                environment.platform,
              )}
            >
              Android
            </option>
            <option
              value="ios"${selectedOption(
                'ios',
                environment.platform,
              )}
            >
              iOS
            </option>
          </select>
        </label>

        <label>
          <span>Execution interface</span>
          <select id="agent-starter-interface">
            <option
              value="unknown"${selectedOption(
                'unknown',
                environment.interface,
              )}
            >
              I don't know
            </option>
            <option
              value="native"${selectedOption(
                'native',
                environment.interface,
              )}
            >
              Native / local
            </option>
            <option
              value="browser"${selectedOption(
                'browser',
                environment.interface,
              )}
            >
              Browser
            </option>
          </select>
        </label>

        <label>
          <span>Available memory · GiB</span>
          <input
            id="agent-starter-memory-gib"
            type="number"
            min="0.25"
            step="0.25"
            inputmode="decimal"
            value="${escapeHtml(
              environment.memoryGiB,
            )}"
            placeholder="Unknown"
          >
          <small>
            Leave empty when memory is not known.
          </small>
        </label>

        <div
          class="
            agent-starter-runtime-field
            agent-starter-runtime-selector
          "
        >
          <span class="agent-starter-field-label">
            Known local runtimes
          </span>

          <p>
            Select every runtime currently available
            in this environment.
          </p>

          <div
            class="agent-starter-runtime-options"
            role="group"
            aria-label="Known local runtimes"
          >
            <button
              type="button"
              data-agent-starter-runtime="__unknown__"
              aria-pressed="${
                environment.runtimes === null
                  ? 'true'
                  : 'false'
              }"
              class="${
                environment.runtimes === null
                  ? 'is-selected'
                  : ''
              }"
            >
              ? Unknown
            </button>

            <button
              type="button"
              data-agent-starter-runtime="__none__"
              aria-pressed="${
                environment.runtimes !== null
                && environment.runtimes.length === 0
                  ? 'true'
                  : 'false'
              }"
              class="${
                environment.runtimes !== null
                && environment.runtimes.length === 0
                  ? 'is-selected'
                  : ''
              }"
            >
              None installed
            </button>

            ${(options.runtimeOptions ?? [])
              .map((runtime) => {
                const selected =
                  environment.runtimes
                    ?.includes(runtime)
                  ?? false

                return `
                  <button
                    type="button"
                    data-agent-starter-runtime="${escapeHtml(
                      runtime,
                    )}"
                    aria-pressed="${
                      selected
                        ? 'true'
                        : 'false'
                    }"
                    class="${
                      selected
                        ? 'is-selected'
                        : ''
                    }"
                  >
                    ${escapeHtml(runtime)}
                  </button>
                `
              })
              .join('')}
          </div>

          ${
            options.runtimeOptionsError
              ? `
                <small
                  class="agent-starter-runtime-warning"
                >
                  ${escapeHtml(
                    options.runtimeOptionsError,
                  )}
                  You can continue with Unknown.
                </small>
              `
              : `
                <small>
                  Unknown means the inventory is not
                  known. None installed means it is
                  known that no local runtime exists.
                </small>
              `
          }
        </div>
      </div>

      <div class="agent-starter-environment-note">
        <strong>Evidence rule</strong>
        <p>
          Agent Starter will not infer missing RAM,
          runtime or accelerator capability from the
          browser. Unknown does not mean incompatible.
        </p>
      </div>

      <footer class="agent-starter-environment-actions">
        <button
          type="button"
          class="secondary-button"
          data-agent-starter-change-goal
        >
          ← Start over
        </button>

        <button
          type="button"
          class="primary-button"
          id="generate-agent-starter-recommendation"
        >
          Generate recommendation →
        </button>
      </footer>
    </section>
  `
}


function renderRecommending(
  options: AgentStarterPageOptions,
): string {
  if (options.goal === null) {
    return renderLanding()
  }

  return `
    ${renderWizardHeader(
      options.goal,
      options.evidence.length,
      'Step 4 · Recommendation',
    )}

    <section
      class="agent-starter-question-panel"
      aria-live="polite"
    >
      <p class="section-label">
        Evaluating candidates
      </p>

      <h2>
        Building an evidence-backed recommendation…
      </h2>

      <p>
        DLLO is preparing requirements, assessing
        candidate architectures, matching the
        repository catalog, resolving concrete
        stacks, and preserving indeterminate results.
      </p>

      <div
        class="agent-starter-processing-line"
        aria-hidden="true"
      ></div>
    </section>
  `
}


function humanizeIdentifier(
  value: string,
): string {
  if (value.toLowerCase() === 'llm') {
    return 'LLM'
  }

  return value
    .split(/[-_]+/)
    .filter(Boolean)
    .map((part) => (
      part.charAt(0).toUpperCase()
      + part.slice(1)
    ))
    .join(' ')
}


function verdictLabel(
  verdict: string,
): string {
  switch (verdict) {
    case 'recommended':
      return 'Recommended'
    case 'possible':
      return 'Possible'
    case 'possible_but_not_recommended':
      return 'Possible · not recommended'
    case 'not_recommended':
      return 'Not recommended'
    default:
      return verdict
  }
}


function verdictClass(
  verdict: string,
): string {
  switch (verdict) {
    case 'recommended':
      return 'recommended'
    case 'possible':
      return 'possible'
    case 'possible_but_not_recommended':
      return 'limited'
    case 'not_recommended':
      return 'not-recommended'
    default:
      return 'unknown'
  }
}


function renderCatalogEntry(
  entry: AgentStarterCatalogEntryView,
): string {
  return `
    <div class="agent-starter-entry">
      <div>
        <strong>
          ${escapeHtml(entry.family)}
          ${escapeHtml(entry.version)}
        </strong>

        <small>
          ${escapeHtml(entry.vendor)}
        </small>
      </div>

      <code>${escapeHtml(entry.identifier)}</code>
    </div>
  `
}


function renderEntryGroup(
  label: string,
  entries: AgentStarterCatalogEntryView[],
  tone: string,
): string {
  if (entries.length === 0) {
    return ''
  }

  return `
    <details
      class="agent-starter-entry-group ${tone}"
    >
      <summary>
        <span>${escapeHtml(label)}</span>
        <strong>${entries.length}</strong>
      </summary>

      <div class="agent-starter-entry-list">
        ${entries
          .map(renderCatalogEntry)
          .join('')}
      </div>
    </details>
  `
}


function renderCandidate(
  candidate: AgentStarterCandidateView,
): string {
  const reasons = candidate.why.length > 0
    ? `
      <section class="agent-starter-reason-list">
        <strong>Why it fits</strong>
        <ul>
          ${candidate.why
            .map(
              (reason) =>
                `<li>${escapeHtml(reason)}</li>`,
            )
            .join('')}
        </ul>
      </section>
    `
    : ''

  const reasonsAgainst =
    candidate.whyNot.length > 0
      ? `
        <section class="agent-starter-reason-list why-not">
          <strong>Why not</strong>
          <ul>
            ${candidate.whyNot
              .map(
                (reason) =>
                  `<li>${escapeHtml(reason)}</li>`,
              )
              .join('')}
          </ul>
        </section>
      `
      : ''

  const components =
    candidate.components
      .map((component) => {
        let noSelectionMessage =
          'No concrete entry was automatically selected.'

        if (component.matchedEntries.length > 1) {
          noSelectionMessage =
            `${component.matchedEntries.length} catalog entries match. `
            + 'DLLO does not choose between multiple valid matches '
            + 'without an explicit ranking basis.'
        } else if (
          component.matchedEntries.length === 0
          && component.indeterminateEntries.length > 0
        ) {
          noSelectionMessage =
            'Available evidence is insufficient to select '
            + 'a concrete catalog entry.'
        } else if (
          component.matchedEntries.length === 0
          && component.notRecommendedEntries.length > 0
        ) {
          noSelectionMessage =
            'No catalog entry is currently recommended '
            + 'for the declared environment.'
        }

        const selected =
          component.selectedEntry === null
            ? `
              <div
                class="agent-starter-no-selection"
              >
                ${escapeHtml(noSelectionMessage)}
              </div>
            `
            : `
              <div
                class="agent-starter-selected-entry"
              >
                <span>Selected</span>
                ${renderCatalogEntry(
                  component.selectedEntry,
                )}
              </div>
            `

        return `
          <section class="agent-starter-component">
            <div class="agent-starter-component-heading">
              <span>Component</span>
              <strong>
                ${escapeHtml(
                  humanizeIdentifier(
                    component.componentType,
                  ),
                )}
              </strong>
            </div>

            ${selected}

            <div class="agent-starter-result-groups">
              ${renderEntryGroup(
                'Matched',
                component.matchedEntries,
                'matched',
              )}

              ${renderEntryGroup(
                'Constrained',
                component.constrainedEntries,
                'constrained',
              )}

              ${renderEntryGroup(
                'Indeterminate',
                component.indeterminateEntries,
                'indeterminate',
              )}

              ${renderEntryGroup(
                'Not recommended',
                component.notRecommendedEntries,
                'not-recommended',
              )}

              ${renderEntryGroup(
                'Constraint excluded',
                component.constraintExcludedEntries,
                'excluded',
              )}
            </div>
          </section>
        `
      })
      .join('')

  return `
    <article class="agent-starter-candidate">
      <header class="agent-starter-candidate-header">
        <div>
          <p class="section-label">
            Architecture
          </p>

          <h3>
            ${escapeHtml(
              humanizeIdentifier(
                candidate.architectureId,
              ),
            )}
          </h3>

          <code>
            ${escapeHtml(candidate.architectureId)}
          </code>
        </div>

        <span
          class="
            agent-starter-verdict
            ${verdictClass(candidate.verdict)}
          "
        >
          ${escapeHtml(
            verdictLabel(candidate.verdict),
          )}
        </span>
      </header>

      ${reasons}
      ${reasonsAgainst}

      <div class="agent-starter-components">
        ${components}
      </div>
    </article>
  `
}


function renderResult(
  options: AgentStarterPageOptions,
): string {
  if (
    options.goal === null
    || options.recommendation === null
    || options.recommendation === undefined
  ) {
    return renderLoading(options)
  }

  const recommendation =
    options.recommendation

  const hasRecommendedArchitecture =
    recommendation
      .recommendedArchitectureIds
      .length > 0

  const hasPossibleArchitecture =
    recommendation.alternativeArchitectureIds
      .length > 0

  const hasLimitedArchitecture =
    recommendation
      .possibleButNotRecommendedArchitectureIds
      .length > 0

  const hasConcreteSelection =
    recommendation.candidates.some(
      (candidate) =>
        candidate.components.some(
          (component) =>
            component.selectedEntry !== null,
        ),
    )

  const unknownEvidence =
    recommendation.unknownEvidenceKeys.length === 0
      ? ''
      : `
        <section class="agent-starter-result-aside">
          <strong>Unknown evidence preserved</strong>
          <ul>
            ${recommendation
              .unknownEvidenceKeys
              .map(
                (key) =>
                  `<li>${escapeHtml(
                    humanizeIdentifier(key),
                  )}</li>`,
              )
              .join('')}
          </ul>
        </section>
      `

  const blockers =
    recommendation.blockerKeys.length === 0
      ? ''
      : `
        <section class="agent-starter-result-aside">
          <strong>Blocking constraints</strong>
          <ul>
            ${recommendation
              .blockerKeys
              .map(
                (key) =>
                  `<li>${escapeHtml(
                    humanizeIdentifier(key),
                  )}</li>`,
              )
              .join('')}
          </ul>
        </section>
      `

  return `
    ${renderWizardHeader(
      options.goal,
      options.evidence.length,
      'Step 4 · Recommendation',
    )}

    <section class="agent-starter-result">
      <header class="agent-starter-result-hero">
        <div>
          <p class="section-label">
            Analysis complete
          </p>

          <h2>
            ${
              hasRecommendedArchitecture
                ? 'Recommendation ready.'
                : hasPossibleArchitecture
                  ? 'A viable architecture was found.'
                  : hasLimitedArchitecture
                    ? 'A limited architecture was found.'
                    : 'No automatic architecture recommendation.'
            }
          </h2>

          <p>
            ${
              hasConcreteSelection
                ? (
                    'DLLO found concrete catalog entries '
                    + 'supported by the recorded evidence.'
                  )
                : (
                    'DLLO preserved uncertainty instead '
                    + 'of selecting a concrete component '
                    + 'without enough evidence.'
                  )
            }
          </p>
        </div>

        <div class="agent-starter-provenance-card">
          <span>Catalog provenance</span>
          <code>
            ${escapeHtml(
              recommendation.catalogSnapshotId,
            )}
          </code>
        </div>
      </header>

      <div class="agent-starter-result-summary">
        <article>
          <strong>
            ${recommendation
              .recommendedArchitectureIds.length}
          </strong>
          <span>Recommended</span>
        </article>

        <article>
          <strong>
            ${recommendation
              .alternativeArchitectureIds.length}
          </strong>
          <span>Possible</span>
        </article>

        <article>
          <strong>
            ${recommendation
              .possibleButNotRecommendedArchitectureIds
              .length}
          </strong>
          <span>Limited</span>
        </article>

        <article>
          <strong>
            ${recommendation
              .notRecommendedArchitectureIds.length}
          </strong>
          <span>Not recommended</span>
        </article>
      </div>

      <div class="agent-starter-result-context">
        ${unknownEvidence}
        ${blockers}
      </div>

      <div class="agent-starter-candidate-list">
        ${recommendation.candidates
          .map(renderCandidate)
          .join('')}
      </div>

      <footer class="agent-starter-result-footer">
        <p>
          Results are projections of recorded evidence,
          constraints, catalog provenance, and the
          Agent Starter decision pipeline.
        </p>

        <button
          type="button"
          class="secondary-button"
          data-agent-starter-change-goal
        >
          ← Start another configuration
        </button>
      </footer>
    </section>
  `
}


function renderError(
  options: AgentStarterPageOptions,
): string {
  if (options.goal === null) {
    return renderLanding()
  }

  return `
    ${renderWizardHeader(
      options.goal,
      options.evidence.length,
    )}

    <section
      class="agent-starter-question-panel agent-starter-error"
      role="alert"
    >
      <p class="section-label">
        Questionnaire unavailable
      </p>

      <h2>
        Agent Starter could not load the next question.
      </h2>

      <p>
        ${escapeHtml(
          options.error
          ?? 'Unable to reach the local DLLO Bridge.',
        )}
      </p>

      <button
        type="button"
        class="secondary-button"
        data-agent-starter-change-goal
      >
        ← Change goal
      </button>
    </section>
  `
}

export function renderAgentStarterPage(
  options: AgentStarterPageOptions =
    DEFAULT_OPTIONS,
): string {
  let content: string

  switch (options.state) {
    case 'landing':
      content = renderLanding()
      break
    case 'loading':
      content = renderLoading(options)
      break
    case 'question':
      content = renderQuestion(options)
      break
    case 'complete':
      content = renderComplete(options)
      break
    case 'recommending':
      content = renderRecommending(options)
      break
    case 'result':
      content = renderResult(options)
      break
    case 'error':
      content = renderError(options)
      break
  }

  return `
    <main
      class="agent-starter-page"
      data-agent-starter-state="${options.state}"
    >
      ${content}
    </main>
  `
}
