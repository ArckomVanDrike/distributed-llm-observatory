import {
  renderAgentLabPage,
} from './agent-lab-page'

import {
  renderAgentTestPage,
} from './agent-test-page'

import type {
  AgentTestPageOptions,
} from './agent-test-page'

import {
  renderAppShell,
} from './app-shell'

import {
  renderCollectorPage,
} from './collector-page'

import {
  renderObservatoryPage,
} from './observatory-page'

import type {
  ObservatoryPageOptions,
} from './observatory-page'

import type {
  AppRoute,
} from './navigation'

export interface AppViewOptions {
  agentTest?: AgentTestPageOptions
  observatory?: ObservatoryPageOptions
}

function renderAgentStarterPage(): string {
  return `
    <main class="agent-starter-page">
      <section class="hero">
        <p class="hero-label">Agent Lab</p>

        <h1>Agent Starter</h1>

        <p class="section-label">
          Core v1 complete
        </p>

        <p class="hero-copy">
          Turn goals, constraints, observed environment
          evidence, and explicit preferences into
          reproducible agent architecture and
          stack recommendations.
        </p>

        <p>
          Public interface in development.
        </p>

        <ul>
          <li>Coding</li>
          <li>Knowledge / RAG</li>
          <li>Automation</li>
          <li>Voice</li>
          <li>Personal Assistant</li>
        </ul>
      </section>
    </main>
  `
}

export function renderAppView(
  route: AppRoute,
  currentProbeHtml: string,
  options: AppViewOptions = {},
): string {
  if (route === 'consumer-probe') {
    return renderCollectorPage(
      currentProbeHtml,
    )
  }

  if (route === 'agent-lab') {
    return renderAppShell(
      route,
      renderAgentLabPage(),
    )
  }

  if (route === 'agent-lab-test') {
    return renderAppShell(
      route,
      renderAgentTestPage(
        options.agentTest ?? {
          state: 'disconnected',
          baseUrl: 'http://127.0.0.1:8000',
        },
      ),
    )
  }

  if (route === 'agent-lab-starter') {
    return renderAppShell(
      route,
      renderAgentStarterPage(),
    )
  }

  return renderAppShell(
    route,
    renderObservatoryPage(
      options.observatory ?? {
        state: 'loading',
        history: null,
        temporalPairs: null,
        geographicPairs: null,
        geographicMaxSkewInput: '',
        error: null,
      },
    ),
  )
}
