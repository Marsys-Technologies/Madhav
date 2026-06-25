---
artifact: L2_BODHA_REMEDIATION_PHASE_PLAN_v1_0.md
canonical_id: L2_BODHA_REMEDIATION_PHASE_PLAN
version: 1.0
status: ACTIVE
authored_by: Claude (Cowork) 2026-06-25
purpose: >
  Extensive, DAG-ordered phase plan to address EVERY identified L2 Bodha correction effectively.
  Division of labor: Claude Code (Antigravity) UPDATES ALL CODE + writes tests; the operator
  GENERATES THE DATA via the localhost Nirmāṇa build tracker; then a RE-AUDIT against the live data
  confirms every correction landed. Deep-audit the 7 pending assets FIRST so the full list is fixed
  once (not the partial list twice). Fixes applied upstream→downstream; ONE L2 regeneration at the end.
audience: Claude Code executor + operator
constraints: >
  Prod data plane via Cloud SQL proxy :5433. Native = Abhisek 482012f1 (never destructive-test).
  Non-native test = Abhinandan 1c826d5a (safe). L0/L1 are the AUTHORITY — L2 references their
  fact_ids, never restates computed values (Trap-1). FROZEN orchestrator contract. main only.
---

# L2 Bodha Remediation — Phase Plan

## §0 — The consolidated correction list this plan addresses
Source of truth: `FOUNDATION_ROOT_CAUSE_MAP.md` §4 + §12 + §8/§13, governed by
`FOUNDATION_INTEGRITY_CAMPAIGN_v2_0.md`.

**A. Confirmed-WRONG (known):**
- **L2-W3 — CDLM non-canonical vocabulary** (`bo_sangati.py` ~L42): `spirituality→spiritual`,
  `character→psychological`, `wealth→financial`. Strands CDLM rows from phala_anchors; CAUSES the
  ph_sankrama 96.5% career skew. Blast radius: `bo_drishti.py` (L39–49), `ka_bhavishya_lekha.py`.
  Fix already authored: `CLAUDE_CODE_PROMPT_L2_CDLM_VOCAB_FIX.md`. NOT applied.
- **L2-W1 — `bodha_cgm_nodes` degenerate** (`bo_cgm`): every node strength=0.506, `bodha_cgm_edges`
  NULL. Graph dead (no edges, no differentiation). Full CGM rebuild required after fix.
- **L2-W2 — `bodha_rm_resonances` degenerate** (`bo_upaya`): resonance_score=0.28 for all rows.
- **§12 convergence root — `bodha_msr_signals` WRONG ×4** (`bo_laksana`): F4 graha-extraction source
  mismatch → 83% (55,514 structural rows) get identical midpoint salience (`_compute_salience()`
  L541–556); F1 computed_salience near-degenerate (9 values, 85.7% at one); F3 signature_class NULL
  for 100% of 66,738 rows (hardcoded None L787) → downstream `WHERE signature_class=…` returns 0;
  F2 fact_value_num=1 for ~83% (semantic overload). NOTE: there is NO eligibility_score column —
  earlier framing was wrong. Fix = extract graha from `fact_key` (split on `:`). FK resolution=100%.

**B. PENDING DEEP AUDIT (the 7 — never thoroughly examined; msr_signals proved "superficial" assets
hide root causes):** `bo_laksana`, `bo_sangati` (partially known), `bo_anveshana`, `bo_drishti`,
`bo_pramana_mapa`, `bo_upaya`, plus deferred bucket (contradictions, gestalt, bo_bimba, bo_upaya stub).
Intended artifact `L2_SOUNDNESS_REPORT.md` does NOT exist yet; staging prompt
`CONDUCTOR/audit/CLAUDE_CODE_PROMPT_L2_AUDIT.md` (ASSESS-ONLY).

**Degenerate-distribution theme:** L2-W1 (0.506), L2-W2 (0.28), msr F1/F2 are all the same class as
the all-Jupiter / constant-collapse bug — a column collapsing to one value where diversity is
expected. The build/seal MUST gain a distribution guard (memory: degenerate-distribution-guard).

---

## §PHASE 0 — Complete the deep audit FIRST (ASSESS-ONLY, no code changes)
Goal: turn the 7 PENDING assets into a known list so we fix the COMPLETE set once.
- Run the staged `CONDUCTOR/audit/CLAUDE_CODE_PROMPT_L2_AUDIT.md` against the live L2 data
  (1c826d5a where built; read-only). For EACH of the 7 + the deferred bucket, examine the ACTUAL
  ROWS (distribution per key column — detect any constant-collapse), the writer code, and the
  L1-authority compliance (does it reference fact_ids or restate computed values? Trap-1).
- Produce **`L2_SOUNDNESS_REPORT_v1_0.md`** — per-asset verdict (SOUND / WRONG / STUB), the specific
  finding, the fix scope, and the rebuild blast radius. Fold in the 4 already-known (A above) so the
  report is the single consolidated L2 correction list.
- **GATE 0:** native reviews `L2_SOUNDNESS_REPORT`. The fix phases below execute against THIS report's
  final list, not the partial list. If the audit finds new WRONGs, they join the fix waves in DAG order.
- Output: assess-only. No code edits in Phase 0.

## §PHASE 1 — Cross-cutting guards + canonical vocabulary (the shared substrate)
Fix the things multiple assets depend on, before per-asset fixes.
1. **Canonical domain vocabulary (fixes L2-W3 root):** establish ONE canonical domain set (spiritual,
   psychological, financial, … — match phala_anchors / CDLM canonical). Apply to `bo_sangati.py`,
   and the blast-radius sites `bo_drishti.py` (L39–49) and `ka_bhavishya_lekha.py`. Prefer a SHARED
   constant/map both read, so vocab can't drift per-writer again. (Use the authored
   `CLAUDE_CODE_PROMPT_L2_CDLM_VOCAB_FIX.md` as the basis; extend to all sites.)
2. **Degenerate-distribution guard (build/seal gate):** add a gate that HALTS the build if a column
   expected to be diverse collapses to one value (e.g. cgm strength all-0.506, resonance all-0.28,
   salience 85.7%-at-one, signature_class 100%-NULL). General L2 hygiene; reusable downstream.
3. **Trap-1 conformance check:** a test that every L2 signal's `constituent_facts_array` resolves to
   real `chart_facts.fact_id` and does NOT restate an L1 computed value as its own truth.
- GATE 1: vocab unified + guard exists (fails on a deliberately-degenerate fixture) + Trap-1 test green.

## §PHASE 2 — Fix the CONVERGENCE ROOT: bodha_msr_signals (bo_laksana)
This is upstream-most and feeds all L3/L4 — fix before everything downstream.
- **F4:** rewrite `_compute_salience()` (bo_laksana.py L541–556) to extract graha from `fact_key`
  (split on `:`), not from absent jsonb tags. Verify the 55,514 structural rows now get real,
  varied salience (not midpoint-constant).
- **F1:** confirm computed_salience distribution is no longer near-degenerate (target: many distinct
  values, no single value dominating ~86%).
- **F3:** populate `signature_class` (remove hardcoded None at L787) with the real class per signal —
  so downstream `WHERE signature_class=…` (ka_yojaka etc.) returns rows.
- **F2:** stop overloading `fact_value_num=1`; carry the real numeric where one exists, NULL+reason
  where not (canonical-or-floor rule), so downstream doesn't misread 83% of rows.
- Keep FK resolution at 100% (don't regress the one thing that's right).
- GATE 2: unit tests prove each F1–F4 fixed on a seeded fixture; distribution guard passes.

## §PHASE 3 — Fix the graph + remedy + remaining-audit assets (DAG order under msr)
- **L2-W1 `bo_cgm`:** fix the formula collapse (strength all-0.506) AND populate `bodha_cgm_edges`
  (the graph needs edges — centrality/paths/final-dispositor were the whole point). Distribution
  guard must pass on node strength + edge existence.
- **L2-W2 `bo_upaya` resonance:** fix `resonance_score` collapse (all-0.28) to real per-remedy
  potency. (Also addresses the bo_upaya "stub" deferred item if it's the same root.)
- **Any new WRONGs from Phase 0** (`bo_anveshana`, `bo_drishti`, `bo_pramana_mapa`, `bo_bimba`,
  contradictions, gestalt): fix per the L2_SOUNDNESS_REPORT verdicts, in DAG order.
- GATE 3: every fixed asset has a passing unit test + distribution guard; no degenerate columns remain
  in code-level fixtures.

## §PHASE 4 — Commit + deploy code (NO data yet)
- All code fixes land on main (DAG-ordered commits). Run typecheck + full test suite green.
- Confirm the deployed web image AND the Cloud Run job image carry the fix (job_image_tag) — the L2
  build runs in the cloud job, so a stale job image would regenerate with OLD code.
- GATE 4: image SHAs == fix commit. THIS IS THE HANDOFF LINE — code done, data not yet regenerated.

## §PHASE 5 — OPERATOR regenerates L2 data (localhost Nirmāṇa tracker)
**Operator action — Claude Code does NOT trigger data builds.**
- On localhost:3000, press Build/Rebuild for **Layer 2 (Bodha)** for the chosen chart, in DAG order:
  `bo_laksana → bodha_msr_signals → bo_sangati → bo_cgm → bodha_rm_resonances → … → all L2` (the
  §8 Wave-2 sequence; the layer-build button assembles this from the registry).
- Use the now-reliable tracker (delete/clear fixed, layer-build fixed). Recommended: regenerate on
  **non-native 1c826d5a first** (safe), confirm, then native 482012f1.
- Watch: every L2 asset lights green, real (DIVERSE) row counts, zero errored assets (error badge=0).

## §PHASE 6 — RE-AUDIT against the freshly-generated data (the proof)
The plan's closing gate — re-run the deep audit against the NEW L2 data:
- Every Phase-0/§0 finding RESOLVED in the live rows: cgm strength diverse + edges present;
  resonance diverse; msr salience diverse + signature_class populated + fact_value_num not overloaded;
  CDLM vocab canonical (CDLM rows now JOIN phala_anchors — and check the ph_sankrama career-skew is
  gone downstream); all 7-pending verdicts now SOUND.
- Distribution guard passes on live data (not just fixtures).
- Trap-1: constituent_facts resolve; no restated L1 values.
- Produce **`L2_SOUNDNESS_REPORT_v2_0.md`** (post-fix) — every item OPEN→RESOLVED, or a residual list
  for a targeted Phase 3b. If clean → L2 re-seal (`L2_BODHA_CLOSE` update) + CURRENT_STATE.
- GATE 6: native reviews. L2 closes only when the re-audit is clean on live data.

---

## §SEQUENCING SUMMARY
Phase 0 (deep audit, assess-only) → GATE 0 native review →
Phase 1 (vocab + guards) → Phase 2 (msr root) → Phase 3 (graph/remedy/remainder) [all code, DAG order] →
Phase 4 (commit/deploy, image-SHA gate) → **OPERATOR** Phase 5 (regenerate via tracker) →
Phase 6 (re-audit on live data → L2_SOUNDNESS_REPORT_v2 → re-seal).

## §HARD CONSTRAINTS
- Claude Code: CODE + TESTS + AUDIT REPORTS only. NEVER triggers a data build (operator does, Phase 5).
- Deep audit (Phase 0) BEFORE any fix — fix the complete list once.
- Upstream-first within the DAG; ONE full L2 regeneration at the end (Phase 5), not per-asset.
- L1/L0 are authority — L2 references fact_ids (Trap-1); a fix that restates an L1 computed value is wrong.
- Degenerate-distribution guard is mandatory — these bugs are all constant-collapse; the guard is the
  durable defense so they can't silently recur.
- Destructive regeneration: non-native 1c826d5a first; native 482012f1 only after it's proven.
- FROZEN orchestrator contract — fix writers/routes that conform; a needed contract change is STOP-and-raise.
- Re-audit on LIVE data is the close gate — code-green is necessary, not sufficient.
```
