---
artifact: L2_BODHA_AUTONOMOUS_EXECUTION_PLAN_v1_0.md
canonical_id: L2_BODHA_AUTONOMOUS_EXECUTION_PLAN
version: 1.0
status: PLAN_FOR_NATIVE_REVIEW (the pre-implementation closeout + the fully-autonomous Conductor/swarm execution of L2 Bodha)
authored_by: Cowork (grounded in the existing Conductor + AUTONOMY_RESILIENCE + SWARM_CHARTER framework) 2026-06-19
purpose: >
  Take L2 Bodha from "planning complete (9 briefs + governing docs)" to "fully built, verified, committed, merged
  to main, pushed, data generated, sealed — autonomously, zero synchronous human gates." Two parts: (A) the
  PRE-IMPLEMENTATION closeout (everything to settle before the Conductor kicks off, incl. F2 + the open items);
  (B) the AUTONOMOUS EXECUTION plan (the wave queue, the hard internal gates, the swarm roles, the seal).
governing_framework:
  - AUTONOMY_RESILIENCE_PATTERN_v1_0.md (3-tier escalation; only catastrophic-budget reaches the native)
  - BUILD_GUARANTOR_AUTONOMOUS_MODE_v1_0.md + BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md (the role roster)
  - CONDUCTOR_PROMPT_v1_0.md + the proven L0/L1 autonomous-closure kickoff templates
  - CLAUDECODE_BRIEF_CONN_RESILIENCE_AND_RESUME_v1_0.md (the context-decay / resume defense)
native_decisions_2026_06_19:
  - "Fully autonomous: authoring→build→runtime→data-generation→commit→merge→push→seal, NO synchronous human gate (only catastrophic-budget per AUTONOMY_RESILIENCE Tier-3)."
  - "The bo_laksana anti-drift SPINE GATE is a SWARM-ENFORCED HARD INTERNAL GATE (not a native pause); fan-out BLOCKED until it verifies; failure → deep-fix ladder."
  - "B6 seal is FULLY AUTONOMOUS + AI-ASSESSED (multi-model consensus, logged to Smṛti, native reviews retrospectively); L2_BODHA_CLOSE sealed autonomously."
---

# L2 Bodha — Autonomous Execution Plan v1.0

## PART A — PRE-IMPLEMENTATION CLOSEOUT (settle BEFORE the Conductor kicks off)
These are the things a fresh autonomous Conductor needs in place + the open issues to close. Do them in this session / a short prep session — NOT inside the autonomous run.

### A1 — Git / branch housekeeping (the foundation)
- [ ] **Fresh branch off current `origin/main`** (NOT the stale `recovery/pre-l2-stash-salvage`, which is 16 behind). The build must start from main (ga_structural v2.0, 14 L1 assets, retrieval layer, migrations ≤324).
- [ ] **Commit ALL planning docs** (9 briefs + ~12 governing docs + this plan) onto that branch — they are the swarm's INPUT artifacts; they belong in the repo.
- [ ] `test-results/` → gitignore/delete (junk).
- [ ] Confirm **`platform/migrations/` is the CANONICAL tree (max 324); new L2 migrations start at 325+** — document in the kickoff (the "two migrations numbered 174" trap).

### A2 — Prod == main verification (the seed→prod-divergence guard)
- [ ] `git log origin/main` HEAD == deployed prod revision; migrations ≤324 APPLIED on prod (not just on disk). `/api/cockpit/stats?chart_id=482012f1-...` for live asset state.

### A3 — Close the open data/corpus issues (incl. F2)
- [ ] **F2 residual:** verify `brahma_remedy_corpus` CONTENT actually has medical / vastu / nakshatra remedy rows (not just the design-slot). Where rows are missing → flag as an L0-corpus-expansion sub-task the swarm handles (or defer with a tracked gap). Do NOT let RM silently lack subsystem coverage.
- [ ] **Cross-subsystem L0 mappings:** confirm the classical cross-discipline mapping tables exist for the §XS edges — `bg_nakshatra_medical` VERIFIED; CONFIRM the vastu (graha→direction) + any other mappings exist, or flag the gap.
- [ ] **Embedding:** confirm the classical_text_chunks model (text-multilingual-embedding-002, 768) is the live one; decide the classical_chunks (stale ivfflat) retire/repoint.

### A4 — Author the CONDUCTOR INPUTS (these don't exist yet — the swarm can't run without them)
- [ ] **`00_ARCHITECTURE/CONDUCTOR/l2-bodha/session_queue.yaml`** — the wave/asset queue with the hard gates (Part B).
- [ ] **`KICKOFF_L2_BODHA_AUTONOMOUS.md`** — the single paste-prompt (mirrors the L1-closure kickoff structure; embeds the standards + the L2-specific gates + the resilience-pattern pointer).
- [ ] The Smṛti dir (`00_ARCHITECTURE/CONDUCTOR/l2-bodha/smriti/`) + halt log.

### A5 — Surfaced PLANNING residuals (must exist before kickoff — they're swarm inputs)
- [ ] All 9 asset briefs + B6 brief + the governing docs are FINAL (they are — this conversation closed them).
- [ ] The schema-migration DDL is a BUILD deliverable (the swarm writes it from the schema-redesign doc) — but confirm the schema-redesign doc is complete enough to generate DDL from. (It is — §3 per-asset.)
- [ ] The LEL `lel_origin` tagging + `lel_enabled` is in the briefs/retrieval-strategy (it is) — the swarm implements it.

---

## PART B — THE AUTONOMOUS EXECUTION (the Conductor run)

### B0 — Framework (reuse, do NOT reinvent)
The Sūtradhāra Conductor walks `session_queue.yaml`, spawns sub-agents per the SWARM_CHARTER roles, runs gates,
and operates under AUTONOMY_RESILIENCE: **Tier-1 auto-resolved, Tier-2 decided+Smṛti-logged, Tier-3 (catastrophic
budget ONLY) async-notifies the native.** Vimarśaka adversarial-audits every merge; the deep-fix escalation ladder
(4 attempts → stronger reasoner → 3-model parallel → park) handles failures; CONN_RESILIENCE_AND_RESUME defends
context-decay (checkpoint + resume). Model policy: Gemini/DeepSeek (Anthropic banned unless asked).

### B1 — THE WAVE QUEUE (with the hard internal gate — the L2-specific change)
L2 is NOT fully parallel — it has a load-bearing sequence:

```
WAVE-0  PRE-FLIGHT (swarm): apply schema migrations 325+ (DROP+CREATE empty bodha_* to enriched contract —
        disposition classifier confirms NO live reader per DROP, the bodha_signals-live-reader trap); the
        embedding shared-constant module; classical_chunks cleanup; seed the registry. PROD-VERIFY tables exist.
   │
WAVE-A  bo_laksana (ROOT) + THE ANTI-DRIFT SPINE GATE  ← HARD INTERNAL GATE
        Build bo_laksana (full projection, all 14 L1 assets, source_subsystem tags, L0 bridge, salience/
        signature_tier/epistemic, lossless summary). Then the SPINE PROOF on prod:
        zero unresolved constituent_fact_ids · count == pinned chart_facts-population count · FORENSIC anchors
        inherit L1 values · every L1 subsystem produced ≥1 tagged signal · weak tail present · idempotent.
        ★ FAN-OUT IS BLOCKED UNTIL THIS PASSES. Failure → deep-fix ladder (NOT the native). ★
   │  (gate passed)
WAVE-B  FAN-OUT (parallel sub-agents): bo_sangati (CDLM + evidence ledgers) · bo_karanajala+bo_bimba (CGM +
        cross-subsystem edges) · bo_samskara (real Vertex embeddings) · bo_samvada (gestalt). Each verifies vs prod.
   │
WAVE-C  DEPENDENTS: bo_upaya (RM, R1-R5, seed-fix) · bo_drishti (lens). (depend on laksana+sangati[+karanajala])
   │
WAVE-D  bo_anveshana (DISCOVERY — mines all the above; intra + cross-subsystem; meaningfulness gate; non-fabrication).
   │
WAVE-E  bo_pramana_mapa (the CONSCIENCE — audits the whole layer: anti-drift itemized, judgment-integrity,
        pillars-meet reachability, LEL zero-leak, calibration frame). + the L2_bodha RETRIEVAL TOOLS + coverage gate.
   │
WAVE-F  B6 EVAL HARNESS (AI-assessed seal gate): run the question corpus through live retrieval+LLM in BOTH LEL
        modes; LEL-OFF baseline must pass all thresholds (recall/provenance/judgment/discovery/no-fab/dedup/
        zero-LEL-DNA); sub-threshold → deep-fix loop (NOT native). Multi-model-consensus verdict logged to Smṛti.
   │  (B6 passes)
WAVE-G  SEAL (autonomous): promote bo_* DRAFT→CURRENT; author L2_BODHA_CLOSE (with the L3 Kāla onboarding
        contract); update CURRENT_STATE + SESSION_LOG; final merge to main + push. Vimarśaka final audit.
```

### B2 — The L2-SPECIFIC SWARM ADDITIONS (gaps I'm surfacing — fold into the charter for this run)
1. **The hard SPINE GATE (Wave-A)** — a gate type the data-swarms didn't have (they were parallel-across-assets).
   The Sūtradhāra MUST NOT dispatch Wave-B until the spine proof passes. Encode as a queue dependency + a gate verdict.
2. **Pramāṇa-Bodha (judgment-integrity verifier)** — Pramāṇa's sibling for the JUDGMENT layer: ledger independence
   (no double-count), discovery-not-fabricated, pillars-meet reachability, LEL zero-leak proof, no-pre-answer. It's
   Pramāṇa with the bo_pramana_mapa checklist — verifies "the judgment is sound," not just "the data is correct."
3. **B6-in-swarm (LLM-in-the-loop eval)** — unusual for data swarms: a step that runs an LLM over questions at a
   PINNED model/temperature for reproducibility, scores vs the deterministic known-complete sets, AI-assessed seal
   verdict (multi-model consensus). Sub-threshold is a FIX loop, not a seal.
4. **Destructive-migration rails** — the Wave-0 DROP+CREATE routes through the B.2 disposition classifier (confirm
   no live reader per table — the bodha_signals trap); empty tables make it safe but the check is mandatory.
5. **Vimarśaka extended to judgment** — its adversarial post-merge read now also checks the judgment-integrity
   guarantees (not just data ACs).
6. **The LEL zero-leak proof** — a Pramāṇa-Bodha check baked into every wave: any lel_origin-tagged element in a
   toggle-off return = a finding (the strict rule, machine-checked).

### B3 — Commit / merge / push cadence (CI-CD, autonomous)
- **Per-asset:** the Śilpī commits as ACs land; Nirīkṣaka/Pramāṇa-Bodha verify; Vimarśaka audits; MERGE the asset's
  work to main at its wave-gate pass (canary→promote per AUTONOMOUS_MODE); push to GitHub. CI green is a gate.
- **The frozen-orchestrator rule:** writers conform (@register/WriterBase, never commit ctx.db_conn, no
  asset_throughput); if a writer seems to need a contract change → Tier-2 STUB+log or deep-fix, never a native halt.
- **Each wave-gate** = a clean merge point to main. Pushes happen at every merge. CI/CD (deploy.yml) runs per merge.

### B4 — The ONLY native-input event
Per AUTONOMY_RESILIENCE Tier-3: the catastrophic-runaway budget ceiling. Async notification; resumable. Nothing
else pauses. The native reviews the SEALED layer retrospectively (Smṛti digests + the L2_BODHA_CLOSE + Vimarśaka audits).

## §C — WHAT I'D FLAG AS RISK (honest, for the autonomous run)
1. **B6 is the riskiest autonomous step** — judgment quality is fuzzier to auto-assess than data integrity. Mitigation:
   multi-model consensus + the deterministic known-complete answer sets (the scoring IS deterministic; only the
   LLM-under-test isn't) + a generous deep-fix budget + the optional retrospective acharya calibration (§D of the resilience pattern).
2. **The spine gate failing repeatedly** would park bo_laksana → the whole layer blocks (it's the root). This is
   CORRECT behavior (don't build on a broken root) but means bo_laksana gets the deepest fix-budget. Acceptable.
3. **Volumetrics unknown until Wave-A runs** — the projection count is the load-bearing number; the swarm pins it
   with one prod query at Wave-A start (per bo_laksana §2.4) and sets target_floors = achieved.
4. **Two new assets (drishti, anveshana) have NO scaffold** — the swarm authors them from briefs (Śilpī from the brief). Fine.

---
*End of L2_BODHA_AUTONOMOUS_EXECUTION_PLAN v1.0. PART A pre-impl: fresh branch off main + commit the docs;
prod==main; close F2 (corpus content) + cross-subsystem L0 mappings + embedding cleanup; AUTHOR the missing
Conductor inputs (session_queue.yaml + KICKOFF + Smṛti dir). PART B autonomous run on the existing Conductor/
AUTONOMY_RESILIENCE/SWARM framework: Wave-0 schema → Wave-A bo_laksana + the HARD SPINE GATE (fan-out blocked
until proven) → Wave-B fan-out → C dependents → D discovery → E conscience+retrieval → F B6 AI-assessed seal gate
→ G autonomous seal+merge+push. L2-specific additions: the hard spine gate, Pramāṇa-Bodha (judgment-integrity),
B6-in-swarm, destructive-migration rails, Vimarśaka-extended-to-judgment, the LEL zero-leak proof. Only the
catastrophic-budget ceiling reaches the native; everything else is autonomous.*
