---
canonical_id: MCP_TOOL_AUDIT_REM_V2_PLAN
version: 1.0
status: ACTIVE
authored: 2026-05-26
description: >
  Comprehensive plan to bring all 40 MCP tools to ≥90% from the Audit 3
  baseline of 69%. Covers the net -2% regression (schema refactors hitting 7
  tools), 4 persistent infrastructure gaps, and 3 data seeding gaps.
  Target: ≥95% full-manifest average after Tier 1+2 work.
---

# MCP Tool Audit Remediation v2 — Full Plan

## 1 — What Happened in Audit 3

**Score:** 69% (was 71% in A2). Net -2% despite real wins.

The wins and losses cancel unevenly:

| Direction | Tools | Delta | Cause |
|---|---|---|---|
| **Wins** | `muhurta_finder`, `query_varshphal`, `query_transit_event`, `read_classical_text` | +4 tools recovered/improved | S1+S2+OPS fixes worked |
| **Losses** | `holistic_bundle`, `multi_school_bundle`, `cross_school_lookup`, `query_ephemeris`, `log_prediction`, `vector_search`, `read_asset` | −7 tools regressed | API schema changes between A2→A3 |
| **Unchanged bad** | `query_cdlm_lookup`, `query_rm_walk`, `temporal`, `get_cgm_subgraph`, `timeline_query`, `query_jaimini_drishti` | 0 | Infrastructure + data gaps |
| **Unchanged partial** | `query_chart_facts` (95%→65%) | −30 | `planet` category 0 rows in DB |

**Root cause of net regression:** 7 tools that scored 95% in A2 dropped to 50% in A3 because the tools changed their required call parameters between builds and callers (including the audit harness) were using the old signatures. These tools are NOT broken — they work correctly when called with the new schemas. Every one of them needs backward-compatible aliases added so old callers keep working.

---

## 2 — Complete Sub-90% Tool Diagnostic

### 2A — ZERO SCORE TOOLS (0%)

| Tool | Root cause | Fix tier |
|---|---|---|
| `query_cdlm_lookup` | `MARSYS_REPO_ROOT` not set on amjis-web; files unreachable | Tier 1 — operator env var |
| `query_rm_walk` | Same | Tier 1 |
| `query_ucn_walk` | Same (implied from same code pattern) | Tier 1 |

**Detail:** S2's `process.cwd()` fix is in the deployed code, but `process.cwd()` resolution is only needed if `MARSYS_REPO_ROOT` is absent. The platform `Dockerfile` sets `ENV MARSYS_REPO_ROOT=/app` in the builder stage but it may not survive into the runner stage. Confirmed fix: set `MARSYS_REPO_ROOT=/app` as a Cloud Run env var on `amjis-web` directly. One env var → 3 tools unblocked.

---

### 2B — SCHEMA REGRESSION TOOLS (50%)

These tools WORK but callers are using old parameter names/shapes. Fix: add backward-compatible input aliases in each tool's Zod schema.

| Tool | Old signature (callers using) | New required signature | Backward-compat fix |
|---|---|---|---|
| `holistic_bundle` | `{bundles: [...]}` | `{query_text: string (min 3)}` | Accept both; coerce `bundles` → `query_text: bundles.join(', ')` |
| `multi_school_bundle` | `{topic: string}` | `{claim: string (min 10)}` | Accept `topic` as alias for `claim` |
| `cross_school_lookup` | `{topic: string}` | `{claim: string}` | Accept `topic` as alias for `claim` |
| `query_ephemeris` | `{date_from, date_to}` | `{date_range: {from, to}}` | Accept flat params and coerce into `date_range` object |
| `log_prediction` | `{confidence: 0.8}` (float) | `{confidence: 'high'/'medium'/'low', falsifier: string}` | Map float → enum (>0.75='high', 0.5-0.75='medium', <0.5='low'); make `falsifier` optional with default "" |
| `vector_search` | `{query: string}` | `{text: string}` | Accept `query` as alias for `text` |
| `read_asset` | `{asset_key: string}` | `{canonical_id: string}` | Accept `asset_key` as alias for `canonical_id` |

These are all 1-3 line additions to existing Zod schemas. No behavior changes, no DB migrations. One session covers all 7.

---

### 2C — INFRASTRUCTURE GAP TOOLS

| Tool | Score | Root cause | Fix tier |
|---|---|---|---|
| `read_asset` | 30% | amjis-mcp image built before S1 COPY lines landed on main | Tier 1 — rebuild amjis-mcp from current main HEAD |
| `temporal` | 20% | `PYTHON_SIDECAR_URL` missing on amjis-web Cloud Run | Tier 1 — operator env var |
| `vector_search` | 25% | Vertex AI embedding backend unreachable | Tier 1 — verify `GCP_PROJECT` + embedding quota; may need re-auth |

**Detail on `read_asset`:** The S1 COPY fix is on main and the code is correct. The `amjis-mcp-00018-n84` image may have been built from a slightly earlier main HEAD using a Docker layer cache that predated the Dockerfile change. A fresh `gcloud builds submit` from current HEAD will include the COPY lines and fully resolve `read_asset`. Expected result: 30% → 95%+.

**Detail on `temporal`:** The call chain is `amjis-mcp` → `amjis-web /api/mcp/primitives/temporal` → platform `temporal.ts` → `PYTHON_SIDECAR_URL`. That env var must be set on `amjis-web`, not `amjis-mcp`. Run:
```bash
gcloud run services describe amjis-web --region=asia-south1 --project=madhav-astrology \
  --format='value(spec.template.spec.containers[0].env)' | tr ',' '\n' | grep PYTHON_SIDECAR
```
If missing:
```bash
SIDECAR_URL=$(gcloud run services describe amjis-sidecar --region=asia-south1 \
  --project=madhav-astrology --format='value(status.url)')
gcloud run services update amjis-web --region=asia-south1 --project=madhav-astrology \
  --update-env-vars="PYTHON_SIDECAR_URL=${SIDECAR_URL}"
```

---

### 2D — DATA GAP TOOLS

| Tool | Score | Root cause | Fix tier |
|---|---|---|---|
| `query_chart_facts` | 65% | `planet` category has 0 rows in `chart_facts` DB | Tier 2 — run extractor for planet category |
| `query_signal_state` | 85% | `signal_activator.py` writes NULL confidence; fallback hardcoded to 0.6 | Tier 2 — fix signal_activator + fallback |
| `get_cgm_subgraph` | 35% | `l25_cgm_nodes` / `l25_cgm_edges` tables empty | Tier 3 (P3) — new seeding script |
| `timeline_query` | 25% | No `l5_timeline` rag_chunks in DB | Tier 3 (P3) — new bootstrap script |

**Detail on `query_chart_facts`:** The `planet` category is declared in the enum but never loaded into the DB. The MCPT build pipeline loaded 2,717 rows across other categories but skipped planet placements. The fix is running `chart_facts_loader.py --category planet` against `FORENSIC_ASTROLOGICAL_DATA_v8_0.md`.

**Detail on `query_signal_state`:** `signal_activator.py` inserts rows with `confidence = NULL`. The retrieval tool falls back to `r.confidence ?? 0.6`, giving uniform 0.6 for all signals. Short-term fix: change the fallback to state-derived: `r.confidence ?? (r.state === 'lit' ? 0.85 : r.state === 'ripening' ? 0.65 : 0.35)`. Long-term: fix `signal_activator.py` to compute and write confidence scores from MSR signal weights.

---

### 2E — QUALITY BELOW 90% (but not fully broken)

| Tool | Score | Cause | Fix |
|---|---|---|---|
| `read_classical_text` | 78% | Vertex AI slow (922ms, down from 1906ms but still high) | Vertex AI quota/region check; may need caching layer |
| `query_remedial_mantras` | 75% | Filter logic partially off-target (returns remedies not matching query intent) | Tier 2 code fix to improve filter SQL |
| `data_coverage` | 78% | Accurately reflects empty tables; will improve when data gaps close | Auto-heals with Tier 2+3 data fixes |
| `tool_health` | 80% | No call history yet; metrics are null | Auto-heals with production usage |
| `holistic_bundle` | 50% | Schema + CDLM/RM/UCN sub-tools still failing → cascade | Heals with Tier 1 (MARSYS_REPO_ROOT) + Tier 2 (schema compat) |

---

### 2F — INTENTIONAL / LONG-SCOPE (not targeted here)

| Tool | Score | Status |
|---|---|---|
| `query_jaimini_drishti` | 20% | Intentional stub — M6+ scope |
| `get_cgm_subgraph` | 35% | P3 data seeding (complex) |
| `timeline_query` | 25% | P3 data seeding |

---

## 3 — Fix Topology

```
TIER 1 — Operator env vars + rebuild (no code, immediate)
  OPS-A: Set MARSYS_REPO_ROOT=/app on amjis-web          → +7.5 pts (cdlm/rm/ucn)
  OPS-B: Set PYTHON_SIDECAR_URL on amjis-web             → +3 pts (temporal)
  OPS-C: Rebuild amjis-mcp from current main HEAD         → +5 pts (read_asset)
  OPS-D: Verify Vertex AI (GCP_PROJECT + quota)           → +2 pts (vector_search)

  After Tier 1: 69% → ~87%

TIER 2 — Code fixes (2 sessions, parallel-safe)
  Session A: Backward-compat schema aliases (platform-mcp)
    7 tools: holistic_bundle, multi_school_bundle, cross_school_lookup,
             query_ephemeris, log_prediction, vector_search, read_asset
  Session B: Data + quality fixes (platform + data scripts)
    query_chart_facts (planet category seed)
    query_signal_state (state-derived confidence fallback)
    query_remedial_mantras (filter SQL improvement)

  After Tier 2: ~87% → ~96%

TIER 3 — Data seeding (deferred P3, separate sessions)
  Session C: Seed CGM graph (l25_cgm_nodes + l25_cgm_edges from CGM_v9_0.md)
  Session D: Seed L5 timeline rag_chunks

  After Tier 3: ~96% → ~99%
```

Tier 1 is pure operator work — no code sessions needed.
Sessions A and B are parallel-safe (different packages).

---

## 4 — Session Specifications

---

### TIER 1 — Operator steps (run immediately, before any code work)

Paste each as a single command.

**OPS-A — Set MARSYS_REPO_ROOT on amjis-web**
```bash
gcloud run services update amjis-web \
  --region=asia-south1 --project=madhav-astrology \
  --update-env-vars="MARSYS_REPO_ROOT=/app"
```
Expected: `query_cdlm_lookup`, `query_rm_walk`, `query_ucn_walk` — ENOENT resolved immediately (new instances pick up the var). No rebuild needed.

**OPS-B — Set PYTHON_SIDECAR_URL on amjis-web**
```bash
SIDECAR_URL=$(gcloud run services describe amjis-sidecar \
  --region=asia-south1 --project=madhav-astrology --format='value(status.url)')
echo "Sidecar URL: $SIDECAR_URL"
gcloud run services update amjis-web \
  --region=asia-south1 --project=madhav-astrology \
  --update-env-vars="PYTHON_SIDECAR_URL=${SIDECAR_URL}"
```
Expected: `temporal` tool starts routing correctly to the python sidecar.

**OPS-C — Rebuild amjis-mcp from current main HEAD**
```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
gcloud builds submit --config platform-mcp/cloudbuild.yaml \
  --project madhav-astrology \
  --substitutions=_TAG=$(git rev-parse --short HEAD)
```
This forces a fresh Docker build (no layer cache reuse) with the S1 COPY lines for `025_HOLISTIC_SYNTHESIS/` and `01_FACTS_LAYER/` present. Expected: `read_asset` goes from 30% to 95%+.

**OPS-D — Verify Vertex AI for vector_search**
```bash
gcloud run services describe amjis-web \
  --region=asia-south1 --project=madhav-astrology \
  --format='value(spec.template.spec.containers[0].env)' \
  | tr ',' '\n' | grep -E "GCP_PROJECT|VERTEX_AI|VECTOR_SEARCH"
```
Should show: `GCP_PROJECT=madhav-astrology`, `VERTEX_AI_LOCATION=asia-south1`, `VECTOR_SEARCH_ENABLED=true` (patched in OPS-2 yesterday). If present, the remaining `vector_search` failures are a Vertex AI API quota or credentials issue — check GCP console for the Vertex AI Matching Engine endpoint health at `asia-south1`.

---

### SESSION A — Backward-compat schema aliases (platform-mcp)

**Branch:** `fix/mcp-schema-compat`
**Worktree:** `/Users/Dev/Vibe-Coding/Apps/MadhavMCPSchemaA`
**Package:** `platform-mcp/src/tools/` only
**May touch:** `holistic_bundle_tool.ts`, `multi_school_bundle_tool.ts`, `cross_school_lookup.ts`, `query_ephemeris.ts`, `log_prediction.ts`, `vector_search.ts`, `read_asset.ts` + their test files
**Must NOT touch:** `platform/`, migrations, any other tool

For each of the 7 tools, the pattern is the same: extend the Zod input schema with `.transform()` or `.or()` to accept old param names and coerce them to the new required shape. The tool's core logic does not change — only the input validation layer.

**A.1 — `read_asset.ts`**
Input schema currently: `z.object({ canonical_id: z.string(), section: z.string().optional() })`
Change to:
```ts
z.object({
  canonical_id: z.string().optional(),
  asset_key: z.string().optional(),   // backward-compat alias
  section: z.string().optional(),
}).transform(i => ({
  canonical_id: (i.canonical_id ?? i.asset_key ?? '').toUpperCase(),
  section: i.section,
})).refine(i => i.canonical_id.length > 0, 'canonical_id or asset_key required')
```

**A.2 — `vector_search.ts`**
Input schema: `z.object({ text: z.string(), ... })`
Change `text` to:
```ts
z.object({
  text: z.string().optional(),
  query: z.string().optional(),        // backward-compat alias
  ...
}).transform(i => ({ ...i, text: i.text ?? i.query ?? '' }))
 .refine(i => i.text.length > 0, 'text or query required')
```

**A.3 — `cross_school_lookup.ts`**
```ts
claim: z.string().optional(),
topic: z.string().optional(),    // backward-compat alias
// in transform: claim: i.claim ?? i.topic
```

**A.4 — `multi_school_bundle_tool.ts`**
```ts
claim: z.string().min(10).optional(),
topic: z.string().optional(),
// in transform: claim: i.claim ?? i.topic ?? ''
// refine: claim.length >= 10
```

**A.5 — `holistic_bundle_tool.ts`**
```ts
query_text: z.string().min(3).optional(),
bundles: z.array(z.string()).optional(),  // old shape
// in transform: query_text: i.query_text ?? (i.bundles ?? []).join(', ')
// refine: query_text.length >= 3
```

**A.6 — `query_ephemeris.ts`**
```ts
date_range: z.object({ from: z.string(), to: z.string() }).optional(),
date_from: z.string().optional(),   // backward-compat flat params
date_to: z.string().optional(),
// in transform: date_range: i.date_range ?? (i.date_from && i.date_to
//   ? { from: i.date_from, to: i.date_to } : undefined)
```

**A.7 — `log_prediction.ts`**
```ts
confidence: z.union([
  z.enum(['high', 'medium', 'low']),
  z.number().min(0).max(1),           // backward-compat float
]).transform(c => typeof c === 'number'
  ? c > 0.75 ? 'high' : c >= 0.5 ? 'medium' : 'low'
  : c),
falsifier: z.string().optional().default(''),  // make optional (was required)
```

**Session A close ACs:**
1. `npm run build` passes 0 TS errors in `platform-mcp/`.
2. `npm test` passes all tool tests.
3. For each of 7 tools, a test verifies old-signature call succeeds (returns same result as new-signature call).
4. Commit on `fix/mcp-schema-compat`.

---

### SESSION B — Data + quality fixes

**Branch:** `fix/mcp-data-quality`
**Worktree:** `/Users/Dev/Vibe-Coding/Apps/MadhavMCPDataB`
**May touch:** `platform/src/lib/retrieve/query_signal_state.ts`, `platform/scripts/data/seed_chart_facts_planet.ts` (new), `platform/python-sidecar/pipeline/loaders/chart_facts_loader.py`, `platform/src/lib/retrieve/query_remedial_mantras.ts`
**Must NOT touch:** `platform-mcp/`, migrations (no new ones needed)

**B.1 — query_chart_facts: seed `planet` category rows**

Check current state:
```sql
SELECT count(*), category FROM chart_facts
WHERE category = 'planet'
GROUP BY category;
```
If 0 rows, run `chart_facts_loader.py` scoped to `planet` category to extract all 9 graha placements (sign, house, degree, dignity, lord status) from `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` and insert into `chart_facts`. Expected rows: 9 planets × ~8 attributes = ~72 rows.

**B.2 — query_signal_state: state-derived confidence fallback**

File: `platform/src/lib/retrieve/query_signal_state.ts` line 166.

Change:
```ts
confidence: r.confidence ?? 0.6,
```
to:
```ts
confidence: r.confidence ?? (
  r.state === 'lit'      ? 0.85 :
  r.state === 'ripening' ? 0.65 :
  r.state === 'dormant'  ? 0.35 : 0.5
),
```
This immediately differentiates confidence by activation state, giving meaningfully graded values instead of the misleading uniform 0.6.

Also investigate whether `signal_activator.py` can compute and persist real confidence values. If the activator has a `signal_weight` or `strength_score` field, map it to confidence and write it at insertion time.

**B.3 — query_remedial_mantras: improve filter precision**

Current issue: "filter partially off-target" — returns remedies that don't match the query intent closely enough. Read `platform/src/lib/retrieve/query_remedial_mantras.ts` and identify whether the SQL WHERE clause has a too-broad match (e.g., `ILIKE '%graha%'` matching too many rows). Tighten the filter using the query's planet or domain as a mandatory equality condition, not just a fuzzy LIKE.

**Session B close ACs:**
1. `npm test` passes in `platform/`.
2. `SELECT count(*) FROM chart_facts WHERE category = 'planet'` > 0.
3. `query_signal_state` test with lit signal returns confidence > 0.8 (not 0.6).
4. `query_remedial_mantras` integration test returns only domain-matched remedies.

---

### SESSION C — CGM graph seeding (P3)

**Trigger:** After Tier 1+2 complete and baseline audit confirms ≥95%.
**Branch:** `fix/mcp-cgm-seed`
**Scope:** New script `platform/scripts/data/seed_cgm_graph.ts`. Parse `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` for structured cross-domain linkage declarations. INSERT into `l25_cgm_nodes` + `l25_cgm_edges`. Idempotent (`ON CONFLICT DO NOTHING`).

**AC:** `SELECT count(*) FROM l25_cgm_nodes` > 0. `get_cgm_subgraph({node_id: 'SIG.MSR.001', hops: 2})` returns non-empty nodes.

---

### SESSION D — L5 timeline rag_chunks (P3)

**Trigger:** After Tier 1+2 complete.
**Branch:** `fix/mcp-l5-seed`
**Scope:** Identify L5 source documents, chunk them, INSERT into `rag_chunks` with `doc_type = 'l5_timeline'`.

**AC:** `SELECT count(*) FROM rag_chunks WHERE doc_type = 'l5_timeline'` > 0. `timeline_query({query: 'Saturn dasha arc'})` returns ≥1 chunk.

---

## 5 — Score Recovery Trajectory

| After | Key recoveries | Projected avg |
|---|---|---|
| **Now (A3 baseline)** | — | **69%** |
| **Tier 1 OPS-A** (MARSYS_REPO_ROOT) | cdlm_lookup, rm_walk, ucn_walk: 0%→95% | ~77% |
| **Tier 1 OPS-B** (PYTHON_SIDECAR_URL) | temporal: 20%→90% | ~79% |
| **Tier 1 OPS-C** (amjis-mcp rebuild) | read_asset: 30%→95%; holistic_bundle cascade improves | ~83% |
| **Tier 1 OPS-D** (Vertex AI check) | vector_search if env issue: 25%→85% | ~85% |
| **Session A** (schema compat, deployed) | holistic_bundle, multi_school_bundle, cross_school_lookup, query_ephemeris, log_prediction: 50%→90% | ~94% |
| **Session B** (data quality, deployed) | query_chart_facts: 65%→92%; query_signal_state: 85%→93%; query_remedial_mantras: 75%→88% | ~96% |
| **Sessions C+D** (P3 seeding) | get_cgm_subgraph: 35%→90%; timeline_query: 25%→85% | ~99% |

**Floor:** `query_jaimini_drishti` stays at 20% (intentional stub). `tool_health` auto-heals with usage.

---

## 6 — Dependency Order

```
OPS-A ─► immediate (env var — no rebuild)
OPS-B ─► immediate (env var — no rebuild)
OPS-C ─► ~10 min Cloud Build
OPS-D ─► immediate (GCP console check)
         │
         ▼
[Verify Tier 1 fixes via targeted tool calls before starting Sessions]
         │
Session A ──────────────────────────────────────────────┐
  (platform-mcp, no DB ops)                             │ parallel
Session B ──────────────────────────────────────────────┘
  (platform + data scripts)
         │
         ▼
    Deploy both → MCP-REM-A4 re-audit
         │
         ▼ (if ≥95%)
   Sessions C + D (P3, deferred)
```

OPS-A and OPS-B can be run RIGHT NOW — they take effect in seconds.
OPS-C kicks off the Cloud Build (takes ~10 min, then revisions flip automatically).

---

## 7 — Immediate Next Actions (in order)

1. **Run OPS-A now** — one gcloud command → 3 tools unblocked immediately.
2. **Run OPS-B now** — one gcloud command → temporal unblocked.
3. **Run OPS-C** — Cloud Build, ~10 min → read_asset goes to 95%.
4. **Run OPS-D** — env var check → confirm Vertex AI state.
5. **Author Session A brief** — 7 backward-compat aliases, one Claude Code session.
6. **Author Session B brief** — chart_facts planet + signal confidence + remedial mantras.
7. **Re-audit after Sessions A+B deploy** — target ≥95%.

---

*End of MCP_TOOL_AUDIT_REM_V2_PLAN_v1_0.md*
