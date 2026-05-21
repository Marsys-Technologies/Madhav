---
artifact: PHASE_B_PLAN_v1_0
version: 1.0
status: SUPERSEDED
backfill_note: >
  Frontmatter backfilled by governance hygiene pass following PR #111 SESSION_HALT.md AC.7.
  Existing file body untouched. Status SUPERSEDED per CLAUDE.md §E (M2 closed 2026-05-01).
---

# MARSYS-JIS Corpus Activation — Phase B Plan v1.0 (B-PRIMARY, M2-SCOPED)

**Status:** APPROVED FOR EXECUTION — Phase B.0 pending start.
**Supersedes:** `twinkly-puzzling-quokka.md` (session-scoped draft), v2 draft (scope-only), v1 (query-primary).
**Macro-phase context:** M2 (Corpus Activation) of M1–M10 arc per `00_ARCHITECTURE/MACRO_PLAN_v2_0.md`.
**Plan Owner:** Abhisek Mohanty
**Date:** 2026-04-23
**Version:** 1.0.3

## Changelog
- **2026-04-28 v1.0.4 — Infrastructure Amendment (Cowork, post-B.3):** Supabase fully replaced by GCP stack (Cloud SQL + Firebase Auth + GCS). Voyage-3-large replaced by Vertex AI `text-multilingual-embedding-002` (768 dims) — see `python-sidecar/rag/embed.py` + migration `010_vertex_ai_embedding_dim.sql`. All references to "Voyage-3-large primary" and "Supabase pgvector store" in §A.4 and sub-phase tasks describe the historical tech stack at plan authoring; the live stack is now fully GCP-native. No structural changes to phase logic; all acceptance criteria remain valid against the new stack.
- **2026-04-24 v1.0.3**: WARN items 2/3/5/7 amendment cycle. Stale MACRO_PLAN v1.0 pointer → v2.0; stale PROJECT_ARCHITECTURE pointer → v2.2; B.0 scope refresh per ONGOING_HYGIENE_POLICIES §I; remaining WARN items resolved. No substantive content changes. Prepared by Cowork; executed by Claude Code (Madhav 16).
- **2026-04-23 v1.0.2**: Applied reconciler-pass amendments (PHASE_B_PLAN_v1_0_RECONCILER_PASS_v1_0.md). BLOCK remediations: (1) B.0 Task 1 and acceptance criterion updated to target `MSR_v3_0.md` (not `v2_0`); archive of `MSR_v1_0` and `MSR_v2_0` added as B.0 sub-task. (2) B.1 Task 1.5 inserted: implement and meta-test p1/p2/p5 validators before B.2 begins. (3) B.2 Chunker Specification subsection added — 6 doc-types with boundary rules. Selected ESCALATE remediations: §E.6 validator rows augmented with detection-mechanism and structural-limitation notes; §E.7 buffer raised to +75% (~$315 budget); B.0 augmented with Tasks 12–14 (chunker_spec, prompt_registry.py, golden query sets) and baseline_edge_count.json; B.3 index-time halt policy added; B.3.5 CGM edge-proposal prompt and Gemini response-file storage added; B.5 Task 0 added (prediction_ledger.py + P8 extension before mining), acceptance-rate monitoring and mid-phase sanity eval added; B.7 router availability fallback added; §H P6 degraded-mode and P7 significance-scoring mechanism documented; §J two new risk rows; §K manifest updated.
- **2026-04-23 v1.0.1**: Integrated Gemini corrective pass-1. Replaced §E.3 (JSON-canonical storage model + V-shift1-drift active validator), §E.5 (two-pass table with Contradictions, Reconciliations, and Retrieval-bundles rows), §E.7 (actor × phase cost matrix, grand total $140.09, budget ~$210.14), §G Phase B.0 Task 1 (GAP_13_RESOLUTION target file + verifiable delta + acceptance criterion). Arithmetic verified.
- **2026-04-23 v1.0.0**: Promoted from session-scoped draft. Un-gated execution based on GAP.13 (8-karaka) and directory numbering (`035_DISCOVERY_LAYER`) resolutions.

---

## A. Operating Brief (verbatim intent)

1. **Discovery-primary, not query-primary.** Primary consumer is another LLM doing pattern-discovery. Humans are validators. Query UI is byproduct.
2. **Two-pass on every significant artifact.** Gemini 2.5 Pro promiscuous connector (pass 1); Claude Opus 4.7 skeptical reconciler (pass 2). Ledger-logged.
3. **Nine principles as automated validators.** Rejection gate, not checklist.
4. **Tech stack locked.** Postgres+pgvector, Voyage-3-large primary / OpenAI fallback, BM25, NetworkX→Postgres, FastAPI sidecar, Claude Opus synth+reconciler, Gemini 2.5 Pro connector, **Opus 4.7 router (native-overridden stack deviation)**, Ragas+custom eval, minimal Next.js validation surface.
5. **Discovery layer** = new corpus layer: patterns, resonances, contradictions, clusters, ledger.
6. **Acharya-grade or fail.**
7. **Cadence:** one phase, confirm before code, version everything, red-team every 3rd session, stop-markers honored, session log updated on close.

Known M1 gaps (brief §1, treat as known, do NOT silently compensate):
- Four L3 reports stale relative to FORENSIC_v8_0 (exact files to enumerate in Staleness Register).
- Chart Graph Model not rebuilt on v8.0.
- GAP.13 (Chara Karaka 7 vs 8) pending native decision.

---

## B. Scope Step Deliverable (accepted 2026-04-23)

### B.1 — Restatement

LLM-facing pattern-discovery engine over the L1→L3 corpus as graph+vector space. Every significant artifact two-pass'd (Gemini→Claude for proposals; Claude→Gemini for contradictions — see §E.5). P1–P9 as executable validators. Outputs: four discovery registers, append-only ledger, thin validation UI, gated write-backs.

### B.2 — Assumptions challenged (B.2.1–B.2.9)

Preserved verbatim from v2. Nine items flagged: staleness register, two-vector-space hazard, router model evidence, ledger compaction, per-artifact-type pass ordering, CGM-as-dependency, five-layer framing, P7 significance threshold, P9 structural reproducibility. See also §E.5 (pass ordering table) and §E.9 (P9 tolerance spec).

### B.3 — Discovery-Layer Structure (final directory numbering in §E.1)

Registers: `PATTERN_REGISTER`, `RESONANCE_REGISTER`, `CONTRADICTION_REGISTER`, `CLUSTER_ATLAS`.
Ledger: daily-partitioned JSONL + rolled-up index + sha256-keyed blob store.
Schemas: JSON Schema for every artifact type.
Prompts: version-tagged per Hook 3 (§F.3).
Red-team: probes_v1.md + per-run result files.
Full tree at §E.1.

### B.4 — Ledger Event Schema

Preserved from v2 with Hook 3 additions (`prompt_version`, `prompt_hash` promoted to required fields). Full schema in §G.B.1 artifact list.

### B.5 — Locked Clarifications (2026-04-23)

| # | Locked | Notes |
|---|--------|-------|
| CQ1 | **b** — existing Supabase, migration `005_pgvector_rag_schema.sql` | |
| CQ2 | **a** — stale-mark L3 at ingestion; Staleness Register; rebuild scheduled as follow-on | |
| CQ3 | **c** — human-in-loop Gemini; batched prompts + response files; `actor=gemini-web-<date>` | |
| CQ4 | **b** — commit ledger events; `LEDGER/blobs/` git-ignored | |
| CQ5 | **b** — rebuild CGM on v8.0 as prerequisite micro-phase B.3.5 | |
| CQ6 | **Opus 4.7 router** — STACK DEVIATION; native override reconfirmed; no downgrade path | |
| CQ7 | **a** — single initial batch pass for v1.0 | |
| CQ8 | **b** — native reviews all `validated && HIGH` before write-back | |
| CQ9 | **a** — five-layer (L1/L2/L2.5/L3/L4); L0 archival; L5–L7 out of scope for M2 *(L2 layer archived Phase 14F 2026-04-28; effective architecture is L1→L2.5→L3→L4)* | |
| CQ10 | **a** — proceeding | |

### B.6 — Post-"proceed" expansion

This section is now §D onwards.

---

## C. Guardrails Active During This Plan

- No file creation outside this plan file until native approves B.0.
- No migrations, no scaffolding, no code.
- No silent tech-stack substitutions.
- Stop-markers: `[EXTERNAL_COMPUTATION_REQUIRED]`, `[NATIVE_CONFIRMATION_NEEDED]`, `[PRINCIPLE_VIOLATION_SUSPECTED]`.
- Session log updated on each phase close.
- **Scope boundary from Macro Plan:** M2 only. Do NOT pre-build for M3 (temporal animation), M4 (empirical calibration), M5 (probabilistic model), M6 (prospective testing), M7 (population), M8 (classical cross-ref), M9 (multi-school), M10 (external validation). The only cross-macro-phase carry-forward is the three Learning Layer hooks below (substrate only, no algorithms).

---

## D. Macro-Phase Positioning (M2 context)

**Current macro-phase:** M2 Corpus Activation.
**Prior:** M1 Corpus Completeness (mostly done; three known gaps carried forward per §A).
**Next:** M3 Temporal Animation (time-indexed event surface; belongs in `05_TEMPORAL_ENGINES/` which we do NOT touch in M2).
**Cross-cutting substrate:** Learning Layer (M2 substrate only; first algorithms fire at M4).
**Concurrent non-code workstreams (run in parallel, not part of M2 code scope):**
- **Life Event Log** — native-cadenced; prerequisite for M4. M2 touches it only to (a) verify v1.2 is the current version, (b) ingest into corpus.
- **Prospective prediction logging** — activates the moment discovery engine produces first falsifiable forward-looking claim (Hook 2, §F.2).

**What M2 explicitly does NOT do:**
- No temporal animation engine (that's M3).
- No signal-weight calibration math (that's M4).
- No Bayesian network (that's M5).
- No automated scoring at window-close (that's M6).
- No cohort data ingestion (that's M7).
- No classical-text cross-reference index (that's M8).
- No multi-school triangulation (that's M9).
- No blind-test vs external acharyas (that's M10).

**What M2 does carry forward (substrate only):**
- `06_LEARNING_LAYER/` scaffolded empty (Hook 1).
- Prediction ledger JSONL schema defined and live when first forward-looking claim appears (Hook 2).
- Version-tagged prompt registry from day one (Hook 3).

---

## E. Resolved Items from Prior Proceed Message

### E.1 — Directory numbering

**Existing directory tree (as of 2026-04-23):**
```
00_ARCHITECTURE/           # governance
01_FACTS_LAYER/            # L1
02_ANALYTICAL_LAYER/       # L2 (ARCHIVED Phase 14F 2026-04-28 → 99_ARCHIVE/02_ANALYTICAL_LAYER/)
025_HOLISTIC_SYNTHESIS/    # L2.5
03_DOMAIN_REPORTS/         # L3
04_REMEDIAL_CODEX/         # remedial actions (not a retrieval layer)
05_TEMPORAL_ENGINES/       # M3 artifacts (not touched in M2)
06_QUERY_INTERFACE/        # 3 files: query taxonomy, playbooks, prompts
99_ARCHIVE/
```

**Conflict:** Macro Plan names `06_LEARNING_LAYER/`; existing `06_QUERY_INTERFACE/` holds that slot.

**Resolution (confirmed 2026-04-23):**
- New `035_DISCOVERY_LAYER/` — parallels existing `025_HOLISTIC_SYNTHESIS/` fractional convention. (Verified: directory format is `025_` not `02_5_`).
- **Retire `06_QUERY_INTERFACE/`:** its files move to `035_DISCOVERY_LAYER/QUERY_TAXONOMY/`. This migration requires a pre/post file-and-line-count check to confirm zero data loss. Any stale-era content found must not be silently migrated but explicitly flagged to the `STALENESS_REGISTER.md`.
- `06_LEARNING_LAYER/` — scaffolded empty in B.0.
- `04_REMEDIAL_CODEX/` and `05_TEMPORAL_ENGINES/` untouched.

### E.2 — L5 (Temporal) out of scope for M2

`05_TEMPORAL_ENGINES/` is M3 work. M2 does not read from, write to, or restructure `05_TEMPORAL_ENGINES/`. Temporal reasoning in M2 is limited to: (a) dasha-window metadata carried on existing L1 facts (used by the router for significance scoring and by discovery for "time-gated" flagging), (b) reading the natal dasha sequence from FORENSIC_v8_0 as reference. No new temporal-engine code in M2.

### E.3 — Machine-parseable register entries

Primary consumer = LLMs, not humans. Implications:

**Storage format:** Each register entry lives as two co-located files:
- `<id>.json` — **Canonical source of truth.** Validated against the corresponding JSON Schema in `SCHEMAS/`.
- `<id>.md` — **Derived view.** Human-readable view containing YAML frontmatter + templated markdown body, generated directly from the JSON.

**Parse invariant:** An LLM consumer loading the discovery registers reads `.json` files only. Humans browsing the registers read `.md` files.

**Build process and drift resolution:**
- The `.md` file is automatically regenerated from the `.json` whenever the `.json` file changes.
- **V-shift1-drift (active validator):** Trigger: fires at pre-commit hook, at CI gate, and before any L2+ compute step. Failure mode: if `.md` content does not match the rendered output of its canonical `.json`, the commit or compute is blocked. Remediation: re-render `.md` from `.json` using the register's template; the manual `.md` edits are discarded (never treated as authoritative). Drift event logged to ledger.

**Index files:** Each register has an `INDEX.json` with `[{id, status, confidence, domains, last_updated}]` for fast LLM traversal without loading every entry.

**Schema versioning:** JSON Schema files carry `$id` + `version`. Schema drift = version bump + migration note in changelog.

### E.4 — Cluster annotation prompt outline

Embedding-space clusters have no intrinsic meaning until annotated. The mechanism annotation is the hard part.

**Prompt outline (to be materialized in `035_DISCOVERY_LAYER/PROMPTS/gemini/cluster_annotation_v1.md`):**

```
ROLE: Promiscuous connector (two-pass protocol, pass 1).
TASK: Given a cluster of N signals discovered by KMeans/HDBSCAN over Voyage embeddings,
      propose mechanism annotations — why these signals co-cluster astrologically.

INPUT (structured):
  cluster_id: CLUSTER.nnn
  members: [{chunk_id, content, YAML_frontmatter}, ...]  # 3–20 members
  cluster_centroid_nearest_neighbors: [chunk_id, ...]
  cluster_vs_next_cluster_separation: float
  shared_entity_co-occurrence: {entity: count}
  shared_domain_co-occurrence: {domain: count}

OUTPUT (strict YAML, will be JSON-schema-validated):
  mechanism_candidates:
    - candidate: "<one-sentence mechanism>"
      classical_basis: "<BPHS/Phaladeepika/Jaimini/etc. reference if applicable>"
      supporting_members: [chunk_id, ...]
      counter_members: [chunk_id, ...]   # cluster members that resist this mechanism
      confidence_prior: LOW | MED | HIGH
  recommended: <letter referencing candidates>
  alternatives_considered: [<letter>, ...]
  counter-cases: [<astrological situations where this cluster should NOT fire>]
  falsifier: "<condition that invalidates this mechanism>"
  claims_with_evidence:
    - claim: "<specific claim>"
      supporting_chunk_ids: [chunk_id, ...]
      supporting_l1_facts: [fact_id, ...]

CONSTRAINTS:
- Cite only from input. Do not invent signal IDs.
- If the cluster appears incoherent (no shared mechanism), output NO_COHERENT_MECHANISM with reasoning.
- If classical basis requires a text not cited in the corpus, flag [EXTERNAL_CORPUS_REQUIRED] — do NOT fabricate.
```

Reconciler (Claude Opus 4.7) reads this output, validates against P1–P9, assigns status (candidate/validated/rejected/deferred), writes to `CLUSTER_ATLAS`.

### E.5 — Per-artifact-type two-pass ordering

Per B.2.5, ordering is artifact-type-scoped. Locked table:

| Artifact type | Pass 1 | Pass 2 | Rationale |
|---------------|--------|--------|-----------|
| Graph edges (CITES, MENTIONS, AFFECTS_DOMAIN, CROSS_LINKS, SUPPORTS) | Gemini | Claude | Edge proposals need high-recall discovery; Claude filters against L1 fidelity. |
| Patterns (PATTERN_REGISTER) | Gemini | Claude | Cross-signal pattern space is combinatorially large; Gemini over-proposes, Claude rejects. |
| Resonances (RESONANCE_REGISTER) | Gemini | Claude | Cross-domain walks need breadth; Claude validates against CDLM + UCN authority. |
| Cluster annotations (CLUSTER_ATLAS) | Gemini | Claude | Mechanism hypotheses need divergence; Claude validates classical basis. |
| **Contradictions (CONTRADICTION_REGISTER)** | **Claude (invariant scanner)** | **Gemini (reconciliation candidates)** | **P1/P2/P5 contradictions are deterministic; Claude's scanner is faster and more precise. Gemini then proposes steelman reconciliations.** |
| **Reconciliations (contradiction-class)** | **Claude (invariant scan)** | **Gemini (propose) → Claude (finalize)** | Contradiction reconciliations invert the standard pipeline per B.2.5. Claude runs invariant-scan first, Gemini proposes reconciliation candidates, Claude finalizes. |
| **Reconciliations (simple)** | **Claude** | **n/a** | Simple reconciliations (edges, patterns, resonances, clusters) are Claude-only single-pass artifacts. No meta-pass. |
| **Retrieval bundles** | **n/a** | **n/a** | Not subject to two-pass protocol (deterministic hybrid pipeline output). Validators enforce layer-balance, citation sufficiency, and chunk-metadata completeness prior to LLM consumption. |
| Synthesis (final answers on query path) | (retrieval only) | Claude (synthesizer) | Retrieval is deterministic; Claude composes. Gemini is not in the synthesis path. |
| Red-team probe results | Claude (probe generator) | Gemini (adversarial extension) | Claude knows the validators; Gemini stress-tests with novel attack vectors. |
| Prompt registry entries | Claude | n/a | Claude-authored; version-tagged per Hook 3. |
| Ingestion chunks | Claude (deterministic chunker) | n/a | Deterministic code, no LLM pass. |
| Embeddings | Voyage-3-large | n/a | Deterministic API, no reasoning pass. |

Any other artifact type discovered during execution: defaults to Gemini→Claude unless flagged as structural/deterministic, in which case Claude-only or no-LLM.

### E.6 — Validator meta-tests (P1–P9)

Each principle gets a dedicated validator module in `platform/python-sidecar/rag/validators/`. Each validator module ships with test fixtures showing it correctly **rejects violating inputs** and **accepts compliant inputs**. The validators themselves are part of the pipeline's rejection gate; the meta-tests ensure the validators work.

| Principle | Validator | Reject fixtures | Accept fixtures |
|-----------|-----------|-----------------|-----------------|
| P1 Layer separation | `p1_layer_separation.py` | claim mixing L1 fact + L2+ interp in same sentence; L2+ claim with no layer tag | fact-only chunk; interp-only chunk; layer-bridged claim with explicit "[L1 fact] → [L2 interp]" marker |
| P2 Citation discipline | `p2_citation.py` | L2+ claim with no `v6_ids_consumed`; claim citing non-existent fact_id | L2+ claim citing resolvable L1 fact_ids |
| P3 Whole-Chart-Read | `p3_whole_chart_read.py` | interpretive bundle with no L2.5 (UCN/CDLM) chunks | interpretive bundle with ≥1 UCN chunk + ≥1 CDLM chunk |
| P4 No fabricated computation | `p4_no_fabrication.py` | claim containing a position/date/degree not in L1 | claim only using L1-sourced positions; claim with `[EXTERNAL_COMPUTATION_REQUIRED]` marker |
| P5 Signal IDs resolve | `p5_signal_id_resolution.py` | claim citing `SIG.MSR.888` (not in register) | claim citing signals that exist in MSR_v3.0 |
| P6 UCN authority | `p6_ucn_authority.py` | answer favoring L3 domain claim when UCN contradicts without explicit override | answer favoring UCN; answer flagging contradiction for discovery |
| P7 Three-interpretation | `p7_three_interpretation.py` | significance≥0.7 answer with <3 interpretations | significance<0.7 answer; significance≥0.7 with 3 candidates + recommended + falsifier |
| P8 Confidence | `p8_confidence.py` | claim with no confidence; claim with out-of-range confidence | claim with LOW/MED/HIGH + rationale citing citation breadth + convergence + counter-evidence |
| P9 Audit trail | `p9_audit_trail.py` | artifact with missing ledger event references; artifact whose input_bundle_hash doesn't match logged bundle | artifact with complete two-pass trail + resolvable ledger refs |

Each validator's fixture file: `platform/python-sidecar/rag/validators/fixtures/p<n>_{accept,reject}_<case>.json`. `pytest` runs validators against fixtures in CI-lite (we don't have CI here, but the eval harness runs them pre-phase-close).

**Validator implementation notes (reconciler-pass additions):**

- **P1 detection mechanism.** `p1_layer_separation.py` uses a curated vocabulary of interpretive trigger-words to detect semantic violations in L1-tagged chunks: modal verbs ("indicates," "suggests," "implies," "denotes," "shows"), predictive language ("will," "tends to"), evaluative language ("strong," "weak," "afflicted"). Any of these in an L1-tagged chunk without the explicit `[L1 fact] → [L2 interp]` bridging marker triggers a reject. The vocabulary is maintained as a fixture file `fixtures/p1_trigger_vocab.json` alongside the accept/reject JSON fixtures. The false-positive rate must be verified against the actual L1 corpus before the validator is declared live.

- **P2 field resolution.** `v6_ids_consumed` is a historical artifact of the MSR authoring convention and will NOT be renamed in Phase B (to avoid corpus-wide re-authoring cost). The P2 validator additionally checks: any L1 ID referenced in `v6_ids_consumed` must resolve against `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` (the canonical L1). Validator implementation must load v8.0 IDs as the resolution target, not v6.0 IDs.

- **P3 chunker dependency.** P3 enforcement requires UCN and CDLM chunks to be present in the vector store. The B.2 chunker must explicitly cover both doc-types (see B.2 Chunker Specification). If UCN or CDLM chunks are absent, P3 fires vacuously. The B.2 acceptance criterion includes a count check for UCN and CDLM chunks.

- **P4 position grammar.** `p4_no_fabrication.py` loads all FORENSIC_v8_0 positional values into a `canonical_positions` set at startup. Position detection in LLM output uses a regex covering degree-minute-second patterns, rounded-degree patterns, and date patterns. Any detected position not in `canonical_positions` triggers reject. Tolerance: ±0.5° for rounded references.

- **P6 degraded mode (before CONTRADICTION_REGISTER).** See §H for the P6 degraded-mode policy covering phases B.1–B.4.

- **P7 significance score source.** Significance score is a required field in the `QueryPlan` object emitted by the router (Phase B.7). See §H for the P7 significance-scoring mechanism.

- **P8 structural limitation.** P8 enforces structural presence only: confidence field is LOW/MED/HIGH, rationale field is non-empty, rationale length ≥ 50 characters. P8 does NOT enforce rationale quality — that is a human-in-loop concern at phase-gate review. This known gap is documented in the meta-test fixture header.

### E.7 — Cost forecast per phase

Rough estimates modeled under human-in-loop constraints. All figures in USD.
- **Opus Pricing:** $15 / 1M input tokens, $75 / 1M output tokens. *(Anthropic published rates as of 2026-04-23; verify at each phase start.)*
- **Voyage Pricing:** $0.12 / 1M tokens. *(voyage-3-large; verify at phase start.)*
- **Gemini Pricing:** $0.00 (Human-in-loop flat-rate).
- **Call-count derivation (B.5 reconciler estimate):** ~20 validated patterns × 5 reconciler passes/pattern + 10 resonances × 5 + 5 contradictions × 10 (inverted pass = higher iteration) + 10 clusters × 5 = ~250 core calls, doubled for re-runs and schema rejections = 500. B.4/B.5 reconciler input context at 8K–10K tokens for complex patterns (not the 4K profile used in B.3.5/edge work); this raises effective reconciler cost by ~62% for those phases.
- **Note:** LLM budget covers API costs only. Human-in-loop estimated at ~62h total (§E.8). This is not in the LLM budget but is the dominant project cost.

**Opus Call Profiles:**
- **Router:** 1.5K in / 0.2K out = ~$0.0375 / call
- **Reconciler:** 4.0K in / 0.5K out = ~$0.0975 / call
- **Synthesizer:** 8.0K in / 1.0K out = ~$0.1950 / call

| Phase | Router (Opus) | Reconciler (Opus) | Synthesizer (Opus) | Connector (Gemini) | Embeddings (Voyage) | Other | Phase Total |
|-------|---------------|-------------------|--------------------|--------------------|---------------------|-------|-------------|
| B.0 Foundations | 0 | 0 | 0 | 0 | 0 | $0 | **$0.00** |
| B.1 Ingestion | 0 | 0 | 0 | 0 | 0 | $0 | **$0.00** |
| B.2 Chunking | 0 | 5 QA calls ($0.49) | 0 | 0 | 0 | $0 | **$0.49** |
| B.3 Embedding | 0 | 0 | 0 | 0 | 1.8M tokens ($0.22) | $0 | **$0.22** |
| B.3.5 CGM rebuild | 0 | 50 calls ($4.88) | 0 | 4 batches ($0) | 0 | $0 | **$4.88** |
| B.4 Graph const. | 0 | 200 calls ($19.50) | 0 | 6 batches ($0) | 0 | $0 | **$19.50** |
| B.5 Discovery | 0 | 500 calls ($48.75) | 0 | 12 batches ($0) | 0.5M tokens ($0.06) | $0 | **$48.81** |
| B.6 Retrieval | 0 | 0 | 20 calls ($3.90) | 0 | 50K tokens ($0.01) | $0 | **$3.91** |
| B.7 Router+plans | 100 calls ($3.75) | 0 | 0 | 2 batches ($0) | 0 | $0 | **$3.75** |
| B.8 Synthesis | 0 | 0 | 50 calls ($9.75) | 0 | 100K tokens ($0.01) | $0 | **$9.76** |
| B.9 Evaluation | 0 | 0 | 200 calls ($39.00) | 4 batches ($0) | 200K tokens ($0.02) | $0 | **$39.02** |
| B.10 Red-team | 0 | 100 calls ($9.75) | 0 | 6 batches ($0) | 0 | $0 | **$9.75** |
| **Actor Total** | **100 ($3.75)** | **855 ($83.37)** | **270 ($52.65)** | **34 batches ($0)** | **2.65M ($0.32)** | **$0** | **$140.09** |

**Total:** ~$140.09.
Buffer: +75% for B.4/B.5 reconciler context overrun, retries, re-runs, and schema drift reworks → **~$315 budget for v1.0 M2.**

### E.8 — Velocity forecast under human-in-loop Gemini

Human-in-loop cycle cost model:
- **Gemini prompt preparation (Claude):** 2–10 min per batch.
- **Native copy-paste into Gemini web + wait for response:** 5–15 min per batch depending on response length.
- **Native paste response to filesystem:** 2 min.
- **Claude reconciler pass:** 1–5 min.
- **Per-batch total: ~15–30 min wall clock.**

| Phase | Gemini batches | Wall clock (human-in-loop) | Net session count |
|-------|---------------|----------------------------|-------------------|
| B.0 | 0 | ~2h infra work | 1 session |
| B.1 | 0 | ~3h coding | 1 session |
| B.2 | 0 | ~6h coding (chunker per doc-type) | 2 sessions |
| B.3 | 0 | ~3h | 1 session |
| B.3.5 | 4 (CGM edge batches) | ~2h Gemini + ~3h coding | 1 session |
| B.4 | 6 (edge type batches) | ~3h Gemini + ~4h coding | 2 sessions |
| B.5 | 12 (patterns×3, resonances×3, clusters×2, contradictions×4) | ~6h Gemini + ~6h coding | 3 sessions |
| B.6 | 0 | ~4h | 1 session |
| B.7 | 2 (router eval) | ~1h Gemini + ~3h coding | 1 session |
| B.8 | 0 | ~3h | 1 session |
| B.9 | 4 (red-team against eval) | ~2h Gemini + ~4h coding | 1 session |
| B.10 | 6 (adversarial red-team) | ~3h Gemini + ~4h coding | 1 session |
| **Total** | **~34 Gemini batches** | **~17h Gemini wall + ~45h coding** | **~15 sessions** |

Calendar: at 1 session/day, **~3 weeks**. At every-third-session red-team (sessions 3, 6, 9, 12, 15 slip by one day each): **~4 weeks**. At real-life variable cadence: **4–6 weeks**.

### E.9 — P9 "structural reproducibility" tolerance specification

Per B.2.9, bit-reproducibility is impossible due to LLM non-determinism. **Structural reproducibility with documented tolerance** defined as:

Given the same input bundle (same chunk IDs, same scores, same retrieval ordering), the same prompt version, and the same model version, two runs must produce outputs satisfying:

| Dimension | Tolerance | Enforcement |
|-----------|-----------|-------------|
| Artifact ID collisions | 100% identical IDs across runs (IDs derived deterministically from content hash, not LLM) | Hash-based ID generator; zero variance |
| Confidence level | ±1 level (LOW↔MED or MED↔HIGH acceptable; LOW↔HIGH requires re-review) | Range check in validator |
| Citation set (fact_ids, signal_ids) | ≥85% Jaccard overlap | Validator measures; flag <85% for human review |
| Three interpretations (when P7 active) | Semantic similarity ≥0.75 on pairwise cosine of embedded interpretations | Voyage embeds interpretations; measure |
| Principle violations flagged | 100% identical set (deterministic once validators are built) | Direct set comparison |
| Accept/reject decision | Same decision; rationale may vary in wording | Decision match required; rationale stored verbatim |

**Tolerance reporting:** Every ledger event records the structural-reproducibility check result if the artifact has a prior event with same (input_bundle_hash, prompt_version, model_version) tuple.

**Out-of-tolerance handling:** Flagged in `LEDGER/reproducibility_failures.jsonl`. Native notified at phase close. Counts against phase acceptance if >5% of artifacts fail.

---

## F. Learning Layer Hooks (M2 substrate, no algorithms)

### F.1 — Hook 1: `06_LEARNING_LAYER/` scaffolded in B.0

Substrate only. Zero algorithms. Zero parameters updated.

```
06_LEARNING_LAYER/
├── README.md                          # what this is; why substrate-only in M2; M4+ activation plan
├── CALIBRATION_TABLES/
│   └── .gitkeep                       # empty; populated at M4
├── PROMPT_REGISTRY/
│   └── INDEX.json                     # v0.1 schema; populated by Hook 3 across all phases
├── PREDICTION_LEDGER/
│   ├── prediction_ledger.jsonl        # Hook 2; empty until first forward-looking claim
│   └── schema_v0_1.json
├── PARAMETER_STORE/
│   └── .gitkeep                       # empty; populated at M4+
├── SHADOW_OBSERVATIONS/
│   └── .gitkeep                       # empty; M4+ substrate for shadow-mode parameter proposals
└── SCHEMAS/
    ├── prediction_schema_v0_1.json
    └── prompt_registry_schema_v0_1.json
```

M2 responsibility: create the tree, populate only `PROMPT_REGISTRY/INDEX.json` and `PREDICTION_LEDGER/prediction_ledger.jsonl`. Everything else stays empty.

### F.2 — Hook 2: Prediction ledger

**Activation trigger:** the moment the discovery engine emits its first forward-looking falsifiable claim. That moment occurs in B.5 (discovery phase) or earlier if a pattern/resonance contains a time-indexed falsifier.

**Rule:** a discovery artifact with no falsifier cannot be classified as forward-looking. Enforced by P8 validator extension.

**Schema (v0.1, minimal; evolves at M4):**

```json
{
  "prediction_id": "PRED.nnn",
  "artifact_id": "PATTERN.042 | RESONANCE.007 | CLUSTER.015 | CONTRA.003",
  "artifact_type": "pattern | resonance | cluster | contradiction",
  "claim_text": "<specific falsifiable statement>",
  "domain": "career | wealth | health | relationships | children | spiritual | parents | mind | travel | meta",
  "verification_window_start": "YYYY-MM-DD",
  "verification_window_end": "YYYY-MM-DD",
  "falsifier_conditions": [
    "<condition 1 that would prove the claim false>",
    "<condition 2>"
  ],
  "confirmation_conditions": [
    "<what would count as confirmation>"
  ],
  "outcome": null,
  "outcome_source": null,
  "outcome_recorded_at": null,
  "created_at": "ISO-8601",
  "created_by_event_id": "<ledger event_id>",
  "ledger_ref": "06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl:line_n",
  "classical_basis": "<optional classical authority cited>",
  "confidence_at_creation": "LOW | MED | HIGH",
  "dependencies": ["<other PRED.nnn if this rests on another prediction>"]
}
```

Append-only. `outcome`, `outcome_source`, `outcome_recorded_at` left null until M6 (prospective testing) activates. M2 never fills them.

**Substrate behavior during M2:** the writer exists; rows are appended when discovery yields forward-looking claims; no reading back, no algorithms.

### F.3 — Hook 3: Prompt registry, version-tagged from day one

Every prompt file in `035_DISCOVERY_LAYER/PROMPTS/` and `platform/python-sidecar/rag/prompts/` carries:
- Version in filename: `pattern_mining_v1_0.md`, `reconciler_v1_3.md`.
- Frontmatter hash: sha256 of file body, recorded at commit time.

Every ledger event references:
- `prompt_ref`: path to file
- `prompt_version`: semver
- `prompt_hash`: sha256

The **PROMPT_REGISTRY/INDEX.json** (in `06_LEARNING_LAYER/PROMPT_REGISTRY/`) accumulates:

```json
[
  {
    "prompt_id": "gemini.pattern_mining",
    "version": "1.0",
    "path": "035_DISCOVERY_LAYER/PROMPTS/gemini/pattern_mining_v1_0.md",
    "hash": "sha256:...",
    "introduced_at": "ISO-8601",
    "deprecated_at": null,
    "event_count": 0,
    "performance_metrics": {}
  }
]
```

`event_count` and `performance_metrics` remain at zero / empty during M2. They become live at M4 when prompt optimization starts. Substrate only.

### F.4 — Discipline boundary

The three hooks are **substrate only in M2**. No learning algorithms fire. Specifically:
- No signal-weight updates.
- No graph-edge-weight learning.
- No embedding-space adaptation beyond the fixed Voyage model.
- No prompt-optimization loop.
- No Bayesian updates.
- No counterfactual learning.

All ten learning mechanisms per Macro Plan activate at M4 or later. M2's only contribution is the data substrate for them.

---

## G. Expanded Phase Plan (B.0 → B.10)

Each phase includes: objective, inputs, tasks, artifacts, two-pass ordering (per §E.5), acceptance criteria, cost/velocity (from §E.7/E.8), stop-markers that might fire.

### Phase B.0 — Foundations (1 session)

**Objective.** Infrastructure ready; `035_DISCOVERY_LAYER/`, `06_LEARNING_LAYER/` scaffolded; Supabase migration applied; dependencies installed. No LLM work.

**Inputs.** Native approval of directory renumbering (§E.1). Resolution of GAP.13 or decision to defer it.

**Tasks.**
1. Implement GAP.13 resolution (8-karaka lock). Create `00_ARCHITECTURE/GAP_13_RESOLUTION_v1_0.md` detailing the 8-karaka lock, the rule preserving 7-karaka as a formal alternative for Pitrukaraka-dependent claims per P7, and an enumerated list of Pitrukaraka-dependent signals in `MSR_v3_0.md`. The document must carry explicit layer tags: karaka sequence assertion tagged `[L1 source: FORENSIC_v8_0 §<section>]`; P7 alternative rule tagged `[L2+ policy: interpretive]`; signal enumeration references signal IDs from `MSR_v3_0.md`. Append the string "7-karaka-alternative" to those specific signals in `MSR_v3_0.md`. Sub-task: archive `025_HOLISTIC_SYNTHESIS/MSR_v1_0.md` and `025_HOLISTIC_SYNTHESIS/MSR_v2_0.md` to `99_ARCHIVE/` to eliminate version ambiguity; `MSR_v3_0.md` is the sole operationally active MSR.
2. Create directories: `035_DISCOVERY_LAYER/` (with full tree per §B.3 + QUERY_TAXONOMY subdir), `06_LEARNING_LAYER/` (per §F.1).
3. Run pre-migration file-and-line-count check on `06_QUERY_INTERFACE/*`. Also run `platform/scripts/citation_graph_builder.py` against the current corpus and emit `verification_artifacts/RAG/baseline_edge_count.json` recording the pre-migration deterministic edge count (this fixes the B.4 acceptance criterion baseline before QUERY_INTERFACE migration can alter citation counts).
4. Move `06_QUERY_INTERFACE/*` → `035_DISCOVERY_LAYER/QUERY_TAXONOMY/`. Flag any stale-era content to `STALENESS_REGISTER.md` instead of silently migrating.
5. Run post-migration file-and-line-count check. Delete `06_QUERY_INTERFACE/` only after verification.
6. Add dependencies to `platform/python-sidecar/requirements.txt`: voyageai, anthropic, openai (fallback), tiktoken, networkx≥3.2, pyyaml, sqlalchemy≥2.0, psycopg[binary]≥3.2, pgvector≥0.3.0, ragas≥0.2.0, pytest, jsonschema.
7. Create Supabase migration `005_pgvector_rag_schema.sql`: enable `vector`; tables `rag_chunks`, `rag_embeddings`, `rag_graph_nodes`, `rag_graph_edges`, `rag_queries`, `rag_retrievals`, `rag_feedback`, `rag_reproducibility_failures`; HNSW + GIN + btree indexes.
8. Create `.env.rag.example`: `VOYAGE_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `SUPABASE_SERVICE_ROLE_KEY`.
9. Scaffold `platform/python-sidecar/rag/` package skeleton (empty modules with docstrings).
10. Scaffold `06_LEARNING_LAYER/` tree + `prediction_ledger.jsonl` (empty) + schema files v0.1.
11. Scaffold `035_DISCOVERY_LAYER/PROMPTS/` empty per Hook 3 filename convention.
12. Create `035_DISCOVERY_LAYER/SCHEMAS/chunker_spec_v1_0.md` specifying for each of the 6 chunker doc-types: (a) chunk unit definition, (b) required metadata fields, (c) boundary detection method, (d) maximum token limit enforcement, (e) stale metadata propagation rule. See §G B.2 Chunker Specification for the enumerated doc-types. B.2 tasks reference this spec.
13. Implement `platform/python-sidecar/rag/prompt_registry.py` with function `register_prompt(path: str, version: str) -> PromptRegistryEntry`. This function reads the prompt file, computes sha256 of body, writes/updates `06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json`, and returns the entry for inline use in ledger events. B.0 smoke-test: register a single empty prompt placeholder and verify INDEX.json is updated. Population deferred to Phase B.4+ when actual prompts are authored.
14. Author golden query sets: (a) 20 router classification queries with expected QueryPlan classifications — saved to `verification_artifacts/RAG/golden_router_queries_v1_0.json`; (b) 50 eval queries with expected retrieval signals — saved to `platform/python-sidecar/rag/eval/golden.jsonl`. Curate to stress-test Whole-Chart-Read enforcement, UCN-vs-L3 contradiction surfacing, and time-gated falsifier handling. A fresh executor must not need to regenerate these sets.
15. Append session log entry.

**Artifacts.**
- `00_ARCHITECTURE/GAP_13_RESOLUTION_v1_0.md`
- `platform/supabase/migrations/005_pgvector_rag_schema.sql`
- `platform/python-sidecar/requirements.txt` (updated)
- `platform/python-sidecar/rag/` (empty package)
- `platform/python-sidecar/rag/prompt_registry.py`
- `035_DISCOVERY_LAYER/` (directory tree)
- `035_DISCOVERY_LAYER/SCHEMAS/chunker_spec_v1_0.md`
- `06_LEARNING_LAYER/` (directory tree with Hook 1 substrate)
- `.env.rag.example`
- `verification_artifacts/RAG/baseline_edge_count.json`
- `verification_artifacts/RAG/golden_router_queries_v1_0.json`
- `platform/python-sidecar/rag/eval/golden.jsonl` (initial 50 queries)
- `00_ARCHITECTURE/SESSION_LOG.md` (append B.0 close)

**Two-pass ordering.** None — deterministic infra.

**Acceptance criteria.**
- `GAP_13_RESOLUTION_v1_0.md` exists with frontmatter, resolution statement, layer tags, and enumerated signal list; grep of `MSR_v3_0.md` for "7-karaka-alternative" returns exactly the count enumerated in the resolution file; `MSR_v1_0.md` and `MSR_v2_0.md` are absent from `025_HOLISTIC_SYNTHESIS/` (confirmed moved to `99_ARCHIVE/`).
- `verification_artifacts/RAG/baseline_edge_count.json` exists and records the pre-migration deterministic edge count.
- `pip install -r requirements.txt` succeeds in clean venv.
- Supabase migration applies locally.
- `SELECT * FROM pg_extension WHERE extname='vector'` returns a row.
- All scaffolded directories present; `tree 035_DISCOVERY_LAYER 06_LEARNING_LAYER` matches spec.
- `06_QUERY_INTERFACE/` no longer exists; contents present at `035_DISCOVERY_LAYER/QUERY_TAXONOMY/`.
- PREDICTION_LEDGER/prediction_ledger.jsonl exists and is empty (0 lines).

**Cost.** $0. **Velocity.** 1 session.

**Stop-markers that might fire.** `[NATIVE_CONFIRMATION_NEEDED]` for directory renumbering (pre-phase).

---

### Phase B.1 — Ingestion + Staleness Register (1 session)

**Objective.** Corpus parsed into typed Document model; Staleness Register populated; ingestion manifest emitted.

**Inputs.** `FILE_REGISTRY_v1_0.md`, all corpus `.md` files, FORENSIC_v8_0.

**Tasks.**
1. `platform/python-sidecar/rag/ingest.py` — `scan_corpus(root)` walks repo; excludes `99_ARCHIVE/`, `node_modules/`, `platform/src/`. Cross-references FILE_REGISTRY. Tags every Document with layer, doc_type, version, supersedes, is_current, frontmatter.
2. `platform/python-sidecar/rag/models.py` — Pydantic: `Document`, `Chunk`, `Signal`, `Fact`, `GraphNode`, `GraphEdge`, `RegisterEntry`, `LedgerEvent`.

**Task 1.5.** Implement and meta-test `rag/validators/p1_layer_separation.py`, `rag/validators/p2_citation.py`, and `rag/validators/p5_signal_id_resolution.py`. These three validators must pass all meta-tests before Phase B.2 begins — P1, P2, and P5 are required to gate every chunk write in B.2. Meta-test requirements: P1: 3 reject fixtures (interpretive claim in L1 chunk, no layer tag, mixed claim without bridging marker) + 2 accept fixtures; P2: 2 reject fixtures (no `v6_ids_consumed` field, non-existent ID in v8.0) + 2 accept fixtures; P5: 2 reject fixtures (non-existent signal ID) + 2 accept fixtures. Run: `pytest platform/python-sidecar/rag/validators/test_p1_p2_p5.py` must pass before B.2 begins.

3. `00_ARCHITECTURE/STALENESS_REGISTER.md` — enumerate each L3 file, record `version_aligned_with` (FORENSIC_v6_0 | v8_0 | partial), mark stale where ≠ v8_0.
4. Emit `verification_artifacts/RAG/ingestion_manifest.json`.
5. Record first prompt-registry entries (none yet; registry still empty).

**Artifacts.**
- `platform/python-sidecar/rag/ingest.py`
- `platform/python-sidecar/rag/models.py`
- `00_ARCHITECTURE/STALENESS_REGISTER.md`
- `verification_artifacts/RAG/ingestion_manifest.json`

**Two-pass ordering.** None — deterministic parse. Staleness Register is Claude-authored based on deterministic version comparison.

**Acceptance criteria.**
- Manifest count matches `FILE_REGISTRY_v1_0.md` `is_current=true` count at phase-start snapshot. Record the actual count from FILE_REGISTRY_v1_0 in the B.0 session log entry and use that count as the B.1 acceptance target (removes the imprecise "~46" from this criterion).
- Every Document has non-null `layer`.
- Staleness Register lists the four known-stale L3 reports (per Macro Plan §M1) + any others detected.
- All 499 MSR signals parseable.

**Cost.** $0. **Velocity.** 1 session.

---

### Phase B.2 — Chunking (2 sessions)

**Objective.** Corpus converted to ~1,200 layer-tagged, type-tagged, schema-validated chunks. Highest-risk phase for retrieval quality.

**Chunker Specification.** The full per-doctype specification lives at `035_DISCOVERY_LAYER/SCHEMAS/chunker_spec_v1_0.md` (authored in B.0 Task 12). The six doc-types and their boundary rules are:

| # | Doc-type | Chunk unit | Boundary detection | Max tokens | Notes |
|---|----------|------------|--------------------|-----------|-------|
| 1 | MSR signals (`MSR_v3_0.md`) | One signal entry (SIG.nnn block) | YAML signal-ID boundary (`^SIG\.\d+:`) | 800 | Each chunk carries signal_id, layer (L2.5), domain, confidence; `is_stale` from Staleness Register |
| 2 | UCN sections (`UCN_v4_0.md`) | One H2 Part section | Markdown H2 (`^## Part`) | 1500 | Each chunk carries part_id, layer (L2.5), doc_type=UCN; P3 enforcement depends on these chunks |
| 3 | CDLM cells (`CDLM_v1_1.md`) | One grid cell (row × column intersection) | Grid-cell regex on table rows | 400 | Each chunk carries row_domain, col_domain, layer (L2.5); P3 enforcement depends on these chunks |
| 4 | L1 fact groups (`FORENSIC_ASTROLOGICAL_DATA_v8_0.md`) | One fact-section group | Markdown H2/H3 section boundary | 1000 | Each chunk carries fact_group_id, layer (L1), source=FORENSIC_v8_0 |
| 5 | Domain report Parts (`03_DOMAIN_REPORTS/*.md`) | One report Part (H2 Part boundary) | Markdown H2 (`^## Part`) | 1500 | Each chunk carries report_name, part_id, layer (L3); `is_stale` propagated from Staleness Register |
| 6 | CGM nodes (`CGM_v9_0.md`, after B.3.5) | One CGM node entry (node property dict) | Node-ID boundary in CGM structure | 600 | Each chunk carries node_id, node_type, layer (L2.5); CGM chunker runs post-B.3.5 (see B.3.5 Task 5.5) |

**Tasks.** Implement per-doctype chunkers for all 6 types above per `chunker_spec_v1_0.md`. Plus:
- Each chunk's metadata includes `is_stale`, `stale_reason`, `stale_since` — pulled from Staleness Register.
- Every chunk validated against `Chunk` Pydantic model pre-write.
- P1, P2, P5 validators gate every chunk write (implemented in B.1 Task 1.5).
- Stored in `rag_chunks` Supabase table.
- Emit `verification_artifacts/RAG/chunking_report.json` with per-doctype counts + token distributions + stale count.

**Two-pass ordering.** None — deterministic code. Opus validation pass on 10 sampled chunks as QA only.

**Acceptance criteria.** Exactly 499 signal chunks (doc-type 1); zero cross-layer chunks; no chunk >2000 tokens; stale chunks count matches Staleness Register; ≥1 UCN chunk per major UCN Part section; ≥1 CDLM chunk per grid cell; CGM node chunks deferred to post-B.3.5 re-run (see B.3.5 Task 5.5).

**Cost.** ~$1 (Opus QA). **Velocity.** 2 sessions.

---

### Phase B.3 — Embedding & Vector Indexing (1 session)

**Objective.** All chunks embedded with Voyage-3-large; HNSW index populated; sanity retrieval works.

**Tasks.**
- `platform/python-sidecar/rag/embed.py` — Voyage batch calls, pre-embedding text enrichment (layer + chunk_type + entities prefix), idempotent content-hash skip.
- **Fallback policy (per B.2.2):** OpenAI only at index time, never at query time. If Voyage down at query time, return `[RETRIEVAL_UNAVAILABLE]` stop-marker. Dual-indexing deferred (cost vs benefit not justified for v1.0).
- **Index-time halt policy:** If Voyage API returns an error on any batch during B.3 indexing, the run HALTS with `[RETRIEVAL_UNAVAILABLE]` and logs unindexed chunk IDs to `verification_artifacts/RAG/unindexed_chunks.jsonl`. No OpenAI fallback at index time. Re-attempt when Voyage is available. Reason: OpenAI-indexed chunks in a Voyage-indexed store create a silently-mixed embedding space undetectable at query time (orphaned chunks).
- HNSW index creation via migration or direct SQL.
- Sanity test: query "Saturn 7th house Libra" returns expected top-3.

**Two-pass ordering.** None — deterministic embed API.

**Acceptance criteria.** ~1,200 embeddings; HNSW p95 query <50ms; sanity query passes.

**Cost.** ~$0.25. **Velocity.** 1 session.

---

### Phase B.3.5 — CGM Rebuild on v8.0 (1 session; micro-phase per CQ5=b)

**Objective.** Produce `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` aligned with FORENSIC_v8_0. Archive CGM_v2_0 to `99_ARCHIVE/`.

**Tasks.**
1. Read CGM_v2_0 structure (node types, edge types, conventions).
2. Regenerate node assertions from L1 v8.0 + matrices. (Positions, lordships, occupations, dignities, karakas fixed at 8-karaka. Ensure 7-karaka reading is preserved as a formal alternative for Pitrukaraka-dependent nodes per P7).
3. Regenerate edge assertions.
3.5. Author `035_DISCOVERY_LAYER/PROMPTS/gemini/cgm_edge_proposals_v1_0.md`. Prompt structure: ROLE (promiscuous connector, pass 1), TASK (propose additional CGM edges beyond the deterministic set from Tasks 2–3), INPUT (node list, existing edge types, L1 basis for proposed nodes), OUTPUT (strict YAML: `proposed_edges: [{source_node, edge_type, target_node, L1_basis, classical_basis_if_applicable, confidence_prior}]`), CONSTRAINTS (cite only from L1 v8.0; no invented positions; flag `[EXTERNAL_COMPUTATION_REQUIRED]` if uncertain). Register prompt in PROMPT_REGISTRY via `prompt_registry.py` before use.
4. **Two-pass.** Gemini proposes any additional edges (e.g., subtle aspect relationships, Chalit shifts) from the L1 base using the prompt from Task 3.5; Claude reconciles against v8.0 invariants (run the invariant scanner p1/p2/p5). Store Gemini response at `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B3-5_batch<N>_raw.md` before Claude reconciler reads it. Record path in ledger event `gemini_response_ref` field.
5. Write `CGM_v9_0.md` with full frontmatter + changelog vs v2_0.
5.5. Re-trigger the CGM chunker (doc-type 6 per `chunker_spec_v1_0.md`) against `CGM_v9_0.md` to generate CGM node chunks in `rag_chunks`. Verify: CGM node chunk count = CGM_v9_0 node count.
6. Update FILE_REGISTRY.

**Artifacts.**
- `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md`
- `99_ARCHIVE/CGM_v2_0.md`
- `00_ARCHITECTURE/FILE_REGISTRY_v1_0.md` (updated)
- `035_DISCOVERY_LAYER/PROMPTS/gemini/cgm_edge_proposals_v1_0.md`
- `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/` (Gemini raw response files)

**Two-pass ordering.** Gemini → Claude for edge additions. Pure computation (positions) is Claude-only.

**Acceptance criteria.** CGM_v9_0 passes P1/P2/P5 validators; all node positions match FORENSIC_v8_0; CGM node chunk count in `rag_chunks` = CGM_v9_0 node count.

**Cost.** ~$5. **Velocity.** 1 session.

**Stop-markers.** `[NATIVE_CONFIRMATION_NEEDED]` on GAP.13 if unresolved.

---

### Phase B.4 — Graph Construction (2 sessions)

**Objective.** Build the queryable graph. Nodes = chunks + fact_ids + signal_ids + domains. Edges = CITES, MENTIONS, AFFECTS_DOMAIN, CROSS_LINKS, SUPPORTS, CONTRADICTS.

**Tasks.**
1. `platform/python-sidecar/rag/graph.py` — NetworkX MultiDiGraph builder reusing `citation_graph_builder.py` regex patterns.
2. Seed deterministic edges (CITES from `v6_ids_consumed`, MENTIONS from signal-ID scans, AFFECTS_DOMAIN from `domains_affected`, CROSS_LINKS from CDLM cells).
3. **Two-pass.** Gemini proposes candidate SUPPORTS edges (signal → UCN section) and potential CONTRADICTS edges from textual tension in the corpus; Claude reconciles.
4. Persist to `rag_graph_nodes`, `rag_graph_edges`. Export adjacency JSON to `verification_artifacts/RAG/graph.json`.
5. Helper library: `expand_neighbors`, `shortest_path`, `domain_cross_links`.

**Two-pass ordering.** Gemini → Claude for SUPPORTS edges. Claude → Gemini for CONTRADICTS edges (per §E.5). Gemini response files stored at `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B4_batch<N>_raw.md` before Claude reconciler reads them. Path recorded in ledger event `gemini_response_ref` field.

**Acceptance criteria.**
- Node count = chunks + unique fact_ids + unique signal_ids + 9 domains.
- Deterministic edges ≥ count recorded in `verification_artifacts/RAG/baseline_edge_count.json` (pre-migration baseline set in B.0 Task 3).
- SUPPORTS edges: at least one per L3 report.
- Zero dangling edges.
- Ledger contains two-pass events for every Gemini-proposed edge.
- Each Gemini-batch ledger event has a `gemini_response_ref` pointing to an existing raw response file in `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/`.

**Cost.** ~$20. **Velocity.** 2 sessions.

---

### Phase B.5 — Discovery Engine (3 sessions)

**Objective.** Produce the four registers with two-pass trails. This is the heart of the build.

**Tasks (parallel within phase):**

**Task 0 (pre-mining gate).** Before beginning any discovery mining: (a) implement and test `rag/prediction_ledger.py` with `append_prediction(entry: Prediction)` method and append-only file writes; (b) implement and test the P8 validator extension: any artifact marked as forward-looking must have a non-null `falsifier_conditions` field; (c) implement and test the P7 validator (significance-gated three-interpretation check). Run `pytest platform/python-sidecar/rag/validators/` — all validators (P1–P9, including P7/P8 extensions) must pass before proceeding. Also: implement `ledger.py`'s `get_acceptance_rate(batch_id)` function; initialize `verification_artifacts/RAG/batch_acceptance_rates.json`.

**Pattern mining.**
1. Enumerate candidate pattern seeds from graph (signal co-occurrence sets, domain-spanning subgraphs, dasha-windowed signal clusters).
2. Gemini pass: propose pattern hypotheses with mechanism, counter-cases, classical basis, alternatives.
3. Claude pass: validate each candidate against P1–P9. Assign status + confidence.
4. Write to `PATTERN_REGISTER_v1_0.md` + `.json` mirror.

**Resonance walk.**
5. Graph traversal across domain-boundary edges (CDLM extensions).
6. Gemini: propose cross-domain resonances beyond CDLM explicit cells.
7. Claude: reconcile.
8. Write to `RESONANCE_REGISTER_v1_0.md` + `.json`.

**Contradiction scan.**
9. Claude's invariant scanner runs P1/P2/P5 deterministic checks across all chunks → contradiction flags. Also compares L3 domain claims against UCN for P6 conflicts.
10. Flag Rahu-as-PK findings where empirical behavior would invert under 7-karaka reading as a specific candidate class.
11. Gemini: for each flag, propose reconciliation candidates (accept / reject / defer with rationale).
12. Claude: validate Gemini's reconciliations.
13. Write to `CONTRADICTION_REGISTER_v1_0.md` + `.json`.

**Cluster annotation.**
13. KMeans/HDBSCAN over Voyage embeddings of L2.5 signal chunks only (filter to signals).
14. Gemini: annotate each cluster per §E.4 prompt.
15. Claude: validate + assign status.
16. Write to `CLUSTER_ATLAS_v1_0.md` + `.json`.

**Prediction-ledger integration (Hook 2 live).**
17. Any register entry containing a time-indexed falsifiable claim triggers a row in `06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl`. P8 validator extension enforces "no falsifier → cannot be classified forward-looking".

**Mid-phase gate.** After the first 5 patterns are validated: run `rag/eval/run_eval.py --mode=discovery_sanity --seed_set=5` against 5 seeded known facts (authored as part of B.5 setup). Seed recall must be ≥ 0.8 on the 5 seeds before proceeding to full discovery mining. This is NOT the full B.9 eval harness — it is an early pipeline-health check. Full eval harness with 50 golden queries remains in B.9.

**Acceptance-rate monitoring.** After each Gemini batch, compute acceptance rate via `ledger.get_acceptance_rate(batch_id)` and log to `verification_artifacts/RAG/batch_acceptance_rates.json`. If rate < 15% or > 80%, emit `[ACCEPTANCE_RATE_ANOMALY]` and surface to native before proceeding to the next batch.

**Gemini response files.** Store all Gemini raw responses at `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/YYYY-MM-DD_B5_batch<N>_raw.md` before Claude reconciler reads them. Path recorded in ledger event `gemini_response_ref` field.

**Two-pass ordering.** Mixed per §E.5 table.

**Acceptance criteria.**
- At least 20 validated patterns, 10 validated resonances, 5 validated contradictions, 10 annotated clusters (minimum bar for v1.0).
- Every entry has complete two-pass trail in ledger.
- Every forward-looking claim has a prediction_ledger row.
- Zero validated entries violate any P1–P9.
- 100% entries structurally reproducible per §E.9 tolerance.
- Each Gemini-batch ledger event has a `gemini_response_ref` pointing to an existing raw response file.

**Cost.** ~$55. **Velocity.** 3 sessions (includes a mid-phase red-team pass).

**Stop-markers.** `[NATIVE_CONFIRMATION_NEEDED]` on any discovery entry the reconciler flags for review.

---

### Phase B.6 — Hybrid Retrieval Library (1 session)

**Objective.** Build the retrieval library that both the discovery engine (re-run) and the thin query UI consume.

**Tasks.** Vector + BM25 + graph-walk + RRF + Voyage rerank + layer-balance. Exposed as a Python library (`platform/python-sidecar/rag/retrieve.py`). Plus TypeScript shim (`platform/src/lib/rag/retrieveClient.ts`) that calls the FastAPI endpoint.

**Two-pass ordering.** None — deterministic retrieval code. Opus eval-set tests are single-pass QA.

**Acceptance criteria.** Golden retrieval set (20 seed queries) achieves precision@10 ≥ 0.7, recall@10 ≥ 0.6. Layer balance invariant holds.

**Cost.** ~$2. **Velocity.** 1 session.

---

### Phase B.7 — Router + Plan Library (1 session)

**Objective.** Plan-based interface. Router is Opus 4.7 (per CQ6). Classifies incoming queries into QueryPlan objects; plans are the primary interface, free-text fallback only.

**Tasks.**
1. `platform/python-sidecar/rag/router.py` — Opus-based classifier + structured-output parsing.
2. Plan taxonomy in `035_DISCOVERY_LAYER/QUERY_TAXONOMY/plans_v1_0.md`.
3. `035_DISCOVERY_LAYER/PROMPTS/claude/router_v1_0.md` prompt file.
4. Classification examples JSON from migrated `06_QUERY_INTERFACE/` contents.
5. Whole-Chart-Read enforcer: interpretive_* classes auto-include UCN + CDLM chunks.
6. **Router availability fallback.** If Opus 4.7 is unavailable (API outage, model deprecation), route all incoming queries to a static fallback QueryPlan: `{type: 'exploratory', significance: 0.5, domains: ['all']}`. Log the degraded routing event to ledger with `actor=static_fallback`. Do NOT fall back to a different model — Opus 4.7 is intentionally specified and a different model would produce incomparable plan taxonomies unauditable against logged plans.

**Two-pass ordering.** None — router is single-pass Opus.

**Acceptance criteria.** 20 golden router queries correctly classified (manual review). Whole-Chart-Read invariant: 100% of interpretive_* bundles include ≥1 UCN chunk.

**Cost.** ~$5. **Velocity.** 1 session.

---

### Phase B.8 — Synthesis Layer (1 session)

**Objective.** Layer-aware synthesis; derivation ledger inline; confidence + three-interpretation gate.

**Tasks.** As v1 plan §B.7 (preserved). Synthesis runs only for validation UI queries, not the discovery engine (discovery has its own register-writing pipeline).

**Two-pass ordering.** None — single-pass Opus synthesis with validator gate.

**Acceptance criteria.** 10 golden queries: 10/10 have complete derivation ledger; 5/5 significance-flagged queries produce three interpretations; zero out-of-bundle signal references.

**Cost.** ~$5. **Velocity.** 1 session.

---

### Phase B.9 — Evaluation Harness (1 session; includes red-team pass)

**Objective.** Eval suite runs end-to-end with documented metrics.

**Tasks.** As v1 plan §B.8 (preserved). Plus:
- **Discovery-engine eval harness:** seeded known facts (must be re-found), seeded contradictions (must be caught), seeded false patterns (must be rejected).
- Golden query set size 50.
- Red-team probes (6 from §I below) run.
- Results to `verification_artifacts/RAG/eval_baseline.json`.

**Two-pass ordering.** Claude → Gemini for adversarial red-team extension (per §E.5).

**Acceptance criteria.** precision@10 ≥0.7, recall@10 ≥0.6, faithfulness ≥0.85, hallucination ≤5%, discovery-eval seed recall ≥0.9, seeded false patterns rejected 100%.

**Cost.** ~$20. **Velocity.** 1 session.

---

### Phase B.10 — Red-Team + Thin UI + Handoff (1 session)

**Objective.** Final adversarial pass; validation UI live at `/dashboard/ask`; RAG_READINESS_REPORT_v1_0 signed off.

**Tasks.**
1. Run all 6 red-team probes (§I).
2. Build minimal Next.js UI per v1 plan §B.9 (reduced scope: answer panel, derivation ledger, bundle inspector, confidence badge — no feedback thumbs beyond a simple "flag for review" button).
3. Add UI routes: `/dashboard/discoveries` (browse registers), `/dashboard/ask` (validation queries).
4. Generate `verification_artifacts/RAG/RED_TEAM_v1_0.md` + `RAG_READINESS_REPORT_v1_0.md`.
5. Corpus version tag v2.0; SESSION_LOG close entry.

**Two-pass ordering.** Claude → Gemini for red-team probes (per §E.5).

**Acceptance criteria.** All 6 probes produce correct behavior; eval metrics at or above baseline; native runs 10 queries end-to-end and confirms acharya-grade; no prediction_ledger rows are missing falsifier.

**Cost.** ~$10. **Velocity.** 1 session.

---

## H. P1–P9 Validator Specifications

See §E.6 for test-fixture summary. Implementation detail deferred to phase B.0 where `platform/python-sidecar/rag/validators/` package is created; each validator becomes implemented in the phase where its principle first applies (B.1 for P1/P2, B.5 for P7/P8, etc.). All validators exist and pass meta-tests by end of B.9.

Principle dependencies:
- P1, P2, P5 run at every chunk write, retrieval, and artifact write.
- P3 runs at every retrieval bundle assembly.
- P4 runs at every synthesis (detects fabricated computation tokens in LLM output).
- P6 runs at synthesis + at contradiction-scan.
- P7 runs at synthesis for significance ≥ 0.7.
- P8 runs at every artifact write (discovery registers + synthesis answers).
- P9 runs at reproducibility checks per §E.9.

**P6 degraded-mode policy.** The CONTRADICTION_REGISTER required for full P6 enforcement is produced in Phase B.5. Prior to that (phases B.1–B.4), P6 operates in degraded mode: if a synthesis answer cites only L3 domain content with no UCN citation, flag as `[P6_UNCHECKED]` rather than rejecting. Full P6 enforcement (semantic comparison against CONTRADICTION_REGISTER + UCN authority) activates at Phase B.8 synthesis, after B.5 register is available. Degraded-mode events are logged separately in the ledger (`p6_enforcement: degraded`) so they can be reviewed retroactively.

**P7 significance-scoring mechanism.** Significance score is a required field (`significance_score: float [0.0, 1.0]`) in the `QueryPlan` Pydantic model emitted by the router (Phase B.7). The router prompt instructs Opus to score significance based on: (a) number of domains affected by the query, (b) presence of timing or prediction language, (c) query type classification (timing > interpretive > factual). The P7 validator reads `significance_score` from the artifact's metadata field. A missing or out-of-range `significance_score` fails the P7 meta-test.

---

## I. Red-Team Probe Set (6 probes, v1.0)

1. **Layer-violation probe.** Query inducing fabrication of future dasha state. Must emit `[EXTERNAL_COMPUTATION_REQUIRED]`.
2. **Signal-invention probe.** "Tell me about Abhisek Yoga." Must refuse, not invent.
3. **Stale-L3 contamination probe.** Query whose best retrieval would include a stale L3 chunk. Retrieval must down-weight; reconciler output must cite the staleness marker.
4. **Whole-Chart-Read bypass probe.** Narrow-domain interpretive query. Bundle must contain UCN + CDLM chunks despite low semantic similarity.
5. **Contradiction-surface probe.** A query where UCN and a domain report disagree. Answer must flag the contradiction and prefer UCN (P6).
6. **Time-gated falsifier probe.** "Did BB-UL crystallization happen?" Must correctly report that the verification window is 2026-11-XX and no outcome yet; must NOT fabricate an outcome.

Each probe has a deterministic pass/fail criterion codified in the eval harness.

---

## J. Risks & Mitigations (discovery-primary refresh)

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| Chunking fragments a signal → derivation chain breaks | M | H | Per-doctype signal-boundary chunkers; sanity tests. |
| Vector retrieval surfaces wrong signals for entity-specific queries | M | H | BM25 ID boost + entity extraction + rerank. |
| Discovery register bloat (Gemini over-proposes, low acceptance rate) | H | M | §B.2.4 rolled-up ledger view; acceptance rate tracked per batch, threshold alerts at <15% or >80% (both suspicious). |
| Stale-L3 contamination | H | H | Staleness Register + down-weighted retrieval + reconciler-surfaced marker (§B.2.1). |
| Cross-vector-space fallback silently wrong | L | H | Index-time Voyage-only, query-time stop-marker instead of OpenAI fallback (§B.2.2). |
| Opus router cost creep | L | L | Budget ~$50/phase; reviewed at phase close; stop-marker if >$100/phase. |
| Human-in-loop Gemini bottleneck blocks velocity | M | M | Prompts designed as large batches; native can queue all Gemini work per session and reconcile asynchronously. |
| Hallucinated signals referenced in registers | M | C | P5 validator rejects; meta-test catches it. |
| Reproducibility failures exceed §E.9 tolerance | L | M | Logged to `reproducibility_failures.jsonl`; >5% fails phase acceptance. |
| Whole-Chart-Read bypassed | M | H | P3 validator hard-gates; red-team probe 4 verifies. |
| Learning Layer creep into M2 | L | M | Hook-only discipline (§F.4) enforced by plan; any learning algorithm proposal halted. |
| Prediction-ledger missing falsifier on forward-looking claim | M | H | P8 validator extension blocks classification. |
| GAP.13 unresolved at B.3.5 | L | M | Stop-marker; native decision required before CGM_v9_0 write. |
| Macro Plan drift (pre-building for M3+) | L | H | Scope boundary in §C; session log review at close. |
| B.4/B.5 reconciler context overrun (complex patterns require 8K–10K tokens, not 4K) | M | M | §E.7 budget raised to ~$315 (+75% buffer); monitor per-phase actual API spend; emit stop-marker if phase exceeds forecast +20%. |
| P6 degraded mode before CONTRADICTION_REGISTER: UCN-vs-L3 conflicts invisible during B.1–B.4 | M | M | §H degraded-mode policy logs all `[P6_UNCHECKED]` events; retroactive review required at B.5 before CONTRADICTION_REGISTER is closed; degraded-mode count tracked at phase close. |
| Gemini pass non-enforcement (executor labels Claude-authored proposal as `actor=gemini-web-<date>`) | L | H | Compensating control: each Gemini batch produces `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/<date>_batch_N_raw.md` committed to git. Existence + timestamp provides non-repudiation. P9 validator checks `gemini_response_ref` for every Gemini-authored ledger event. |

---

## K. File Manifest

**New directories (3):**
- `035_DISCOVERY_LAYER/` (with subtree)
- `06_LEARNING_LAYER/` (with subtree per §F.1)
- `platform/python-sidecar/rag/` (Python package)

**Retired directories (1):**
- `06_QUERY_INTERFACE/` → contents moved to `035_DISCOVERY_LAYER/QUERY_TAXONOMY/`.

**New files (explicit list):**

Python sidecar:
- `platform/python-sidecar/rag/__init__.py`
- `platform/python-sidecar/rag/models.py`
- `platform/python-sidecar/rag/schemas.py`
- `platform/python-sidecar/rag/ingest.py`
- `platform/python-sidecar/rag/chunk.py`
- `platform/python-sidecar/rag/chunkers/*.py` (6 files per doc-type)
- `platform/python-sidecar/rag/embed.py`
- `platform/python-sidecar/rag/graph.py`
- `platform/python-sidecar/rag/retrieve.py`
- `platform/python-sidecar/rag/router.py`
- `platform/python-sidecar/rag/discovery/patterns.py`
- `platform/python-sidecar/rag/discovery/resonances.py`
- `platform/python-sidecar/rag/discovery/contradictions.py`
- `platform/python-sidecar/rag/discovery/clusters.py`
- `platform/python-sidecar/rag/validators/p1_layer_separation.py` … `p9_audit_trail.py` (9 files)
- `platform/python-sidecar/rag/validators/fixtures/*.json` (accept + reject per principle)
- `platform/python-sidecar/rag/ledger.py`
- `platform/python-sidecar/rag/prediction_ledger.py`
- `platform/python-sidecar/rag/prompt_registry.py`
- `platform/python-sidecar/rag/eval/golden.jsonl`
- `platform/python-sidecar/rag/eval/discovery_seeds.jsonl`
- `platform/python-sidecar/rag/eval/run_eval.py`
- `platform/python-sidecar/rag/eval/red_team.py`

Next.js platform:
- `platform/src/lib/rag/synthesize.ts`
- `platform/src/lib/rag/prompts/synthesis.ts`
- `platform/src/lib/rag/validate.ts`
- `platform/src/app/api/rag/query/route.ts`
- `platform/src/app/api/rag/discoveries/route.ts`
- `platform/src/app/dashboard/ask/page.tsx`
- `platform/src/app/dashboard/discoveries/page.tsx`
- `platform/src/components/rag/*.tsx` (5 files)

Corpus artifacts:
- `035_DISCOVERY_LAYER/README.md`
- `035_DISCOVERY_LAYER/REGISTERS/PATTERN_REGISTER_v1_0.md` + `.json`
- `035_DISCOVERY_LAYER/REGISTERS/RESONANCE_REGISTER_v1_0.md` + `.json`
- `035_DISCOVERY_LAYER/REGISTERS/CONTRADICTION_REGISTER_v1_0.md` + `.json`
- `035_DISCOVERY_LAYER/REGISTERS/CLUSTER_ATLAS_v1_0.md` + `.json`
- `035_DISCOVERY_LAYER/REGISTERS/INDEX.json`
- `035_DISCOVERY_LAYER/LEDGER/` (daily JSONL + index + blobs)
- `035_DISCOVERY_LAYER/SCHEMAS/*.json` (5 schemas)
- `035_DISCOVERY_LAYER/PROMPTS/gemini/*_v1_0.md` (~8 prompts)
- `035_DISCOVERY_LAYER/PROMPTS/claude/*_v1_0.md` (~5 prompts)
- `035_DISCOVERY_LAYER/RED_TEAM/probes_v1.md`
- `035_DISCOVERY_LAYER/QUERY_TAXONOMY/*` (migrated from 06_QUERY_INTERFACE/)
- `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` (replaces v2_0)
- `99_ARCHIVE/CGM_v2_0.md`

Learning Layer (Hook substrate):
- `06_LEARNING_LAYER/README.md`
- `06_LEARNING_LAYER/PROMPT_REGISTRY/INDEX.json`
- `06_LEARNING_LAYER/PREDICTION_LEDGER/prediction_ledger.jsonl` (starts empty)
- `06_LEARNING_LAYER/SCHEMAS/prediction_schema_v0_1.json`
- `06_LEARNING_LAYER/SCHEMAS/prompt_registry_schema_v0_1.json`

Infrastructure:
- `platform/supabase/migrations/005_pgvector_rag_schema.sql`
- `platform/python-sidecar/requirements.txt` (updated)
- `.env.rag.example`

Architecture:
- `00_ARCHITECTURE/GAP_13_RESOLUTION_v1_0.md`
- `00_ARCHITECTURE/STALENESS_REGISTER.md`
- `00_ARCHITECTURE/FILE_REGISTRY_v1_0.md` (updated with new layer)
- `00_ARCHITECTURE/SESSION_LOG.md` (updated each phase close)

Verification:
- `verification_artifacts/RAG/ingestion_manifest.json`
- `verification_artifacts/RAG/chunking_report.json`
- `verification_artifacts/RAG/graph.json`
- `verification_artifacts/RAG/eval_baseline.json`
- `verification_artifacts/RAG/RED_TEAM_v1_0.md`
- `verification_artifacts/RAG/RAG_READINESS_REPORT_v1_0.md`
- `verification_artifacts/RAG/baseline_edge_count.json` (B.0; pre-migration deterministic edge count)
- `verification_artifacts/RAG/golden_router_queries_v1_0.json` (B.0; 20 router golden queries)
- `verification_artifacts/RAG/batch_acceptance_rates.json` (B.5; per-batch acceptance rate log)
- `verification_artifacts/RAG/unindexed_chunks.jsonl` (B.3; halt log if Voyage unavailable at index time)

Discovery Layer (additional):
- `035_DISCOVERY_LAYER/SCHEMAS/chunker_spec_v1_0.md` (B.0; 6 doc-type chunker specification)
- `035_DISCOVERY_LAYER/PROMPTS/gemini/cgm_edge_proposals_v1_0.md` (B.3.5; CGM edge-proposal prompt)
- `035_DISCOVERY_LAYER/PROMPTS/gemini/responses/` (all phases; Gemini raw response files at `YYYY-MM-DD_B<phase>_batch<N>_raw.md`)

**Reused utilities:**
- `platform/scripts/corpus_common.py` (extract_msr_signals, parse_yaml_block, normalize_sign)
- `platform/scripts/citation_graph_builder.py` (regex patterns)
- `platform/scripts/invariants_l1.py` (re-run pre-embedding)

---

## L. End-to-End Verification Plan

**Phase-gate checks (every phase close):**
1. All acceptance criteria for the phase met.
2. Session log updated with phase outcome.
3. Validator meta-tests pass (those applicable to the phase).
4. Reproducibility failures for the phase <5%.
5. Cost for the phase within forecast +20%.

**Integration smoke (after B.6):**
- `python -m rag.smoke "Saturn 7th house Libra"` → top-5 bundle, correct layer balance.

**End-to-end (after B.10):**
- Start sidecar + Next.js.
- Native asks 10 curated questions at `/dashboard/ask`.
- Native browses `/dashboard/discoveries` and manually reviews 5 random entries from each register.
- Derivation ledger present and traceable on every answer.
- Zero hallucinated signals.

**Regression guard:** Every future corpus artifact commit triggers re-ingestion + re-embedding.

---

## M. Timeline

| Week | Sessions | Phases closed | Red-team sessions |
|------|----------|---------------|-------------------|
| 1 | 1–3 | B.0, B.1, B.2 (part) | Session 3 red-team |
| 2 | 4–6 | B.2 finish, B.3, B.3.5 | Session 6 red-team |
| 3 | 7–9 | B.4, B.5 (part) | Session 9 red-team |
| 4 | 10–12 | B.5 finish, B.6, B.7 | Session 12 red-team |
| 5 | 13–15 | B.8, B.9, B.10 | Session 15 red-team = final probe |

**Total: 15 sessions, ~4–5 weeks at daily cadence.** Buffer to 6 weeks.

---

## N. Success Criteria for M2 v1.0 Sign-off

1. All B.0–B.10 acceptance criteria met.
2. ≥20 validated patterns, ≥10 resonances, ≥5 contradictions, ≥10 clusters — every entry with complete two-pass trail.
3. Eval metrics: precision@10 ≥0.7, recall@10 ≥0.6, faithfulness ≥0.85, hallucination ≤5%, discovery-seed recall ≥0.9.
4. All 6 red-team probes produce correct behavior.
5. Reproducibility failures <5% cumulative.
6. Learning-Layer hooks substrate in place; prediction ledger live; zero algorithms fired (discipline preserved).
7. Staleness Register complete; zero validated discovery entries depend exclusively on stale L3.
8. `CGM_v9_0.md` current and principle-compliant.
9. `RAG_READINESS_REPORT_v1_0.md` signed off by native.
10. `SESSION_LOG.md` reflects M2 closure; `MACRO_PLAN_v2_0.md` "current macro-phase" advanceable to M3.

Native's acharya-grade review on 10 self-chosen questions is the final gate. Anything reading as generic astrology fails sign-off.

---

## O. Pre-Execution Gating (Resolved)

The following `[NATIVE_CONFIRMATION_NEEDED]` items were surfaced and resolved on 2026-04-23:

1. **Directory numbering**: Adopted `035_DISCOVERY_LAYER/` (verified against `025_` pattern); retiring `06_QUERY_INTERFACE/` via strict pre/post line-count migration to `035_DISCOVERY_LAYER/QUERY_TAXONOMY/`; adopting `06_LEARNING_LAYER/`.
2. **GAP.13**: Resolved definitively as 8-karaka to avoid rebuild costs. 7-karaka readings preserved as formal P7 alternatives for Pitrukaraka claims. Rahu-as-PK inversions tracked as explicit contradiction class.

The plan is now un-gated and ready for execution starting with Phase B.0.
