---
brief_id: M2_C5_TEMPORAL_EXTENSION
karn_session_name: KARN-W5-R1-TEMPORAL-EXTENSION
wave: 5
stream: B
status: COMPLETE
authored_by: Claude (Cowork) 2026-04-30 — Wave 4 close
authored_for: Claude Code execution (autonomous, long-running)
session_type: implementation (TypeScript temporal tool extension + sidecar verification + router prompt + tests + deploy)
target_branch: redesign/r0-foundation
parent_plan: 00_ARCHITECTURE/M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §B4
karn_protocol: 00_ARCHITECTURE/PROJECT_KARN_PROTOCOL.md
karn_session_log: 00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md
related_briefs:
  predecessor: KARN-W4-R1-A-MINOR (/dasha_chain sidecar endpoint committed but NOT deployed to Cloud Run)
  blocks: M2_D7_PER_TOOL_PLANNER (D2 plans against all tools including temporal extension)
parallel_stream_note: |
  Two other Wave-5 briefs run concurrently:
  - KARN-W5-R2-D234-BUNDLE (Stream B — 3 new L3/L4/L5 tools + Python chunkers)
  - KARN-W5-R3-RES-CON-EXPANSION (Stream C — discovery only, no code)
  W5-R1 and W5-R2 are both Stream B but scopes are DISJOINT:
  - W5-R1 owns: platform/src/lib/retrieve/temporal.ts (MODIFY only)
  - W5-R2 owns: 3 new *_query.ts files (CREATE); appends to index.ts + prompt.ts
  W5-R1 does NOT touch index.ts or add a new RETRIEVAL_TOOLS entry — temporal
  is already registered. W5-R2 appends to index.ts and prompt.ts using the
  append-only protocol. If W5-R2 commits before you and modifies prompt.ts,
  ensure your prompt.ts additions are preserved (do not overwrite).
estimated_time: ½–1 day single Claude Code session

carry_forward_notes:
  - "W4-R1 CRITICAL: /dasha_chain was committed to the sidecar but Cloud Run was NOT redeployed.
     The endpoint exists in platform/python-sidecar/routers/dasha_chain.py on the branch.
     PF.8 must verify /dasha_chain is live in Cloud Run before any temporal wiring work.
     If not live, the first action of this session is cloud_build_submit.sh to deploy it."
  - "ToolBundle correct pattern (from live temporal.ts): served_from_cache / result_hash /
     schema_version: '1.0' — do NOT use cached / item_count (those are wrong)."
  - "RETRIEVAL_TOOLS baseline = 14. temporal is already registered at index 6. Do NOT add
     a new entry. This session enhances the existing temporal tool — version bump to 1.1."
  - "Moon nakshatra = Purva Bhadrapada (Jupiter-ruled). Dasha sequence from birth:
     Jupiter MD (1984-02-05→1991-08-21), Saturn MD (1991-08-21→2010-08-21),
     Mercury MD (2010-08-21→2027-08-21), Ketu MD (2027-08-21→2034-08-21),
     Venus MD (2034-08-21→2054-08-21). Do NOT reference Saturn as upcoming MD."
  - "Existing temporal.ts already imports crypto, validate, telemetry — reuse all."
  - "Sidecar uses Python FastAPI. New router files are already in platform/python-sidecar/routers/
     as: dasha_chain.py, sade_sati.py, eclipses.py, retrogrades.py, ephemeris.py.
     Inspect each file's POST endpoint signature before wiring the TypeScript callSidecar() calls."
  - "Pre-existing Jest ESM baseline: 13 suites fail. Vitest baseline: ~979 passing (W4-R2 end-state).
     Do not count pre-existing failures as regressions."

scope_summary: |
  Extend the existing temporal retrieval tool (temporal.ts v1.0 → v1.1) to call
  five sidecar endpoints beyond the current /transits + /ephemeris pair. The Python
  sidecar already has all five routers committed; this session wires them into the
  TypeScript side and teaches the classifier when to invoke each.

  New sidecar endpoints to wire:
  1. /dasha_chain — 5-level Vimshottari for any date (MD/AD/PD/SD/PD2).
     Trigger: plan.dasha_context_required === true, or plan.time_window is set.
  2. /sade_sati — current Sade Sati phase (peak/rising/setting/inactive) for a date.
     Trigger: query mentions "Sade Sati", "Saturn transit", "7.5 years Saturn".
  3. /ephemeris (range) — daily planet positions for a date window.
     Trigger: plan.forward_looking === true AND plan.time_window is set (not just today).
  4. /eclipses — eclipses falling in a date window.
     Trigger: query mentions "eclipse", "Rahu transit", "solar eclipse", "lunar eclipse".
  5. /retrogrades — retrograde stations for a planet in a date window.
     Trigger: query mentions "retrograde", "vakri", "Mercury retrograde", "station".

  Also: investigate the 300s timeout signature noted in master plan probes (§B4).
  The E2E playbook confirmed temporal at 10ms in later tests — confirm that is steady state
  and document any remaining timeout risk in the closing summary.

  No new RETRIEVAL_TOOLS entry. No migrations. No DB schema changes.

may_touch:
  - platform/src/lib/retrieve/temporal.ts                              # MODIFY — extend to v1.1
  - platform/src/lib/retrieve/__tests__/temporal.test.ts               # MODIFY — extend tests
  - platform/src/lib/router/types.ts                                   # MODIFY — add sade_sati_query, eclipse_query, retrograde_query booleans to QueryPlan if absent
  - platform/src/lib/router/prompt.ts                                  # MODIFY — append Temporal Extension Guidance block
  - 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_M2_C5_TEMPORAL_EXTENSION.md  # status flip
  - 00_ARCHITECTURE/BRIEFS/M2_C5_VERIFICATION_<DATE>.txt               # CREATE

must_not_touch:
  - platform/src/lib/retrieve/index.ts                                 # temporal already registered — do not touch
  - platform/src/lib/retrieve/msr_sql.ts
  - platform/src/lib/retrieve/chart_facts_query.ts
  - platform/src/lib/retrieve/kp_query.ts
  - platform/src/lib/retrieve/saham_query.ts
  - platform/src/lib/retrieve/divisional_query.ts
  - platform/src/lib/retrieve/domain_report_query.ts                   # W5-R2 territory (may not exist yet)
  - platform/src/lib/retrieve/remedial_codex_query.ts                  # W5-R2 territory
  - platform/src/lib/retrieve/timeline_query.ts                        # W5-R2 territory
  - platform/python-sidecar/routers/dasha_chain.py                     # already implemented; do not modify
  - platform/python-sidecar/routers/sade_sati.py                       # already implemented; do not modify
  - platform/python-sidecar/routers/eclipses.py                        # already implemented; do not modify
  - platform/python-sidecar/routers/retrogrades.py                     # already implemented; do not modify
  - platform/python-sidecar/routers/ephemeris.py                       # already implemented; do not modify
  - platform/migrations/**
  - platform/src/app/**
  - platform/src/components/**
  - 035_DISCOVERY_LAYER/**
---

# KARN-W5-R1-TEMPORAL-EXTENSION — Execution Brief

## §0 — Context

This is an autonomous Claude Code session. Read this entire brief before writing any code.
Execute §1 (pre-flight) before touching anything. Halt immediately on any pre-flight failure.

**Parent plan:** `M1_M2_EXECUTION_PLAN_v1_0_DRAFT.md §B4`.

You are extending the existing `temporal.ts` retrieval tool (v1.0 → v1.1) to call five new
Python sidecar endpoints. All five endpoints are already implemented in the sidecar as
committed router files. This session's job is: (1) verify the sidecar is deployed with
these endpoints live, (2) wire them into `temporal.ts`, (3) teach the classifier when to
invoke each, (4) write tests, (5) deploy and verify.

**CRITICAL carry-forward from W4-R1:** `/dasha_chain` was implemented in the sidecar but
`Cloud Run was NOT redeployed` during W4-R1. If the pre-flight probe shows `/dasha_chain`
is not live, your first action is a deployment — then continue.

---

## §1 — Pre-flight self-diagnostics

```bash
# PF.1 — Branch check
git branch --show-current
# Expected: redesign/r0-foundation. Any other → HALT.

# PF.2 — Working tree clean
git status --short
# Expected: clean or only files in may_touch list. Unexpected mods → HALT.

# PF.3 — Current Cloud Run revision
gcloud run revisions list --service=amjis-web --region=asia-south1 \
  --limit=3 --format="table(name,status.conditions[0].type)"
# Record current serving revision. Expected: amjis-web-00036-wfs or newer.

# PF.4 — Verify /dasha_chain is live on Cloud Run
SIDECAR_URL=$(gcloud run services describe amjis-web --region=asia-south1 \
  --format="value(status.url)" 2>/dev/null)
# The Python sidecar runs as a subprocess inside the Cloud Run container.
# Its URL is the same Cloud Run URL but routed internally via PYTHON_SIDECAR_URL env var.
# Attempt a direct probe against the live revision:
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "${SIDECAR_URL}/api/sidecar/dasha_chain" \
  -H "Content-Type: application/json" \
  -d '{"native_id":"abhisek_mohanty","date":"2026-01-01"}' 2>/dev/null || echo "unreachable"
# If 200 → /dasha_chain is live. Continue.
# If 404 or unreachable → sidecar not yet deployed with dasha_chain.py. Deploy first (see §1.5).

# PF.5 — Inspect sidecar router signatures
# Read each router to understand POST body + response shape before wiring TypeScript:
cat platform/python-sidecar/routers/dasha_chain.py | head -60
cat platform/python-sidecar/routers/sade_sati.py | head -60
cat platform/python-sidecar/routers/eclipses.py | head -60
cat platform/python-sidecar/routers/retrogrades.py | head -60
cat platform/python-sidecar/routers/ephemeris.py | head -60
# Record: endpoint path, required POST body fields, response JSON shape.
# This determines the TypeScript callSidecar() call bodies in §2.

# PF.6 — Read current temporal.ts in full
cat platform/src/lib/retrieve/temporal.ts
# Understand: existing callSidecar() helper, ToolBundle construction,
# validate() call, telemetry pattern. Extend — do not replace.

# PF.7 — Read current QueryPlan type
grep -A 40 "export interface QueryPlan" platform/src/lib/router/types.ts
# Record which temporal-related fields already exist:
#   forward_looking, dasha_context_required, time_window, planets, etc.
# We may need to add: sade_sati_query?, eclipse_query?, retrograde_query?, retrograde_planet?

# PF.8 — TypeScript + vitest baseline
cd platform && npx vitest run --reporter=verbose 2>&1 | tail -10
# Record pass/fail counts as baseline.

# PF.9 — Verify temporal.test.ts exists and passes
cd platform && npx vitest run src/lib/retrieve/__tests__/temporal.test.ts 2>&1 | tail -10
# Record current pass count.
```

### §1.5 — Deploy gate (if PF.4 shows /dasha_chain not live)

If PF.4 shows `/dasha_chain` is not reachable (404 or connection refused), the sidecar
has not been rebuilt since W4-R1 committed `dasha_chain.py`. Deploy now:

```bash
bash platform/scripts/cloud_build_submit.sh
# Wait for build to complete (usually 3-5 minutes).
# Re-run PF.4 to confirm /dasha_chain is now responding 200.
# Record new revision in closing summary as "pre-work deploy."
```

---

## §2 — Implementation

### §2.0 — Study the sidecar router signatures

Before writing any TypeScript, read each router file in full (from PF.5 above) and document:

```
/dasha_chain  POST body: { native_id, date }
              Response:   { md, md_lord, ad, ad_lord, pd, pd_lord, sd, sd_lord, pd2, pd2_lord, ... }

/sade_sati    POST body: { native_id, date }
              Response:   { phase: "peak|rising|setting|inactive", ... }

/eclipses     POST body: { native_id, start_date, end_date }
              Response:   { eclipses: [...] }

/retrogrades  POST body: { native_id, start_date, end_date, planet? }
              Response:   { stations: [...] }

/ephemeris    POST body: { native_id, date } or { native_id, start_date, end_date, planets[] }
              Response:   { positions: {...} }
```

Adjust the TypeScript call bodies in §2.1 to match what the actual router files expect.
If a router expects different field names, use those. Do not guess — read the file.

---

### §2.1 — Extend temporal.ts to v1.1

**Modify `platform/src/lib/retrieve/temporal.ts`:**

Change version constant: `const TOOL_VERSION = '1.1'`

Add five new conditional sidecar calls inside the `retrieve()` function, after the existing
`/transits` call. The logic below is the target; adapt field names to match actual router
signatures from PF.5:

```typescript
// 1. /dasha_chain — when dasha context is requested or a specific date is implied
if (plan.dasha_context_required || plan.time_window) {
  const chainDate = plan.time_window?.start ?? today
  const dashaData = await callSidecar('/dasha_chain', {
    native_id: NATIVE_ID,
    date: chainDate,
  })
  results.push({
    content: JSON.stringify(dashaData),
    source_canonical_id: 'TEMPORAL_DATA',
    source_version: '1.0',
    confidence: 1.0,
    significance: 0.95,
  })
}

// 2. /sade_sati — when query asks about Sade Sati or Saturn transit phases
if (plan.sade_sati_query) {
  const ssData = await callSidecar('/sade_sati', {
    native_id: NATIVE_ID,
    date: today,
  })
  results.push({
    content: JSON.stringify(ssData),
    source_canonical_id: 'TEMPORAL_DATA',
    source_version: '1.0',
    confidence: 1.0,
    significance: 0.85,
  })
}

// 3. /ephemeris with date range — when forward_looking + time_window (not just today)
if (plan.forward_looking && plan.time_window?.start && plan.time_window?.end) {
  const ephData = await callSidecar('/ephemeris', {
    native_id: NATIVE_ID,
    start_date: plan.time_window.start,
    end_date: plan.time_window.end,
    planets: plan.planets?.length ? plan.planets : undefined,
  })
  results.push({
    content: JSON.stringify(ephData),
    source_canonical_id: 'TEMPORAL_DATA',
    source_version: '1.0',
    confidence: 1.0,
    significance: 0.8,
  })
} else if (plan.forward_looking && !plan.time_window) {
  // Fallback: existing single-date ephemeris call (preserve prior behavior)
  const ephData = await callSidecar('/ephemeris', { native_id: NATIVE_ID, date: today })
  results.push({
    content: JSON.stringify(ephData),
    source_canonical_id: 'TEMPORAL_DATA',
    source_version: '1.0',
    confidence: 1.0,
    significance: 0.8,
  })
}

// 4. /eclipses — when query mentions eclipses
if (plan.eclipse_query && plan.time_window?.start && plan.time_window?.end) {
  const eclData = await callSidecar('/eclipses', {
    native_id: NATIVE_ID,
    start_date: plan.time_window.start,
    end_date: plan.time_window.end,
  })
  results.push({
    content: JSON.stringify(eclData),
    source_canonical_id: 'TEMPORAL_DATA',
    source_version: '1.0',
    confidence: 1.0,
    significance: 0.85,
  })
}

// 5. /retrogrades — when query asks about retrograde stations
if (plan.retrograde_query) {
  const retData = await callSidecar('/retrogrades', {
    native_id: NATIVE_ID,
    start_date: plan.time_window?.start ?? today,
    end_date: plan.time_window?.end ?? new Date(Date.now() + 365 * 86400000)
                 .toISOString().slice(0, 10),
    planet: plan.retrograde_planet ?? undefined,
  })
  results.push({
    content: JSON.stringify(retData),
    source_canonical_id: 'TEMPORAL_DATA',
    source_version: '1.0',
    confidence: 1.0,
    significance: 0.80,
  })
}
```

**Wrap the five new calls inside the existing try/catch block.** The existing graceful
degradation path (the `catch` block) already handles sidecar unavailability — the new
calls must be inside the same try block so any failure routes to the same fallback.

**Preserve all existing behavior:** `/transits` is always called. The existing `/ephemeris`
call for `plan.forward_looking` without a window is now handled in the else-branch above.
Do not remove any existing code — extend only.

**Keep the existing `validate()` call and `telemetry.recordLatency()` call at the end.**
The ToolBundle schema check fires after all results are collected.

---

### §2.2 — Extend QueryPlan types

**Modify `platform/src/lib/router/types.ts`** — add optional boolean flags to QueryPlan
if they don't already exist:

```typescript
// Temporal extension flags (W5-R1)
sade_sati_query?: boolean          // true when query asks about Sade Sati / Saturn transit phases
eclipse_query?: boolean            // true when query asks about eclipses
retrograde_query?: boolean         // true when query asks about retrograde periods
retrograde_planet?: string         // optional planet name filter for retrograde query
time_window?: { start: string; end: string }  // ISO date range for temporal queries
```

Check `types.ts` first — some of these may already exist. Add only what's missing.
Do not remove or rename existing QueryPlan fields.

---

### §2.3 — Update router/prompt.ts

**Append a Temporal Extension Guidance block** to the classifier prompt, after the existing
temporal tool guidance (find it by searching for "temporal" in the guidance section).
Append after the last existing temporal guidance, do not replace it:

```
## Temporal Extension Guidance (temporal tool v1.1)

The temporal tool now supports 5 sidecar endpoints beyond /transits. Set the following
QueryPlan fields to activate them:

**dasha_chain:** Set `dasha_context_required: true` when the query asks:
- "What dasha am I in on [date]?" / "What is my dasha chain for [year]?"
- "When does [dasha] begin/end?" / Any 5-level Vimshottari chain question
Also set `time_window: { start: "<date>", end: "<date>" }` when a specific date or window is mentioned.

**sade_sati_query:** Set `sade_sati_query: true` when the query asks:
- "Am I in Sade Sati?" / "Sade Sati phase" / "7.5 years of Saturn"
- "Saturn transit over Moon" / "Sade Sati peak/rising/setting"

**eclipse_query:** Set `eclipse_query: true` when the query asks:
- "Eclipse" / "solar eclipse" / "lunar eclipse" / "Rahu-Sun conjunction"
- Also set `time_window` to the relevant date range.

**retrograde_query:** Set `retrograde_query: true` when the query asks:
- "Retrograde" / "vakri" / "[planet] retrograde" / "station"
- Set `retrograde_planet` to the planet name if specific (e.g. "Mercury", "Saturn").

**forward_looking + time_window:** For ephemeris range queries:
- Set both `forward_looking: true` and `time_window: { start, end }` for multi-day transit windows.
```

---

### §2.4 — Tests

**Extend `platform/src/lib/retrieve/__tests__/temporal.test.ts`**:

Add ≥ 7 new test cases covering the new endpoints (in addition to existing tests):

1. **dasha_chain call fires** when `plan.dasha_context_required === true` — mock callSidecar,
   verify `/dasha_chain` is called with `{ native_id: 'abhisek_mohanty', date: ... }`.

2. **dasha_chain fires with time_window start date** — `plan.time_window = { start: '2026-06-01', end: '2026-12-31' }` → callSidecar called with date = '2026-06-01'.

3. **sade_sati call fires** when `plan.sade_sati_query === true`.

4. **eclipse call fires** when `plan.eclipse_query === true` with time_window set.

5. **retrograde call fires** when `plan.retrograde_query === true`, no planet filter.

6. **retrograde call passes planet filter** when `plan.retrograde_planet === 'Mercury'`.

7. **ephemeris range call fires** when `plan.forward_looking === true` AND
   `plan.time_window = { start: '2026-06-01', end: '2026-09-30' }` → callSidecar called
   with `start_date` + `end_date` (not single `date`).

8. **No new calls when no new flags set** — existing-only behavior (transits only, no dasha
   call) when `dasha_context_required === false`, `sade_sati_query === false`, etc.

9. **All new calls are inside the try/catch** — if callSidecar throws on `/dasha_chain`,
   the error propagates to the catch block and the warning bundle is returned (not thrown).

**Mocking pattern:** Follow the existing mock pattern in temporal.test.ts exactly.
If it mocks `callSidecar` via jest.mock or vi.mock, extend that mock.

---

## §3 — Acceptance criteria

### AC.1 — Branch state
`git branch --show-current` returns `redesign/r0-foundation`.

### AC.2 — /dasha_chain live in Cloud Run
```bash
curl -s -X POST "${SIDECAR_URL}/api/sidecar/dasha_chain" \
  -H "Content-Type: application/json" \
  -d '{"native_id":"abhisek_mohanty","date":"2026-01-01"}' | python3 -m json.tool
```
Returns 200 with JSON containing dasha level fields (md, ad, pd or equivalent).
If SIDECAR_URL routing differs (internal vs external), adapt the probe accordingly.

### AC.3 — temporal.ts version bumped to 1.1
`grep "TOOL_VERSION" platform/src/lib/retrieve/temporal.ts`
Returns `'1.1'`.

### AC.4 — Five new sidecar calls present in temporal.ts
```bash
grep -c "callSidecar" platform/src/lib/retrieve/temporal.ts
```
Returns ≥ 7 (was 2 for /transits + /ephemeris; now 2 + 5 new = 7).

### AC.5 — QueryPlan has new temporal fields
```bash
grep -E "sade_sati_query|eclipse_query|retrograde_query|retrograde_planet" \
  platform/src/lib/router/types.ts
```
Returns ≥ 4 lines (one per new field).

### AC.6 — Classifier prompt has Temporal Extension Guidance
```bash
grep -c "sade_sati_query\|eclipse_query\|retrograde_query" platform/src/lib/router/prompt.ts
```
Returns ≥ 3.

### AC.7 — Tests: ≥ 7 new temporal tests passing
```bash
cd platform && npx vitest run src/lib/retrieve/__tests__/temporal.test.ts --reporter=verbose 2>&1 | tail -15
```
Total temporal tests ≥ pre-flight count + 7. No new failures.

### AC.8 — TypeScript compiles clean
```bash
cd platform && npx tsc --noEmit 2>&1 | grep -v node_modules | grep "error" | head -10
```
No new TypeScript errors from modified files.

### AC.9 — Full vitest suite: no new failures
```bash
cd platform && npx vitest run 2>&1 | tail -5
```
Pass count ≥ pre-flight baseline. Fail count = pre-flight fail count (13 pre-existing).

### AC.10 — Deploy: new Cloud Run revision serving 100%
```bash
bash platform/scripts/cloud_build_submit.sh
gcloud run revisions list --service=amjis-web --region=asia-south1 \
  --limit=3 --format="table(name,status.conditions[0].type)"
```
New revision is ACTIVE and serving 100%.

### AC.11 — Smoke: temporal tool returns dasha chain in live query
After deploy, issue a live query that should trigger dasha_context_required:
```bash
curl -s -X POST "${APP_URL}/api/chat/consume" \
  -H "Content-Type: application/json" \
  -d '{"message":"What is my full dasha chain on 2027-01-01?","chart_id":"abhisek_mohanty"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('tools_used','no tools_used key'))" 2>/dev/null
```
Confirm `temporal` appears in response. If query_plans table is queryable, verify
`dasha_context_required = true` in a recent row.

### AC.12 — Timeout investigation resolved
Confirm: in the query_plans table (or audit_events), no temporal tool calls exceed 30s.
Document finding in closing summary — "Timeout signature resolved" or "Residual risk: [description]".

---

## §4 — Halt conditions

Halt immediately with a 5-line halt summary if:

1. **PF.1 fails:** Wrong branch.
2. **PF.4 fails AND cloud_build_submit fails:** Sidecar cannot be deployed. HALT with build error.
3. **Sidecar router signature mismatch:** If any router file has a different endpoint path than
   expected (e.g., `/dasha-chain` with a hyphen instead of underscore), note it and adjust the
   TypeScript callSidecar() call to match the actual path. This is not a halt — it is a self-
   correction. Document the discrepancy in the closing summary.
4. **validate() call fails on new ToolBundle:** If the schema validator rejects a ToolBundle
   with the new results added, investigate the schema and fix before deploying. Do not disable
   the validator.
5. **Test regression > 5 new failures:** Halt before deploy.
6. **Cloud Build fails after 1 retry:** HALT with build log excerpt.

Non-halting: sidecar router returns partial data for an edge-case date (log it, don't halt);
TypeScript warnings that are not errors.

---

## §5 — Closing summary template

```
SESSION CLOSE — M2_C5_TEMPORAL_EXTENSION — <ISO timestamp>

ACs result:
  AC.1:  <PASS|FAIL> — branch check
  AC.2:  <PASS|FAIL> — /dasha_chain live in Cloud Run
  AC.3:  <PASS|FAIL> — temporal.ts version 1.1
  AC.4:  <PASS|FAIL> — ≥7 callSidecar calls
  AC.5:  <PASS|FAIL> — QueryPlan new temporal fields
  AC.6:  <PASS|FAIL> — Temporal Extension Guidance in prompt
  AC.7:  <PASS|FAIL> — ≥7 new temporal tests passing
  AC.8:  <PASS|FAIL> — TypeScript compiles clean
  AC.9:  <PASS|FAIL> — no new vitest failures
  AC.10: <PASS|FAIL> — Cloud Run revision updated
  AC.11: <PASS|FAIL> — smoke: temporal fires on dasha chain query
  AC.12: <PASS|FAIL> — timeout investigation resolved

Pre-work deploy (if needed):
  <none | "deployed amjis-web-XXXXX to bring /dasha_chain live before implementation">

Files created/modified:
  platform/src/lib/retrieve/temporal.ts (MODIFY — v1.0 → v1.1, 5 new callSidecar calls)
  platform/src/lib/retrieve/__tests__/temporal.test.ts (MODIFY — +7 new tests)
  platform/src/lib/router/types.ts (MODIFY — 4 new QueryPlan temporal fields)
  platform/src/lib/router/prompt.ts (MODIFY — Temporal Extension Guidance block appended)

DB changes: None

Cloud Run: <prior revision> → <new revision>

Tests:
  Before: <X passed / Y failed>
  After: <X' passed / Y' failed>
  Delta: <new failures count>

Timeout investigation: <finding>

Halt-and-report cases: <none | description>

Brief status: <COMPLETE | HALTED_AT_AC.N>
Next brief in stream: M2_D234_BUNDLE (W5-R2) runs in parallel this wave
```

After emitting the closing summary, append a session entry to
`00_ARCHITECTURE/PROJECT_KARN_SESSION_LOG.md` per protocol §3.1, and flip
`status: COMPLETE` in this brief's frontmatter.

---

*End of CLAUDECODE_BRIEF_M2_C5_TEMPORAL_EXTENSION v1.0 (authored 2026-04-30 — Wave 4 close).*
