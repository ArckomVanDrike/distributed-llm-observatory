import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  renderAppShell,
} from './app-shell'

describe('renderAppShell', () => {
  it('renders the primary DLLO navigation', () => {
    const html = renderAppShell(
      'agent-lab-test',
      '<main>content</main>',
    )

    expect(html).toContain(
      'href="#/observatory"',
    )
    expect(html).toContain(
      'href="#/consumer-probe"',
    )
    expect(html).toContain(
      'href="#/agent-lab"',
    )
    expect(html).toContain(
      'href="#/agent-lab/test"',
    )
    expect(html).toContain(
      'href="#/agent-lab/starter"',
    )
  })

  it('marks the active route', () => {
    const html = renderAppShell(
      'agent-lab-test',
      '<main>content</main>',
    )

    expect(html).toContain(
      'data-route="agent-lab-test" aria-current="page"',
    )
  })

  it('renders supplied page content', () => {
    const html = renderAppShell(
      'observatory',
      '<main id="page-content">Observatory</main>',
    )

    expect(html).toContain(
      '<main id="page-content">Observatory</main>',
    )
  })
})
