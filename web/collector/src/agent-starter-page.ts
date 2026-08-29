const AGENT_STARTER_GOALS = [
  {
    id: 'coding',
    mark: '</>',
    title: 'Coding',
    description:
      'Build an agent that can understand code, work with repositories, and optionally execute development tasks.',
  },
  {
    id: 'knowledge-rag',
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

export function renderAgentStarterPage(): string {
  return `
    <main class="agent-starter-page">
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
    </main>
  `
}
