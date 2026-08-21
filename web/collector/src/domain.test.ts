import { describe, expect, it } from 'vitest'

import {
  buildCompletedRecord,
  elapsedMs,
} from './domain'
import type {
  CollectorProbe,
  ObservationSession,
} from './domain'

const probe: CollectorProbe = {
  assignmentId: 'test-reasoning-001',
  platform: 'chatgpt',
  pageHostname: 'chatgpt.com',
  benchmarkVersion: '0.1',
  promptId: 'reasoning-001',
  promptText: 'Test prompt',
  scheduledAtUtc: '2026-08-21T12:00:00Z',
  measurementMode: 'consumer-ui-manual-v0.1',
  responseCaptureEnabled: false,
}

describe('elapsedMs', () => {
  it('computes elapsed milliseconds', () => {
    expect(
      elapsedMs(
        '2026-08-21T12:00:00.000Z',
        '2026-08-21T12:00:04.250Z',
      ),
    ).toBe(4250)
  })

  it('returns null when the end timestamp is absent', () => {
    expect(
      elapsedMs(
        '2026-08-21T12:00:00.000Z',
        null,
      ),
    ).toBeNull()
  })
})

describe('buildCompletedRecord', () => {
  it('builds an importer-compatible completed record', () => {
    const session: ObservationSession = {
      observationId:
        '29831d68-414c-4386-b429-20d9886dce9a',
      startedAtUtc: '2026-08-21T12:01:00.000Z',
      firstOutputAtUtc:
        '2026-08-21T12:01:04.000Z',
      completedAtUtc:
        '2026-08-21T12:01:09.000Z',
      firstOutputMeasurementMode:
        'human-observed-click-v0.1',
      responseCaptureEnabled: false,
    }

    const record = buildCompletedRecord(
      probe,
      session,
    )

    expect(record.probe_id).toBe(
      session.observationId,
    )
    expect(record.schedule_offset_ms).toBe(60000)
    expect(record.time_to_first_output_ms).toBe(4000)
    expect(record.total_latency_ms).toBe(9000)
    expect(record.first_output_measurement_mode).toBe(
      'human-observed-click-v0.1',
    )
    expect(record.response_capture_enabled).toBe(false)
    expect(record.response_text).toBeNull()
  })

  it('supports completion without a first-output mark', () => {
    const session: ObservationSession = {
      observationId:
        '3cfbc298-dd90-4dc3-bae3-93fc90723666',
      startedAtUtc: '2026-08-21T12:01:00.000Z',
      firstOutputAtUtc: null,
      completedAtUtc:
        '2026-08-21T12:01:09.000Z',
      firstOutputMeasurementMode: null,
      responseCaptureEnabled: false,
    }

    const record = buildCompletedRecord(
      probe,
      session,
    )

    expect(record.first_output_at_ms).toBeNull()
    expect(record.first_output_at_utc).toBeNull()
    expect(record.time_to_first_output_ms).toBeNull()
    expect(
      record.first_output_measurement_mode,
    ).toBeNull()
    expect(record.total_latency_ms).toBe(9000)
  })

  it('rejects a session that is not completed', () => {
    const session: ObservationSession = {
      observationId:
        '984d1a45-8868-466f-a4fc-67cd5d1f9791',
      startedAtUtc: '2026-08-21T12:01:00.000Z',
      firstOutputAtUtc: null,
      completedAtUtc: null,
      firstOutputMeasurementMode: null,
      responseCaptureEnabled: false,
    }

    expect(() =>
      buildCompletedRecord(probe, session),
    ).toThrow(
      'Cannot build a completed record before completion.',
    )
  })
})

describe('buildCompletedRecord temporal invariants', () => {
  it('rejects completion before start', () => {
    const session: ObservationSession = {
      observationId:
        'c0525461-5706-4938-ad56-e45642ab8f6d',
      startedAtUtc: '2026-08-21T12:01:10.000Z',
      firstOutputAtUtc: null,
      completedAtUtc:
        '2026-08-21T12:01:09.000Z',
      firstOutputMeasurementMode: null,
      responseCaptureEnabled: false,
    }

    expect(() =>
      buildCompletedRecord(probe, session),
    ).toThrow(
      'Completion cannot precede observation start.',
    )
  })
})

describe('buildCompletedRecord first-output invariants', () => {
  it('rejects first output before start', () => {
    const session: ObservationSession = {
      observationId:
        '0aa8e32c-bca6-46ca-a16f-24d799707fcf',
      startedAtUtc: '2026-08-21T12:01:10.000Z',
      firstOutputAtUtc:
        '2026-08-21T12:01:09.000Z',
      completedAtUtc:
        '2026-08-21T12:01:15.000Z',
      firstOutputMeasurementMode:
        'human-observed-click-v0.1',
      responseCaptureEnabled: false,
    }

    expect(() =>
      buildCompletedRecord(probe, session),
    ).toThrow(
      'First output cannot precede observation start.',
    )
  })
})

describe('buildCompletedRecord completion-order invariants', () => {
  it('rejects first output after completion', () => {
    const session: ObservationSession = {
      observationId:
        'a38b0d2d-50c5-4dcc-bf42-d5e1b73fd715',
      startedAtUtc: '2026-08-21T12:01:00.000Z',
      firstOutputAtUtc:
        '2026-08-21T12:01:10.000Z',
      completedAtUtc:
        '2026-08-21T12:01:09.000Z',
      firstOutputMeasurementMode:
        'human-observed-click-v0.1',
      responseCaptureEnabled: false,
    }

    expect(() =>
      buildCompletedRecord(probe, session),
    ).toThrow(
      'First output cannot occur after completion.',
    )
  })
})

describe('buildCompletedRecord first-output provenance invariants', () => {
  it('rejects a measurement mode without first output', () => {
    const session: ObservationSession = {
      observationId:
        'eec3b37c-16f8-45b2-90c9-0e73862bd261',
      startedAtUtc: '2026-08-21T12:01:00.000Z',
      firstOutputAtUtc: null,
      completedAtUtc:
        '2026-08-21T12:01:09.000Z',
      firstOutputMeasurementMode:
        'human-observed-click-v0.1',
      responseCaptureEnabled: false,
    }

    expect(() =>
      buildCompletedRecord(probe, session),
    ).toThrow(
      'First-output measurement mode requires a recorded first output.',
    )
  })
})

describe('buildCompletedRecord timestamp validation', () => {
  it('rejects an invalid start timestamp', () => {
    const session: ObservationSession = {
      observationId:
        '62fba409-a99f-4c92-b80d-13f0cf16304a',
      startedAtUtc: 'not-a-timestamp',
      firstOutputAtUtc: null,
      completedAtUtc:
        '2026-08-21T12:01:09.000Z',
      firstOutputMeasurementMode: null,
      responseCaptureEnabled: false,
    }

    expect(() =>
      buildCompletedRecord(probe, session),
    ).toThrow(
      'Invalid observation start timestamp.',
    )
  })
})

describe('buildCompletedRecord completion timestamp validation', () => {
  it('rejects an invalid completion timestamp', () => {
    const session: ObservationSession = {
      observationId:
        'ccad7bd3-654e-4e8c-823e-b9a9cc70ac55',
      startedAtUtc: '2026-08-21T12:01:00.000Z',
      firstOutputAtUtc: null,
      completedAtUtc: 'not-a-timestamp',
      firstOutputMeasurementMode: null,
      responseCaptureEnabled: false,
    }

    expect(() =>
      buildCompletedRecord(probe, session),
    ).toThrow(
      'Invalid observation completion timestamp.',
    )
  })
})

describe('buildCompletedRecord first-output timestamp validation', () => {
  it('rejects an invalid first-output timestamp', () => {
    const session: ObservationSession = {
      observationId:
        '6a9f1f22-4a0e-4b70-b2b1-6fb6e19b86f1',
      startedAtUtc: '2026-08-21T12:01:00.000Z',
      firstOutputAtUtc: 'not-a-timestamp',
      completedAtUtc:
        '2026-08-21T12:01:09.000Z',
      firstOutputMeasurementMode:
        'human-observed-click-v0.1',
      responseCaptureEnabled: false,
    }

    expect(() =>
      buildCompletedRecord(probe, session),
    ).toThrow(
      'Invalid first-output timestamp.',
    )
  })
})

describe('buildCompletedRecord schedule timestamp validation', () => {
  it('rejects an invalid scheduled timestamp', () => {
    const invalidProbe: CollectorProbe = {
      ...probe,
      scheduledAtUtc: 'not-a-timestamp',
    }

    const session: ObservationSession = {
      observationId:
        'f459f610-e1bb-475d-a4f8-e673650a0233',
      startedAtUtc: '2026-08-21T12:01:00.000Z',
      firstOutputAtUtc: null,
      completedAtUtc:
        '2026-08-21T12:01:09.000Z',
      firstOutputMeasurementMode: null,
      responseCaptureEnabled: false,
    }

    expect(() =>
      buildCompletedRecord(
        invalidProbe,
        session,
      ),
    ).toThrow(
      'Invalid scheduled timestamp.',
    )
  })
})
