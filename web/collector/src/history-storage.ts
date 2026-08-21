import {
  createObservationHistory,
} from './domain'
import type {
  ObservationHistory,
} from './domain'

const STORAGE_KEY =
  'dllo.collector.observation-history'

type StorageLike = {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
  removeItem(key: string): void
}

type PersistedObservationHistory = {
  storage_schema_version: '0.1'
  history: ObservationHistory
}

export function loadObservationHistory(
  storage: StorageLike,
): ObservationHistory {
  try {
    const raw = storage.getItem(STORAGE_KEY)

    if (raw === null) {
      return createObservationHistory()
    }

    const parsed =
      JSON.parse(raw) as Partial<PersistedObservationHistory>

    if (
      parsed.storage_schema_version !== '0.1'
      || parsed.history === undefined
      || !Array.isArray(parsed.history.records)
    ) {
      return createObservationHistory()
    }

    return {
      records: [...parsed.history.records],
    }
  } catch {
    return createObservationHistory()
  }
}

export function saveObservationHistory(
  storage: StorageLike,
  history: ObservationHistory,
): void {
  const payload: PersistedObservationHistory = {
    storage_schema_version: '0.1',
    history: {
      records: [...history.records],
    },
  }

  try {
    storage.setItem(
      STORAGE_KEY,
      JSON.stringify(payload),
    )
  } catch {
    // Persistence is best-effort. The in-memory history remains usable.
  }
}

export function clearObservationHistory(
  storage: StorageLike,
): void {
  try {
    storage.removeItem(STORAGE_KEY)
  } catch {
    // Clearing persistence is best-effort.
  }
}
