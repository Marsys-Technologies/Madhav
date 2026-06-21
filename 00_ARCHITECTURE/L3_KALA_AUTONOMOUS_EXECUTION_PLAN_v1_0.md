---
artifact: L3_KALA_AUTONOMOUS_EXECUTION_PLAN_v1_0.md
canonical_id: L3_KALA_AUTONOMOUS_EXECUTION_PLAN
version: 1.0
status: PLAN_FOR_NATIVE_REVIEW (pre-implementation closeout + fully-autonomous Conductor/swarm execution of L3 Kāla)
authored_by: Cowork 2026-06-21 — modelled on L2_BODHA_AUTONOMOUS_EXECUTION_PLAN_v1_0
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
purpose: >
  Take L3 Kāla from "planning complete (13 briefs K0→K6 + templates/weights ratified + closeout)" to "fully
  built, verified, committed, merged, data-generated, sealed — autonomously". Two parts: (A) the
  PRE-IMPLEMENTATION closeout (the gate before kickoff); (B) the AUTONOMOUS EXECUTION (the K0→K6 wave queue,
  the hard internal gates, the swarm roles, the seal).
governing_framework (reuse — do NOT reinvent):
  - 00_ARCHITECTURE/AUTONOMY_RESILIENCE_PATTERN_v1_0.md   # 3-tier escalation; only catastrophic-budget reaches the native
  - 00_ARCHITECTURE/BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md # the role roster
  - 00_ARCHITECTURE/BUILD_GUARANTOR_AUTONOMOUS_MODE_v1_0.md
  - 00_ARCHITECTURE/CONDUCTOR/ (the proven L0/L1/L2 kickoff + log templates)
inputs (all authored + ratified before kickoff):
  - 13 briefs: 00_ARCHITECTURE/briefs/CLAUDECODE_BRIEF_L3_*.md (K0 + 12 ka_*)
  - L3_KALA_PRE_IMPL_CLOSEOUT_v1_0.md (this plan's PART A in detail)
  - L3_KALA_ACTIVATION_TEMPLATES_AND_WEIGHTS_v1_0.md (status RATIFIED — the pre-approved I-7/I-15/I-16 inputs)
  - L3_KALA_CAMPAIGN_PLAN_v0_10.md (the governing design)
native_decisions:
  - "Fully autonomous: authoring→build→runtime→data-gen→commit→merge→push→seal, NO synchronous human gate."
  - "The I-7/I-15/I-16 native-ratify gates are PRE-SATISFIED (templates/weights RATIFIED) — the run does NOT halt for them."
  - "The ka_sangam convergence SPINE-FIRST internal gate is SWARM-ENFORCED HARD; K4-kalasutra + K5/K6 blocked until it verifies."
  - "Seal is AUTONOMOUS + AI-ASSESSED (multi-model consensus, logged to Smṛti, native reviews retrospectively)."
---

# L3 Kāla — Autonomous Execution Plan v1.0

## PART A — PRE-IMPLEMENTATION CLOSEOUT (settle BEFORE the Conductor kicks off)
The full detail + evidence is in `L3_KALA_PRE_IMPL_CLOSEOUT_v1_0.md §F` (the gate table). Summary — the
build launches only when ALL of these are green:

**A1 — Decisions + judgments (✅ DONE):** D-Q4 (embeddings = known-gap), D-Q7 (coarse-to-fine ratified),
D7 (templates + weights RATIFIED — the pre-approved inputs). The three native-ratify gates are pre-satisfied.

**A2 — Drift corrections (✅ done in-brief; one plan edit pending):** DR1 (7 daśā systems, Nārāyaṇa absent,
KP = sub-level — corrected in `ka_dasha_kala` brief), DR2 (`chart_dashas` level-4 Sookshma, not
`ganita_dashas` level-3 — corrected in brief), DR3 (TRUE_NODE — code already consistent). Pending: a
plan-maintenance text edit to §5.6/§5.7.4 (anti-drift; non-blocking for the build).

**A3 — Swarm-safety (2 fixed, 2 for the queue):** CS3 (DAG contradiction — FIXED), CS4 (service-asset id —
NORMALIZED), CS1 (serialize `asset_registry_seed.ts` per wave — ENCODED in the session_queue), CS2
(pre-allocate the 8 migration numbers — the Conductor does this at launch, BEFORE fan-out).

**A4 — Operator / data-plane gates (HARD; NOT Cowork-executable):**
- **OP1 — reconcile the 4 temporal branches (Q5)** — a HARD pre-kickoff gate. K2 (`ka_gochara`) builds on
  the consolidated transit/panchanga source; consolidate the panchanga branches first, then transit. If not
  settled, K2 forks the mess.
- **OP2 — commit the swarm inputs to a clean branch off `origin/main`** (briefs + plans + templates + this
  plan are currently uncommitted). Normalize the briefs dir case (`BRIEFS/` is on-disk truth).
- **OP3 — prod == main verification** (L2 migrations applied on prod; `/api/cockpit/stats` confirms live state).
- **OP4 — prod residual checks** (real Vertex vectors in `bodha_signal_embeddings`; the 4 L3-fill hooks NULL in prod).

**A5 — Conductor inputs (Cowork-authored):** this plan; `session_queue.yaml`; `KICKOFF_L3_KALA_AUTONOMOUS.md`;
the Smṛti dir + halt log; reconcile vs. the existing `RED_TEAM_L3_v1_0.md`.

---

## PART B — THE AUTONOMOUS EXECUTION (the Conductor run)

### B0 — Framework (reuse, do NOT reinvent)
The Sūtradhāra Conductor walks `00_ARCHITECTURE/CONDUCTOR/l3-kala/session_queue.yaml`, spawns
BUILD_GUARANTOR_SWARM_CHARTER roles, runs the gates, and operates under AUTONOMY_RESILIENCE (Tier-1 auto /
Tier-2 decide+log / Tier-3 catastrophic-budget async-notify only). Vimarśaka adversarial-audits every merge;
the deep-fix ladder handles failures; CONN_RESILIENCE checkpoint+resume defends against context decay.
**Model policy:** Gemini / DeepSeek (Anthropic banned unless the native asks). **Frozen-orchestrator
contract:** `@register` / `WriterBase`, never commit `ctx.db_conn`, never write `asset_throughput`.
**L3-new:** K0 introduces a SERVICE asset type — writers may be service-shaped (on-demand compute, no row
store, a self-testing `run(ctx)`); the contract still holds (see the K0 brief §4).

### B1 — THE WAVE QUEUE (K0→K6, with the hard internal gate)
L3 is NOT fully parallel — it has a load-bearing spine anchored on the service-type gate and the convergence
core. The dependency DAG (from the briefs' swarm_coordination headers, collision-audited 2026-06-21):

```
K0  k0_service_asset_type — the service-asset KIND + service-shaped WriterBase conformance + cockpit
    recognition. PROD-VERIFY the type resolves. ★ ALL K1 services BLOCKED until this lands (runs ALONE). ★
 │
K1  SERVICES (parallel — disjoint files): ka_graha_sancara · ka_dasha_kala · ka_muhurta_seva
    (ka_graha_sancara wraps the M3 ephemeris + cache; ka_dasha_kala reads chart_dashas level-4, 7 systems;
     ka_muhurta_seva is live by (date,location), demotes the fenced cache).
 │
K2  ka_gochara — BUILD pipeline/transit_search from the PHASE_4D spec (the UNBUILT HEART; TRUE_NODE;
    coarse-to-fine long-horizon; subsumes ka_transit_almanac; fixes the crashing router).
 │
K3  ka_yojaka — THE ACTIVATION BRIDGE (the crux). Uses the RATIFIED I-15 templates + I-7 weights
    (pre-approved — NO halt). Classifier + class→template binder; references L2 signal_id, zero L2 writes.
 │
K4  ka_sangam — THE CONVERGENCE CORE (Mode A+B + the rigor stratum; uses RATIFIED I-16 form + weights).
    ★ HARD SPINE-FIRST GATE: prove ONE signal end-to-end (classify→Mode A+B→rigor→ranked window→anti-drift)
      BEFORE anything downstream. Failure → deep-fix ladder, NOT the native. ★
    THEN ka_kalasutra — the activation artifact (fills L2's NULL hooks via the artifact; preserves the id
    5 downstream assets depend on). ★ ka_sangam MUST finish before ka_kalasutra within K4. ★
 │
K5  ka_vighnakara (the DANGER engine — inverse search reuse of the ka_sangam spine) THEN
    ka_kala_darshana (the lifetime CATALOG — reads danger windows for collision detection, so it runs
    AFTER ka_vighnakara, not parallel — CS3 fix).
 │
K6  SERVE-TIME PRODUCTS + L5 HOOK (parallel — disjoint): ka_tulana (prioritization, RATIFIED I-11 weights) ·
    ka_jivana_parva (daśā macro-narrative) · ka_bhavishya_lekha (prediction-record emitter → L5 mi_bhavisya;
    must NOT write the L5 tables).
 │
SEAL (autonomous, AI-assessed): the COMPUTATIONAL eval gate (reproduce known past activations — §5.4;
    predictive calibration DEFERRED to L4/L5) → promote ka_* DRAFT→CURRENT → author L3_KALA_CLOSE (with the
    L4 Phala onboarding contract) → update CURRENT_STATE + SESSION_LOG → merge to main + push. Vimarśaka final audit.
```

### B2 — The L3-SPECIFIC swarm additions (fold into the charter for this run)
- **Service-asset-type verifier (K0):** a gate prior storage-swarms lacked — confirms the service shape
  (on-demand, no stored rows where service-typed, the self-test path) is recognized end-to-end before K1.
- **The ka_sangam SPINE-FIRST gate (K4):** the Conductor MUST NOT dispatch ka_kalasutra or any K5/K6 consumer
  until the single-signal convergence proof passes. Encode as a queue dependency + a gate verdict.
- **Activation-bridge integrity (K3):** verify ka_yojaka's bound predicates reference REAL L2 signal_ids +
  L1 fact_ids (no fabricated triggers) — the L1/L2-authority rule extended to the temporal bridge.
- **transit_search BUILD verifier (K2):** confirm the heart is genuinely built (not the old stub) via a
  deterministic transit re-derivation — internal-consistency only (NO JH-parity, plan §N.4).
- **Pre-approved-input enforcement:** the RATIFIED templates/weights are READ-ONLY. Any swarm impulse to
  "re-pick a weight/template" is a Tier-2 STUB+log, NEVER a mid-run native halt (canonical-or-floor rule).
- **Vimarśaka extended to temporal claims:** adversarial post-merge reads check time-indexed/probabilistic
  outputs (a window's rarity/confidence resolve; anti-drift holds), not just data-row ACs.

### B3 — Commit / merge / push cadence (CI-CD, autonomous)
- **Per-asset:** Śilpī commits as ACs land; Nirīkṣaka + the temporal verifier verify; Vimarśaka audits;
  MERGE at the wave-gate pass (canary→promote); push; CI-green is a gate.
- **Per-wave gate** = a clean merge point to main; push at every merge; deploy.yml runs per merge.
- **`asset_registry_seed.ts` (CS1):** within each multi-agent wave (K1/K5/K6), seed-file edits are
  SERIALIZED — a single post-wave seed-reconciliation step appends that wave's rows in one commit. No
  intra-wave concurrent edits to the seed.
- **Migration numbers (CS2):** the Conductor pre-allocates the contiguous block (8 numbers) in DAG order at
  launch; agents use their pre-assigned number, never resolve `<next>` themselves.
- **Frozen-orchestrator rule:** writers conform; contract-change pressure → Tier-2 STUB+log or deep-fix, never a native halt.

### B4 — The ONLY native-input event
Per AUTONOMY_RESILIENCE Tier-3: the catastrophic-runaway budget ceiling only — async, resumable. Nothing else
pauses (the ratify gates are pre-satisfied). The native reviews the SEALED layer retrospectively (Smṛti
digests + L3_KALA_CLOSE + the Vimarśaka audits).

---

## §C — RISK FLAGS (honest, for the autonomous run)
- **K2 ka_gochara is the BUILD-risk peak** — transit_search was never built + the adapter is a stub; the
  swarm builds the pipeline from the PHASE_4D spec. *Mitigation:* deterministic re-derivation + generous
  deep-fix budget + the TRUE_NODE/coarse-to-fine corrections already baked into the brief.
- **K3 ka_yojaka is the DESIGN-risk peak** — the activation bridge is the hardest mapping; bad activations
  poison every downstream product. *Mitigation:* the fact_id-resolution gate + Vimarśaka-temporal audit +
  the RATIFIED templates (no improvised rules).
- **The ka_sangam spine gate failing repeatedly** correctly BLOCKS ka_kalasutra + K5/K6 — do not build on a
  broken convergence root. ka_sangam gets the deepest fix-budget. *Acceptable behavior.*
- **OP1 (the 4-branch reconciliation)** — if not fully settled pre-kickoff, K2 risks building on a stale
  source. This is a HARD PART-A gate, not a build-time discovery.
- **Pre-approved-input drift** — if a brief's logic implies different weights than the RATIFIED set, the
  swarm STUBs+logs, never silently re-picks. Flag any such tension for a versioned re-ratification.
- **The L3 product is probabilistic + time-indexed** — the Ethical Framework (calibrated, auditable, not
  fortune-telling) binds the serve layer; the seal's eval gate checks computational correctness only
  (predictive calibration is L5's, not a blocker here).

---
*End of L3_KALA_AUTONOMOUS_EXECUTION_PLAN v1.0. PART A = the closeout gate (decisions ✅, drifts ✅, swarm-safety
2-fixed/2-queued, operator OP1–OP4 pending). PART B = the autonomous K0→K6 run: K0 service-type → K1 services →
K2 ka_gochara (build the heart) → K3 ka_yojaka (bridge, pre-approved templates) → K4 ka_sangam spine-gate THEN
ka_kalasutra → K5 vighnakara THEN kala_darshana → K6 serve-time products + L5 hook → AI-assessed seal. The
I-7/I-15/I-16 gates are PRE-SATISFIED so nothing halts mid-build; only the catastrophic-budget ceiling reaches
the native.*
