/**
 * query_pratijna — L2 Bodha promise/denial ledger serving surface
 * ================================================================
 * WP-1.3j / F-0156,0176 (W1-FOLLOWUP). Serves bodha_pratijna — the per-event-class
 * "what the chart promises / denies" adjudication (110 rows/chart) that was computed
 * and stored but had NO MCP serving path. Read-only, bounded.
 *
 * §N.5: supporting_signal_ids / contradicting_signal_ids REFERENCE upstream signal
 * ids (emits_references) — this tool never restates their derived values.
 *
 * PRATIJÑĀ v4 (Lane B4 consumer audit, 2026-08-09): the v4.0 bo_pratijna engine
 * NEVER populates supporting_signal_ids / contradicting_signal_ids (it never reads
 * bodha_msr_signals at all — see bo_pratijna.py's module docstring); they are always
 * NULL now, not "reference ids to resolve via query_signals." The row's real
 * classical evidence lives in `derivation.factor_ledger` / `derivation.weights`
 * instead. Also: `status = 'no_evidence'` no longer means "zero supporting/
 * contradicting signals matched" (that was v3's meaning) — under v4 it means "no
 * KARYATVA_REGISTRY entry exists for this event_class_id" (a defensive path that
 * should not fire now that the registry covers all 27 classes; a v4 row with
 * genuinely weak/absent classical evidence gets status='denied' instead, not
 * 'no_evidence'). Both the static description and the dynamic
 * `no_evidence_qualification` string below were updated to state this honestly
 * (§N.7 narration fidelity — a stale claim about what a served field means is the
 * same defect class as a stale computed value).
 */
import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

const MAX_LIMIT = 50

export const queryPratijnaCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L2/query_pratijna',
  type:  'tool',
  layer: 'L2',
  name:  'query_pratijna',

  description: [
    'Retrieve the chart pratijna (promise / denial) ledger from bodha_pratijna — one adjudicated',
    'row per event_class: status (promised | denied | conditional | no_evidence), grade, varga_confirmation,',
    'and a derivation (bo_pratijna v4.0: a factor ledger of classical significators, weights, and denial',
    'checks — the row\'s real evidence). Filters: ayanamsha_id, status, event_class_id. Bounded (LIMIT ≤50)',
    'with a disclosed total + offset pagination.',
    'supporting_signal_ids / contradicting_signal_ids are always NULL under the v4 engine (it does not use',
    'MSR-signal matching); no_evidence rows now mean "no karyatva registry entry for this event class" (a',
    'defensive case, not "zero signals") — their grade is NULL (not scored), served honestly per R6/R8, not',
    'gated or fabricated.',
  ].join(' '),

  input_schema: {
    chart_id:       { type: 'string', description: 'Chart UUID. Required.', required: true },
    ayanamsha_id:   { type: 'string', description: "Filter by ayanamsha. Omit for all." },
    status:         { type: 'string', description: "Filter by status ('promised' | 'denied' | 'conditional' | 'no_evidence'). Omit for all." },
    event_class_id: { type: 'string', description: 'Filter by event_class_id. Omit for all.' },
    limit:          { type: 'number', description: `Max rows (default ${MAX_LIMIT}, max ${MAX_LIMIT}).` },
    offset:         { type: 'number', description: 'Pagination offset (default 0).' },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'rich_relational',
  traversal_level: 'L-DOMAIN',
  tool_role: 'leaf',
  emits_references: true,
  grounds_to: { l1_fact_ids: false },
  lel_capable: false,
  llm_hints: {
    agentic: { cost_class: 'cheap', cacheable: true },
    bulk_context: { pre_fetch_priority: 55, always_include: false },
  },
  // L7-SERVING (ŚABDA-ŚUDDHI): density_contract discloses paginated behaviour,
  // the facets callers can filter on, and the honest empty condition.
  // empty_reason=true: the handler never silently returns empty — it always serves
  // the honest row count including no_evidence rows and sets no_evidence_qualification.
  density_contract: {
    paginated: true,
    facets: ['status', 'ayanamsha_id', 'event_class_id'],
    empty_reason: true,
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) return { content: { error: 'chart_id is required' }, is_error: true }

    const ayanamsha_id = args['ayanamsha_id'] ? String(args['ayanamsha_id']) : null
    const status = args['status'] ? String(args['status']) : null
    const event_class_id = args['event_class_id'] ? String(args['event_class_id']) : null
    const limit = Math.min(Math.max(Number(args['limit'] ?? MAX_LIMIT), 1), MAX_LIMIT)
    const offset = Math.max(Number(args['offset'] ?? 0), 0)

    const filters: string[] = ['chart_id = $1']
    const params: unknown[] = [chart_id]
    let p = 2
    if (ayanamsha_id)   { filters.push(`ayanamsha_id = $${p++}`);   params.push(ayanamsha_id) }
    if (status)         { filters.push(`status = $${p++}`);         params.push(status) }
    if (event_class_id) { filters.push(`event_class_id = $${p++}`); params.push(event_class_id) }
    const where = filters.join(' AND ')

    const sql = `
      SELECT pratijna_id, ayanamsha_id, event_class_id, status, grade,
             varga_confirmation, supporting_signal_ids, contradicting_signal_ids,
             derivation, formula_version,
             to_char(computed_at, 'YYYY-MM-DD') AS computed_date
      FROM bodha_pratijna
      WHERE ${where}
      ORDER BY event_class_id, ayanamsha_id
      LIMIT $${p} OFFSET $${p + 1}`

    try {
      const [rowsRes, countRes] = await Promise.all([
        query(sql, [...params, limit, offset]),
        query<{ total: string }>(`SELECT COUNT(*)::text AS total FROM bodha_pratijna WHERE ${where}`, params),
      ])
      const total_matching = Number(countRes.rows[0]?.total ?? 0)
      // L7-SERVING (ŚABDA-ŚUDDHI): count no_evidence rows and disclose them explicitly
      // so callers can distinguish adjudicated verdicts from evidence-free placeholders.
      const noEvidenceCount = (rowsRes.rows as Array<Record<string, unknown>>).filter(
        (r) => r['status'] === 'no_evidence'
      ).length
      const no_evidence_qualification = noEvidenceCount > 0
        ? `${noEvidenceCount} of ${rowsRes.rows.length} row(s) have status 'no_evidence' — under the v4.0 engine this means no karyatva registry entry exists for that event class (a defensive case; it should not occur for any of the 27 standard classes). Their grade is NULL (not scored). They are served honestly (R6, R8) but should not be treated as assessed verdicts.`
        : null
      return {
        content: {
          chart_id,
          rows: rowsRes.rows,
          count: rowsRes.rows.length,
          total_matching,
          more_available: offset + rowsRes.rows.length < total_matching,
          no_evidence_qualification,
          filters: { ayanamsha_id, status, event_class_id, limit, offset },
          reference_note: 'supporting_signal_ids / contradicting_signal_ids are always NULL under the v4.0 engine (it does not match bodha_msr_signals) — the real classical evidence for a row is derivation.factor_ledger / derivation.weights, served inline above.',
          provenance: { tables: ['bodha_pratijna'], source: 'L2 Bodha pratijna ledger; served chart-scoped, budgeted.' },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
