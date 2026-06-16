---
artifact: MCP_PLATFORM_IMPROVEMENTS_BRIEF_v1_0.md
canonical_id: MCP_PLATFORM_IMPROVEMENTS_BRIEF
version: 1.0
status: DRAFT
authored_by: Claude (Cowork session, Sonnet)
authored_on: 2026-05-21
sealed_on: TBD (awaiting native approval)
sealed_by: TBD
brief_path: 00_ARCHITECTURE/BRIEFS/MCP_PLATFORM_IMPROVEMENTS_BRIEF_v1_0.md
parent_plan: 00_ARCHITECTURE/MACRO_PLAN_v2_0.md (concurrent workstream)
sibling_brief: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
related_artifacts:
  - 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md (transport-layer brief; this brief is platform-layer)
  - 025_HOLISTIC_SYNTHESIS/MSR_v5_0.md (asset-legibility audit target)
  - 025_HOLISTIC_SYNTHESIS/CGM_v9_0.md (asset-legibility audit target)
  - platform/src/lib/retrieve/ (where new advisory tools live)
  - 025_HOLISTIC_SYNTHESIS/UCN_v4_0.md (canonical query cache references this)
governance:
  workstream_name: MCP_PLATFORM_IMPROVEMENTS
  concurrent_workstream: true
  blocks_macro_progress: false
  parallelizable_with: MCP_BRIEF_v1_0 phases 2+
  mirror_pair: none
estimated_phases: 4
estimated_total_sessions: 6–9
---

# MARSYS-JIS Platform Improvements for MCP Effectiveness — Brief v1.0

**Project:** MARSYS-JIS Jyotish Instrument
**Workstream:** MCP_PLATFORM_IMPROVEMENTS — concurrent workstream, sibling to MCP_BRIEF
**Date:** 2026-05-21
**Status:** DRAFT — awaiting native approval to seal
**Author:** Claude (Cowork session)

---

## §1 — Context: Why This Now

The native asked: *"from the perspective of the current architecture of the product we have, what should we do to make this better so that Claude Chat and Claude Cowork will be more effective with user requests on astrology?"*

The companion brief (`MCP_BRIEF_v1_0.md`) covers the **transport layer**: exposing what exists, with discipline, over MCP. This brief covers the **platform layer**: investments in MARSYS-JIS itself that would make every MCP call meaningfully better — and benefit the web pipeline too. These are not MCP-specific; they are products of the realisation that "exposing the system over MCP" forces us to look hard at the system's interaction surface.

Four investments emerged from the same 2026-05-21 brainstorm pass:

1. **Canonical Query Cache** — the single highest cost/latency/quality lever.
2. **Domain-specific Advisory Tools** — closer to how users actually ask questions.
3. **Semantic Neighborhood Tools** — turning the corpus from a lookup table into a navigable graph.
4. **Asset Legibility Audit** — making MSR signals + CGM nodes/edges self-describing.

Each is independently shippable, parallelizable with the MCP transport phases, and benefits both MCP and web consumers.

---

## §2 — Decisions Settled (via brainstorming with native, 2026-05-21)

The strategic call settled in the same session was:

| # | Decision | Native's Call |
|---|---|---|
| D1 | Ship sibling brief now, separate from MCP_BRIEF | **Yes.** Keeps transport vs platform investments cleanly separated. Allows MCP_BRIEF phases 1-2 to land while platform improvements run in parallel. |
| D2 | Scope of v1 platform improvements | The four items above (cache, advisory tools, semantic neighborhood, legibility audit). Defer asset-side restructuring (UCN re-sectioning, CGM edge-type expansion) to a separate workstream if motivated by observed gaps. |
| D3 | Sequencing relative to MCP_BRIEF | Phase MCP-P1 (canonical cache) can ship before MCP_BRIEF Phase 2 — its absence does not block the MCP server. Phase MCP-P2-P4 can ship in parallel with MCP_BRIEF Phase 3 (primitives) or after. |
| D4 | Web pipeline parity | Every improvement lands in the web pipeline first (used by `/api/chat/consume`) and is then exposed via MCP. No MCP-only code paths. |

---

## §3 — Strategic Placement

This workstream is platform-layer additive. It introduces:

- New retrieval tools (in `platform/src/lib/retrieve/`) — adds to the 30, does not modify them.
- A new canonical asset class (the query cache) registered in `CAPABILITY_MANIFEST.json`.
- New columns on `msr_signals` and `l25_cgm_nodes`/`l25_cgm_edges` (the legibility audit).
- New columns/tables for semantic-neighborhood-precomputed indexes if warranted.

It does NOT:
- Modify the planner prompt (those changes are M-arc territory).
- Modify the orchestrator's synthesis logic.
- Change the L2.5 corpus authoring discipline.
- Pre-build for macro phases later than M5.

```
                MCP_BRIEF_v1_0 (transport)
                       │
                       │ uses
                       ▼
    ┌──────────────────────────────────────────┐
    │  MCP_PLATFORM_IMPROVEMENTS (this brief)   │
    │  ┌──────────────────────────────────┐    │
    │  │  Canonical Query Cache (P1)      │    │  ← cached high-frequency answers
    │  │  Advisory Tools (P2)             │    │  ← predict_period, assess_decision, etc.
    │  │  Semantic Neighborhood (P3)      │    │  ← find_similar_signals, find_related_questions
    │  │  Asset Legibility Audit (P4)     │    │  ← claude_summary on MSR, human_label on CGM
    │  └──────────────────────────────────┘    │
    └──────────────────────────────────────────┘
                       │
                       │ adds tools to / annotates assets in
                       ▼
              Existing platform stack
              (retrieval tools, signal store,
               orchestrator, web /consume chat)
```

Web `/api/chat/consume` benefits identically to MCP `/api/mcp/execute`. No code-path forking.

---

## §4 — The Four Investments

### §4.1 — Investment P1: Canonical Query Cache

**Problem:** End-user astrology questions cluster heavily around ~30-50 archetypal queries. "How is the next year looking?", "What does my chart say about marriage?", "Health outlook for this dasha?", "Should I take this job?", "When is a good time to start a business?", etc. Each runs the full pipeline today — planner + 5-10 tools + synthesis — costing 30-90s and ~$0.05-0.20 per call. The same answer would be the same answer next week.

**Investment:** A `canonical_queries` table + a `query_canonical(intent_id)` retrieval tool. For each canonical intent:

- Native (with Claude assist) authors a polished, reviewed answer once.
- Answer stored with full citations to MSR/UCN/CDLM/CGM/RM source IDs.
- Asset bundle stamped with `last_validated_at` and `freshness_window_days`.
- Cache invalidated automatically when a source signal updates or freshness expires.

**Schema sketch:**

```sql
CREATE TABLE canonical_queries (
  intent_id text PRIMARY KEY,            -- e.g. "next_12_months_outlook"
  intent_label text NOT NULL,             -- human label
  intent_description text NOT NULL,       -- when this matches a user query
  question_archetype text NOT NULL,       -- the canonical question form
  example_questions text[],               -- 3-5 ways users phrase this
  query_class text NOT NULL,              -- holistic | predictive | etc.
  answer_markdown text NOT NULL,          -- the polished answer
  citations jsonb NOT NULL,               -- [{signal_id, asset_id, section}]
  parameters jsonb,                       -- e.g. {time_window: "12_months"}
  last_validated_at timestamptz NOT NULL,
  freshness_window_days int NOT NULL DEFAULT 30,
  invalidates_on_signals text[],          -- signal_ids that trigger refresh
  authored_by text NOT NULL,
  authored_at timestamptz NOT NULL,
  version int NOT NULL DEFAULT 1
);
```

**Retrieval flow:**

1. Planner adds an early step: `match_canonical_intent(query) → intent_id | null`.
2. If matched and not stale: return cached answer with refresh metadata. End.
3. If not matched or stale: fall through to full pipeline; flag for human review of whether this should become a new canonical.

**Tool surfaces:**

- New retrieval tool `query_canonical` exposed in the planner's tool list (web side benefits).
- New MCP tool `query_canonical(intent_id?)` exposed in v2 of MCP (after this phase ships).
- Admin UI `/admin/canonical_queries` for native to author, edit, validate.

**Expected impact:** 60-80% of MCP/web queries served from cache. 95%+ cost/latency reduction on those. Most-asked questions get the most-polished answer.

**Risks:**

- Stale cache returning outdated guidance. Mitigated by `invalidates_on_signals` + `freshness_window_days`.
- Canonical answers drifting from current corpus. Mitigated by quarterly re-validation cadence.
- Intent matching false positives (different question, same archetype). Mitigated by similarity threshold + fallback to full pipeline if confidence low.

**Estimated:** 2-3 sessions. Phase MCP-P1.

### §4.2 — Investment P2: Domain-specific Advisory Tools

**Problem:** Today's tools are mostly "fetch data from corpus." User questions are advisory ("should I do X?", "what's the outlook for Y?"). The orchestrator translates between them via the planner, but the planner has to reinvent the framing each time. Advisory framing is brittle in the planner prompt.

**Investment:** A small set of advisory retrieval tools that bake the framing into the tool itself:

| Tool | Purpose | Backing |
|---|---|---|
| `predict_period(start_date, end_date, focus?)` | Predictive synthesis for a date window. Returns ranked themes, key transit events, dasha context, confidence per theme. | Wraps `ask_madhav` internally with a predictive-framed prompt + curated tool list (MSR forward-looking + ephemeris + dasha + transit_event + CGM). |
| `assess_decision(decision_type, options[], context?)` | "Should I do A or B?" with chart-based scoring per option. | Wraps `ask_madhav` with a decision-framed prompt + per-option scoring rubric. |
| `find_remedies(concern, severity?, modality_preference?)` | Remedial measures (mantra, gemstone, charity, fasting, ritual) with classical backing. | Wraps `remedial_codex_query` + classical_text_search + MSR contextualisation. |
| `compare_periods(period_a, period_b, focus?)` | Temporal comparative analysis. | Wraps `temporal` + `query_dasha_periods` + MSR overlay. |

Each is a thin wrapper: a curated planner prompt + a curated tool list + a structured response shape. They become exposable as MCP tools in MCP_BRIEF Phase 3+.

**Why not just "ask_madhav with the right query"?** Three reasons:
1. Framing consistency — a `predict_period` call always returns the same response shape; Claude can rely on it.
2. Planner reliability — instead of trusting the planner to identify a predictive query and route correctly, the tool itself sets the query class.
3. Discoverability — Claude sees a `predict_period` tool and knows what's available; with only `ask_madhav` it has to guess what's possible.

**Estimated:** 2 sessions. Phase MCP-P2.

### §4.3 — Investment P3: Semantic Neighborhood Tools

**Problem:** We have 768-dim Vertex embeddings on every chunk in `rag_embeddings` and every message in `conversation_message_embeddings`. We use them only for `vector_search` (text → top-k chunks). The corpus is more navigable than that:

**Investment:** Two new tools that turn embeddings into a research affordance:

| Tool | Purpose | Mechanism |
|---|---|---|
| `find_similar_signals(signal_id, top_k?, min_similarity?)` | "What other MSR signals live near this one in concept space?" | Cosine similarity over MSR signal embeddings. |
| `find_related_questions(query, top_k?)` | "What past queries are semantically similar to this one, and how were they answered?" | Cosine over `conversation_message_embeddings` + return the assistant's prior answer. |

Asset-side prereq: ensure every MSR signal has an embedding row. `rag_embeddings` already covers chunks at the chunk level; we may need a per-signal aggregation pass. (1 ETL session, included in phase scope.)

**Why these matter:**

- `find_similar_signals` is the foundation for serendipitous synthesis — "I'm looking at career signals; what unexpected health signals live near them?" Cross-domain discovery without the planner having to know to look.
- `find_related_questions` lets Claude learn from prior answers — both for caching ("this exact question was answered three weeks ago") and for analogical reasoning ("a similar question about a different period was answered like this").

Both also benefit the web /consume chat — power-user "show me adjacent signals" affordances become available.

**Estimated:** 2 sessions. Phase MCP-P3.

### §4.4 — Investment P4: Asset Legibility Audit

**Problem:** MSR signals, UCN sections, CGM nodes/edges were authored for internal use — assumed orchestrator context, you-as-author context, the synthesis prompt's framing. When exposed verbatim via MCP (e.g., via `read_asset` or in a citation payload), Claude (the external client) may not have enough context to interpret them well. This degrades MCP answer quality silently.

**Investment:** A focused audit pass adding two new columns:

- `msr_signals.claude_summary text` — one-to-three-sentence plain-language interpretation of the signal, written for an LLM with no prior context. Surfaces what the signal claims, why it matters, and what would falsify it.
- `l25_cgm_nodes.human_label text` + `l25_cgm_edges.human_label text` — short labels (5-15 words) describing the node/edge in plain language. The internal `node_id` ("Moon_in_2nd_navamsa") becomes a `human_label` ("Moon in 2nd house of D9 — emotional speech and family wealth karaka").

**Authoring strategy:**

- Generate first drafts via an LLM pass over each signal/node/edge.
- Native reviews + corrects (high-leverage; ~499 signals, ~N nodes, ~N edges; estimate 2-4 sessions of review).
- Bake into the source markdown for each asset (so the next CGM v10 / MSR v6 carries it forward natively).

**Validation:** Held-out test — give Claude (cold, no resources) a set of 20 MSR signal payloads with `claude_summary` vs without; have it write a sentence about each; rate which version produces accurate interpretation. Target: ≥90% accuracy with `claude_summary`; baseline likely 50-65% without.

**Estimated:** 2-3 sessions. Phase MCP-P4.

---

## §5 — Phasing

| Phase | Investment | Parallelizable with | Sessions |
|---|---|---|---|
| MCP-P1 | Canonical Query Cache | MCP_BRIEF Phase 2 (after P1 ships, Phase 2 can expose `query_canonical` as MCP tool) | 2-3 |
| MCP-P2 | Advisory Tools | MCP_BRIEF Phase 3 (advisory tools exposed as MCP primitives in v2) | 2 |
| MCP-P3 | Semantic Neighborhood Tools | MCP_BRIEF Phase 3 (same as P2) | 2 |
| MCP-P4 | Asset Legibility Audit | Any time; benefits everything downstream | 2-3 |

No hard dependencies between phases. P1 has the highest expected impact and should ship first.

---

## §6 — Acceptance Criteria (workstream-level)

- AC.1 — Canonical Query Cache: ≥30 canonical queries authored; cache-hit rate on held-out user query corpus ≥50%; cached answer latency <500ms p95.
- AC.2 — Advisory Tools: 4 tools shipped (`predict_period`, `assess_decision`, `find_remedies`, `compare_periods`); each returns structured response; web pipeline planner uses each correctly on test corpus.
- AC.3 — Semantic Neighborhood: 2 tools shipped (`find_similar_signals`, `find_related_questions`); MSR signal embedding coverage = 100%; user-facing demo of "show me adjacent signals" in web UI.
- AC.4 — Asset Legibility Audit: ≥95% of MSR signals have `claude_summary`; ≥95% of CGM nodes/edges have `human_label`; held-out test shows ≥25 percentage point improvement in cold-Claude interpretation accuracy.

---

## §7 — Scope Boundary

### §7.1 — `may_touch`

```
platform/src/lib/retrieve/                                                    # APPEND new tools
platform/src/lib/retrieve/canonical_query.ts                                  # CREATE — P1
platform/src/lib/retrieve/predict_period.ts                                   # CREATE — P2
platform/src/lib/retrieve/assess_decision.ts                                  # CREATE — P2
platform/src/lib/retrieve/find_remedies.ts                                    # CREATE — P2
platform/src/lib/retrieve/compare_periods.ts                                  # CREATE — P2
platform/src/lib/retrieve/find_similar_signals.ts                             # CREATE — P3
platform/src/lib/retrieve/find_related_questions.ts                           # CREATE — P3
platform/src/lib/retrieve/index.ts                                            # APPEND only
platform/supabase/migrations/071_canonical_queries.sql                        # CREATE — P1
platform/supabase/migrations/072_msr_claude_summary.sql                       # CREATE — P4
platform/supabase/migrations/073_cgm_human_labels.sql                         # CREATE — P4
platform/supabase/migrations/074_msr_signal_embeddings.sql                    # CREATE — P3 (if per-signal embedding aggregation needed)
platform/src/app/admin/canonical_queries/                                     # CREATE — P1 admin UI
025_HOLISTIC_SYNTHESIS/MSR_v5_1.md                                            # BUMP — P4 (claude_summary column added)
025_HOLISTIC_SYNTHESIS/CGM_v9_1.md                                            # BUMP — P4 (human_label column added)
00_ARCHITECTURE/CAPABILITY_MANIFEST.json                                      # APPEND — canonical_queries asset, new tool entries
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md → v2_1                                 # BUMP — add canonical-cache early-return logic + advisory-tool descriptions
```

### §7.2 — `must_not_touch`

```
01_FACTS_LAYER/                                          # L1 facts sealed
platform/src/app/api/chat/consume/route.ts               # orchestrator unchanged
platform/src/app/api/mcp/                                # owned by MCP_BRIEF
platform-mcp/                                            # owned by MCP_BRIEF
00_ARCHITECTURE/MACRO_PLAN_v2_0.md                       # macro arc unchanged
00_ARCHITECTURE/PROJECT_ARCHITECTURE_v2_2.md             # architecture principles unchanged
```

---

## §8 — Proposed §E Row (for native review on seal)

Add to `CLAUDE.md §E` after the MCP_BRIEF row:

> - **MCP_PLATFORM_IMPROVEMENTS — Platform investments for MCP effectiveness** — canonical_id `MCP_PLATFORM_IMPROVEMENTS_BRIEF`, path `00_ARCHITECTURE/BRIEFS/MCP_PLATFORM_IMPROVEMENTS_BRIEF_v1_0.md`. **STATUS: PHASE_MCP_P1_PENDING.** Workstream declared 2026-05-21, sibling to MCP_BRIEF. Scope: four platform-layer investments — canonical query cache (P1), advisory tools (P2), semantic neighborhood tools (P3), asset legibility audit (P4). Each parallelizable with MCP_BRIEF phases 2+. Benefits both web /consume chat and MCP /api/mcp/execute. No mirror pair.

Header sentence updates: count of concurrent workstreams bumps to **eleven**.

---

## §9 — Risks & Open Questions

| Risk / Question | Mitigation / Resolution |
|---|---|
| **R1.** Canonical cache becomes a maintenance burden (50+ answers to re-validate quarterly). | Quarterly cadence in `ONGOING_HYGIENE_POLICIES`; LLM-assisted re-validation pass before native review; freshness windows tuned per query class. |
| **R2.** Advisory tools become thin wrappers that the planner could have produced anyway, adding complexity without value. | Validate by A/B testing on held-out queries: advisory-tool vs raw `ask_madhav` with equivalent prompt. Ship only the advisory tools that show measurable framing-consistency or quality improvement. |
| **R3.** Semantic neighborhood tools may surface noise (similarity ≠ relevance). | Calibrate `min_similarity` thresholds per tool; require human review of top results on a sample before exposing externally. |
| **R4.** Asset legibility audit is a lot of native review time (~499 signals + CGM nodes/edges). | Batch by domain (audit career signals first; ship; gather feedback; audit health; etc.). Defer CGM coverage if MSR alone produces measurable improvement. |
| **OQ1.** Should canonical query cache support per-user customisation (e.g., one user wants "next 12 months" framed by their professional concerns; another by health)? | v1: no. Singleton chart + singleton query archetype. Per-user customisation considered if multi-native lands. |
| **OQ2.** Should advisory tools accept free-text or only structured input (decision_type as enum, options as typed)? | Recommend: structured input only. Forces clarity at the call site; reduces planner ambiguity. Free-text always available via `ask_madhav`. |
| **OQ3.** Should asset legibility audit also cover UCN sections and CDLM cells, or stop at MSR + CGM? | Recommend: stop at MSR + CGM for v1; defer UCN/CDLM to v2 based on observed gaps. |

---

## §10 — Cadence & Sealing

Per CLAUDE.md §M: daily sessions, closed-artifact-per-session, red-team passes per §IS.8 cadence.

**Sealing protocol:**

1. Native reviews this DRAFT.
2. On acceptance:
   - Status flips DRAFT → CURRENT.
   - `sealed_on` + `sealed_by` populated.
   - `CLAUDE.md §E` updated per §8.
   - `CLAUDECODE_BRIEF_MCP_P1_v1_0.md` authored to drive Phase P1 execution.

**Workstream close (post-Phase P4):**

- `MCP_PLATFORM_IMPROVEMENTS_CLOSE_v1_0.md` sealing artifact.
- This brief moves SUPERSEDED-AS-COMPLETE.
- Tools and assets remain LIVE.

---

*End of MCP_PLATFORM_IMPROVEMENTS_BRIEF_v1_0.md (DRAFT 2026-05-21). Sibling to MCP_BRIEF_v1_0.md. Investments are platform-layer, additive, parallelizable, and benefit both web and MCP consumers.*
