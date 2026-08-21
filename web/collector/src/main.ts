import './style.css'

type CollectorState =
  | 'idle'
  | 'ready'
  | 'running'
  | 'first-output-marked'
  | 'completed'

type CollectorProbe = {
  assignmentId: string
  platform: 'chatgpt' | 'claude' | 'gemini'
  pageHostname: string
  benchmarkVersion: string
  promptId: string
  promptText: string
  scheduledAtUtc: string
  measurementMode: 'consumer-ui-manual-v0.1'
  responseCaptureEnabled: false
}

type ConsumerProbeExport = {
  export_schema_version: '0.1'
  exported_at_utc: string
  sample_count: number
  records: CompletedObservationRecord[]
}

type CompletedObservationRecord = {
  schema_version: '0.1'
  probe_id: string

  prompt_id: string
  benchmark_version: string

  scheduled_at_utc: string
  schedule_offset_ms: number

  platform: CollectorProbe['platform']
  page_hostname: string

  started_at_ms: number
  started_at_utc: string

  first_output_at_ms: number | null
  first_output_at_utc: string | null

  completed_at_ms: number
  completed_at_utc: string

  time_to_first_output_ms: number | null
  first_output_measurement_mode:
    | 'human-observed-click-v0.1'
    | null
  total_latency_ms: number

  generation_failed: false
  interrupted: false
  retry_observed: false

  response_capture_enabled: false
  response_text: null

  measurement_mode: 'consumer-ui-manual-v0.1'

  local_telemetry: null
  local_telemetry_error: null
}

type ObservationSession = {
  observationId: string
  startedAtUtc: string
  firstOutputAtUtc: string | null
  completedAtUtc: string | null
  firstOutputMeasurementMode:
    | 'human-observed-click-v0.1'
    | null
  responseCaptureEnabled: false
}

const demoProbe: CollectorProbe = {
  assignmentId: 'demo-reasoning-001',
  platform: 'chatgpt',
  pageHostname: 'chatgpt.com',
  benchmarkVersion: '0.1',
  promptId: 'reasoning-001',
  promptText:
    'A farmer has 17 sheep. All but 9 run away. How many sheep remain?',
  scheduledAtUtc: '2026-08-21T12:00:00Z',
  measurementMode: 'consumer-ui-manual-v0.1',
  responseCaptureEnabled: false,
}

let state: CollectorState = 'idle'
let currentProbe: CollectorProbe | null = null
let observationSession: ObservationSession | null = null
let completedRecord: CompletedObservationRecord | null = null

function getAppRoot(): HTMLDivElement {
  const element =
    document.querySelector<HTMLDivElement>('#app')

  if (element === null) {
    throw new Error('Collector root element not found.')
  }

  return element
}

const app = getAppRoot()

function elapsedMs(
  startUtc: string,
  endUtc: string | null,
): number | null {
  if (endUtc === null) {
    return null
  }

  return (
    new Date(endUtc).getTime()
    - new Date(startUtc).getTime()
  )
}

function buildCompletedRecord(
  probe: CollectorProbe,
  session: ObservationSession,
): CompletedObservationRecord {
  if (session.completedAtUtc === null) {
    throw new Error(
      'Cannot build a completed record before completion.',
    )
  }

  const startedAtMs =
    new Date(session.startedAtUtc).getTime()

  const completedAtMs =
    new Date(session.completedAtUtc).getTime()

  const firstOutputAtMs =
    session.firstOutputAtUtc === null
      ? null
      : new Date(session.firstOutputAtUtc).getTime()

  const scheduledAtMs =
    new Date(probe.scheduledAtUtc).getTime()

  return {
    schema_version: '0.1',
    probe_id: session.observationId,

    prompt_id: probe.promptId,
    benchmark_version: probe.benchmarkVersion,

    scheduled_at_utc: probe.scheduledAtUtc,
    schedule_offset_ms:
      startedAtMs - scheduledAtMs,

    platform: probe.platform,
    page_hostname: probe.pageHostname,

    started_at_ms: startedAtMs,
    started_at_utc: session.startedAtUtc,

    first_output_at_ms: firstOutputAtMs,
    first_output_at_utc: session.firstOutputAtUtc,

    completed_at_ms: completedAtMs,
    completed_at_utc: session.completedAtUtc,

    time_to_first_output_ms:
      firstOutputAtMs === null
        ? null
        : firstOutputAtMs - startedAtMs,

    first_output_measurement_mode:
      session.firstOutputMeasurementMode,

    total_latency_ms:
      completedAtMs - startedAtMs,

    generation_failed: false,
    interrupted: false,
    retry_observed: false,

    response_capture_enabled: false,
    response_text: null,

    measurement_mode: probe.measurementMode,

    local_telemetry: null,
    local_telemetry_error: null,
  }
}

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
          When a scheduled observation is available, its benchmark,
          prompt, platform, and timing window will appear here.
        </p>

        <button type="button" id="check-probe">
          Load demo probe
        </button>
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
        Download local JSON
      </button>

      <button
        type="button"
        id="clear-probe"
        class="secondary-button"
      >
        Clear completed probe
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
  app.innerHTML = `
    <main class="shell">
      <header class="topbar">
        <div>
          <p class="eyebrow">Distributed LLM Observatory</p>
          <h1>Collector</h1>
        </div>

        <div class="status">
          <span class="status-dot" aria-hidden="true"></span>
          Local session
        </div>
      </header>

      <section class="hero">
        <p class="hero-label">Consumer observation interface</p>

        <h2>
          Measure what you observe.
          <span>Do not infer what you cannot see.</span>
        </h2>

        <p class="hero-copy">
          DLLO Collector guides human-in-the-loop observations of
          consumer LLM interfaces while keeping measurement provenance
          explicit and avoiding response-content collection.
        </p>
      </section>

      <section class="grid">
        <article class="panel primary-panel">
          ${renderCurrentProbe()}
        </article>

        <aside class="panel">
          <p class="section-label">Measurement boundaries</p>
          <h3>Privacy by design</h3>

          <ul class="boundary-list">
            <li>
              <strong>No response scraping</strong>
              <span>Generated text is not collected.</span>
            </li>

            <li>
              <strong>No account credentials</strong>
              <span>
                Passwords, cookies, and session tokens are excluded.
              </span>
            </li>

            <li>
              <strong>Human-observed timing</strong>
              <span>
                Consumer first-output timing is explicitly identified
                as a manual observation.
              </span>
            </li>

            <li>
              <strong>Measurement provenance</strong>
              <span>
                Collection methods remain identifiable in exported data.
              </span>
            </li>
          </ul>
        </aside>
      </section>

      <section class="principles">
        <article>
          <span>01</span>
          <h3>Observe</h3>
          <p>
            Record measurable events without assigning unsupported causes.
          </p>
        </article>

        <article>
          <span>02</span>
          <h3>Preserve provenance</h3>
          <p>
            Keep methodology, platform, benchmark, region, and time explicit.
          </p>
        </article>

        <article>
          <span>03</span>
          <h3>Compare carefully</h3>
          <p>
            Only combine measurements whose semantics are compatible.
          </p>
        </article>
      </section>

      <footer>
        <span>DLLO Collector · experimental</span>
        <span>No data leaves this page in the current build.</span>
      </footer>
    </main>
  `

  bindEvents()
}

function downloadCompletedRecord(): void {
  if (completedRecord === null) {
    return
  }

  const exportPayload: ConsumerProbeExport = {
    export_schema_version: '0.1',
    exported_at_utc: new Date().toISOString(),
    sample_count: 1,
    records: [completedRecord],
  }

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
    `dllo-consumer-probe-${completedRecord.probe_id}.json`

  document.body.appendChild(link)
  link.click()
  link.remove()

  URL.revokeObjectURL(url)
}

function bindEvents(): void {
  document
    .querySelector<HTMLButtonElement>('#check-probe')
    ?.addEventListener('click', () => {
      currentProbe = demoProbe
      observationSession = null
      completedRecord = null
      state = 'ready'
      render()
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
      )

      state = 'completed'
      render()
    })
}

render()
