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
    </main>
  `
}
