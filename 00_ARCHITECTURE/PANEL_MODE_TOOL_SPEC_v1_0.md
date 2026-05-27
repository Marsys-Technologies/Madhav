---
artifact: PANEL_MODE_TOOL_SPEC_v1_0.md
status: DRAFT
version: 1.0
authored_by: Claude (Cowork session) — synthesis of native-led design discussion 2026-05-27
authored_on: 2026-05-27
audience: native (Abhisek Mohanty); implementation executor (Claude Code in Antigravity IDE)
disposition: >
  MCP tool-surface specification for provenance-aware, panel-mode-ready interpretation.
  Defines the always-loaded compact chart table, the on-demand structural tools that serve
  T0+T1, and the explicit exclusion of T2 (UCN/MSR-selection/CDLM/CGM narrative) from
  panelist context. PENDING NATIVE APPROVAL of the parent decision.
parent_brief: 00_ARCHITECTURE/PROVENANCE_TIERING_DECISION_v1_0.md
sibling_artifact: 00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md
relates_to:
  - 00_ARCHITECTURE/MCP_ARCH_v3_PROPOSAL_2026-05-22.md (the v3.1 pure-MCP architecture this extends)
  - platform-mcp/ (MCP sidecar — implementation home; amjis-mcp Cloud Run service)
  - chart_facts, rag_chunks, classical_chunks, l25_ucn_sections (data sources)
design_authority: >
  The on-demand tool list is the model's own first-person account (this session) of what
  it needs to reason at acharya grade without computing under query pressure. Treat the
  shadbala-on-demand tool as the priority addition.
approval_gate: inherits parent_brief approval gate
---

# Panel-Mode MCP Tool Surface — Specification

## §0 — Design objective

A single objective governs every tool here: **the most accurate astrological interpretation
or prediction of the data provided.** That requires two things the current surface does not
cleanly provide: (1) structural facts the model would otherwise mis-compute mid-query, and
(2) a hard guarantee that **no model-authored synthesis (T2) enters a panelist's context**,
so each model forms an independent reading on neutral data. Tiers (T0/T1/T2) are defined in
the parent brief.

---

## §1 — The always-loaded compact chart table (~800 tokens)

Auto-loaded as an MCP resource for every interpretation query (replaces dumping the full
25K-token FORENSIC file as the default input). One row per graha plus lagna/dasha header.

Per-planet columns (all T1, all pre-computed per `STRUCTURAL_FACT_LAYER_SPEC`):
`house · sign · exact_degree · dignity · nakshatra · nakshatra_lord · kp_sublord ·
retrograde · shadbala_total_rupas · vimshopaka · sav_bindus_of_its_house`

Header block: lagna (sign, degree, lord, lord placement), Moon nakshatra/pada,
**active mahadasha + antardasha with exact dates**, ayanamsha, birth data echo.

- **Rationale (model's own):** the full FORENSIC .md is ~25–28K tokens in human-reading
  format; parsing it burns cognitive budget and is where misreads creep in. An 800-token
  structured table gives the entire chart as fact, with strength already quantified, so
  every subsequent step is interpretation, not arithmetic.
- This resource is **T1-only**. It contains zero synthesis.

---

## §2 — On-demand tools (called by query type)

Each is a thin reader over pre-computed `chart_facts` / classical corpus. **None computes
in the LLM; none returns T2.**

| Tool | Returns | Called when |
|---|---|---|
| `planetary_strength(planet)` | Full shadbala (6 components + sub-scores + total + threshold verdict), vimshopaka across vargas, chesta/speed | "Can planet X deliver its significations?" — **priority tool** |
| `aspect_matrix()` | Complete graha **and** rashi drishti, with arc orbs and aspect type | Any relationship / partnership / inter-planetary dynamics question |
| `yoga_register()` | All detected yogas: name, classical source, constituents, present/partial/cancelled, modifier | Before any synthesis — to know which configurations are validated present |
| `dispositor_chain()` | Full chain per planet to termination | Tracking planetary networks / unexpected signification flow |
| `dasha_timeline(years_ahead)` | Vimshottari sequence with exact dates; per period the lord's natal dignity + shadbala + SAV | Any predictive / timing question |
| `transit_overlay(date)` | Current positions vs. natal: conjunctions/aspects/transits, transiting-vs-natal dignity, SAV of transited sign | "What's happening around <date>?" |
| `classical_lookup(query, text?)` | Semantic search in **L0 classical corpus only** (BPHS/Jaimini/KP/Tajaka) | Grounding an interpretation in a named classical authority |
| `forensic_section(entity)` | Full FORENSIC deep-detail for ONE entity (e.g. PLN.MARS, CUSP.7H) | Need provenance-level detail on one planet/house, not the whole chart |
| `lel_event_correlation(event_type)` | LEL events of that type + the dasha/antardasha/transits active at each | Predictive calibration — what has historically triggered this event type for the native |

Note: `ashtakavarga` and `proximity/criticality` facts ride inside `planetary_strength`
and `transit_overlay` payloads rather than as separate tools, to keep the surface tight.

---

## §3 — The exclusion guarantee (the core of this spec)

### §3.1 — What panelists must NOT receive
UCN prose, MSR signal rows in bulk (selection + names + scores), CDLM cells, CGM narrative
nodes — i.e. **all T2**. Rationale: the instant T2 is in context, the model reasons *about*
the prior reading rather than *from* the data, and independence is lost. This holds for
panel mode and for any non-Anthropic single query.

### §3.2 — Plug the RAG leak (mandatory)
Today `vector_search` can surface `UCN.SEC.*` chunks (and UCN-merged CGM nodes), silently
injecting T2 into any query. The panelist `vector_search` path must be provenance-filtered.
Two implementation options (native to choose — parent brief §4 Q2):

- **Option A — tag-and-filter (lower migration):** add `tier` / `provenance` columns to
  `rag_chunks` + synthesis-node tables; panelist context-builder filters `WHERE tier IN
  ('T0','T1')`. Risk: a missed tag leaks. Requires a backfill + a CI assertion that no
  untagged synthesis chunk exists.
- **Option B — separate indexes (leak-proof):** a panelist index containing only T0
  (classical) + T1 (structural facts + FORENSIC sections); a separate judge index that
  additionally contains T2. Panelist tools physically cannot reach T2. Higher migration,
  stronger guarantee. **Recommended for the research instrument.**

### §3.3 — Mode awareness in B.11
The B.11 Whole-Chart-Read bundle becomes mode-conditioned. In `panel` / non-Anthropic mode,
the holistic context = compact chart table (§1) + on-demand T1 tools + scoped T0 lookups.
The model still reads the whole chart first — but the "whole chart" is the **neutral
structural** whole chart, not the synthesised one.

---

## §4 — Judge / reconciliation layer (where T2 lives)

The judge is the **only** consumer of T2, and consumes it **attributed**:
- Collects each panelist's independent interpretation (each produced from T0+T1 only).
- Has access to prior model-authored synthesis (UCN v4.1, MSR, CDLM) labelled with its
  `authoring_model`, as **one reading to compare against**, not as ground truth.
- Scores convergence/divergence across panelists; where independent models diverge, flags
  a candidate `DISAGREEMENT_REGISTER` entry (the "divergence dividend", parent §2.4).
- Synthesises the final answer, citing which panelists agreed and where the prior UCN
  reading aligned or differed.

Tooling: a `judge_context_bundle()` that assembles panelist outputs + attributed T2; this
is the inverse of the panelist bundle and the only place `ucn_walk` / MSR-bulk reads are
permitted.

---

## §5 — Token economy summary

| Mode | Default context | On-demand | Excluded |
|---|---|---|---|
| Panelist | ~800-token compact chart (T1) | structural tools, scoped classical (T0) | UCN/MSR/CDLM/CGM (T2) |
| Judge | panelist outputs + attributed T2 | full FORENSIC sections, ucn_walk | — |

The full 25K FORENSIC file is fetched only via `forensic_section(entity)` (one entity) or
explicitly for deep single-entity provenance — never as the default panelist dump.

---

## §6 — Priority for implementation
1. `planetary_strength` backed by computed **shadbala** — the single highest-value addition.
2. The §1 compact chart table resource.
3. `aspect_matrix` + `yoga_register` (the two the model most often mis-computes).
4. The §3.2 RAG provenance filter / index split (the leak plug — required before any real
   panel run).
The rest can follow incrementally.

---

## §7 — Provenance of this brief
Model-authored (Claude, Cowork). DRAFT. Inherits the parent brief's approval gate. The
tool list reflects the model's first-person account of its own reasoning needs and should
be read as informed recommendation, not a ruling.
