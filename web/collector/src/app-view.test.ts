import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  renderAppView,
} from './app-view'

describe('renderAppView', () => {
  it('renders the Consumer Probe route', () => {
    const html = renderAppView(
      'consumer-probe',
      '<div id="probe">probe</div>',
    )

    expect(html).toContain('Collector')
    expect(html).toContain(
      '<div id="probe">probe</div>',
    )
  })

  it('renders the Agent Lab route inside the DLLO shell', () => {
    const html = renderAppView(
      'agent-lab',
      '',
    )

    expect(html).toContain('Agent Lab')
    expect(html).toContain('Test Your Agent')
    expect(html).toContain(
      'data-route="agent-lab" aria-current="page"',
    )
  })

  it('renders Test Your Agent inside the DLLO shell', () => {
    const html = renderAppView(
      'agent-lab-test',
      '',
    )

    expect(html).toContain('Test Your Agent')
    expect(html).toContain(
      'http://127.0.0.1:8000',
    )
    expect(html).toContain(
      'data-route="agent-lab-test" aria-current="page"',
    )
  })

  it('renders the Observatory landing route', () => {
    const html = renderAppView(
      'observatory',
      '',
    )

    expect(html).toContain('Observatory')
    expect(html).toContain(
      'Distributed LLM Observatory',
    )
  })

  it('renders Agent Starter as in development', () => {
    const html = renderAppView(
      'agent-lab-starter',
      '',
    )

    expect(html).toContain('Agent Starter')
    expect(html).toContain('In development')
  })
})
