import type {
  AgentStarterEvidenceInput,
  AgentStarterGoal,
  AgentStarterQuestionSet,
} from './agent-starter-bridge'

export type AgentStarterPageState =
  | 'landing'
  | 'loading'
  | 'question'
  | 'complete'
  | 'error'

export interface AgentStarterPageOptions {
  state: AgentStarterPageState
  goal: AgentStarterGoal | null
  evidence: AgentStarterEvidenceInput[]
  questionSet: AgentStarterQuestionSet | null
  error: string | null
}

const AGENT_STARTER_GOALS = [
  {
    id: 'coding',
    mark: '</>',
    title: 'Coding',
    description:
      'Build an agent that can understand code, work with repositories, and optionally execute development tasks.',
  },
  {
    id: 'knowledge_rag',
    mark: 'RAG',
    title: 'Knowledge / RAG',
    description:
      'Build an agent around documents, retrieval, citations, and controlled knowledge sources.',
  },
  {
    id: 'automation',
    mark: 'AUTO',
    title: 'Automation',
    description:
      'Design an agent for workflows, tools, approvals, and repeatable operational tasks.',
  },
  {
    id: 'voice',
    mark: 'VOICE',
    title: 'Voice',
    description:
      'Build a voice-capable agent with audio, realtime, locality, and interaction requirements.',
  },
  {
    id: 'personal',
    mark: 'AI',
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
            ${goal.mark}
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
        <span>Step 2 · Requirements</span>
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

function renderComplete(
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
      class="agent-starter-question-panel agent-starter-requirements-complete"
      aria-live="polite"
    >
      <p class="section-label">
        Requirements captured
      </p>

      <h2>
        The adaptive questionnaire is complete.
      </h2>

      <p>
        DLLO recorded ${options.evidence.length}
        explicit answers for this ${labelForGoal(
          options.goal,
        )} agent.
      </p>

      <p>
        The next wizard stage will combine these
        requirements with hardware and execution
        environment evidence.
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
