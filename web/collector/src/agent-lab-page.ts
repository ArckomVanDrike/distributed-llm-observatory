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
              Core v1 complete
            </p>

            <h2>Agent Starter</h2>

            <p>
              Turn goals, constraints, hardware evidence,
              and explicit preferences into evidence-backed
              agent architecture and stack recommendations.
            </p>

            <p>
              Public interface in development.
            </p>

            <ul>
              <li>Adaptive guidance across five goals</li>
              <li>Hard constraints and soft preferences</li>
              <li>Technical feasibility assessment</li>
              <li>Concrete stack recommendations</li>
              <li>Why / Why Not evidence</li>
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
