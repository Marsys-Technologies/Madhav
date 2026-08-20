/**
 * P2-G (Edge-state lexicon) — pins EVERY §7.8 edge-state row's exact lexicon
 * copy against `lib/pariprashna/lexicon.ts`'s `EDGE_STATE_LABELS` /
 * `renderCappedPartialLabel` / `renderModelSwitchQueuedLabel`, by real string
 * equality against the design plan's literal table text — never a loose
 * `.toContain()` that would pass on paraphrased or drifted copy.
 *
 * Source: `PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md` §7.8 "Edge & exception
 * states" table. §7.8's table renders band text in ALL CAPS for legibility;
 * per that same section's own closed-lexicon convention (and this file's
 * sibling `lexicon_closed_set.test.ts`), the authored source strings are
 * natural (sentence) case — the client applies `text-transform: uppercase`
 * at render time, never the data. So each expected literal below is the
 * table's copy lower-cased to sentence case, not a re-paraphrase.
 *
 * This is the exhaustive half of P2-G's fixture coverage: every one of
 * §7.8's ten situation rows (eleven `EdgeStateKey`s — network splits into its
 * two sequential states) is pinned here, regardless of whether a live wire/
 * reducer path exists for it yet. The render-level proof for the subset that
 * DOES have a real path today (network drop/resume, user-stopped, the six
 * §7.5 error kinds) lives in `edge_state_rendering.test.tsx`.
 */
import { describe, it, expect } from 'vitest'
import {
  EDGE_STATE_LABELS,
  renderCappedPartialLabel,
  renderModelSwitchQueuedLabel,
  type EdgeStateKey,
} from '@/lib/pariprashna/lexicon'

describe('§7.8 edge-state table — exact lexicon copy, row by row', () => {
  it('Engine asks back (clarification) → "A question first"', () => {
    expect(EDGE_STATE_LABELS.clarification_needed).toBe('A question first')
  })

  it('Open window relevant (J8) → "Before I answer —"', () => {
    expect(EDGE_STATE_LABELS.open_prediction_window).toBe('Before I answer —')
  })

  it('Chart rebuilt since last turn → "The chart has been rebuilt — re-reading"', () => {
    expect(EDGE_STATE_LABELS.chart_rebuilt).toBe('The chart has been rebuilt — re-reading')
  })

  it('Network drop mid-turn, stage 1 → "Reconnecting…"', () => {
    expect(EDGE_STATE_LABELS.network_drop).toBe('Reconnecting…')
  })

  it('Network drop mid-turn, stage 2 (resumed) → "Resumed — nothing lost"', () => {
    expect(EDGE_STATE_LABELS.network_resumed).toBe('Resumed — nothing lost')
  })

  it('Provider overloaded / rate-limited → "The model is busy — retrying"', () => {
    expect(EDGE_STATE_LABELS.provider_busy).toBe('The model is busy — retrying')
  })

  it('Timeout (at 20s, pre-hard-limit) → "Taking longer than usual…"', () => {
    expect(EDGE_STATE_LABELS.timeout_20s).toBe('Taking longer than usual…')
  })

  it('Cost/coverage cap trips (partial) → "Served within limits — ⟨n⟩ of ⟨m⟩ steps"', () => {
    expect(renderCappedPartialLabel(3, 8)).toBe('Served within limits — 3 of 8 steps')
    expect(renderCappedPartialLabel(9, 9)).toBe('Served within limits — 9 of 9 steps')
  })

  it('User presses Stop → "Stopped — kept what arrived"', () => {
    expect(EDGE_STATE_LABELS.user_stopped).toBe('Stopped — kept what arrived')
  })

  it('Mid-turn model switch requested → "Will switch to ⟨model⟩ next turn"', () => {
    expect(renderModelSwitchQueuedLabel('Opus')).toBe('Will switch to Opus next turn')
    expect(renderModelSwitchQueuedLabel('Gemini 3 Pro')).toBe('Will switch to Gemini 3 Pro next turn')
  })

  it('Queue wait (busy instrument) → "In line — starts in a moment"', () => {
    expect(EDGE_STATE_LABELS.queue_wait).toBe('In line — starts in a moment')
  })

  it('the closed vocabulary has exactly the eleven EdgeStateKeys §7.8 defines (no silent additions/removals)', () => {
    const staticKeys = Object.keys(EDGE_STATE_LABELS).sort()
    const expectedStaticKeys: Exclude<EdgeStateKey, 'capped_partial' | 'model_switch_queued'>[] = [
      'chart_rebuilt',
      'clarification_needed',
      'network_drop',
      'network_resumed',
      'open_prediction_window',
      'provider_busy',
      'queue_wait',
      'timeout_20s',
      'user_stopped',
    ]
    expect(staticKeys).toEqual([...expectedStaticKeys].sort())
  })
})
