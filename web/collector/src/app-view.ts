import {
  renderAgentLabPage,
} from './agent-lab-page'

import {
  renderAgentStarterPage,
} from './agent-starter-page'

import type {
  AgentStarterPageOptions,
} from './agent-starter-page'

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
  agentStarter?: AgentStarterPageOptions
  observatory?: ObservatoryPageOptions
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
      renderAgentStarterPage(
        options.agentStarter,
      ),
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
