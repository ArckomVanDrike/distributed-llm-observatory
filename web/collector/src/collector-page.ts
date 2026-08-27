export function renderCollectorPage(
  currentProbeHtml: string,
): string {
  return `
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
          ${currentProbeHtml}
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
}
