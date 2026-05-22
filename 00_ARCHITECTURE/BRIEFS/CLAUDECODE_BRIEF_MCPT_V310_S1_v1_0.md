---
artifact: CLAUDECODE_BRIEF_MCPT_V310_S1_v1_0.md
status: ACTIVE
version: 1.0
project: MCP Transformation
authored_by: Claude (Cowork session, Opus 4.7)
authored_on: 2026-05-22
parent_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md (collective v3.1.0 brief; this brief is the per-sub-phase break-out for S1)
parent_plan: 00_ARCHITECTURE/CONDUCTOR/MCP_TRANSFORMATION_PLAN_v1_0.md
parent_memory: 00_ARCHITECTURE/PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md
audience: Claude Code sub-agent (running in Antigravity IDE) spawned by the Conductor on WT-A
session_id: v3.1.0-S1
worktree_path: /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN
branch: feature/mcpt-foundation
implementation_surface: Claude Code extension in Google Antigravity IDE
disposition: code-level fixes from MCP_DIAGNOSIS_2026-05-22.md — F.1 through F.5 + F.7 (NOT F.6)
---

# v3.1.0-S1 — Code-Level Fixes

You are a Claude Code sub-agent running in Google Antigravity IDE on worktree `MadhavMCPT-FDN` (branch `feature/mcpt-foundation`). Your job is to land the five v1 diagnosis code fixes that block everything downstream in MCP Transformation v3.1.0.

Read in order before any edit: `PROJECT_MEMORY_MCP_TRANSFORMATION_v1_0.md` (§2 — Cowork is planning, Claude Code is implementation); `MCP_TRANSFORMATION_PLAN_v1_0.md §3, §5, §10`; `MCP_DIAGNOSIS_2026-05-22.md §3, §7`; `MCP_ARCH_v3_PROPOSAL_2026-05-22.md §3.1, §10`; the parent collective brief `CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md §4 — v3.1.0-S1`.

## §1 — Scope

Land fixes **F.1, F.2, F.3, F.4, F.5, F.7** from `CLAUDECODE_BRIEF_MCP_V3_0_v1_0.md §4 / v3.1.0-S1` and `MCP_ARCH_v3_PROPOSAL_2026-05-22.md §10`. **F.6 (`marsys_methodology_block` removal) is explicitly out of scope** — do not touch `platform/src/lib/prompts/templates/shared.ts`.

## §2 — Files in scope (`may_touch`)

```
platform/src/lib/retrieve/vector_search.ts                              # F.1
platform/src/lib/retrieve/msr_sql.ts                                    # F.2 primary
platform/src/lib/retrieve/*.ts                                          # F.2 audit pass (every primitive)
platform-mcp/src/tools/query_chart_facts.ts                             # F.3 enum-derived description
platform-mcp/src/tools/*.ts                                             # F.3 generalized (descriptions from enum/registry)
platform-mcp/cloudbuild.yaml                                            # F.4
platform-mcp/src/auth.ts                                                # F.5 in-memory cache
platform/src/app/api/mcp/primitives/[tool]/route.ts                     # F.7 (remove arbitrateBudgets call site on MCP path)
platform-mcp/test/**                                                    # new integration tests per AC
```

## §3 — Files NOT in scope (`must_not_touch`)

```
platform/src/lib/prompts/templates/shared.ts                            # F.6 is OUT OF SCOPE
platform/src/lib/pipeline/budget_arbiter.ts                             # KEEP for /consume path; only remove MCP call site
platform/src/app/consume/**                                             # web /consume untouched
platform/src/app/api/chat/**                                            # web chat API untouched
01_FACTS_LAYER/**, 025_HOLISTIC_SYNTHESIS/**                            # no data changes in S1
00_ARCHITECTURE/MACRO_PLAN_v2_0.md, PROJECT_ARCHITECTURE_v2_2.md        # no governance edits
platform-mcp/src/bundles/**                                             # S2 territory
platform-mcp/src/resources/**                                           # S3 territory
platform/src/lib/perf/**                                                # S4 territory
```

## §4 — Per-fix specification

### F.1 — `vector_search` placeholder-query bug

File: `platform/src/lib/retrieve/vector_search.ts:236`.

Change: when the embedding query is being computed, prefer `params.text` / `params.query_text` over `plan.query_text` when the latter starts with `surgical_primitive:`:

```ts
const queryText =
  (params?.text as string | undefined) ??
  (params?.query_text as string | undefined) ??
  (plan?.query_text?.startsWith('surgical_primitive:') ? '' : plan?.query_text) ??
  '';
if (!queryText) throw new Error('vector_search: no query text resolved from params or plan');
```

Test (new): `platform-mcp/test/vector_search.integration.test.ts` — calls `vector_search({text:"saturn shadbala bala", top_k:5})` against the deployed MCP and asserts the returned chunks reference Saturn or shadbala (Jaccard ≥ 0.20 with the query).

### F.2 — `params` vs `plan` smuggling audit

Primary file: `platform/src/lib/retrieve/msr_sql.ts`. Known affected fields: `domain`, `limit`, `karakas`.

Audit pass: every file in `platform/src/lib/retrieve/*.ts`. For each, identify filter fields read from `plan.<field>` and add fallback to `params.<field>`:

```ts
const filterDomain = (params?.domain as string | undefined) ?? plan?.domain ?? null;
const filterLimit = (params?.limit as number | undefined) ?? plan?.limit ?? DEFAULT_LIMIT;
```

For each affected file, write an integration test at `platform-mcp/test/primitives/{tool}.integration.test.ts` that calls the tool via MCP with a specific filter (e.g., `domain:"career"`, `limit:3`) and asserts the response respects the filter.

### F.3 — Enum-derived tool descriptions

File: `platform-mcp/src/tools/query_chart_facts.ts:19,54`.

Replace the hand-authored description (which lists fake `dignity`, `nakshatra`, `house_placement`, `divisional_D9` categories) with a function that generates the description at registration time from `platform/src/lib/retrieve/chart_facts_query.ts:21–30` (the `ChartFactsCategory` enum) plus the current coverage state per category (joined from `data_source_expected` if the table exists; otherwise just the enum list).

Generalize: every tool in `platform-mcp/src/tools/*.ts` derives its description from the underlying enum/registry. Author a helper `platform-mcp/src/tools/description_builder.ts`:

```ts
export function buildToolDescription({
  baseDescription,
  enumSource,
  coverageHint,
}: {
  baseDescription: string;
  enumSource: readonly string[];
  coverageHint?: string;
}): string { /* … */ }
```

Test: `platform-mcp/test/tool_descriptions.test.ts` reads the registered MCP tool list and asserts every advertised category for `query_chart_facts` exists in the `ChartFactsCategory` enum.

### F.4 — `cloudbuild.yaml` `MCP_INTERNAL_TOKEN` binding

File: `platform-mcp/cloudbuild.yaml`.

Add a `--update-secrets` flag binding `MCP_INTERNAL_TOKEN` from Secret Manager. Required Cloud Run flag string in the `gcloud run deploy` step:

```yaml
- '--update-secrets=MCP_INTERNAL_TOKEN=mcp-internal-token:latest'
```

Verify: a clean redeploy via `gcloud builds submit --config=platform-mcp/cloudbuild.yaml platform-mcp/` produces a Cloud Run revision where the token is set without operator manual env-var work.

### F.5 — Bearer-key validation cache

File: `platform-mcp/src/auth.ts`.

Add a module-scoped `Map<string, {principal: Principal, expiresAt: number}>` with 60-second TTL. Cache key = SHA-256 of the Bearer token (do not store the raw token). Cache lookup before the PBKDF2 + DB call; cache write after a successful validation. On revocation, the next cache miss after 60s picks up the revocation (acceptable grace per `MCP_DIAGNOSIS §6.1`).

Test: `platform-mcp/test/auth_cache.test.ts` — 100 sequential validations with the same key produce ≥95 cache hits.

### F.7 — `arbitrateBudgets` call-site removal on MCP path

File: `platform/src/app/api/mcp/primitives/[tool]/route.ts` (and any other MCP-path file invoking `budget_arbiter`).

Identify every call site of `arbitrateBudgets()` (or the equivalent function name from `platform/src/lib/pipeline/budget_arbiter.ts`) on a code path that originates from `/api/mcp/`. Remove the invocation; keep the underlying function file intact (the `/consume` path still uses it).

Verify: `grep -rn "arbitrateBudgets\|budget_arbiter" platform/src/app/api/mcp/` returns no matches.

## §5 — Acceptance criteria

Per parent brief §4 — v3.1.0-S1 acceptance criteria AC.S1.1 through AC.S1.8.

## §6 — Workflow

1. `git checkout -b feature/mcpt-foundation` if not already on it; pull latest from `main`.
2. Implement fixes in the order F.1 → F.2 → F.3 → F.4 → F.5 → F.7.
3. After each fix: commit with message `MCPT v3.1.0-S1: F.{N} {short_subject}`.
4. After all fixes: run `cd platform-mcp && npm test` and `cd platform && npm test`; both must pass.
5. Push: `git push origin feature/mcpt-foundation`.
6. Emit the FINAL_SUMMARY (machine-readable; per the Conductor's expected format).

## §7 — Gate command (the Conductor runs this)

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-FDN && \
  ! grep -rn "arbitrateBudgets\|budget_arbiter" platform/src/app/api/mcp/ && \
  grep -q "params?.text" platform/src/lib/retrieve/vector_search.ts && \
  grep -q "update-secrets=MCP_INTERNAL_TOKEN" platform-mcp/cloudbuild.yaml && \
  grep -q "Map<string" platform-mcp/src/auth.ts && \
  cd platform-mcp && npm test 2>&1 | tail -5 && \
  cd ../platform && npm test 2>&1 | tail -5
```

Exit 0 = PASS. Anything else = halt with `GATE_FAILED`.

## §8 — Sealing artifact

`00_ARCHITECTURE/MCPT_V310_S1_CLOSE.md`. Frontmatter status `CLOSED`. Body: per-fix evidence (test names + last passing run timestamp), audit notes on which `plan.*` vs `params.*` smuggling was found per primitive, residuals (none expected).

---

*End of CLAUDECODE_BRIEF_MCPT_V310_S1_v1_0.md. Conductor reads at session spawn; sub-agent reads at session start; gate runs at session close.*
