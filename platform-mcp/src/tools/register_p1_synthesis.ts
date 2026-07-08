/**
 * P1 Group 3 — Synthesis-adjacent surface tools (3 tools)
 * =========================================================
 * Exposes L5 Mīmāṃsā, L2 Bodha, and L3 Kāla capabilities
 * that existed in the registry but were NOT previously MCP-exposed.
 * Per BA-P1 brief §Step 3.
 *
 * mimamsa_insight_get  → marsys://tool/L5/query_insights (PD-1: 14 rows, STRUCTURAL mode)
 * bodha_discoveries_get → bodha_discoveries table (acharya-grade cross-domain observations)
 * kala_life_arc_get    → marsys://tool/L3/query_life_arc (kala_jivana_parva biographical parvas)
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { z } from 'zod'

const PLATFORM_URL = (process.env['PLATFORM_URL'] ?? 'http://localhost:3000').replace(/\/$/, '')
const MCP_INTERNAL_TOKEN = process.env['MCP_INTERNAL_TOKEN'] ?? ''

async function callRegistryCapability(uri: string, args: Record<string, unknown>): Promise<unknown> {
  const res = await fetch(`${PLATFORM_URL}/api/retrieval/capability`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-mcp-internal-token': MCP_INTERNAL_TOKEN },
    body: JSON.stringify({ uri, args }),
    signal: AbortSignal.timeout(20_000),
  })
  if (!res.ok) {
    const text = await res.text().catch(() => '')
    throw new Error(`[p1_synthesis] capability call failed (${res.status}): ${text.slice(0, 200)}`)
  }
  const data = await res.json() as { ok: boolean; content?: unknown; error?: string }
  if (!data.ok) throw new Error(`[p1_synthesis] capability error: ${data.error ?? 'unknown'}`)
  return data.content
}

async function platformQuery(sql: string, params: unknown[]): Promise<{ rows: Record<string, unknown>[] }> {
  const res = await fetch(`${PLATFORM_URL}/api/mcp/db/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'x-mcp-internal-token': MCP_INTERNAL_TOKEN },
    body: JSON.stringify({ sql, params }),
    signal: AbortSignal.timeout(15_000),
  })
  if (!res.ok) throw new Error(`[p1_synthesis] platform DB query failed: ${res.status}`)
  return res.json() as Promise<{ rows: Record<string, unknown>[] }>
}

function envelope(content: unknown, toolName: string, queryClass: string) {
  return {
    envelope_version: 'v1',
    tool: toolName,
    verdict: null,
    ranking_basis: null,
    grounding: { fact_ids: [], citations: [], grounding_score: null },
    pagination: { offset: 0, limit: 0, total: null, next_cursor: null },
    drill_pointers: [],
    judgment_flags: [],
    insight_type: null,
    query_class: queryClass,
    content,
  }
}

const DUAL_OUTPUT_TEXT_THRESHOLD_BYTES = 50_000

// S3 fix (R5 W0a perf lane): no pretty-print; text duplicate suppressed above
// threshold (structuredContent already carries the full payload).
function dualOutput(data: unknown) {
  const structuredContent = { type: 'object' as const, object: data }
  const json = JSON.stringify(data)
  if (Buffer.byteLength(json, 'utf8') > DUAL_OUTPUT_TEXT_THRESHOLD_BYTES) {
    return { structuredContent, content: [{ type: 'text' as const, text: '[large payload — see structuredContent]' }] }
  }
  return { structuredContent, content: [{ type: 'text' as const, text: json }] }
}

function errorOutput(tool: string, message: string, extra?: Record<string, unknown>) {
  return { ...dualOutput({ ok: false, error: message, tool, ...extra }), isError: true as const }
}

export function registerP1SynthesisTools(server: McpServer): void {

  // ── 1. mimamsa_insight_get ────────────────────────────────────────────────
  server.tool(
    'mimamsa_insight_get',
    'Retrieve L5 Mīmāṃsā insight units for a chart. ' +
    'Returns calibrated insight units from the mimamsa_insight_units table: ' +
    'calibrated outlooks (prediction→outcome match scores), manifestation-grammar learnings, ' +
    'emergent-law discoveries (pattern candidates from cross-chart mining), ' +
    'load-bearing conclusions (the chart\'s most consequential structural claims), ' +
    'and negative-knowledge statements (what this chart rules out). ' +
    'IMPORTANT: The system is in STRUCTURAL mode (L5 SEALED per BA build arc). ' +
    'calibration_status=\'prior_only\' — empirical scores populate as outcome data accrues. ' +
    'All units carry provenance chains back to L1 chart_facts.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      insight_type: z.enum([
        'calibrated_outlook', 'manifestation_grammar', 'emergent_law',
        'load_bearing', 'negative_knowledge', 'verdict_object',
      ]).optional().describe('Filter by insight type. Omit for all types.'),
      domain: z.string().optional().describe('Filter by life domain (career, health, relationship, wealth, etc.).'),
      min_rank: z.number().min(0).max(1).optional().describe('Minimum rank_consequence threshold (0..1, default: 0).'),
      top_k: z.number().int().min(1).max(200).optional().describe('Max insight units (default: 30, max: 200).'),
      include_negative_knowledge: z.boolean().optional()
        .describe('Include is_negative_knowledge=true rows (default: true).'),
    },
    async ({ chart_id, insight_type, domain, min_rank, top_k, include_negative_knowledge }) => {
      if (!chart_id) return errorOutput('mimamsa_insight_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L5/query_insights', {
          chart_id, insight_type, domain,
          min_rank: min_rank ?? 0,
          top_k: top_k ?? 30,
          include_negative_knowledge: include_negative_knowledge !== false,
        })
        const wrapped = {
          calibration_status: 'prior_only',
          mode: 'STRUCTURAL',
          note: 'L5 Mīmāṃsā is SEALED in STRUCTURAL mode. Empirical calibration accrues as outcome data is recorded.',
          ...(typeof data === 'object' && data ? data : { content: data }),
        }
        return dualOutput(envelope(wrapped, 'mimamsa_insight_get', 'synthesis_calibration'))
      } catch (err) {
        return errorOutput('mimamsa_insight_get', String(err), { chart_id })
      }
    }
  )

  // ── 2. bodha_discoveries_get ──────────────────────────────────────────────
  server.tool(
    'bodha_discoveries_get',
    'Retrieve acharya-grade cross-domain discoveries for a chart from L2 Bodha. ' +
    'Queries the bodha_discoveries table — the "Bimba" (image/reflection) layer of Bodha, ' +
    'which contains the system\'s highest-signal cross-domain observations: ' +
    'patterns that surface only when multiple L1 data streams are synthesized. ' +
    'Examples: Saturn-Ketu mutual aspect amplifying 8th house themes across D1+D9+D10; ' +
    'strong Atmakaraka-Arudha Pada relationship forecasting public prominence. ' +
    'Returns discovery_id, domain tags, supporting fact_ids, salience score, and narrative.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      domain:   z.string().optional().describe('Filter by life domain (career, health, relationship, wealth, etc.).'),
      min_salience: z.number().min(0).max(1).optional().describe('Minimum salience score (0..1, default: 0).'),
      limit:    z.number().int().min(1).max(200).optional().describe('Max results (default: 30, max: 200).'),
      offset:   z.number().int().min(0).optional().describe('Pagination offset (default: 0).'),
    },
    async ({ chart_id, domain, min_salience, limit, offset }) => {
      if (!chart_id) return errorOutput('bodha_discoveries_get', 'chart_id is required')
      try {
        const params: unknown[] = [chart_id]
        const filters: string[] = ['chart_id = $1']
        if (domain) { params.push(domain); filters.push(`domain = $${params.length}`) }
        if (min_salience != null && min_salience > 0) {
          params.push(min_salience); filters.push(`salience_score >= $${params.length}`)
        }
        params.push(limit ?? 30)
        params.push(offset ?? 0)
        const sql = `
          SELECT *
          FROM bodha_discoveries
          WHERE ${filters.join(' AND ')}
          ORDER BY salience_score DESC NULLS LAST
          LIMIT $${params.length - 1} OFFSET $${params.length}
        `
        const result = await platformQuery(sql, params)
        return dualOutput(envelope({
          discoveries: result.rows,
          total: result.rows.length,
          filters: { domain, min_salience },
          source_table: 'bodha_discoveries',
        }, 'bodha_discoveries_get', 'synthesis_cross_domain'))
      } catch (err) {
        return errorOutput('bodha_discoveries_get', String(err), { chart_id })
      }
    }
  )

  // ── 3. kala_life_arc_get ──────────────────────────────────────────────────
  server.tool(
    'kala_life_arc_get',
    'Retrieve the biographical life-arc (Jīvana Parva) for a chart from L3 Kāla. ' +
    'Returns the kala_jivana_parva view: the life divided into named biographical periods ' +
    '(Parvas) based on Vimshottari mahadasha + dasha-sequence logic. Each Parva covers ' +
    'a named life stage with its dominant dasha lord, expected thematic domain, ' +
    'start/end years (age-based), and cross-links to LEL events that fell within that Parva. ' +
    'Use as the temporal backbone for reading the native\'s life story.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      include_lel_events: z.boolean().optional()
        .describe('Include Life Event Log matches for each Parva (default: true).'),
      limit:   z.number().int().min(1).max(100).optional().describe('Max Parvas (default: 50).'),
      offset:  z.number().int().min(0).optional().describe('Pagination offset (default: 0).'),
    },
    async ({ chart_id, include_lel_events, limit, offset }) => {
      if (!chart_id) return errorOutput('kala_life_arc_get', 'chart_id is required')
      try {
        const data = await callRegistryCapability('marsys://tool/L3/query_life_arc', {
          chart_id,
          include_lel_events: include_lel_events !== false,
          limit: limit ?? 50,
          offset: offset ?? 0,
        })
        return dualOutput(envelope(data, 'kala_life_arc_get', 'temporal_life_arc'))
      } catch (err) {
        return errorOutput('kala_life_arc_get', String(err), { chart_id })
      }
    }
  )

  // ── 4. synth_tail_divergence_get ─────────────────────────────────────────
  server.tool(
    'synth_tail_divergence_get',
    'Retrieve the tail-divergence signals for a domain — the lowest-salience signals from L2 Bodha ' +
    'that contradict or diverge from the dominant synthesis reading. Per BA-P4 attention budget ' +
    '(70/20/10 head/dissent/tail), these are the "10% dissent" signals that surface minority positions. ' +
    'Use before anchoring high-confidence forecasts to surface contradicting evidence. ' +
    'Returns bodha_msr_signals rows in the bottom salience decile for the requested domain, ' +
    'with signal type, salience percentile, domains, and classical sources for audit.',
    {
      chart_id:  z.string().uuid().describe('Chart UUID. Required.'),
      domain:    z.string().optional().describe('Life domain filter (career, health, relationship, wealth, dharma, etc.). Omit for all domains.'),
      top_k:     z.number().int().min(1).max(50).optional().describe('Max tail signals to return (default: 10).'),
    },
    async ({ chart_id, domain, top_k }) => {
      if (!chart_id) return errorOutput('synth_tail_divergence_get', 'chart_id is required')
      try {
        const limitVal = top_k ?? 10
        const params: unknown[] = [chart_id, 'lahiri_chitrapaksha']
        const domainClause = domain
          ? `AND domains_affected_array && ARRAY[$${(params.push(domain), params.length)}::text]`
          : ''
        params.push(limitVal)
        const sql = `
          WITH ranked AS (
            SELECT signal_id, signal_type_id, computed_salience, tier,
                   domains_affected_array, classical_sources_array,
                   constituent_facts_array, valence,
                   PERCENT_RANK() OVER (
                     PARTITION BY chart_id, ayanamsha_id
                     ORDER BY computed_salience ASC NULLS LAST
                   ) AS salience_pctl
            FROM bodha_msr_signals
            WHERE chart_id = $1 AND ayanamsha_id = $2 ${domainClause}
          )
          SELECT * FROM ranked
          WHERE salience_pctl <= 0.10
          ORDER BY salience_pctl ASC
          LIMIT $${params.length}
        `
        const result = await platformQuery(sql, params)
        return dualOutput(envelope({
          tail_signals: result.rows,
          total: result.rows.length,
          divergence_memo:
            `${result.rows.length} tail-divergence signal(s) (bottom 10% salience) ` +
            `for chart ${chart_id}${domain ? ` / domain ${domain}` : ''}. ` +
            `Per BA-P4 attention budget 70/20/10: these form the dissent/tail tier. ` +
            `Review before anchoring high-confidence forecasts.`,
          filters: { domain, top_k: limitVal, ayanamsha: 'lahiri_chitrapaksha' },
          attention_budget_note: 'BA-P4: head=70%, dissent=20%, tail=10%. These signals occupy the tail=10%.',
        }, 'synth_tail_divergence_get', 'synthesis_tail_divergence'))
      } catch (err) {
        return errorOutput('synth_tail_divergence_get', String(err), { chart_id })
      }
    }
  )

  // ── 5. synth_chart_brief_get ──────────────────────────────────────────────
  server.tool(
    'synth_chart_brief_get',
    'Assemble the Mahā-Brief — a comprehensive chart synthesis across 38 canonical topic slots. ' +
    'Draws from L5 Mīmāṃsā insight_units (verdict_object + calibrated_outlook + load_bearing + ' +
    'negative_knowledge) and L2 Bodha discoveries. Covers: domain verdicts (career/health/' +
    'relationship/wealth/creativity/dharma/moksha), load-bearing conclusions, negative knowledge, ' +
    'tradition concordance overview, and calibration status. ' +
    'depth=standard: key verdicts only (38 topics). depth=deep: + evidence chains. ' +
    'depth=complete: + tail divergence + all tradition stacks. ' +
    'System is in STRUCTURAL mode (L5 SEALED) — empirical scores accrue as outcome data records.',
    {
      chart_id: z.string().uuid().describe('Chart UUID. Required.'),
      depth:    z.enum(['standard', 'deep', 'complete']).optional()
        .describe('Brief depth: standard (default), deep, or complete.'),
    },
    async ({ chart_id, depth = 'standard' }) => {
      if (!chart_id) return errorOutput('synth_chart_brief_get', 'chart_id is required')
      try {
        const topK = depth === 'complete' ? 200 : depth === 'deep' ? 80 : 38
        const insightResult = await platformQuery(`
          SELECT insight_id, insight_type, domain, question_lens,
                 statement, rank_consequence, confidence_band,
                 n_support, evidence_grade, is_negative_knowledge,
                 surface_formula_version
                 ${depth !== 'standard' ? ', provenance_chain' : ''}
          FROM mimamsa_insight_units
          WHERE chart_id = $1
          ORDER BY
            CASE insight_type
              WHEN 'verdict_object'     THEN 1
              WHEN 'load_bearing'       THEN 2
              WHEN 'calibrated_outlook' THEN 3
              WHEN 'emergent_law'       THEN 4
              WHEN 'negative_knowledge' THEN 5
              ELSE 6
            END,
            rank_consequence DESC NULLS LAST
          LIMIT $2
        `, [chart_id, topK])

        const discLimit = depth === 'complete' ? 20 : 5
        const discResult = await platformQuery(`
          SELECT discovery_id, domain, statement, salience_score, activation_status
          FROM bodha_discoveries
          WHERE chart_id = $1
          ORDER BY salience_score DESC NULLS LAST
          LIMIT $2
        `, [chart_id, discLimit])

        const rows = insightResult.rows
        const verdicts     = rows.filter(r => r['insight_type'] === 'verdict_object')
        const loadBearing  = rows.filter(r => r['insight_type'] === 'load_bearing')
        const calibrated   = rows.filter(r => r['insight_type'] === 'calibrated_outlook')
        const negKnowledge = rows.filter(r => r['is_negative_knowledge'])
        const domains      = [...new Set(verdicts.map(r => r['domain']).filter(Boolean))]

        const lbLimit  = depth === 'standard' ? 5  : 20
        const calLimit = depth === 'standard' ? 3  : 10
        const negLimit = depth === 'standard' ? 3  : 10

        const brief = {
          chart_id,
          depth,
          formula_version: 'mi_darshana_v1.0',
          calibration_mode: 'STRUCTURAL',
          calibration_note: 'L5 SEALED — empirical scores accrue as outcome data is recorded.',
          topics_covered: rows.length,
          domains_covered: domains,
          verdict_summary: verdicts,
          load_bearing_signals: loadBearing.slice(0, lbLimit),
          calibration_strata: calibrated.slice(0, calLimit),
          negative_knowledge: negKnowledge.slice(0, negLimit),
          top_discoveries: discResult.rows,
          attention_budget: {
            head:    '70% — top verdicts and load-bearing conclusions (this brief)',
            dissent: '20% — contradictions and conditional signals (synth_tail_divergence_get)',
            tail:    '10% — minority signals (synth_tail_divergence_get)',
          },
        }

        return dualOutput(envelope(brief, 'synth_chart_brief_get', 'synthesis_maha_brief'))
      } catch (err) {
        return errorOutput('synth_chart_brief_get', String(err), { chart_id })
      }
    }
  )

  // ── prashna_undertaking_get ───────────────────────────────────────────────
  // BA-P5B Step 3: Q4 undertaking recipe = prashna verdict × election scoring × fructification.
  // Reads ga_prashna_judgment (prashna chart), phala_muhurta (election windows for domain),
  // phala_anchors (fructification timing anchor), brahma_activity_ontology (rules).
  server.tool(
    'prashna_undertaking_get',
    'Q4 undertaking recipe: prashna (horary) verdict × muhurta election scoring × fructification timing. ' +
    'Provide the prashna chart_id (cast at question moment) and domain. ' +
    'Returns: horary verdict, best election windows, fructification anchor, composite undertaking score.',
    {
      chart_id:       z.string().uuid().describe('Prashna chart UUID (cast at question moment, not natal chart).'),
      domain:         z.string().describe('Undertaking domain (career | financial | relationship | health | spiritual | transition).'),
      top_windows:    z.number().int().min(1).max(10).default(3).describe('Number of top election windows to return.'),
    },
    async ({ chart_id, domain, top_windows }) => {
      try {
        // 1. Prashna judgment (from ga_prashna_judgment)
        const prashnaResult = await platformQuery(`
          SELECT gj.question_class, gj.verdict, gj.verdict_strength, gj.ayanamsha_id,
                 gj.significator_positions, gj.timing_indication, gj.classical_citations
          FROM ga_prashna_judgment gj
          WHERE gj.chart_id = $1
          ORDER BY gj.ayanamsha_id
          LIMIT 5
        `, [chart_id])

        // 2. Election windows (phala_muhurta for domain → action class mapping)
        const muhurtaResult = await platformQuery(`
          SELECT pm.action_class, pm.window_start, pm.window_end,
                 pm.composite_quality, pm.window_quality_verdict,
                 pm.fructification_anchor, pm.tarabala_chandrabala_jsonb,
                 pm.significators_met_jsonb, pm.follow_up_hook_jsonb
          FROM phala_muhurta pm
          WHERE pm.chart_id = $1
            AND pm.composite_quality IS NOT NULL
          ORDER BY pm.composite_quality DESC NULLS LAST
          LIMIT $2
        `, [chart_id, top_windows])

        // 3. Fructification timing from phala_anchors (domain-filtered)
        const anchorResult = await platformQuery(`
          SELECT pa.anchor_id, pa.domain, pa.event_type, pa.posterior,
                 pa.magnitude, pa.window_start, pa.window_end,
                 pa.structured_falsifier_jsonb, pa.lift_vector_jsonb
          FROM phala_anchors pa
          WHERE pa.chart_id = $1
            AND pa.domain = $2
            AND pa.posterior IS NOT NULL
          ORDER BY pa.posterior DESC NULLS LAST
          LIMIT 3
        `, [chart_id, domain])

        // 4. Activity ontology fructification rules for inferred action class
        const _DOMAIN_TO_ACTION: Record<string, string> = {
          career: 'business_start', financial: 'contract_signing',
          health: 'medical_procedure', relationship: 'marriage',
          spiritual: 'sadhana', transition: 'travel_journey',
        }
        const actionClass = _DOMAIN_TO_ACTION[domain] ?? 'business_start'
        const ontologyResult = await platformQuery(`
          SELECT activity_class_id, name_en, significators, fructification_rules, citations
          FROM brahma_activity_ontology
          WHERE activity_class_id = $1
        `, [actionClass])

        // Composite undertaking score = mean(prashna verdict_strength, best election quality, best posterior)
        const verdictStrength = prashnaResult.rows[0]?.['verdict_strength'] as number | null ?? 0.5
        const bestElection = (muhurtaResult.rows[0]?.['composite_quality'] as number | null) ?? 0.5
        const bestPosterior = (anchorResult.rows[0]?.['posterior'] as number | null) ?? 0.1
        const compositeScore = Math.round(((verdictStrength + bestElection + bestPosterior) / 3) * 1000) / 1000

        const recipe = {
          chart_id,
          domain,
          action_class: actionClass,
          formula_version: 'prashna_undertaking_v1.0_ba_p5b',
          composite_undertaking_score: compositeScore,
          prashna_verdict: prashnaResult.rows,
          election_windows: muhurtaResult.rows,
          fructification_anchors: anchorResult.rows,
          fructification_rules: ontologyResult.rows[0]?.['fructification_rules'] ?? null,
          classical_citations: ontologyResult.rows[0]?.['citations'] ?? [],
          note: 'Q4 undertaking recipe: horary verdict × election scoring × fructification. ' +
                'JL-009: posterior values use placeholder base rates until native review.',
        }

        return dualOutput(envelope(recipe, 'prashna_undertaking_get', 'q4_undertaking'))
      } catch (err) {
        return errorOutput('prashna_undertaking_get', String(err), { chart_id, domain })
      }
    }
  )
}
