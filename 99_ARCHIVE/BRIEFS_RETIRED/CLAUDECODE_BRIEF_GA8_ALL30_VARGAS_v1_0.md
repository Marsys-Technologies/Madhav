---
artifact: CLAUDECODE_BRIEF_GA8_ALL30_VARGAS_v1_0.md
canonical_id: GA8_ALL30_VARGAS_BRIEF
version: 1.0
status: CURRENT
authored_by: Cowork (planning) 2026-06-12
authored_for: Claude Code in Antigravity IDE (NOT the CLI)
follows: CLAUDECODE_BRIEF_GA8_STRUCTURAL_ENUMERATION_v2_0.md (shipped; enumerated 16 shodasha vargas)
native_decision: extend GA8 relationship enumeration from 16 shodasha vargas → ALL 30 vargas GA6 computes, every relationship type (completeness-first; serve-time decides relevance, never pre-drop)
target_writer: platform/python-sidecar/ga_writers/ga_structural_writer.py
data_plane: ALWAYS prod via Cloud SQL proxy
---

# GA8 — Extend Enumeration to ALL 30 Vargas — Execution Brief v1.0

## §0 — Why this brief

GA8 v2.0 shipped enumerating relationships on the **16 shodasha vargas** (`SHODASHA_VARGAS`
constant). That 16-set was an *implicit* choice in the brief, not a native decision. **Native
decided 2026-06-12: enumerate ALL 30 vargas GA6 computes, for every relationship type** — the
completeness-first principle (capture everything deterministic; the LLM/serve-time layer decides
relevance; never pre-drop at creation). The "aspects in ultra-high vargas like D150/D2700 may be
noise" concern is handled at SERVE-TIME (downweight/filter), NOT by omitting the data.

## §1 — The change (small + clean — the infra already exists)

GA6 already computes positions for all 30 vargas and exposes them:
- **Parashari 16:** D1,D2,D3,D4,D7,D9,D10,D12,D16,D20,D24,D27,D30,D40,D45,D60
- **Supplementary 11:** D5,D6,D8,D11,D14,D15,D21,D32,D33,D50,D54
- **Nadi 3:** D108,D150,D2700
- (GA6 constant: `ALL_30_VARGAS`. D81 remains skipped per the GA6 locked decision J.)

GA8's `_load_varga_positions` is already varga-parameterized and works for any varga label (proven
by the v2.0 fix). So the change is:

1. **Replace the enumeration set:** in `ga_structural_writer.py`, change `SHODASHA_VARGAS` (16) to
   the full 30-varga list (mirror GA6's `ALL_30_VARGAS`; keep D81 excluded). `_build_varga_aspect_rows`
   already loops `for varga in <set>` — point it at the 30.
2. **Confirm `_load_varga_positions` returns rows for the 14 added vargas** (D5/D6/D8/D11/D14/D15/
   D21/D32/D33/D50/D54/D108/D150/D2700) — GA6 writes their `varga_position` rows; the loader query
   should already match (it's the same shape that now works for the 16). If any added varga returns
   empty, the loud `VARGA_MISSING` WARNING fires (no silent drop) — investigate that varga's GA6
   storage rather than skipping silently.
3. **EVERY D1 construct extends to all 30 — no exceptions (native decision 2026-06-12, maximal
   completeness):** dignity, aspects (Parāśarī/Jaimini/Tājik), conjunctions, dispositor chains,
   parivartana, vargottama, the yoga/dosha LABEL pass, **AND `argala_natal_matrix` /
   `virodha_argala_natal_matrix` (the 144-cell matrices)**. The rule is uniform: *whatever GA8
   computes for D1, compute identically for all 30 vargas*, each row tagged with its varga. Do NOT
   special-case argala or any "rashi-anchored" construct as D1-only — that would be a silent
   scope-cap. The mainstream "argala is D1-only" view is a SERVE-TIME relevance weighting, never a
   creation-time omission. (Label pass still sources names from `brahma_yoga_catalog`; unmatched
   configs still stored.) No new relationship logic — one enumeration, applied 30×.
4. **Disambiguation unchanged + enforced:** every row still carries varga + sign + ayanamsha +
   position. The 14 new vargas' rows are tagged with their varga (D5_/D150_/… prefixes in
   fact_subject), so "Venus dignity in D6 Cancer lahiri" is distinct + queryable.

## §2 — Note on the high Nadi vargas (D108/D150/D2700)
These divide a sign very finely. Enumerating aspects/conjunctions in them is INCLUDED per the
completeness decision. Two honest implementation notes for the executor:
- Conjunction in a varga = "same varga-sign" (already the v2.0 convention for D2–D60) — applies
  uniformly to D108/D150/D2700.
- These are stored as deterministic facts; any relevance-weighting is a serve-time concern, NOT a
  creation-time filter. Do NOT add a "skip high vargas" shortcut — that would reintroduce a silent
  scope-cap.

## §3 — Volume expectation (honest)
Per-varga relationship layer ≈ ~45–60 rows × 5 ayanamshas, PLUS argala+virodha now per-varga
(144×2 = 288 rows × 5 ayanamshas per varga). Across 30 vargas that's the dominant term:
argala alone ≈ 288 × 30 × 5 ≈ **~43,000 rows**, plus ~30 × ~55 × 5 ≈ ~8,000 relationship rows, on
top of the D1 base. Estimated GA8 total: **roughly ~55,000–65,000 rows**. This is the maximal-
completeness number the native chose; floors aspirational, `target_floor` = achieved count after
rebuild. (Do NOT trim to hit a number; do NOT skip the high vargas.)

## §4 — Conformance + verification
- Orchestrator FROZEN contract unchanged; heavy writer (now substantially heavier — confirm
  `plan_substeps` chunks sensibly, e.g. per-ayanamsha or per-varga, to stay within step limits);
  per-chart delete-then-insert idempotency; `ctx.db_conn`; no `asset_throughput`; FORENSIC guarded
  to native. No orchestrator edit.
- **Acceptance [verify-against: prod]:**
  - [ ] By-varga count (the v2.0 V-C query) shows ALL 30 vargas populated (not 16). `[psql_prod]`
  - [ ] The 14 added vargas each have aspect + dignity + **argala** rows for the native. `[psql_prod]`
  - [ ] `argala_natal_matrix` + `virodha_argala_natal_matrix` now present for ALL 30 vargas (144×2 each), each row tagged with its varga. `[psql_prod: count argala rows grouped by varga = 30 distinct]`
  - [ ] No silent skips — any empty varga logs `VARGA_MISSING` WARNING. `[build log]`
  - [ ] Every row fully qualified (varga + sign + ayanamsha + position). `[psql_prod: no NULL varga/sign]`
  - [ ] FORENSIC 7/7 still passes; two-pass still true.
  - [ ] `target_floor` updated to new achieved count; `count_sql` includes `%_per_varga` + argala categories.

## §5 — Out of scope
Dasha-temporal (L3 Kāla); MSR projection (separate brief). This brief widens the varga set from
16 → 30 AND replicates ALL D1 constructs (incl. argala) across all 30 — every relationship type,
no D1-only exceptions.

---
*End of GA8_ALL30_VARGAS_BRIEF v1.0 (maximal-completeness). The rule is uniform: whatever GA8
computes for D1 — dignity, aspects, conjunctions, dispositors, parivartana, vargottama, yoga/dosha
labels, AND argala/virodha-argala — compute identically for all 30 vargas, each row varga-tagged.
No D1-only special-cases, no silent scope-caps; serve-time handles relevance (incl. the mainstream
"argala is D1-only" view). Est. ~55–65k rows; floors aspirational.*
