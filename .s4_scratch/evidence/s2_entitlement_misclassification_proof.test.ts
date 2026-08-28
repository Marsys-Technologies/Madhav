/**
 * S4 SCRATCH TEST — synergy test §4.3 item 2 (degradation propagation honesty).
 * NOT part of the permanent suite; written to empirically demonstrate that
 * entitlement-denial (S2) error codes fall through `classifyPariprashnaError`'s
 * `classifyKind()` into the generic 'unknown' bucket, producing a MISLEADING
 * "transient plumbing" band label instead of an honest "you are not authorized /
 * consent required" disclosure. Delete after S4 report is filed.
 */
import { describe, it, expect } from 'vitest'
import { classifyPariprashnaError } from '../classify'

describe('S4 degradation honesty — S2 entitlement-denial error codes', () => {
  it('FORBIDDEN (authorizeChartAccess deny, safety_gate.ts authorizeTurn) collapses to unknown/plumbing', () => {
    const e = classifyPariprashnaError('FORBIDDEN')
    expect(e.kind).toBe('unknown')
    expect(e.bandLabel).toBe('Something failed on our side')
    expect(e.sentence).toBe('Not the chart, not your question — the plumbing. It is logged.')
    expect(e.actions).toEqual(['retry'])
  })

  it('CHART_NOT_FOUND collapses to unknown/plumbing', () => {
    const e = classifyPariprashnaError('CHART_NOT_FOUND')
    expect(e.kind).toBe('unknown')
    expect(e.bandLabel).toBe('Something failed on our side')
  })

  it('SUBJECT_CONSENT_REQUIRED:<reason> collapses to unknown/plumbing', () => {
    const e = classifyPariprashnaError('SUBJECT_CONSENT_REQUIRED:no_consent_row')
    expect(e.kind).toBe('unknown')
    expect(e.bandLabel).toBe('Something failed on our side')
    // The 'retry' action is actively wrong advice for a permission/consent
    // denial: retrying changes nothing about consent state.
    expect(e.actions).toEqual(['retry'])
  })

  it('CONVERSATION_NOT_FOUND collapses to unknown/plumbing', () => {
    const e = classifyPariprashnaError('CONVERSATION_NOT_FOUND')
    expect(e.kind).toBe('unknown')
  })
})
