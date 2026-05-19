---
artifact: CLAUDECODE_BRIEF_PHASE_4C_3_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-05-19
authored_at: 2026-05-19
session_id: 4C-3
session_name: 4C-3 — query_panchanga RetrievalTool + Sidecar Endpoint + Planner Integration
executor: Claude Code sub-agent (spawned by Conductor)
execution_mode: autonomous, --dangerously-skip-permissions
worktree:
  name: Panchang
  branch: feature/phase-4c-panchang
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §5.4 + §5.6 + §6 Phase 4C.3
operational_brief: 00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md
predecessor_session: 4C-1-S2 (Phase 4C.1 CLOSED — panchang_engine v1.0.0-S2; 150 tests; 30/30 Drik parity)
skipped_predecessor: 4C-2 (skipped pending Phase 4B close — engine-direct path doesn't need SQL cache)
target_subphase: 4C.3 (single session per master plan)
next_session_anticipated: 4C-4-S1 (/panchang page MVP — server-rendered shell + 5-anga primary strip)
---

# CLAUDECODE_BRIEF — Phase 4C-3
## query_panchanga RetrievalTool + Sidecar Endpoint + Planner Integration

**Engine-direct path:** This brief deliberately scopes `query_panchanga` to call the Python sidecar's `/api/compute/panchanga` endpoint which computes via `panchang_engine` on demand. There is NO SQL cache layer in this session — the `panchang_daily` table is 4C-2's deliverable and 4C-2 is `skipped_pending_4b`. The sidecar endpoint MAY ship a stub cache-check that always returns miss; when 4C-2 eventually closes, the cache layer slots in below the endpoint with zero changes to `queryPanchanga` itself.

---

## §0 — How to start this session (autonomously, via Conductor)

Sub-agent context — you have a fresh 200K window. The Conductor has passed you this brief. You are in `/Users/Dev/Vibe-Coding/Apps/Panchang` on branch `feature/phase-4c-panchang`. You operate under `--dangerously-skip-permissions`.

Read in order:
1. `CLAUDE.md` per §C
2. This brief
3. The §2 Mandatory Reads below

Then execute Item 1 through Item 12 in sequence. Commit after each scope item with message `4C-3 Item N: <one-line summary>`. Emit `---FINAL_SUMMARY---` per the Conductor's sub-agent prompt template when done.

**Pre-flight integrity check (FIRST, before any work):**

```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
test -f platform/python-sidecar/panchang_engine/__init__.py
test -f 00_ARCHITECTURE/PHASE_4C_1_CLOSE_v1_0.md
cd platform/python-sidecar/panchang_engine && pytest -q
# Expected: 150/150 pass (the S2 close baseline)
cd /Users/Dev/Vibe-Coding/Apps/Panchang
ls platform/src/lib/retrieve/   # confirm RetrievalTool harness exists from Phase 4A
test -f platform/src/lib/retrieve/types.ts
grep -l "RETRIEVAL_TOOLS" platform/src/lib/retrieve/index.ts
test -f 00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md
```

If pre-flight fails, halt with `HALT_NEEDS_HUMAN`.

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | 4C-3 |
| Cowork thread name | `Phase 4C-3 query_panchanga + sidecar + planner 2026-05-19` |
| Branch | `feature/phase-4c-panchang` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/Panchang` |
| Execution mode | Autonomous sub-agent, `--dangerously-skip-permissions` |
| Predecessor | 4C-1-S2 (Phase 4C.1 CLOSED) |
| Anticipated next | 4C-4-S1 (`/panchang` page MVP — first session of the UI sub-phase) |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read)
2. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` §2 (confirm Phase 4C.1 CLOSED, 4C-3 OPEN)
3. `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` §5.4 (query_panchanga interface), §5.6 (API routes), §6 Phase 4C.3 acceptance
4. `platform/python-sidecar/panchang_engine/__init__.py` (public API — what to expose via sidecar)
5. `platform/python-sidecar/panchang_engine/types.py` (the Panchang dataclass — JSON serialization shape)
6. `platform/src/lib/retrieve/types.ts` (the RetrievalTool TS interface — must conform)
7. `platform/src/lib/retrieve/index.ts` (the RETRIEVAL_TOOLS array — registration target)
8. One existing retrieval tool — `platform/src/lib/retrieve/query_ephemeris.ts` (the Phase 4A sibling — model pattern, especially the sidecar-call shape)
9. `platform/python-sidecar/` main app file (probably `main.py` or `app.py`) — confirm the FastAPI route pattern for `/api/compute/<type>`
10. `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` §4 (few-shot section), §5 (R-TC rule from Phase 4A — extend, don't replace)
11. `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md` (the schema being returned — field semantics for the ToolBundle)

Then emit the session_open block.

---

## §3 — Scope (12 items — execute in order; commit after each)

### Item 1 — Pre-flight integrity verification

**What:** Run the pre-flight check from §0. Confirm S2 close state is intact: `panchang_engine` v1.0.0-S2, 150 tests pass, PHASE_4C_1_CLOSE artifact exists, RetrievalTool harness exists from Phase 4A. Halt with `HALT_NEEDS_HUMAN` on any failure.

**AC.4C3.1:** Pre-flight OK; commit message `4C-3 Item 1: pre-flight integrity OK`.

### Item 2 — Sidecar endpoint `/api/compute/panchanga`

**What:** Extend the Python sidecar to expose a new compute endpoint. Locate the sidecar's main FastAPI app file (likely `platform/python-sidecar/main.py` or `app.py`). Add a route:

```python
from datetime import date as DateType
from pydantic import BaseModel, Field
from typing import Optional
from panchang_engine import compute_panchang, panchang_range
from panchang_engine.types import Panchang

class PanchangaRequest(BaseModel):
    date: DateType
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    tz_offset_minutes: int = Field(..., ge=-720, le=840)
    chart_id: Optional[str] = None  # for future personalize overlay; ignored this session
    fields: Optional[list[str]] = None  # field projection for token-budget control

class PanchangaRangeRequest(BaseModel):
    date_from: DateType
    date_to: DateType
    lat: float
    lon: float
    tz_offset_minutes: int

@app.post("/api/compute/panchanga")
async def compute_panchanga_endpoint(req: PanchangaRequest):
    """Returns full Panchang for a single (date, lat, lon, tz). Engine-direct;
    no cache layer this session. 4C-2 will add panchang_daily cache below."""
    panchang = compute_panchang(req.date, req.lat, req.lon, req.tz_offset_minutes)
    payload = panchang_to_dict(panchang)  # see Item 3
    if req.fields:
        payload = {k: v for k, v in payload.items() if k in req.fields}
    return {"ok": True, "panchang": payload, "cache_hit": False}

@app.post("/api/compute/panchanga/range")
async def compute_panchanga_range_endpoint(req: PanchangaRangeRequest):
    """Range variant for calendar feed / week views. Same engine-direct logic."""
    panchangs = panchang_range(req.date_from, req.date_to, req.lat, req.lon, req.tz_offset_minutes)
    return {"ok": True, "panchangs": [panchang_to_dict(p) for p in panchangs], "count": len(panchangs)}
```

**Performance note:** `compute_panchang` invokes swisseph multiple times (sunrise + sunset + 9 grahas + anga transitions). Expect ~100–300ms per call on the sidecar machine. The endpoint does NOT need to be sub-100ms in this session — 4C-2's cache layer will handle that when it lands. Just make sure the endpoint doesn't time out for single-day calls.

**AC.4C3.2:** Endpoint exists; FastAPI app starts cleanly (`uvicorn` smoke); a curl POST against `/api/compute/panchanga` with a known date+location returns a valid `Panchang` JSON; commit message `4C-3 Item 2: sidecar /api/compute/panchanga endpoint`.

### Item 3 — `panchang_to_dict` serializer

**What:** Add a helper `panchang_to_dict(p: Panchang) -> dict` to either `panchang_engine/types.py` or a new `panchang_engine/serialize.py`. The output dict must match the JSONB shape defined in `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md §2` (so that later, when 4C-2's cache layer reads from `panchang_daily` table, the shape is identical to engine-direct compute output).

Field mapping rules:
- `datetime` → ISO 8601 string with `Z` for UTC
- `Anga` → `{"id": int, "name": str, "end_utc": "..."}`
- `Timing` → `{"label": str, "start_utc": "...", "end_utc": "..."}`
- `PlanetState` → flat dict with all fields
- `special_yogas` → list of `{"yoga": "...", "start_utc": "...", "end_utc": "...", "strength": "auspicious|inauspicious", "stars": int}` (the existing detect_all_special_yogas output shape)

Round-trip test (in `panchang_engine/tests/test_serialize.py`):
- `panchang_to_dict(compute_panchang(...))` produces a dict
- The dict is JSON-serializable (no datetime / dataclass leaks)
- A dict round-tripped through `json.dumps`/`json.loads` is byte-identical to the original

**AC.4C3.3:** Serializer exists; round-trip test passes; commit `4C-3 Item 3: panchang_to_dict serializer + round-trip test`.

### Item 4 — `queryPanchanga` RetrievalTool implementation

**What:** Create `platform/src/lib/retrieve/query_panchanga.ts`. Conform to the `RetrievalTool` interface from `types.ts`. Model on `query_ephemeris.ts`.

```typescript
import { RetrievalTool, RetrievalPlan, ToolBundle } from './types';

interface PanchangaParams {
  date: string;            // ISO date YYYY-MM-DD
  lat: number;
  lon: number;
  tz_offset_minutes?: number;  // default +330 (IST) if omitted
  chart_id?: string;       // personalize overlay; 4C-5 will use; ignored here
  fields?: string[];       // field projection for token budget
  range?: { from: string; to: string };  // optional range query
}

export const queryPanchanga: RetrievalTool = {
  name: 'query_panchanga',
  version: '1.0.0',
  description:
    'Returns daily Panchang state — five angas (tithi, nakshatra, yoga, karana, vara), ' +
    'sunrise/sunset, inauspicious windows (Rahu Kalam, Yamagandam, Gulika), auspicious ' +
    'windows (Abhijit, Brahma Muhurta), Choghadiya, Hora, special yogas (Sarvartha Siddhi, ' +
    'Amrit Siddhi, Ravi/Guru Pushya, Tripushkar, Bhadra, Panchaka), and 9-graha positions ' +
    'at sunrise. Call when the query asks about today/a date\'s Panchang, auspicious timing, ' +
    'or a good day for X. Use query_ephemeris for raw planetary positions at arbitrary moments; ' +
    'use query_panchanga for the panchang_daily-shaped daily state.',
  async retrieve(plan: RetrievalPlan, params: PanchangaParams): Promise<ToolBundle> {
    // 1. Resolve sidecar URL from env (SIDECAR_URL or fallback to localhost:PORT)
    // 2. POST to /api/compute/panchanga with the params
    // 3. Apply field projection if params.fields set (already handled server-side, but
    //    also clip client-side for defense in depth)
    // 4. Wrap response in ToolBundle:
    //    {
    //      tool: 'query_panchanga',
    //      facts: [ ... structured fact entries derived from Panchang fields ... ],
    //      citations: [ ... per-fact citations pointing at the engine version + ephemeris source ... ],
    //      diagnostics: { cache_hit: bool, latency_ms: number, computation_version, ephemeris_version }
    //    }
    // 5. On sidecar timeout / 5xx, throw a typed RetrievalToolError so the orchestrator
    //    can handle it; do NOT swallow errors and return empty bundles.
  },
};
```

Each `Panchang` field becomes one or more `Fact` entries in the bundle. For example, `tithi` becomes a fact like `{ subject: 'tithi', value: 'Shukla Dvitiya', end_utc: '...', layer: 'L1.5', source: 'PANCHANG_DAILY_v1_0' }`. Citations point at the engine's `computation_version` + ephemeris version. This is what downstream synthesis sees.

**AC.4C3.4:** `query_panchanga.ts` exists; TypeScript compiles clean (no errors); unit test for `retrieve()` with mocked sidecar response passes; commit `4C-3 Item 4: queryPanchanga RetrievalTool implementation`.

### Item 5 — Register `queryPanchanga` in `RETRIEVAL_TOOLS`

**What:** Open `platform/src/lib/retrieve/index.ts`. Add `import { queryPanchanga } from './query_panchanga';` near the existing tool imports. Add `queryPanchanga` to the `RETRIEVAL_TOOLS` array.

Verify the planner can see it: there's typically a registry-introspection helper somewhere (e.g., `getAvailableTools()` or similar). Confirm it lists `query_panchanga` after the change.

**AC.4C3.5:** `queryPanchanga` in the `RETRIEVAL_TOOLS` array; registry introspection returns it; TS compiles clean; commit `4C-3 Item 5: register queryPanchanga in RETRIEVAL_TOOLS`.

### Item 6 — Planner prompt few-shot addition

**What:** Open `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` §4 (few-shot examples). Add a new example block:

```
EXAMPLE — Panchang query
User: "What's today's tithi and is it a good day for buying property?"
Planner emits:
  tool_calls:
    - tool_name: query_panchanga
      params:
        date: "<today>"
        lat: 20.27
        lon: 85.84
        tz_offset_minutes: 330
        fields: ["tithi", "nakshatra", "vara", "special_yogas", "inauspicious"]
Reasoning: Panchang query about a specific date — query_panchanga returns the
five angas plus special yogas plus inauspicious windows, which together inform
whether property purchase is auspicious. The fields projection keeps token
budget tight by skipping unrequested data (Choghadiya, Hora, full planet table).
```

Add 1-2 more variants if the existing few-shot pattern in §4 uses multi-example blocks. Match the file's existing style.

**AC.4C3.6:** New few-shot block present; existing planner-prompt format preserved; commit `4C-3 Item 6: planner few-shot for query_panchanga`.

### Item 7 — R-TC (transit-context) rule extension

**What:** Open `PLANNER_PROMPT_v2_0.md §5` (or wherever the R-TC rule lives — added in Phase 4A). The current R-TC rule routes transit-context queries to `query_ephemeris`. Extend it so that Panchang-specific queries route to `query_panchanga` instead.

Heuristic to encode in the rule (preserve the wording style of the existing rule):
- If query mentions tithi, nakshatra, yoga, karana, vara, paksha, masa, muhurat, choghadiya, hora, rahu kalam, yamagandam, gulika, abhijit, brahma muhurta, sarvartha siddhi, guru pushya, ravi pushya, bhadra, panchaka, or asks "good day for X" / "auspicious time for Y" → call `query_panchanga`
- If query asks about raw planetary positions, retrogrades, ingresses, transit aspects, or a specific moment's chart → call `query_ephemeris`
- If query asks about both → call both tools; planner emits two tool_calls

Do NOT delete or rewrite the existing R-TC rule — append a clause.

**AC.4C3.7:** R-TC rule extended with Panchang routing; existing query_ephemeris routing intact; commit `4C-3 Item 7: R-TC rule extension for Panchang routing`.

### Item 8 — Planner probe set (10 curated queries)

**What:** Create `platform/tests/planner/panchang_probe_set.json` (or extend existing planner probe sets if the path differs). 10 curated queries:

```json
{
  "schema_version": "1.0",
  "purpose": "Validate planner routes Panchang queries to query_panchanga and non-Panchang queries to query_ephemeris.",
  "queries": [
    {"id": "PP.01", "query": "What's the tithi today?", "expected_tool": "query_panchanga"},
    {"id": "PP.02", "query": "Is today auspicious for starting a business?", "expected_tool": "query_panchanga"},
    {"id": "PP.03", "query": "What nakshatra is the moon in right now?", "expected_tool": "query_panchanga"},
    {"id": "PP.04", "query": "When does Rahu Kalam end today in Bhubaneswar?", "expected_tool": "query_panchanga"},
    {"id": "PP.05", "query": "Is it a Guru Pushya yoga day this Thursday?", "expected_tool": "query_panchanga"},
    {"id": "PP.06", "query": "Where is Saturn right now in my chart?", "expected_tool": "query_ephemeris"},
    {"id": "PP.07", "query": "When does Jupiter go retrograde next?", "expected_tool": "query_ephemeris"},
    {"id": "PP.08", "query": "What's the sidereal longitude of the Sun at noon UTC on 2026-06-21?", "expected_tool": "query_ephemeris"},
    {"id": "PP.09", "query": "Is Mars combust today and what's the panchang look like?", "expected_tool_calls": ["query_ephemeris", "query_panchanga"]},
    {"id": "PP.10", "query": "When's a good Tuesday for buying a vehicle next month?", "expected_tool": "query_panchanga"}
  ]
}
```

PP.09 is a mixed query — the planner should emit BOTH tools. Test accommodates that.

**AC.4C3.8:** Probe set committed; commit `4C-3 Item 8: planner probe set for Panchang routing — 10 queries`.

### Item 9 — Planner gate test

**What:** Create `platform/tests/planner/test_panchang_routing.ts` (match the project's planner-test pattern). Loop over the probe set. For each query, run the planner module, parse its emitted `tool_calls`, assert:

- For single-tool entries: `tool_calls[0].tool_name === expected_tool`
- For multi-tool entries (PP.09): each name in `expected_tool_calls` appears in `tool_calls` (order-independent)
- No `query_panchanga` calls on non-Panchang queries (false positives)
- No missing `query_panchanga` calls on Panchang queries (false negatives)

This is the gate for 4C-3 close: 10/10 PASS. If any query fails, halt with diagnosis.

**AC.4C3.9:** `pytest` or `npm test` for `test_panchang_routing.ts` reports 10/10 PASS; commit `4C-3 Item 9: planner routing gate — 10/10 PASS`.

### Item 10 — End-to-end smoke (sidecar live + tool wired)

**What:** A small integration test that:
1. Starts the sidecar locally (`uvicorn` or whatever the project uses)
2. Invokes `queryPanchanga.retrieve()` with `{ date: today, lat: 20.27, lon: 85.84, tz_offset_minutes: 330 }`
3. Asserts the returned ToolBundle has non-empty `facts`, including at least `tithi`, `nakshatra`, `vara`, and `special_yogas` entries
4. Asserts `diagnostics.latency_ms` is finite (sanity)
5. Stops the sidecar

If the project doesn't have an existing integration-test harness for the sidecar, add a minimal one (`platform/tests/integration/test_query_panchanga_e2e.ts` or similar). If running the sidecar in-test is infeasible in your environment, halt with `HALT_NEEDS_HUMAN` — do not skip the smoke.

**AC.4C3.10:** E2E smoke PASS; tool actually fetches from a live sidecar; commit `4C-3 Item 10: queryPanchanga E2E smoke PASS`.

### Item 11 — Update PANCHANG_DAILY status in CAPABILITY_MANIFEST

**What:** PANCHANG_DAILY is currently `IN_DEVELOPMENT` (flipped in 4C-1-S2). After 4C-3 lands, `query_panchanga` is exposed and callable. But the asset is still not `CURRENT` — `CURRENT` requires the SQL cache (4C-2). Add a sub-field to the manifest entry: `runtime_path: "engine_direct"` (vs `"cached"` after 4C-2 lands). Document this distinction.

Also: add `query_panchanga` to the manifest's `expose_to_chat: true` confirmation — verify it's listed.

Run mirror MP.2 propagation to `.gemini/project_state.md` for the manifest change.

**AC.4C3.11:** CAPABILITY_MANIFEST entry updated; `mirror_enforcer.py` exits 0; commit `4C-3 Item 11: CAPABILITY_MANIFEST + MP.2 mirror for query_panchanga exposure`.

### Item 12 — Session close + handoff

**What:**
1. Update `CURRENT_STATE_v1_0.md` Phase 4C block: `last_session_id: 4C-3`; `next_session_objective: 4C-4-S1 (/panchang page MVP — server shell + 5-anga primary strip)`
2. Append `SESSION_LOG.md` with 4C-3 atomic entry
3. Update Phase 4 master plan §B: 4C.3 row to CLOSED with commit hash
4. Update queue: 4C-3 status → `passed`; 4C-4-S1 stays `pending` with `requires_brief_authoring: true` (Cowork will author after 4C-3 closes)
5. Flip THIS brief's frontmatter `status: READY` → `status: COMPLETE`
6. Emit FINAL_SUMMARY

**AC.4C3.12:** All close-protocol steps done; FINAL_SUMMARY emitted; final commit `4C-3 Item 12: session close — 4C.3 CLOSED; next halt at 4C-4-S1 brief authoring`.

---

## §4 — Mirror discipline

**MP.2 active this session** (Item 11) — CAPABILITY_MANIFEST status field addition triggers `.gemini/project_state.md` adapted-parity update.

---

## §5 — Constraints

**may_touch:**
- `platform/python-sidecar/main.py` (or app.py — wherever FastAPI routes are defined) — extend with `/api/compute/panchanga` and `/api/compute/panchanga/range`
- `platform/python-sidecar/panchang_engine/serialize.py` OR `types.py` (the `panchang_to_dict` helper)
- `platform/python-sidecar/panchang_engine/tests/test_serialize.py` (new test file)
- `platform/src/lib/retrieve/query_panchanga.ts` (new file)
- `platform/src/lib/retrieve/index.ts` (RETRIEVAL_TOOLS registration only)
- `platform/tests/planner/panchang_probe_set.json` (new file)
- `platform/tests/planner/test_panchang_routing.ts` (new file)
- `platform/tests/integration/test_query_panchanga_e2e.ts` (new file if needed)
- `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` §4 few-shot + §5 R-TC rule extension
- `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` (PANCHANG_DAILY runtime_path addition + status check)
- `.gemini/project_state.md` (MP.2 propagation)
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` (last_session_id + next_session_objective)
- `00_ARCHITECTURE/SESSION_LOG.md` (append)
- `00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md` §B
- `00_ARCHITECTURE/CONDUCTOR/session_queue.yaml` (status updates only)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_PHASE_4C_3_v1_0.md` (status flip at close)

**must_not_touch:**
- `platform/python-sidecar/panchang_engine/__init__.py`, `angas.py`, `timings.py`, `planets.py`, `special_yogas.py`, `muhurat.py`, `shastra_tables.py`, `ayanamsha.py`, `types.py` (except adding `panchang_to_dict` if you choose to place it in types.py) — the engine is sealed at v1.0.0-S2
- `01_FACTS_LAYER/**`, `025_HOLISTIC_SYNTHESIS/**`, `035_DISCOVERY_LAYER/**` (corpus frozen)
- `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` (sealed)
- `00_ARCHITECTURE/BRIEFS/PHASE_4C_PANCHANG_BRIEF_v1_0.md` (sealed)
- Any prior session's close artifacts
- `00_ARCHITECTURE/CONDUCTOR/CONDUCTOR_PROMPT_v1_0.md` (orchestrator config frozen)
- `00_ARCHITECTURE/CONDUCTOR/schemas/**` (frozen)
- `CLAUDE.md` (no §E edits this session)
- `.geminirules` (MP.1 not triggered)
- Phase 4B's territory — sunrise derivation, MEAN_NODE rebuild, ephemeris_daily migrations — that's its own workstream
- The `panchang_daily` Cloud SQL table (4C-2's deliverable; deliberately skipped)

---

## §6 — Session-close checklist

- [ ] Pre-flight integrity check PASSED
- [ ] All 12 ACs completed (AC.4C3.1 through AC.4C3.12)
- [ ] Sidecar endpoint live and returning valid JSON
- [ ] `panchang_to_dict` round-trip test passes
- [ ] TypeScript compiles cleanly (no errors anywhere in `platform/src/lib/retrieve/`)
- [ ] Planner probe set 10/10 PASS (the gate)
- [ ] E2E smoke PASS (sidecar live + tool wired)
- [ ] `mirror_enforcer.py` exits 0
- [ ] `drift_detector.py` exits 0
- [ ] `validate_queue.py` exits 0
- [ ] CURRENT_STATE Phase 4C block updated; SESSION_LOG appended; Phase 4 master plan §B updated
- [ ] Queue entry 4C-3 status: passed; 4C-4-S1 stays pending (brief authoring halt expected next)
- [ ] FINAL_SUMMARY emitted

---

## §7 — LLM stack for this session

| Role | Model | Notes |
|---|---|---|
| Primary inference | Gemini (gemini-2.5-pro for code/TS, flash for prompt edits) | Default |
| Fallback | DeepSeek v4 Pro | |
| Tertiary | NIM | |
| Anthropic/Claude API | **BANNED** | Per memory file 2026-05-19 |

---

## §8 — Context carried (do not re-derive)

- **Engine-direct path:** `query_panchanga` calls the sidecar's `/api/compute/panchanga` which invokes `panchang_engine.compute_panchang()` on demand. No SQL cache this session — 4C-2 is `skipped_pending_4b`. When 4C-2 eventually closes, cache hits get added inside the endpoint without changing `query_panchanga.ts`.
- **Shape contract:** `panchang_to_dict()` output MUST match the JSONB columns defined in `03_DERIVATIONS/PANCHANG_DAILY_v1_0.md §2`. This ensures 4C-2's cache writes/reads are byte-identical to engine-direct compute output.
- **Default location for examples:** Bhubaneswar (20.27°N, 85.84°E, tz_offset_minutes 330). Settled D1 2026-05-19.
- **Planner few-shot lives in `PLANNER_PROMPT_v2_0.md §4`.** R-TC rule lives in §5 — extend, don't replace.
- **Tool description length budget:** the `description` field on `queryPanchanga` is what the planner sees when deciding which tool to invoke. Keep it precise — list the data types it returns and the keyword cues that signal Panchang queries. Skimped descriptions cause planner false negatives.
- **Native overlay (chart_id) is 4C-5 territory.** Accept the param in this session's interface; do NOT implement personalize logic. The endpoint and tool accept `chart_id` and pass it through but the engine ignores it. 4C-5 will fill in the overlay.

---

## §9 — On the canary: planner probe set 10/10

This is the close gate for 4C.3. Failure modes:

- **False positive on non-Panchang query:** planner emits `query_panchanga` for "where is Saturn?" → tool description is too greedy. Tighten the description's keyword cues.
- **False negative on Panchang query:** planner emits `query_ephemeris` for "when does Rahu Kalam end?" → R-TC rule extension didn't trigger. Check the rule wording.
- **Wrong tool for mixed query (PP.09):** planner emits only one tool when both needed. Confirm planner supports multi-tool emission (it does per Phase 4A precedent); confirm both routings activate.

If any single probe fails, halt and report the failing query + planner output. Don't fudge the test to make it pass — that's the canary's whole point.

---

## §10 — On what happens AFTER this session

- Conductor advances queue; 4C-3 marked passed.
- Next eligible entry: 4C-4-S1 (`/panchang` page MVP — server shell + 5-anga primary strip + date picker + location selector).
- 4C-4-S1 has `requires_brief_authoring: true` — Conductor halts. Cowork authors 4C-4-S1 brief; user stages + updates queue + re-paste kickoff.
- 4C-2 stays `skipped_pending_4b`. When Phase 4B closes (separate workstream), Cowork authors a fresh 4C-2 brief and the queue gets a new entry.

---

*End of CLAUDECODE_BRIEF_PHASE_4C_3_v1_0.md — authored 2026-05-19 in Cowork session after Conductor halt at 4C-2 + Cowork-driven SKIP of 4C-2 pending Phase 4B.*
*Executor: Conductor sub-agent. Branch: feature/phase-4c-panchang. Worktree: /Users/Dev/Vibe-Coding/Apps/Panchang.*
*Master plan §6 Phase 4C.3 — single-session sub-phase per plan.*
