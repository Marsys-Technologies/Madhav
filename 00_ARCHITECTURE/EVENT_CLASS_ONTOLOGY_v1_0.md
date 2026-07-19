---
artifact: EVENT_CLASS_ONTOLOGY_v1_0.md
canonical_id: EVENT_CLASS_ONTOLOGY
version: 1.0
status: CURRENT
authored_by: Claude Code (Sonnet 5), D-4a Lane A-2 ("Canonical event ontology"), 2026-07-19
governs: brahma_event_ontology (DB table; migration 388 + 456)
consumed_by:
  - Lane A-1 (shape-aware matcher, CR-47 root fix)
  - Lane A-4 (prospective ledger, claim_shape validation)
  - D-5 (Gochara-Chitra engine — resonance map §4.1, forward-sweep shape-aware output §4.4)
  - platform/src/lib/mcp/lel_event_writer.ts (LEL intake event_class validation — pre-existing)
  - platform/src/lib/lel/event_ontology_shapes.ts (shape validator this artifact's schema targets)
related_doctrine:
  - DIS.026 / DR-13 (Event-Scoring Semantics: shape/tolerance/control-mirroring) — RATIFIED
  - DIS.027 / DR-14 (Timing-System Plurality) — this ontology is generator-agnostic, not
    Vimśottarī-only, per DR-14's binding requirement
---

# Event Class Ontology — D-4a Lane A-2

## §0 — What this is

The canonical, stable event-class registry shared by the Life Event Log (LEL), the shape-aware
matcher (A-1), the prospective ledger (A-4), and — eventually — the D-5 engine's own λ_e output.
An event_class_id appearing anywhere in this system (an LEL row, a filed prediction's
`event_class`, a served λ_e curve) means the SAME thing everywhere: the same canonical temporal
shape, the same evidence discrimination, the same self-report/kill-switch handling.

**The registry is the `brahma_event_ontology` Postgres table**, not a parallel JSON/YAML file.
That table already existed before this lane (migration 388, BA-P3A "bg_ghatana", 22 classes) and
is already the enforced validation source for LEL intake
(`platform/src/lib/mcp/lel_event_writer.ts` rejects any `event_class` not present as a row here).
This lane (migration 456) EXTENDS that table with the DR-13 fields it lacked — temporal shape,
evidence requirements, self-report discrimination, kill-switch criteria — rather than creating a
second, competing ontology artifact. Duplicating a canonical registry is exactly what
`CLAUDE.md`'s versioning discipline forbids; extending the existing enforced one is the reusable
choice.

## §1 — Live coverage check (performed 2026-07-19, not assumed)

Exact query run against the live `life_events` table for the canonical chart
(`482012f1-710e-4a25-994a-93821f5871aa`, 57 rows):

```sql
SELECT category, domain, event_type, count(*)
FROM life_events
WHERE chart_id = '482012f1-710e-4a25-994a-93821f5871aa'
GROUP BY category, domain, event_type
ORDER BY category, domain;
```

Result: **13 distinct `category` values**, 49 distinct `(category, domain)` pairs, summing to all
57 rows (verified: `SELECT count(*) FROM life_events WHERE chart_id = '482012f1-…'` = 57,
matching the sum of the grouped counts).

Live categories found: `career`, `creative`, `education`, `family`, `finance`, `health`, `loss`,
`other`, `psychological`, `relationship`, `residential+travel`, `spiritual`, `travel`.

**Against the pre-work 9-category list** (health, psychological, spiritual, education, finance,
career, relationship, loss, residential+travel) — confirmed present, but INCOMPLETE: live data
also contains `creative` (2 rows: `creative/award`, `creative/modeling`), `family` (3 rows,
distinct from `relationship`), `other` (2 rows: `other/birth`, `other/psychological_shift`), and
`travel` as a category SEPARATE from the compound `residential+travel` string (1 row:
`travel/first_foreign_trip`). The pre-work list undercounted by 4 categories.

The 22 pre-existing `brahma_event_ontology` classes covered 9 of the 13 live categories
(`career`, `education`, `family`, `finance`→`wealth`+`residence`, `health`, `loss`→`transition`+
`wealth`, `relationship`, `spiritual`→`spirituality`, `residential+travel`→`residence`+`travel`
split across two existing classes). **Uncovered: `creative`, `psychological`, `other`, and the
self-report-only subset of `loss` (fraud/deception, evidentially distinct from a documented market
loss).** This migration adds 5 classes closing that gap — see §3.

## §2 — The DR-13 schema (columns added by migration 456)

| Column | Type | Meaning |
|---|---|---|
| `temporal_shape` | `point \| interval \| chain` | Canonical shape per DIS.026/DR-13. |
| `duration_prior` | `{min_days, typical_days, max_days}` | interval-only; NULL otherwise. |
| `milestone_template` | `[{milestone_id, name_en, typical_offset_days_from_first}]` | chain-only; NULL otherwise; ≥2 entries required. |
| `irreversibility_milestone` | `milestone_id` string | chain-only, nullable even then (e.g. `relocation` has none — reversible by nature). |
| `evidence_requirements` | `{valence, externally_verifiable, verification_sources[], self_report_risk, notes}` | class-specific; gain and loss classes carry DIFFERENT values (§4). |
| `self_report_non_discriminating` | boolean | true ⇒ this class's evidence is inherently self-reported; calibration must not weight it like an externally-verifiable class. |
| `kill_switch_criteria` | `[{criterion_id, description}]` | conditions that, if met by an instance, disqualify it from λ_e scoring / primary hit-rate (§5). |

A DB `CHECK` constraint enforces shape/data consistency at the row level (point ⇒ the three
shape-fields NULL; interval ⇒ `duration_prior` set, others NULL; chain ⇒ `milestone_template` set
with ≥2 entries) and that `irreversibility_milestone`, when set, names a real entry in
`milestone_template`. The TypeScript validator (`platform/src/lib/lel/event_ontology_shapes.ts`)
enforces the SAME shape discipline at the claim/instance level — see §6.

## §3 — All 27 classes

**22 pre-existing classes** (native-ratified v1.1 → shape-extended to v2.0 by this migration, no
astrological signature_model changes — this lane made zero kernel/weight/threshold/orb/valence
changes, per BRIEF_D4A's hard constraint):

| event_class_id | shape | irreversibility_milestone | self_report_non_discriminating |
|---|---|---|---|
| career_entry | point | — | false |
| career_advancement | point | — | false |
| career_change | chain | new_role_start | false |
| career_setback | interval | — | false (kill-switch: subjective_instability_perception) |
| business_launch | chain | first_revenue | false |
| education_milestone | chain | completion | false (kill-switch: declined_or_non_completion) |
| exam_outcome | point | — | false |
| marriage | point | — | false |
| romantic_start | point | — | **true** |
| separation | chain | final_decree | false |
| childbirth | point | — | false |
| parental_event | interval | — | false |
| bereavement | point | — | false |
| major_gain | interval | — | false |
| major_loss | interval | — | false |
| property_acquisition | point | — | false |
| relocation | interval | — | false |
| foreign_settlement | chain | residency_established | false |
| illness_acute | point | — | false |
| chronic_onset | interval | — | false |
| surgery | point | — | false |
| spiritual_turn | interval | — | **true** (kill-switch: internal_state_only) |

**5 new classes** (added by this migration to close the §1 coverage gap; `signature_model`
provisionally inherited from the nearest existing class and marked `"provisional": true` — a
dedicated Jyotish-domain sourcing pass for these 5 is an open item, not silently presented as
equally verified per B.10):

| event_class_id | shape | covers (live domain) | self_report_non_discriminating |
|---|---|---|---|
| achievement_recognition | point | career/award_selection, creative/award, creative/modeling, education/leadership_role | false |
| financial_deception | interval | loss/financial_deception | **true** (kill-switch: unresolved_allegation) |
| psychological_arc | interval | psychological/*, other/psychological_shift | **true** (kill-switch: congenital_onset) |
| birth_anchor | point | other/birth (the chart subject's OWN birth) | false — but **always kill-switched** (epoch_tautology: never scored, it defines t=0) |
| travel_event | point | travel/first_foreign_trip | false |

## §4 — Worked example: gain ≠ loss (the brief's explicit ask)

`major_gain` and `major_loss` are BOTH `interval`-shaped with near-identical `duration_prior`
windows, but their `evidence_requirements` differ in exactly the way a shared "finance" bucket
could not express:

- `major_gain.evidence_requirements`: `valence: "gain"`, externally verifiable via bank
  credit/payment receipt/settlement statement.
- `major_loss.evidence_requirements`: `valence: "loss"`, externally verifiable via
  brokerage/insurance statement or asset valuation record.
- `financial_deception.evidence_requirements`: `valence: "loss"` but
  `self_report_non_discriminating: true` — a fraud claim's default evidence is the native's own
  account, NOT a documentary trail, so it is deliberately NOT folded into `major_loss`'s bucket.

## §5 — Kill-switch criteria as data

Five classes carry non-empty `kill_switch_criteria`, each a `{criterion_id, description}` pair a
downstream harness (A-3/A-5) reads mechanically rather than re-implementing ad hoc exclusion
logic per consumer:

- `career_setback.subjective_instability_perception` — perceived-but-undocumented instability.
- `education_milestone.declined_or_non_completion` — a declined offer or partial program must not
  be scored as if the completion milestone fired.
- `spiritual_turn.internal_state_only` — a devotional shift with no external marker.
- `financial_deception.unresolved_allegation` — an uncorroborated fraud claim.
- `psychological_arc.congenital_onset` — a condition present since birth (e.g. congenital
  stammering, per the native-ratified date-tightening correction) has no discrete trigger
  transit; scoring it against a timing model would be a category error, not a measurement.
- `birth_anchor.epoch_tautology` — the chart's own birth is the chart's t=0, always excluded.

## §6 — Shape enforcement (the schema-violation acceptance proof)

`platform/src/lib/lel/event_ontology_shapes.ts` exports `validateClaimShape(ontology, claim)` — a
pure function A-1 (matcher) and A-4 (prospective ledger) import to reject a claim/event whose
submitted shape does not match its declared class's canonical shape. Its test file
(`event_ontology_shapes.test.ts`, 15 tests, all passing) demonstrates, among other cases, the
brief's own worked example verbatim: a `point`-shaped claim submitted against `major_gain`
(canonically `interval`-shaped) is REJECTED with `SHAPE_MISMATCH`. This is Lane A-2's gate-item-3
acceptance proof ("ontology published; matcher + ledger provably consume its shapes —
schema-violation test").

## §7 — Generator-agnosticism (DIS.027/DR-14 compliance)

Nothing in this ontology assumes Vimśottarī as the sole or default timing generator.
`temporal_shape`, `duration_prior`, `milestone_template`, `evidence_requirements`, and
`kill_switch_criteria` are all timing-system-agnostic — they describe the EVENT, not which daśā
system, transit rule, or return cycle might time it. This is a deliberate design choice matching
DR-14's binding requirement that windows be generated by a plurality of systems, none served as
exclusive.

## §8 — What this lane explicitly did NOT do

- Did not modify the `life_events` table schema (that is Lane A-1's migration; if A-1 has not yet
  landed an `event_class` column on `life_events`, this ontology is ready to be referenced by that
  column the moment it exists — no coordination blocker on this lane's side).
- Did not touch any kernel weight, threshold, orb, or valence computation.
- Did not touch the FROZEN orchestrator contract.
- Did not re-derive or assert any astrological signature_model for the 22 pre-existing classes —
  those values are untouched (v1.1 → v2.0 version bump reflects only the DR-13 field additions).
