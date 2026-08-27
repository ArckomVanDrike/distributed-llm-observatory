import type {
  AgentTestBridgeResponse,
} from './agent-test-bridge'

import type {
  AgentTestHistoryResponse,
} from './agent-test-history'

import type {
  AgentTemporalComparisonResponse,
} from './agent-test-comparison'


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
  history?: AgentTestHistoryResponse | null
  baselineSessionId?: string | null
  candidateSessionId?: string | null
  comparison?: AgentTemporalComparisonResponse | null
  comparisonError?: string | null
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


function renderAgentTestHistory(
  history: AgentTestHistoryResponse,
  baselineSessionId: string | null,
  candidateSessionId: string | null,
): string {
  if (history.runs.length === 0) {
    return `
      <section
        class="agent-test-history"
        data-agent-test-history="empty"
      >
        <div class="panel-heading">
          <div>
            <p class="section-label">
              Agent observations
            </p>

            <h2>Run History</h2>
          </div>
        </div>

        <div class="agent-test-history-empty">
          <strong>
            No saved agent runs yet.
          </strong>

          <p>
            Completed Agent Lab observations will appear here after a test.
          </p>
        </div>
      </section>
    `
  }

  const runs = history.runs
    .map((run) => {
      const role =
        run.session_id === baselineSessionId
          ? 'baseline'
          : run.session_id === candidateSessionId
            ? 'candidate'
            : null

      const roleAttribute =
        role === null
          ? ''
          : `data-observation-role="${role}"`

      const roleLabel =
        role === null
          ? ''
          : `
              <span class="agent-history-role">
                ${
                  role === 'baseline'
                    ? 'Baseline'
                    : 'Candidate'
                }
              </span>
            `

      const passRate =
        run.pass_rate === null
          ? 'n/a'
          : `${
              Math.round(
                run.pass_rate * 1000,
              ) / 10
            }%`

      const medianLatency =
        run.median_latency_ms === null
          ? 'n/a'
          : `${
              Math.round(
                run.median_latency_ms * 100,
              ) / 100
            } ms`

      return `
        <article
          class="agent-history-run"
          data-session-id="${escapeHtml(
            run.session_id,
          )}"
          ${roleAttribute}
        >
          <div class="agent-history-run-heading">
            <div>
              <span class="agent-history-run-time">
                ${escapeHtml(run.started_at_utc)}
              </span>

              <h3>
                ${escapeHtml(run.target_id)}
              </h3>
            </div>

            <div class="agent-history-run-identity">
              ${roleLabel}

              <code>
                ${escapeHtml(run.session_id)}
              </code>
            </div>
          </div>

          <div class="agent-history-run-metrics">
            <div>
              <span>Tasks</span>
              <strong>
                ${run.passed_tasks} / ${run.total_tasks}
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

            <div>
              <span>Protocol</span>
              <strong>
                ${escapeHtml(run.suite_id)}
                ${escapeHtml(run.suite_version)}
              </strong>
            </div>
          </div>

          <div class="agent-history-run-actions">
            <button
              type="button"
              data-set-baseline="${escapeHtml(
                run.session_id,
              )}"
            >
              Set as baseline
            </button>

            <button
              type="button"
              data-set-candidate="${escapeHtml(
                run.session_id,
              )}"
            >
              Set as candidate
            </button>
          </div>

          <div class="agent-history-run-provenance">
            <p>
              Observer
              <strong>
                ${escapeHtml(
                  run.observer_id ?? 'n/a',
                )}
              </strong>
            </p>

            <p>
              <strong>
                Observed from ${escapeHtml(
                  run.region_code ?? 'n/a',
                )}
              </strong>
            </p>

            <p>
              ${
                run.observatory.temporal_eligible
                  ? 'Temporal eligible'
                  : 'Temporal not eligible'
              }
            </p>

            <p>
              ${
                run.observatory.geographic_eligible
                  ? 'Geographic eligible'
                  : 'Geographic not eligible'
              }
            </p>
          </div>
        </article>
      `
    })
    .join('')

  return `
    <section
      class="agent-test-history"
      data-agent-test-history="ready"
    >
      <div class="panel-heading">
        <div>
          <p class="section-label">
            Agent observations
          </p>

          <h2>Run History</h2>
        </div>

        <span class="badge">
          ${history.runs.length} saved
        </span>
      </div>

      <p class="agent-history-guidance">
        Select comparison roles explicitly when comparing observations.
        DLLO does not choose a baseline or candidate automatically.
      </p>

      <div class="agent-history-runs">
        ${runs}
      </div>

      ${
        baselineSessionId !== null
        && candidateSessionId !== null
          ? `
              <div class="agent-history-compare-actions">
                <button
                  type="button"
                  id="compare-agent-runs"
                >
                  Compare selected runs
                </button>
              </div>
            `
          : ''
      }
    </section>
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


function formatSignedDelta(
  value: number,
  suffix = '',
): string {
  const rounded =
    Math.round(value * 100) / 100

  const prefix =
    rounded > 0
      ? '+'
      : ''

  return `${prefix}${rounded}${suffix}`
}

function renderAgentComparisonError(
  error: string | null,
): string {
  if (error === null) {
    return ''
  }

  return `
    <section
      class="agent-test-comparison agent-test-comparison-rejected"
      data-agent-comparison="rejected"
    >
      <div class="panel-heading">
        <div>
          <p class="section-label">
            Comparison status
          </p>

          <h2>Comparison rejected</h2>
        </div>

        <span class="badge">
          Temporal comparison
        </span>
      </div>

      <p class="agent-comparison-guidance">
        The selected observations do not satisfy the
        requirements for this comparison.
      </p>

      <div class="agent-comparison-reason">
        <span>Reason</span>

        <strong>
          ${escapeHtml(error)}
        </strong>
      </div>
    </section>
  `
}


function renderAgentTemporalComparison(
  comparison:
    AgentTemporalComparisonResponse | null,
): string {
  if (comparison === null) {
    return ''
  }

  const changes = comparison.changes

  const passRateDelta =
    changes.pass_rate_delta === null
      ? 'n/a'
      : formatSignedDelta(
          changes.pass_rate_delta * 100,
          ' pp',
        )

  const latencyDelta =
    changes.median_latency_ms_delta === null
      ? 'n/a'
      : formatSignedDelta(
          changes.median_latency_ms_delta,
          ' ms',
        )

  const retryDelta =
    formatSignedDelta(
      changes.retry_delta,
    )

  const humanInterventionDelta =
    formatSignedDelta(
      changes.human_intervention_delta,
    )

  const taskChanges = changes.task_changes
    .filter((change) => (
      change.transition === 'fail-to-pass'
      || change.transition === 'pass-to-fail'
    ))
    .map((change) => {
      const label =
        change.transition === 'fail-to-pass'
          ? 'Fail → Pass'
          : 'Pass → Fail'

      return `
        <div class="agent-comparison-task-change">
          <code>
            ${escapeHtml(change.task_id)}
          </code>

          <strong>
            ${label}
          </strong>
        </div>
      `
    })
    .join('')

  return `
    <section
      class="agent-test-comparison"
      data-agent-comparison="temporal"
    >
      <div class="panel-heading">
        <div>
          <p class="section-label">
            Observed changes
          </p>

          <h2>Observed Changes</h2>
        </div>

        <span class="badge">
          Temporal comparison
        </span>
      </div>

      <p class="agent-comparison-guidance">
        Descriptive comparison of two explicitly
        selected observations. No cause or global
        quality judgment is inferred.
      </p>

      <div class="agent-comparison-context">
        <div>
          <span>Baseline</span>
          <code>
            ${escapeHtml(
              comparison.baseline_session_id,
            )}
          </code>
        </div>

        <div>
          <span>Candidate</span>
          <code>
            ${escapeHtml(
              comparison.candidate_session_id,
            )}
          </code>
        </div>

        <div>
          <span>Observer</span>
          <strong>
            ${escapeHtml(comparison.observer_id)}
          </strong>
        </div>

        <div>
          <span>Observation region</span>
          <strong>
            Observed from ${escapeHtml(
              comparison.region_code,
            )}
          </strong>
        </div>
      </div>

      <div class="agent-comparison-metrics">
        <div>
          <span>Tasks</span>
          <strong>${changes.total_tasks}</strong>
        </div>

        <div>
          <span>Regressions</span>
          <strong>${changes.regressions}</strong>
        </div>

        <div>
          <span>Improvements</span>
          <strong>${changes.improvements}</strong>
        </div>

        <div>
          <span>Unchanged</span>
          <strong>${changes.unchanged}</strong>
        </div>

        <div>
          <span>Pass rate Δ</span>
          <strong>${passRateDelta}</strong>
        </div>

        <div>
          <span>Median latency Δ</span>
          <strong>${latencyDelta}</strong>
        </div>

        <div>
          <span>Retries Δ</span>
          <strong>${retryDelta}</strong>
        </div>

        <div>
          <span>Human intervention Δ</span>
          <strong>
            ${humanInterventionDelta}
          </strong>
        </div>
      </div>

      ${
        taskChanges === ''
          ? ''
          : `
              <div class="agent-comparison-task-changes">
                <h3>Task outcome transitions</h3>
                ${taskChanges}
              </div>
            `
      }
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

      ${
        options.history === undefined
        || options.history === null
          ? ''
          : renderAgentTestHistory(
              options.history,
              options.baselineSessionId ?? null,
              options.candidateSessionId ?? null,
            )
      }

      ${renderAgentTemporalComparison(
        options.comparison ?? null,
      )}

      ${renderAgentComparisonError(
        options.comparisonError ?? null,
      )}

    </main>
  `
}
