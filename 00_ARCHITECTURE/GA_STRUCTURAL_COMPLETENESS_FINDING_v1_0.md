---
artifact: GA_STRUCTURAL_COMPLETENESS_FINDING_v1_0.md
canonical_id: GA_STRUCTURAL_COMPLETENESS_FINDING
version: 1.0
status: CURRENT — native review pending
authored_by: Cowork (forensic analysis, 2 sub-agents + direct code read) 2026-06-12
authored_for: the native — a data-integrity finding + remediation design for ga_structural
severity: HIGH — silent data loss upstream of MSR; reopens a sealed L1 layer
purpose: >
  Answer the native's question: can a real, computable astrological configuration silently
  vanish before the LLM can ever retrieve it? Forensic verdict + the exhaustive-vs-catalog-gated
  map + the fix design that guarantees no deterministic fact falls through L0→L1→MSR.
evidence_base:
  - platform/python-sidecar/ga_writers/ga_structural_writer.py (read in full)
  - platform/supabase/migrations/176_l0_phase_alpha_new_content_tables.sql (brahma_yoga_catalog DDL)
  - platform/supabase/migrations/187_bg_yogas_floor.sql (175 yogas), 189 (50 doshas), 191 (rules 8.1%)
  - platform/scripts/seed/asset_registry_seed.ts (bg_ + ga_ asset definitions)
relates_to:
  - MSR_UCN_CONTAMINATION_AUDIT (the C2 "silent drop" this re-discovers one layer lower)
  - A10_MSR_SPEC (MSR can only project what ga_structural emits)
---

# ga_structural Completeness — Forensic Finding + Fix Design v1.0

## §0 — The native's question, answered in one paragraph

**Yes — real computable configurations of the chart can silently vanish, and it happens at L0
and L1, *below* MSR, where MSR cannot recover them.** BUT the loss is confined to the
**named-pattern layer** (yogas/doshas): the **raw relational structure** of the chart (every
aspect, every dispositor chain, all 144 argala cells, every conjunction, every avastha/dignity)
**is emitted exhaustively and is NOT dropped.** So the LLM *can* see the raw configurations; what
it cannot see is any *named* yoga/dosha that isn't in a small hardcoded list — and that list
ignores the L0 catalog built for exactly this purpose. This is the same "silent drop"
(Contamination C2) the native eliminated at the MSR-threshold level, re-entered one layer lower at
the recognition level. Fixing MSR cannot fix it; ga_structural must be fixed.

## §1 — The three drop points (verified)

### Drop 1 — L0 classical libraries are a curated subset, gaps unrecorded
- `bg_yogas` / `brahma_yoga_catalog` = **175 yogas** (target was 250; 70%). `bg_doshas` = 50.
  `bg_rules` extracted from only **8.1% of text chunks** (660/8193).
- **Gaps are logged to the console, never stored as data.** No column/flag/view answers "which
  configurations have NO classical coverage." Absence is invisible — only presence is stored.

### Drop 2 — ga_structural is CATALOG-GATED and ignores L0 (the worst one)
- `ga_structural_writer.py` **hardcodes 24 yogas (`YOGA_LIBRARY`) + 15 doshas (`DOSHA_LIBRARY`)**
  as Python constants. Comment admits: *"G12 subset — 200+ checked … representative subset."*
- **It reads `brahma_yoga_catalog` ZERO times** (grep: 0 hits). So the 175-yoga L0 catalog —
  built, source-cited, with a machine-readable `formation_rule_jsonb` GIN-indexed column designed
  to be evaluated — **is not used by the engine that fires yogas.** A redundant, smaller, drifting
  hardcode sits next to the canonical catalog. (Integrity + redundancy break.)
- **Firing loop is `for yoga_def in YOGA_LIBRARY`.** If a yoga is present in the chart but not one
  of the 24, it is **never checked, never fired, never emitted, and nothing is flagged.** Silent
  drop. Same for doshas (15). A real Raja-yoga variant outside the 24 simply does not exist to the
  system.
- A further internal gap: `_evaluate_yoga_fires` returns `False, "condition not implemented in
  simplified evaluator"` for yogas whose conditions the simplified evaluator can't express — so
  even some of the 24 may silently not fire.

### Drop 3 — orb thresholds discard relational facts unrecorded
- Conjunctions > 10° orb, Tajik aspects > 30° orb: `continue` (no row). Silent. (Lower severity —
  these are genuinely weak, but per "no threshold drop / strength is a column not a gate," they
  should be emitted with a low strength, not dropped.)

### Bonus finding — `constituent_facts_array` uses `_mock_fact_id_ref` (NEEDS VERIFICATION)
The back-references MSR depends on (the L1-is-authority spine) are built by `_mock_fact_id_ref`,
a deterministic SHA-256 of `category|subject|rupa|chart_prefix|ayanamsha|ga3_build`. It is NOT
random — it *could* resolve IF `chart_facts.fact_id` uses the identical hash formula. **Verify:
do the real chart_facts fact_ids match this scheme?** If not, MSR's `constituent_facts_array`
won't resolve back to L1 — a direct break of the anti-drift guarantee (SIG.MSR.377 trap). Flagged,
not yet confirmed.

## §2 — The exhaustive-vs-catalog-gated map (the load-bearing distinction)

ga_structural emits ~35 fact categories. They split cleanly:

**EXHAUSTIVE — computed for ALL planets/pairs, NO catalog gate → NOTHING DROPPED (~30 categories):**
`aspect_parashari_given`/`_received`, `aspect_jaimini` (all 12×12), `aspect_tajik`,
`conjunction_within_orb` (all 36 pairs, modulo orb), `aspect_matrix_summary`, all `bhava_bala_*`,
`ashtakavarga_anubindu`, all 5 `graha_avastha_*`, `graha_in_house_composite_strength`,
`graha_functional_class_per_ascendant`, `graha_yoga_karaka_flag`, `karakatva_strength_*`,
`graha_dispositor_chain`, `composite_dispositor_strength`, `parivartana_pairs`,
`graha_composite_state_classification`, `graha_special_state_rollup`,
`graha_effective_dignity_*`, `argala_natal_matrix` (all 144), `virodha_argala_natal_matrix`
(all 144), `pranic_strength_*`, `jaimini_tri_deva_role_*`. **The chart's raw structure is complete.**

**CATALOG-GATED — emitted only on a hardcoded named match → SILENT DROP (2 categories):**
`yoga_fires` (24 defs), `dosha_fires` (15 defs). **This is the entire loss surface for named patterns.**

**Implication for LLM visibility:** the LLM, via retrieval, CAN see every raw configuration of the
chart (aspects, chains, argala, dignities). It CANNOT see named yogas/doshas outside the 24/15.
So the chart's *structure* is fully retrievable; its *classical nomenclature* is not.

## §3 — Why this defeats the project's own intent

- Violates **completeness** (the native's #1 priority): named-pattern recognition is incomplete
  and the incompleteness is invisible.
- Violates **single-source / no-redundancy**: two yoga definition lists (L0 catalog 175 vs L1
  hardcode 24) that can drift, with the canonical one unused.
- Re-introduces **Contamination C2** (silent candidate-pool drop) at the recognition layer.
- MSR inherits the loss: A10's "evaluate every classical predicate" cannot rescue what
  ga_structural never emitted; and if MSR re-fires from G52 predicates instead, it becomes a
  THIRD definition list — more drift, not less.

## §4 — The fix design (guarantee: no deterministic fact falls through)

**Principle: separate "compute the raw structure" (exhaustive, keep as-is) from "recognize named
patterns" (must become catalog-driven + must never silently drop).**

### Fix 4.1 — ga_structural reads the L0 catalog, not a hardcode
Replace the hardcoded `YOGA_LIBRARY` (24) / `DOSHA_LIBRARY` (15) with a read of
`brahma_yoga_catalog.formation_rule_jsonb` + `brahma_dosha_catalog`. The catalog already has a
machine-readable, GIN-indexed `formation_rule_jsonb` designed for exactly this. One source of
truth; L1 inherits L0's 175/50, and grows automatically as L0 grows. (Mirrors the G52
"predicate evaluation is data-driven, not hardcoded" intent — but sourced from L0, not a 3rd list.)

### Fix 4.2 — emit an `uncatalogued_configuration` fact so nothing is invisible
The raw exhaustive facts already capture the *structure*. Add a deterministic pass that, when a
structural pattern is present but matches NO catalog entry, emits a typed
`uncatalogued_configuration` fact (e.g. "Jupiter+Moon mutual kendra, no named-yoga match")
referencing its constituent fact_ids. **Now absence becomes presence** — the LLM can retrieve
"here is a real configuration with no classical name," instead of it vanishing. This is the
structural realization of "never drop data."

### Fix 4.3 — no orb-threshold drop (strength as column)
Conjunctions/aspects beyond orb cutoffs are emitted with a low `orb_tightness`/strength value, not
`continue`d. Serve-time ranks; the asset never gates. (Consistent with the locked no-threshold rule.)

### Fix 4.4 — coverage-flag column (make gaps queryable)
Add a `classical_coverage` flag on yoga/dosha facts: `cited` (catalog entry has classical_citations)
vs `computed_only` (fired structurally but no classical text backs it). And a build-time coverage
report: "N configurations present, M named, K uncatalogued." Gaps stop being console-only.

### Fix 4.5 — verify + fix `_mock_fact_id_ref`
Confirm whether the deterministic hash matches real `chart_facts.fact_id` generation. If not,
replace mock refs with real resolved fact_ids so MSR's anti-drift back-reference actually resolves.

### How MSR then behaves (resolves the earlier architecture question)
With 4.1–4.4 done, MSR/`bo_laksana` becomes the clean **deterministic transform** the native
described: project EVERY ga_structural fact (raw + named + uncatalogued) into one signal,
inherit the L1 value via the (now-real) fact_id, attach salience. **No re-firing, no G52 predicate
gate** — G52 demoted to optional metadata (citation/domain/remedy annotation keyed off what L1
already fired). Signal count = ga_structural fact count. Completeness preserved end-to-end.

## §5 — Scope + caution

This **reopens L1 (Gaṇita), a SEALED layer** (`L1_GANITA_CLOSURE`). Per CLAUDE.md §L, architecture
changes need native approval + version bump. ga_structural is on the FROZEN orchestrator contract —
the fix is to the *writer's internal logic*, NOT the orchestrator (no contract change). Recommended:
treat this as an L1 amendment workstream (its own brief + migration to re-run ga_structural),
sequenced BEFORE the bo_laksana writer brief — because bo_laksana must project a complete,
non-dropping, real-fact_id ga_structural.

## §6 — Decisions for the native
1. Approve reopening L1 to fix ga_structural (4.1–4.5)? (HIGH severity; the alternative is Bodha
   inherits the silent drop.)
2. Confirm the fix priority: ga_structural completeness fix is a PRE-requisite of bo_laksana
   (it moves ahead of the writer briefs in the runway).
3. Confirm MSR = pure transform of (fixed) ga_structural, G52 = metadata-only (not a firing engine).

---
*End of GA_STRUCTURAL_COMPLETENESS_FINDING_v1_0. Verdict: raw structure is exhaustive + safe; named
yoga/dosha recognition is catalog-gated, hardcoded, ignores the L0 catalog, and silently drops the
uncatalogued — a HIGH-severity completeness defect upstream of MSR. Fix = catalog-driven recognition
from L0 + emit uncatalogued configurations + no orb drop + real fact_ids, making MSR a clean
non-dropping transform.*
