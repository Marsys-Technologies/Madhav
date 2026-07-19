/**
 * event_ontology_shapes.ts — DR-13/DIS.026 canonical event-class SHAPE enforcement.
 *
 * D-4a Lane A-2 ("Canonical event ontology"). The event-class registry itself lives in the
 * `brahma_event_ontology` table (migration 388, extended by migration 456 with the DR-13 fields
 * this module reads: temporal_shape, duration_prior, milestone_template,
 * irreversibility_milestone, evidence_requirements, self_report_non_discriminating,
 * kill_switch_criteria). This module is the SHARED, PURE validation logic other lanes import to
 * enforce that a claim/event's shape matches its declared event_class's canonical shape:
 *
 *   - the matcher (Lane A-1) uses it to reject a mis-shaped LEL intake or to score a
 *     shape-appropriate match (overlap for interval, per-milestone for chain);
 *   - the prospective ledger (Lane A-4) uses it to validate a filed prediction's claim_shape
 *     BEFORE it is accepted — "a point-claim for an interval-class event is a schema violation"
 *     (BRIEF_D4A.md Lane A-4) is exactly what `validateClaimShape` below implements.
 *
 * Deliberately DB-agnostic: `EventClassOntologyEntry` is a plain data shape, not a live query
 * result type, so this module's core logic is unit-testable without a database (see
 * event_ontology_shapes.test.ts — the schema-violation acceptance proof for this lane). A thin
 * DB accessor (`getEventClassOntology`) is provided separately for callers that need the live row.
 *
 * @module event_ontology_shapes
 */

import 'server-only'
import { query } from '@/lib/db/client'

// ── Types ───────────────────────────────────────────────────────────────────────────────────

export type TemporalShape = 'point' | 'interval' | 'chain'

export interface DurationPrior {
  min_days: number
  typical_days: number
  max_days: number
}

export interface MilestoneTemplateEntry {
  milestone_id: string
  name_en: string
  typical_offset_days_from_first?: number
}

export type EvidenceValence = 'gain' | 'loss' | 'neutral' | 'mixed'
export type SelfReportRisk = 'none' | 'low' | 'moderate' | 'high'

export interface EvidenceRequirements {
  valence: EvidenceValence
  externally_verifiable: boolean
  verification_sources: string[]
  self_report_risk: SelfReportRisk
  notes?: string | null
}

export interface KillSwitchCriterion {
  criterion_id: string
  description: string
}

/**
 * The DR-13 shape-relevant slice of a `brahma_event_ontology` row. A full row carries additional
 * columns (signature_model, base_rate_by_age, adjacency, …) this module does not need.
 */
export interface EventClassOntologyEntry {
  event_class_id: string
  temporal_shape: TemporalShape
  duration_prior: DurationPrior | null
  milestone_template: MilestoneTemplateEntry[] | null
  irreversibility_milestone: string | null
  evidence_requirements: EvidenceRequirements
  self_report_non_discriminating: boolean
  kill_switch_criteria: KillSwitchCriterion[]
}

/** A claim or LEL event's ACTUAL recorded shape — what a caller submits for validation. */
export type ClaimShape =
  | { kind: 'point'; date: string }
  | { kind: 'interval'; start: string; end: string }
  | { kind: 'chain'; milestones: Array<{ milestone_id: string; date: string }> }

export interface ShapeViolation {
  code:
    | 'SHAPE_MISMATCH'
    | 'UNKNOWN_MILESTONE'
    | 'INVERTED_INTERVAL'
    | 'EMPTY_CHAIN_CLAIM'
    | 'UNKNOWN_EVENT_CLASS'
  message: string
}

// ── Pure validation ────────────────────────────────────────────────────────────────────────────

/**
 * Validate a claim/event's shape against its declared event_class's canonical shape.
 *
 * Returns an empty array when the claim is shape-valid. Returns one or more ShapeViolation
 * entries otherwise — the caller (matcher / ledger intake) rejects on any non-empty result. This
 * function never throws; use `assertClaimShape` for a throwing variant.
 *
 * The load-bearing rule (BRIEF_D4A Lane A-4): **a point-claim for an interval-class event, or an
 * interval-claim for a point-class event, etc., is a schema violation** — shape is not advisory
 * metadata, it is an enforced contract shared identically by measurement (the matcher/harness) and
 * generation (the ledger/engine), per TEMPORAL_ENGINE_ARC_PLAN_v1_0.md §7's "event-shape symmetry"
 * invariant.
 */
export function validateClaimShape(
  ontology: EventClassOntologyEntry,
  claim: ClaimShape
): ShapeViolation[] {
  const violations: ShapeViolation[] = []

  if (claim.kind !== ontology.temporal_shape) {
    violations.push({
      code: 'SHAPE_MISMATCH',
      message:
        `event_class '${ontology.event_class_id}' is canonically '${ontology.temporal_shape}'-shaped ` +
        `per the ontology; claim was submitted as '${claim.kind}'-shaped. A claim/event must speak in ` +
        `its class's declared temporal grammar (DR-13 event-shape symmetry).`,
    })
    // Shape family mismatch makes any further structural check meaningless — stop here.
    return violations
  }

  if (claim.kind === 'interval') {
    const start = Date.parse(claim.start)
    const end = Date.parse(claim.end)
    if (Number.isFinite(start) && Number.isFinite(end) && end < start) {
      violations.push({
        code: 'INVERTED_INTERVAL',
        message: `interval claim for '${ontology.event_class_id}' has end (${claim.end}) before start (${claim.start}).`,
      })
    }
  }

  if (claim.kind === 'chain') {
    if (claim.milestones.length === 0) {
      violations.push({
        code: 'EMPTY_CHAIN_CLAIM',
        message: `chain claim for '${ontology.event_class_id}' names zero milestones; a chain claim must anchor at least one named milestone from the class's milestone_template.`,
      })
    }
    const templateIds = new Set((ontology.milestone_template ?? []).map((m) => m.milestone_id))
    for (const m of claim.milestones) {
      if (!templateIds.has(m.milestone_id)) {
        violations.push({
          code: 'UNKNOWN_MILESTONE',
          message: `milestone '${m.milestone_id}' is not in '${ontology.event_class_id}'s declared milestone_template (${[...templateIds].join(', ')}).`,
        })
      }
    }
  }

  return violations
}

/** Throwing variant of {@link validateClaimShape}. Throws on the first violation set found. */
export function assertClaimShape(ontology: EventClassOntologyEntry, claim: ClaimShape): void {
  const violations = validateClaimShape(ontology, claim)
  if (violations.length > 0) {
    const msg = violations.map((v) => `[${v.code}] ${v.message}`).join('; ')
    throw new Error(`Claim shape violation for event_class '${ontology.event_class_id}': ${msg}`)
  }
}

/**
 * Does this event instance meet ANY of its class's kill_switch_criteria? Callers pass the set of
 * criterion_ids they have determined apply (e.g. from evidence review) — this function does not
 * itself inspect evidence, it only checks membership. Returns the matching criteria (empty = not
 * kill-switched).
 */
export function checkKillSwitch(
  ontology: EventClassOntologyEntry,
  metCriterionIds: readonly string[]
): KillSwitchCriterion[] {
  const met = new Set(metCriterionIds)
  return ontology.kill_switch_criteria.filter((c) => met.has(c.criterion_id))
}

// ── DB accessor ──────────────────────────────────────────────────────────────────────────────

interface EventClassOntologyRow {
  event_class_id: string
  temporal_shape: TemporalShape
  duration_prior: DurationPrior | null
  milestone_template: MilestoneTemplateEntry[] | null
  irreversibility_milestone: string | null
  evidence_requirements: EvidenceRequirements
  self_report_non_discriminating: boolean
  kill_switch_criteria: KillSwitchCriterion[]
}

/**
 * Fetch the DR-13 shape-relevant slice of one `brahma_event_ontology` row by event_class_id.
 * Returns null if the class does not exist (an unknown event_class is the caller's concern to
 * report — this function does not throw for a missing row, matching lel_event_writer.ts's own
 * "not present in brahma_event_ontology" handling pattern).
 */
export async function getEventClassOntology(
  eventClassId: string
): Promise<EventClassOntologyEntry | null> {
  const { rows } = await query<EventClassOntologyRow>(
    `SELECT event_class_id, temporal_shape, duration_prior, milestone_template,
            irreversibility_milestone, evidence_requirements, self_report_non_discriminating,
            kill_switch_criteria
       FROM brahma_event_ontology
      WHERE event_class_id = $1`,
    [eventClassId]
  )
  const row = rows[0]
  return row ?? null
}
