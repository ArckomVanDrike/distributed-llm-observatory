import type {
  AppRoute,
} from './navigation'

function routeAttributes(
  route: AppRoute,
  activeRoute: AppRoute,
): string {
  if (route === activeRoute) {
    return (
      `data-route="${route}" `
      + 'aria-current="page"'
    )
  }

  return `data-route="${route}"`
}

function isAgentLabRoute(
  route: AppRoute,
): boolean {
  return (
    route === 'agent-lab'
    || route === 'agent-lab-test'
    || route === 'agent-lab-starter'
  )
}


export function renderAppShell(
  activeRoute: AppRoute,
  content: string,
): string {
  return `
    <div class="dllo-app-shell">
      <header class="dllo-app-header">
        <a
          class="dllo-brand"
          href="#/observatory"
        >
          <span>DLLO</span>
          <small>Distributed LLM Observatory</small>
        </a>

        <nav
          class="dllo-primary-nav"
          aria-label="Primary navigation"
        >
          <a
            href="#/observatory"
            ${routeAttributes(
              'observatory',
              activeRoute,
            )}
          >
            Observatory
          </a>

          <a
            href="#/consumer-probe"
            ${routeAttributes(
              'consumer-probe',
              activeRoute,
            )}
          >
            Consumer Probe
          </a>

          <a
            href="#/agent-lab"
            ${routeAttributes(
              'agent-lab',
              activeRoute,
            )}
          >
            Agent Lab
          </a>
        </nav>
      </header>

      ${
        isAgentLabRoute(activeRoute)
          ? `
            <nav
              class="dllo-agent-nav"
              aria-label="Agent Lab navigation"
            >
              <a
                href="#/agent-lab/test"
                ${routeAttributes(
                  'agent-lab-test',
                  activeRoute,
                )}
              >
                Test Your Agent
              </a>

              <a
                href="#/agent-lab/starter"
                ${routeAttributes(
                  'agent-lab-starter',
                  activeRoute,
                )}
              >
                Agent Starter
              </a>
            </nav>
          `
          : ''
      }

      <div class="dllo-page">
        ${content}
      </div>
    </div>
  `
}
