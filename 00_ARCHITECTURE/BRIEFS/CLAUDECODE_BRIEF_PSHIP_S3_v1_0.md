---
artifact: CLAUDECODE_BRIEF_PSHIP_S3_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
authored_by: Cowork 2026-05-20
session_id: PSHIP-S3
session_name: PSHIP-S3 — Fix the x-api-key auth bug + the 2 pre-existing validator failures
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/panchang-ship
  path_absolute: /Users/Dev/Vibe-Coding/Apps/PanchangShip
predecessor: PSHIP-S2 (shared-file integration)
---

# CLAUDECODE_BRIEF — PSHIP-S3
## Fix the production-breaking auth bug + the two known validator failures

The Panchang sidecar calls omit the `x-api-key` header, which 401s in production (where the sidecar enforces the key). This session fixes that across all calling paths, plus the two pre-existing governance-validator failures that return EXIT 4 on every close.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
test -f platform/src/lib/retrieve/query_panchanga.ts
git log --oneline -5   # PSHIP-S2 commits present
cd platform && npx tsc --noEmit | tail -5   # should be 0 errors from S2
```

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. `platform/src/lib/retrieve/query_panchanga.ts` (the `callSidecar` function — missing the header)
3. `platform/python-sidecar/main.py` (`verify_api_key` — confirms the header name is `x-api-key`)
4. How a WORKING sidecar caller sends the key — read `platform/src/lib/retrieve/query_ephemeris.ts` and any shared sidecar-fetch helper (grep for how other tools pass the key); model the fix on the established pattern
5. The Next.js proxy routes: `platform/src/app/api/panchang/day/route.ts`, `platform/src/app/api/compute/muhurat/route.ts` (or wherever the muhurat proxy lives) — check whether THEY forward the key to the sidecar

## §3 — Scope (8 items)

### Item 1 — Map every Panchang→sidecar call path
Enumerate every place Panchang code calls the Python sidecar:
- `query_panchanga.ts` `callSidecar` (server-side RetrievalTool — direct sidecar call)
- `/api/panchang/day` Next.js route → sidecar (the page data path)
- `/api/panchang/range` route → sidecar
- `/api/compute/muhurat` route → sidecar (Muhurat Finder)
- any others surfaced by grep `PYTHON_SIDECAR_URL` + `fetch.*compute`

Write the list to the FINAL_SUMMARY notes. For each, note whether it currently sends `x-api-key`.

**AC.PSHIP3.1:** Complete call-path map; each tagged sends-key / omits-key.

### Item 2 — Fix `callSidecar` in query_panchanga.ts
Add the header to the fetch:
```typescript
headers: {
  'Content-Type': 'application/json',
  'x-api-key': process.env.PYTHON_SIDECAR_API_KEY ?? '',
},
```
Match the exact env-var name `verify_api_key` expects (confirm from main.py — it reads the key into `API_KEY`; find which env var feeds it, likely `PYTHON_SIDECAR_API_KEY`).

**AC.PSHIP3.2:** `callSidecar` sends `x-api-key`; tsc clean.

### Item 3 — Fix any Next.js proxy routes that omit the key
For each `/api/panchang/*` and `/api/compute/muhurat` route that calls the sidecar without the key, add the `x-api-key` header to the server-side fetch. (These run server-side so they can read `process.env.PYTHON_SIDECAR_API_KEY` safely.)

**AC.PSHIP3.3:** All sidecar-calling routes forward the key.

### Item 4 — Auth round-trip test
Add a test that asserts every Panchang sidecar call includes the `x-api-key` header (mock the sidecar, assert the header is present on the outgoing request). This prevents regression.

**AC.PSHIP3.4:** Auth-header test passes; would fail if any path drops the key.

### Item 5 — Fix schema_validator timestamp overflow
Investigate `platform/scripts/governance/schema_validator.py` EXIT 4 timestamp overflow. Likely an integer/epoch overflow or a far-future/far-past date parse. Fix the root cause (widen the type, guard the parse, or correct the offending timestamp). Re-run: must EXIT 0.

**AC.PSHIP3.5:** `python3 platform/scripts/governance/schema_validator.py` EXIT 0.

### Item 6 — Fix drift_detector directory error
Investigate `platform/scripts/governance/drift_detector.py` `IsADirectoryError` on `08_CLASSICAL_CROSS_REFERENCE`. The detector is likely trying to read a directory as a file. Fix to skip directories or recurse properly. Re-run: must EXIT 0 (or EXIT 3 with documented known_residuals, but NOT EXIT 4 crash).

**AC.PSHIP3.6:** `python3 platform/scripts/governance/drift_detector.py` EXIT 0 (or clean EXIT 3).

### Item 7 — Full validator + test sweep
```bash
cd /Users/Dev/Vibe-Coding/Apps/PanchangShip
python3 platform/scripts/governance/schema_validator.py   # EXIT 0
python3 platform/scripts/governance/drift_detector.py      # EXIT 0/3
python3 platform/scripts/governance/mirror_enforcer.py     # EXIT 0
cd platform && npx tsc --noEmit && npm test 2>&1 | tail -30
```
All clean.

**AC.PSHIP3.7:** All validators clean; tsc 0; tests green.

### Item 8 — Session close
CURRENT_STATE; SESSION_LOG; brief flip; FINAL_SUMMARY noting the call-path map + validator fixes.

**AC.PSHIP3.8:** Close protocol complete.

---

## §5 — Constraints
**may_touch:** `platform/src/lib/retrieve/query_panchanga.ts`, the `/api/panchang/*` + `/api/compute/muhurat` routes, the auth-header test file, `platform/scripts/governance/schema_validator.py`, `platform/scripts/governance/drift_detector.py`, governance state, this brief.
**must_not_touch:** the engine internals; the UI components (unless a proxy route lives in the app dir — then only that route's fetch); Conductor files; corpus; the shared-file integrations from S2 (don't re-touch — only add the auth header where a sidecar call exists).

## §6 — Close checklist
- [ ] 8 ACs PASS
- [ ] Every sidecar call path sends x-api-key
- [ ] schema_validator + drift_detector both EXIT 0 (the 2 pre-existing failures gone)
- [ ] Auth-header regression test added
- [ ] tsc 0; tests green
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- BUG 1 (auth): documented in memory project_panchang_known_bugs.md. verify_api_key only enforces when API_KEY is set (prod) → keyless calls 401 in prod. Local keyless sidecar masks it.
- The 2 validator failures are pre-existing (not Panchang-introduced) but fixing them now means the close checklist runs clean and they stop returning EXIT 4 on every future session.
- Match the established key-passing pattern from query_ephemeris.ts / the shared sidecar helper — don't invent a new convention.

## §9 — Canary
The auth-header test (Item 4). It must FAIL if the header is removed from any path — that's what stops this prod-breaking bug from regressing. If you can't make it fail-on-removal, the test isn't actually guarding the fix.

*End — PSHIP-S3.*
