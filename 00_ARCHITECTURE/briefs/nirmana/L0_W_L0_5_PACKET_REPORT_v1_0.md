---
artifact: L0_W_L0_5_PACKET_REPORT
version: 1.0
status: CURRENT
packet: W-L0-5 (Provenance completion)
session: l0/nirmana-elevation-20260921 execution session (worktree /Users/Dev/madhav-l3/l0-exec)
date: 2026-09-25
plan: MADHAV_DATA_PLANE_L0_BRAHMAGYAN_STRATEGY_v2_1.md
---

# W-L0-5 Packet Report — Provenance completion

Per-packet report per the execution kickoff. Convention: change → detector before →
detector after → blocks. All production figures measured live on 2026-09-25 via
read-only queries; this session writes nothing to production. Migration 1124 is
HELD (ledger unreconciled; madhav-65 owns reconciliation). All code below is
uncommitted in the worktree.

## Packet scope (strategy §4.2 W-L0-5, five items)

`school` on sutravali_rules / bg_transit_rules / bg_parihara_rules; provenance
columns on both vidhi tables; DP §4.3's five rule qualification states on
bg_rules; and a standing detector for the defect class "a registry
english_description claims a provenance the table does not have" (the
migration-1079 finding, generalised — strategy §2.1 boundary table marked it
**gap**: "1079 was a one-off correction; the description-vs-table check has no
detector").

## Verified facts (production, 2026-09-25)

**sutravali_rules (3,002 rows):** 0 text-join misses to classical_texts, 0
license-cleared misses, 0 chunk-witness misses → every row backfills to
QUALIFIED_EXECUTABLE. Derived school distribution: parashari 2,839 / jaimini 112
/ nadi 39 / hellenistic 12. classical_texts: 16 rows, all license_cleared=true.

**bg_transit_rules (76 rows, 15 distinct citations):** 19 ×
`BPHS Ch.29 (Gochara Phala — Transit Results)`; 51 Phaladipika/Phaladeepika
variants (page-anchored `Phaladipika Adh. XXVI, Sloka N — phaladeepika:PG322/
PG323:C1 (Sastri trans. 1950)` incl. the `Phaladeepika ch.26 §double-gochara`
composites that name BPHS/Saravali/Jataka Parijata secondarily); 6 ×
`UNSOURCED —` Rahu/Ketu vedha rows (retained per B.10). → 70 mapped to a school,
6 NULL by design. rule_type census: 43 favourable / 26 unfavourable / 7
double_transit; all 6 UNSOURCED rows are favourable (rahu 3, ketu 3).

**bg_parihara_rules (60 rows):** 60/60 join brahma_dosha_catalog via
dosha_canonical_id; derived school parashari 60/60.

**Vidhi corpus:** 14 intent floors / 409 floor items / 60 primitives.
Per-intent item counts (measured): biography_narrative 33, career_deepdive 39,
education_deepdive 34, general_synthesis 32, health_deepdive 43,
marriage_deepdive 39, panoramic_breadth 8, progeny_deepdive 30, retrieval_only 1,
ritual_yajna 33, spirituality_deepdive 35, structure_read 6,
undertaking_election 33, wealth_deepdive 43. Sourced intents (8) carry 280 items
(43+39+35+34+30+33+33+33) — the migration's inheritance backfill count.

**Apply-order probe:** information_schema shows `unlinked_reason`, `school`,
`qualification_state`, `source_authority`, `source_ref` all ABSENT in production
→ 1123 is unapplied; 1124 must apply after 1123 (the migration refuses otherwise).

## Item 1 — `school` + `qualification_state` on sutravali_rules

**Change:**
- `platform/python-sidecar/brahmagyan/l0_rules.py` — `seed_rules` loads
  `SELECT text_id, school, license_cleared FROM classical_texts` once and
  derives both fields per rule at write time: school = the text's school (never
  authored per rule); qualification_state = QUALIFIED_EXECUTABLE (license-cleared
  text) / UNQUALIFIED_SOURCE (known text, rights unresolved) /
  READABLE_NOT_EXECUTABLE (text_id not in classical_texts). UNSUPPORTED_SCOPE
  and METHOD_INAPPLICABLE are application-time verdicts about a rule's USE and
  are never stored. New INSERT params are appended after the existing ones, so
  the W-L0-3 positional pin test (params[10]/[11]) is untouched.
- Migration 1124 (a): DDL + deterministic backfill; a pre-flight REFUSES if any
  license-cleared rule lacks an exact (text_id, verse_ref) chunk witness
  (production: 0) — a licensed-but-witnessless row is a state the vocabulary
  cannot name honestly, so the migration will not force a label onto it.
  CHECK constraint `sutravali_rules_qualification_state_vocab` carries all five
  DP §4.3 states (the two application-time states are in the vocabulary so a
  future consumer column or a ruled change can store them without DDL).

**Detector before:** strategy §2.1 DP02 row — "sutravali_rules carries text but
0.6 % concept links"; §1.2 per-asset verdict: bg_rules source-present PARTIAL
("text_id on all 3,002; no school").
**Detector after:** 1124 postflight — `school IS NULL` count must be 0 and
QUALIFIED_EXECUTABLE must equal 3,002, else the migration aborts. Contract test
`tests/unit/migrations/l0_provenance_completion.test.ts` (6/6, real-PostgreSQL
block included) asserts the vocab CHECK rejects an invented state and the
witness guard refuses a licensed-without-witness fixture.

## Item 2 — `school` on bg_transit_rules

**Change:**
- `platform/python-sidecar/brahmagyan/l0_transit.py` — `school_for_citation()`
  citation→text_id map joined to classical_texts (never a hardcoded school;
  the map resolves the TEXT, the table carries the school). ILIKE order is
  load-bearing: `%phalad%` first (the §double-gochara composites name BPHS /
  Saravali / Jataka Parijata secondarily), then `BPHS%`, `%Saravali%`,
  `%Jataka Parijata%`, `%Uttara Kalamrita%`; the `UNSOURCED%` guard excludes
  the six retained Rahu/Ketu rows whose own citation text names Phaladipika —
  no school is ever guessed.
- Migration 1124 (b): same map as SQL CASE, same guard order; rowcount pinned
  at 70 mapped / 6 NULL.

**Detector before:** §1.2 — bg_transit_rules PARTIAL ("per-row citation, no
school; provenance not table-wide per 1079").
**Detector after:** 1124 postflight — school NOT NULL = 70 AND no non-UNSOURCED
row left NULL. The contract test proves guard order with sentinel-school
fixture texts: the §double-gochara composite maps to phaladeepika, not bphs;
the UNSOURCED rows stay NULL despite naming Phaladipika.

## Item 3 — `school` on bg_parihara_rules

**Change:**
- `platform/python-sidecar/pipeline/orchestrator/writers/bg_parihara_rules.py` —
  `_DOSHA_QUERY` selects `school`; it flows through `fetch_parihara_rows` into
  the `_upsert_parihara` INSERT/UPDATE. No new join (the writer already queries
  the catalog).
- Migration 1124 (c): backfill from brahma_dosha_catalog.school, rowcount
  pinned at 60.
- `python-sidecar/tests/l0/test_bg_parihara_rules_dictrow.py` — fixture dosha
  rows gained the `school` column; the fetch test now asserts the derived value.

**Detector before:** §1.2 — bg_parihara_rules PARTIAL ("source text and
chapter, no school").
**Detector after:** 1124 postflight — school='parashari' = 60.

## Item 4 — provenance columns on the vidhi tables

**Change:**
- `platform/src/lib/vidhi/types.ts` — optional `source_ref?: string | null` on
  `VidhiPrimitive` and `IntentFloor`.
- `platform/src/lib/vidhi/registry_data.ts` — source_ref authored on 10
  primitives (medical_read 'BPHS Ch.18 / Aṣṭāṅga Hṛdayam',
  sensitive_degree_check 'MC-029 (Śodhana Builder T6)', the eight ṢAḌ-DARŚANA W5
  kala primitives 'SHAD_DARSHANA_BRIEF_v2_0.md §3 W5') and 8 floors
  (wealth/career/spirituality/education/progeny + the three W5 routing floors).
- `platform/scripts/census/dump_vidhi_registry.ts` — materializes
  `source_ref ?? null` on both sides so the parity gate compares the field.
- `platform/python-sidecar/pipeline/orchestrator/writers/bg_vidhi_primitives.py`
  — `_SOURCE_REFS` map + `_SOURCE_AUTHORITY`; the upsert writes both columns
  (a `_SOURCE_REFS` pid→ref dict rather than re-touching all 60 tuple literals;
  the parity gate enforces equivalence).
- `platform/python-sidecar/pipeline/orchestrator/writers/bg_vidhi_floors.py` —
  `_FLOOR_SOURCE_REFS` + `_SOURCE_AUTHORITY`; floor ITEMS inherit their intent's
  provenance at write time (declared derivation, mirrored by the 1124 backfill).
- Migration 1124 (d): `source_authority TEXT NOT NULL DEFAULT
  'src/lib/vidhi/registry_data.ts'` + `source_ref TEXT` on vidhi_primitives /
  vidhi_intent_floors / vidhi_floor_items; backfills pinned at 10 primitives /
  8 floors / 409 items inherited (280 non-null).

**Detector before:** §1.2 — bg_vidhi_floors and bg_vidhi_primitives FAIL on
"source present" (no provenance column / version only).
**Detector after:** vidhi parity gate PASS (14/14 floors) WITH the new field in
the compared shape on both sides; writer dumps verified: primitives 10/60 with
source_ref, floors 8/14 with source_ref; 1124 postflight pins 10/8/280 and the
constant source_authority on all three tables.

## Item 5 — the truthfulness repair and the standing detector

**The 642 defect (found by measurement, repaired in this packet):** production
`asset_registry.bg_vidhi_floors.english_description` claims "12/14 intent floors
are writer-tagged [MANDATORY] (settled)". The writer source
(`bg_vidhi_floors.py` FLOORS, mirrored in `registry_data.ts`) carries exactly
1 [MANDATORY] (spirituality_deepdive), 2 [CANDIDATE] (education_deepdive,
progeny_deepdive), 11 untagged.

**Change:**
- `platform/scripts/seed/asset_registry_seed.ts` — truthful replacement text
  (base sentence + "per the writer source, 1/14 … [MANDATORY]
  (spirituality_deepdive), 2/14 … [CANDIDATE] (education_deepdive,
  progeny_deepdive — VIDHI-PURNATA P-2, not yet fully ratified), and 11/14
  carry no writer tag").
- Migration 1124 (e): the swap is pinned to the exact 642 composite pre-state
  and refuses anything else ("moved on by another session" is a refusal, not an
  overwrite); re-application accepts its own post-state.

**Standing detector — `platform/scripts/__tests__/l0_description_truthfulness.test.ts`
(10/10 green).** Fail-closed claim grammar over all 40 bg_* descriptions:
1. writer-tag distribution claims (642 class) — verified against the writer's
   own tag distribution parsed from the FLOORS block; a claim on an asset with
   no registered truth source is a violation, not a skip;
2. category-count claims ("N classical transit rules: A favourable, …") —
   verified against the writer's rule literals plus internal arithmetic;
3. provenance-column name claims (backticked names from the provenance
   vocabulary; 1079 class) — the asset's registered writer must actually write
   the column. No current description makes such a claim; synthetic tests prove
   the checker bites (including the 642 text verbatim, which it flags as
   "claims 12/14 MANDATORY; the writer source carries 1/14").

Boundary, stated in the detector header: it verifies description↔writer truth.
Description↔production drift belongs to the census/integrity_check_sql path.

**Detector before:** none standing (strategy §2.1: **gap**).
**Detector after:** the suite above runs in CI on every change to the seed or
the writers; the corpus test covers all 40 assets and cannot silently shrink
(40-count anchor, same convention as l0_registry_parity).

## Item 6 — migration 1124 authored, rehearsed, HELD

`platform/migrations/1124_nirmana_l0_provenance_completion.sql`
(618/1075/1120/1123 pattern): BEGIN/COMMIT; measured pre-flight guards (tables
present via to_regclass; `unlinked_reason` present = 1123-first ordering; counts
3002/76/60/14/409/60, UNSOURCED=6, parihara-join=60; licensed-without-witness=0
refusal; the post-1123 digest `f1d56d0c…` re-verified — 1124 adds columns
OUTSIDE the digest vector and never touches it); state A/B detection on
`sutravali_rules.school`; IF-NOT-EXISTS DDL; rowcount-pinned backfills; the
description swap pinned to both states; full postflight; 10 column comments;
VERIFY/DOWN footer. Number 1124 confirmed free across every origin/* head and
local branch in both migration trees (heads: platform/migrations 1123 —
1120–1123 are this session's HELD files — and supabase/migrations 1090).

**Rehearsal (fixture PostgreSQL 17, throwaway instance):** the contract test's
real-PostgreSQL block builds the measured production shape (3,002 rules with
chunk witnesses, 76 transit rows incl. guard-precedence fixtures, 60 parihara,
60/14/409 vidhi with the per-intent distribution) and verifies: apply → all
postflight states exact (parashari/QUALIFIED_EXECUTABLE 3,002; transit
19+51+NULL 6; parihari 60; vidhi 10/8/280; description post-state; vocab CHECK
present) → re-apply is a verifying no-op → refusals fire on digest tamper,
missing chunk witness, deviating count, and a moved-on description.

**Gates:** campaign vitest set 7 files / 54 passed (incl. 1123's suite re-run
green against the same fixture instance); python-sidecar 179 passed / 1 skipped
(tests/l0 + l0_rules_yoga + l0_transit_fk + has_writer_completeness);
`tsc --noEmit` clean; eslint clean on every touched TS file; vidhi parity gate
PASS; writer dumps match the migration's pinned counts.

## Caveats (recorded, not repaired here)

1. **RESOLVED 2026-09-25 (post-merge) — Writer/production drift on
   bg_transit_rules.** This caveat originally recorded that production carried
   the 1078/1079-repaired page-anchored citations while this worktree's
   `l0_transit.py` carried the pre-1078 constants, and that production's 76 rows
   (43 favourable) diverged from the writer boundary of 75 (42+26+7). Both
   halves dissolved when this worktree integrated `origin/main` (`b6690928f`,
   merge `0411c5a46`): the repaired writer now emits 69 owned rows (43
   favourable + 26 unfavourable) + 7 retained migration-owned double_transit =
   **76 — exactly production**, and its citation strings match production
   verbatim (36 page-anchored Phaladipika + 6 UNSOURCED Rahu/Ketu + 19 "BPHS
   Ch.29" + 8 other Phaladeepika on the owned rows; 7 Phaladeepika on
   double_transit). The seed description's 76/43/26/7 claim (main's 1079 text)
   verifies green against the repaired writer in the standing detector. The
   "one extra live row" finding is withdrawn: it was measured against the
   pre-repair writer.
2. **bg_vidhi_primitives catalog_status:** production reads CURRENT while the
   seed carries DRAFT. Flagged for the strategy session; not a W-L0-5 repair.
3. **UNSOURCED rows keep NULL school by design (B.10)** — a non-NULL school on
   those six rows would be an invented source, the exact boundary this packet
   exists to defend. Post-merge the six rows are writer-owned (the repaired
   writer emits them via `RAHU_KETU_HOUSE_VEDHA_UNSOURCED`) and the writer
   derives the same NULL the migration backfill assigns — the two paths agree.

## Blocks — RE-SCOPED 2026-09-25 (strategy-session correction, independently verified)

The original block read: "1124 applies only after madhav-65 reconciles
`_migrations_applied`." The strategy session corrected the premise; every load-
bearing claim was re-verified here by structural probe, not by reading the
ledger:

1. **The ledger is not untrustworthy.** `_migrations_applied` holds 869 rows;
   exactly six in 1060–1130 (1070, 1075–1079), all correct. 1075–1079 live in
   `platform/supabase/migrations/` on `origin/main` (`b6690928f`, PR #2727) —
   this session had inventoried only `platform/migrations/` on a stale branch.
2. **The real unrecorded-but-live set is eight gochara files** on
   `origin/l3/gochara-autonomous-wp0-7`, applied out-of-band by
   `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/scripts/apply_migration.sh`,
   which never writes a ledger row (grep count 0; application recorded in
   commit `5ee6280bd`; the 1075/1076→1080/1081 renumber in `aa92cbc4e`).
   Structural probes against production this session: **1080, 1081, 1082,
   1083, 1084, 1087, 1091 all live** (columns, tables, constraints, trigger,
   function, registry edges, cutover snapshot and ka_gochara repin all
   present). **1086 is NOT applied** — the old ga_strength digest spec
   `3743484c…` is still active and the new spec `52a0d253…` is absent (an
   unrelated retired row `7251b119…` also present). This sharpens the
   correction's "partial/ambiguous": 1086 is simply pending, so it is not a
   ledger-honesty gap either — it will apply when the branch merges.
3. **Numbers 1092–1130 are free** on every origin/* head in both migration
   directories except this session's own 1120–1124.

Disposition: the ledger-reconciliation precondition on 1120–1124 is **lifted**;
the sole remaining gate was the 76-vs-75 `bg_transit_rules` row question, which
**dissolved** as recorded in caveat 1. 1124's pinned counts
(3002/76/60/14/409/60, UNSOURCED=6, post-1123 digest `f1d56d0c…`) were
re-verified against production after the merge. The prohibition on reading
`_migrations_applied` to decide deployment state **stands** — this re-scope was
reached structurally.

**1124 (and 1120–1123) are therefore ready to apply on the strategy session's
go-ahead.** The writer changes and 1124 must still roll out TOGETHER — the
writers emit the new columns and will error against the pre-1124 schema (the
DOWN footer records the symmetric requirement).

Filed, not executed (outside this packet's mandate):

- **Recurrence fix:** `apply_migration.sh` must write its ledger row (filename,
  sha256, `sql_identity`) or be forbidden in favour of `migrate.ts --target`.
  Without it the next out-of-band apply drifts again. Filed to the strategy
  session as `L0_DEFECT_APPLY_MIGRATION_LEDGER_WRITING_v1_0.md`.
- **Gochara ledger backfill** (1080–1084, 1087, 1091 — seven live-but-unrecorded
  files) belongs to the L3 gochara lane, not madhav-65 and not this session.
  Re-apply on merge is idempotent (`IF NOT EXISTS` / guarded `array_append`),
  so this is ledger honesty, not safety.

## Packet status

W-L0-5 complete pending migration application: all five strategy items executed
(writer derivations, vidhi provenance columns, the 642 truthfulness repair, the
standing detector), migration 1124 rehearsed and ready to apply on the strategy
session's go-ahead — both original holds (the ledger premise and the 76-vs-75
row question) are resolved as recorded above. Every detector green, re-verified
after the `origin/main` integration (`0411c5a46`): campaign vitest set 7 files /
54 passed, python-sidecar 179 passed / 1 skipped, `tsc --noEmit` clean, eslint
clean, vidhi parity gate PASS.
