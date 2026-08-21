import type { CollectorProbe } from './domain'

export type BridgeStatus =
  | 'due'
  | 'upcoming'
  | 'none'

export type BridgeProbeItem = {
  scheduled_at_utc: string
  prompt_id: string
  category: string
  prompt: string
  overdue_by_ms?: number
  starts_in_ms?: number
}

export type BridgeNextResponse = {
  schema_version: '0.1'
  status: BridgeStatus
  now_utc: string
  schedule_date: string
  observer_id: string
  platform: CollectorProbe['platform']
  benchmark_version: string
  completed_today: number
  item: BridgeProbeItem | null
}

export type CollectorAssignment = {
  status: 'due' | 'upcoming'
  category: string
  probe: CollectorProbe
}

function hostnameForPlatform(
  platform: CollectorProbe['platform'],
): string {
  if (platform === 'chatgpt') {
    return 'chatgpt.com'
  }

  if (platform === 'claude') {
    return 'claude.ai'
  }

  if (platform === 'gemini') {
    return 'gemini.google.com'
  }

  throw new Error(
    'Unsupported Collector platform.',
  )
}

function isRecord(
  value: unknown,
): value is Record<string, unknown> {
  return (
    typeof value === 'object'
    && value !== null
    && !Array.isArray(value)
  )
}

function isPlatform(
  value: unknown,
): value is CollectorProbe['platform'] {
  return (
    value === 'chatgpt'
    || value === 'claude'
    || value === 'gemini'
  )
}

function isBridgeStatus(
  value: unknown,
): value is BridgeStatus {
  return (
    value === 'due'
    || value === 'upcoming'
    || value === 'none'
  )
}

function isBridgeProbeItem(
  value: unknown,
): value is BridgeProbeItem {
  if (!isRecord(value)) {
    return false
  }

  return (
    typeof value.scheduled_at_utc === 'string'
    && typeof value.prompt_id === 'string'
    && typeof value.category === 'string'
    && typeof value.prompt === 'string'
  )
}

function parseBridgeNextResponse(
  value: unknown,
): BridgeNextResponse {
  if (!isRecord(value)) {
    throw new Error(
      'Invalid DLLO bridge payload.',
    )
  }

  if (
    value.schema_version !== '0.1'
    || !isBridgeStatus(value.status)
    || typeof value.now_utc !== 'string'
    || typeof value.schedule_date !== 'string'
    || typeof value.observer_id !== 'string'
    || !isPlatform(value.platform)
    || typeof value.benchmark_version !== 'string'
    || typeof value.completed_today !== 'number'
  ) {
    throw new Error(
      'Invalid DLLO bridge payload.',
    )
  }

  if (value.status === 'none') {
    if (value.item !== null) {
      throw new Error(
        'Invalid DLLO bridge payload.',
      )
    }
  } else if (!isBridgeProbeItem(value.item)) {
    throw new Error(
      'Invalid DLLO bridge payload.',
    )
  }

  return value as BridgeNextResponse
}

export function assignmentFromBridgeResponse(
  response: BridgeNextResponse,
): CollectorAssignment | null {
  if (
    response.status === 'none'
    || response.item === null
  ) {
    return null
  }

  return {
    status: response.status,
    category: response.item.category,
    probe: {
      platform: response.platform,
      pageHostname: hostnameForPlatform(
        response.platform,
      ),
      benchmarkVersion:
        response.benchmark_version,
      promptId: response.item.prompt_id,
      promptText: response.item.prompt,
      scheduledAtUtc:
        response.item.scheduled_at_utc,
      measurementMode:
        'consumer-ui-manual-v0.1',
      responseCaptureEnabled: false,
    },
  }
}

export type BridgeFetchResponse = {
  ok: boolean
  status: number
  json(): Promise<unknown>
}

export type BridgeFetch = (
  input: string,
) => Promise<BridgeFetchResponse>

export async function fetchBridgeAssignment(
  fetchImpl: BridgeFetch,
): Promise<CollectorAssignment | null> {
  const response = await fetchImpl('/v1/next')

  if (!response.ok) {
    throw new Error(
      `DLLO bridge request failed with HTTP ${response.status}.`,
    )
  }

  const payload = await response.json()

  return assignmentFromBridgeResponse(
    parseBridgeNextResponse(payload),
  )
}
