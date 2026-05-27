---
artifact: MODERNIZATION_AUDIT_PROMPT_v1_0.md
purpose: Pasteable prompt for Claude Code (project folder, main branch) to perform an extensive grounding audit of PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0
status: prompt (read-only audit; no implementation)
date: 2026-05-27
expose_to_chat: false
---

# Prompt — Extensive grounding audit of the Platform Modernization Master Plan

Paste everything below the line into Claude Code running on the project on `main`.

---

You are performing an **extensive, read-only grounding audit** of a modernization plan against the actual
codebase. The goal is **zero surprises at implementation time**: every claim, assumption, conflict, gap,
and risk must be surfaced and verified now. You will NOT edit code and you will NOT edit the plan — you
produce one structured audit report.

## Operating rules (non-negotiable)
- **Read-only.** No code changes, no migrations, no edits to any plan. Audit only.
- **Verify, never trust.** Every factual claim in the plan must be checked against the code on `main` HEAD.
  Cite `path:line` for every verdict. If you cannot verify, say so — do not guess.
- **Classify every claim** as: `CONFIRMED` / `WRONG` / `PARTIALLY-CORRECT` / `UNVERIFIABLE`, each with
  evidence and a one-line note.
- **Disagree openly.** If the plan's design is unsound, ambiguous, or under-specified, say so with reasoning.
- Record the `git` state (branch, HEAD sha, dirty?) at the top of your report.

## Read first (the plan + its constituents)
1. `00_ARCHITECTURE/PLATFORM_MODERNIZATION_MASTER_PLAN_v2_0.md` — the plan under audit (primary).
2. Its constituents (verify each path EXISTS as cited — flag path drift):
   `00_ARCHITECTURE/PLATFORM_MODERNIZATION_MASTER_PLAN_v1_0.md`,
   `00_ARCHITECTURE/PORTAL_NORTH_STAR_ARCHITECTURE_v1_0.md` (+ `.svg`),
   `00_ARCHITECTURE/PLATFORM_REBUILD_ARCHITECTURE_v1_0.md`,
   `00_ARCHITECTURE/DATA_LAYER_REBUILD_TARGET_SPEC_v1_0.md`,
   `00_ARCHITECTURE/TARGET_ARCHITECTURE_REPORT_v1_0.md`,
   `00_ARCHITECTURE/BRIEFS/FACT_ENGINE_PYJHORA_BRIEF_v1_0.md`,
   `00_ARCHITECTURE/STRUCTURAL_FACT_LAYER_SPEC_v1_0.md`,
   `00_ARCHITECTURE/BRIEFS/TOOL_PORTFOLIO_PLAN_v1_4.md` (note: under BRIEFS/, not 00_ARCHITECTURE/ — confirm),
   `00_ARCHITECTURE/INVESTIGATION/TOOL_PORTFOLIO_REALITY_REPORT.md`,
   `00_ARCHITECTURE/MSR_UCN_CONTAMINATION_AUDIT_v1_0.md`,
   `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` + `manifest_overrides.yaml`.

## High-stakes claims to verify explicitly (the plan leans on these — prove or disprove each)
1. **Tenant-key state:** `charts.client_id` type/semantics; the chart_id-uuid vs chart_id-text vs native_id
   vs client_id split across migrations (001/006/008/009/022/023/024/025/031/033/058/071/072/110). Which
   tables have which key + type? Is the data plane really single-native?
2. **De-judgment floors:** `platform/src/lib/retrieve/msr_sql.ts:20/24/33/44` — `DEFAULT_CONFIDENCE_FLOOR`,
   `FINANCE_WEALTH_CONFIDENCE_FLOOR`, `PANCHA_MP_CLIQUE`, `LL1_PRODUCTION_WEIGHTS`. Confirm + find peers
   (`query_signals.ts`, `query_varshphal.ts` redaction).
3. **Two pipelines:** confirm both live inside `platform/src/app/api/chat/consume/route.ts`, branch on
   `R11V2_USE_ADAPTERS`; Classic = `createOrchestrator` path, Claude-style = `getAdapter`+`runAgenticLoop`.
   Identify EVERY shared stage that the plan says moves to `lib/pipelines/shared/`.
4. **B.11 citation-gate asymmetry:** confirm `validateCitationsForStream` runs on the legacy path only and
   NOT the adapter/agentic path. This gates the legacy-delete ordering (G5) — confirm it's real.
5. **TierPicker == depth selector:** confirm `platform/src/components/consume/TierPicker.tsx` maps
   Deep/Study/Brief → super_admin/acharya_reviewer/client.
6. **Tier/disclosure subsystem surface:** `lib/disclosure/`, `X-MCP-Audience-Tier`, `mcp_api_keys.audience_tier`
   (mig 070/117), `tier_catalog.ts`, the `acharya`/`acharya_reviewer` split, hard-403 health routes.
7. **Per-chart Firebase user:** `platform/src/app/api/clients/route.ts` POST creates a Firebase user per chart.
8. **L2 already archived** (`99_ARCHIVE/02_ANALYTICAL_LAYER/`); confirm no live L2 in the source tree.
9. **Dual-channel duplication:** same engines in `platform/src/lib/retrieve/*` AND `platform-mcp/src/tools/*`;
   `MCP_TO_RETRIEVAL_TOOL` aliases, `SURGICAL_TOOLS` dups, the ~6 portal↔MCP tool-name splits.
10. **Gateway / unified contract / null query_schema:** confirm the manifest `query_schema` fields are null;
    confirm there is no gateway (`search_tools`/`invoke_tool`) today; confirm 17 ghost tools + count
    discrepancies (server.ts vs catalog vs RETRIEVAL_TOOLS vs manifest).
11. **GCP map:** Cloud Run services (`amjis-web/sidecar/mcp`), the Cloud Run **Job** `marsys-build-pipeline-job`
    (exists? triggered how?), Cloud SQL tier (`db-g1-small`?), GCS buckets, Vertex embeddings, dual deploy
    paths (GitHub Actions + Cloud Build), MCP on legacy GCR + `--allow-unauthenticated`, hardcoded DB
    passwords in scripts, Cloud Scheduler (real or comment-only?).
12. **JH engine / L0:** confirm no JH-equivalent natal engine exists yet; confirm what L0/classical assets
    exist; confirm the FORENSIC v8.0 oracle + ayanamsha pinning state.
13. **LEL boundary:** confirm whether LEL is currently consumed in any build/churn path vs serve-time only;
    confirm the per-query LEL toggle feeds synthesis (not retrieval/planning).

## Required output — a structured report with multi-dimensional matrices
Write the report to `00_ARCHITECTURE/INVESTIGATION/MODERNIZATION_AUDIT_REPORT_v1_0.md`. Include, in this order:

**0. Executive summary** — top findings, overall plan soundness verdict, and the prioritized
"MUST-RESOLVE-BEFORE-IMPLEMENTATION" list.

**1. Claim-Verification Matrix** — one row per discrete claim in the plan (walk §1–§15 exhaustively):
`| Plan ref (§) | Claim | Evidence (path:line) | Verdict (CONFIRMED/WRONG/PARTIAL/UNVERIFIABLE) | Note |`

**2. Conflict Matrix** — three sub-types: (a) plan-vs-code, (b) plan-vs-constituent-plan, (c) intra-plan
(internal contradictions). `| Conflict | Source A | Source B | Evidence | Severity | Resolution proposal |`

**3. Gap Matrix** — what is missing / unowned / underspecified for implementation:
`| Gap | Where it bites | Owner track | Severity | What's needed |`

**4. Complexity & Roadblock Matrix** — `| Item | Blast radius (files/surfaces) | Complexity (L/M/H) | Roadblock | Mitigation |`

**5. Sequencing & Dependency Matrix** — validate the 5 hard gates (G1–G5) and the 5 waves; find hidden
dependencies, ordering errors, and anything that cannot be parallel-safe as claimed. `| Wave/Track | Depends on | Hard gate | Risk if reordered |`

**6. Technical / Architectural Review** — per track (Engine/Data, Tooling, Multi-tenancy/Build, Portal,
Serve-time/Learning + Governance Track 0): soundness, missing design, integration seams, data-model risks.

**7. UI/UX Review** — the portal nav + page model (dashboard role-gating, Profile/Build/Consult/Panchang,
chart switcher, sharing UI, Command Center, multi-tenant cockpit/panchang). Heuristic review + each user
flow (guest, super-admin, shared-access guest) + a matrix: `| Surface | Current state | Target | Gap | UX risk |`.
Flag where the plan's UX is under-specified or breaks existing flows.

**8. Naming-Taxonomy Verification** — confirm each §3 inconsistency exists; for each proposed rename, give the
blast radius (grep counts) + a safe-migration note. `| Concept | Current names (cited) | Proposed canonical | Blast radius | Risk |`

**9. Elimination-Safety Matrix** — for each §6 deletion: confirm it is truly dead, enumerate ALL consumers
(grep transitive), and rate safe-to-remove. `| Item | Cited path | Consumers found | Truly dead? | Safe-to-remove | Note |`

**10. GCP Review** — confirm the §4 current map; assess each improvement opportunity for feasibility +
prerequisites + cost direction.

**11. Open-questions resolution** — for each §9 open decision, state what the code implies the answer should
be (where determinable).

## Discipline
- Be exhaustive — the explicit goal is that implementation finds **not a single inconsistency** that this
  audit didn't surface. Prefer over-reporting to silence.
- Every verdict carries evidence. Mark confidence. Where the plan is right, say so plainly (don't only hunt
  for errors — a validated claim is a finding too).
- Do not begin any implementation. This is the audit pass of the Cowork ⇄ Claude Code ⇄ other-LLM loop.
