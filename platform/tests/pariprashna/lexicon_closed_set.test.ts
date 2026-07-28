/**
 * Paripraśna PB-1 (DHĀRĀ), Lane S-2 — closed-lexicon self-consistency.
 * ======================================================================
 * Proves the lexicon module (`src/lib/pariprashna/lexicon.ts`) is genuinely
 * CLOSED and leak-proof, independent of any registry wiring:
 *
 *  1. Every string the module can statically produce is free of internal-leak
 *     patterns (asset ids, table names, layer names, tool-shaped identifiers,
 *     capability URIs) — `isLeakFree()` over `CLOSED_LEXICON_STRINGS`.
 *  2. The dynamic renderers (`renderPlanCompileLabel`, `renderFullCoverageLabel`,
 *     etc.) never introduce a leak either, across representative inputs.
 *  3. `STATIC_REGISTRY_READER_LABELS` (the subset a capability descriptor may
 *     legally declare) is a proper subset of `CLOSED_LEXICON_STRINGS`.
 */
import { describe, it, expect } from 'vitest'
import {
  CLOSED_LEXICON_STRINGS,
  STATIC_REGISTRY_READER_LABELS,
  RETRIEVAL_FACET_NAMES,
  DIVISIONAL_CHART_LABELS,
  BAND_PHASES,
  SEAM_LABELS,
  EDGE_STATE_LABELS,
  FALLBACK_READER_LABEL,
  isLeakFree,
  renderRetrievalLabel,
  renderDivisionalLabel,
  renderPlanCompileLabel,
  renderFullCoverageLabel,
  renderDeliberatingLabel,
  renderGroundingGateLabel,
  renderSealCompleteLabel,
  renderCappedPartialLabel,
  renderModelSwitchQueuedLabel,
  type RetrievalFacetKey,
} from '@/lib/pariprashna/lexicon'

describe('lexicon — closed set is genuinely exhaustive and leak-free', () => {
  it('CLOSED_LEXICON_STRINGS is non-empty and every member is leak-free', () => {
    expect(CLOSED_LEXICON_STRINGS.size).toBeGreaterThan(10)
    for (const label of CLOSED_LEXICON_STRINGS) {
      expect(isLeakFree(label), `leak pattern matched in closed-lexicon string: "${label}"`).toBe(
        true
      )
    }
  })

  it('STATIC_REGISTRY_READER_LABELS is a subset of CLOSED_LEXICON_STRINGS', () => {
    for (const label of STATIC_REGISTRY_READER_LABELS) {
      expect(CLOSED_LEXICON_STRINGS.has(label), `"${label}" missing from CLOSED_LEXICON_STRINGS`).toBe(
        true
      )
    }
  })

  it('every band phase label is leak-free', () => {
    for (const phase of BAND_PHASES) {
      expect(isLeakFree(phase.label), `band phase "${phase.id}" label leaked: "${phase.label}"`).toBe(
        true
      )
    }
  })

  it('every seam label is leak-free', () => {
    for (const label of Object.values(SEAM_LABELS)) {
      expect(isLeakFree(label)).toBe(true)
    }
  })

  it('every static edge-state label is leak-free', () => {
    for (const label of Object.values(EDGE_STATE_LABELS)) {
      expect(isLeakFree(label)).toBe(true)
    }
  })

  it('every retrieval facet name and rendered label is leak-free and closed', () => {
    for (const key of Object.keys(RETRIEVAL_FACET_NAMES) as RetrievalFacetKey[]) {
      const rendered = renderRetrievalLabel(key)
      expect(isLeakFree(rendered)).toBe(true)
      expect(CLOSED_LEXICON_STRINGS.has(rendered)).toBe(true)
    }
  })

  it('every divisional-chart plain name and rendered label is leak-free and closed', () => {
    for (const code of Object.keys(DIVISIONAL_CHART_LABELS)) {
      const rendered = renderDivisionalLabel(code)
      expect(isLeakFree(rendered)).toBe(true)
      expect(CLOSED_LEXICON_STRINGS.has(rendered)).toBe(true)
    }
    // Unmapped/omitted varga falls back to the generic facet — still closed and leak-free.
    const genericFallback = renderDivisionalLabel('D999-does-not-exist')
    expect(isLeakFree(genericFallback)).toBe(true)
    expect(CLOSED_LEXICON_STRINGS.has(genericFallback)).toBe(true)
    expect(renderDivisionalLabel(undefined)).toBe(renderRetrievalLabel('divisional_charts'))
  })

  it('dynamic renderers stay leak-free across representative inputs', () => {
    expect(isLeakFree(renderPlanCompileLabel())).toBe(true)
    expect(isLeakFree(renderPlanCompileLabel(7))).toBe(true)
    expect(isLeakFree(renderFullCoverageLabel())).toBe(true)
    expect(isLeakFree(renderFullCoverageLabel(63))).toBe(true)
    expect(isLeakFree(renderDeliberatingLabel(1234))).toBe(true)
    expect(isLeakFree(renderGroundingGateLabel())).toBe(true)
    expect(isLeakFree(renderGroundingGateLabel(9, 14))).toBe(true)
    expect(isLeakFree(renderSealCompleteLabel(14, 42))).toBe(true)
    expect(isLeakFree(renderCappedPartialLabel(3, 8))).toBe(true)
    expect(isLeakFree(renderModelSwitchQueuedLabel('Opus'))).toBe(true)
  })

  it('band phase 3/7/9 suffix formatting is exact', () => {
    expect(renderPlanCompileLabel()).toBe('Composing the approach')
    expect(renderPlanCompileLabel(5)).toBe('Composing the approach · 5 steps')
    expect(renderFullCoverageLabel()).toBe('Completing full coverage')
    expect(renderFullCoverageLabel(63.4)).toBe('Completing full coverage · 63%')
    expect(renderGroundingGateLabel()).toBe('Verifying every claim')
    expect(renderGroundingGateLabel(14, 14)).toBe('Verifying every claim · 14/14')
    expect(renderSealCompleteLabel(14, 42)).toBe('Grounded in 14 sources · 42s')
  })

  it('FALLBACK_READER_LABEL itself is leak-free and a member of the closed set', () => {
    expect(isLeakFree(FALLBACK_READER_LABEL)).toBe(true)
    expect(CLOSED_LEXICON_STRINGS.has(FALLBACK_READER_LABEL)).toBe(true)
  })

  it('no phase, seam, or edge-state label collides across categories (each string is unambiguous)', () => {
    const phaseLabels = BAND_PHASES.map((p) => p.label)
    const seamLabels = Object.values(SEAM_LABELS)
    // Phases and seams are allowed to be disjoint sets; assert no accidental duplication.
    const overlap = phaseLabels.filter((l) => seamLabels.includes(l))
    expect(overlap).toEqual([])
  })
})

describe('lexicon — isLeakFree catches the categories it claims to', () => {
  it('flags an asset id', () => {
    expect(isLeakFree('Consulting ga_chart_facts')).toBe(false)
    expect(isLeakFree('Reading bo_sangati now')).toBe(false)
    expect(isLeakFree('mi_bhavisya lookup')).toBe(false)
  })

  it('flags a layer name', () => {
    expect(isLeakFree('Fetching from L2')).toBe(false)
  })

  it('flags a table name', () => {
    expect(isLeakFree('Querying chart_facts')).toBe(false)
    expect(isLeakFree('Reading bodha_signals')).toBe(false)
  })

  it('flags a capability URI', () => {
    expect(isLeakFree('marsys://tool/L1/get_dashas')).toBe(false)
  })

  it('flags a tool-name-shaped identifier', () => {
    expect(isLeakFree('calling get_dashas')).toBe(false)
    expect(isLeakFree('running ganita_yogas_get')).toBe(false)
  })

  it('does not flag ordinary reader-facing prose', () => {
    expect(isLeakFree('Consulting the chart — Daśā structure')).toBe(true)
    expect(isLeakFree('Reading the whole chart')).toBe(true)
    expect(isLeakFree('Grounded in 14 sources · 42s')).toBe(true)
  })
})
