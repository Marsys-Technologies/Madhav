import type { WireEvent } from '../state/types'

/**
 * A scheduled fixture event: `atMs` is an absolute offset from turn-open
 * (t=0), not a delta from the previous event — this makes fixtures easy to
 * reason about and easy to re-splice (see `useFixtureStream`).
 */
export interface ScheduledEvent {
  atMs: number
  event: WireEvent
}

export interface Fixture {
  id: string
  label: string
  userText: string
  events: ScheduledEvent[]
}
