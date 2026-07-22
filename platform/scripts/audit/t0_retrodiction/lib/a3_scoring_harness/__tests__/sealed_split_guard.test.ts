import { describe, it, expect } from 'vitest'
import {
  TEST_SPLIT_BOUNDARY,
  SealedTestSplitViolation,
  assertNoSealedSplitEvents,
  filterToTrainScope,
} from '../sealed_split_guard'
import type { CurveEvent } from '../shape_scoring'

const trainPoint: CurveEvent = {
  eventId: 'EVT.2013.12.11.01',
  shape: 'point',
  dateConfidence: 'exact',
  eventDate: new Date('2013-12-11T00:00:00.000Z'),
}

const sealedPoint: CurveEvent = {
  eventId: 'EVT.2021.01.15.01',
  shape: 'point',
  dateConfidence: 'exact',
  eventDate: new Date('2021-01-15T00:00:00.000Z'),
}

const boundaryPoint: CurveEvent = {
  eventId: 'EVT.2020.01.01.01',
  shape: 'point',
  dateConfidence: 'exact',
  eventDate: new Date('2020-01-01T00:00:00.000Z'),
}

const trainInterval: CurveEvent = {
  eventId: 'EVT.2010.07.XX.01',
  shape: 'interval',
  dateConfidence: 'month_known',
  intervalStart: new Date('2010-07-01T00:00:00.000Z'),
  intervalEnd: new Date('2011-03-01T00:00:00.000Z'),
}

const sealedIntervalEndOnly: CurveEvent = {
  eventId: 'EVT.2019.11.XX.01',
  shape: 'interval',
  dateConfidence: 'month_known',
  intervalStart: new Date('2019-11-01T00:00:00.000Z'),
  intervalEnd: new Date('2020-02-01T00:00:00.000Z'), // sealed on the END side only
}

const trainChain: CurveEvent = {
  eventId: 'EVT.CHAIN.01',
  shape: 'chain',
  dateConfidence: 'exact',
  milestones: [
    { eventId: 'EVT.CHAIN.01.a', shape: 'point', dateConfidence: 'exact', eventDate: new Date('2015-01-01T00:00:00.000Z') },
    { eventId: 'EVT.CHAIN.01.b', shape: 'point', dateConfidence: 'exact', eventDate: new Date('2016-01-01T00:00:00.000Z') },
  ],
}

const sealedChainMilestone: CurveEvent = {
  eventId: 'EVT.CHAIN.02',
  shape: 'chain',
  dateConfidence: 'exact',
  milestones: [
    { eventId: 'EVT.CHAIN.02.a', shape: 'point', dateConfidence: 'exact', eventDate: new Date('2015-01-01T00:00:00.000Z') },
    { eventId: 'EVT.CHAIN.02.b', shape: 'point', dateConfidence: 'exact', eventDate: new Date('2022-01-01T00:00:00.000Z') }, // sealed milestone
  ],
}

describe('sealed_split_guard (CR-123 / DR-20)', () => {
  it('TEST_SPLIT_BOUNDARY is 2020-01-01', () => {
    expect(TEST_SPLIT_BOUNDARY.toISOString().slice(0, 10)).toBe('2020-01-01')
  })

  it('assertNoSealedSplitEvents PASSES for train-only point/interval/chain events', () => {
    expect(() => assertNoSealedSplitEvents([trainPoint, trainInterval, trainChain])).not.toThrow()
  })

  it('assertNoSealedSplitEvents THROWS SealedTestSplitViolation for a sealed point event', () => {
    expect(() => assertNoSealedSplitEvents([trainPoint, sealedPoint])).toThrow(SealedTestSplitViolation)
  })

  it('assertNoSealedSplitEvents THROWS for the exact boundary date (>=, not >)', () => {
    expect(() => assertNoSealedSplitEvents([boundaryPoint])).toThrow(SealedTestSplitViolation)
  })

  it('assertNoSealedSplitEvents THROWS for an interval whose END (not start) is sealed', () => {
    expect(() => assertNoSealedSplitEvents([sealedIntervalEndOnly])).toThrow(SealedTestSplitViolation)
  })

  it('assertNoSealedSplitEvents THROWS for a chain with one sealed milestone, even if others are train', () => {
    expect(() => assertNoSealedSplitEvents([sealedChainMilestone])).toThrow(SealedTestSplitViolation)
  })

  it('the thrown error names every offending event, not just the first', () => {
    try {
      assertNoSealedSplitEvents([trainPoint, sealedPoint, boundaryPoint])
      expect.fail('should have thrown')
    } catch (e) {
      expect(e).toBeInstanceOf(SealedTestSplitViolation)
      const msg = (e as Error).message
      expect(msg).toContain('EVT.2021.01.15.01')
      expect(msg).toContain('EVT.2020.01.01.01')
      expect(msg).not.toContain('EVT.2013.12.11.01') // the clean event is not named as an offender
    }
  })

  it('filterToTrainScope keeps train events and drops sealed ones (point/interval/chain)', () => {
    const input = [trainPoint, sealedPoint, trainInterval, sealedIntervalEndOnly, trainChain, sealedChainMilestone]
    const result = filterToTrainScope(input)
    expect(result.map((e) => e.eventId)).toEqual([trainPoint.eventId, trainInterval.eventId, trainChain.eventId])
  })

  it('filterToTrainScope on an all-clean list returns everything unchanged', () => {
    const input = [trainPoint, trainInterval, trainChain]
    expect(filterToTrainScope(input)).toEqual(input)
  })

  it('filterToTrainScope on an all-sealed list returns empty, never throws', () => {
    expect(filterToTrainScope([sealedPoint, boundaryPoint])).toEqual([])
  })
})
