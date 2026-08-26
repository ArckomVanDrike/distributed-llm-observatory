import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  renderCollectorPage,
} from './collector-page'

describe('renderCollectorPage', () => {
  it('preserves the Consumer Probe identity', () => {
    const html = renderCollectorPage(
      '<div id="current-probe">probe</div>',
    )

    expect(html).toContain('Collector')
    expect(html).toContain(
      'Consumer observation interface',
    )
    expect(html).toContain(
      'Measure what you observe.',
    )
  })

  it('renders supplied probe content', () => {
    const html = renderCollectorPage(
      '<div id="current-probe">probe</div>',
    )

    expect(html).toContain(
      '<div id="current-probe">probe</div>',
    )
  })

  it('preserves the measurement boundaries', () => {
    const html = renderCollectorPage('probe')

    expect(html).toContain('No response scraping')
    expect(html).toContain('No account credentials')
    expect(html).toContain('Human-observed timing')
    expect(html).toContain('Measurement provenance')
  })

  it('preserves the Observatory principles', () => {
    const html = renderCollectorPage('probe')

    expect(html).toContain('Observe')
    expect(html).toContain('Preserve provenance')
    expect(html).toContain('Compare carefully')
  })
})
