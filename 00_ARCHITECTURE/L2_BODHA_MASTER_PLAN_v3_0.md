---
artifact: L2_BODHA_MASTER_PLAN_v3_0.md
canonical_id: L2_BODHA_MASTER_PLAN
version: 3.0
status: PLAN_FOR_NATIVE_REVIEW
authored_by: Cowork (planning) 2026-06-16
authored_for: native review → then Claude Code in Antigravity executes
supersedes: CLAUDECODE_BRIEF_BODHA_B1_FULL_PROJECTION_v1_0/v2.0 (folded in here, expanded)
data_plane: ALWAYS prod via Cloud SQL Auth Proxy (platform/scripts/start_db_proxy.sh, 127.0.0.1:5433)
native_chart_id: 482012f1-710e-4a25-994a-93821f5871aa
core_decisions_this_plan_encodes:
  - "DUAL-CAPTURE MODEL (native 2026-06-16): ga_structural is enriched to INGEST the 4 currently-missing
     L1 assets and derive their RELATIONAL value (staying L1, staying relational); bo_laksana (MSR) then
     projects from ALL L1 assets — ga_structural (relational) + the individual assets (native-grained) —
     so both the relational value AND each fact's individuality are captured. One-surface is NOT a goal;
     completeness + retrievability are."
  - "TRAP-1 GUARDRAIL (load-bearing): when ga_structural ingests another asset's fact, it stores ONLY the
     NEW relational fact it derives, referencing the source fact_id. It NEVER restates the source's bare
     value as its own row. Magnitude stays owned by ga_strength; the relationship is a new fact_id citing it."
  - "NO CURATION: the legacy 31-category allow-list in bo_laksana is DELETED. Projection is enumerated
     from LIVE chart_facts, never a hardcoded list. Salience is a column, never a filter (weak tail kept)."
  - "EMBEDDINGS ALREADY EXIST: reuse L0's pinned Vertex AI text-multilingual-embedding-002 (768-dim) in
     bo_samskara — same vector space as bg_texts, so signals ↔ classical citations are similarity-bridgeable.
     No generative LLM in the build (deterministic-first intact)."
  - "FULL L0 BRIDGE: every signal carries classical_sources_array (catalog + rules + texts citations)."
  - "EVAL HARNESS gates the L2 seal (semantic completeness, not just per-table coverage)."
---

# L2 Bodha — Master Plan v3.0 (the dual-capture model)

## §0 — The thesis in one paragraph
L1 stores facts; L2 projects them. The native's dual-capture refinement: **`ga_structural` is L1's
cross-asset RELATIONAL synthesizer** — it ingests the other L1 assets' facts and derives the
relationships among them (relationships that cannot exist without cross-asset data, e.g. "weak Saturn
aspects the 10th-lord"). **`bo_laksana` (MSR) then projects from the WHOLE of L1** — `ga_structural`
for the relational layer, and each individual asset for its native-grained facts (magnitudes, positions,
time-windows, birth-moment qualities). This captures BOTH the relational value AND each fact's
individuality, at correct grain, with full completeness and retrievability. The guardrail that keeps it
honest: ga_structural derives NEW relationships referencing source `fact_id`s — it never restates a
source asset's bare value (Trap 1).

**Why this is the right model (and not a one-surface merge):** verified in code, `ga_structural` ALREADY
ingests cross-asset facts today (it reads `chart_facts` for `varga_position`, `upagraha_position`,
`jaimini_chara_karaka`). It is already a cross-asset relational engine — just incompletely wired. This
plan completes that wiring (L1 enrichment) and then projects everything (L2). The seal reopens for
GENUINE NEW COMPLETENESS (relationships we were structurally missing), not for reorganization.

---

## §1 — The four lenses that justify the model (for the record)
1. **Synthesis LLM:** never queries an asset; queries retrieval tools. Benefits from `fact_kind` typing
   (relationship / magnitude / position / time_window / birth_moment), which this model carries end-to-end.
2. **Downstream L2 assets:** the enrichment HELPS exactly where it matters — CDLM gets linkable relational
   signals that didn't exist; **CGM (the graph) gets new weighted edges** ("weak Saturn → aspects → 10th
   lord"), serving design-philosophy #5 (invest hardest in the graph); RM gets tighter weakest-graha
   targeting. MSR gets both magnitude-signals and richer relational-signals. Net: neutral→strongly positive.
3. **Cockpit:** all L1 tiles stay truthful (assets stay separate); ga_structural's count grows honestly.
4. **Completeness + retrievability (the two pillars):** maximized — nothing dropped, everything typed,
   everything reachable.

---

## §2 — PHASE L1-E: enrich ga_structural (reopen the seal for new completeness)
**Goal:** ga_structural ingests the 4 currently-un-ingested L1 assets and derives their relational value.

Currently ga_structural ingests positions/vargas/upagrahas/chara-karakas but NOT the relational
consequences of strength, sade-sati, panchanga, and the rest of sensitive. Add ingestion + relational
derivation for:
- **ga_strength** → strength-conditioned relationships: "weak/strong graha aspects/conjoins X",
  shadbala-weighted aspect strength, ashtakavarga-supported vs starved house relationships,
  ishta/kashta-phala-modulated yoga effects. (The magnitude stays in ga_strength; the *relationship that
  USES the magnitude* is the new ga_structural fact.)
- **ga_sensitive** (the non-ingested part: KP significators, arudha padas, swamsa/karakamsa) → relational
  facts: arudha-to-graha relationships, karakamsa-significator relationships, KP-significator chains.
- **ga_sade_sati** → time-windowed structural relationships: which natal relationships are amplified/
  afflicted during sade-sati phases (the relationship is natal-structural; the temporal activation is the
  L3 Kāla layer's job — here store only the *structural* tie, flagged as sade-sati-relevant).
- **ga_panchanga** → birth-moment structural ties: panchanga-yoga ↔ graha relationships, tithi/vara lord
  relationships.

**HARD GUARDRAIL (Trap 1):** every new ga_structural row stores a DERIVED RELATIONSHIP and carries the
source `fact_id`(s) it consumed in its derivation provenance. It does NOT re-emit the bare magnitude/
position/phase as a structural fact. Two-pass verification + real sha256 fact_ids (the existing
ga_structural discipline) apply to the new rows.

**DAG change:** `ga_structural depends_on` gains `[ga_strength, ga_sensitive, ga_sade_sati, ga_panchanga]`
(it already transitively depends on positions/vargas). Surgical migration; the orchestrator self-orders.

**Acceptance [verify-against: prod]:** ga_structural row count grows (record old 74,644 → new N); every
NEW row is a relationship (not a restated value) and cites its source fact_id(s); FORENSIC 7/7 still
PASSES (the enrichment must not perturb the 7 birth anchors); two-pass verified; no silent drops.
**Re-seal ga_structural at the new count only after FORENSIC re-passes.**

---

## §3 — PHASE B1: bo_laksana (MSR) projects the WHOLE of L1 (no curation)
**Goal:** one MSR signal per meaningful L1 fact, across ALL L1 assets, no allow-list, full parity.

**B1.0 preconditions:** proxy up; migrations 226+230 applied (verify on prod); L1-E complete (ga_structural
re-sealed); **pin the projection count now** — run, against prod, the count of every projectable
`chart_facts` row for the native (all signal-bearing categories across all L1 assets). That number is
B1's parity target; it is knowable today via one query, not "at build time."

**B1.1 — DELETE the curation allow-list.** Remove `ALL_SIGNAL_CATEGORIES` as a fetch filter. bo_laksana
enumerates projectable categories FROM LIVE `chart_facts` (e.g. every `source_asset_id` in the L1 set,
minus a tiny, documented EXCLUDE list of pure-helper rows that are inputs only — and even those, per the
native, are ALSO projected as their own magnitude-signals; see B1.2). The category set is data-derived,
never hardcoded. Salience computed per signal but NEVER used as a filter (weak tail kept).

**B1.2 — Project ga_strength facts as SIGNALS *and* keep them as INPUTS.** Every shadbala/ashtakavarga/
bhava-bala/ishta-kashta/vimsopaka fact becomes a retrievable magnitude-signal (`fact_kind=magnitude`),
AND remains in the salience lookup dicts. A fact being a salience input does not bar it from being a
stored signal. Closes the ~2,184-row gap where strength was previously invisible to retrieval.

**B1.3 — Carry `fact_kind` on every signal** (relationship / magnitude / position / time_window /
birth_moment), derived from `source_asset_id` + category. This is the typing that serves the synthesis LLM.

**B1.4 — Anti-drift spine (the load-bearing acceptance — prove on bo_laksana ALONE before any fan-out):**
every signal's `constituent_facts_array` resolves to a real `chart_facts.fact_id` (zero unresolved);
MSR count == the B1.0 pinned count (parity over the WHOLE L1 population, not ga_structural alone, not a
subset); FORENSIC anchors inherit L1 values; weak tail present; idempotent (delete-then-insert per
chart×ayanamsha). **HALT and fix if the spine doesn't resolve — do not fan out onto a broken root.**

**B1.5 — THE L0 CLASSICAL BRIDGE.** Populate every matchable signal's `classical_sources_array` by
deterministic join: named yogas/doshas → brahma_yoga_catalog / brahma_dosha_catalog (id + citation);
rule-traceable configs → bg_rules (verse ref); classical chunks → bg_texts via the existing L0 id-linkage.
Unmatched raw signals stay empty (not faked); report coverage ratio. **This is what makes retrieval return
the FACT + its connected classical citation(s) together — the native's explicit goal.**

**B1.6 — E2 lossless signal_summary_text.** Deterministic template, EXHAUSTIVE BY CONSTRUCTION: render
ALL typed columns THEN iterate EVERY `configuration_jsonb` key (no hardcoded key subset). No LLM. Fuzz
test proves no key is omitted. This is the dense citable surface the synthesis LLM reasons over + the
embedding input.

**B1.7 — 3 materialized views** (A10 §11): top_signals / recurring_patterns / domain_summary; refresh
after insert.

---

## §4 — PHASE B2: fan-out (parallel on bo_laksana; only after B1.4+B1.5 pass)
- **bo_sangati (CDLM):** cdlm_cells / domain_rollups / chart_summary / pattern_clusters /
  evolution_gradients + **bodha_convergence** (convergence-density-per-domain, convergence_formula_v1).
  Benefits directly from the new relational signals (more domain linkages).
- **bo_karanajala (CGM edges) — invest deepest:** cgm_edges / sub_graphs / motifs / topology_summary +
  **bodha_cgm_paths** (centrality_formula_v1, final-dispositor, significator paths) + **bodha_contradictions**
  (drift guardrail). The enriched ga_structural relationships become NEW WEIGHTED EDGES — this is the
  biggest beneficiary of the dual-capture model.
- **bo_bimba (CGM nodes):** cgm_nodes (graha/bhava/special-point/configuration/domain/dasha-lord nodes),
  each with centrality columns.
- **bo_samskara (embeddings) — E1, real, reusing L0's path:** replace `placeholder_hash_v1` with a real
  embedding of the B1.6 summary text via **Vertex AI text-multilingual-embedding-002 (768-dim)** — the
  SAME model L0's bg_texts uses, so signals land in the classical-text vector space and a signal can be
  similarity-matched to its classical sources. Pin model+version on the row (deterministic transform; an
  external deterministic call in the build is accepted — L0 already does it). 1:1 with MSR signals.
- **bo_samvada (UCD) = Option A:** vw_chart_digest view + query_ucd tool (read-side; not a writer).

**B2 acceptance:** each asset's tables populated; convergence + contradiction first-class ROWS; CGM graph
metrics present (incl. the new strength-weighted edges); embeddings real + 1:1; query_ucd returns digest.

---

## §5 — PHASE B3: bo_upaya (RM) — depends_on bo_laksana + bo_sangati
6 bodha_rm_* tables via resonance_score_v1 + resonance_match_score_v1; every remedy grounded to
brahma_remedy_corpus (L0) with a classical citation. Benefits from richer weakest-graha relational
signals. **Acceptance:** 6 tables populated; every remedy cites a real L0 corpus row; deterministic.

## §6 — PHASE B4: bo_pramana_mapa (global scorecard) + UCD surface
synthesis_quality_scorecard with the **standing Trap-1 audit** (re-checks every constituent_facts_array
resolves — the spine becomes a permanent metric). Confirm query_ucd. **Acceptance:** scorecard populated;
Trap-1 audit reports zero unresolved fact_ids.

## §7 — PHASE B5: orchestrator build + cockpit + retrieval tools (NOT seal yet)
One run `POST /api/cockpit/runs scope=layer/bodha`; 8 bo_ assets lit with summed count_sql; target_floor =
achieved; ≥1 retrieval tool per bodha_* table added to the existing retrieval layer + coverage gate
extended. Every tool return carries tier + salience + citation + fact_ids (**E5 provenance contract test**).
DRAFT→CURRENT flip. CURRENT_STATE + SESSION_LOG updated. **L2 NOT sealed until §8.**

## §8 — PHASE B6: SEMANTIC-COMPLETENESS EVAL HARNESS (GATES THE SEAL)
Curated native chart questions (span domains / convergence / contradiction / graph / remedies / classical
grounding), each with a deterministically-derived known-complete answer-set. Run through LIVE
retrieval+planner; score RECALL ("did it retrieve everything relevant?") + PROVENANCE ("each with tier +
citation?"). Seed from the existing answer:eval baseline. **Committed re-runnable suite** = the standing
synthesis-completeness regression gate. **L2_BODHA_CLOSE seals ONLY when the harness meets the native's
recall+provenance threshold**, with the L3 Kāla onboarding contract. Plus E6 (path-as-reasoning-chain
tool), E7 (cross-ayanamsha consistency surfaced), E8 (weak-tail reachability proof).

---

## §9 — Sequence + dependency summary
```
L1-E (enrich ga_structural; reopen→re-seal; FORENSIC 7/7)        ← reopens the L1 seal for NEW completeness
  └─ B1 bo_laksana (project WHOLE L1; no curation; spine; L0 bridge; summary text)   ← prove spine ALONE
       ├─ B2 bo_sangati / bo_karanajala / bo_bimba / bo_samskara(real embeddings) / bo_samvada
       │      └─ B3 bo_upaya
       └─ B4 bo_pramana_mapa
            └─ B5 orchestrate + cockpit + retrieval tools + provenance test  (NOT seal)
                 └─ B6 eval harness (GATE) → L2_BODHA_CLOSE seal + L3 onboarding
```

## §10 — The non-negotiables (every phase)
Deterministic-first (no generative LLM in the build; embeddings = deterministic transform, pinned);
no audience tier; no silent drops; per-chart isolation; **real fact_ids, never mock**; FROZEN orchestrator
contract (bo_* + the enriched ga_structural all conform — @register, ctx.db_conn never committed, no
asset_throughput writes); count_sql is data-truth; floors aspirational (target_floor = achieved);
**Trap-1 guardrail** (ga_structural derives relationships citing source fact_ids, never restates values);
FORENSIC 7/7 is the L1 authority gate and must re-pass after L1-E.

---
*End of L2_BODHA_MASTER_PLAN v3.0 — the dual-capture model: ga_structural enriched to ingest the 4
missing L1 assets and derive their relational value (L1, relational, seal reopened for genuine new
completeness, Trap-1-guarded); bo_laksana projects the WHOLE of L1 (relational + native-grained, no
curation, fact_kind-typed, anti-drift-spine-proven, L0-bridged); fan-out with the graph as biggest
beneficiary; real embeddings reusing L0's pinned Vertex model; eval harness gates the seal. Completeness
and retrievability both maximized; each fact's individuality and its relational value both captured.*
