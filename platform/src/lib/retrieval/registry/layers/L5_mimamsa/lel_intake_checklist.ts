/**
 * lel_intake_checklist — guided LEL intake surface (L5 Mīmāṃsā)
 * =================================================================
 * Elevation Campaign v2.1, Lane γ.J, EL-54 ("morning-ready packet").
 *
 * WHAT THIS IS: a checklist-style guide to what retrodiction needs per domain,
 * grounded in `brahma_event_ontology` (the real, already-built event-class
 * taxonomy — never an invented list), plus a `mode=validate` path that checks a
 * native-authored DRAFT entry against `life_events`' real shape/field rules
 * before it is ever filed.
 *
 * HARD BOUNDARY (B.10 / charter §12 "LEL content entry is native-only — the
 * intake surface is built, the events are not"): this tool NEVER invents,
 * fills in, or guesses life-event content. `mode=checklist` only echoes back
 * what the ontology + schema already require; `mode=validate` only reports
 * whether native-SUPPLIED text satisfies those requirements — a missing field
 * is always reported as a validation error for the native to fill in, never
 * silently defaulted or fabricated. This tool performs NO WRITE to `life_events`
 * — filing itself is intentionally left to the native's own action (or a
 * future explicit-filing tool), mirroring `brahma_prospective_ledger`'s
 * §11 explicit-filing-only discipline for the sibling prospective ledger.
 *
 * NO-LEAKAGE (mirrors query_life_events.ts / mechanism_retrodiction_get):
 * life_events is a calibration corpus only — this tool never feeds prediction
 * generation; it only prepares/validates calibration intake.
 *
 * Grounding: `brahma_event_ontology.temporal_shape` decides which life_events
 * date field(s) an entry needs (point -> event_date; interval -> interval_start
 * + interval_end; chain -> milestone_label [+ chain_parent_event_id for
 * non-first milestones]) — the same shape vocabulary migration 457 added to
 * `life_events` (life_events_shape_check). `evidence_requirements` (jsonb,
 * migration 456) supplies the real verification_sources/self_report_risk
 * prompts per event class — not invented copy.
 */

import type { CapabilityDescriptor } from '../../types'
import { query } from '@/lib/db/client'

type Shape = 'point' | 'interval' | 'chain'
const VALID_DATE_CONFIDENCE = ['exact', 'month_known', 'year_only'] as const

const DATE_RE = /^\d{4}-\d{2}-\d{2}$/

/** Loose placeholder detector — rejects obviously-unfilled template text, never generates replacement text. */
const PLACEHOLDER_RE = /^\s*(tbd|todo|tba|n\/a|na|xxx+|<[^>]*>|\.\.\.|pending|fill.?in|native.?to.?supply)\s*$/i

interface OntologyRow {
  event_class_id: string
  name_en: string
  domain: string
  lel_category: string | null
  temporal_shape: Shape
  evidence_requirements: {
    verification_sources?: string[]
    self_report_risk?: string
    externally_verifiable?: boolean
    valence?: string
    notes?: string | null
  } | null
}

interface DraftEntry {
  domain?: string
  event_class?: string
  event_date?: string
  interval_start?: string
  interval_end?: string
  milestone_label?: string
  chain_parent_event_id?: string
  date_confidence?: string
  category?: string
  description?: string
  significance?: string
  source_citation?: string
}

function requiredFieldsForShape(shape: Shape): string[] {
  if (shape === 'point') return ['event_date']
  if (shape === 'interval') return ['interval_start', 'interval_end']
  return ['milestone_label'] // chain — chain_parent_event_id only required for non-first milestones
}

function validateEntry(entry: DraftEntry, ontologyByClass: Map<string, OntologyRow>): { valid: boolean; errors: string[]; warnings: string[] } {
  const errors: string[] = []
  const warnings: string[] = []

  if (!entry.event_class || !entry.event_class.trim()) {
    errors.push('event_class is required (must be a real brahma_event_ontology.event_class_id — see mode=checklist for the list).')
  }
  const ontRow = entry.event_class ? ontologyByClass.get(entry.event_class) : undefined
  if (entry.event_class && !ontRow) {
    errors.push(`event_class '${entry.event_class}' is not a known event class. Call mode=checklist to see the real, built taxonomy — do not invent a new class name here.`)
  }
  if (ontRow && entry.domain && entry.domain !== ontRow.domain) {
    warnings.push(`domain '${entry.domain}' does not match event_class '${entry.event_class}''s ontology domain '${ontRow.domain}' — using the ontology domain is recommended.`)
  }

  // Shape-consistency check, only meaningful once we know the event_class's real shape.
  if (ontRow) {
    const shape = ontRow.temporal_shape
    const req = requiredFieldsForShape(shape)
    for (const field of req) {
      const val = (entry as Record<string, unknown>)[field]
      if (!val || (typeof val === 'string' && !val.trim())) {
        errors.push(`event_class '${entry.event_class}' is shape='${shape}' — field '${field}' is required and missing.`)
      }
    }
    if (shape === 'point' && entry.event_date && !DATE_RE.test(entry.event_date)) {
      errors.push(`event_date '${entry.event_date}' is not YYYY-MM-DD.`)
    }
    if (shape === 'interval') {
      if (entry.interval_start && !DATE_RE.test(entry.interval_start)) errors.push(`interval_start '${entry.interval_start}' is not YYYY-MM-DD.`)
      if (entry.interval_end && !DATE_RE.test(entry.interval_end)) errors.push(`interval_end '${entry.interval_end}' is not YYYY-MM-DD.`)
      if (entry.interval_start && entry.interval_end && DATE_RE.test(entry.interval_start) && DATE_RE.test(entry.interval_end)
          && entry.interval_start > entry.interval_end) {
        errors.push('interval_start must be on or before interval_end.')
      }
    }
    if (shape === 'chain' && entry.chain_parent_event_id === undefined) {
      warnings.push("chain_parent_event_id is unset — acceptable only if this is the FIRST milestone in its chain; otherwise supply the parent event's id.")
    }
  }

  if (!entry.description || !entry.description.trim()) {
    errors.push('description is required — this tool never fabricates event content; the native must supply the factual description.')
  } else if (PLACEHOLDER_RE.test(entry.description.trim())) {
    errors.push(`description '${entry.description}' reads as an unfilled placeholder, not real content — supply the actual event description.`)
  }

  if (!entry.category || !entry.category.trim()) {
    errors.push('category is required.')
  } else if (ontRow?.lel_category && entry.category !== ontRow.lel_category) {
    warnings.push(`category '${entry.category}' differs from this event_class's conventional lel_category '${ontRow.lel_category}' — not an error (life_events.category is free text), but worth a second look.`)
  }

  if (!entry.source_citation || !entry.source_citation.trim()) {
    errors.push('source_citation is required (B.3 provenance mandate) — e.g. "native-disclosed, <date this session>".')
  } else if (PLACEHOLDER_RE.test(entry.source_citation.trim())) {
    errors.push(`source_citation '${entry.source_citation}' reads as an unfilled placeholder — supply a real provenance note.`)
  }

  if (entry.date_confidence && !(VALID_DATE_CONFIDENCE as readonly string[]).includes(entry.date_confidence)) {
    errors.push(`date_confidence '${entry.date_confidence}' must be one of: ${VALID_DATE_CONFIDENCE.join(', ')}.`)
  }

  if (ontRow?.evidence_requirements?.verification_sources?.length) {
    warnings.push(`Suggested verification sources for '${entry.event_class}': ${ontRow.evidence_requirements.verification_sources.join(', ')}. Not required to file, but strengthens later calibration.`)
  }
  if (ontRow?.evidence_requirements?.self_report_risk === 'high') {
    warnings.push(`event_class '${entry.event_class}' is flagged self_report_risk=high (self_report_non_discriminating candidate) — an internal-state report is acceptable, but note it as such in source_citation.`)
  }

  return { valid: errors.length === 0, errors, warnings }
}

export const lelIntakeChecklistCapability: CapabilityDescriptor = {
  uri:   'marsys://tool/L5/lel_intake_checklist',
  type:  'tool',
  layer: 'L5',
  name:  'lel_intake_checklist',

  description: [
    'Guided Life Event Log (LEL) intake surface (EL-54). mode=checklist (default) returns,',
    'per domain, the real event classes brahma_event_ontology already defines that',
    'retrodiction needs LEL coverage for — each with its required temporal shape',
    '(point/interval/chain -> which life_events date fields to fill), suggested',
    'verification sources, and self-report-risk flag. Also reports current life_events',
    'coverage per domain so the native can see which domains are already logged vs. thin.',
    'mode=validate takes a `entries[]` array of native-authored DRAFT life events and',
    'checks each against the real event_class/shape/field rules, returning per-entry',
    'errors + warnings. HARD BOUNDARY: this tool never invents, fills in, or guesses life-event',
    'content, and it never writes to life_events — it only structures and validates what the',
    'native supplies. A missing field is always reported as an error for the native to fill,',
    'never defaulted. Designed as a 30-60 minute guided session scaffold (charter §13 packet 1).',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID. Required.',
      required: true,
    },
    mode: {
      type: 'string',
      description: "'checklist' (default) — the per-domain guided checklist. 'validate' — check draft entries[] against the real shape/field rules.",
      enum: ['checklist', 'validate'],
      required: false,
    },
    domain: {
      type: 'string',
      description: 'checklist mode only: filter to one domain. Omit for all domains.',
      required: false,
    },
    entries: {
      type: 'array',
      description: 'validate mode only: draft entries to check. Each: {domain?, event_class, event_date|interval_start+interval_end|milestone_label, date_confidence?, category, description, significance?, source_citation}.',
      required: false,
    },
  },

  required_inputs: ['chart_id'],
  scope: 'per_chart',
  archetype: 'calibration',
  traversal_level: 'L-SIGNAL',
  tool_role: 'quality',
  emits_references: false,
  grounds_to: { l1_fact_ids: false },
  lel_capable: true,
  // NOT calibration_context_only: that flag (F-R7) is for outcome/LEL-READ tools supplying raw
  // ledger context to the calibration loop (lel_query, query_predictions). This tool is the
  // opposite direction — guided LEL-WRITE assistance (checklist + draft validation) — so it does
  // not fit the documented semantic; left unset rather than force-classified under time pressure.
  data_source: 'stored',

  llm_hints: {
    agentic: {
      cost_class: 'cheap',
      cacheable: false, // validate mode is native-input-dependent; checklist mode is cheap but ontology can grow
    },
    bulk_context: {
      pre_fetch_priority: 20, // low priority — an on-demand native workflow surface, not a reading-time primitive
    },
  },

  async handler(args: Record<string, unknown>, _ctx: unknown) {
    void _ctx
    const chart_id = args['chart_id'] ? String(args['chart_id']) : ''
    if (!chart_id) {
      return { content: { error: 'chart_id is required' }, is_error: true }
    }

    const mode = args['mode'] === 'validate' ? 'validate' : 'checklist'

    try {
      const ontologyResult = await query<OntologyRow>(
        `SELECT event_class_id, name_en, domain, lel_category, temporal_shape, evidence_requirements
         FROM brahma_event_ontology
         ORDER BY domain, event_class_id`,
        [],
      )
      const ontologyRows = ontologyResult.rows as OntologyRow[]
      const ontologyByClass = new Map(ontologyRows.map(r => [r.event_class_id, r]))

      if (mode === 'validate') {
        const rawEntries = Array.isArray(args['entries']) ? (args['entries'] as DraftEntry[]) : []
        if (rawEntries.length === 0) {
          return {
            content: {
              error: 'mode=validate requires a non-empty entries[] array of draft life events.',
              chart_id,
            },
            is_error: true,
          }
        }
        const results = rawEntries.map((entry, idx) => ({
          index: idx,
          event_class: entry.event_class ?? null,
          ...validateEntry(entry, ontologyByClass),
        }))
        const entries_valid = results.filter(r => r.valid).length
        return {
          content: {
            chart_id,
            mode,
            results,
            entries_checked: results.length,
            entries_valid,
            entries_invalid: results.length - entries_valid,
            governance: 'This tool validates shape/field completeness only. It never invents or fills in event content — every error above names a field the native must supply. It performs no write to life_events; filing remains a separate, explicit, native-authorized action (§11-style explicit-filing-only discipline, mirroring brahma_prospective_ledger).',
          },
          is_error: false,
        }
      }

      // mode=checklist
      const domainFilter = args['domain'] ? String(args['domain']).toLowerCase() : null
      const domains = new Map<string, OntologyRow[]>()
      for (const row of ontologyRows) {
        if (domainFilter && row.domain !== domainFilter) continue
        if (!domains.has(row.domain)) domains.set(row.domain, [])
        domains.get(row.domain)!.push(row)
      }

      // Chart-scoped existing coverage — read-only, tells the native which domains are thin.
      const coverageResult = await query<{ domain: string; total: string }>(
        `SELECT split_part(domain, '/', 1) AS domain, COUNT(*)::text AS total
         FROM life_events
         WHERE chart_id = $1
         GROUP BY split_part(domain, '/', 1)`,
        [chart_id],
      )
      const coverageByDomain = new Map(
        (coverageResult.rows as Array<{ domain: string; total: string }>).map(r => [r.domain, Number(r.total)]),
      )

      const domainEntries = Array.from(domains.entries()).map(([domain, classes]) => ({
        domain,
        event_class_count: classes.length,
        under_target_count_note: classes.length < 3
          ? `Only ${classes.length} event class(es) currently defined for this domain in brahma_event_ontology — below the charter's 3-5 target. Honest gap, not padded: no invented classes added to reach the target.`
          : null,
        existing_lel_events_for_chart: coverageByDomain.get(domain) ?? 0,
        event_classes: classes.map(c => ({
          event_class_id: c.event_class_id,
          name_en: c.name_en,
          lel_category: c.lel_category,
          temporal_shape: c.temporal_shape,
          required_fields: ['category', 'description', 'source_citation', ...requiredFieldsForShape(c.temporal_shape)],
          optional_fields: ['significance', 'date_confidence', ...(c.temporal_shape === 'chain' ? ['chain_parent_event_id'] : [])],
          suggested_verification_sources: c.evidence_requirements?.verification_sources ?? [],
          self_report_risk: c.evidence_requirements?.self_report_risk ?? null,
          externally_verifiable: c.evidence_requirements?.externally_verifiable ?? null,
        })),
      }))

      return {
        content: {
          chart_id,
          mode,
          domains: domainEntries,
          domain_count: domainEntries.length,
          total_event_classes: domainEntries.reduce((s, d) => s + d.event_class_count, 0),
          filters: { domain: domainFilter },
          intake_instructions: [
            'For each domain below, walk the event_classes list and note which ones this chart has a',
            'real, dated life event for (or an honest "none" — absence is data too, never fabricate a filler).',
            "Supply: category, description, source_citation, and the shape-specific date field(s)",
            "(point -> event_date; interval -> interval_start + interval_end; chain -> milestone_label).",
            'Then call this same tool with mode=validate and entries=[...] to check the draft before filing.',
            'This tool never files anything itself — filing is a separate, explicit, native-authorized step.',
          ].join(' '),
          governance: 'life_events is a calibration corpus only (no-leakage) — never feeds prediction generation. This surface structures and validates intake; it does not generate or infer event content (B.10 / charter §12: LEL content entry is native-only).',
          provenance: {
            tables: ['brahma_event_ontology', 'life_events'],
            source: 'brahma_event_ontology (real, already-built taxonomy) joined against chart-scoped life_events coverage counts.',
          },
        },
        is_error: false,
      }
    } catch (err) {
      return { content: { error: String(err), chart_id }, is_error: true }
    }
  },
}
