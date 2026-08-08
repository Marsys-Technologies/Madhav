/**
 * event_classes.ts — TS mirror of the canonical 27 life-event classes.
 *
 * SERVE-SIDE MIRROR. The single source of truth is the Python module
 * ``brahmagyan/l0_ghatana.py`` (`EVENT_CLASSES`), which seeds the
 * `brahma_event_ontology` DB table (migration 388, extended by migration 456
 * with the DR-13 shape/evidence fields). This file must stay in exact id
 * parity with that source; `python-sidecar/tests/test_event_classes_parity.py`
 * asserts member-for-member agreement. Change one, that test fails until you
 * change the other.
 *
 * ZERO-IMPORT: this file must not import from any other project module so it
 * can be consumed by any layer without creating circular dependencies (same
 * discipline as ``domain_vocabulary.ts``).
 *
 * WHY THIS FILE EXISTS (ADHIṢṬHĀNA campaign, Lane A4, 2026-08-08)
 * -----------------------------------------------------------------
 * Before this module, `l0_ghatana.EVENT_CLASSES` (the build-side source of
 * truth for event classification) had NO TypeScript mirror. TS code that
 * needed the same 27 classes either hardcoded a stale subset (see the
 * now-corrected "22 classes" comments in `lel_event_writer.ts`) or validated
 * an event_class purely against a live DB round-trip to `brahma_event_ontology`
 * with no static, zero-dependency id set to check against ahead of a query.
 * This module fills that gap, mirroring the `domain_vocabulary.ts` SSoT+mirror
 * pattern established by the ŚABDA-ŚUDDHI campaign (R7).
 *
 * NOTE ON SCOPE: this mirror carries `event_class_id`, `name_en`, `domain`,
 * and `lel_category` for each class — the identity + classification fields.
 * It intentionally does NOT duplicate the heavier per-class fields
 * (`signature_model`, `base_rate_by_age`, `citations`, `temporal_shape`,
 * `duration_prior`, `milestone_template`, `evidence_requirements`, …) that
 * live in `brahma_event_ontology` and are already read live by TS callers via
 * `platform/src/lib/lel/event_ontology_shapes.ts`'s `getEventClassOntology()`.
 * Mirroring those too would create a second drift-prone copy of data the DB
 * table already serves authoritatively; the identity set is what needed (and
 * lacked) a static, zero-import mirror.
 */

/**
 * One life-event class's identity + classification fields, mirroring the
 * corresponding subset of an `l0_ghatana.EVENT_CLASSES` entry / a
 * `brahma_event_ontology` row.
 */
export interface EventClassEntry {
  readonly event_class_id: string
  readonly name_en: string
  readonly domain: string
  readonly lel_category: string
}

/**
 * The canonical 27 life-event classes. Mirrors `l0_ghatana.EVENT_CLASSES`
 * member-for-member (id, name_en, domain, lel_category) — the same set seeded
 * into `brahma_event_ontology` by migration 388 (22 classes) + migration 456
 * (5 DR-13 additions: achievement_recognition, financial_deception,
 * psychological_arc, birth_anchor, travel_event).
 *
 * Order matches the Python source's declaration order.
 */
export const EVENT_CLASSES: readonly EventClassEntry[] = [
  { event_class_id: 'career_entry', name_en: 'Career Entry', domain: 'career', lel_category: 'career' },
  { event_class_id: 'career_advancement', name_en: 'Career Advancement', domain: 'career', lel_category: 'career' },
  { event_class_id: 'career_change', name_en: 'Career Change', domain: 'career', lel_category: 'career' },
  { event_class_id: 'career_setback', name_en: 'Career Setback', domain: 'career', lel_category: 'career' },
  { event_class_id: 'business_launch', name_en: 'Business Launch', domain: 'career', lel_category: 'career' },
  { event_class_id: 'education_milestone', name_en: 'Education Milestone', domain: 'education', lel_category: 'education' },
  { event_class_id: 'exam_outcome', name_en: 'Exam Outcome', domain: 'education', lel_category: 'education' },
  { event_class_id: 'marriage', name_en: 'Marriage', domain: 'relationship', lel_category: 'relationship' },
  { event_class_id: 'romantic_start', name_en: 'Romantic Relationship Start', domain: 'relationship', lel_category: 'relationship' },
  { event_class_id: 'separation', name_en: 'Separation', domain: 'relationship', lel_category: 'relationship' },
  { event_class_id: 'childbirth', name_en: 'Childbirth', domain: 'progeny', lel_category: 'family' },
  { event_class_id: 'parental_event', name_en: 'Parental Event', domain: 'family', lel_category: 'family' },
  { event_class_id: 'bereavement', name_en: 'Bereavement', domain: 'transition', lel_category: 'loss' },
  { event_class_id: 'major_gain', name_en: 'Major Financial Gain', domain: 'wealth', lel_category: 'finance' },
  { event_class_id: 'major_loss', name_en: 'Major Financial Loss', domain: 'wealth', lel_category: 'loss' },
  { event_class_id: 'property_acquisition', name_en: 'Property Acquisition', domain: 'residence', lel_category: 'finance' },
  { event_class_id: 'relocation', name_en: 'Relocation', domain: 'residence', lel_category: 'residential' },
  { event_class_id: 'foreign_settlement', name_en: 'Foreign Settlement', domain: 'travel', lel_category: 'travel' },
  { event_class_id: 'illness_acute', name_en: 'Acute Illness', domain: 'health', lel_category: 'health' },
  { event_class_id: 'chronic_onset', name_en: 'Chronic Illness Onset', domain: 'health', lel_category: 'health' },
  { event_class_id: 'surgery', name_en: 'Surgery', domain: 'health', lel_category: 'health' },
  { event_class_id: 'spiritual_turn', name_en: 'Spiritual Turn', domain: 'spirituality', lel_category: 'spiritual' },
  { event_class_id: 'achievement_recognition', name_en: 'Achievement / Recognition', domain: 'general', lel_category: 'creative' },
  { event_class_id: 'financial_deception', name_en: 'Financial Deception / Fraud Loss', domain: 'wealth', lel_category: 'loss' },
  { event_class_id: 'psychological_arc', name_en: 'Psychological / Speech-Pattern Arc', domain: 'character', lel_category: 'psychological' },
  { event_class_id: 'birth_anchor', name_en: "Birth (Subject's Own, Chart Epoch)", domain: 'transition', lel_category: 'other' },
  { event_class_id: 'travel_event', name_en: 'Discrete Travel Event', domain: 'travel', lel_category: 'travel' },
] as const

/** Just the ids, in the same order as `EVENT_CLASSES`. */
export const EVENT_CLASS_IDS: readonly string[] = EVENT_CLASSES.map((e) => e.event_class_id)

export type EventClassId = (typeof EVENT_CLASSES)[number]['event_class_id']

const EVENT_CLASS_ID_SET: ReadonlySet<string> = new Set(EVENT_CLASS_IDS)

const EVENT_CLASS_BY_ID: ReadonlyMap<string, EventClassEntry> = new Map(
  EVENT_CLASSES.map((e) => [e.event_class_id, e])
)

/**
 * Check whether a string is a member of the canonical 27-class event
 * vocabulary (mirrors `isCanonicalDomain` in `domain_vocabulary.ts`).
 */
export function isKnownEventClass(id: string | null | undefined): id is EventClassId {
  return id != null && EVENT_CLASS_ID_SET.has(id)
}

/** Look up the identity/classification row for a known event_class_id, or undefined. */
export function getEventClassEntry(id: string | null | undefined): EventClassEntry | undefined {
  if (id == null) return undefined
  return EVENT_CLASS_BY_ID.get(id)
}
