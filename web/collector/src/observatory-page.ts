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
              <dd>${run.started_at_utc}</dd>
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
                ${run.median_latency_ms} ms
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

      <h2>Recent observations</h2>

      <div class="observatory-observation-list">
        ${cards}
      </div>
    </section>
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
      <section class="hero">
        <p class="hero-label">
          Distributed LLM Observatory
        </p>

        <h1>Observatory</h1>

        <p class="hero-copy">
          Explore reproducible observations of models,
          agents, and AI systems across time and
          observed regions.
        </p>
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
          <strong>${observations}</strong>
          <span>observations</span>
        </div>

        <div>
          <strong>${targets}</strong>
          <span>targets</span>
        </div>

        <div>
          <strong>${regions}</strong>
          <span>observed regions</span>
        </div>
      </section>

      <section class="observatory-comparability">
        <article>
          <p class="section-label">
            Comparable observations
          </p>

          <h2>Temporal</h2>

          ${renderTemporalSummary(
            options.temporalPairs,
          )}
        </article>

        <article>
          <p class="section-label">
            Comparable observations
          </p>

          <h2>Geographic</h2>

          ${renderGeographicSummary(options)}
        </article>
      </section>

      ${renderRecentObservations(
        options.history,
      )}
    </main>
  `
}
