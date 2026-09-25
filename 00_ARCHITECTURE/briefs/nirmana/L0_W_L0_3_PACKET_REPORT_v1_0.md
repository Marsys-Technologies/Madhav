---
artifact: L0_W_L0_3_PACKET_REPORT
version: 1.0
status: CODE_COMPLETE_MIGRATION_HELD
packet: W-L0-3 (one identity, linked rules)
session: NIRMANA_L0_BRAHMAGYAN_EXECUTION_20260921
branch: l0/brahmagyan-exec
date: 2026-09-26
---

# W-L0-3 Packet Report — One identity, linked rules

This report discharges the owed packet report for commit `118aa9a65` (2026-09-25, marked
"PARTIAL — packet report pending" at commit time so the work was not at risk). The code
landed then; the coverage numbers and the measured-ceiling statement land here.

## Packet scope (strategy §4.2 W-L0-3, two items)

1. **sutravali_rules concept links.** 17 of 3,002 rules carry a concept link. Add the
   link where a rule qualifies a catalogued concept, or an explicit `unlinked_reason` on
   the remainder — coverage reported as a measured number with a stated ceiling, never as
   a target.
2. **brahma_remedy_corpus.source_canonical_id.** One identity space with spelling drift
   (BPHS vs bphs, Phaladeepika vs phaladeepika, classical_tradition naming no work). Fix
   by normalization plus alias entries, not redesign.

## Item 1 — sutravali_rules: the 17 links were partly false; the honest number is 7

**Defect found while building the link detector** (this is why the packet says "measured,
never a target"): of the 17 production links, **11 are provably false attributions** —

- 6 × `parijata`: the Tier-1 bare-name pattern matched "Parijata" inside parenthetical
  *work citations* of the form "(Jataka Parijata, ch. 8)" — a source text, not a concept
  the rule qualifies;
- 5 single-row collisions (`particular`, `raja`, `sunapha`, `neecha_bhanga`, `durudhura`)
  where a common English word matched a yoga name.

**Repair** (`platform/python-sidecar/brahmagyan/l0_rules.py`, W-L0-3 hunks riding commit
`1c4035132` — shared-file attribution disclosed in both commit bodies):

- `_CITATION_PAREN_RE` + `_inside_citation_paren` (l0_rules.py:200-216): any match whose
  span sits inside a parenthetical group carrying a citation marker (chapter/verse
  locator word or a digit) is suppressed. Parenthesized concept names *without* a marker
  — e.g. "(Sunapha)" naming the yoga a sloka belongs to — stay eligible.
- Sentence-window truncation (l0_rules.py:1431-1449): the 40/160 raw detection window is
  cut at sentence boundaries (". ") so a yoga named in a *neighbouring* sentence (chapter
  header, next/prior verse) can no longer be attributed to this rule. Same-sentence
  attribution is the defensible claim.
- `unlinked_reason` is recorded on **every** rule: NULL when linked,
  `ambiguous_reference` when candidates collided, `no_concept_reference_in_window`
  otherwise; the migration adds a third value, `reference_not_in_catalog`, for candidates
  naming no catalogued yoga. Two CHECK constraints make the accounting structural: linked
  ⇒ no reason; unlinked ⇒ a reason from the closed three-value vocabulary.

**Coverage, measured** (deterministic replay of all 36 movable rows — 17 linked + 19
extraction_pass_log-flagged ambiguous — against the fixed detector, row-by-row backfill
carried in migration 1123; digest simulated read-only against production 2026-09-25):

| outcome | rows |
|---|---|
| link survives replay (katanidhi ×2, durudhura ×2, sunapha ×1, ubhayachari ×1) | 6 |
| false link killed → `no_concept_reference_in_window` | 11 |
| ambiguous, stays `ambiguous_reference` | 7 |
| ambiguous → `no_concept_reference_in_window` | 9 |
| ambiguous → `reference_not_in_catalog` ('second', 'khala' — no such catalogued yoga) | 2 |
| ambiguous resolves to a real link (cf36fd63… → sunapha) | 1 |
| **final linked** | **7 of 3,002** |

**The ceiling statement.** 7 of 3,002 (0.23%) is the measured coverage, and it is a
*ceiling*, not a floor to grow from: the detector links only same-sentence,
non-citation-context references to catalogued concepts, which is the strongest claim the
text supports. The remaining 2,995 rules name no catalogued concept in their own sentence
— they carry an explicit reason, not a silent NULL. Coverage must never rise by loosening
the window or the vocabulary; if the corpus is re-extracted with more catalogued
concepts, the number moves and is re-measured then.

## Item 2 — remedy corpus: one identity space, drift normalized, aliases registered

**Drift measured on production 2026-09-25, re-verified unchanged 2026-09-26** (1123
unapplied): `BPHS` ×193, `Phaladeepika` ×11, `Tajaka` ×3, `bphs_jaimini` ×1,
`classical_tradition` ×80 — alongside already-correct `bphs` ×7 and `phaladeepika` ×4.
Same work, two spellings, one identity space: the violation exactly as the packet names
it.

**Repair** (`platform/python-sidecar/brahmagyan/l0_remedy_corpus.py`, commit `118aa9a65`)
— normalization plus alias entries, not redesign:

- `canonical_source_id()` — a single choke point in `build_all_remedies` through which
  every hand-authored row's `source_canonical_id` passes;
- `_SOURCE_ID_ALIASES`: `BPHS`→`bphs`, `Phaladeepika`→`phaladeepika`,
  `Tajaka`→`tajaka_neelakanthi`;
- `bphs_jaimini`→`jaimini_sutram` is an **attribution fix** (the row's own citation
  names Jaimini), not an alias;
- `classical_tradition` is a bucket, not a work: exactly 1 of the 80 rows carries
  `source_citation = 'Muhurta Chintamani, classical Jyotish muhurta text'` (re-verified
  2026-09-26) and resolves to `muhurta_chintamani`; the other 79 name no catalogued work
  and pass through unchanged — measured, not assumed;
- migration 1123 registers the observed drift spellings as **synonyms on the
  brahma_ontology text-class rows**, so both surfaces (remedy corpus, ontology) resolve
  to one identity.

## Detector output, before and after

| detector | before | after |
|---|---|---|
| production `sutravali_rules` | 3,002 rows / 17 linked / no `unlinked_reason` column (re-verified 2026-09-26 — column absent, links 17: state A holds, 1123 unapplied) | — |
| 1123 read-only digest simulation (2026-09-25) | old digest `87b69704…` verified before any change | 3,002 rows / **7 linked** / 7 ambiguous / 2 reference_not_in_catalog / **0 XOR violations** → new digest `f1d56d0c…` |
| `bg_rules.integrity_check_sql` (migration-618 contract) | yoga link count pinned at 17 | tightened contract: 17→7, XOR pin `(yoga_canonical_id IS NULL) = (unlinked_reason IS NOT NULL)`, vocabulary filter, digest vector extended with `unlinked_reason` |
| python `tests/test_l0_rules_yoga.py` + `tests/test_l0_remedy_corpus.py` (re-run 2026-09-26) | — | **49 passed** (TestWL03CitationParenSuppression / TestWL03SentenceWindowTruncation / TestWL03UnlinkedReason included) |
| TS `platform/tests/unit/migrations/l0_rules_link_accountability.test.ts` (re-run 2026-09-26) | — | 5 tests: 1 static **passed**; 4 real-PostgreSQL skipped without `TEST_DATABASE_URL` — the live block ran **green against the throwaway fixture instance** in W-L0-5's gate set 2026-09-25 (54 passed across the 7-file campaign vitest set) |
| production `brahma_remedy_corpus` drift counts | BPHS ×193 / Phaladeepika ×11 / Tajaka ×3 / bphs_jaimini ×1 / classical_tradition ×80 (1 MC-cited) | unchanged 2026-09-26 (migration HELD); writer emission is single-identity once 1123 applies and the corpus is re-seeded |

## Caveats (recorded, not repaired here)

1. **Writer-nuance flagged at build time:** `canonical_source_id`'s alias map fires
   before the Muhurta-Chintamani citation rule, so the one writer row emitted with
   source `BPHS` and the MC citation stays `bphs` — contradictory provenance in the
   writer data. Recorded for W-L0-5's provenance lane; not silently fixed.
2. **Production stays at 17 links until 1123 applies.** The writer change is
   emission-side; the 36 existing rows move only via the migration's replay-verified
   backfill. Nothing here routes around the hold.

## Migration 1123 — committed, HELD

`platform/migrations/1123_l0_rules_link_accountability.sql` (committed with `1c4035132`
per strategy instruction). Guard discipline (618/1075/1120/1121/1122 pattern): refuses an
unknown starting state — state A/B digest detection (state B = verifying no-op re-run),
all 36 backfill rule_ids must be present, remedy drift counts pinned, the three ontology
text rows must exist, the bg_rules registry contract must be known. Number chosen by
scanning every `origin/*` head across both migration trees (heads: platform/migrations
1122, supabase/migrations 1090 at authoring). **Gate: governed-runner apply only, after
strategy-session confirmation; must apply before 1124** (1124 refuses otherwise — its
`unlinked_reason`-present pre-flight enforces the ordering).

## Packet status

**Code: COMPLETE** (`118aa9a65` + W-L0-3 hunks in `1c4035132`). **Migration 1123: HELD**
(unapplied; gate above). **Report: emitted** — coverage 7 of 3,002 measured with the
ceiling stated; remedy drift normalized at the writer with aliases registered in 1123.

Open rulings, restated as OPEN — none inferred here: W-L0-9 identity [OPEN], W-L0-6
Sarvatobhadra school [OPEN], `Dom` vs Decision 11 [OPEN — strategy]. Merge gate on the
sangam-stage3 carriage stands; 1124 stays gated on the `bg_transit_rules` 76-vs-75
reconciliation.
