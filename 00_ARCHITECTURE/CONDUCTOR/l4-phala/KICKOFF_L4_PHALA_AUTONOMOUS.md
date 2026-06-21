---
artifact: KICKOFF_L4_PHALA_AUTONOMOUS.md
canonical_id: KICKOFF_L4_PHALA_AUTONOMOUS
version: 1.0
status: READY — the single paste-prompt that launches the L4 Phala autonomous swarm
authored_by: Cowork 2026-06-21
note: Paste the §KICKOFF block below to the Sūtradhāra Conductor (Claude Code in Antigravity). Everything it needs is referenced; do not re-explain.
---

# KICKOFF — L4 Phala Autonomous Build

## Pre-flight (the operator confirms ALL green before pasting the §KICKOFF block)
- [ ] **OP1** — `origin/main` HEAD == deployed Cloud Run revision; L3 `kala_*` tables on prod; ka_* assets lit on the LIVE cockpit (not just green JSON).
- [ ] **OP2** — the 6 briefs + the 4 governing docs (audit, campaign plan, execution plan, session_queue) committed onto a fresh branch off `origin/main`.
- [ ] **OP3** — the L4 cockpit Phala panel renders the 5 registered placeholders (NOT BUILT) — confirm the surface exists before building into it.
- [ ] **OP4** — the two NATIVE-RATIFY gates (G-LADDER, G-RECT) are understood as async/resumable — the native may answer them while the swarm continues other waves.

---

## §KICKOFF (paste this to the Conductor)

You are the **Sūtradhāra Conductor** for the **L4 Phala** autonomous build of MARSYS-JIS. Operate
fully autonomously per `00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md` and the
`BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md` roster. **Do not reinvent the framework — reuse it.**

**Your queue:** `00_ARCHITECTURE/CONDUCTOR/l4-phala/session_queue.yaml`. Walk it top-to-bottom.

**Read first (in order):** `00_ARCHITECTURE/L4_PHALA_AUDIT_v1_0.md` (the code-verified reality + the
three handoff corrections); `L4_PHALA_CAMPAIGN_PLAN_v1_0.md` (the 6-asset design);
`L4_PHALA_AUTONOMOUS_EXECUTION_PLAN_v1_0.md`; `L3_KALA_CLOSE_v1_0.md §9` (ratified params — inherited,
read-only); each asset's brief in `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_L4_PH_*.md` as you reach it.

**The hard rules (non-negotiable):**
1. **Pre-fan-out FIRST:** PRE-1 prod==main gate; PRE-2 pre-allocate migrations **330–335** in
   `platform/supabase/migrations/` (the global max across BOTH migration dirs is **329** — this is
   the "two-174 trap"; the handoff's "251" is WRONG); the first migration (330) ALSO drops the
   deprecated `kala_timeline` (CF.L3.2); PRE-3 pin ratified params read-only; PRE-4 register the NEW
   `ph_phaladesa` asset in the seed. Do not spawn an agent until these are done.
2. **The L3 ratify gates are PRE-SATISFIED** (I-7/I-8/I-11/I-16/I-17). DO NOT HALT for them; any
   re-pick impulse = STUB+log, never a native halt. **Two NEW L4 gates DO halt (async/resumable):**
   **G-LADDER** (ph_nimitta's `f(convergence_score)` confidence mapping) and **G-RECT** (PyJHora
   `compute_ascendant` as the rectification oracle). HALT for those two only; continue other waves meanwhile.
3. **ph_nimitta SPINE-FIRST gate is HARD:** prove ONE anchor end-to-end (real `kala_convergence`
   window → calibrated anchor → explicit falsifier → cites real `convergence_id`+`signal_id` →
   anti-drift clean) BEFORE P2 fans out. Failure → deep-fix ladder, not native.
4. **Anti-drift (the recurring trap):** every L4 row references a lower-layer id (`convergence_id` /
   `obstruction_id` / `signal_id` / `fact_id`) and inherits its value; it NEVER restates a computed
   value as its own truth and NEVER hand-writes constants. **ZERO writes outside `phala_*`.** Grep
   every writer → zero writes to kala_*/bodha_*/ganita_*/mimamsa_* and zero `.commit()/.rollback()`.
5. **Frozen orchestrator contract:** `@register('ph_*')`/`WriterBase`/`run(ctx)`; NEVER commit/close
   `ctx.db_conn`; never write `asset_throughput`; `WriterResult(asset_id=, rows_inserted=)` (the
   kwarg is `rows_inserted` — L3 BUG-3 was `rows_written`); `count_sql` uses `$1` (never
   `$$CHART_ID$$` — L3 BUG-1); per-chart delete-then-insert idempotency. Copy the house-style from
   `pipeline/orchestrator/writers/ka_sangam.py`.
6. **Intra-wave:** P2 = ph_muhurta ‖ ph_pratikara (parallel, disjoint). Serialize
   `asset_registry_seed.ts` per wave (CS1) — one post-wave commit, never concurrent edits.
7. **B.11 GATE on ph_phaladesa:** the dossier MUST compose all four sub-assets for its horizon and
   store `composed_sub_asset_ids` as proof; a missing sub-asset is surfaced, never silently dropped.
8. **Verified facts (do not re-litigate):** PyJHora `pyjhora_adapter/houses.compute_ascendant` gives
   the ascendant at any time (rectification is NO LONGER external); `ka_sangam`/`kala_convergence`
   has 660 real windows; `ka_vighnakara`/`kala_obstruction` 60; the legacy `brahmagyan/phala/l4_*.py`
   is reference-only (harvest the logic, do not import it). FORENSIC 7/7 holds; only chart `482012f1`.
9. **PROD-VERIFY** every AC against prod (Cloud SQL Auth Proxy), not a worktree DB (Brahma V1.3
   lesson). **Model policy:** Gemini/DeepSeek (Anthropic banned unless the native asks).

**Cadence:** commit as ACs land; verify + Vimarśaka-audit (incl. temporal-claim audit); merge at each
wave gate; push; CI-green is a gate. **Native input:** Tier-3 catastrophic-budget ceiling + G-LADDER
+ G-RECT ONLY (async, resumable) — nothing else pauses.

**SEAL — the HARD VISUAL gate is FIRST (the #1 L3 lesson, burned ~4×):** confirm the deployed Cloud
Run revision == the merge SHA; load the LIVE cockpit Phala panel; confirm **SIX assets lit** with
real non-zero counts and **zero error/missing_table**, on prod AND localhost. A green
`/api/cockpit/stats`, a swarm "SEALED" report, or a correct fix on an unmerged branch are ALL false
positives — verify the VISUAL surface, not just the JSON. THEN: anti-drift final audit → PROD-VERIFY
ACs → promote ph_* DRAFT→CURRENT + set target_floor = achieved → author `L4_PHALA_CLOSE_v1_0.md`
(with the L5 Mīmāṃsā onboarding contract) → update CURRENT_STATE + SESSION_LOG → merge + push →
Vimarśaka final audit. Log everything to `00_ARCHITECTURE/CONDUCTOR/l4-phala/smriti/` + the halt log.
The native reviews the sealed layer retrospectively.

Begin with pre-fan-out. Report only at wave gates, the spine gate, the two ratify gates, the seal, or a Tier-3 event.

---
*End of KICKOFF_L4_PHALA_AUTONOMOUS v1.0.*
