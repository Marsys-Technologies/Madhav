---
artifact: BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md
canonical_id: BUILD_GUARANTOR_SWARM_CHARTER
version: 1.0
status: CURRENT
authored_by: Claude (Cowork) 2026-06-02
authored_for: native (Abhisek Mohanty)
purpose: >
  Standing charter for the agentic swarm that guarantees the chart-build workflow —
  from "new client" through birth-data entry, save/build/consume, and the full data-asset
  DAG — is correctly CODED, correctly DEPLOYED, and correctly GENERATED AT RUNTIME, against
  one explicit per-unit contract. This is a governing artifact: it is read at the open of
  every session that builds, audits, deploys, or verifies any part of the chart-build
  workflow, and it is the authority for how such work is organised, dispatched, and gated.
read_in_combination_with:
  - CLAUDE.md (project root — mission + mandatory reading)
  - 00_ARCHITECTURE/CURRENT_STATE_v1_0.md (you-are-here)
  - 00_ARCHITECTURE/GOVERNANCE_INTEGRITY_PROTOCOL_v1_0.md (session open/close, gates)
  - 00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md (the orchestrator this charter enhances)
  - 00_ARCHITECTURE/PARIKSHA/PARIKSHA_MASTER_PLAN_v1_0.md (the runtime QA swarm this charter extends)
  - 00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json (logical asset registry by layer)
  - platform/migrations/158_build_dependencies.sql (the 28-unit asset DAG + dependencies)
  - platform/python-sidecar/pipeline/build_chart.py (DAG_ORDER — what is actually wired)
supersedes: none (new artifact)
changelog:
  - v1.0 (2026-06-02): Initial charter. Formalises the v2 build-workflow guarantor swarm:
    Gate 0 (Assess & Author) + three gates (Code / Deploy / Runtime), 12 roles, the Asset
    Contract Registry schema, orchestration loop, per-session usage protocol, and standing
    constraints. Authored in Cowork from the 2026-06-02 design conversation.
---

# Build-Workflow Guarantor Swarm — Charter v1.0

## §A — Mission

The MARSYS-JIS chart-build workflow lets a user create a client, enter the essential
astrological data, and then build that client's data assets — mostly deterministic
mathematical derivations — layer by layer (L1 → L2.5 → L3 → …), where each asset can only
be built once its dependency assets exist. The more assets that are correctly built, the
richer the astrological insight the instrument can produce.

This swarm exists to make that workflow **watertight**. It is an end-to-end guarantor that
checks reality against an explicit plan across three gates:

1. **CODE** — what gets written matches the defined expectation for each unit.
2. **DEPLOY** — the code is actually live and correct in production.
3. **RUNTIME** — the data a chart build produces aligns with the plan's definition of what
   each asset should compute.

Ahead of those three sits **Gate 0 — Assess & Author**: a standing pair that audits the
current state of every unit and drafts the work needed to close the gap to the contract —
full authoring for a from-scratch unit, a targeted delta for an existing one.

The swarm does not replace the existing spine. It **enhances the Conductor** (orchestration)
and **extends Pariksha** (runtime verification), and adds the assess/author front and the
deploy gate that the spine lacks today.

## §B — The workflow this charter guards

The swarm's scope is the **entire** workflow, not only the asset DAG. Every gate spans all
four stages:

1. **New Client** — entry from the roster/dashboard (`/clients/new`).
2. **Birth-data form** — essential client + birth inputs (name, email, birth date/time/place,
   coordinates; ayanamsha selection is a known gap). `POST /api/clients` creates the chart,
   the client user, and seeds the coarse pyramid-layer rows.
3. **Save · Build · Consume** — the three actions: save (chart persists, resumable from the
   roster), build (construct the data assets), consume (chat against whatever is built).
4. **Asset DAG build** — the dependency-gated construction of the data assets (§C), with live
   visual progress in the build cockpit.

Each of these is a *workflow unit* with its own contract entry (§F). The build cockpit's
progress model and the asset DAG are currently at different granularities; aligning them is
in scope.

## §C — The asset set the swarm operates over

The authoritative asset sources are, in precedence order:
`platform/migrations/158_build_dependencies.sql` (the dependency DAG),
`00_ARCHITECTURE/VALIDATED_ASSET_REGISTRY_v1_0.json` (logical assets by layer), and
`platform/python-sidecar/pipeline/build_chart.py` `DAG_ORDER` (what is actually wired).
**This charter references those; it does not duplicate them** (B.8 no-duplication discipline).

The DAG declares **28 units** (sort_order 1–28). The native's "A0–A27" recollection maps to
these 28. Summary map:

| Units | Layer | What | Status |
|---|---|---|---|
| A1 | engine (L1 boundary) | natal engine output (positions, houses, vargas, dashas, panchanga, sensitive points) per 5 ayanamshas | wired |
| A2–A9 | L1 facts | A2 forensic render · A3 chart_facts · A4 panchanga · A5 sensitive points · A6 vargas · A7 dashas · A8 T1 structural (shadbala/ashtakavarga) · A9 sade-sati | wired (some writers historically stubbed — Nirīkṣaka to re-confirm) |
| A10–A14 | L2.5 synthesis | A10 MSR · A11 CDLM · A12 CGM · A13 RM · A14 UCN digest | wired |
| A15–A22 | L3 | timeline / phase-anchors / sarvatobhadra / vedha / bhrigu-bindu / year-lords / graha-aspects-lifetime / varsha-digest (codenames differ between migration sets — see note) | **built (writer + table + tests), NOT wired** |
| META_α–ζ | L3 synthesis | chart-lattice · pattern-catalog · divergence-ledger · negative-space · derivation-graph · unified-lattice view (+ BRIDGE, UTEE backfill) | **built (writer + table + tests), NOT wired** |

Two facts the program targets:

- **Wiring gap (the dominant gap).** A15–A22 + META are *built* — writer modules under
  `platform/python-sidecar/pipeline/` (and `/writers/`), DB tables from migrations 140–153, and
  test files all exist — but they are NOT wired into `build_chart.py` `DAG_ORDER` or
  `WRITER_REGISTRY`, and no orchestrator invokes their `seed_*()` / `write_*()` entry points.
  They run today only as standalone reference implementations. The watertight target is therefore
  predominantly **wiring + un-stubbing + verification**, not green-field construction.
- **Naming/mapping drift.** Migration 158's `build_dependencies` labels do not match the
  migration 140–153 writers/tables (e.g. A17 = "Yantra/derivation-graph" in 158 but its writer is
  `sarvatobhadra_chakra.py`; A21 = "Drishti-Patrika/lattice" in 158 but its writer is
  `graha_aspects_writer.py`). The authoritative per-asset identity must be reconciled in
  Nirīkṣaka's first pass against the per-asset spec/brief docs (`00_ARCHITECTURE/A*_SPEC_v1_0.md`).
- **Depth-starvation gap.** The engine's `compute_chart()` returns ~6 content domains and does
  not surface depth (shadbala, ashtakavarga, KP, Tajaka, yogas), so several synthesis writers
  stub or recompute. This is the root cause of the forensic-renderer-at-38%-of-v8.0 finding.
- **Gating gap.** Dependency order is implicit (hard-coded list), not enforced; the cascade /
  resume logic in `dispatcher.py` is never called; a missing dependency yields a
  `"…_not_computed"` sentinel rather than a block.

**Reconciling the exact catalog — brief numbering vs DB DAG vs wired DAG, and the precise
per-unit current state — is Nirīkṣaka's first pass (§E.1) and seeds the Contract Registry (§F).**

## §D — The gate model

```
GATE 0  ASSESS & AUTHOR   →  is current state known, and is the work drafted?
GATE 1  CODE              →  is the unit built to its contract?
GATE 2  DEPLOY            →  is it live and correct in production?
GATE 3  RUNTIME           →  does a chart build produce data per the contract?
```

A unit advances only when its current gate passes. Gate results route back to the
orchestrator, which advances or halts (for human approval). The visual topology is the
build-workflow guarantor swarm diagram (v2) from the 2026-06-02 design conversation.

## §E — Roles

Each role lists: **mandate · inputs · outputs · status** (exists today vs new) and its
relationship to existing infrastructure. Sanskrit codenames are mnemonic, not load-bearing.

### Gate 0 — Assess & Author

**E.1 · Nirīkṣaka — current-state auditor (NEW).**
Mandate: for every workflow unit (§B) and asset (§C), determine what exists vs stub vs
missing, and classify each as *fresh* (needs full authoring) or *existing* (needs a delta).
Inputs: the codebase, DB schema, build wiring, deployed revisions, the asset sources (§C).
Outputs: a per-unit current-state map feeding the Contract Registry. Advisory only.
Lineage: the standing, per-unit, continuous form of `GROUNDING_AUDIT_v1_0` and the
exploration passes that precede every arc. **Its first full run is the data-asset review the
native commissioned; that run seeds §F.**

**E.2 · Racayitā — gap author (NEW).**
Mandate: given the contract (target) minus Nirīkṣaka's audit (current), draft the work to
close the gap — full spec/brief for a fresh unit, a targeted delta brief for an existing one.
Inputs: Contract Registry target + current-state map. Outputs: executable briefs in
`00_ARCHITECTURE/briefs/` (CLAUDECODE_BRIEF format). Advisory only — the human approval gate
is unchanged; Racayitā removes the manual *drafting*, not the judgment. Directly closes the
Conductor's named limitation that brief authoring is fully manual with no scaffolding.

### Orchestration

**E.3 · Sūtradhāra — orchestrator (ENHANCE the Conductor).**
Mandate: read the contract, walk the unit queue, dispatch role-agents per unit, run gates,
halt for human approval, persist state. Inputs: Contract Registry + session queue. Outputs:
gate verdicts, halts, logs. Enhancements over today's Conductor: a watchdog hook (E.11),
PR-level CI gating, contract-aware eligibility, and consumption of the Gate-0 outputs.

### Gate 1 — Code

**E.4 · Śilpī — builders (EXISTS as Conductor sub-agents).**
Mandate: implement code for a unit (UI, API, or engine/writer) to satisfy its contract, in
isolated worktrees, in parallel along independent DAG branches. Inputs: a Racayitā brief.
Outputs: committed code + tests, one `---FINAL_SUMMARY---` per session.

**E.5 · Review Swarm ×5 — multi-lens code review (NEW; the "same diff, many perspectives" model).**
Five parallel reviewers on the same diff, each a single lens:
(a) **contract** — does the change satisfy the unit's contract;
(b) **layer-discipline** — facts/interpretation separation + derivation ledger + whole-chart-read
    (B.1 / B.3 / B.11);
(c) **schema/migration** — DB changes correct, idempotent, reversible;
(d) **tests** — coverage, FORENSIC-grounded assertions, determinism;
(e) **security** — auth, the BUILD_TASK_AUTH_BYPASS class of holes.
Outputs: scored findings; the orchestrator gates on them. Aligns with the off-the-shelf
parallel-review pattern but scoped to MARSYS contracts.

### Gate 2 — Deploy

**E.6 · Pratiṣṭhā — deploy verifier (NEW; the spine's weakest surface today).**
Mandate: confirm a merge actually became correct production state. Checks: migrations applied,
Cloud Run revision live, image SHA matches `main`, env vars/flags correct, post-deploy smoke
green — across `amjis-web`, `amjis-sidecar`, `amjis-mcp`, and the build job. Catches the
build-task 401 and headless-boot classes of "merged but not correctly live." Outputs: a
deploy verdict. Production actions remain human-gated (§J).

### Gate 3 — Runtime (Pariksha, extended)

**E.7 · Drashta — portal walker (EXISTS).** Walks the form, save/build/consume, and the
cockpit via browser automation; reports UI/workflow defects.

**E.8 · Pramāṇa — data-integrity battery (EXISTS).** Verifies a built chart across its
categories: row counts, schema, structural invariants, cross-asset FK, layer-completion gates,
determinism, and FORENSIC consistency. (NOTE: the existing "Cat 7 JH Oracle Parity" /
`native_oracles` naming is jh-parity residue and must be renamed to FORENSIC-consistency per
the standing no-JH-parity constraint — §J.)

**E.9 · Sambandha — dependency-completeness checker (NEW).** Given a chart and the DAG (§C),
asserts that **every asset whose dependencies were satisfied was actually built** — no silent
stubs, no `"…_not_computed"` sentinels passed off as complete. This is the lens the runtime
gate lacks today and the one the dependency-gated build most needs.

**E.10 · Darpaṇa — render-coverage checker (NEW).** Asserts the renderers surface what was
computed: cell-density and domain coverage vs the contract's render spec. Prevents the
forensic-renderer-at-38%-of-v8.0 class of regression from ever shipping silently.

### Cross-cutting

**E.11 · Praharī — watchdog (NEW).** Detects stalled/timed-out sub-agent sessions and triggers
resume; closes the Conductor's "no watchdog" gap.

**E.12 · Smṛti — shared state / memory (NEW).** Maintains the Contract Registry and build-state
as the disk-of-record across worktrees and sessions, and reconciles state-tracking drift
(e.g., queue-vs-halt-log disagreement). Closes the "no cross-session memory" and
state-discrepancy gaps.

## §F — The Asset Contract Registry (the plan)

The single source of truth the whole swarm reads and writes against. One entry per workflow
unit (§B) and per asset (§C). It is produced by Nirīkṣaka's first full pass (the data-asset
review) and maintained thereafter. Proposed per-unit schema:

```yaml
unit_id:                 # A3 | A15 | "form.birth_data" | "action.save" | "cockpit.dependency_graph"
display_name:            # human + Sanskrit codename where applicable
layer:                   # L1 | L2.5 | L3 | L4 | L5 | workflow-ui
depends_on: []           # upstream unit_ids that gate this one
owns:                    # the single domain/output this unit is authoritative for
code_contract:           # what code must exist (writer/renderer/API/component/engine-domain) + file paths
deploy_contract:         # what "correctly live" means (migration ids, revision, env/flags, smoke)
runtime_contract:        # what a correct build produces — expected rows, schema, invariants,
                         #   render cell-density, FORENSIC-consistency assertions
acceptance_gate:         # the shell/test command that proves the unit, per gate
current_state:           # Nirīkṣaka: built | partial | stub | missing  (+ evidence)
build_mode:              # fresh (full authoring) | existing (delta)     ← drives Racayitā
provenance:              # source brief(s), owning session, last audited
```

Discipline: `owns` enforces **one domain, one unit** — the antidote to the historical drift
where L1-forensic content was bolted onto other assets as supplementary sections. No unit
without an `acceptance_gate`. No `runtime_contract` claim without FORENSIC grounding.

## §G — The loop

```
Nirīkṣaka audits current state ─┐
                                 ├─→ Contract Registry (target ⊖ current = gap)
Contract target (from review) ──┘
        │
        ▼
Racayitā drafts work (fresh | delta) ──→ brief
        │
        ▼
Sūtradhāra dispatches ──→ Śilpī builds ──→ Review Swarm ×5  (GATE 1)
                                                │ pass
                                                ▼
                                       Pratiṣṭhā verifies deploy (GATE 2)
                                                │ pass
                                                ▼
                              Drashta · Pramāṇa · Sambandha · Darpaṇa (GATE 3)
                                                │ pass → unit done
                                                ▼ fail → halt for human
        (Praharī watches throughout · Smṛti is the disk-of-record)
```

## §H — Per-session usage protocol (how this is "used every time")

Any session that touches the chart-build workflow:

1. Reads this charter at session open (it is on the CLAUDE.md §C mandatory-reading list).
2. Declares which **units** (§F) are in scope in its `may_touch` / `must_not_touch`.
3. Runs (or consumes the latest) **Nirīkṣaka** audit for those units before authoring or coding.
4. Works only from a **Racayitā** brief approved by the native.
5. Passes its unit's **acceptance_gate** at the relevant gate(s) before claiming progress.
6. Closes via the standard SESSION_CLOSE checklist; **Smṛti**/state is updated atomically.

## §I — Relationship to existing infrastructure

- **Conductor** (`CONDUCTOR_PROMPT_v1_0`) is Sūtradhāra; this charter specifies its enhancements.
- **Pariksha** (`PARIKSHA_MASTER_PLAN_v1_0`) is Gate 3; Drashta + Pramāṇa exist, Sambandha +
  Darpaṇa are added here.
- **Governance validators** (`drift_detector.py`, `schema_validator.py`, session open/close)
  remain the mechanical enforcement layer; gate commands wrap them.
- This charter **adds** Gate 0 (Nirīkṣaka, Racayitā), Gate 2 (Pratiṣṭhā), and the cross-cutting
  Praharī + Smṛti. It changes none of the standing governance protocol.

## §J — Standing constraints binding on the swarm

- **PR-to-main, prod deploy, prod DB ops, secret rotation, flag flips are human-gated.**
  Nirīkṣaka and Racayitā are **advisory**; they never auto-merge or mutate prod.
- **No Anthropic models in any production path.** Default planner Gemini Pro; fallback
  DeepSeek; dev-loop agents are unconstrained.
- **No JH-parity oracle anywhere** — in code, briefs, tests, or fixtures. The Pramāṇa "JH
  Oracle Parity" naming + `native_oracles` files are residue to rename to FORENSIC-consistency.
- **Cowork plans; Antigravity executes.** Charter, contract, and briefs are authored in Cowork;
  Śilpī builders run in Antigravity worktrees.
- **Only computed facts** — no narrative, opinion, or judgement in built data (prime directive).
- **Verification is internal consistency** across the gate categories; no external oracle.

## §K — Decisions

- **First watertight target (CONFIRMED by native 2026-06-02):** the FULL set A1–A22 + META_α–ζ
  (there is no A0), every unit fully un-stubbed, fully coded, and **wired** into the active build
  with true dependency-gating — L1, L2.5, and L3 together. Not a phased "L1→L2.5 first." Because
  A15–A22 + META are already built-not-wired (§C), this is dominated by wiring, un-stubbing the
  A1–A14 stubs, the engine depth-domain fill, and end-to-end verification — not green-field work.
- **Brief review (native-led):** the native will review the per-asset spec/brief docs
  (`00_ARCHITECTURE/A*_SPEC_v1_0.md`, the `CLAUDECODE_BRIEF_M2_*` briefs, and
  `MULTI_AYANAMSHA_BUILD_CLOSE_v1_0.md`) with specific aspects to check; that review feeds the
  Contract Registry (§F) and may amend asset scope/identity.
- Whether the build cockpit's progress model is re-based onto the asset DAG (§B) in this program
  or a later one.

## §L — Registration (keeping this canonical)

- Placement: `00_ARCHITECTURE/` per `ROOT_FILE_POLICY §3` (canonical governance artifact).
- Added to `CLAUDE.md §C` mandatory reading (item 13) and the `§D` snapshot table (same edit).
- Follow-ups for a governance session: register `BUILD_GUARANTOR_SWARM_CHARTER` in
  `CAPABILITY_MANIFEST.json`, then run `drift_detector.py` + `schema_validator.py` to confirm
  no registry divergence.

---

*End of BUILD_GUARANTOR_SWARM_CHARTER v1.0 — authored in Cowork 2026-06-02. Design for native
review; roles and contract schema are proposals until the native confirms and the first
Nirīkṣaka pass populates §F.*
