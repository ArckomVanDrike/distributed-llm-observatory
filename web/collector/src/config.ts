export type CollectorMode =
  | 'bridge'
  | 'public'

export function parseCollectorMode(
  value: string | undefined,
): CollectorMode {
  if (value === undefined || value === '') {
    return 'bridge'
  }

  if (value === 'bridge' || value === 'public') {
    return value
  }

  throw new Error(
    `Invalid DLLO Collector mode: ${value}`,
  )
}
