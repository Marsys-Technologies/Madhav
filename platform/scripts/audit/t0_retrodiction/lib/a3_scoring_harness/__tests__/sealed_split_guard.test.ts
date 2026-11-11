import { describe, expect, it } from 'vitest'
import {
  TEST_SPLIT_BOUNDARY,
  SealedTestSplitViolation,
  assertNoSealedSplitEvents,
  filterToTrainScope,
} from '../sealed_split_guard'
import type { CurveEvent } from '../shape_scoring'

const boundary = Date.UTC(2020, 0, 1)
const trainDate = new Date(Date.UTC(1900, 1, 3))
const sealedDate = new Date(Date.UTC(2100, 2, 4))

const trainPoint: CurveEvent = {
  eventId: 'synthetic-train-point',
  shape: 'point',
  dateConfidence: 'exact',
  eventDate: trainDate,
}

const sealedPoint: CurveEvent = {
  ...trainPoint,
  eventId: 'synthetic-sealed-point',
  eventDate: sealedDate,
}

const boundaryPoint: CurveEvent = {
  ...trainPoint,
  eventId: 'synthetic-boundary-point',
  eventDate: new Date(boundary),
}

const trainInterval: CurveEvent = {
  eventId: 'synthetic-train-interval',
  shape: 'interval',
  dateConfidence: 'month_known',
  intervalStart: trainDate,
  intervalEnd: new Date(boundary - 1),
}

const sealedInterval: CurveEvent = {
  ...trainInterval,
  eventId: 'synthetic-sealed-interval',
  intervalEnd: sealedDate,
}

function chain(eventId: string, ...milestones: CurveEvent[]): CurveEvent {
  return { eventId, shape: 'chain', dateConfidence: 'exact', milestones }
}

const trainChain = chain('synthetic-train-chain', chain('synthetic-train-subchain', trainPoint, trainInterval))
const sealedChain = chain('synthetic-sealed-chain', trainChain, chain('synthetic-sealed-subchain', sealedPoint))

const cyclicChain = chain('synthetic-cyclic-chain')
cyclicChain.milestones?.push(cyclicChain)

const inheritedMilestones = new Array<CurveEvent>(1)
Object.setPrototypeOf(inheritedMilestones, Object.assign(Object.create(Array.prototype), { 0: trainPoint }))

function maskedLength(events: CurveEvent[], length: unknown): CurveEvent[] {
  return new Proxy(events, {
    get(target, key, receiver) {
      return key === 'length' ? length : Reflect.get(target, key, receiver)
    },
  })
}

const malformedEvents: [string, unknown][] = [
  ['null event', null],
  ['unknown shape', { ...trainPoint, shape: 'synthetic-invalid-shape' }],
  ['missing point date', { ...trainPoint, eventDate: undefined }],
  ['invalid Date', { ...trainPoint, eventDate: new Date(NaN) }],
  ['date-like object', { ...trainPoint, eventDate: { getTime: () => trainDate.getTime() } }],
  ['date string', { ...trainPoint, eventDate: trainDate.toISOString() }],
  ['missing interval start', { ...trainInterval, intervalStart: undefined }],
  ['missing interval end', { ...trainInterval, intervalEnd: undefined }],
  ['reversed interval', { ...trainInterval, intervalStart: trainInterval.intervalEnd, intervalEnd: trainDate }],
  ['missing milestones', { ...trainChain, milestones: undefined }],
  ['non-array milestones', { ...trainChain, milestones: { 0: trainPoint } }],
  ['empty milestones', chain('synthetic-empty-chain')],
  ['sparse milestones', { ...trainChain, milestones: new Array<CurveEvent>(1) }],
  ['prototype-supplied milestone', { ...trainChain, milestones: inheritedMilestones }],
  ['non-numeric milestone length', { ...trainChain, milestones: maskedLength([sealedPoint], 'synthetic-length') }],
  ['masked milestone length', { ...trainPoint, milestones: maskedLength([sealedPoint], 0) }],
  ['invalid nested milestone', chain('synthetic-invalid-subchain', { ...trainPoint, eventDate: new Date(NaN) })],
  ['cyclic milestones', cyclicChain],
]

describe('sealed_split_guard', () => {
  it('keeps the policy boundary at midnight UTC', () => {
    expect(TEST_SPLIT_BOUNDARY.getTime()).toBe(boundary)
  })

  it('accepts train points, ordered intervals and nested chains with reused train events', () => {
    expect(() => assertNoSealedSplitEvents([trainPoint, trainInterval, trainChain])).not.toThrow()
  })

  it.each([
    ['sealed point', sealedPoint],
    ['exact boundary', boundaryPoint],
    ['interval with a sealed end', sealedInterval],
    ['nested chain with a sealed point', sealedChain],
    ['additional date carried by a train point', { ...trainPoint, intervalEnd: sealedDate }],
  ])('rejects a %s', (_label, event) => {
    expect(() => assertNoSealedSplitEvents([event])).toThrow(SealedTestSplitViolation)
  })

  it.each(malformedEvents)('rejects %s with a redacted error and excludes it from train filtering', (_label, malformed) => {
    const input = [malformed as CurveEvent]
    expect(() => assertNoSealedSplitEvents(input)).toThrow(SealedTestSplitViolation)
    expect(() => assertNoSealedSplitEvents(input)).toThrow('sealed_split_guard: INVALID_EVENT')
    expect(filterToTrainScope([...input, trainPoint])).toEqual([trainPoint])
  })

  it('rejects a malformed event list with a redacted error', () => {
    const input = null as unknown as CurveEvent[]
    expect(() => assertNoSealedSplitEvents(input)).toThrow('sealed_split_guard: INVALID_EVENT')
    expect(() => filterToTrainScope(input)).toThrow('sealed_split_guard: INVALID_EVENT')
  })

  it.each([NaN, 0])('rejects an event list with a proxy length of %s', (length) => {
    const input = maskedLength([sealedPoint], length)
    expect(() => assertNoSealedSplitEvents(input)).toThrow('sealed_split_guard: INVALID_EVENT')
    expect(() => filterToTrainScope(input)).toThrow('sealed_split_guard: INVALID_EVENT')
  })

  it('keeps all failure details out of the message and stack', () => {
    const reject = () => assertNoSealedSplitEvents([trainPoint, sealedPoint, boundaryPoint, sealedChain])
    expect(reject).toThrow(SealedTestSplitViolation)
    try {
      reject()
    } catch (error) {
      expect(error).toMatchObject({
        name: 'SealedTestSplitViolation',
        message: 'sealed_split_guard: SEALED_SPLIT',
      })
      expect((error as Error).stack).not.toMatch(/synthetic-|\d{4}-\d{2}-\d{2}/)
    }
  })

  it('filters valid events by date while keeping train references and order', () => {
    const input = [sealedPoint, trainPoint, sealedInterval, trainInterval, trainChain, boundaryPoint, sealedChain]
    const result = filterToTrainScope(input)
    expect(result).toEqual([trainPoint, trainInterval, trainChain])
    expect(result[2]).toBe(trainChain)
    expect(input).toHaveLength(7)
  })

  it('retains all clean events and returns an empty list for entirely sealed inputs', () => {
    const input = [trainPoint, trainInterval, trainChain]
    expect(filterToTrainScope(input)).toEqual(input)
    expect(filterToTrainScope([sealedPoint, boundaryPoint])).toEqual([])
  })
})
