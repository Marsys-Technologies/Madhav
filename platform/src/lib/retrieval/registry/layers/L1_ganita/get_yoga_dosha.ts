/**
 * L1 retrieval: yoga and dosha firings
 * Covers: yoga_fires, yoga_label, dosha_fires, dosha_label, bhadra_flag, panchaka_flag
 * Tool: marsys://tool/L1/get_yoga_dosha
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const YD_CATEGORIES = ['yoga_fires', 'yoga_label', 'dosha_fires', 'dosha_label', 'bhadra_flag', 'panchaka_flag']

// R5.3 B2 (Q9-N-1 ruling item B): `facet` was accepted on this URI's args (register_p1_ganita.ts's
// ganita_structural_get always passes it) but silently ignored — every facet routed through
// get_yoga_dosha (parivartana/yoga_fires/dosha_fires/graha_yuddha) returned the identical
// unfiltered ~530-row union of all 6 categories. This map scopes the two facets that DO have a
// clean 1:1 category grouping in this tool (yoga_fires→yoga rows, dosha_fires→dosha rows);
// parivartana/graha_yuddha are pre-existing routing mismatches (their real data lives in
// get_dispositors/get_graha_yuddha) and are out of scope for this bounded fix.
const FACET_TO_TYPE: Record<string, 'yoga' | 'dosha' | 'flag'> = {
  yoga_fires: 'yoga',
  dosha_fires: 'dosha',
}

export const getYogaDoshaCapability: CapabilityDescriptor = {
  uri: 'marsys://tool/L1/get_yoga_dosha',
  type: 'tool',
  layer: 'L1',
  name: 'get_yoga_dosha',
  description:
    'Retrieve yoga and dosha data for a chart: yoga_fires (predicate firings with activating factors), ' +
    'yoga_label (canonical name and tradition), dosha_fires (affliction firings), dosha_label, ' +
    'bhadra_flag, and panchaka_flag. ' +
    'Every yoga/dosha firing carries its constituent grahas and fact_id for Bodha back-reference. ' +
    'Weak-tail signals (low-salience yogas) are included — strength is a column, not a gate. ' +
    'Covers 6 fact_categories. A3/CR-92/R-3: also returns firings_pointer (a genuine ' +
    'ga_yoga_firings fired-count for this chart/ayanamsha — that table, served via ' +
    'get_yoga_firings/ganita_yoga_firings_get, is firings-authoritative; this tool\'s rows are ' +
    'single-pass catalog matches, JL-004) and catalog_only_rows_in_page (count of rows whose ' +
    'fire_reason is requires_pass — not yet cross-verified confirmed firings). ' +
    'B9 dosha gate (D-1.5b, mirrors the get_yoga_firings all=true pattern): dosha_label rows whose ' +
    'fire_reason is requires_pass (shared-stub/catalog-only, not a confirmed per-chart finding) are ' +
    'EXCLUDED from the default page — pass all=true to include them.',
  input_schema: {
    chart_id:     { type: 'string', description: 'Chart UUID', required: true },
    ayanamsha_id: { type: 'string', description: 'Filter by ayanamsha. Omit for all.' },
    type:         { type: 'string', description: 'yoga | dosha | flag. Omit for all.', enum: ['yoga', 'dosha', 'flag'] },
    categories:   { type: 'array',  description: 'Subset of categories.', items: { type: 'string' } },
    facet:        { type: 'string', description: "Structural facet alias from ganita_structural_get " +
      "('yoga_fires' | 'dosha_fires' scope categories; other facet values are ignored here)." },
    all:          { type: 'boolean', description: 'B9 dosha gate: if true, include catalog-only ' +
      'dosha_label rows (fire_reason=requires_pass) that are excluded by default. Default false.' },
    offset: { type: 'number', default: 0 },
    limit:  { type: 'number', default: 500 },
  },
  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'flat_fact',
  traversal_level: 'L-SIGNAL',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: true },
  lel_capable: false,
  // PB-1/S-2: reader-facing working-band label — closed lexicon, never a bespoke string.
  register: { reader_label: 'Consulting the chart — Yogas, cross-checked' },
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 88, always_include: false },
  },
  // Lane 5 (§N.6 (iv), Doctrine Campaign D-1 Night-1): backs ganita_structural_get
  // (facet=yoga_fires/dosha_fires) and ganita_yogas_get — both Lane-3-touched surfaces.
  density_contract: {
    paginated: true,
    facets: ['type', 'categories', 'facet', 'all'],
    // W3 "One Envelope" (2026-07-20): was `false` with a "not yet added" note — the
    // handler below now sets `content.empty_reason` whenever `total === 0`, naming the
    // exact filter combination (categories/type/ayanamsha_id) that matched no rows,
    // so an honest zero-row page is never indistinguishable from an unfiltered miss.
    empty_reason: true,
  },
  async handler(args, _ctx) {
    try {
      const chartId    = args.chart_id as string
      const limit      = Math.min((args.limit as number) ?? 500, 2000)
      const offset     = (args.offset as number) ?? 0
      const facet      = args.facet as string | undefined
      const type       = (args.type as string | undefined) ?? (facet ? FACET_TO_TYPE[facet] : undefined)
      const all        = args.all === true

      let categories = (args.categories as string[]) ?? YD_CATEGORIES
      if (type === 'yoga')  categories = categories.filter(c => c.startsWith('yoga') || c === 'bhadra_flag')
      if (type === 'dosha') categories = categories.filter(c => c.startsWith('dosha'))
      if (type === 'flag')  categories = categories.filter(c => c.endsWith('_flag'))

      // Base filter params — shared by the COUNT query and the paged SELECT below, so
      // `total` (D5 coverage receipt — family size, envelope.ts buildCoverageStamp)
      // genuinely reflects the SAME filter conditions the page was drawn from, not a
      // re-guess or the page length mislabeled as the family size (the prior bug here).
      const baseParams: unknown[] = [chartId, categories]
      let whereClause = `chart_id = $1 AND fact_category = ANY($2::text[])`
      if (args.ayanamsha_id) {
        baseParams.push(args.ayanamsha_id as string)
        whereClause += ` AND ayanamsha_id = $${baseParams.length}`
      }
      // B9 dosha gate (D-1.5b — mirrors get_yoga_firings.ts's `all` pattern): a shared-stub
      // dosha_label row (fire_reason=requires_pass — a catalog/label match, not a cross-verified
      // per-chart finding) is NEVER served in the default page. `all=true` lifts the gate. This
      // is applied IN SQL (not a post-fetch filter) so `total`/pagination stay consistent with
      // what is actually served.
      const doshaGateClause =
        `NOT (fact_category = 'dosha_label' AND (fact_value_jsonb->>'fire_reason') = 'requires_pass')`
      if (!all) {
        whereClause += ` AND ${doshaGateClause}`
      }

      // A3 (CR-92 residue, R-3): ga_yoga_firings is the firings-authoritative table (per-yoga
      // strength, bhaṅga/cancellation state, partial-formation %, dāśā-activation) — this tool's
      // own chart_facts yoga_label/dosha_label rows are single-pass catalog matches (JL-004),
      // NOT a substitute. Rather than silently under-report families like Dhana/Raja Yoga that
      // fire in ga_yoga_firings but were never a strong chart_facts yoga_label presence, serve a
      // first-class pointer + a genuine COUNT(*) of what's actually fired there — zero new
      // computation (B.10), same bounded-query discipline as the total/count query above.
      const firingsParams: unknown[] = [chartId]
      let firingsWhere = `chart_id = $1 AND fired = true`
      if (args.ayanamsha_id) {
        firingsParams.push(args.ayanamsha_id as string)
        firingsWhere += ` AND ayanamsha_id = $${firingsParams.length}`
      }

      // B9 dosha gate honesty receipt: how many dosha_label/requires_pass rows this same
      // chart/ayanamsha/category filter is currently withholding by default (0 when all=true,
      // since the gate clause isn't applied to whereClause in that case).
      const gatedCountParams: unknown[] = [chartId, categories]
      let gatedCountWhere = `chart_id = $1 AND fact_category = ANY($2::text[]) AND NOT (${doshaGateClause})`
      if (args.ayanamsha_id) {
        gatedCountParams.push(args.ayanamsha_id as string)
        gatedCountWhere += ` AND ayanamsha_id = $${gatedCountParams.length}`
      }

      const [countResult, result, firingsCountResult, doshaGatedCountResult] = await Promise.all([
        query<{ total: string }>(
          `SELECT COUNT(*)::text AS total FROM chart_facts WHERE ${whereClause}`,
          baseParams,
        ),
        query<Record<string, unknown>>(
          `SELECT fact_id, fact_category, fact_subject, ayanamsha_id, fact_key, fact_value_num,
                  fact_value_text, fact_value_jsonb, unit, verification_pass_status, citation_ref
           FROM chart_facts
           WHERE ${whereClause}
           ORDER BY fact_category, ayanamsha_id, fact_key
           LIMIT $${baseParams.length + 1} OFFSET $${baseParams.length + 2}`,
          [...baseParams, limit, offset],
        ),
        query<{ total: string }>(
          `SELECT COUNT(*)::text AS total FROM ga_yoga_firings WHERE ${firingsWhere}`,
          firingsParams,
        ),
        query<{ total: string }>(
          `SELECT COUNT(*)::text AS total FROM chart_facts WHERE ${gatedCountWhere}`,
          gatedCountParams,
        ),
      ])

      const total = Number(countResult.rows[0]?.total ?? 0)
      const doshaLabelGatedTotal = Number(doshaGatedCountResult.rows[0]?.total ?? 0)
      const firingsFiredTotal = Number(firingsCountResult.rows[0]?.total ?? 0)
      const firingsPointer = {
        tool: 'ganita_yoga_firings_get',
        table: 'ga_yoga_firings',
        fired_count: firingsFiredTotal,
        note:
          'ga_yoga_firings is the firings-authoritative source for this chart/ayanamsha — per-yoga ' +
          'strength scoring, bhaṅga (cancellation) state, partial-formation %, and dāśā-activation. ' +
          "This tool's yoga_label/dosha_label rows are single-pass catalog matches (JL-004); cross-" +
          'check against ganita_yoga_firings_get before asserting a yoga did or did not fire.',
      }

      // B9-preview (1-line presentation guard; full gating is D-1.5b's job): rows whose
      // fire_reason is 'requires_pass' are catalog/label matches awaiting cross-verification, not
      // confirmed findings — they still serve (never silently dropped), but are counted separately
      // so a caller doesn't read the raw row count as "N confirmed yogas/doshas".
      const catalogOnlyCount = (result.rows ?? []).filter(r => {
        const v = r['fact_value_jsonb'] as { fire_reason?: string } | null
        return v?.fire_reason === 'requires_pass'
      }).length

      // R5.3 B2 (Q9-N-1 ruling item C, updated D-1.6 Lane S-2/CR-74): the dosha_label catalog
      // row for "Kala Sarpa Dosha" is now wired directly to the SAME genuinely-computed
      // `_detect_kala_sarpa` function this writer already runs per-varga (`ga_structural_writer.
      // _detect_kala_sarpa_dosha`, on the D1 varga only — CR-74's "no second detector, wire the
      // label to the existing computed fact") — the two are consistent by construction on any
      // fresh build, not by a serve-time coincidence. This block still surfaces the raw
      // `kala_sarpa_per_varga` rows (fetched only via facet=dosha_fires, unchanged bounded
      // zero-new-computation SELECT) AND now adds an explicit `kala_sarpa_reconciliation` check
      // below (Gate Ś item 4 assertion surface) — a live agreement receipt, not just a
      // side-by-side pointer, so any future regression in the wiring is caught at serve time
      // rather than silently trusted.
      let kalaSarpaPerVarga: { natal: Record<string, unknown>[]; divisional_fired: Record<string, unknown>[] } | undefined
      if (facet === 'dosha_fires') {
        const ksParams: unknown[] = [chartId]
        let ksWhere = `chart_id = $1 AND fact_category = 'kala_sarpa_per_varga' AND fact_key = 'ks_detection'`
        if (args.ayanamsha_id) {
          ksParams.push(args.ayanamsha_id as string)
          ksWhere += ` AND ayanamsha_id = $${ksParams.length}`
        }
        const ksResult = await query<Record<string, unknown>>(
          `SELECT fact_id, ayanamsha_id, fact_value_jsonb, fact_value_text, verification_pass_status, citation_ref
           FROM chart_facts WHERE ${ksWhere}
           ORDER BY ayanamsha_id, (fact_value_jsonb->>'varga')`,
          ksParams,
        )
        const ksRows = ksResult.rows ?? []
        const natal = ksRows.filter(r => (r['fact_value_jsonb'] as { varga?: string } | null)?.varga === 'D1')
        const divisional_fired = ksRows.filter(r => {
          const v = r['fact_value_jsonb'] as { varga?: string; fires?: boolean } | null
          return v?.varga !== 'D1' && v?.fires === true
        })
        kalaSarpaPerVarga = { natal, divisional_fired }
      }

      // D-1.6 Lane S-2 item (c): a live agreement receipt between the served dosha_label
      // "kala_sarpa" row and the D1 kala_sarpa_per_varga computed fact — the label row must
      // NEVER contradict the per-varga authoritative verdict. Computed only when both sides are
      // actually in view (facet=dosha_fires so kalaSarpaPerVarga was fetched, and the current
      // page includes the dosha_label row) — a null verdict on either side is an honest
      // "not_checked_this_call", never a fabricated agreement.
      let kalaSarpaReconciliation: Record<string, unknown> | undefined
      if (kalaSarpaPerVarga) {
        const doshaLabelRow = (result.rows ?? []).find(
          r => r['fact_category'] === 'dosha_label' && r['fact_subject'] === 'kala_sarpa',
        )
        const doshaLabelFires = doshaLabelRow
          ? ((doshaLabelRow['fact_value_jsonb'] as { fires?: boolean | null } | null)?.fires ?? null)
          : null
        const perVargaD1 = kalaSarpaPerVarga.natal[0]
        const perVargaFires = perVargaD1
          ? ((perVargaD1['fact_value_jsonb'] as { fires?: boolean } | null)?.fires ?? null)
          : null
        // dosha_label omits the row entirely when the bespoke detector returns "does not form"
        // (honest absence, not a stub — see ga_structural_writer._detect_kala_sarpa_dosha) — so
        // "no row served" + "per-varga D1 fires=false" IS agreement, not a gap.
        const effectiveDoshaLabelFires = doshaLabelRow ? doshaLabelFires : (perVargaFires === false ? false : null)
        const agrees = perVargaFires === null || effectiveDoshaLabelFires === null
          ? null
          : perVargaFires === effectiveDoshaLabelFires
        kalaSarpaReconciliation = {
          dosha_label_row_served: !!doshaLabelRow,
          dosha_label_fires: effectiveDoshaLabelFires,
          per_varga_d1_fires: perVargaFires,
          agrees,
          note: agrees === null
            ? 'per-varga D1 fact not resolved this call — cannot check agreement.'
            : agrees
              ? 'dosha_label kala_sarpa verdict agrees with the computed kala_sarpa_per_varga D1 fact.'
              : 'CONTRADICTION: dosha_label kala_sarpa verdict disagrees with kala_sarpa_per_varga D1 ' +
                '— per CLAUDE.md §N.5, the L1 computed fact is authoritative; this indicates a build ' +
                'regression in ga_structural_writer._detect_kala_sarpa_dosha, not a data-quality choice.',
        }
      }

      // W3 "One Envelope" (density_contract.empty_reason implementation, CLAUDE.md §N.6
      // point 3 / B.10): a genuinely-empty page must say WHY, not ship a silent `[]`.
      // Named against the SAME whereClause the total/page queries above were drawn
      // from, so this never drifts from what was actually filtered.
      const empty_reason = total === 0
        ? `No chart_facts rows match categories=[${categories.join(', ')}]` +
          (args.type ? ` type='${String(args.type)}'` : '') +
          (args.ayanamsha_id ? ` ayanamsha_id='${String(args.ayanamsha_id)}'` : '') +
          ` for chart ${chartId}.`
        : undefined

      return {
        content: {
          chart_id: chartId, categories, rows: result.rows ?? [], total,
          ...(empty_reason ? { empty_reason } : {}),
          firings_pointer: firingsPointer,
          catalog_only_rows_in_page: catalogOnlyCount,
          dosha_label_gate: {
            applied: !all,
            all,
            excluded_total: all ? 0 : doshaLabelGatedTotal,
            note: all
              ? 'all=true — catalog-only dosha_label rows (fire_reason=requires_pass) are included in this response.'
              : doshaLabelGatedTotal > 0
                ? `${doshaLabelGatedTotal} shared-stub dosha_label row(s) (fire_reason=requires_pass, ` +
                  'catalog-only — not a cross-verified per-chart finding) are excluded from this ' +
                  'default page (B9 dosha gate). Pass all=true to include them.'
                : 'No shared-stub dosha_label rows matched this filter — nothing was gated.',
          },
          ...(catalogOnlyCount > 0 ? {
            catalog_only_note:
              `${catalogOnlyCount} of ${(result.rows ?? []).length} row(s) in this page are ` +
              "catalog_only/requires_pass — single-pass label matches (JL-004), not yet " +
              'cross-verified confirmed firings. Do not present them as settled findings; see ' +
              'ganita_yoga_firings_get for cross-verified detection detail.',
          } : {}),
          ...(kalaSarpaPerVarga ? { kala_sarpa_per_varga: kalaSarpaPerVarga } : {}),
          ...(kalaSarpaReconciliation ? { kala_sarpa_reconciliation: kalaSarpaReconciliation } : {}),
        },
        is_error: false,
      }
    } catch (err) {
      return { content: String(err), is_error: true }
    }
  },
}
