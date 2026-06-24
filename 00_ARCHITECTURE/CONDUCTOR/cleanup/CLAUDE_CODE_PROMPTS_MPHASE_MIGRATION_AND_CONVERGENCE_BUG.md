---
artifact: CLAUDE_CODE_PROMPTS_MPHASE_MIGRATION_AND_CONVERGENCE_BUG.md
canonical_id: CLAUDE_CODE_PROMPTS_MPHASE_MIGRATION_AND_CONVERGENCE_BUG
version: 1.0
status: READY — two independent Claude Code prompts: (1) M-phase→layer governance migration; (2) L3 kala_convergence all-Jupiter bug. NO SEAL.
authored_by: Cowork 2026-06-22
native_decisions: "(1) FULL migration off M-phases in all LIVE docs+code, preserve history. (2) Investigate + fix the 660/660 Jupiter convergence collapse."
---

# Two Cleanup Prompts — M-Phase Migration + Convergence Bug

> Two INDEPENDENT workstreams. Run as separate sessions/branches (no shared files). Each is diagnostic-
> first where needed. NEITHER seals anything.

---

## PROMPT 1 — M-phase → layer-model governance migration (paste to Claude Code)

You are Claude Code in Antigravity on MARSYS-JIS (repo amonty84/Madhav, main). The native authorized FULLY
migrating the project off the legacy M1–M10 "macrophase" model to the layer model (L0–L5 =
Brahmagyan/Gaṇita/Bodha/Kāla/Phala/Mīmāṃsā) in all LIVE documents and code, while PRESERVING closed
historical artifacts verbatim (rewriting them falsifies the audit trail). A full read-only inventory is
done — work from it; do NOT re-discover. **DO NOT seal; do NOT touch Bucket C.**

**THE HARD CONSTRAINT:** governance TOOLING hard-requires M-phase fields. Editing a document's M-phase
field BEFORE the validators accept layer vocabulary will HARD-FAIL `schema_validator.py` on the next
session open/close and block all work. Follow the sequence EXACTLY.

**Bucket A — LIVE GOVERNANCE (migrate):**
- `platform/scripts/governance/schema_validator.py` (line ~490 requires handshake key `step_number_or_macro_phase`)
- `platform/scripts/governance/schemas/artifact_schemas.yaml` (lines ~299–302 require `active_macro_phase`,
  `active_macro_phase_status`, `active_phase_plan`, `active_phase_plan_version`; line ~201 "post-M3")
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` — **only the LIVE top state-block** (line ~4154
  `active_macro_phase: M6` is STALE — real state is L3 SEALED / L4. The thousands of dated log lines below
  are HISTORY — DO NOT touch them.)
- `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md` + `SESSION_CLOSE_TEMPLATE_v1_0.md` (field
  `step_number_or_macro_phase`; worked example "M2.B.3"; MACRO_PLAN mandatory-read lines)
- `platform/scripts/governance/drift_detector.py` (`check_mp_pbp_alignment()` ~line 302 validates the
  closed PHASE_B_PLAN; class `macro_plan_phase_plan_drift`; "later macro phases" whitelist line ~557)
- `CLAUDE.md` (the §C reading list + §M cadence frame work as "ten-macro-phase arc M1–M10")
- `00_ARCHITECTURE/MACRO_PLAN_v2_0.md` (`id_namespace: M1..M10`; status CURRENT)

**Bucket B — LIVE CODE provenance leaks (low-risk string swaps):**
- `services/ph_rectification/engine.py` + `tests/test_ph_rectification.py`: `LEL v1.7 M5-A-S1 enrichment`
  → use the real discriminator `LEL v1.7` (the M5-A-S1 is just which batch; the version is what matters).
- `platform/scripts/seed/asset_registry_seed.ts` line ~1589: same `M5-A-S1` string in ph_rectification's
  description (this SEEDS prod asset_registry — re-seed + verify after).
- `platform/python-sidecar/brahmagyan/bodha/l2_lenses_salience.py` line ~184: comment "M9-A additions" →
  cite the school/L2 source (Yogini+Tajika lenses), not the closed M9 phase.

**Bucket D — verify first:** `brahmagyan/phala/l4_rectification.py` + `phala/rectification.py` — confirm
whether the orchestrator's `@register('ph_rectification')` writer imports these or the `services/ph_*`
path. If dead/legacy → leave as Bucket C (history). If live → treat like Bucket B.

**FALSE POSITIVES — DO NOT TOUCH:** `ph_muhurta` engine's "M1–M4" (local milestone labels, not
macrophases); `feature_flags.ts` M3/M4/M5 (flag-provenance comments); all `venv/` library hits.

**THE SEQUENCE (do not reorder — tooling-safety):**
1. **Validators back-compat FIRST (no behavior change):** make `schema_validator.py` accept EITHER
   `step_number_or_macro_phase` OR a new `step_number_or_layer`; make `artifact_schemas.yaml` accept the
   `active_macro_phase*` keys OR their layer equivalents. Run the validator against the current
   CURRENT_STATE + a sample handshake to prove both vocabularies pass. COMMIT.
2. **Migrate CURRENT_STATE top state-block** to the correct layer pointer (L3 SEALED / L4 active/next, per
   the changelog tip). Leave all historical log lines verbatim. Validate (passes via step 1).
3. **Migrate the SESSION templates + flip schema_validator's canonical key** to `step_number_or_layer`.
4. **Retire the MP↔PBP drift check** in drift_detector.py (PHASE_B_PLAN is closed M2). Run drift_detector
   to confirm no dangling canonical-id/registration.
5. **Tighten the schema:** remove the old `active_macro_phase*` acceptance + the back-compat alias (reverse
   of step 1). Validate.
6. **CLAUDE.md + MACRO_PLAN prose LAST** (no tooling depends on wording): reframe the §C/§M references to
   the L0–L5 layer arc; cite MACRO_PLAN as strategic-orientation only. Native will decide MACRO_PLAN's
   final status (demote to SUPERSEDED-orientation vs keep) — propose, don't unilaterally re-status it.
7. **Bucket B** string swaps (any time; independent). Re-seed asset_registry after B3; verify the prod row.
8. **Bucket C: nothing.** Confirm `platform/scripts/m9/*` + `09_MULTI_SCHOOL_TRIANGULATION/` stay untouched.

After each step run `schema_validator.py` + `drift_detector.py` (manifest mode) to prove green. Version-bump
CLAUDE.md + CURRENT_STATE + any changed governance artifact per B.8. **Report** a per-file changelog + the
validator/drift output after each step. **DO NOT seal; preserve all Bucket C.** This is governance — if any
step can't pass validation, STOP and report rather than forcing it.

---

## PROMPT 2 — L3 kala_convergence all-Jupiter bug (paste to Claude Code, separate session)

You are Claude Code in Antigravity on MARSYS-JIS. DIAGNOSE then FIX an L3 Kāla defect. **DO NOT seal.**

**The defect:** `kala_convergence` for the native (482012f1-710e-4a25-994a-93821f5871aa) has
`constituent_factors->>'planet' = 'jupiter'` for **660/660 rows** → all 60 `kala_obstruction` →
all ph_pratikara mitigation = Jupiter. **This is almost certainly wrong:** the convergence ENGINE
(`brahmagyan/kala/convergence.py`) enumerates dasha events DSH.V.001–DSH.V.022 with VARIED mahadasha lords
(Jupiter 1984, Saturn 2008, Mercury 2022, Ketu/Venus periods, etc.), so the source dasha sequence is
correctly diverse — yet the stored convergence `planet` collapsed to all-Jupiter.

**Rails:** This is L3 (sealed) — native-authorized surgical fix. Frozen contract; anti-drift; L-is-
authority; verify against live prod data; Gemini/DeepSeek only; canonical chart never mutated.

**STEP 1 — Diagnose the exact mechanism (don't assume).** Trace how `constituent_factors['planet']` is set
in the convergence write path: `writers/ka_sangam.py` (_generate_windows / _generate_lifetime_windows /
the window-scoring + `_insert_windows` ~line 297) + the predicates it reads + `KaDashaKalaService`. Run:
```
-- what dasha lords SHOULD the windows span? (the source truth)
SELECT system_id, level_n, lord, count(*), min(start_date), max(end_date)
  FROM chart_dashas WHERE chart_id='482012f1-...' AND system_id='vimshottari' AND level_n IN (1,2)
  GROUP BY system_id, level_n, lord ORDER BY 3 DESC;
-- what planets does convergence actually store, by window date?
SELECT constituent_factors->>'planet' AS planet, count(*),
       min(window_start), max(window_end)
  FROM kala_convergence WHERE chart_id='482012f1-...'
  GROUP BY 1 ORDER BY 2 DESC;
```
Determine which of these is true:
  (a) The writer HARDCODES or DEFAULTS planet (e.g. a fallback that never gets overridden) → bug in the
      assignment.
  (b) The writer reads the WRONG field / wrong dasha level (e.g. always the MD lord at birth, or a single
      predicate's planet, not the window's actual active lord) → bug in the lookup.
  (c) Only Jupiter-associated windows actually scored ≥3 factors and survived `_dedup`/the cap, so the
      table is legitimately Jupiter-dominated → NOT a bug; document why (but 660/660 with zero other
      planets is implausible if Saturn/Mercury MDs have real transit+dasha activity).
Report the root cause with evidence BEFORE fixing.

**STEP 2 — Fix (only if 1 = a or b).** Derive each window's `planet` from the ACTUAL active dāśā lord for
that window's date (via KaDashaKalaService / chart_dashas at the window midpoint), so convergence reflects
the real lord sequence. Preserve the convergence-scoring logic; fix only the planet attribution. Keep it
within the frozen contract (ka_sangam writes only kala_* tables).

**STEP 3 — Rebuild the chain + verify.** Rebuild via the orchestrator (not a direct runner — so
asset_throughput is correct): ka_sangam → (re-derive kala_obstruction via ka_vighnakara) → ph_pratikara.
Verify `kala_convergence` now shows a DIVERSE planet distribution matching the dāśā sequence; ph_pratikara
mitigation now spans multiple afflicting grahas (not 60× Jupiter). Add a test asserting convergence planet
diversity is consistent with the chart_dashas lord sequence (guard against re-collapse).

**STEP 4 — Report (NO SEAL).** Root cause (a/b/c), the fix (if any), the before/after planet distribution,
the rebuilt ph_pratikara graha spread, and whether this changes the L4 seal picture. If the fix reopens any
L3 seal artifact, version-bump it (don't re-seal from scratch). Do NOT seal L3 or L4. STOP for native review.

> NOTE on the L4 seal: ph_pratikara was earlier "accepted as genuine Jupiter dominance." This investigation
> SUPERSEDES that — if the convergence collapse is a bug, the all-Jupiter mitigation was an artifact, and
> ph_pratikara must be rebuilt before L4 seals. Flag this to the native explicitly.

---
*End. Prompt 1: tooling-safe M-phase→layer migration (back-compat validators FIRST; preserve Bucket C
history). Prompt 2: diagnose+fix the L3 convergence all-Jupiter collapse, rebuild the obstruction→mitigation
chain. Both independent; NEITHER seals.*
