---
artifact: FILE_REGISTRY_v1_14.md
version: "1.14"
status: "SUPERSEDED (2026-04-27 — content absorbed into CAPABILITY_MANIFEST.json; retained in place for historical audit and provenance)"
date: 2026-04-27
scope: Delta registry for Madhav_M2A_Exec_13 — B.7 Router + Plan Library.
supersedes: FILE_REGISTRY_v1_13.md (2026-04-27, Madhav_M2A_Exec_12)
schema_version: 1.8
changelog:
  - "v1.14 (2026-04-27, Madhav_M2A_Exec_13 close — B.7 Router + Plan Library):"
  - "  (a) §9.1 — FILE_REGISTRY row updated to v1.14 (this file); FILE_REGISTRY_v1_13 flipped to SUPERSEDED."
  - "  (b) §9.16 NEW — Exec_13 deliverables: QueryPlan schema, plan taxonomy, router prompt, router.py implementation, FastAPI router endpoint, TypeScript shim, golden eval 20/20."
  - "  (c) §9.2–§9.15 — unchanged from v1.13 by reference."
  - "v1.13 (2026-04-27, Madhav_M2A_Exec_12): B.6 Hybrid Retrieval Library + M2B milestone close."
  - "v1.12 (2026-04-27, Madhav_M2A_Exec_11): B.5 Session 3 complete."
---

# MARSYS-JIS File Registry — Final Corpus (v1.14)

**Subject**: Abhisek Mohanty, b. 1984-02-05, 10:43 IST, Bhubaneswar
**Branch**: `feature/amjis-platform`
**Registry date**: 2026-04-27 (v1.14 published at Madhav_M2A_Exec_13 close; supersedes v1.13)

---

## §9.1 — Registry version row

| artifact | version | status | date |
|---|---|---|---|
| `FILE_REGISTRY_v1_14.md` | 1.14 | CURRENT | 2026-04-27 |
| `FILE_REGISTRY_v1_13.md` | 1.13 | SUPERSEDED | 2026-04-27 |
| `FILE_REGISTRY_v1_12.md` | 1.12 | SUPERSEDED | 2026-04-27 |
| `FILE_REGISTRY_v1_11.md` | 1.11 | SUPERSEDED | 2026-04-26 |
| `FILE_REGISTRY_v1_10.md` | 1.10 | SUPERSEDED | 2026-04-27 |

---

## §9.2–§9.15 — Earlier deliverables

See `FILE_REGISTRY_v1_13.md §9.2–§9.15` — unchanged.

---

## §9.16 — Madhav_M2A_Exec_13 deliverables (B.7 Router + Plan Library)

### §9.16.1 — Schema (Python sidecar)

| Path | Version | Status | Role |
|---|---|---|---|
| `platform/python-sidecar/rag/schemas.py` | 1.0 | CURRENT | Pydantic schemas. B.7 addition: `QueryPlan` model — 7 fields: `query_text`, `plan_type` (Literal, 6 values), `significance_score` (ge=0.0, le=1.0), `domains`, `actor`, `wcr_forced`, `routing_rationale`. Imports: `pydantic.BaseModel`, `pydantic.Field`, `typing.Literal`. |

### §9.16.2 — Taxonomy and prompt documents

| Path | Version | Status | Role |
|---|---|---|---|
| `035_DISCOVERY_LAYER/QUERY_TAXONOMY/plans_v1_0.md` | 1.0 | CURRENT | QueryPlan type taxonomy. Defines 5 primary plan types (interpretive_multidomain, interpretive_single, factual, timing, meta) + static fallback (exploratory). Contains significance-scoring rubric, WCR enforcement rule, downstream behavior matrix, worked examples drawn from existing QUERY_TAXONOMY corpus. |
| `035_DISCOVERY_LAYER/PROMPTS/claude/router_v1_0.md` | 1.0 | CURRENT | Router system prompt for claude-opus-4-6. Contains: classification task + output format (4-field JSON: plan_type, significance_score, domains, routing_rationale); significance-scoring rubric verbatim; 5 plan type definitions; disambiguation rules A (document count ≠ domain count) and B (time-gated validity queries → timing); 7 worked examples (1 per primary type + 2 targeted disambiguation examples). Model note: "Uses claude-opus-4-6 per native decision Q1 (2026-04-27). CQ6 carry-forward: upgrade to claude-opus-4.7 when available — see CLAUDECODE_BRIEF CF.1." |

### §9.16.3 — Code (Python sidecar — router)

| Path | Version | Status | Role |
|---|---|---|---|
| `platform/python-sidecar/rag/router.py` | 1.0 | CURRENT | Query router. `ANTHROPIC_MODEL = "claude-opus-4-6"`. Implements: `_load_router_prompt()` (reads router_v1_0.md, strips YAML frontmatter, path resolved relative to repo root); `classify_query(query) -> QueryPlan` (Anthropic SDK call, temp=0.0, max_tokens=300, JSON parse, WCR enforcer post-parse, static fallback on any exception). Static fallback: plan_type="exploratory", actor="static_fallback", significance_score=0.5, domains=["all"], wcr_forced=False. |
| `platform/python-sidecar/rag/routers/rag_router.py` | 1.0 | CURRENT | FastAPI router for POST /rag/route. `RouteRequest(BaseModel)`: `query: str = Field(..., min_length=1, max_length=2000)`. Endpoint returns `{"plan": plan.model_dump()}`. HTTP 500 on exception. |
| `platform/python-sidecar/main.py` | 1.2 | CURRENT | FastAPI app entry point. Extended: imports `rag_router_router`; registers at `/rag` prefix with verify_api_key dependency. Full path: POST /rag/route. |

### §9.16.4 — Code (TypeScript — router client)

| Path | Version | Status | Role |
|---|---|---|---|
| platform/src/lib/rag/routerClient.ts | 1.0 | DELETED (Pipeline-Transform-S1 2026-05-11) | TypeScript shim for POST /rag/route — deleted when legacy RAG route removed. |

### §9.16.5 — Evaluation artifacts

| Path | Version | Status | Role |
|---|---|---|---|
| `verification_artifacts/RAG/router_eval_v1_0.json` | 1.0 | CURRENT | Golden router eval results. Session: Madhav_M2A_Exec_13. Model: claude-opus-4-6. Total: 20/20 PASS (100%). AC.7 gate (≥18/20): PASS. AC.8 WCR invariant: 15/15 interpretive plans have wcr_forced=True (100%). Distribution: interpretive_multidomain×11 (11/11), interpretive_single×4 (4/4), timing×5 (5/5). Note: 5 queries required prompt disambiguation refinements (rules A+B added to router_v1_0.md) to achieve 20/20. |

## §9.18 — Codex onboarding governance registration

| Path | Version | Status | Role |
|---|---|---|---|
| `00_ARCHITECTURE/CROSS_CUTTING_DECISION_REGISTER_v1_0.md` | 1.0 | LIVING | Append-only, tool-neutral register for cross-cutting decisions; read immediately after CURRENT_STATE by Claude Code and Codex. CCD-001 establishes the shared-brain onboarding convention. |
