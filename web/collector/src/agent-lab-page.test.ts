import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  renderAgentLabPage,
} from './agent-lab-page'

describe('renderAgentLabPage', () => {
  it('presents the two Agent Lab workflows', () => {
    const html = renderAgentLabPage()

    expect(html).toContain('Agent Lab')
    expect(html).toContain('Test Your Agent')
    expect(html).toContain('Agent Starter')

    expect(html).toContain(
      'href="#/agent-lab/test"',
    )
    expect(html).toContain(
      'href="#/agent-lab/starter"',
    )
  })

  it('uses the Agent Lab visual', () => {
    const html = renderAgentLabPage()

    expect(html).toContain('agent-lab.webp')
    expect(html).toContain(
      'alt="DLLO Agent Lab"',
    )
  })

  it('describes Test Your Agent without self-certification', () => {
    const html = renderAgentLabPage()

    expect(html).toContain(
      'observer-owned evidence',
    )
    expect(html).toContain(
      'Agent Protocol Core 1.0',
    )
  })

  it('distinguishes the complete Agent Starter core from its public interface', () => {
    const html = renderAgentLabPage()

    expect(html).toContain(
      'Agent Starter',
    )
    expect(html).toContain(
      'Core v1 complete',
    )
    expect(html).toContain(
      'Public interface in development',
    )
    expect(html).toContain(
      'evidence-backed',
    )
  })
})
