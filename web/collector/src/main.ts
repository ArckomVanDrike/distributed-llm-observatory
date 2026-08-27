import './style.css'

import {
  renderAppView,
} from './app-view'

import {
  executeAgentTest,
} from './agent-test-flow'

import {
  fetchAgentTestHistory,
} from './agent-test-history'

import type {
  AgentTestHistoryResponse,
} from './agent-test-history'

import type {
  AgentTestBridgeResponse,
} from './agent-test-bridge'

import type {
  AgentTestPageState,
} from './agent-test-page'

import {
  resolveAppRoute,
} from './navigation'

import {
  fetchBridgeAssignment,
} from './bridge'

import {
  parseCollectorMode,
} from './config'

import {
  PUBLIC_PROMPT_BANK,
} from './generated/public-prompt-bank'

import {
  buildPublicAssignment,
} from './public-assignment'

import {
  clearObservationHistory,
  loadObservationHistory,
  saveObservationHistory,
} from './history-storage'

import {
  appendObservationRecord,
  buildCompletedRecord,
  buildConsumerProbeExport,
  createObservationHistory,
  elapsedMs,
} from './domain'
import type {
  CollectorProbe,
  CompletedObservationRecord,
  ConsumerProbeExport,
  ObservationHistory,
  ObservationOutcomes,
  ObservationSession,
} from './domain'

const collectorMode = parseCollectorMode(
  import.meta.env.VITE_COLLECTOR_MODE,
)

type CollectorState =
  | 'idle'
  | 'ready'
  | 'running'
  | 'first-output-marked'
  | 'completed'

let state: CollectorState = 'idle'

let agentTestState: AgentTestPageState =
  'disconnected'

let agentBaseUrl =
  'http://127.0.0.1:8000'

let agentTestResult:
  AgentTestBridgeResponse | null = null

let agentTestError: string | null = null

let agentTestHistory:
  AgentTestHistoryResponse | null = null

let currentProbe: CollectorProbe | null = null
let observationSession: ObservationSession | null = null
let observationHistory: ObservationHistory =
  loadObservationHistory(window.localStorage)
let observationOutcomes: ObservationOutcomes = {
  generationFailed: false,
  interrupted: false,
  retryObserved: false,
}
let completedRecord: CompletedObservationRecord | null = null
let bridgeMessage =
  collectorMode === 'bridge'
    ? 'Check the local DLLO Bridge for a scheduled probe.'
    : (
        'Public mode: the local scheduler bridge is not '
        + 'available in this deployment.'
      )

function getAppRoot(): HTMLDivElement {
  const element =
    document.querySelector<HTMLDivElement>('#app')

  if (element === null) {
    throw new Error('Collector root element not found.')
  }

  return element
}

const app = getAppRoot()

function renderObservationStatus(): string {
  if (observationSession === null) {
    return `
      <div class="session-status">
        <span>Observation</span>
        <strong>Not started</strong>
      </div>
    `
  }

  const timeToFirstOutputMs = elapsedMs(
    observationSession.startedAtUtc,
    observationSession.firstOutputAtUtc,
  )

  const totalLatencyMs = elapsedMs(
    observationSession.startedAtUtc,
    observationSession.completedAtUtc,
  )

  const recordStatus =
    completedRecord === null
      ? 'not finalized'
      : 'local record ready'

  return `
    <dl class="session-details">
      <div>
        <dt>Observation ID</dt>
        <dd>${observationSession.observationId}</dd>
      </div>

      <div>
        <dt>State</dt>
        <dd>${state}</dd>
      </div>

      <div>
        <dt>Record</dt>
        <dd>${recordStatus}</dd>
      </div>

      <div>
        <dt>Session records</dt>
        <dd>${observationHistory.records.length}</dd>
      </div>

      <div>
        <dt>Started UTC</dt>
        <dd>${observationSession.startedAtUtc}</dd>
      </div>

      <div>
        <dt>First output UTC</dt>
        <dd>${observationSession.firstOutputAtUtc ?? 'not marked'}</dd>
      </div>

      <div>
        <dt>First-output mode</dt>
        <dd>
          ${observationSession.firstOutputMeasurementMode ?? 'n/a'}
        </dd>
      </div>

      <div>
        <dt>Completed UTC</dt>
        <dd>${observationSession.completedAtUtc ?? 'not completed'}</dd>
      </div>

      <div>
        <dt>Time to first output</dt>
        <dd>
          ${timeToFirstOutputMs === null
            ? 'n/a'
            : `${timeToFirstOutputMs} ms`}
        </dd>
      </div>

      <div>
        <dt>Total latency</dt>
        <dd>
          ${totalLatencyMs === null
            ? 'n/a'
            : `${totalLatencyMs} ms`}
        </dd>
      </div>
    </dl>
  `
}

function renderOutcomeControls(): string {
  if (
    state !== 'running'
    && state !== 'first-output-marked'
  ) {
    return ''
  }

  return `
    <fieldset class="outcome-controls">
      <legend>Human-observed outcomes</legend>

      <label>
        <input
          type="checkbox"
          id="outcome-generation-failed"
          ${observationOutcomes.generationFailed
            ? 'checked'
            : ''}
        />
        Generation failed
      </label>

      <label>
        <input
          type="checkbox"
          id="outcome-interrupted"
          ${observationOutcomes.interrupted
            ? 'checked'
            : ''}
        />
        Interrupted
      </label>

      <label>
        <input
          type="checkbox"
          id="outcome-retry-observed"
          ${observationOutcomes.retryObserved
            ? 'checked'
            : ''}
        />
        Retry observed
      </label>

      <p>
        Manual observation only. No response content is inspected.
      </p>
    </fieldset>
  `
}

function renderCurrentProbe(): string {
  if (state === 'idle' || currentProbe === null) {
    return `
      <div class="panel-heading">
        <div>
          <p class="section-label">Current probe</p>
          <h3>No probe assigned</h3>
        </div>

        <span class="badge">idle</span>
      </div>

      <div class="empty-state">
        <p>
          ${bridgeMessage}
        </p>

        <p>
          Session records:
          <strong>${observationHistory.records.length}</strong>
        </p>

        ${
          collectorMode === 'bridge'
            ? `
              <button type="button" id="check-probe">
                Check scheduled probe
              </button>
            `
            : `
              <label>
                Platform
                <select id="public-platform">
                  <option value="chatgpt">ChatGPT</option>
                  <option value="claude">Claude</option>
                  <option value="gemini">Gemini</option>
                </select>
              </label>

              <label>
                Prompt
                <select id="public-prompt">
                  ${PUBLIC_PROMPT_BANK.map(
                    (prompt) => `
                      <option value="${prompt.promptId}">
                        ${prompt.promptId} — ${prompt.category}
                      </option>
                    `,
                  ).join('')}
                </select>
              </label>

              <button type="button" id="load-public-probe">
                Load public probe
              </button>

              <p>
                Manual selection only. No provider request is sent
                by the Collector.
              </p>
            `
        }

        ${
          observationHistory.records.length > 0
            ? `
              <button
                type="button"
                id="download-record"
                class="secondary-button"
              >
                Download session JSON
                (${observationHistory.records.length} records)
              </button>

              <button
                type="button"
                id="reset-session-history"
                class="secondary-button"
              >
                Reset local session
              </button>
            `
            : ''
        }
      </div>
    `
  }

  const controls = (() => {
    if (state === 'ready') {
      return `
        <button type="button" id="copy-prompt">
          Copy prompt
        </button>

        <button type="button" id="start-observation">
          Start observation
        </button>

        <button
          type="button"
          id="clear-probe"
          class="secondary-button"
        >
          Clear
        </button>
      `
    }

    if (state === 'running') {
      return `
        <button type="button" id="copy-prompt">
          Copy prompt
        </button>

        <button type="button" id="mark-first-output">
          Mark First Output (Human)
        </button>

        <button
          type="button"
          id="complete-observation"
          class="secondary-button"
        >
          Complete without First Output
        </button>
      `
    }

    if (state === 'first-output-marked') {
      return `
        <button type="button" id="complete-observation">
          Complete observation
        </button>
      `
    }

    return `
      <button type="button" id="download-record">
        Download session JSON
        (${observationHistory.records.length} records)
      </button>

      <button
        type="button"
        id="clear-probe"
        class="secondary-button"
      >
        Clear completed probe
      </button>

      <button
        type="button"
        id="reset-session-history"
        class="secondary-button"
      >
        Reset local session
      </button>
    `
  })()

  return `
    <div class="panel-heading">
      <div>
        <p class="section-label">Current probe</p>
        <h3>${currentProbe.promptId}</h3>
      </div>

      <span class="badge">${state}</span>
    </div>

    <dl class="probe-meta">
      <div>
        <dt>Platform</dt>
        <dd>${currentProbe.platform}</dd>
      </div>

      <div>
        <dt>Benchmark</dt>
        <dd>${currentProbe.benchmarkVersion}</dd>
      </div>

      <div>
        <dt>Scheduled UTC</dt>
        <dd>${currentProbe.scheduledAtUtc}</dd>
      </div>

      <div>
        <dt>Measurement mode</dt>
        <dd>${currentProbe.measurementMode}</dd>
      </div>
    </dl>

    <div class="prompt-card">
      <p class="section-label">Prompt</p>
      <p class="prompt-text">${currentProbe.promptText}</p>
    </div>

    ${renderOutcomeControls()}

    <div class="probe-actions">
      ${controls}
    </div>

    ${renderObservationStatus()}

    <p class="privacy-note">
      Response capture: disabled
    </p>
  `
}

function render(): void {
  const route = resolveAppRoute(
    window.location.hash,
  )

  app.innerHTML = renderAppView(
    route,
    renderCurrentProbe(),
    {
      agentTest: {
        state: agentTestState,
        baseUrl: agentBaseUrl,
        result: agentTestResult,
        error: agentTestError,
        history: agentTestHistory,
      },
    },
  )

  if (route === 'consumer-probe') {
    bindEvents()
  }

  if (route === 'agent-lab-test') {
    bindAgentTestEvents()
  }
}

function downloadCompletedRecord(): void {
  if (observationHistory.records.length === 0) {
    return
  }

  const exportPayload: ConsumerProbeExport =
    buildConsumerProbeExport(
      observationHistory,
      new Date().toISOString(),
    )

  const blob = new Blob(
    [
      JSON.stringify(
        exportPayload,
        null,
        2,
      ),
    ],
    {
      type: 'application/json',
    },
  )

  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download =
    `dllo-consumer-probes-session-${exportPayload.sample_count}.json`

  document.body.appendChild(link)
  link.click()
  link.remove()

  URL.revokeObjectURL(url)
}

async function refreshAgentTestHistory(): Promise<void> {
  try {
    agentTestHistory = await fetchAgentTestHistory(
      (
        request,
        init,
      ) => fetch(request, init),
    )
  } catch {
    agentTestHistory = null
  }

  render()
}


function bindAgentTestEvents(): void {
  const button =
    document.querySelector<HTMLButtonElement>(
      '#run-agent-test',
    )

  const input =
    document.querySelector<HTMLInputElement>(
      '#agent-base-url',
    )

  if (
    button === null
    || input === null
  ) {
    return
  }

  button.addEventListener(
    'click',
    async () => {
      agentBaseUrl = input.value.trim()

      agentTestResult = null
      agentTestError = null

      try {
        const result = await executeAgentTest({
          baseUrl: agentBaseUrl,
          fetchImpl: (
            request,
            init,
          ) => fetch(request, init),
          onStateChange(nextState) {
            agentTestState = nextState

            if (nextState === 'running') {
              render()
            }
          },
        })

        agentTestResult = result
        render()

        await refreshAgentTestHistory()
      } catch (error) {
        agentTestError =
          error instanceof Error
            ? error.message
            : 'Agent test failed.'

        render()
      }
    },
  )
}


function bindEvents(): void {
  document
    .querySelector<HTMLButtonElement>('#check-probe')
    ?.addEventListener('click', async () => {
      bridgeMessage =
        'Checking the local DLLO Bridge...'
      render()

      try {
        const assignment =
          await fetchBridgeAssignment(
            (input) => fetch(input),
          )

        observationSession = null
        completedRecord = null

        if (assignment === null) {
          currentProbe = null
          state = 'idle'
          bridgeMessage =
            'No scheduled probe is currently available.'
          render()
          return
        }

        if (assignment.status === 'upcoming') {
          currentProbe = null
          state = 'idle'
          bridgeMessage =
            'The next scheduled probe is upcoming and is not actionable yet.'
          render()
          return
        }

        currentProbe = assignment.probe
        state = 'ready'
        bridgeMessage =
          'Scheduled probe loaded from the local DLLO Bridge.'
        render()
      } catch (error) {
        currentProbe = null
        observationSession = null
        completedRecord = null
        state = 'idle'

        bridgeMessage =
          error instanceof Error
            ? error.message
            : 'Unable to reach the local DLLO Bridge.'

        render()
      }
    })

  document
    .querySelector<HTMLButtonElement>('#load-public-probe')
    ?.addEventListener('click', () => {
      const platformElement =
        document.querySelector<HTMLSelectElement>(
          '#public-platform',
        )

      const promptElement =
        document.querySelector<HTMLSelectElement>(
          '#public-prompt',
        )

      if (
        platformElement === null
        || promptElement === null
      ) {
        return
      }

      const platform = platformElement.value

      if (
        platform !== 'chatgpt'
        && platform !== 'claude'
        && platform !== 'gemini'
      ) {
        bridgeMessage =
          'Unsupported public Collector platform.'
        render()
        return
      }

      const assignment = buildPublicAssignment(
        promptElement.value,
        platform,
      )

      if (assignment === null) {
        bridgeMessage =
          'Selected public prompt is not available.'
        render()
        return
      }

      currentProbe = assignment
      observationSession = null
      completedRecord = null
      state = 'ready'
      bridgeMessage =
        'Public probe loaded locally. Send the prompt manually.'
      render()
    })

  document
    .querySelector<HTMLInputElement>(
      '#outcome-generation-failed',
    )
    ?.addEventListener('change', (event) => {
      const input = event.currentTarget

      if (!(input instanceof HTMLInputElement)) {
        return
      }

      observationOutcomes = {
        ...observationOutcomes,
        generationFailed: input.checked,
      }
    })

  document
    .querySelector<HTMLInputElement>(
      '#outcome-interrupted',
    )
    ?.addEventListener('change', (event) => {
      const input = event.currentTarget

      if (!(input instanceof HTMLInputElement)) {
        return
      }

      observationOutcomes = {
        ...observationOutcomes,
        interrupted: input.checked,
      }
    })

  document
    .querySelector<HTMLInputElement>(
      '#outcome-retry-observed',
    )
    ?.addEventListener('change', (event) => {
      const input = event.currentTarget

      if (!(input instanceof HTMLInputElement)) {
        return
      }

      observationOutcomes = {
        ...observationOutcomes,
        retryObserved: input.checked,
      }
    })

  document
    .querySelector<HTMLButtonElement>('#download-record')
    ?.addEventListener('click', () => {
      downloadCompletedRecord()
    })

  document
    .querySelector<HTMLButtonElement>('#clear-probe')
    ?.addEventListener('click', () => {
      currentProbe = null
      observationSession = null
      completedRecord = null
      state = 'idle'
      render()
    })

  document
    .querySelector<HTMLButtonElement>('#reset-session-history')
    ?.addEventListener('click', () => {
      const confirmed = window.confirm(
        'Delete all locally persisted DLLO session records?',
      )

      if (!confirmed) {
        return
      }

      clearObservationHistory(window.localStorage)
      observationHistory = createObservationHistory()
      currentProbe = null
      observationSession = null
      completedRecord = null
      state = 'idle'
      render()
    })

  document
    .querySelector<HTMLButtonElement>('#copy-prompt')
    ?.addEventListener('click', async () => {
      if (currentProbe === null) {
        return
      }

      await navigator.clipboard.writeText(
        currentProbe.promptText,
      )
    })

  document
    .querySelector<HTMLButtonElement>('#start-observation')
    ?.addEventListener('click', () => {
      observationOutcomes = {
        generationFailed: false,
        interrupted: false,
        retryObserved: false,
      }

      observationSession = {
        observationId: crypto.randomUUID(),
        startedAtUtc: new Date().toISOString(),
        firstOutputAtUtc: null,
        completedAtUtc: null,
        firstOutputMeasurementMode: null,
        responseCaptureEnabled: false,
      }

      state = 'running'
      render()
    })

  document
    .querySelector<HTMLButtonElement>('#mark-first-output')
    ?.addEventListener('click', () => {
      if (observationSession === null) {
        return
      }

      observationSession = {
        ...observationSession,
        firstOutputAtUtc: new Date().toISOString(),
        firstOutputMeasurementMode:
          'human-observed-click-v0.1',
      }

      state = 'first-output-marked'
      render()
    })

  document
    .querySelector<HTMLButtonElement>('#complete-observation')
    ?.addEventListener('click', () => {
      if (observationSession === null) {
        return
      }

      observationSession = {
        ...observationSession,
        completedAtUtc: new Date().toISOString(),
      }

      if (currentProbe === null) {
        return
      }

      completedRecord = buildCompletedRecord(
        currentProbe,
        observationSession,
        observationOutcomes,
      )

      observationHistory = appendObservationRecord(
        observationHistory,
        completedRecord,
      )

      saveObservationHistory(
        window.localStorage,
        observationHistory,
      )

      state = 'completed'
      render()
    })
}


function handleRouteChange(): void {
  render()

  if (
    resolveAppRoute(window.location.hash)
    === 'agent-lab-test'
  ) {
    void refreshAgentTestHistory()
  }
}

window.addEventListener(
  'hashchange',
  handleRouteChange,
)

handleRouteChange()
