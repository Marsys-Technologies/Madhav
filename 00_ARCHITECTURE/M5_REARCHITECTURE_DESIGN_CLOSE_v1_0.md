---
artifact: M5_REARCHITECTURE_DESIGN_CLOSE_v1_0.md
canonical_id: M5_REARCHITECTURE_DESIGN_CLOSE
version: 1.0
status: SUPERSEDED 2026-06-02 by MARSYS_MASTER_ARCHITECTURE_v2_0.md (v1 design baseline; v2 re-audit folds in two reviews + four new assets + the robustness spine). Retained as the v1 record.
macro_phase: M5
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-02
purpose: >
  Logs the M5 re-architecture design phase into the record and CLOSES all the design briefs produced.
  It is the sealing artifact for the clean-slate redesign of the MARSYS-JIS instrument into a six-layer
  stack (L0–L5). The design is now the agreed baseline; remaining per-layer open decisions carry into
  the build/execution phase as per-asset execution briefs.
---

# M5 — Re-Architecture Design Close

## §A — What this closes

A full, native-led redesign of the instrument (Cowork planning), ending the design phase and sealing the
baseline. The system is recast from the legacy stack into a clean six-layer architecture, on a clean
slate (legacy teardown), deployed on cost-optimized GCP.

## §B — The new architecture (L0 → L5)

- **L0 — Foundation** (global, build-once): Ephemeris (tropical-at-source, DE441, 1800–2200, geocentric +
  topocentric-on-read, ~14 bodies), Reference Library, Classical Texts (full canon, Sanskrit+translation),
  Text Index (hybrid retrieval), Ontology, Rule Base, Concordance, Daily Almanac (location-dynamic,
  Drik-Panchang superset).
- **L1 — Chart Facts** (per chart × user-selected ayanamshas): PyJHora computes the COMPLETE deterministic
  catalog (§E★ — module-traceable); JSONL artifact → **typed category-organized Fact Store** + Forensic MD.
  PyJHora invoked ONLY here. Dashas to **Sukshma** depth. On-demand temporal/relational capabilities.
- **L2 — Chart Intelligence** (signal-centric): rule-generated **signals** (grounded, scored, cited) +
  **signal graph** + lenses (domain/resonance/concordance/contradiction) + temporal-activation + negative-
  space + **salience** + embeddings. Tabular + graph + vector. Pre-digested intelligence for the LLM.
- **L3 — Temporal Fabric** (deterministic): dasha×transit alignment, convergence timeline (measured),
  obstruction overlaps, period snapshot. "Alignment exists."
- **L4 — Predictive Engine** (probabilistic, learned): a calibrated **ensemble** of classical predictors →
  **Event Anchors** (window + theme + confidence + falsifier), mitigation, birth-time rectification.
- **L5 — Learning** (held-out): pure-event **LEL** (isolated) + the derived Event Chart-State Index;
  scoring (Brier/calibration/timing/per-technique/per-ayanamsha) → recalibration via the **learning
  multiplier**; cross-corpus research (rule validation, discovery). LEL never feeds generation.

## §C — Key decisions logged (M5)

1. **Clean-slate teardown** — wipe all legacy data, build code, tools, FORENSIC v8.0; keep the serve
   shells (provider/agentic loop, MCP shell, portal, auth) + LEL. (`LEGACY_TEARDOWN_KILL_LIST_v1_0`,
   `CLAUDECODE_BRIEF_LEGACY_TEARDOWN_v1_0`.)
2. **Infra: stay on GCP, cost-optimized scale-to-zero** (Railway evaluated + rejected on cost).
   (`INFRASTRUCTURE_INVENTORY_v1_0`.)
3. **PyJHora is the single deterministic engine, invoked only in L1**; compute its full single-chart output;
   relational/dynamic functions are L1-owned on-demand capabilities; no JH-parity oracle; internal-
   consistency verification only.
4. **L1 storage = typed category schema** (not key-value), relationships as first-class rows, JSONL as
   canonical artifact + L2 build input, no RAG over facts, dashas to SD depth. (`LAYER_1_STORAGE_STRATEGY`.)
5. **L2 = Chart Intelligence**, signal-centric, three representations; vectorize processed signals (never
   facts); CDLM/RM are views over the signal graph. (`LAYER_2_CHART_INTELLIGENCE_DESIGN`.)
6. **Split old L3 into L3 (temporal, deterministic) + L4 (predictive, learned).**
7. **L4 = calibrated ensemble** of classical + cosmological predictors with falsifiable, probabilistic output.
8. **L5 learning via a single `learning_multiplier`** (default 1.0, two-level corpus×chart, shrinkage,
   bounded) on every learnable unit-class — classical layer modulated, never overwritten.
9. **LEL = pure-event log, isolated**; calculations live in the separate derived Event Chart-State Index;
   two intake paths (portal/MCP + one-time v1.2 migration). (`LEL_SCHEMA_AND_INTAKE_v1_0` §0 tracked migration.)
10. **Tooling standard:** one registry, two transports (MCP + internal), capability-over-primitives,
    provenance envelope; one tool per asset/layer.
11. **Build-guarantor swarm** governs build/deploy/runtime. (`BUILD_GUARANTOR_SWARM_CHARTER_v1_0`.)

## §D — Design briefs — CLOSED

| Brief | Status |
|---|---|
| `BUILD_GUARANTOR_SWARM_CHARTER_v1_0` | CURRENT (charter) |
| `BUILD_PROGRAM_TRACKER_v1_0` | LIVING (tracker) |
| `INFRASTRUCTURE_INVENTORY_v1_0` | LIVING (infra + cost) |
| `ASSET_RECONCILIATION_v1_0` | CLOSED |
| `FACT_ENGINE_A1_SCOPE_ANALYSIS_v1_0` | CLOSED |
| `LEGACY_TEARDOWN_KILL_LIST_v1_0` + `CLAUDECODE_BRIEF_LEGACY_TEARDOWN_v1_0` | READY (execution-gated) |
| `LAYER_0_FOUNDATION_DESIGN_v1_0` + `LAYER_0_PLAN_BRIEF_v1_0` | CLOSED |
| `LAYER_1_CHART_FACTS_DESIGN_v1_0` (scope-locked) + `LAYER_1_STORAGE_STRATEGY_v1_0` | CLOSED |
| `LAYER_2_CHART_INTELLIGENCE_DESIGN_v1_0` | CLOSED |
| `LAYER_3_TEMPORAL_FABRIC_DESIGN_v1_0` | CLOSED |
| `LAYER_4_PREDICTIVE_ENGINE_DESIGN_v1_0` | CLOSED |
| `LAYER_5_LEARNING_DESIGN_v1_0` + `LEL_SCHEMA_AND_INTAKE_v1_0` | CLOSED |
| `LAYER_3_TIME_AND_PREDICTION_DESIGN_v1_0` | SUPERSEDED (split) |
| `LAYER_2_SYNTHESIS_DESIGN_v1_0` | SUPERSEDED (reimagined) |

## §E — Open items carried into the BUILD phase

Per-layer open decisions (each layer's §K/§J/§I) are deferred to **per-asset execution briefs**, not
re-opened here: L0 (corpus final list, embedding model, ontology depth, rule extraction), L1 (JSONL/
schema field-lock, tool surface), L2 (domain taxonomy, salience initial weights, edge thresholds), L3
(time resolution, intensity formula), L4 (anchor threshold, ensemble combination, falsifier model), L5
(calibration method, significance bars, multiplier bounds, consent/ethics for cross-corpus).
**Tracked one-time action:** the v1.2 → pure-event LEL migration (`LEL_SCHEMA_AND_INTAKE §0`).

## §F — Next phase

The build phase: execute the **legacy teardown** (human-gated), stand up the clean GCP baseline, then
build L0 → L5 per the Build-Guarantor Swarm Charter (Nirīkṣaka audit → Racayitā briefs → build → review →
deploy → runtime verify), each asset shipping with its tool, contract, and acceptance gate.

---

*End of M5_REARCHITECTURE_DESIGN_CLOSE v1.0 — design baseline SEALED 2026-06-02. The six-layer
architecture (L0–L5) is the agreed baseline; the build phase begins from here.*
