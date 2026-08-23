import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  parseCollectorMode,
} from './config'

describe('parseCollectorMode', () => {
  it('defaults to bridge mode when unset', () => {
    expect(parseCollectorMode(undefined)).toBe('bridge')
  })

  it('accepts explicit bridge mode', () => {
    expect(parseCollectorMode('bridge')).toBe('bridge')
  })

  it('accepts explicit public mode', () => {
    expect(parseCollectorMode('public')).toBe('public')
  })

  it('rejects unsupported modes', () => {
    expect(() => {
      parseCollectorMode('production')
    }).toThrow(
      'Invalid DLLO Collector mode: production',
    )
  })
})
