/**
 * CR-123 / DR-20 pre-score validation for the TypeScript scoring harness.
 * The input and its milestones are already in memory here. DR-20 separately
 * requires retrieval-time exclusion at the query/data layer.
 */

import { types } from 'node:util'
import type { CurveEvent } from './shape_scoring'

const testSplitBoundaryTime = Date.UTC(2020, 0, 1)

/** Events dated on/after this boundary are TEST and may never be scored by a build/admission agent. */
export const TEST_SPLIT_BOUNDARY: Date = new Date(testSplitBoundaryTime)

type SplitFailure = 'INVALID_EVENT' | 'SEALED_SPLIT'
type EventScope = 'train' | 'sealed' | 'invalid'

export class SealedTestSplitViolation extends Error {
  readonly code: SplitFailure

  constructor(reason: SplitFailure | Array<{ eventId: string; date: Date }>) {
    // Keep the legacy constructor usable without retaining its sensitive arguments.
    const code = reason === 'INVALID_EVENT' ? 'INVALID_EVENT' : 'SEALED_SPLIT'
    super(`sealed_split_guard refuses to proceed: ${code}`)
    this.name = 'SealedTestSplitViolation'
    this.code = code
  }
}

function timestamp(date: Date | undefined): number | undefined {
  return date === undefined ? undefined : Date.prototype.getTime.call(date)
}

function isEventArray(value: unknown): value is CurveEvent[] {
  return Array.isArray(value) && !types.isProxy(value)
}

function eventAt<T extends CurveEvent>(events: T[], index: number): T | undefined {
  const slot = Object.getOwnPropertyDescriptor(events, index)
  return slot && 'value' in slot ? slot.value : undefined
}

function eventScope(event: CurveEvent | undefined, ancestors: Set<CurveEvent>): EventScope {
  if (!event || typeof event !== 'object' || ancestors.has(event)) return 'invalid'

  ancestors.add(event)
  try {
    const { shape, eventDate, intervalStart, intervalEnd, milestones } = event
    const point = timestamp(eventDate)
    const start = timestamp(intervalStart)
    const end = timestamp(intervalEnd)
    const dates = [point, start, end].filter((time) => time !== undefined)
    if (dates.some((time) => !Number.isFinite(time))) return 'invalid'
    if (milestones !== undefined && !isEventArray(milestones)) return 'invalid'

    switch (shape) {
      case 'point':
        if (point === undefined) return 'invalid'
        break
      case 'interval':
        if (start === undefined || end === undefined || start > end) return 'invalid'
        break
      case 'chain':
        if (!milestones?.length) return 'invalid'
        break
      default:
        return 'invalid'
    }

    // Every carried date counts, including dates outside the event's primary shape.
    let sealed = dates.some((time) => time >= testSplitBoundaryTime)
    if (milestones) {
      for (let index = 0; index < milestones.length; index++) {
        const scope = eventScope(eventAt(milestones, index), ancestors)
        if (scope === 'invalid') return 'invalid'
        sealed ||= scope === 'sealed'
      }
    }
    return sealed ? 'sealed' : 'train'
  } catch {
    // A non-Date value or malformed object must never supply diagnostic text.
    return 'invalid'
  } finally {
    ancestors.delete(event)
  }
}

/** Refuses malformed inputs and any event that touches the sealed split before scoring. */
export function assertNoSealedSplitEvents(events: CurveEvent[]): void {
  let sealed = false
  try {
    if (!isEventArray(events)) throw new SealedTestSplitViolation('INVALID_EVENT')

    const ancestors = new Set<CurveEvent>()
    for (let index = 0; index < events.length; index++) {
      const scope = eventScope(eventAt(events, index), ancestors)
      if (scope === 'invalid') throw new SealedTestSplitViolation('INVALID_EVENT')
      sealed ||= scope === 'sealed'
    }
  } catch {
    throw new SealedTestSplitViolation('INVALID_EVENT')
  }
  if (sealed) throw new SealedTestSplitViolation('SEALED_SPLIT')
}

/** Builds a train-scope packet from valid train events, preserving their order and identity. */
export function filterToTrainScope<T extends CurveEvent>(events: T[]): T[] {
  const train: T[] = []
  try {
    if (!isEventArray(events)) throw new SealedTestSplitViolation('INVALID_EVENT')

    const ancestors = new Set<CurveEvent>()
    for (let index = 0; index < events.length; index++) {
      const event = eventAt(events, index)
      if (event && eventScope(event, ancestors) === 'train') train.push(event)
    }
    return train
  } catch {
    throw new SealedTestSplitViolation('INVALID_EVENT')
  }
}
