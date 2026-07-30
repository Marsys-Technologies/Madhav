/**
 * synthesis/surface_gateway.ts — the seam that composes FROM existing served surfaces
 * ====================================================================================
 * WP-1.4 constraint (HARD): the instrument does NOT re-implement ranking, queries, or the
 * envelope — it COMPOSES from the surfaces WP-1.3(a)/(g) + WP-1.2 already serve. This
 * gateway is that seam: a narrow interface the instrument depends on, with a default
 * implementation that calls the registered L2 capabilities' own handlers (single query
 * source — drift structurally impossible, per the D6 orchestrator precedent).
 *
 * Because the instrument depends on the INTERFACE (not the registry directly), unit tests
 * inject a fake gateway with controlled family sizes to prove budget-boundedness and ledger
 * resolvability without a live DB; the integration test uses the real RegistrySurfaceGateway.
 */

import { getCapability } from '../registry/index'
import type { Domain, LinkageCell, SignalExemplar } from './types'

// ── Gateway contract ──────────────────────────────────────────────────────────

export interface GestaltOrientation {
  /** domain → { signal_id, confidence, verdict_class } — the PRE-AGGREGATED verdict map. */
  verdict_map: Record<string, { signal_id: string; confidence: number; verdict_class: string }>
  central_question: Record<string, unknown> | null
  found: boolean
}

export interface FamilyDrill {
  /** The bounded, composite-ranked, text-hydrated exemplars for a domain family. */
  exemplars: SignalExemplar[]
  /** True family size (disclosed) — the honest total this bounded slice is drawn from. */
  total_in_family: number
  /** Pre-aggregated CDLM cross-domain cells bearing on this domain. */
  linkages: LinkageCell[]
}

export interface DispositorPath {
  path_id: string
  path_label: string | null
  path_strength: number | null
  is_final_dispositor: boolean
}

export interface TensionResult {
  contradiction_count: number
  contradictions: Array<Record<string, unknown>>
  note: string
}

/** The narrow surface the Large-N instrument composes from. */
export interface SurfaceGateway {
  gestalt(chartId: string, ayanamsha: string): Promise<GestaltOrientation>
  familyDrill(chartId: string, ayanamsha: string, domain: Domain, cap: number): Promise<FamilyDrill>
  dispositorPaths(chartId: string, ayanamsha: string, cap: number): Promise<DispositorPath[]>
  tension(chartId: string, ayanamsha: string): Promise<TensionResult>
}

// ── Default implementation — calls the registered L2 capability handlers ───────

function asRecord(content: unknown): Record<string, unknown> {
  return typeof content === 'object' && content !== null ? (content as Record<string, unknown>) : {}
}

export class RegistrySurfaceGateway implements SurfaceGateway {
  async gestalt(chartId: string, ayanamsha: string): Promise<GestaltOrientation> {
    const cap = getCapability('marsys://tool/L2/query_chart_gestalt')
    if (!cap) return { verdict_map: {}, central_question: null, found: false }
    try {
      const res = await cap.handler({ chart_id: chartId, ayanamsha_id: ayanamsha, limit: 1 }, { chart_id: chartId })
      const data = asRecord(res.content)
      const rows = (data['rows'] as Array<Record<string, unknown>>) ?? []
      const row = rows[0]
      if (!row) return { verdict_map: {}, central_question: null, found: false }
      const vmRaw = (row['domain_verdict_map_jsonb'] as Record<string, unknown>) ?? {}
      const verdict_map: GestaltOrientation['verdict_map'] = {}
      for (const [domain, v] of Object.entries(vmRaw)) {
        const o = asRecord(v)
        // SAMĀPTI B-N8-FIX / Ruling 76: bo_chart_gestalt no longer STORES a verdict —
        // post-fix rows carry a pointer + whole-domain evidence counts only. Keeping
        // signal_id populated for such a row would satisfy instrument.ts's
        // `verdict && verdict.signal_id` guard and render a fabricated
        // "…is unknown (confidence 0)". Emptying it routes that guard to its existing
        // honest-empty branch. Rows in the old/full shape (verdict_class present) are
        // unaffected.
        const hasVerdict = o['verdict_class'] != null && String(o['verdict_class']).length > 0
        verdict_map[domain] = {
          signal_id: hasVerdict ? String(o['signal_id'] ?? '') : '',
          confidence: Number(o['confidence'] ?? 0),
          verdict_class: String(o['verdict_class'] ?? 'unknown'),
        }
      }
      return {
        verdict_map,
        central_question: (row['central_question_jsonb'] as Record<string, unknown>) ?? null,
        found: true,
      }
    } catch {
      return { verdict_map: {}, central_question: null, found: false }
    }
  }

  async familyDrill(chartId: string, ayanamsha: string, domain: Domain, cap: number): Promise<FamilyDrill> {
    const readingCap = getCapability('marsys://tool/L2/query_domain_reading')
    if (!readingCap) return { exemplars: [], total_in_family: 0, linkages: [] }
    try {
      const res = await readingCap.handler(
        { chart_id: chartId, ayanamsha_id: ayanamsha, domain, max_signal_refs: cap },
        { chart_id: chartId },
      )
      const data = asRecord(res.content)

      // ranked_signals is the domain-DISCRIMINATED, composite-ranked, text-hydrated surface
      // (WP-1.2β / LCA-14) — the right exemplar source (not the domain-agnostic global order).
      const ranked = (data['ranked_signals'] as Array<Record<string, unknown>>) ?? []
      const refs = (data['signal_refs'] as Array<Record<string, unknown>>) ?? []
      const src = ranked.length > 0 ? ranked : refs

      const exemplars: SignalExemplar[] = src.slice(0, cap).map(r => ({
        signal_id: String(r['signal_id'] ?? ''),
        headline: (r['headline'] ?? r['signal_headline_text'] ?? null) as string | null,
        summary: (r['summary'] ?? r['signal_summary_text'] ?? r['rationale'] ?? null) as string | null,
        salience: r['computed_salience'] != null ? Number(r['computed_salience']) : null,
        constituent_fact_ids: Array.isArray(r['constituent_facts_array'])
          ? (r['constituent_facts_array'] as string[])
          : [],
      })).filter(e => e.signal_id.length > 0)

      // Disclosed total — prefer the surface's own disclosed count of the family.
      const total_in_family = Number(
        data['signal_id_refs_total'] ?? data['total_matching_filters'] ?? exemplars.length,
      )

      const cells = (data['cdlm_cells'] as Array<Record<string, unknown>>) ?? []
      const linkages: LinkageCell[] = cells.map(c => ({
        domain_row: String(c['domain_row'] ?? ''),
        domain_col: String(c['domain_col'] ?? ''),
        shared_signal_count: Number(c['shared_signal_count'] ?? 0),
        linkage_strength: c['computed_linkage_strength'] != null ? Number(c['computed_linkage_strength']) : null,
        contradiction_flag: Boolean(c['cross_domain_contradiction_flag'] ?? false),
      }))

      return { exemplars, total_in_family, linkages }
    } catch {
      return { exemplars: [], total_in_family: 0, linkages: [] }
    }
  }

  async dispositorPaths(chartId: string, ayanamsha: string, cap: number): Promise<DispositorPath[]> {
    const pathCap = getCapability('marsys://tool/L2/query_cgm_paths')
    if (!pathCap) return []
    try {
      const res = await pathCap.handler(
        { chart_id: chartId, ayanamsha_id: ayanamsha, limit: cap },
        { chart_id: chartId },
      )
      const data = asRecord(res.content)
      const rows = (data['rows'] as Array<Record<string, unknown>>) ?? []
      return rows.slice(0, cap).map(r => ({
        path_id: String(r['path_id'] ?? ''),
        path_label: (r['path_label_human'] ?? null) as string | null,
        path_strength: r['path_strength'] != null ? Number(r['path_strength']) : null,
        is_final_dispositor: Boolean(r['is_final_dispositor'] ?? false),
      }))
    } catch {
      return []
    }
  }

  async tension(chartId: string, ayanamsha: string): Promise<TensionResult> {
    const cap = getCapability('marsys://tool/L2/query_contradictions')
    if (!cap) return { contradiction_count: 0, contradictions: [], note: 'query_contradictions not registered.' }
    try {
      const res = await cap.handler({ chart_id: chartId, ayanamsha_id: ayanamsha }, { chart_id: chartId })
      const data = asRecord(res.content)
      const contradictions = (data['contradictions'] as Array<Record<string, unknown>>) ?? []
      return {
        contradiction_count: contradictions.length,
        contradictions: contradictions.slice(0, 10),
        note: String(data['graceful_empty_note'] ?? ''),
      }
    } catch {
      return { contradiction_count: 0, contradictions: [], note: 'tension query failed (graceful-empty).' }
    }
  }
}
