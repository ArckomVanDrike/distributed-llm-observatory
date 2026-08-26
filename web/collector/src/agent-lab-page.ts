const agentLabVisualUrl = new URL(
  '../../assets/visuals/agent-lab.webp',
  import.meta.url,
).href

export function renderAgentLabPage(): string {
  return `
    <main class="agent-lab-page">
      <section class="agent-lab-hero">
        <div class="agent-lab-hero-copy">
          <p class="hero-label">Agent Lab</p>

          <h1>
            Test, understand,
            and compare AI agents.
          </h1>

          <p>
            Connect an agent to DLLO, evaluate its behavior
            with a stable protocol, and collect
            observer-owned evidence for reproducible analysis.
          </p>
        </div>

        <div class="agent-lab-hero-visual">
          <img
            src="${agentLabVisualUrl}"
            alt="DLLO Agent Lab"
          />
        </div>
      </section>

      <section
        class="agent-lab-workflows"
        aria-label="Agent Lab workflows"
      >
        <article class="agent-lab-workflow-card">
          <div>
            <p class="section-label">
              Available now
            </p>

            <h2>Test Your Agent</h2>

            <p>
              Connect your agent through the Local SUT
              Protocol and evaluate it with
              Agent Protocol Core 1.0.
            </p>

            <ul>
              <li>Compatibility-aware execution</li>
              <li>Observer-owned evidence</li>
              <li>Technical report</li>
              <li>Comparable run history</li>
            </ul>
          </div>

          <a
            class="primary-action"
            href="#/agent-lab/test"
          >
            Test your agent
          </a>
        </article>

        <article class="agent-lab-workflow-card">
          <div>
            <p class="section-label">
              In development
            </p>

            <h2>Agent Starter</h2>

            <p>
              Profile the capabilities of your device
              and understand what kind of local agent
              stack it can reasonably support.
            </p>

            <ul>
              <li>Hardware and capability profiling</li>
              <li>Desktop and mobile-aware guidance</li>
              <li>Agent stack recommendations</li>
            </ul>
          </div>

          <a
            class="secondary-action"
            href="#/agent-lab/starter"
          >
            Explore Agent Starter
          </a>
        </article>
      </section>
    </main>
  `
}
