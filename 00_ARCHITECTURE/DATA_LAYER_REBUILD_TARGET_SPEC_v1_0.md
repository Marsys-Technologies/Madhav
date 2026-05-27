---
artifact: DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md
document: Deterministic Data-Layer Rebuild — Unified Target Specification
status: DRAFT (target architecture — pending native approval; modifies nothing canonical)
version: 1.0
date: 2026-05-27
authored_by: Claude (Cowork session) — synthesis of native decisions 2026-05-27
native_decisions:
  - "Replace CONTENT of all data assets with 100% deterministic facts; keep STRUCTURE intact."
  - "Upper layers = deterministic + COMPUTED salience (formula authored once, value computed never assigned); opinion-prose removed."
  - "Old corpus: ARCHIVE (freeze as model_attributed reference) + REPLACE live canonical files after JH gate."
  - "Build JH-equivalent fact engine FIRST; nothing above L1 buildable until L1 validated vs JH."
supersedes_within_family:
  - "PROVENANCE_TIERING_DECISION 'reposition T2' → upgraded to 'archive + replace with deterministic'."
  - "MSR_UCN_CONTAMINATION_AUDIT §5.2.3 'salience = serve-time panel vote' → upgraded to 'salience = computed column'; panel role narrows to meaning/valence only."
relates_to:
  - 00_ARCHITECTURE/PROVENANCE_TIERING_DECISION_v1_0.md
  - 00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md
  - 00_ARCHITECTURE/MSR_UCN_CONTAMINATION_AUDIT_v1_0.md
  - 00_ARCHITECTURE/BRIEFS/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md
  - 00_ARCHITECTURE/FACT_ENGINE_BRIEF_REVIEW_v1_0.md
  - 00_ARCHITECTURE/BRIEFS/JYOTISH_ENGINE_SCOPE_CATALOGUE_v1_0.md
approval_gate: native sign-off + version bumps on affected canonical surfaces (CLAUDE.md §L)
expose_to_chat: false
---

# Deterministic Data-Layer Rebuild — Unified Target Specification

## §0 — Target in one paragraph

Every data asset becomes a **pure deterministic projection** of the JH-equivalent fact base,
carrying **computed** values only — including a **computed salience** column on the synthesis
layers. No model-authored prose, scores, names-as-claims, or curation survives in the data
layer. **All interpretation (meaning, valence-for-this-native) moves to serve-time**, produced
by the LLM panel reading T0 (classical) + the deterministic data layer. The current corpus is
**frozen and archived** as a model-attributed reference, then the live canonical files are
**replaced** by their deterministic regenerations after each passes the JH validation gate.
Build order is forced: **fact engine → structural facts → signal/graph projections →
serve-time synthesis.**

---

## §1 — The salience discipline (the load-bearing rule)

"Deterministic + computed salience" is safe **only** under this rule, which directly answers
the contamination audit's C1 (opinion-scores-as-data):

> The salience **formula** is authored once, versioned, and committed as code/config. The
> salience **value** on every row is **computed** from deterministic inputs — never assigned
> by a model. Same chart + same `salience_formula_version` ⇒ identical salience, reproducibly,
> across all models.

**Permitted salience inputs (all deterministic):** computed strength (aspect-orb tightness,
shadbala of involved planet[s], dignity state), classical-source-corroboration count,
divisional-corroboration count, dasha-activation proximity (is an involved planet's
mahadasha/antardasha current or imminent), house-weight (kendra/trikona/dusthana — itself a
deterministic classification), ashtakavarga bindu support.

**Forbidden in salience:** "how much this matters for this life," benefic/malefic-*for-native*,
domain-importance opinion. These are serve-time interpretation, never a stored column.

Each synthesis row therefore carries a **decomposed, fully-computed coefficient**:
`{ deterministic_strength, verification_certainty, computed_salience }` + the
`salience_formula_version` in provenance. This is the audit's §5.2 split with item (3)
*computed* rather than panel-voted.

---

## §2 — Per-asset rebuild specification

### §2.1 — FORENSIC (L1)
Regenerated as the rendered view of the engine JSONL (per the FACT_ENGINE brief + its review).
Pure facts. Structure/IDs (MET.*, PLN.*, HSE.* …) preserved so existing tools/citations hold.
**Oracle:** JH transcription + JH-side of FORENSIC's dual columns (review R1). Already mostly fact.

### §2.2 — Structural fact layer (T1 expansion — NEW, feeds everything above)
Per `STRUCTURAL_FACT_LAYER_SPEC`: aspect matrix, dispositor chains, cross-varga strength,
yoga-presence booleans, nakshatra/KP sub-lord chains, proximity/criticality metrics,
shadbala (+sub-scores), ashtakavarga (full matrices), vimshopaka, Tajaka predicates. All into
`chart_facts` with `tier:T1, deterministic:true`. This layer **is** the deterministic-strength
input for §2.3–§2.5 salience.

### §2.3 — MSR → complete never-drop signal enumeration + computed coefficient
- **Never-drop:** every observable configuration gets a row — including weak, wide-orb,
  single-source ones. Strength is a **column, not a gate** (closes audit C2, the silent drop).
- Each row: `{signal_id, chart_id, configuration (structured, not prose), constituent_facts[],
  classical_sources[], deterministic_strength, verification_certainty, computed_salience,
  domains_affected (deterministic mapping via fact→domain table, not opinion),
  provenance:{engine_version, salience_formula_version, ...}}`.
- **Removed:** hand-assigned `strength_score`/`confidence`, `signal_name`-as-claim,
  deliberation-in-fields (C3), interpretive `supporting_rules` prose (C4). Names become neutral
  structural descriptors; meaning is serve-time.

### §2.4 — CDLM → deterministic shared-factor graph
- Edges = computable shared factors between signals/configurations: shared planet, shared
  house, shared karaka, shared dasha-activation-window, mutual aspect. Each edge carries a
  **computed linkage-strength** (e.g. number/quality of shared factors) — a salience analogue.
- **Removed:** "this linkage means X across domains" narrative → serve-time.

### §2.5 — CGM → deterministic structural graph (subgraph)
- Nodes = planets/houses/signs/configurations; edges = **computable structural relations**:
  aspect, dispositor, lordship, karaka, conjunction, parivartana. Each edge typed + weighted by
  computed strength.
- **Removed:** causal-outcome edges ("this configuration causes this life event") → serve-time.
  CGM stops being a *causal* model and becomes a *structural* graph; the causal reading is the
  panel's job.

### §2.6 — UCN → computed chart-signature digest (no narrative)
- UCN has no deterministic narrative equivalent. It is replaced by a **computed signature
  digest**: top configurations by computed salience, system-convergence counts, dominant /
  weakest planets by shadbala, strongest yogas by computed strength, dasha-context — all
  salience-ranked, zero prose.
- The synthesized "argument of the chart" (UCN's actual value) becomes a **serve-time output**.
- Old UCN → frozen archive reference (§3).

### §2.7 — RM → deterministic remedy lookup
- `computed_weakness (from shadbala/dignity/ashtakavarga) → classical_remedy` mapping table
  (deterministic lookup keyed on the fact layer). Remedy **prioritization** → serve-time.

---

## §3 — Archive + replace (corpus disposition + cutover)

1. **Freeze** the current FORENSIC/MSR/UCN/CDLM/CGM/RM as an immutable, version-tagged archive
   labelled `provenance: model_attributed`, `authoring_model: Claude/Anthropic`. Retained as
   (a) the judge-layer / serve-time **divergence-dividend** reference, (b) human acharya reading.
2. **Build new deterministic layer in parallel** (isolated namespace / build_id — review R4),
   never mutating canonical until validated.
3. **Per-asset JH/oracle gate** must pass before that asset's canonical file is replaced.
4. **Replace** live canonical files with deterministic regenerations; loader projects JSONL →
   existing Postgres schema unchanged (existing retrieval tools keep working); renderer
   projects JSONL → L1.md (review R7). Enumerate FK dependents before any DB swap (review R4).
5. **Version-bump** affected canonical surfaces + CLAUDE.md / PROJECT_ARCHITECTURE (B.11
   mode-awareness from the provenance brief) on cutover.

---

## §4 — Serve-time synthesis layer (where interpretation now lives)

All meaning-making is regenerated per query by the LLM panel reading **T0 (classical) + the
deterministic data layer (T1)**. The panel produces: signal valence-for-native, cross-domain
narrative, the chart "argument" (old-UCN function), remedy prioritization. Divergence between
the live panel reading and the frozen archived synthesis (§3) is a logged research output
(DISAGREEMENT_REGISTER candidate). B.11 holistic-read is satisfied from T1, not from stored T2.

---

## §5 — Build order (forced dependency chain)

0. **JH fact engine + ayanamsha Phase-0 gate** (FACT_ENGINE brief + review). `oracle_map`, per-section ayanamsha, JSONL schema.
1. **Structural fact layer** (T1 derivations) → `chart_facts`.
2. **Signal enumeration (MSR) + CDLM/CGM projections + RM lookup + UCN digest**, all consuming §1 salience formula.
3. **Loader + renderer** (JSONL → DB + JSONL → L1.md), read-compat verified.
4. **Archive freeze + cutover** (§3).
5. **Serve-time synthesis layer** (§4) + DAG runner wiring 0–4 into one-command build.

`salience_formula_version` and `engine_version` are stamped on every row at every level.

---

## §6 — Open items carried forward
- Canonical **JSONL schema + `oracle_map`** (next deliverable; everything keys off it).
- **Salience formula v1** definition + unit tests (the §1 discipline made concrete).
- **DAG-runner design** (~25 nodes; custom lightweight, content-addressed à la DVC).
- LEL re-fit decision under JH dasha dates (review R1 downstream).

---

## §7 — Provenance
Model-authored (Claude, Cowork), DRAFT, native-approval-gated. Modifies nothing canonical.
Records native decisions of 2026-05-27 and reconciles the DRAFT family to them.
