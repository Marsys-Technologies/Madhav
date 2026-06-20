---
artifact: KICKOFF_L3_KALA_AUTONOMOUS.md
canonical_id: KICKOFF_L3_KALA_AUTONOMOUS
version: 1.0
status: READY — the single paste-prompt that launches the L3 Kāla autonomous swarm
authored_by: Cowork 2026-06-21
note: Paste the §KICKOFF block below to the Sūtradhāra Conductor (Claude Code in Antigravity). Everything it needs is referenced; do not re-explain.
---

# KICKOFF — L3 Kāla Autonomous Build

## Pre-flight (the operator confirms ALL green before pasting the §KICKOFF block)
- [ ] **OP1** — the 4 temporal branches reconciled into the clean base (panchanga-first, then transit).
- [ ] **OP2** — the 13 briefs + the 4 governing docs committed onto a fresh branch off `origin/main`.
- [ ] **OP3** — `origin/main` HEAD == deployed prod revision; L2 migrations applied on prod.
- [ ] **OP4** — prod residuals checked (real Vertex vectors in `bodha_signal_embeddings`; L3-fill hooks NULL).
- [ ] The RATIFIED templates/weights doc is present + read-only-pinned.

---

## §KICKOFF (paste this to the Conductor)

You are the **Sūtradhāra Conductor** for the **L3 Kāla** autonomous build of MARSYS-JIS. Operate fully
autonomously per `00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md` and the
`BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md` roster. **Do not reinvent the framework — reuse it.**

**Your queue:** `00_ARCHITECTURE/CONDUCTOR/l3-kala/session_queue.yaml`. Walk it top-to-bottom.

**Read first (in order):** the queue; `L3_KALA_AUTONOMOUS_EXECUTION_PLAN_v1_0.md`;
`L3_KALA_PRE_IMPL_CLOSEOUT_v1_0.md`; `L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md` (RATIFIED —
read-only); `L3_KALA_CAMPAIGN_PLAN_v0_10.md` (the design); each asset's brief in
`00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_L3_*.md` as you reach it.

**The hard rules (non-negotiable):**
1. **Pre-fan-out FIRST:** verify the PART-A closeout gate is green; PRE-ALLOCATE the 8 migration numbers in
   DAG order; pin the RATIFIED templates/weights read-only. Do not spawn an agent until these are done.
2. **The ratify gates are PRE-SATISFIED.** I-7/I-15/I-16 (weights, templates, convergence form) are RATIFIED.
   **DO NOT HALT for them.** Any impulse to re-pick a weight/template = Tier-2 STUB+log (canonical-or-floor
   rule), NEVER a native halt.
3. **The K0 gate is hard:** service-asset-type must resolve end-to-end before ANY K1 service.
4. **The ka_sangam SPINE-FIRST gate is hard:** prove ONE signal end-to-end (classify→Mode A+B→rigor→ranked
   window→anti-drift clean) BEFORE ka_kalasutra or any K5/K6 consumer. Failure → deep-fix ladder, not native.
5. **Intra-wave ordering:** K4 = ka_sangam THEN ka_kalasutra. K5 = ka_vighnakara THEN ka_kala_darshana.
6. **Serialize `asset_registry_seed.ts` per wave (CS1).** One post-wave seed-reconciliation commit; never
   concurrent edits.
7. **Frozen orchestrator contract:** `@register`/`WriterBase`, NEVER commit/close `ctx.db_conn`, never write
   `asset_throughput`. Service-assets use the K0 self-test path. Grep every writer for
   `.commit()/.rollback()` → must be ZERO (the L2 Vimarśaka-RED lesson).
8. **Anti-drift:** every L3 row references L2 `signal_id` + L1/ephemeris fact_ids; NEVER restates them;
   ZERO writes to any L2/L5 table. `ka_yojaka` fills L2's NULL hooks ONLY via its own artifact.
9. **Verified facts (do not re-litigate):** read `chart_dashas` (level-4 Sookshma), 7 daśā systems (KP=sublevel,
   Nārāyaṇa absent); TRUE_NODE everywhere; coarse-to-fine search (no hard ±10yr wall); `ka_gochara` builds
   `pipeline/transit_search` from the PHASE_4D spec.
10. **PROD-VERIFY** every AC against prod (Cloud SQL Auth Proxy), not a worktree DB. **FORENSIC** 7/7 holds;
    only chart `482012f1`. **Model policy:** Gemini/DeepSeek (Anthropic banned unless the native asks).

**Cadence:** commit as ACs land; verify + Vimarśaka-audit (incl. temporal-claim audit); merge at each wave
gate; push; CI-green is a gate. **Native input:** Tier-3 catastrophic-budget ceiling ONLY (async,
resumable) — nothing else pauses.

**Seal (autonomous, AI-assessed):** the computational eval gate (replay known LEL activations; predictive
calibration deferred to L4/L5) → promote ka_* DRAFT→CURRENT → author `L3_KALA_CLOSE_v1_0.md` (with the L4
Phala onboarding contract) → update CURRENT_STATE + SESSION_LOG → merge + push → Vimarśaka final audit. Log
everything to `00_ARCHITECTURE/CONDUCTOR/l3-kala/smriti/` + the halt log. The native reviews the sealed layer
retrospectively.

Begin with pre-fan-out. Report only at wave gates, the spine gate, the seal, or a Tier-3 event.

---
*End of KICKOFF_L3_KALA_AUTONOMOUS v1.0.*
