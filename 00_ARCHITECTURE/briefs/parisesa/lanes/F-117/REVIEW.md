---
lane: F-117
stream: S3
stage: R (REVIEW) — draft, pending ratification
reviewer: VERIFIER
verdict: COMPLETE
drafted_by: pool-1
draft_verdict: COMPLETE
ratified_by: ratifier-1
---

## Method

Read: PROTOCOL.md, SPEC.md, DIAGNOSIS.md, lane directory listing (no REVIEW_LEADS.md present).
Source verified line-by-line against `/Users/Dev/par-night/main-ro`:
- `bo_upaya.py` lines 44-51, 808-845, 1000-1034, 1062-1183, 1185-1257
- `bo_cgm_motifs.py` lines 235-298, 415-506, 760-789
- `bodha_writers/formulas.py` lines 250-294
- `platform/src/lib/retrieval/registry/layers/L2_bodha/query_remedies.ts` lines 445-494
- `brahmagyan/graha_vocabulary.py` (grep for to_title/norm_graha)
- `pipeline/orchestrator/writers/bo_bimba.py` (grep for to_title/_SUBJECT_TO_GRAHA precedent)
- `bo_upaya.py` lines 560-610 (_fetch_graha_cdlm_cells)

No test runs possible at review stage (no build worktree); all exit-test claims traced line-by-line.

## Q1 — Mechanism vs symptom

COMPLETE. The spec addresses mechanisms at every level:
- C1: identifies exact format mismatch (`'MAR' != 'MARS'` at lines 838-840) and provides the canonical fix via `to_title()` from `brahmagyan.graha_vocabulary`, citing the identical `bo_bimba.py` fix (lines 26, 49-56) as both precedent and structural model.
- C2: identifies the hardcoded `0.0` literal (line 1175) and proposes wiring already-fetched `graha_cdlm_cells` (fetched line 1103, used at lines 1213/1241 but not yet at 1175). Build-stage divisor decision explicitly deferred with a stop-and-raise option — honest, not evasive.
- C3: identifies flat per-class strength literals (0.8 at bo_cgm_motifs.py:291, 0.6 at :461, 0.75 at :499) and establishes that `computed_strength` is already fetched in `all_edges` (lines 772-773) and sits in every edge dict passed to the three detector functions — unused.
- C5: correctly reframes from "inflates ranking" to "undisclosed-fallback narration gap" after tracing the clamping math (min(sha_norm, 1.0) treats Rahu/Ketu identically to Sun/Saturn whose real ratios also clamp to 1.0).
- C6: correctly characterises `_priority_class` as confirmed-as-designed (lines 1005-1034, docstring explicit), and proposes surfacing its own internal framing text to the served response.

## Q2 — Sub-claim coverage

COMPLETE. SPEC §8 coverage table maps all 6 diagnosis sub-claims (C1-C6) to spec elements. C4 (rank order collapses to inverse-shadbala) is correctly identified as a downstream consequence of C1-C3 with no independent fix element needed — it resolves automatically once §2a-§2c land and are rebuilt. No unmapped diagnosis claim found.

## Q3 — Exit tests fail today (traced line-by-line)

**test_active_doshas_by_graha_finds_mars_manglik**: FAILS TODAY — confirmed.
`KNOWN_GRAHAS` (lines 48-51): Title-case `["Sun", "Moon", "Mars", ...]`.
Current loop (lines 837-844): `subj = ... .upper()` → "MAR"; `graha.upper()` for "Mars" → "MARS"; `"MAR" == "MARS"` is False. Mars is structurally unmatchable. Test asserts `"Mars" in result` → FAIL.

**test_resonance_inputs_are_not_degenerate**: FAILS TODAY — confirmed.
`domain_burden`: `cdlm_weakest_constituent_count=0.0` (line 1175) is a hardcoded literal for every graha → `set(values) == {0.0}` → len=1 → assertion fails.
`motif_burden`: `_detect_mutual_aspects` assigns `"strength": 0.6` (line 461) to every mutual aspect pair regardless of which grahas. DIAGNOSIS.md §1 confirms every graha in this chart participates in mutual_aspect and no other reachable motif class → `min(motif_strength) = 0.6` → `motif_burden = 0.4` identically for all 8 grahas → `set(values) == {0.4}` → len=1 → assertion fails.

**test_citation_human_discloses_shadbala_fallback**: FAILS TODAY — confirmed.
`citation_human` (line 1255): `f"Resonance: {graha} | sha={sha_norm:.2f} dosha_count=..."` — the string `"no classical shadbala"` does not appear anywhere. `missing_inputs` already records `"shadbala"` for Rahu/Ketu (line 1139) but is serialized only into `ephemeris_audit_jsonb`, never into `citation_human`. Test asserts `"no classical shadbala" in by_graha[node].lower()` → FAIL.

**TypeScript test (§4b)**: FAILS TODAY — confirmed by reading `query_remedies.ts` lines 450-494. No `remedy_priority_class_note` field is constructed or returned anywhere in the file. `leadSentence` (lines 451-459) references `remedy_priority_class` but carries no rank-relative disclosure string. Both test assertions fail immediately.

## Q4 — Sibling sites

COMPLETE. §5 covers all sites:
- §2a (graha-identifier): one hit confirmed (`bo_upaya.py:840`); `bo_laksana.py:1408` excluded with stated reason (membership test against short-code dict, different shape from direct code-vs-full-name equality).
- §2b: one definition, one call site — no siblings.
- §2c: all three flat-literal sites covered; `_detect_parivartana_chains` (line ~403) already uses a computed `strength` variable — correctly excluded.
- §2d/§2e: single call sites each — no siblings.

## Q5 — Recurrence guard

COMPLETE. §6 specifies genuine guards:
- §2a class: CI grep-guard (deferred to conductor as follow-up, honest scope, same pattern as existing `check_fact_category_pinning.py`). The note that this is a "twice-confirmed defect class" (bo_bimba + bo_upaya) correctly meets the threshold for a permanent lint.
- §2b/§2c: `test_resonance_inputs_are_not_degenerate` is itself a hard CI assertion — any re-hardcoding immediately fails.
- §2d/§2e: exit tests assert disclosure text is present; removal fails CI immediately.
All guards detect the actual defect class, not a proxy.

## Q7 — File:line citations verified

All key citations verified against source:
- `bo_upaya.py:808` (_fetch_active_doshas_by_graha start) ✓
- `bo_upaya.py:837-844` (graha-matching loop) ✓
- `bo_upaya.py:48-51` (KNOWN_GRAHAS, Title-case) ✓
- `bo_upaya.py:1062` (_build_resonances_and_prescriptions start) ✓
- `bo_upaya.py:1103` (graha_cdlm_cells fetch) ✓
- `bo_upaya.py:1175` (cdlm_weakest_constituent_count=0.0) ✓
- `bo_upaya.py:1213` (associated_cdlm_cells_array uses graha_cdlm_cells) ✓
- `bo_upaya.py:1241` (associated_cdlm_cell_count uses graha_cdlm_cells) ✓
- `bo_upaya.py:1255` (citation_human format, no disclosure) ✓
- `bo_upaya.py:1275` (_priority_class call site) ✓
- `bo_upaya.py:1005-1034` (_priority_class, docstring confirms rank-relative design) ✓
- `bo_cgm_motifs.py:239` (_detect_mutual_reception start) ✓
- `bo_cgm_motifs.py:257` (disp_edges captures only edge_id, not computed_strength) ✓
- `bo_cgm_motifs.py:291` ("strength": 0.8) ✓
- `bo_cgm_motifs.py:419` (_detect_mutual_aspects start) ✓
- `bo_cgm_motifs.py:437` (asp captures only edge_id) ✓
- `bo_cgm_motifs.py:461` ("strength": 0.6) ✓
- `bo_cgm_motifs.py:499` ("strength": 0.75) ✓
- `bo_cgm_motifs.py:770-777` (edge fetch includes computed_strength) ✓
- `formulas.py:257-294` (resonance_score_v1, reads from ResonanceInputs fields) ✓
- `formulas.py:271-273` (contradiction_factor/domain_burden/motif_burden reads) ✓
- `bo_bimba.py:26` (to_title import — precedent confirmed) ✓
- `bo_bimba.py:45-56` (minor: _SUBJECT_TO_GRAHA dict body starts line 49, not 45 — comment block above; not a wrong claim, sub-line precision) ✓
- `query_remedies.ts:450-459` (leadSentence construction, no disclosure) ✓
- `query_remedies.ts:463-478` (resonanceRanked mapping, no remedy_priority_class_note) ✓
- `brahmagyan.graha_vocabulary.to_title` importable, confirmed exportable at line 70 ✓

**writer_asset/rebuild_group/RS-A check:** Context declares `writer_asset: bo_upaya`, `rebuild_group: G3`. PROTOCOL.md rebuild groups confirm G3 = `bo_upaya` ← F-116, F-117. SPEC §7 correctly identifies bo_upaya rebuild is required for Phase 1 changes (§N.3 delete-then-insert). Phase 2 (TS only) requires no rebuild — correctly stated. RS-A (code+data path) is consistent with Phase 1's writer-level fix requiring a rebuild to take effect. All accurate.

**One observation for Build (not a deficiency):** §2c notes a sub-nuance: `_detect_mutual_reception` uses `_edge_strength_v1(0.6, ...)` with a flat base-salience input, so post-fix mutual_reception strength may still cluster. The spec honestly flags this as a possible narrower follow-up. Build/VERIFIER should confirm non-degeneracy of mutual_reception strength post-fix before treating that sub-fix as fully resolved. This is appropriately scoped — the mutual_aspect fix (real MSR salience input) is unambiguously differentiating.

## Verdict: COMPLETE
