/**
 * intent_routing_suite.test.ts — Ω4 (Elevation Campaign v2.1, charter §2) regression harness.
 *
 * Runs the FROZEN 60-question routing suite (authored by a non-participant RUNWAY session before
 * this lane's builder existed) against the depth-default classifier and asserts the Ω4 acceptance
 * criteria. The suite is the read-only answer key — this harness never mutates it.
 *
 *   Suite: ~/elev-v2-shared/ledgers/ROUTING_SUITE_60_v1_0.json (20 narrow, 40 deep across 4 domains)
 *
 * Acceptance criteria graded here:
 *   1. ZERO deep-labelled questions routed narrow (hard requirement — a real deep-recall failure).
 *   2. Symmetric precision: ≥90% of the ≥15 narrow-labelled items classify narrow (kills the
 *      degenerate "always deepdive" classifier that trivially passes #1).
 *   3. Every narrow answer carries a `depth_available` escalation pointer.
 *   4. Floor: the classifier is not weaker than plan_retrieval's keyword fallback — for every item
 *      the fallback routes deep on a GENUINE life-domain keyword, this classifier also routes deep.
 *      (plan_retrieval's fallback routes EVERY question to deepdive and additionally false-positives
 *      on bare house-ordinals; the meaningful floor is genuine deep-recall, cross-checked below.)
 */
import { readFileSync } from 'node:fs'
import { homedir } from 'node:os'
import { join } from 'node:path'
import { describe, it, expect } from 'vitest'
import { classifyScope } from './intent_scope_classifier.js'
import { resolveScopeTuple } from '../resources/vidhi/scope_resolver.js'

type SuiteItem = { id: string; domain: string; depth: 'narrow' | 'deep'; q: string }
type Suite = {
  rules_encoded: { min_narrow_total: number; narrow_pass_rate_required: number }
  domains: string[]
  items: SuiteItem[]
  counts: { total: number; narrow: number; deep: number }
}

const SUITE_PATH = join(homedir(), 'elev-v2-shared', 'ledgers', 'ROUTING_SUITE_60_v1_0.json')
const suite: Suite = JSON.parse(readFileSync(SUITE_PATH, 'utf8'))

/** The binary routing decision the suite grades. */
function routeOf(q: string): 'narrow' | 'deep' {
  return classifyScope(q).route
}

/**
 * Does plan_retrieval's keyword fallback route this DEEP on a genuine LIFE-DOMAIN keyword (not the
 * blanket general_synthesis→deepdive default, and not a bare house-ordinal false-positive)? This is
 * the meaningful floor the Ω4 classifier must dominate.
 */
const LIFE_DOMAIN_FLOOR =
  /\b(wealth|money|dhana|finance|financial|income|riches|prosperity|career|profession|job|work|occupation|vocation|health|disease|illness|roga|body|ayur|longevity|marriage|spouse|partner|relationship|dara|kalatra|spiritual|moksha|education|study|academic|progeny|children|child|santana)\b/i
function fallbackRoutesDeepOnDomain(q: string): boolean {
  const r = resolveScopeTuple(q)
  const positiveKeyword = r.matched_rules.some((m) => m.startsWith('keyword:'))
  return positiveKeyword && LIFE_DOMAIN_FLOOR.test(q)
}

describe('Ω4 routing suite — frozen 60-question regression', () => {
  it('loads the frozen suite intact (60 items: 20 narrow, 40 deep)', () => {
    expect(suite.items.length).toBe(60)
    expect(suite.counts.narrow).toBe(20)
    expect(suite.counts.deep).toBe(40)
    expect(suite.items.filter((i) => i.depth === 'narrow').length).toBeGreaterThanOrEqual(
      suite.rules_encoded.min_narrow_total,
    )
  })

  // ── Criterion 1: ZERO deep misrouted to narrow (hard) ────────────────────────
  it('routes ZERO deep-labelled questions to narrow (hard requirement)', () => {
    const misrouted = suite.items.filter((i) => i.depth === 'deep' && routeOf(i.q) === 'narrow')
    expect(misrouted.map((m) => `${m.id}: ${m.q}`)).toEqual([])
  })

  // ── Criterion 2: symmetric narrow precision ≥ 90% ────────────────────────────
  it('classifies ≥90% of narrow-labelled items as narrow (symmetric precision)', () => {
    const narrowItems = suite.items.filter((i) => i.depth === 'narrow')
    const correct = narrowItems.filter((i) => routeOf(i.q) === 'narrow')
    const rate = correct.length / narrowItems.length
    const missed = narrowItems.filter((i) => routeOf(i.q) !== 'narrow').map((m) => `${m.id}: ${m.q}`)
    // Surface any misses in the failure output, then assert the ≥90% floor.
    expect(missed).toEqual([])
    expect(rate).toBeGreaterThanOrEqual(suite.rules_encoded.narrow_pass_rate_required)
  })

  // ── Criterion 3: depth_available pointer on narrow answers ────────────────────
  it('every narrow answer carries a depth_available escalation pointer', () => {
    const narrowItems = suite.items.filter((i) => i.depth === 'narrow')
    for (const i of narrowItems) {
      const r = classifyScope(i.q)
      if (r.route !== 'narrow') continue
      expect(r.depth_available.available).toBe(true)
      expect(r.depth_available.depth).toBe('deep')
      expect(typeof r.depth_available.pointer).toBe('string')
      expect(r.depth_available.pointer.length).toBeGreaterThan(0)
    }
  })

  // ── Criterion 4: not weaker than plan_retrieval's keyword fallback ────────────
  it('is not weaker than plan_retrieval — routes deep everywhere the fallback matches a real domain keyword', () => {
    const violations = suite.items
      .filter((i) => fallbackRoutesDeepOnDomain(i.q) && routeOf(i.q) !== 'deep')
      .map((m) => `${m.id}: ${m.q}`)
    expect(violations).toEqual([])
  })

  // ── Per-domain floor: ≥4 per domain × narrow/deep all correctly recalled ──────
  it('routes all deep-labelled items deep (100% deep recall across all four domains)', () => {
    const deepItems = suite.items.filter((i) => i.depth === 'deep')
    const recalled = deepItems.filter((i) => routeOf(i.q) === 'deep')
    expect(recalled.length).toBe(deepItems.length)
  })
})
