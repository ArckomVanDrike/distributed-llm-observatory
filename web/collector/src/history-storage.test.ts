import {
  describe,
  expect,
  it,
} from 'vitest'

import {
  appendObservationRecord,
  buildCompletedRecord,
  createObservationHistory,
} from './domain'
import type {
  CollectorProbe,
  ObservationSession,
} from './domain'

import {
  clearObservationHistory,
  loadObservationHistory,
  saveObservationHistory,
} from './history-storage'

class MemoryStorage {
  private readonly values = new Map<string, string>()

  getItem(key: string): string | null {
    return this.values.get(key) ?? null
  }

  setItem(key: string, value: string): void {
    this.values.set(key, value)
  }

  removeItem(key: string): void {
    this.values.delete(key)
  }
}

const probe: CollectorProbe = {
  platform: 'chatgpt',
  pageHostname: 'chatgpt.com',
  benchmarkVersion: '0.1',
  promptId: 'reasoning-001',
  promptText: 'Test prompt',
  scheduledAtUtc: '2026-08-21T12:00:00.000Z',
  measurementMode: 'consumer-ui-manual-v0.1',
  responseCaptureEnabled: false,
}

const session: ObservationSession = {
  observationId:
    'b5ebca43-c9dd-41b0-a502-6047a34dd91a',
  startedAtUtc: '2026-08-21T12:01:00.000Z',
  firstOutputAtUtc: '2026-08-21T12:01:04.000Z',
  completedAtUtc: '2026-08-21T12:01:09.000Z',
  firstOutputMeasurementMode:
    'human-observed-click-v0.1',
  responseCaptureEnabled: false,
}

describe('observation history storage', () => {
  it('returns empty history when nothing is persisted', () => {
    const storage = new MemoryStorage()

    expect(loadObservationHistory(storage)).toEqual(
      createObservationHistory(),
    )
  })

  it('round-trips persisted observation history', () => {
    const storage = new MemoryStorage()

    const record = buildCompletedRecord(
      probe,
      session,
    )

    const history = appendObservationRecord(
      createObservationHistory(),
      record,
    )

    saveObservationHistory(
      storage,
      history,
    )

    expect(loadObservationHistory(storage)).toEqual(
      history,
    )
  })

  it('falls back safely when persisted JSON is corrupted', () => {
    const storage = new MemoryStorage()

    storage.setItem(
      'dllo.collector.observation-history',
      '{not-json',
    )

    expect(loadObservationHistory(storage)).toEqual(
      createObservationHistory(),
    )
  })
})

describe('observation history storage failures', () => {
  it('falls back safely when storage reads fail', () => {
    const storage = {
      getItem(): string | null {
        throw new Error('storage unavailable')
      },
      setItem(): void {},
      removeItem(): void {},
    }

    expect(loadObservationHistory(storage)).toEqual(
      createObservationHistory(),
    )
  })

  it('does not throw when storage writes fail', () => {
    const storage = {
      getItem(): string | null {
        return null
      },
      setItem(): void {
        throw new Error('quota exceeded')
      },
      removeItem(): void {},
    }

    expect(() => {
      saveObservationHistory(
        storage,
        createObservationHistory(),
      )
    }).not.toThrow()
  })
})

describe('clearObservationHistory', () => {
  it('removes persisted observation history', () => {
    const storage = new MemoryStorage()

    const record = buildCompletedRecord(
      probe,
      session,
    )

    const history = appendObservationRecord(
      createObservationHistory(),
      record,
    )

    saveObservationHistory(
      storage,
      history,
    )

    clearObservationHistory(storage)

    expect(loadObservationHistory(storage)).toEqual(
      createObservationHistory(),
    )
  })
})
