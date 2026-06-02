---
artifact: CONTRACT_REGISTRY_SEED_BRIEF_v1_0.md
canonical_id: CONTRACT_REGISTRY_SEED_BRIEF
version: 1.0
status: DRAFT (handoff brief — Cowork; hands the design baseline to the Build-Guarantor Swarm)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-02
authored_for: the Build-Guarantor Swarm (Nirīkṣaka first pass) + native approval
inputs_authoritative:
  - MARSYS_MASTER_ARCHITECTURE_v2_0.md (v2.1) — WHAT is built (L0–L5 + 4 new assets + robustness spine)
  - BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0.md — the product/build experience + the tool taxonomy
  - BRAHMA_BUILD_UX_SPEC_v1_0.md — the implementation-ready UI/UX
inputs_supporting:
  - LAYER_0..LAYER_5 design docs (per-layer detail; now Brahma-bannered)
  - LAYER_1_STORAGE_STRATEGY_v1_0, LEL_SCHEMA_AND_INTAKE_v1_0, INFRASTRUCTURE_INVENTORY_v1_0
  - ASSET_RECONCILIATION_v1_0, FACT_ENGINE_A1_SCOPE_ANALYSIS_v1_0 (merge map + superset requirement)
governed_by:
  - BUILD_GUARANTOR_SWARM_CHARTER_v1_0.md (the swarm + the Contract Registry schema §F)
purpose: >
  Hand the three canonical design documents to the Build-Guarantor Swarm as the authoritative inputs for
  Nirīkṣaka's first full pass, which SEEDS the Asset Contract Registry. Specifies the unit set to register,
  the v2 additions each entry must carry (the asset's tool(s), volume floor, external Brahma name, and the
  parallel build-the-tool-with-the-asset code/deploy/runtime contract), and the swarm's first concrete actions.
---

# Contract Registry Seed Brief — Project Brahma

## §A — What this hands off

The design phase is complete. Three documents are the authoritative target the swarm builds against:
**MARSYS_MASTER_ARCHITECTURE v2.1** (what), **BUILD_WORKFLOW_AND_TOOLING_DESIGN v2.0** (the build experience +
tool taxonomy), **BRAHMA_BUILD_UX_SPEC v1.0** (the UI/UX). This brief tells the Build-Guarantor Swarm how to
turn that target into the **Asset Contract Registry** (charter §F) — the single plan the whole swarm reads and
writes against.

## §B — Do these first (before any unit work)

1. **Re-base the charter + tracker off the legacy DAG.** `BUILD_GUARANTOR_SWARM_CHARTER §C/§K` and
   `BUILD_PROGRAM_TRACKER` still reference the legacy `A1–A22 + META` DAG and the "reuse what's built" rule.
   Re-base both onto **L0–L5 + the four new assets** (Remediation, Muhurta, Relational, Spatial). Master Arch
   §E names this the first build-phase action.
2. **Stand the verification spine up** (Master Arch C1/C2): the **astronomical ground-truth harness** (PyJHora
   vs JPL/Swiss Ephemeris — astronomy, *not* a JH-parity oracle) and the **engine-version migration policy**.
3. **Run Nirīkṣaka's first pass** against the three inputs to produce the per-unit current-state map (built /
   partial / stub / missing), which — minus the contract target — yields the gap that seeds Racayitā's briefs.

## §C — The unit set to register (one Contract Registry entry each)

**Workflow-UI units** (from BUILD_WORKFLOW v2 §C + UX spec §1):
`form.birth_data` (+ ayanamsha selector) · `account.create` · `account.edit` (auto-cascade rebuild) ·
`account.delete` (hard wipeout) · `dashboard.roster` · `buildpage.layer_tower` · `buildpage.inspector` ·
`buildpage.controls` · `buildpage.telemetry` · `consult.progressive` · `admin.brahmagyan_foundation` (one-time
global + infra).

**Asset units** (from Master Arch §B + the per-layer docs; external Brahma name in parentheses):
- **Brahmagyan / L0** (global, build-once): ephemeris · reference library · classical texts · text index ·
  ontology · rule base · concordance · daily almanac · **remedy corpus (new)**.
- **Gaṇita / L1**: the engine (enumerated **superset of FORENSIC v8.0**, per FACT_ENGINE_A1_SCOPE_ANALYSIS) →
  typed Fact Store + forensic render; ayanamsha-invariant/dependent split; location-parameterized recompute.
- **Bodha / L2**: signals (MSR) · signal graph (CGM) · cross-domain links (CDLM) · resonance (RM) · lenses ·
  activation · negative-space · salience · embeddings · **Remediation (new)** · **Relational/composite (new)**.
- **Kāla / L3**: dasha×transit alignment · convergence timeline · obstruction overlaps · period snapshot ·
  **Spatial activation index (new)**.
- **Phala / L4**: calibrated ensemble · event anchors · mitigation map · rectification · **Muhurta/electional
  (new)**.
- **Mīmāṃsā / L5**: pure-event LEL · event chart-state index · scoring · learning multiplier · cross-corpus
  research (BigQuery/Parquet).

## §D — What each entry must carry (charter §F schema + the v2 additions)

Use the charter §F schema, with these **mandatory v2 additions** on every asset entry:

- `external_name:` the Brahma Sanskrit / English display name (governs all user-facing copy).
- `tools:` the asset's retrieval tool(s) — **built in the same arc as the asset, not stubbed.** Each tool
  carries: `tool_id`, capability description, typed input/output **schema**, an **MCP resource** (the asset's
  schema + data dictionary), the **provenance-envelope** contract, `channels:[mcp, portal]`, and `auth_tier`.
  Grain = the three-tier taxonomy (per-asset primitives close to the source + a few composite capability tools
  + meta/ops) — **not** one-tool-per-layer (Bodha is the worked counter-example: MSR/CGM/CDLM/RM each get
  their own source-close tool).
- `volume_floor:` the minimum expected row/coverage count **as a function of the ayanamsha set**, from the
  FORENSIC coverage benchmark × the per-ayanamsha multiplier. Below floor → the runtime gate returns **amber**.
- `code_contract:` now spans **writer + tool(s) + schema + resource + tests**.
- `deploy_contract:` deploy to **both** `amjis-web` (portal) **and** `amjis-mcp` (MCP) — both must be live.
- `runtime_contract:` the asset's data **and** a live tool call against that freshly-generated data must pass
  (Sambandha dependency-completeness · Pramāṇa integrity · Darpaṇa render-coverage · volume floor · tool test).
- `acceptance_gate:` the shell/test command proving the unit per gate.

A layer is "verified/lit" only when **all its assets and their tools** pass. Continuity is dependency-gated
(`depends_on` green) — Gaṇita → Bodha → Kāla → Phala, with Mīmāṃsā reading Phala (pre-outcome) + the isolated
LEL.

## §E — Standing constraints the swarm inherits (unchanged)

PR-to-main / prod deploy / prod DB ops / secret rotation / flag flips are **human-gated**; Nirīkṣaka +
Racayitā are advisory. **No Anthropic models in production.** **No JH-parity oracle anywhere** (astronomical
ground-truth check is allowed). **Cowork plans; Claude Code (Antigravity) executes** — including the front-end,
built with Claude Code's installed front-end design plugins against the UX spec. **Only computed facts** in
built data. FORENSIC v8.0 is **archived as the coverage benchmark**, not wiped. Legacy teardown is human-gated.

## §F — Open items the swarm carries into per-asset briefs

Rule-extraction pilot + confidence rubric (gate before the full canon); embedding-model spike; classical-text
licensing (hard-blocker risk); the per-asset **volume floors** (author from FORENSIC × ayanamsha multiplier);
L2 domain taxonomy + salience initial weights; L3 time resolution + intensity formula; L4 anchor threshold +
ensemble combination + falsifier model + the hybrid precompute/lazy split (native to confirm); L5 calibration
method + significance bars + multiplier bounds + cross-corpus consent/acquisition; the relational consent
model; the spatial module scope. **Tracked one-time action:** the LEL v1.2 → pure-event migration
(`LEL_SCHEMA_AND_INTAKE §0`).

## §G — Governance follow-ups

Register `MARSYS_MASTER_ARCHITECTURE` (v2.1), `BUILD_WORKFLOW_AND_TOOLING_DESIGN` (v2.0), `BRAHMA_BUILD_UX_SPEC`
(v1.0), and `CONTRACT_REGISTRY_SEED_BRIEF` (v1.0) in `CAPABILITY_MANIFEST.json`; run `drift_detector.py` +
`schema_validator.py` to confirm no registry divergence; update `CURRENT_STATE` to point at the build phase.

---

*End of CONTRACT_REGISTRY_SEED_BRIEF v1.0 — Project Brahma — DRAFT handoff, 2026-06-02. The three design docs
are the authoritative target; Nirīkṣaka's first pass seeds the Asset Contract Registry from them, and the build
phase proceeds under the (re-based) Build-Guarantor Swarm Charter.*
