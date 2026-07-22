/**
 * event_class_resolution.ts — D-4b Lane F-1 (resonance-map coverage).
 *
 * Fixes the defect `B1_NARROWED_STATUS_v1_0.md` §5a / `REPORT_D4B.md` §0
 * named: `b1_driver_v1_0.ts` passed a raw `life_events.category` string
 * (e.g. "family", "finance", "career") straight through as the
 * `event_class` parameter to `pratyantar_lord`'s significator lookup AND
 * the `/api/compute/permission_curve` route — a value that essentially
 * never matches a `gochara_resonance_map.event_class` row, degrading every
 * PERMISSION-system contender to its coarse fallback path (see
 * `permission_curve.py`'s own `notes` field) SILENTLY, with no disclosure
 * that this had happened.
 *
 * ── F-1 disposition (investigated, not assumed — see PR description for
 * the full evidence trail) ─────────────────────────────────────────────
 *
 * `gochara_resonance_map` has exactly 3 populated `event_class` rows for
 * chart 482012f1 (`career_advancement`=22, `major_gain`=35, `marriage`=23
 * rows, live-queried 2026-07-22) against `brahma_event_ontology`'s full
 * 27-class ontology. This is `ka_gochara_resonance`'s DESIGNED, DOCUMENTED
 * scope, not a bug or an incomplete prior run:
 * `services/ka_gochara_resonance/writer.py`'s own `TARGET_EVENT_CLASSES`
 * tuple names exactly these 3, and `GOCHARA_RESONANCE_MAP_SPEC.md` §4
 * ("Event-class coverage: why these 3 (of 27)") documents the live
 * `bg_transit_rules`-coverage inspection that chose them, explicitly
 * framing wider coverage as "a follow-on, not a G-1 blocker." Per F-1's own
 * task ground rules, this module does NOT force-populate more classes (that
 * would mean writing fabricated/under-evidenced resonance rows) — instead
 * it resolves each event to its populated class ONLY when the evidence
 * genuinely supports it, and marks every other event UNRESOLVED, honestly
 * and machine-readably, rather than silently degrading it to the fallback
 * path the way the original bug did.
 *
 * ── Why a plain `category`->`event_class` table is NOT sufficient ──────
 *
 * `brahma_event_ontology.lel_category` is itself many-to-one against
 * `life_events.category` for every category this chart actually uses in
 * the 3 populated classes' neighbourhood: `lel_category='career'` names 5
 * event classes (business_launch, career_advancement, career_change,
 * career_entry, career_setback — only 1 populated); `lel_category='family'`
 * names 2 (parental_event, childbirth — NEITHER populated, and does not
 * even include `marriage`, whose own `lel_category` is `'relationship'`,
 * even though this chart's actual marriage event was recorded with
 * `life_events.category='family'`); `lel_category='finance'` names 2
 * (major_gain, property_acquisition). A bare category match cannot
 * disambiguate any of these — resolving on category alone would either
 * under-resolve (miss the marriage specimen entirely, the original bug) or
 * over-resolve (stamp every "career"-category event, including a job exit
 * or a company crash, as "career_advancement", misrepresenting its real
 * content — its own kind of dishonesty, not a coverage fix).
 *
 * This module instead resolves on `life_events.domain` — a real,
 * already-recorded, human-authored "<category>/<subtype>" tag (see e.g.
 * `family/marriage`, `finance/business_milestone_windfall`,
 * `career/employer_switch`) that IS specific enough to disambiguate, and
 * matches ONLY the domain values whose own text is a genuine, direct
 * correspondence to one of the 3 populated classes' classical signature
 * (BPHS-cited via `brahma_event_ontology.citations`) — never a same-domain
 * guess. Verified live 2026-07-22 against chart 482012f1's full 58-row
 * `life_events` table (every row's `category`+`domain`+`description`
 * inspected, not sampled):
 *
 *   - `family/marriage` -> `marriage` (the ONLY domain value in this
 *     chart's data literally describing a marriage; the marriage
 *     specimen, EVT.2013.12.11.01 / life_events row 2013-12-10, carries
 *     exactly this domain string).
 *   - `finance/family_windfall`, `finance/business_milestone_windfall` ->
 *     `major_gain` (both of this chart's ONLY 2 `category='finance'` rows;
 *     both descriptions use the word "windfall" directly; `major_gain`'s
 *     own BPHS ch.2,11 dhana-bhava citation is a direct semantic match).
 *
 * `career_advancement` legitimately resolves ZERO events under this table
 * — this chart's 13 `category='career'` rows are, on inspection, entries,
 * exits, switches, setbacks, and business-launch/milestone events, none of
 * which is itself an "advancement" in `career_advancement`'s own sense (the
 * single closest candidate, `career/award_selection` — "selected as one of
 * the top employees... sponsored" — more precisely matches the ontology's
 * OWN separate `achievement_recognition` class, which is not populated
 * either; force-mapping it to `career_advancement` instead would be exactly
 * the over-resolution this module exists to avoid). This is reported
 * honestly via the coverage report below, not hidden.
 *
 * Extending this table (more domain values, or a genuinely new populated
 * resonance-map class) is a follow-on, the same way `GOCHARA_RESONANCE_MAP_
 * SPEC.md` §4 frames extending `TARGET_EVENT_CLASSES` itself — this module's
 * `DOMAIN_TO_EVENT_CLASS` map is a plain object, one line per addition, and
 * every addition must cite its own evidence the same way the entries above
 * do.
 */
import type { EventClass } from './model_interface'

export type RawEventForResolution = {
  eventId: string
  category: string
  /** `life_events.domain` — real, already-recorded data. Never invented by
   * this module. Optional only because some historical rows/fixtures may
   * lack it (treated as unresolved, never guessed from `category` alone). */
  domain?: string
}

export type EventClassResolution = {
  eventClass: EventClass | null
  resolved: boolean
  method: 'domain_exact_match' | 'unresolved'
  reason: string
}

/**
 * Evidence-cited `life_events.domain` -> `event_class` table, restricted to
 * `gochara_resonance_map`'s 3 currently-populated classes (see module
 * docstring for the per-entry evidence). NOT a general LEL-category
 * ontology mapping — deliberately narrow so this module never resolves an
 * event to a class it cannot actually score against.
 */
export const DOMAIN_TO_EVENT_CLASS: Record<string, EventClass> = {
  'family/marriage': 'marriage',
  'finance/family_windfall': 'major_gain',
  'finance/business_milestone_windfall': 'major_gain',
}

/** Resolves one event's `event_class` from its `domain` (falling back to an
 * honest `unresolved` result — never a same-category guess). Pure, DB-free,
 * unit-testable. */
export function resolveEventClass(event: RawEventForResolution): EventClassResolution {
  const domain = event.domain?.trim()
  if (domain && Object.prototype.hasOwnProperty.call(DOMAIN_TO_EVENT_CLASS, domain)) {
    const eventClass = DOMAIN_TO_EVENT_CLASS[domain]
    return {
      eventClass,
      resolved: true,
      method: 'domain_exact_match',
      reason: `life_events.domain='${domain}' matches DOMAIN_TO_EVENT_CLASS's evidence-cited entry -> event_class='${eventClass}'`,
    }
  }
  return {
    eventClass: null,
    resolved: false,
    method: 'unresolved',
    reason: domain
      ? `life_events.domain='${domain}' (category='${event.category}') has no evidence-cited entry in DOMAIN_TO_EVENT_CLASS — gochara_resonance_map has no populated row this event genuinely corresponds to; NOT force-mapped to a same-category populated class (e.g. every 'career' event -> 'career_advancement'), since that would misrepresent this event's real content. See module docstring, F-1 disposition.`
      : `event carries no life_events.domain value (category='${event.category}') — cannot be resolved without it (category alone is many-to-one against brahma_event_ontology, see module docstring).`,
  }
}

// ── Coverage assertion (task item c: "every pre-registered event's class
// must resolve to a populated resonance row, OR be explicitly listed as
// unresolved in the run header -- no silent gaps") ────────────────────────

export type EventClassCoverageEntry = {
  eventId: string
  category: string
  domain?: string
  resolvedEventClass: EventClass | null
  resolved: boolean
  /** true iff resolvedEventClass is one of the LIVE-queried populated
   * gochara_resonance_map classes for this chart (never hardcoded — see
   * `fetchPopulatedEventClasses`). */
  populated: boolean
  reason: string
}

export type EventClassCoverageReport = {
  chartId: string
  /** Live-queried at run time, never a hardcoded literal — if G-1's scope
   * is ever extended, this report reflects that automatically. */
  populatedEventClassesLive: string[]
  entries: EventClassCoverageEntry[]
  resolvedAndPopulatedCount: number
  unresolvedCount: number
}

export class EventClassCoverageIntegrityError extends Error {
  constructor(entries: EventClassCoverageEntry[]) {
    super(
      `event-class coverage assertion found ${entries.length} event(s) whose RESOLVED event_class is ` +
        `NOT a live-populated gochara_resonance_map row for this chart -- this is a resolver bug (a ` +
        `class was resolved that is not actually populated), not an honest "unresolved" gap, and must ` +
        `never be silently scored against the fallback path: ${entries
          .map((e) => `${e.eventId} -> '${e.resolvedEventClass}'`)
          .join('; ')}`
    )
    this.name = 'EventClassCoverageIntegrityError'
  }
}

/**
 * Resolves every event and cross-checks each resolution against the LIVE
 * set of populated `gochara_resonance_map` classes. Throws
 * `EventClassCoverageIntegrityError` (fail loudly, mirrors
 * `roster_bind.ts`'s `RosterBindFailureError` discipline) if any event
 * resolves to a class that is NOT actually populated -- that is a resolver
 * defect, never a thing to score around. An event with NO resolution is NOT
 * a failure here -- it is recorded in the report's `entries` (resolved:
 * false) so a caller can disclose it in the run header, per this task's own
 * "no silent gaps" requirement; this function never drops an event from the
 * report.
 */
export function assertEventClassCoverage(
  chartId: string,
  events: RawEventForResolution[],
  populatedEventClassesLive: string[]
): EventClassCoverageReport {
  const populatedSet = new Set(populatedEventClassesLive)
  const entries: EventClassCoverageEntry[] = events.map((event) => {
    const res = resolveEventClass(event)
    const populated = res.eventClass !== null && populatedSet.has(res.eventClass)
    return {
      eventId: event.eventId,
      category: event.category,
      domain: event.domain,
      resolvedEventClass: res.eventClass,
      resolved: res.resolved,
      populated,
      reason: res.reason,
    }
  })

  const integrityFailures = entries.filter((e) => e.resolved && !e.populated)
  if (integrityFailures.length > 0) throw new EventClassCoverageIntegrityError(integrityFailures)

  return {
    chartId,
    populatedEventClassesLive,
    entries,
    resolvedAndPopulatedCount: entries.filter((e) => e.resolved && e.populated).length,
    unresolvedCount: entries.filter((e) => !e.resolved).length,
  }
}

/**
 * Live DB read: the set of `event_class` values `gochara_resonance_map`
 * actually has rows for, for this chart -- never hardcoded (if G-1's
 * TARGET_EVENT_CLASSES scope is ever extended, this function picks that up
 * automatically, no code change needed here). Read-only, no write, no
 * change to `gochara_resonance_map` or its writer.
 *
 * Not unit-tested against a live DB (same "no live-data dependency in the
 * unit test file" discipline as `permission_model.test.ts` /
 * `model_interface.test.ts` -- CI has no DB); `assertEventClassCoverage`
 * above is the pure, DB-free, fully-tested piece, taking this function's
 * result as a plain `string[]` argument.
 */
export async function fetchPopulatedEventClasses(
  pool: { query: (sql: string, params: unknown[]) => Promise<{ rows: { event_class: string }[] }> },
  chartId: string
): Promise<string[]> {
  const { rows } = await pool.query(
    `SELECT DISTINCT event_class FROM gochara_resonance_map WHERE chart_id = $1 ORDER BY event_class`,
    [chartId]
  )
  return rows.map((r) => r.event_class)
}
