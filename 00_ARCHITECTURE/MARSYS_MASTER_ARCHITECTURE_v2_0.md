---
artifact: MARSYS_MASTER_ARCHITECTURE_v2_0.md
canonical_id: MARSYS_MASTER_ARCHITECTURE
version: 2.1
project_codename: Brahma
status: CURRENT (authoritative architecture baseline — supersedes the v1 design baseline M5_REARCHITECTURE_DESIGN_CLOSE_v1_0)
authored_by: Claude (Cowork) 2026-06-02
supersedes: M5_REARCHITECTURE_DESIGN_CLOSE_v1_0.md (v1 baseline)
incorporates:
  - Review A (12-point architectural critique, 2026-06-02)
  - Review B (4 missing-asset analysis, 2026-06-02)
  - Native decisions: learning multiplier; MVP already proven in legacy → full build this phase
  - Build-workflow + tooling decisions (2026-06-02): see BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0 + BRAHMA_BUILD_UX_SPEC_v1_0
context: >
  The legacy MVP proved the value; this phase enlarges scope + applies the architectural lessons. v2 is
  the full, hardened build target — not a thin slice. It folds in two external reviews, four new assets,
  the learning-multiplier mechanism, and a cross-cutting robustness spine.
read_with:
  - the per-layer design docs (LAYER_0..LAYER_5), which are amended to align with v2
  - BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0 (product/build experience + tool taxonomy)
  - BRAHMA_BUILD_UX_SPEC_v1_0 (implementation-ready UI/UX)
changelog:
  - v2.1 (2026-06-02): Cascade of the build-workflow decisions — added §A0 (Project Brahma: external
    lexicon, account-management product model, one-time global Brahmagyan/infra build, parallel real-tool
    build); updated §I.5 to the parallel build-the-tool-with-the-asset rule. No change to the L0–L5
    architecture itself.
  - v2.0 (2026-06-02): initial v2 hardened baseline (reviews A+B, four new assets, robustness spine).
---

# MARSYS-JIS — Master Architecture v2.1 — Project Brahma

## §A0 — Project Brahma: naming, product model, tool build

This architecture is delivered as **Project Brahma**. Three product-level decisions (2026-06-02) bind the
whole build and are authoritative here:

- **External lexicon — no "L0–L5" shown to users.** Layers are named in Sanskrit + English on every
  client-facing surface; internal code/docs may keep L0–L5 for precision.

  | Internal | Sanskrit | English |
  |---|---|---|
  | L0 | **Brahmagyan** | Foundation |
  | L1 | **Gaṇita** | Chart Facts |
  | L2 | **Bodha** | Chart Intelligence |
  | L3 | **Kāla** | Temporal |
  | L4 | **Phala** | Prediction |
  | L5 | **Mīmāṃsā** | Learning |

- **Product model = account management.** A client is an *account* whose defining record is the birth data;
  build / resume / consume happen at the owner's convenience, with full CRUD. Birth-data edit → **auto-cascade
  full rebuild** (Gaṇita→Mīmāṃsā). Delete → **immediate hard wipeout, no retention**.
- **Brahmagyan (L0) is a one-time global build.** The native builds L0 + the GCP data infrastructure **once**;
  every later account sees Brahmagyan already green and stands on it. No user rebuilds the foundation or infra.
- **Tools are built for real, in parallel with each layer's assets — no stubs.** Each asset's contract
  includes its retrieval tool(s) + schema + MCP resource + tests; the swarm builds + deploys (web *and* MCP) +
  tests the tool against freshly-generated data in the **same arc** as the asset. Tool granularity is a
  three-tier taxonomy (per-asset primitives close to the source + a few composite capability tools + meta/ops),
  not one-tool-per-layer. Full detail in BUILD_WORKFLOW_AND_TOOLING_DESIGN_v2_0 §L.

## §A — What v2 changes over v1

The v1 baseline (L0–L5) was structurally sound. v2 keeps the layering and hardens it on three fronts:
1. **A correctness spine** the reviews exposed as missing — astronomical ground-truth verification and
   an answer-quality eval, not just internal consistency + prediction calibration.
2. **Four new assets** that turn the instrument from *analytical* to *actionable*: Remediation, Muhurta/
   Electional, Relational/Synastry, Spatial.
3. **Operational robustness** — engine-version migration, an OLTP/OLAP split, an embedding spike, the
   held-out rectification split, correlation-aware confidence, and the unifying learning multiplier.
MVP gating is dropped (the legacy MVP already proved value); this is the full build.

## §B — The enhanced stack (overview)

```
L0 Foundation   — ephemeris · reference library · classical texts · text index · ontology · RULE BASE ·
                  concordance · daily almanac · + REMEDY CORPUS (new)
L1 Chart Facts  — PyJHora full catalog → typed Fact Store + Forensic doc; ayanamsha-invariant/dependent
                  split (new); location-parameterized recompute (new, feeds Spatial)
L2 Intelligence — signals · signal graph · domain/resonance/concordance/contradiction lenses ·
                  activation · negative-space · salience · embeddings · + REMEDIATION asset (new) ·
                  + RELATIONAL/COMPOSITE graph (new)
L3 Temporal     — dasha×transit alignment · convergence timeline · obstruction overlaps · period snapshot ·
                  + SPATIAL activation index (new module)
L4 Predictive   — calibrated ensemble · event anchors · mitigation · birth-time rectification ·
                  + MUHURTA / ELECTIONAL engine (new, inverts L4)
L5 Learning     — pure-event LEL · event chart-state index · scoring · LEARNING MULTIPLIER · cross-corpus
                  research → BigQuery/Parquet (OLAP)
```

## §C — Cross-cutting robustness (the v2 spine)

- **C1 · Verification spine (three tiers).** (a) **Astronomical ground-truth** — one-time + periodic
  spot-checks of PyJHora's longitudes/sunrise/eclipses against an *independent astronomical* source
  (JPL Horizons / raw Swiss Ephemeris). This is verifying *astronomy*, not a Jyotish-parity oracle — it
  does **not** violate the no-JH-parity rule, and it closes the "engine bug is unfalsifiable" hole.
  (b) **Internal consistency** (counts, schema, invariants, determinism). (c) **Answer-quality eval** —
  a golden Q&A set scoring *reading quality* (the actual product), separate from prediction calibration.
- **C2 · Engine-version migration policy.** PyJHora + DE441 versions are pinned; an upgrade is a
  **deliberate, versioned migration**: bump `engine_version`, re-hash, **cascade-rebuild L1→L5** under
  the swarm, diff against the prior version, gate on the astronomical + answer-quality checks. `build_id`
  versions a build; `engine_version` versions the migration across the stack.
- **C3 · OLTP / OLAP split.** **Postgres (+pgvector)** stays the per-chart OLTP + low-latency retrieval
  store. **Cross-corpus L5 research (C10/C11/C12) runs in BigQuery** over **Parquet exports** of L1/L2
  rows to GCS — never as heavy scans on the transactional DB. Keeps OLTP fast and the (non-HA) Postgres unstressed.
- **C4 · Embedding strategy = a real spike, not a deferral.** Evaluate candidate models on a Jyotish/
  Sanskrit retrieval set *before* committing; re-embedding later is costly. Decision precedes L0.4/L2 build.
- **C5 · The learning multiplier (unifying mechanism).** A `learning_multiplier` (default 1.0, two-level
  corpus×chart, Bayesian shrinkage, bounded ≈0.5–2.0) on every learnable unit-class (L0 rules, L2 signal/
  template classes, L4 techniques). L5's only recalibration action is to move multipliers from outcomes;
  the classical layer is modulated, never overwritten. *Ceiling named:* a scalar can't express conditional
  corrections (works-for-career-not-health) — that's a v3 per-domain extension.
- **C6 · Held-out integrity + rectification split.** Predictions logged before outcomes; LEL read-only to
  scoring. **Birth-time rectification uses its own train/test split inside LEL** — events used to rectify
  the time are excluded from later prediction scoring (no leak).
- **C7 · Correlation-aware confidence.** Convergence confidence does **not** treat schools as independent
  witnesses (they read the same chart). Replace `1−Π(1−sᵢ)` with a **correlation-discounted** combination,
  so agreement across correlated systems doesn't inflate certainty.
- **C8 · Provenance + determinism (carried).** Every fact/signal/prediction cites its inputs + rule/verse;
  deterministic parts rebuild identically; full audit trail.

## §D — Per-layer enhancements + new assets

### L0 — Foundation
- **+ Remedy Corpus & Rules (new):** classical upaya texts (mantras, gemstone logic, charity, ritual)
  indexed + structured as remedy rules `{affliction-condition → remedy, source, school, caveat}`. Feeds the
  L2 Remediation asset. (Re-includes the old remedial codex, properly grounded.)
- **Rule Base hardening (the keystone, #3):** rule extraction is its own research track — a **gold-standard
  pilot on one text**, a **defined rule schema + confidence rubric** (confidence has a principled origin:
  textual-strength + cross-text corroboration, not a human guess or an LLM assertion), and a **measured
  quality bar** before the full canon is committed.
- **Embedding spike (C4)** precedes the Text Index build.
- **Licensing** of real editions (Tajaka Neelakanthi, quality translations) is a tracked **hard-blocker risk**.
- **FORENSIC v8.0 → ARCHIVED (cold) as the coverage benchmark** (not wiped). Resolves the kill-list §2 ↔
  FACT_ENGINE §4.2 contradiction; under-production is the failure that already happened once, so the
  benchmark stays.

### L1 — Chart Facts
- **Ayanamsha-invariant / dependent split (#9):** store invariant facts **once** (tropical longitudes,
  declination, speed, much of panchanga); store only ayanamsha-dependent facts per ayanamsha. Materially
  cuts volume + build cost. **SD-depth-for-all dashas retained** (native decision) — the curated 12 systems.
- **Location-parameterized recompute (new):** the engine can re-derive ascendant/houses for a relocation
  — the foundation the Spatial module (L3) builds on.
- Otherwise per `LAYER_1_STORAGE_STRATEGY` (typed Fact Store, JSONL artifact, no RAG over facts).

### L2 — Chart Intelligence
- **+ Remediation asset (new, #Review-B-2):** maps each contradiction-hub / negative-space / high-tension
  anchor → **cited classical upayas** from the L0 Remedy Corpus. `remediation_id, target(contradiction/
  negative_space/anchor), remedy_type(mantra/gem/charity/ritual), prescription, source_citation, school,
  confidence, caveats`. Completes the **diagnose→prescribe** loop; the LLM prescribes grounded, cited
  remedies instead of hallucinating.
- **+ Relational / Composite Signal Graph (new, #Review-B-1):** when two consenting profiles are linked
  (spouse, co-founder), a **persistent composite graph** of cross-chart edges (reinforce/contradict between
  the two natives' signals), enabling relationship-domain prediction + relational L5 learning. Requires
  multi-native data + **consent under the ethical framework**. (Bigger build; sequenced after the single-
  chart stack — §I.)
- **Concordance silent-handling fix (#smaller):** `agreement_level` distinguishes **silent (orthogonal)**
  from **contradicts** — silence is not a "no" vote.
- **Salience expectation (#4):** salience weights start neutral; learned slowly via the multiplier.

### L3 — Temporal Fabric
- **+ Spatial Activation Index (new module, #Review-B-3):** over the location-parameterized recompute (L1),
  identify geographic zones where the native's Travel/Residence (and other) signals are structurally
  amplified — relocational/astro-cartographic prediction. Specialist module; lower priority (§I).
- Otherwise per `LAYER_3_TEMPORAL_FABRIC_DESIGN`.

### L4 — Predictive Engine
- **+ Muhurta / Electional engine (new, #Review-B-4):** **inverts** L4 — takes a *desired action/outcome*,
  searches the L3 fabric + L0/L1 muhurta tools + the native's L2 signals, and returns the highest-confidence
  *future windows* to act. Completes the **predict→optimize** loop.
- **Correlation-aware confidence (C7)** + **rectification holdout (C6)** applied here.
- **Learning expectation (#4):** L4 v1 behaves as a ~equal-weighted **classical ensemble with a slow
  learning veneer** (the multiplier stays ~1.0 until corpus evidence exists). Stated honestly.

### L5 — Learning
- **Cross-corpus research → BigQuery/Parquet (C3)**, not on the OLTP Postgres.
- **Answer-quality eval (C1c)** added alongside prediction calibration.
- **Cross-corpus acquisition strategy (new, #4):** the population learning loop needs a path to many
  consenting natives' outcomes — a defined acquisition + consent plan (currently absent).
- Otherwise per `LAYER_5_LEARNING_DESIGN` + `LEL_SCHEMA_AND_INTAKE` (pure-event LEL, derived event
  chart-state index, the learning multiplier).

## §E — Governance re-base (#2, do first)

The **Build-Guarantor Charter** and the **Program Tracker** are re-based from the legacy A1–A22+META DAG
onto **L0–L5 + the new assets**, and tracker rule R3 ("reuse what's built") is replaced by the clean-slate
+ enlarge intent. Nirīkṣaka's first audit must target L0–L5, not the legacy DAG. **This is the first build-
phase action**, before any swarm work.

## §F — The four new assets, at a glance

| Asset | Layer | Completes | Priority |
|---|---|---|---|
| **Remediation Ledger** | L0 (remedy corpus) + L2 | diagnose → **prescribe** | high (first addition) |
| **Muhurta / Electional engine** | L4 (inverts) | predict → **optimize** | high |
| **Relational / Composite graph** | L2 | single-chart → **relational** | medium (needs multi-native + consent) |
| **Spatial activation index** | L1 recompute + L3 | time → **place** | lower (specialist module) |

## §G — Decisions resolved in v2

- **Verification:** astronomical ground-truth check adopted (not a parity oracle).
- **FORENSIC v8.0:** archived cold as coverage benchmark (not wiped).
- **Dasha dates:** resolved by prior decisions — PyJHora (JH) dates are canonical by construction; FORENSIC
  dates gone; LEL carries real-world event dates; matching computed fresh. No open conflict.
- **SD-depth-for-all:** retained (native), with the ayanamsha-invariant split as the efficiency win.
- **Learning:** single learning-multiplier mechanism; L4 v1 = classical ensemble + slow veneer.
- **OLTP/OLAP:** Postgres for per-chart + retrieval; BigQuery/Parquet for cross-corpus learning.

## §H — Open items → execution briefs

Rule-extraction pilot + quality bar; embedding-model spike; classical-text licensing; cross-corpus consent/
acquisition; L2 domain taxonomy + salience initial weights; L3 time resolution + intensity formula; L4
anchor threshold + ensemble combination + falsifier model; L5 calibration method + significance bars +
multiplier bounds; the relational consent model; the spatial module scope.

## §I — Build sequencing (full build, past MVP)

1. **Governance re-base** (§E) + **astronomical verification harness** (C1a) + **engine-migration policy** (C2).
2. **Rule-extraction pilot** (L0.6, #3) — gate before the full canon.
3. **L0 Foundation** (incl. Remedy Corpus) → **L1** (incl. invariant split + location recompute) → **L2**
   (incl. Remediation) → **L3** → **L4** (incl. Muhurta) → **L5** (incl. BigQuery split + answer-quality eval).
4. **Relational** + **Spatial** modules after the single-chart stack is green.
5. Each asset is built **together with its retrieval tool(s)** — code → deploy (web + MCP) → generate data →
   test the tool against that fresh data — plus its contract, acceptance gate, volume floor, and (where
   applicable) its learning multiplier, under the (re-based) Build-Guarantor Swarm. A layer lights only when
   its assets **and** their tools are verified.

---

*End of MARSYS_MASTER_ARCHITECTURE v2.1 — Project Brahma — CURRENT baseline, 2026-06-02. Supersedes the v1
design baseline. Per-layer docs amended to align (external Brahma lexicon; internal L0–L5 retained). Full
hardened build target; the build phase begins here.*
