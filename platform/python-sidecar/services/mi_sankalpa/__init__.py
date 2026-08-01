"""
`mi_sankalpa` (Saṅkalpa — "the elected resolve") — the Unified Intervention Ledger.
L5 Mīmāṃsā-seated, registry item 42.

Spec: `00_ARCHITECTURE/llm_consumption_audit/briefs/kala_elevation/
KALA_W4_UPAYA_DESIGN_v1_0.md` (v1.1) §4 (the Lane S design), §4.3 (this package's writer
contract). Execution contract: `SHAD_DARSHANA_BRIEF_v2_0.md` §3 W4, §2.5.

── WHAT THIS PACKAGE DOES ──────────────────────────────────────────────────────────────────
`mimamsa_intervention_ledger` rows are FILED live, at serve time, through the sanctioned HTTP
action (`platform-mcp/src/lib/intervention_filing.ts`'s `fileInterventionFalsifier` — the
ṢAḌ-DARŚANA W4 Lane S spine PR) — never inserted by this package (ruling S-1: the prediction
spine is `brahma_prospective_ledger`; this table only REFERENCES it). This package's build-time
job over the rows that already exist is:

  1. FALSIFIER RESOLUTION FIRST (§4.3, before any arm transition): score every unresolved
     ledger row's own falsifier/window against the LEL, reusing
     `services/mi_bhara/living_lel.py`'s `score_predictions_against_event` — the design's own
     binding instruction ("reuse ... rather than writing a second matcher") — and link
     `outcome_event_id` where a matching LEL event is found.
  2. STUDY-ARM RECLASSIFICATION: `elected_pending` / `acted_with_election` / `elected_not_acted`
     are re-derived, deterministically, from each row's own already-native-attested
     `performed`/`performed_at` fields against its `elected_window` — never fabricated, and
     never re-deriving a combination the design's own §4.3 table left unspecified (see
     `arms.classify_study_arm`'s docstring).
  3. `acted_without_election` (the fourth arm) is ORIGINATED by this writer alone: an LEL event
     whose class already appears among this chart's own filed interventions, with no existing
     elected_window covering it, becomes a new row — the one arm this package writes rather
     than merely reclassifies.

── THE STATUS-PRESERVING IDEMPOTENCY GUARD (§4.3, load-bearing) ───────────────────────────
Adjudicated and native-attested rows are IRREPLACEABLE. The writer's delete-then-insert scope
(§N.3, transposed from `mi_bhavisya`'s `... AND lifecycle_status IN ('pending','due')`) is
`study_arm = 'elected_pending' AND performed IS NULL AND outcome_event_id IS NULL` — and this
package additionally guarantees the round trip is loss-free: every row matching that predicate
is READ before it is deleted and is re-inserted (verbatim, or upgraded with a freshly-resolved
`outcome_event_id`) in the SAME pass, under the SAME `intervention_id`. A row is dropped from
that round trip ONLY when it has just been protected by this same pass's own resolution step
(an outcome link, or a native attestation read elsewhere) — never silently.

── LAYOUT ───────────────────────────────────────────────────────────────────────────────────
    arms.py   pure, DB-free study-arm classification + the LEL-matcher reuse wrapper
    db.py     the ONLY module in this package that touches a database
"""
