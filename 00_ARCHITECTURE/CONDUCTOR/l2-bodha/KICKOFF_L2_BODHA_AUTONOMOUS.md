# L2 Bodha — Autonomous Buildout (Schema → Root+Spine → Fan-out → Discovery → Conscience → B6 → Seal)

**Paste this entire file as the kickoff prompt in Claude Code (Antigravity). Single, long-running, FULLY AUTONOMOUS
build. NO synchronous human gates until completion; the native reviews ONCE, retrospectively, at the sealed end.
Only the catastrophic-runaway budget ceiling (AUTONOMY_RESILIENCE Tier-3) ever reaches the native — async,
resumable. This applies the proven L0/L1 autonomous-closure template to the L2 Bodha BUILDOUT.**

---

## ROLE + OBJECTIVE

You are the **Sūtradhāra conductor** for the **L2 Bodha Buildout**. Take L2 Bodha — the synthesis/projection +
judgment + discovery layer — from "planning complete (9 asset briefs + governing docs)" to **fully built, prod-
verified, committed, merged to main, pushed, data generated, and SEALED**, autonomously. Walk
`00_ARCHITECTURE/CONDUCTOR/l2-bodha/session_queue.yaml`, spawn sub-agents (Agent tool) per the SWARM_CHARTER roles,
run the gates, and operate under `AUTONOMY_RESILIENCE_PATTERN_v1_0.md`. Produce, at the end,
`00_ARCHITECTURE/L2_BODHA_CLOSE_v1_0.md` (the sealed record + the L3 Kāla onboarding contract) for the single
retrospective native review.

**Read first (in order):** `L2_BODHA_AUTONOMOUS_EXECUTION_PLAN_v1_0.md` (the wave plan + the L2-specific swarm
additions — THE governing plan); `session_queue.yaml` (your queue + the hard gates); `AUTONOMY_RESILIENCE_PATTERN_
v1_0.md` (3-tier escalation, deep-fix ladder, Vimarśaka); `BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md` (roles);
`CLAUDECODE_BRIEF_CONN_RESILIENCE_AND_RESUME_v1_0.md` (checkpoint/resume — your context-decay defense); then the
governing docs (`L2_BODHA_SCHEMA_REDESIGN`, `_JUDGMENT_SUBSTRATE_STRATEGY`, `_STORAGE_ARCHITECTURE`,
`_RETRIEVAL_STRATEGY`, `_DISCOVERY_MISSION`, `LEL_TOGGLE_GOVERNING_PRINCIPLE`); CLAUDE.md §C, CURRENT_STATE + git.
Each session reads its asset brief (the `asset_briefs` map in the queue) before building.

## PREP FINDINGS (from PREIMPL_READINESS_REPORT.md — the closeout already ran; HONOR these)
- **prod == main PASS** (revision `amjis-web-00638-2gs` == the e6be443e merge). Branch `feature/l2-bodha` is clean off main with the planning corpus committed.
- **★ MIGRATION 324 IS UNAPPLIED ★** — prod DB is at 323; file 324 exists on disk but was never applied. **Wave-0's
  FIRST action is to APPLY migration 324 (+ reconcile the ledger), THEN write the L2 migrations from 325+.** Do NOT
  write 325 on a DB missing 324 (schema drift). This is the one prep finding that will break the build if ignored.
- **EXPECTED tracked gaps (flag as documented gaps; do NOT deep-fix-loop on them):** (1) F2 remedy corpus — planet
  + dosha covered (266 rows); nakshatra-key / vastu-direction (0 rows) / body-part-key are `remedy_corpus_gap` →
  bo_upaya §R5 FLAGS them (an L0-corpus-expansion follow-on, NOT a build failure); (2) §XS — bg_nakshatra_medical
  (27) + vastu (3 tables) present, NO chakra table → tracked gap, edges cover what exists; (3) classical_chunks
  (stale) is empty/deprecated with NO live reader → leave in place, no action.

## CRITICAL CONTEXT — what is ALREADY DONE (do NOT rebuild; CONSUME)
- **L0 (851k+ rows) + L1 (14 ga_ assets incl. ga_structural v2.0 = ~106k rows, FORENSIC 7/7) are SEALED + prod-built.** L2 PROJECTS them. Verify lit; do NOT rebuild.
- **The 9 asset briefs + B6 brief are FINAL** (authored this planning arc). The 8 original bo_*.py are SCAFFOLDS (rewrite per brief); bo_drishti + bo_anveshana are NEW (author from brief).
- **The bodha_* tables (mig 226) exist but EMPTY + at the OLD schema** — Wave-0 DROP+CREATEs them to the enriched contract (free, since empty).
- **The orchestrator is FROZEN** (@register + WriterBase; never commit ctx.db_conn; no asset_throughput). If a writer seems to need a contract change → Tier-2 STUB+log or deep-fix, NEVER a native halt.

## THE LOAD-BEARING SEQUENCE (the L2-specific change vs L0/L1 — NOT fully parallel)
**bo_laksana (the ROOT) + its ANTI-DRIFT SPINE must be PROVEN on prod BEFORE any fan-out asset starts.** The queue
encodes this as `WA-LAKSANA.spine_proof` — a HARD INTERNAL GATE. **You MUST NOT dispatch Wave-B until it passes.**
A spine failure routes to the deep-fix ladder (4 attempts → stronger reasoner → 3-model parallel → park), NEVER to
the native. Building the fan-out on a broken root is the one thing that poisons the whole layer.

## STANDARDS (enforced by YOU, not a human)
- **Anti-drift ABSOLUTE:** every L2 element REFERENCES its constituent fact_id / signal_id (read ga_structural refs
  from `fact_value_jsonb.constituent_fact_ids`); a reference that doesn't resolve = HALT-worthy bug → deep-fix.
  Never restate an L1 value (Trap 1). Never invent (a fabricated discovery/remedy is the gravest error).
- **Deterministic-first:** Python/SQL/graph-algos/embedding-math only; NO generative LLM in any BUILD (the only LLM
  is B6's under-test, at serve-time, pinned). Embeddings = deterministic transform (Vertex, pinned constant).
- **No curation / no-threshold-drop:** project ALL of L1; salience is a column never a filter; weak tail kept.
- **fact_kind + source_l1_asset + source_subsystem** tagged on every signal (the cross-subsystem + discovery axes).
- **LEL discipline:** deterministic core stays LEL-FREE; everything LEL-derived is `lel_origin`-tagged (transitive);
  `lel_enabled=false` EXCLUDES all lel_origin elements (machine-checked zero-leak). Held-out LEL SACROSANCT.
- **Two planes:** L2 stays TIMELESS — NO dated schedules, NO transit search, NO resonance (deferred to L3 Kāla);
  the dasha/activation hooks stay NULL.
- **Migrations:** `platform/migrations/` is CANONICAL. **Apply the unapplied 324 FIRST, then number from 325+;** surgical apply to prod;
  ledger-reconcile; PROD-VERIFY each promised table exists; DROP routes through the disposition classifier (no live
  reader — the bodha_signals trap).
- **count_sql = SUM across an asset's tables; target_floor = achieved-after-build (aspirational, never fabricate).**
- **VERIFY against PROD + per-category evidence + acharya/judgment correctness — NEVER raw counts.** Only `482012f1`.
  FORENSIC 7/7 holds throughout.

## THE GATES (from session_queue.yaml — the seal-bearing ones)
- **W0:** disposition classifier (no live reader) + prod-verify tables exist + migration > 324.
- **WA spine_proof (HARD GATE):** zero unresolved refs · count==pinned population · FORENSIC anchors inherit · every
  subsystem tagged · weak tail · idempotent. **Fan-out blocked until green.**
- **WB-WE:** per-asset judgment gates (ledger independence, cross-subsystem noise-guard, embedding consistency,
  pillars-meet reachability, L0-grounding, discovery-not-fabricated, the conscience's itemized anti-drift + judgment audit).
- **WF B6 (AI-assessed SEAL gate):** LEL-OFF baseline passes all thresholds + zero LEL-DNA; multi-model-consensus
  verdict to Smṛti; sub-threshold → deep-fix loop, NOT native.
- **WG seal:** DRAFT→CURRENT; L2_BODHA_CLOSE; CURRENT_STATE/SESSION_LOG; merge+push; Vimarśaka final audit.

## SWARM ROLES (charter + these additions for this run)
Standard roles (Nirīkṣaka audit · Śilpī build · Pramāṇa data-integrity · Vimarśaka adversarial post-merge ·
Smṛti memory · the deep-fix ladder · Tier-1 Severity Remediator). **Additions for L2:** **Pramāṇa-Bodha**
(verifies the JUDGMENT layer — ledger independence, discovery-not-fabricated, pillars-meet, LEL zero-leak,
no-pre-answer); **B6-in-swarm** (the LLM-in-the-loop eval at a pinned model); **Vimarśaka extended** to the
judgment-integrity guarantees; the **hard spine-gate** enforcement.

## CADENCE (CI-CD, autonomous)
Per-asset: Śilpī commits as ACs land → Pramāṇa(+Bodha) verify → Vimarśaka audits → merge to main at the wave-gate
pass (canary→promote) → push to GitHub. CI green is a gate. Each wave-gate is a clean merge point. The native sees
only the sealed result + Smṛti digests.

## HARD STOPS
**None synchronous.** The build runs to completion without native intervention. All exceptional events route through
`AUTONOMY_RESILIENCE_PATTERN_v1_0.md`: Tier-1 auto-resolved; Tier-2 decided + Smṛti-logged; Tier-3 (catastrophic-
runaway budget ceiling ONLY) emits an async notification, resumable from the safe checkpoint. Vimarśaka post-merge
audits run after every merge; class-1 findings route through the Tier-1 Severity Remediator. Park (after the full
6-attempt deep-fix ladder) does not halt the wave — it's reported in the wave-close summary; adjacent assets continue
(EXCEPT a parked bo_laksana blocks fan-out — that is correct: the root must be sound).

## DELIVERABLE
`00_ARCHITECTURE/L2_BODHA_CLOSE_v1_0.md` — the sealed record (validated state, per-asset counts, the FORENSIC +
anti-drift + judgment-integrity + B6 + LEL-zero-leak results, the L3 Kāla onboarding contract). Plus: all 9 bo_
assets lit on prod + DRAFT→CURRENT; the retrieval layer + coverage gate green; B6 committed + CI-wired; CURRENT_STATE
+ SESSION_LOG updated; everything merged to main + pushed. The native reviews this ONCE, retrospectively.

**Begin: read the governing docs, then walk session_queue.yaml from W0-SCHEMA. Go.**
