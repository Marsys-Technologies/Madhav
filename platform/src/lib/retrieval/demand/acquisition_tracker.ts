/**
 * acquisition_tracker.ts — WP-1.6 (P-12) demand-side acquisition-tracker record schema.
 *
 * The machine-readable substrate for the E3 "demand-side chase" posture
 * (REMEDIATION_PLAN_v3_0 §1 E3, §5 WP-1.6 widened). A consuming LLM — or the
 * future doctrine-campaign planner — forms an EXPECTED-evidence set for a
 * question, then chases each item across the served tool surface, recording for
 * every item whether it is still `needed`, was `received`, or is honestly
 * `exhausted` (with a reason). This module defines ONLY the record types + a
 * handful of pure, side-effect-free constructors/reducers so the shape
 * round-trips (serialize → parse → serialize is identity) and any planner can
 * track received-vs-needed without re-deriving the contract.
 *
 * This file is intentionally free of I/O, DB, and MCP imports: it is the
 * data contract, consumed by (a) the served consumption PROTOCOL resource
 * (platform-mcp/src/resources/consumption_protocol.ts) and (b) W4's Lane-2
 * demand-side re-run. It pairs with the capability MAP
 * (00_ARCHITECTURE/llm_consumption_audit/capability_map/CONCEPT_CAPABILITY_MAP.json):
 * the map answers "which tool serves concept X"; the tracker answers "did I
 * actually get X yet, and if not, why did I stop chasing".
 *
 * Not a runtime engine — the actual chase is performed by the consuming LLM
 * following the protocol; this schema is what it writes down as it goes.
 */

// ── Item status ───────────────────────────────────────────────────────────────

/**
 * The lifecycle state of a single expected-evidence item.
 *
 * - `needed`    — planned but not yet fetched; the chase must continue.
 * - `received`  — the evidence arrived (from a planned route or volunteered).
 * - `exhausted` — the chase stopped WITHOUT the evidence, for a stated reason.
 *                 Honest exhaustion is a valid terminal state (E3: "not finding
 *                 everything is acceptable; not chasing is not").
 */
export type AcquisitionStatus = 'needed' | 'received' | 'exhausted'

/**
 * Why a `needed` item became `exhausted`. Drives the honesty ledger — an item
 * may only leave the chase via one of these declared reasons, never silently.
 *
 * - `no_route`          — the capability map exposes no tool/service for it
 *                         (truly-unreachable or served-only-by-down-pipeline).
 * - `route_empty`       — a route exists and was called, but returned no rows
 *                         for this chart (honest-empty, not an error).
 * - `route_error`       — the route was called and errored / timed out.
 * - `not_applicable`    — on inspection the item does not apply to this chart /
 *                         question (e.g. progeny karaka for a non-progeny query).
 * - `budget_exhausted`  — the chase hit its call/latency budget before this item.
 * - `superseded`        — a broader item's arrival subsumed this one.
 */
export type ExhaustionReason =
  | 'no_route'
  | 'route_empty'
  | 'route_error'
  | 'not_applicable'
  | 'budget_exhausted'
  | 'superseded'

/**
 * How an item's evidence was obtained (provenance of a `received` item, or the
 * intended source of a `needed` one).
 *
 * - `planned`     — fetched via a route the planner listed up front (the frame).
 * - `volunteered` — arrived as a bonus inside another tool's payload without
 *                   having been separately planned/chased (E3: bonus, never the
 *                   frame). Counts toward coverage but is tracked distinctly so
 *                   supply-side satisfaction can never masquerade as the plan.
 */
export type AcquisitionProvenance = 'planned' | 'volunteered'

// ── A single expected-evidence item ───────────────────────────────────────────

/**
 * One item in the expected-evidence set: a concept the question's domain leads
 * the consumer to EXPECT, keyed to the capability map by concept family.
 */
export interface EvidenceItem {
  /** Stable id within a plan (e.g. `e7-bhavesha-dignity`). Unique per plan. */
  item_id: string

  /**
   * The concept-family key from CONCEPT_CAPABILITY_MAP (e.g. `dignity_state`,
   * `dasha_lord`). Anchors the item to a map route. May be null for an
   * expected concept the map does not yet enumerate (logged for W4 seeding).
   */
  family_key: string | null

  /** Human-readable statement of what evidence is expected. */
  label: string

  /** Current lifecycle status. */
  status: AcquisitionStatus

  /**
   * Candidate serving routes for this item, copied from the capability map at
   * plan time (marsys:// URIs and/or MCP tool names). The chase walks these.
   */
  candidate_routes: string[]

  /** Set when status === 'received'. */
  received?: {
    /** The route that produced the evidence (URI or MCP tool name). */
    via_route: string
    provenance: AcquisitionProvenance
    /** Optional count / id-set of what arrived, for audit. */
    arrived_count?: number
    /** Reference ids that resolve the evidence (fact_id / signal_id / etc.). */
    reference_ids?: string[]
  }

  /** Set when status === 'exhausted'. Required reason enforces honesty. */
  exhausted?: {
    reason: ExhaustionReason
    /** Free-text note (which route was tried, what came back). */
    detail?: string
    /** Routes actually attempted before giving up. */
    routes_tried?: string[]
  }
}

// ── The tracker record (per question / consumption session) ────────────────────

/** Rollup counters — derivable from `items`, materialized for cheap reads. */
export interface AcquisitionSummary {
  total: number
  needed: number
  received: number
  exhausted: number
  /** received items whose provenance was 'volunteered' (bonus, not frame). */
  volunteered: number
  /** received / total, rounded to 4 dp. 1.0 only when nothing is outstanding. */
  coverage: number
  /** true iff no item remains in `needed` (every item resolved or exhausted). */
  chase_complete: boolean
}

/**
 * The full demand-side tracker for one consumption session. Round-trips through
 * JSON.stringify / JSON.parse with no loss (all fields are plain data).
 */
export interface AcquisitionTracker {
  /** Schema version for the tracker record itself. */
  schema_version: '1.0'
  /** Free-form question / intent this plan serves. */
  question: string
  /** Chart under analysis, when chart-scoped. */
  chart_id?: string
  /** The domain(s) that shaped the expected set (e.g. ['marriage']). */
  domains?: string[]
  /** Capability-map artifact version the routes were drawn from. */
  map_version?: string
  /** ISO-8601 timestamp the plan was formed. */
  planned_at: string
  /** The expected-evidence set — the frame. */
  items: EvidenceItem[]
  /** Materialized rollup (keep in sync via recomputeSummary). */
  summary: AcquisitionSummary
}

// ── Pure constructors / reducers (no side effects) ─────────────────────────────

/** Recompute the summary rollup from the item list. Pure. */
export function recomputeSummary(items: EvidenceItem[]): AcquisitionSummary {
  const total = items.length
  let needed = 0
  let received = 0
  let exhausted = 0
  let volunteered = 0
  for (const it of items) {
    if (it.status === 'needed') needed += 1
    else if (it.status === 'received') {
      received += 1
      if (it.received?.provenance === 'volunteered') volunteered += 1
    } else if (it.status === 'exhausted') exhausted += 1
  }
  const coverage = total === 0 ? 0 : Math.round((received / total) * 1e4) / 1e4
  return {
    total,
    needed,
    received,
    exhausted,
    volunteered,
    coverage,
    chase_complete: needed === 0,
  }
}

/** Build a fresh tracker from an expected-evidence set. Pure. */
export function createTracker(input: {
  question: string
  items: EvidenceItem[]
  chart_id?: string
  domains?: string[]
  map_version?: string
  planned_at?: string
}): AcquisitionTracker {
  const items = input.items
  const tracker: AcquisitionTracker = {
    schema_version: '1.0',
    question: input.question,
    planned_at: input.planned_at ?? new Date().toISOString(),
    items,
    summary: recomputeSummary(items),
  }
  if (input.chart_id !== undefined) tracker.chart_id = input.chart_id
  if (input.domains !== undefined) tracker.domains = input.domains
  if (input.map_version !== undefined) tracker.map_version = input.map_version
  return tracker
}

/**
 * Mark an item `received`. Returns a NEW tracker (immutable update) with the
 * summary recomputed. No-op-safe if item_id is unknown.
 */
export function markReceived(
  tracker: AcquisitionTracker,
  item_id: string,
  received: NonNullable<EvidenceItem['received']>
): AcquisitionTracker {
  const items = tracker.items.map((it) =>
    it.item_id === item_id
      ? ({ ...it, status: 'received' as const, received })
      : it
  )
  return { ...tracker, items, summary: recomputeSummary(items) }
}

/**
 * Mark an item `exhausted` with a required reason. Returns a NEW tracker.
 */
export function markExhausted(
  tracker: AcquisitionTracker,
  item_id: string,
  exhausted: NonNullable<EvidenceItem['exhausted']>
): AcquisitionTracker {
  const items = tracker.items.map((it) =>
    it.item_id === item_id
      ? ({ ...it, status: 'exhausted' as const, exhausted })
      : it
  )
  return { ...tracker, items, summary: recomputeSummary(items) }
}

/**
 * Validate a parsed tracker's structural integrity (post-round-trip guard).
 * Returns an array of problems; empty array === valid. Pure.
 */
export function validateTracker(t: AcquisitionTracker): string[] {
  const problems: string[] = []
  if (t.schema_version !== '1.0') problems.push(`bad schema_version: ${String(t.schema_version)}`)
  const ids = new Set<string>()
  for (const it of t.items) {
    if (ids.has(it.item_id)) problems.push(`duplicate item_id: ${it.item_id}`)
    ids.add(it.item_id)
    if (it.status === 'received' && !it.received) problems.push(`${it.item_id}: received status without received block`)
    if (it.status === 'exhausted' && !it.exhausted) problems.push(`${it.item_id}: exhausted status without reason`)
    if (it.status === 'exhausted' && it.exhausted && !it.exhausted.reason) problems.push(`${it.item_id}: exhausted without reason`)
  }
  const recomputed = recomputeSummary(t.items)
  if (recomputed.received !== t.summary.received || recomputed.needed !== t.summary.needed || recomputed.exhausted !== t.summary.exhausted) {
    problems.push('summary out of sync with items')
  }
  return problems
}
