---
artifact: KICKOFF_L4_PHALA_REMEDIATION.md
canonical_id: KICKOFF_L4_PHALA_REMEDIATION
version: 1.0
status: READY — the SINGLE paste-prompt that launches the autonomous L4 Phala REMEDIATION pass (no human gates)
authored_by: Cowork 2026-06-22
operates_on: feature/l4-phala-autonomous @ cf4089f4 (the existing PR #328 build — DO NOT rebuild; remediate in place)
source_audit: L4_PHALA_CODE_AUDIT_REMEDIATION_v1_0.md (the code-grounded gap list)
note: Paste the §KICKOFF block ONCE to the Sūtradhāra Conductor (Claude Code in Antigravity). It remediates the existing branch — it does NOT re-run the original build.
---

# KICKOFF — L4 Phala REMEDIATION (Fully Autonomous, One Kickoff)

## What this is
The original L4 build (PR #328) is **strong and largely complete** — 10 of 12 components are real,
contract-clean, anti-drift-clean. This is a **targeted remediation of the real gaps**, NOT a rebuild.
The audit (`L4_PHALA_CODE_AUDIT_REMEDIATION_v1_0.md`) is ground truth — read it first. Do not touch
the components marked SOLID in audit §1. Only the R3–R9 items below.

## There is NO operator pre-flight.
The Conductor self-provisions (the branch already exists at `feature/l4-phala-autonomous`; reuse it).
The ONLY human action is pasting the §KICKOFF block once. The single pre-set value: the **$5k Tier-3
budget ceiling**. Everything else — proxy, deps, prod==main check, CI remediation — the Conductor does.

---

## §KICKOFF (paste this to the Conductor)

You are the **Sūtradhāra Conductor** for the **L4 Phala REMEDIATION** pass of MARSYS-JIS. Operate fully
autonomously per `00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md` + the
`BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md` roster. **Remediate the existing build in place — do NOT rebuild.**

**Read first (in order):**
1. `00_ARCHITECTURE/L4_PHALA_CODE_AUDIT_REMEDIATION_v1_0.md` — the gap list + the LOCKED native decisions (§4). THIS GOVERNS.
2. `00_ARCHITECTURE/CONDUCTOR/l4-phala-remediation/remediation_queue.yaml` — your queue. Walk it top-to-bottom.
3. `00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_U2_LIFETIME_PRANA_v1_0.md` — the U2 spec (for R3).
4. The original `L4_PHALA_DECISIONS_LEDGER_v1_0.md` (D29 = Prāṇa dropped; D41 = rectification spec; D43 = no-auto-override).
5. `L3_KALA_CLOSE_v1_0.md §9` — ratified L3 params (U2 re-seals L3).

**Branch:** reuse the existing `feature/l4-phala-autonomous` (worktree `MadhavL4Phala`). Per-task
sub-branches for the parallel band. The original PR #328 stays open; your commits extend it.

### THE LOCKED DECISIONS (from the audit §4 — non-negotiable)
- **D-R1 — ph_sodhana = KEEP BOTH.** The anomaly registry (migrations 333_phala_sodhana +
  334_phala_suddha_sodhana, the writers) is RATIFIED as-is — **do not touch it.** ADD birth-time
  rectification as a SEPARATE capability: fill the dead `333_phala_rectification.sql` +
  `334_phala_rectification_best.sql` stubs with real DDL; build rectification writer(s).
- **D-R2 — U3 §3.5 = DROPPED.** Delete the empty `339_kala_convergence_current_breakdown.sql`. The
  currents enrichment logic itself stays (it exists + passes).
- **N4 BOUNDARY (HARD):** L4 + U2 are bounded at **level-4 (Sūkṣma)**. NO Prāṇa, NO `chart_dashas_prana`,
  NO level-5 persistence ANYWHERE. U2 is lifetime-horizon over the existing N1–N4 parvas only. Any code
  path that would create level-5 data is a STOP-and-Tier-2-park.

### THE REMEDIATION TASKS (the queue — file-disjoint ones run in parallel)
**BAND A (parallel — file-disjoint):**
- **R3 — U2 lifetime + null-score fix (N4-bounded).** Per the U2 brief: extend `ka_sangam` convergence
  horizon 5y→lifetime (COARSE grain — keep `kala_convergence` row budget bounded, ~13k cap per §3.1);
  re-run `ka_jivana_parva` scoring so `kala_jivana_parva.avg_effective_score` is **non-null** across all
  739 parvas; fill the real DDL in `338_kala_convergence_horizon_tier.sql`
  (`ALTER TABLE kala_convergence ADD COLUMN horizon_tier text CHECK (horizon_tier IN ('near','lifetime'))`).
  Re-seal L3 (version-bump `L3_KALA_CLOSE`, authority confirmed D27). `[verify: prod]` non-null scores.
- **R4 — Birth-time rectification (the new build, D-R1 + D41).** Fill `333_phala_rectification.sql` +
  `334_phala_rectification_best.sql` with real DDL (candidate-time table + best-candidate table). Build
  the rectification writer(s): PyJHora `compute_ascendant` per candidate birth time over a window around
  10:43 IST; score each candidate against LEL life events (whole-instrument fit); **LEAKAGE-FIREWALL**
  (no post-event-disclosure data in the fit); confidence interval; **NO-AUTO-OVERRIDE** — the writer
  STAGES the best candidate for one-click native adoption and NEVER UPDATEs the canonical chart
  (`482012f1`); B.10 — canonical chart immutable without native sign-off. Register the rectification
  asset(s); count_sql `$1`; Dockerfile.pipeline COPY (already covers services/ — verify).
- **R5 — Fix CI-breaking hardcoded paths.** Replace `/Users/Dev/Vibe-Coding/...` absolute paths with a
  repo-root-relative resolver (`Path(__file__).resolve().parents[N]`) in the L4-touched files:
  `tests/test_u1_dasha_consensus.py`, `tests/l2/test_b6_eval_harness.py`, and the 6 scripts listed in
  audit MAJOR-4. (Pre-existing governance scripts: fix if trivial, else log as known_residual.)

**THEN (serial after Band A):**
- **R6 — Stub cleanup.** Delete `337_phala_outlook.sql` + `339_kala_convergence_current_breakdown.sql`.
  Confirm 333/334 filled (R4), 338 filled (R3). End state: ONE real file per migration number, ZERO dead
  stubs, ZERO duplicate-number collisions.
- **R7 — Rename test.** `test_phala_outlook.py` → `test_phala_phaladesa.py`, repoint to the real table.
- **R8 — CI GREEN (merge gate).** Run the full deploy.yml PR-build-check: both images build, the
  ga_writers import-guard passes, **migrate.ts applies 330–340 cleanly on a fresh DB**, full pytest
  passes (now that R5 unblocked it). Reconcile + report the REAL test count. CI must be green on the head SHA.

### THE HARD RULES (non-negotiable — same as the original build)
1. **Frozen orchestrator contract:** `@register('ph_*')` / `WriterBase` / `run(ctx)`; NEVER commit or
   close `ctx.db_conn`; never write `asset_throughput`; `WriterResult(asset_id=, rows_inserted=)`; `$1`
   count_sql (never `$$CHART_ID$$`); delete-then-insert idempotency. New writers' service dirs COPY'd in
   Dockerfile.pipeline.
2. **Anti-drift:** every writer writes ONLY its own layer's tables (phala_* for L4; the U2 re-run writes
   only L3 kala_* tables it owns). Zero out-of-layer writes.
3. **L-is-authority:** rectification references LEL event IDs + L1 fact_ids; never restates a computed value.
4. **Model policy:** Gemini/DeepSeek only; Anthropic BANNED (already enforced in ph_phaladesa — keep it).
5. **Autonomy:** all gate failures → the 6-attempt multi-model deep-fix ladder → Tier-2 park + Smṛti.
   The ONLY thing that reaches the native: the **$5k Tier-3 budget ceiling**, and (async, non-blocking)
   the rectification chart-revision flag if a different Lagna scores best (staged, one-click adopt post-seal).

### THE SEAL (R9 — HARD VISUAL gate, the #1 L3 lesson)
After merge + deploy: the deployed **Cloud Run revision == the merge SHA**; the LIVE cockpit Phala panel
shows **all assets lit with real counts** (the 8 ph_* + the rectification asset(s)), the rectification
tables POPULATED, `kala_jivana_parva` scores non-null, ZERO error/missing_table — on **prod AND
localhost**. Green JSON / a "DONE" report / an unmerged-branch fix are ALL false positives. Then:
anti-drift final audit, PROD-VERIFY every AC, FORENSIC 7/7, canonical chart NOT mutated, promote DRAFT→
CURRENT, set target_floor = achieved count, author `L4_PHALA_CLOSE_v1_0.md`, update CURRENT_STATE +
SESSION_LOG. Final Vimarśaka audit (temporal + anti-drift).

**Budget ceiling: $5,000 (Tier-3). Begin with Phase 0 self-provisioning, then walk the remediation_queue.**

---
*End of KICKOFF_L4_PHALA_REMEDIATION v1.0. Remediate in place: U2 (build), rectification (build),
CI-paths (fix), stub cleanup, CI-green, visual seal. Keep everything the audit marked SOLID. N4-bounded.*
