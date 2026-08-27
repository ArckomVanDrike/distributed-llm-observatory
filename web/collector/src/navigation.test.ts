import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  resolveAppRoute,
} from './navigation'

describe('resolveAppRoute', () => {
  it('resolves the Observatory route', () => {
    expect(
      resolveAppRoute('#/observatory'),
    ).toBe('observatory')
  })

  it('resolves the Consumer Probe route', () => {
    expect(
      resolveAppRoute('#/consumer-probe'),
    ).toBe('consumer-probe')
  })

  it('resolves the Agent Lab route', () => {
    expect(
      resolveAppRoute('#/agent-lab'),
    ).toBe('agent-lab')
  })

  it('resolves Test Your Agent', () => {
    expect(
      resolveAppRoute('#/agent-lab/test'),
    ).toBe('agent-lab-test')
  })

  it('resolves Agent Starter', () => {
    expect(
      resolveAppRoute('#/agent-lab/starter'),
    ).toBe('agent-lab-starter')
  })

  it('defaults unknown routes to Observatory', () => {
    expect(
      resolveAppRoute('#/something-else'),
    ).toBe('observatory')
  })

  it('defaults an empty hash to Observatory', () => {
    expect(
      resolveAppRoute(''),
    ).toBe('observatory')
  })
})
