---
artifact: PROVENANCE_TIERING_DECISION_v1_0.md
status: DRAFT
version: 1.0
authored_by: Claude (Cowork session) — synthesis of native-led design discussion 2026-05-27
authored_on: 2026-05-27
audience: native (Abhisek Mohanty); secondary acharya readership at approval
disposition: >
  Architectural decision proposal. Establishes a provenance-aware context-tiering
  discipline that distinguishes model-neutral data (L0 + L1 + deterministic
  derivations) from model-authored synthesis (UCN / MSR-selection / CDLM / CGM
  narrative). PENDING NATIVE APPROVAL — does not modify any canonical artifact,
  does not change architecture, until the native signs off + a version bump is
  applied to the affected canonical surfaces (PROJECT_ARCHITECTURE, B.11 protocol).
sibling_artifacts:
  - 00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md
  - 00_ARCHITECTURE/PANEL_MODE_TOOL_SPEC_v1_0.md
relates_to:
  - CLAUDE.md §A (research-tool mission), §I (B.1/B.3/B.11 principles), §L (no architecture change without approval)
  - 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md (the artifact whose status this proposal would change)
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md, CDLM_v1_1.md, CGM_v9_0.md
  - 01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md (the model-neutral spine)
approval_gate: native sign-off required before any downstream implementation brief is dispatched
---

# Provenance-Aware Context Tiering — Architectural Decision

## §0 — One-paragraph statement

The MARSYS-JIS corpus does not currently distinguish between **what the chart is**
(model-neutral fact) and **what a model concluded the chart means** (model-authored
synthesis). The two are conflated in the synthesis layer and, via RAG chunking, leak
back into the retrieval context that every query consumes. This proposal draws a hard
provenance boundary: **panelist models receive only model-neutral data; model-authored
synthesis is demoted from "canonical" to "model-attributed" and is consumed only by the
judge/reconciliation layer, never by an independent panelist.** This is required for the
project's stated research mission (CLAUDE.md §A: "a research tool for astrology as a
discipline"), which is impossible to honour on a substrate that silently encodes one
model's interpretation as ground truth.

---

## §1 — The problem, precisely

### §1.1 — The bias is structural, not stylistic
The native's original concern was that UCN "builds bias by giving short interpretation."
On inspection the problem is sharper than narrative tone. **UCN commits interpretation
into the data layer.** It contains:

- **Named conceptual frames** ("Authority-Through-Tension Pattern", "Mercury Seven-System
  Convergence", "Dharma-Moksha Dual Track"). Once a model has the label, its reasoning
  organises around the label rather than re-deriving from positions.
- **A single coherent narrative arc.** LLMs follow narrative continuity; a model reading
  UCN prose will extend and confirm it, not independently re-weight the evidence.
- **Pre-loaded confidence** ("this is the chart's primary finding", "this is not common"),
  which signals settledness and suppresses divergent reads.

None of this is a defect in UCN *as a reading*. It is acharya-grade synthesis. The defect
is using a **terminal synthesis product as upstream input** to a process whose entire
value depends on independence.

### §1.2 — The provenance problem is worse than the panel-mode problem
UCN, MSR, CDLM, and CGM were all authored by Claude (Anthropic API). Therefore:

- Handing UCN to **Gemini or GPT in panel mode** gives them a semi-judged Anthropic
  verdict to react to — independence is lost before they start.
- But the same contamination applies to **any single non-Anthropic query**, not only
  panel mode. A Gemini individual query that ingests UCN is doing further work on top of
  Claude's interpretation, not forming its own.

The truly model-neutral layer is therefore **narrower than it appears**:
- **L0** — classical texts (BPHS, Jaimini, KP Reader, Tajaka, Nadi). Rules, not opinions
  about *this* chart. Neutral.
- **L1** — FORENSIC chart facts from Swiss Ephemeris (positions, degrees, houses, dignity,
  divisional positions, Chara Karakas, dasha dates). Computation, not reasoning. Neutral.
- **Everything above L1 carries a model fingerprint** — including MSR's *selection* of
  573 signals out of thousands of observable combinations, its strength/confidence scores,
  its signal names, and its domain mappings. MSR's *citations* (FORENSIC + classical) are
  neutral; MSR's *curation* is not.

### §1.3 — The live-pipeline leak
The contamination is not contained to whichever model reads UCN deliberately. The build
pipeline chunks UCN into the `rag_chunks` table (`UCN.SEC.*` nodes), vectorises it, and
serves it through `vector_search`. UCN section nodes are also merged into `l25_cgm_nodes`
and extracted into `l25_ucn_sections`. **Net effect:** any tool that calls semantic search
can surface Claude's interpretive prose as "retrieved context" — silently, to any model,
in any mode. This is the loop that must be cut for panel/multi-model integrity.

---

## §2 — The decision

### §2.1 — Three provenance tiers (the core abstraction)

| Tier | Contents | Provenance | Panelist context? | Judge context? |
|---|---|---|---|---|
| **T0 — Neutral rules** | Classical texts (L0), via `read_classical_text` / scoped `vector_search` | Pre-existing tradition | Yes, on demand | Yes |
| **T1 — Neutral facts** | FORENSIC L1 + **all deterministic derivations of L1** (see §2.2) | Swiss Ephemeris + classical rule application; no LLM judgment | **Yes — this is the panelist substrate** | Yes |
| **T2 — Model-authored synthesis** | UCN, MSR signal-selection/scoring, CDLM, CGM narrative | Authored by a specific model (currently Claude) | **No — never** | Yes, **attributed**, as one prior reading to compare against |

### §2.2 — The pivotal reclassification: *deterministic derivation of L1 is still L1*
A function of L1 data that requires **no interpretation** — only positional arithmetic and
classical rule application — produces **fact, not synthesis.** Examples: the aspect matrix,
dispositor chains, nakshatra-lord chains, cross-varga dignity, yoga *presence* (boolean),
proximity-to-exaltation degrees, and the classical mathematical strength systems
(shadbala, ashtakavarga, vimshopaka, KP sub-lords). These belong in **T1**, served to
every model, and are the subject of the sibling
`STRUCTURAL_FACT_LAYER_SPEC_v1_0.md`. The distinction that governs the boundary:

> **"Is this configuration present?" is fact. "What does its presence mean for this
> native?" is interpretation.** The first is T1. The second is the model's job — and in
> panel mode, each model's *independent* job.

### §2.3 — UCN status change: canonical → model-attributed
UCN's frontmatter currently implies canonical authority. This proposal relabels it:

- `status` framing moves from implied-canonical to **`model_attributed`**, with an explicit
  `authoring_model` field (e.g. `Claude / Anthropic API`).
- UCN is **removed from the default retrieval/RAG path** for panelist-facing queries. Its
  chunks are either (a) tagged with a `tier: T2` / `provenance: model_authored` filter that
  the panelist context-builder excludes, or (b) routed to a separate index consulted only
  by the judge. (Implementation options in the tool spec.)
- UCN is **retained, unchanged in content** as a first-class judge-layer input and as a
  human-facing acharya reading. Nothing of value is destroyed — it is **repositioned**.

### §2.4 — The divergence dividend (why this strengthens the instrument)
Once panelists work from T0+T1 only, the comparison between Claude's prior synthesis (UCN)
and an independent Gemini/GPT reading becomes a **research output**, not a contamination:
- **Convergence** across independent models on clean data = stronger signal.
- **Divergence** = a legitimate interpretive disagreement the judge must reason about
  explicitly, and a candidate entry for the `DISAGREEMENT_REGISTER`.

This directly serves the CLAUDE.md §A research mission and is unreachable on the current
substrate.

---

## §3 — What this proposal does and does not change

### §3.1 — Changes (pending approval)
1. Introduces the T0/T1/T2 provenance tier as a first-class concept in
   `PROJECT_ARCHITECTURE` (version bump required).
2. Amends the **B.11 Whole-Chart-Read protocol** to be **mode-aware**: in `panel` (and any
   non-Anthropic single-query) mode, the holistic context bundle is assembled from
   **T0+T1 only**, substituting the structural fact layer for UCN/MSR/CDLM.
3. Relabels UCN (and, by extension, flags MSR/CDLM/CGM) as model-attributed T2.
4. Adds a provenance tag to `rag_chunks` / synthesis-node tables so the context-builder can
   filter by tier.

### §3.2 — Does NOT change
- FORENSIC L1 (untouched — it is already the neutral spine).
- The *content* of UCN/MSR/CDLM/CGM (repositioned, not rewritten).
- The existing `/consume` web chat behaviour, unless the native chooses to apply the same
  tiering there (separate decision).
- Any canonical artifact, until native sign-off + version bump (CLAUDE.md §L).

---

## §4 — Open questions for the native (decide before implementation)

1. **MSR in panel mode — include or exclude?** MSR is less biasing than UCN (structured,
   citable, falsifiable) but its *signal selection* is still Claude-curated. Two defensible
   positions: (a) exclude entirely — purest independence, each model builds its own signal
   layer from T1; (b) include MSR **citations/anchors stripped of names and scores** as a
   neutral "here are observable configurations" checklist. Recommendation: **(a) for the
   research instrument; (b) optionally as a labelled, judge-only aid.**
2. **Filter vs. separate index** for T2 chunks — tag-and-filter in one `rag_chunks` table,
   or physically separate the panelist index from the judge index? (Tool spec lays out
   both; separate index is more leak-proof, tag-filter is less migration.)
3. **Scope** — apply tiering to panel mode + non-Anthropic single queries only, or make
   T0+T1-only the default for *all* panelists including Claude (maximum symmetry)?
4. **UCN relabel mechanics** — in-place frontmatter amendment (version bump UCN) vs. a
   wrapper manifest entry. Affects mirror discipline.

---

## §5 — Downstream artifacts (this is the parent)

- `STRUCTURAL_FACT_LAYER_SPEC_v1_0.md` — the T1 build: what deterministic facts to
  pre-compute, how, and into which `chart_facts` rows. The "more columns, not more
  interpretation" layer.
- `PANEL_MODE_TOOL_SPEC_v1_0.md` — the MCP tool surface that serves T0+T1 to panelists,
  the ~800-token always-loaded compact chart table, and the explicit exclusion of T2 from
  panelist context.

Both are DRAFT and inherit this brief's approval gate.

---

## §6 — Provenance of this brief
This document is itself model-authored (Claude, Cowork). It is a **proposal**, not a
ruling. Per CLAUDE.md §L, architecture does not change without the native's explicit
approval and a version bump on the affected canonical surfaces. Treat §2's decision as
*recommended*, not *applied*.
