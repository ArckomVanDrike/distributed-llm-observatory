import type {
  AgentTestHistoryResponse,
} from './agent-test-history'

import type {
  GeographicObservationPairsResponse,
  TemporalObservationPairsResponse,
} from './observatory-pairs'

export type ObservatoryPageState =
  | 'loading'
  | 'ready'
  | 'error'

export type ObservatoryPageOptions = {
  state: ObservatoryPageState
  history: AgentTestHistoryResponse | null
  temporalPairs:
    TemporalObservationPairsResponse | null
  geographicPairs:
    GeographicObservationPairsResponse | null
  geographicMaxSkewInput: string
  error: string | null
}

type ObservatoryIconName =
  | 'observations'
  | 'targets'
  | 'regions'
  | 'temporal'
  | 'geographic'
  | 'history'

const observatoryIconFiles:
  Record<ObservatoryIconName, string> = {
    observations: 'observations.svg',
    targets: 'targets.svg',
    regions: 'observed-regions.svg',
    temporal: 'temporal.svg',
    geographic: 'geographic.svg',
    history: 'history.svg',
  }

function renderObservatoryIcon(
  name: ObservatoryIconName,
): string {
  return `
    <img
      class="observatory-icon"
      data-observatory-icon="${name}"
      src="/observatory-icons/${
        observatoryIconFiles[name]
      }"
      alt=""
      aria-hidden="true"
    />
  `
}


function countDistinctTargets(
  history: AgentTestHistoryResponse | null,
): number {
  if (history === null) {
    return 0
  }

  return new Set(
    history.runs.map(
      (run) => run.target_id,
    ),
  ).size
}

function countDistinctRegions(
  history: AgentTestHistoryResponse | null,
): number {
  if (history === null) {
    return 0
  }

  return new Set(
    history.runs
      .map(
        (run) => run.region_code,
      )
      .filter(
        (region): region is string =>
          region !== null,
      ),
  ).size
}

function renderTemporalSummary(
  temporalPairs:
    TemporalObservationPairsResponse | null,
): string {
  if (temporalPairs === null) {
    return `
      <p>
        Temporal observation pairs are not loaded.
      </p>
    `
  }

  const total = temporalPairs.pairs.length

  const comparable =
    temporalPairs.pairs.filter(
      (pair) => pair.comparable,
    ).length

  const rejected = total - comparable

  return `
    <div class="observatory-pair-summary">
      <p><strong>${total}</strong> pairs</p>
      <p><strong>${comparable}</strong> comparable</p>
      <p><strong>${rejected}</strong> rejected</p>
    </div>
  `
}

function renderGeographicSummary(
  options: ObservatoryPageOptions,
): string {
  if (options.geographicPairs === null) {
    return `
      <p>
        Maximum observation skew required
      </p>

      <label>
        Maximum observation skew
        <input
          id="observatory-geographic-max-skew"
          type="number"
          min="0"
          step="any"
          value="${options.geographicMaxSkewInput}"
        />
        seconds
      </label>

      <button
        type="button"
        id="discover-geographic-pairs"
      >
        Discover pairs
      </button>
    `
  }

  const total =
    options.geographicPairs.pairs.length

  const comparable =
    options.geographicPairs.pairs.filter(
      (pair) => pair.comparable,
    ).length

  const rejected = total - comparable

  return `
    <p>
      Maximum observation skew:
      <strong>
        ${options
          .geographicPairs
          .max_observation_skew_seconds}
        seconds
      </strong>
    </p>

    <div class="observatory-pair-summary">
      <p><strong>${total}</strong> pairs</p>
      <p><strong>${comparable}</strong> comparable</p>
      <p><strong>${rejected}</strong> rejected</p>
    </div>
  `
}

function formatObservationTimestamp(
  value: string,
): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  const months = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ]

  const day = String(
    date.getUTCDate(),
  ).padStart(2, '0')

  const month =
    months[date.getUTCMonth()]

  const year =
    date.getUTCFullYear()

  const hours = String(
    date.getUTCHours(),
  ).padStart(2, '0')

  const minutes = String(
    date.getUTCMinutes(),
  ).padStart(2, '0')

  const seconds = String(
    date.getUTCSeconds(),
  ).padStart(2, '0')

  return `
    <span>${day} ${month} ${year}</span>
    <span>${hours}:${minutes}:${seconds} UTC</span>
  `
}


function formatLatencyMs(
  value: number | null,
): string {
  if (value === null) {
    return 'Unavailable'
  }

  return `${value.toFixed(2)} ms`
}


function renderRecentObservations(
  history: AgentTestHistoryResponse | null,
): string {
  if (
    history === null
    || history.runs.length === 0
  ) {
    return `
      <section class="observatory-recent">
        <p class="section-label">
          Observation history
        </p>

        <h2>Recent observations</h2>

        <p>
          No observations recorded yet.
        </p>
      </section>
    `
  }

  const runs = [...history.runs].sort(
    (left, right) =>
      right.started_at_utc.localeCompare(
        left.started_at_utc,
      ),
  )

  const cards = runs
    .map(
      (run) => `
        <article class="observatory-observation-card">
          <div class="observatory-observation-heading">
            <div>
              <p class="section-label">
                Target
              </p>

              <h3>${run.target_id}</h3>
            </div>

            <p class="observatory-observed-from">
              ${
                run.region_code === null
                  ? 'Observation region unavailable'
                  : `Observed from ${run.region_code}`
              }
            </p>
          </div>

          <dl class="observatory-observation-details">
            <div>
              <dt>Observed at</dt>
              <dd>
                <time datetime="${run.started_at_utc}">
                  ${formatObservationTimestamp(
                    run.started_at_utc,
                  )}
                </time>
              </dd>
            </div>

            <div>
              <dt>Tasks passed</dt>
              <dd>
                ${run.passed_tasks} / ${run.total_tasks}
              </dd>
            </div>

            <div>
              <dt>Median latency</dt>
              <dd>
                ${formatLatencyMs(
                  run.median_latency_ms,
                )}
              </dd>
            </div>
          </dl>
        </article>
      `,
    )
    .join('')

  return `
    <section class="observatory-recent">
      <p class="section-label">
        Observation history
      </p>

      <div class="observatory-section-heading">
        <h2>Recent observations</h2>

        ${renderObservatoryIcon(
          'history',
        )}
      </div>

      <div class="observatory-observation-list">
        ${cards}
      </div>
    </section>
  `
}


function renderObservatoryGlobePoints(): string {
  const points = [
    ['70%', '27%', '-0.6s', '6.3s', '1.0'],
    ['79%', '31%', '-3.1s', '7.1s', '0.85'],
    ['65%', '37%', '-4.7s', '6.8s', '0.9'],
    ['75%', '41%', '-1.9s', '7.5s', '1.1'],
    ['82%', '45%', '-5.2s', '6.6s', '0.8'],
    ['70%', '50%', '-2.8s', '7.3s', '0.95'],
  ]

  return `
    <div
      class="observatory-globe-points"
      data-observatory-globe-points
      aria-hidden="true"
    >
      ${points
        .map(
          ([
            x,
            y,
            delay,
            duration,
            scale,
          ]) => `
            <span
              style="
                --point-x: ${x};
                --point-y: ${y};
                --point-delay: ${delay};
                --point-duration: ${duration};
                --point-scale: ${scale};
              "
            ></span>
          `,
        )
        .join('')}
    </div>
  `
}


export function renderObservatoryPage(
  options: ObservatoryPageOptions,
): string {
  const observations =
    options.history?.runs.length ?? 0

  const targets =
    countDistinctTargets(options.history)

  const regions =
    countDistinctRegions(options.history)

  return `
    <main class="observatory-page">
      <section class="hero observatory-hero">
        <div class="observatory-hero-copy">
          <p class="hero-label">
            Distributed LLM Observatory
          </p>

          <h1>Observatory</h1>

          <p class="hero-copy">
            Explore reproducible observations of models,
            agents, and AI systems across time and
            observed regions.
          </p>
        </div>

        <div
          class="observatory-hero-visual"
          data-observatory-hero-visual
          aria-hidden="true"
        >
          ${renderObservatoryGlobePoints()}
        </div>
      </section>

      ${
        options.state === 'loading'
          ? `
            <section>
              <p>Loading observations...</p>
            </section>
          `
          : ''
      }

      ${
        options.error !== null
          ? `
            <section>
              <p>${options.error}</p>
            </section>
          `
          : ''
      }

      <section class="observatory-summary">
        <div>
          <div>
            <strong>${observations}</strong>
            <span>observations</span>
          </div>

          ${renderObservatoryIcon(
            'observations',
          )}
        </div>

        <div>
          <div>
            <strong>${targets}</strong>
            <span>targets</span>
          </div>

          ${renderObservatoryIcon(
            'targets',
          )}
        </div>

        <div>
          <div>
            <strong>${regions}</strong>
            <span>observed regions</span>
          </div>

          ${renderObservatoryIcon(
            'regions',
          )}
        </div>
      </section>

      <section class="observatory-comparability">
        <article>
          <p class="section-label">
            Comparable observations
          </p>

          <div class="observatory-panel-heading">
            <h2>Temporal</h2>

            ${renderObservatoryIcon(
              'temporal',
            )}
          </div>

          ${renderTemporalSummary(
            options.temporalPairs,
          )}
        </article>

        <article>
          <p class="section-label">
            Comparable observations
          </p>

          <div class="observatory-panel-heading">
            <h2>Geographic</h2>

            ${renderObservatoryIcon(
              'geographic',
            )}
          </div>

          ${renderGeographicSummary(options)}
        </article>
      </section>

      ${renderRecentObservations(
        options.history,
      )}
    </main>
  `
}
