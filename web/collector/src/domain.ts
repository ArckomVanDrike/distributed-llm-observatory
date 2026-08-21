export type CollectorProbe = {
  platform: 'chatgpt' | 'claude' | 'gemini'
  pageHostname: string
  benchmarkVersion: string
  promptId: string
  promptText: string
  scheduledAtUtc: string
  measurementMode: 'consumer-ui-manual-v0.1'
  responseCaptureEnabled: false
}

export type CompletedObservationRecord = {
  schema_version: '0.1'
  probe_id: string

  prompt_id: string
  benchmark_version: string

  scheduled_at_utc: string
  schedule_offset_ms: number

  platform: CollectorProbe['platform']
  page_hostname: string

  started_at_ms: number
  started_at_utc: string

  first_output_at_ms: number | null
  first_output_at_utc: string | null

  completed_at_ms: number
  completed_at_utc: string

  time_to_first_output_ms: number | null
  first_output_measurement_mode:
    | 'human-observed-click-v0.1'
    | null
  total_latency_ms: number

  generation_failed: boolean
  interrupted: boolean
  retry_observed: boolean

  response_capture_enabled: false
  response_text: null

  measurement_mode: 'consumer-ui-manual-v0.1'

  local_telemetry: null
  local_telemetry_error: null
}

export type ConsumerProbeExport = {
  export_schema_version: '0.1'
  exported_at_utc: string
  sample_count: number
  records: CompletedObservationRecord[]
}

export type ObservationOutcomes = {
  generationFailed: boolean
  interrupted: boolean
  retryObserved: boolean
}

const DEFAULT_OBSERVATION_OUTCOMES: ObservationOutcomes = {
  generationFailed: false,
  interrupted: false,
  retryObserved: false,
}

export type ObservationSession = {
  observationId: string
  startedAtUtc: string
  firstOutputAtUtc: string | null
  completedAtUtc: string | null
  firstOutputMeasurementMode:
    | 'human-observed-click-v0.1'
    | null
  responseCaptureEnabled: false
}

export function elapsedMs(
  startUtc: string,
  endUtc: string | null,
): number | null {
  if (endUtc === null) {
    return null
  }

  return (
    new Date(endUtc).getTime()
    - new Date(startUtc).getTime()
  )
}

export function buildCompletedRecord(
  probe: CollectorProbe,
  session: ObservationSession,
  outcomes: ObservationOutcomes =
    DEFAULT_OBSERVATION_OUTCOMES,
): CompletedObservationRecord {
  if (session.completedAtUtc === null) {
    throw new Error(
      'Cannot build a completed record before completion.',
    )
  }

  const startedAtMs =
    new Date(session.startedAtUtc).getTime()

  if (Number.isNaN(startedAtMs)) {
    throw new Error(
      'Invalid observation start timestamp.',
    )
  }

  const completedAtMs =
    new Date(session.completedAtUtc).getTime()

  if (Number.isNaN(completedAtMs)) {
    throw new Error(
      'Invalid observation completion timestamp.',
    )
  }

  if (completedAtMs < startedAtMs) {
    throw new Error(
      'Completion cannot precede observation start.',
    )
  }

  const firstOutputAtMs =
    session.firstOutputAtUtc === null
      ? null
      : new Date(session.firstOutputAtUtc).getTime()

  if (
    firstOutputAtMs !== null
    && Number.isNaN(firstOutputAtMs)
  ) {
    throw new Error(
      'Invalid first-output timestamp.',
    )
  }

  if (
    firstOutputAtMs === null
    && session.firstOutputMeasurementMode !== null
  ) {
    throw new Error(
      'First-output measurement mode requires a recorded first output.',
    )
  }

  if (
    firstOutputAtMs !== null
    && firstOutputAtMs < startedAtMs
  ) {
    throw new Error(
      'First output cannot precede observation start.',
    )
  }

  if (
    firstOutputAtMs !== null
    && firstOutputAtMs > completedAtMs
  ) {
    throw new Error(
      'First output cannot occur after completion.',
    )
  }

  const scheduledAtMs =
    new Date(probe.scheduledAtUtc).getTime()

  if (Number.isNaN(scheduledAtMs)) {
    throw new Error(
      'Invalid scheduled timestamp.',
    )
  }

  return {
    schema_version: '0.1',
    probe_id: session.observationId,

    prompt_id: probe.promptId,
    benchmark_version: probe.benchmarkVersion,

    scheduled_at_utc: probe.scheduledAtUtc,
    schedule_offset_ms:
      startedAtMs - scheduledAtMs,

    platform: probe.platform,
    page_hostname: probe.pageHostname,

    started_at_ms: startedAtMs,
    started_at_utc: session.startedAtUtc,

    first_output_at_ms: firstOutputAtMs,
    first_output_at_utc: session.firstOutputAtUtc,

    completed_at_ms: completedAtMs,
    completed_at_utc: session.completedAtUtc,

    time_to_first_output_ms:
      firstOutputAtMs === null
        ? null
        : firstOutputAtMs - startedAtMs,

    first_output_measurement_mode:
      session.firstOutputMeasurementMode,

    total_latency_ms:
      completedAtMs - startedAtMs,

    generation_failed:
      outcomes.generationFailed,
    interrupted:
      outcomes.interrupted,
    retry_observed:
      outcomes.retryObserved,

    response_capture_enabled: false,
    response_text: null,

    measurement_mode: probe.measurementMode,

    local_telemetry: null,
    local_telemetry_error: null,
  }
}
