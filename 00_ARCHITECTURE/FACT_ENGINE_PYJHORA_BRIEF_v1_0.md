---
artifact: FACT_ENGINE_PYJHORA_BRIEF_v1_0.md
status: DRAFT
version: 1.0
authored_by: Claude (Cowork session) — engine-layer implementation spec for the fact-centric parallel build, 2026-05-27
authored_on: 2026-05-27
audience: native (Abhisek Mohanty); implementation executor (Claude Code in Antigravity IDE)
disposition: >
  Implementation guidance for the L1 fact engine of the fact-centric PARALLEL build:
  how to wrap PyJHora, what to emit, how to guarantee accuracy, and what to fall back to.
  Engine emits to canonical JSONL → deterministic loader → existing data stores (schema
  unchanged, so existing retrieval tools work without modification). PENDING NATIVE APPROVAL.
parent_brief: 00_ARCHITECTURE/PROVENANCE_TIERING_DECISION_v1_0.md
sibling_artifacts:
  - 00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md
  - 00_ARCHITECTURE/PANEL_MODE_TOOL_SPEC_v1_0.md
  - 00_ARCHITECTURE/MSR_UCN_CONTAMINATION_AUDIT_v1_0.md
build_mode: clean parallel build (native decision) — leaves current corpus intact
oracle: 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md (validated JH transcription = regression ground truth)
approval_gate: native sign-off required before implementation begins
---

# Fact Engine (PyJHora) — Implementation Brief

## §0 — One-paragraph statement

The parallel build takes a single input — **date, time (IST), latitude, longitude, location** —
and deterministically generates the full per-chart data corpus, narrative-free, Python-only.
PyJHora is the formula engine (it re-implements Jagannatha Hora over Swiss Ephemeris). The
engine is **wrapped, normalized, and validated**, not trusted: it emits **schema-validated
JSONL** (the new source of truth), which a **separate deterministic loader** projects into
the **existing data stores with their schema unchanged**, so every existing retrieval tool
keeps working. Accuracy is guaranteed by triangulation: PyJHora + an independent pyswisseph
cross-check + FORENSIC v8.0 as the human-validated regression oracle.

---

## §1 — Architecture placement

### §1.1 — Shared vs. per-chart (build-once vs. build-on-input)
- **Shared, build-once (chart-independent):** L0 classical texts + their vector index; raw
  ephemeris (Parquet). Built once, reused for every chart. The new pipeline does NOT
  regenerate these.
- **Per-chart, build-on-input (keyed by `chart_id`):** everything else — chart facts,
  structural facts, signals, graph, chart-mapped panchanga. Triggered by the single input.

### §1.2 — Structural identity with existing stores (hard constraint)
The loader writes into the **same Postgres tables with the same schema** the current
retrieval tools read (`chart_facts`, `ephemeris_*`, signal store, etc.). Columns are
preserved so tools do not break. What changes is **content, not schema**: scores are
computed not authored; narrative/prose fields are emptied or replaced with rule-IDs and
structured references; the signal set is the *complete* enumeration (never-drop), so row
count rises. `chart_id` is first-class everywhere (multi-native by construction).

### §1.3 — Single-input trigger
Input `{datetime_IST, lat, lon, location}` → DAG runs all per-chart nodes → JSONL emit →
schema gate → FORENSIC/oracle gate → loader → existing stores. One command, end to end.

---

## §2 — Output format decision

**Decision: PyJHora → adapter → canonical JSONL → deterministic loader → existing DB.
Do NOT write PyJHora output directly into the data stores.**

| Path | Audit/diff | Validation gate before serving | Reproducible | Verdict |
|---|---|---|---|---|
| Direct PyJHora → DB | none (mutable) | none | weak | **rejected** — recreates the drift class |
| PyJHora → **JSONL** → loader → DB | line-level git diff | yes (schema + oracle on JSONL) | content-addressed | **adopted** |

Rationale: the JSONL-in-between is the auditable, diffable, content-addressed source of
truth; the DB becomes a pure reproducible projection. Bad facts are caught at the JSONL
gate **before** they reach the retrieval layer. The engine adapter and the DB loader become
independently testable — a schema change re-runs the loader, not the engine.

**Format specifics:**
- **Per-chart facts → JSONL**, one flat typed record per line:
  `{fact_id, chart_id, category, divisional_chart, value, unit, tier:"T1",
  provenance:{engine, engine_version, ephemeris_version, ayanamsha, inputs_hash, computed_at, source_rule}}`.
  One fact = one line ⇒ a single change is a one-line diff (clean drift detection + blame).
- **Bulk shared time-series → Parquet** (ephemeris, eclipses, retrogrades). Columnar, built once.
- **Exact astronomical values stored as integers (arc-seconds) or decimal strings, never raw
  floats** — so regeneration is bit-stable across engine versions.
- **Content-address** each chart's fact set by hashing `(engine_version + ephemeris_version +
  ayanamsha + birth inputs)`. Reproducible; tells you exactly which engine produced which fact.

---

## §3 — PyJHora implementation approach: wrap, don't trust

### §3.1 — The adapter layer (the critical component)
PyJHora returns heterogeneous shapes (indices vs names, locale-sensitive strings, tuples
whose meaning is positional, varying across versions). Build a **thin typed adapter per
PyJHora function**: call → normalize to the typed schema → emit JSONL record. The adapter is
where a misread index becomes a silent systematic error across every chart, so:
- Force deterministic settings (English/index mode, fixed house system, explicit node type).
- One adapter function per PyJHora call, each with its own unit test against known values.
- No raw PyJHora output ever reaches JSONL un-normalized.

### §3.2 — Pin everything (reproducibility)
Reproducibility depends on the **library**, not just your code. Pin and record in provenance:
the exact PyJHora version, its bundled Swiss Ephemeris data files (de440/de431), the
ayanamsha mode, the node type (mean vs true — must match JH; resolves the pending MEAN_NODE
question), and swe flags. A library bump can change outputs — treat version-pinning as
load-bearing, not hygienic (PyJHora is single-maintainer OSS).

---

## §4 — Accuracy strategy: triangulation, not faith

"Absolute accuracy" comes from three independent sources cross-checked, gated before serving.

### §4.1 — FORENSIC v8.0 as the regression oracle `[primary gate]`
FORENSIC v8.0 *is* a human-validated JH transcription. Therefore: run PyJHora for Abhisek
with pinned config and **diff field-by-field against FORENSIC v8.0**. Every divergence
triages to one of: (a) ayanamsha/config mismatch, (b) adapter bug, (c) genuine PyJHora bug.
This is the concrete form of the standing "validate-once vs JH" rule, and it is where the
known JH-vs-FORENSIC ayanamsha discrepancy (and KP-ayanamsha-per-section) surfaces and gets
pinned — **before any downstream layer is built.** The corpus being replaced certifies its
replacement.

### §4.2 — Independent pyswisseph cross-check
For the astronomical core (planetary longitudes, ascendant, ayanamsha value, house cusps),
compute the same quantities directly from `pyswisseph` and assert agreement with PyJHora to
a tight tolerance. Two independent engines agreeing = absolute confidence on the core.

### §4.3 — Per-function unit tests + golden master
Each adapter function tested against known values (ideally on 2–3 reference charts with
published JH output, not only Abhisek — single-chart validation can pass by luck). Once
validated, snapshot the canonical JSONL as a **golden master**; any future engine/library
change that alters output triggers a mandatory diff review.

### §4.4 — Ayanamsha resolution is Phase 0
Resolving and pinning the ayanamsha so PyJHora reproduces FORENSIC v8.0 is the **first
milestone and a hard prerequisite** — nothing downstream is trustworthy until it passes.

---

## §5 — Known PyJHora risks and mitigations

| Risk | Mitigation |
|---|---|
| Heterogeneous returns (index vs name, locale strings) | Per-function typed adapter; force English/index mode; unit-test each |
| Ayanamsha / FORENSIC mismatch (known open item) | Phase-0 ayanamsha resolution against FORENSIC v8.0; pin + document |
| Node type (mean vs true Rahu/Ketu) | Pin explicitly to match JH; record in provenance (closes MEAN_NODE question) |
| House-system trap (e.g. pyswisseph 'S' returns sandhis, not madhyas — already hit) | Adapter computes madhyas correctly; unit-test against FORENSIC house cusps |
| Single-maintainer OSS, version-sensitive output | Hard version pin + bundled-ephemeris pin in provenance; golden-master diff gate |
| Float drift across regenerations | Store arc-seconds as integers / decimal strings |
| Module-level correctness gaps (a varga/dasha may be wrong) | Per-section FORENSIC validation; modular fallback (§6) for any failing module |

---

## §6 — Fallback and alternatives (if PyJHora has issues)

**Recommendation: PyJHora primary + pyswisseph as independent oracle + JH desktop/FORENSIC
as ground truth. Replace failing PyJHora modules individually, never the whole engine.**

| Option | Role | Note |
|---|---|---|
| **PyJHora** | primary engine | JH-modeled; broadest Jyotish coverage in Python |
| **pyswisseph (Swiss Ephemeris)** | cross-check + fallback foundation | Gold standard for astronomy; no Jyotish logic — you'd add it for any replaced module |
| **Jagannatha Hora (desktop)** | ground-truth reference | The authority, but GUI-only / not pipeline-scriptable; use to generate reference reports (FORENSIC v8.0 already is one) |
| Commercial APIs (ProKerala etc.) | **rejected** | Non-deterministic, network dependency, not auditable, violates GCP-only/no-external rule |
| Other libs (Maitreya, etc.) | not recommended | Less comprehensive / less JH-aligned |

Modular-replacement rule: if module M (e.g. a specific varga or dasha) fails the §4.1 gate,
reimplement M on pyswisseph and keep the rest of PyJHora. The adapter boundary makes this a
local change.

---

## §7 — Implementation sequencing (each phase validation-gated)

0. **Pin config + resolve ayanamsha** against FORENSIC v8.0. Output: locked engine config. *(hard gate)*
1. **Adapter for L1 core** (positions, divisionals, ascendant, houses) → JSONL → validate vs FORENSIC §2/§3 + pyswisseph cross-check.
2. **Extend adapter** to panchanga, dashas, shadbala, ashtakavarga, KP, Jaimini karakas, sahams, arudhas, Tajaka → validate each vs the matching FORENSIC section.
3. **Canonical JSONL schema** finalized + schema-validation gate.
4. **Loader** JSONL → existing Postgres tables (schema-identical). Verify retrieval tools read unchanged.
5. **Custom layers** (structural fact layer, fact-graph, complete never-drop signal substrate with decomposed coefficients) — per the sibling specs.
6. **DAG runner** wires 0–5 into the single-input one-command build (content-addressed, per-node gates).

---

## §8 — Provenance
Model-authored (Claude, Cowork), DRAFT, for native review. Modifies nothing. Per CLAUDE.md
§L, implementation begins only after native sign-off. The DAG-runner design and the
custom-layer specs are separate documents in this family.
