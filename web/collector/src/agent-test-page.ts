export type AgentTestPageState =
  | 'disconnected'
  | 'running'
  | 'success'
  | 'failed'

export interface AgentTestPageOptions {
  state: AgentTestPageState
  baseUrl: string
}

const stateVisuals: Record<
  AgentTestPageState,
  string
> = {
  disconnected: new URL(
    '../../assets/visuals/no-agent.webp',
    import.meta.url,
  ).href,
  running: new URL(
    '../../assets/visuals/benchmark-lab.webp',
    import.meta.url,
  ).href,
  success: new URL(
    '../../assets/visuals/experiment-complete.webp',
    import.meta.url,
  ).href,
  failed: new URL(
    '../../assets/visuals/experiment-failed.webp',
    import.meta.url,
  ).href,
}

const stateLabels: Record<
  AgentTestPageState,
  string
> = {
  disconnected: 'Agent not connected',
  running: 'Test running',
  success: 'Test completed',
  failed: 'Test failed',
}

export function renderAgentTestPage(
  options: AgentTestPageOptions,
): string {
  const visualUrl = stateVisuals[options.state]
  const stateLabel = stateLabels[options.state]

  return `
    <main class="agent-test-page">
      <section class="agent-test-hero">
        <div class="agent-test-copy">
          <p class="hero-label">Agent Lab</p>

          <h1>Test Your Agent</h1>

          <p>
            Connect an agent through the Local SUT Protocol
            and evaluate its behavior with
            Agent Protocol Core 1.0.
          </p>

          <p>
            DLLO collects observer-owned evidence and
            produces a technical report without allowing
            the system under test to certify itself.
          </p>
        </div>

        <div class="agent-test-visual">
          <img
            src="${visualUrl}"
            alt="${stateLabel}"
          />
        </div>
      </section>

      <section class="agent-test-console">
        <div class="panel-heading">
          <div>
            <p class="section-label">
              Local agent connection
            </p>

            <h2>${stateLabel}</h2>
          </div>

          <span
            class="badge"
            data-agent-test-state="${options.state}"
          >
            ${options.state}
          </span>
        </div>

        <label
          class="agent-endpoint-field"
          for="agent-base-url"
        >
          Agent endpoint
        </label>

        <input
          id="agent-base-url"
          name="agent-base-url"
          type="url"
          value="${options.baseUrl}"
          placeholder="http://127.0.0.1:8000"
          autocomplete="off"
          spellcheck="false"
        />

        <div class="agent-test-protocol">
          <div>
            <span>Protocol</span>
            <strong>Agent Protocol Core 1.0</strong>
          </div>

          <div>
            <span>Transport</span>
            <strong>Local SUT Protocol</strong>
          </div>

          <div>
            <span>Evidence</span>
            <strong>Observer-owned</strong>
          </div>
        </div>

        <div class="agent-test-actions">
          <button
            type="button"
            id="run-agent-test"
            ${
              options.state === 'running'
                ? 'disabled'
                : ''
            }
          >
            ${
              options.state === 'running'
                ? 'Running test...'
                : 'Run Agent Test'
            }
          </button>

          <a
            href="#/agent-lab"
            class="secondary-action"
          >
            Back to Agent Lab
          </a>
        </div>

        <details class="agent-test-advanced">
          <summary>Advanced settings</summary>

          <p>
            Observer identity, region, suite bank,
            and task bank will use the canonical DLLO
            defaults unless explicitly configured.
          </p>
        </details>
      </section>
    </main>
  `
}
