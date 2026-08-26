import type {
  AgentTestBridgeResponse,
} from './agent-test-bridge'


export type AgentTestPageState =
  | 'disconnected'
  | 'running'
  | 'success'
  | 'failed'

export interface AgentTestPageOptions {
  state: AgentTestPageState
  baseUrl: string
  result?: AgentTestBridgeResponse | null
  error?: string | null
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

function renderRunningIndicator(): string {
  return `
    <div
      class="agent-test-running"
      data-agent-test-loader="running"
      role="status"
      aria-live="polite"
    >
      <div
        class="dllo-orbit"
        aria-hidden="true"
      >
        <span class="dllo-orbit-ring dllo-orbit-ring-outer"></span>
        <span class="dllo-orbit-ring dllo-orbit-ring-inner"></span>
        <span class="dllo-orbit-core"></span>
      </div>

      <div class="agent-test-running-copy">
        <strong>Running Agent Protocol</strong>
        <span>
          Collecting observer-owned evidence...
        </span>
      </div>
    </div>
  `
}


function renderFailureMessage(
  error: string,
  baseUrl: string,
): string {
  return `
    <div
      class="agent-test-error"
      data-agent-test-error="failed"
      role="alert"
    >
      <div class="agent-test-error-copy">
        <p class="section-label">
          Agent test error
        </p>

        <strong>
          ${escapeHtml(error)}
        </strong>

        <p>
          Verify that the agent is running and exposes
          the DLLO Local SUT Protocol.
        </p>
      </div>

      <div class="agent-test-error-endpoint">
        <span>Endpoint</span>
        <code>${escapeHtml(baseUrl)}</code>
      </div>
    </div>
  `
}


function renderTechnicalSummary(
  result: AgentTestBridgeResponse,
): string {
  const passRate =
    result.pass_rate === null
      ? 'n/a'
      : `${Math.round(result.pass_rate * 1000) / 10}%`

  const medianLatency =
    result.median_latency_ms === null
      ? 'n/a'
      : `${
          Math.round(
            result.median_latency_ms * 100,
          ) / 100
        } ms`

  const findings = result.findings.length === 0
    ? '<li>No findings.</li>'
    : result.findings
        .map(
          (finding) => (
            `<li>${escapeHtml(finding)}</li>`
          ),
        )
        .join('')

  const recommendations =
    result.recommendations.length === 0
      ? '<li>No recommendations.</li>'
      : result.recommendations
          .map(
            (recommendation) => (
              `<li>${escapeHtml(recommendation)}</li>`
            ),
          )
          .join('')

  return `
    <section class="agent-technical-report">
      <div class="panel-heading">
        <div>
          <p class="section-label">
            Technical report
          </p>

          <h2>
            ${escapeHtml(result.target_id)}
          </h2>
        </div>
      </div>

      <div class="agent-report-metrics">
        <div>
          <span>Protocol</span>
          <strong>
            ${escapeHtml(result.suite_id)}
            ${escapeHtml(result.suite_version)}
          </strong>
        </div>

        <div>
          <span>Tasks passed</span>
          <strong>
            ${result.passed_tasks} / ${result.total_tasks}
          </strong>
        </div>

        <div>
          <span>Pass rate</span>
          <strong>${passRate}</strong>
        </div>

        <div>
          <span>Median latency</span>
          <strong>${medianLatency}</strong>
        </div>
      </div>

      <div class="agent-report-observatory">
        <p>
          Observer
          <strong>
            ${escapeHtml(result.observer_id ?? 'n/a')}
          </strong>
        </p>

        <p>
          <strong>
            Observed from ${escapeHtml(
              result.region_code ?? 'n/a',
            )}
          </strong>
        </p>

        <p>
          ${
            result.observatory.temporal_eligible
              ? 'Temporal eligible'
              : 'Temporal not eligible'
          }
        </p>

        <p>
          ${
            result.observatory.geographic_eligible
              ? 'Geographic eligible'
              : 'Geographic not eligible'
          }
        </p>
      </div>

      <div class="agent-report-notes">
        <div>
          <h3>Findings</h3>
          <ul>${findings}</ul>
        </div>

        <div>
          <h3>Recommendations</h3>
          <ul>${recommendations}</ul>
        </div>
      </div>
    </section>
  `
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

        ${
          options.state === 'running'
            ? renderRunningIndicator()
            : ''
        }

        ${
          options.state === 'failed'
          && options.error
            ? renderFailureMessage(
                options.error,
                options.baseUrl,
              )
            : ''
        }

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
                : options.state === 'failed'
                  ? 'Retry Agent Test'
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

      ${
        options.result === undefined
        || options.result === null
          ? ''
          : renderTechnicalSummary(
              options.result,
            )
      }
    </main>
  `
}
