---
canonical_id: CHAT_V2_R7_S3_BRIEF
version: 1.0
status: READY_FOR_EXECUTION
round: R7
session_id: R7-S3
owner: chat-v2/round7-polish worktree
branch: chat-v2/round7-polish
worktree: /Users/Dev/Vibe-Coding/Apps/MadhavR7
flag_namespace: MARSYS_FLAG_R7_CITATION
authored: 2026-05-20
depends_on: [R7-S1, R7-S2]
---

## Context

This brief covers R6.3 fix-forward: wire `enrichCitations` server-side so that every `data-citation` stream part carries both a `snippet` (verbatim text from the MSR signal store) and a `layer` (e.g. `L2.5`) by the time the assistant-ui renderer consumes it. Currently, citations are emitted with only a `signal_id` and an `index`; the frontend `citationRichMap` memo has slots for `snippet` and `layer` but both arrive as `undefined`. This session closes that gap end-to-end: backend fetch → stream emission → frontend rendering in `CitationSidePanel`.

The MSR signal store is the Supabase table `l25_msr_signals`. A helper `fetchMsrSnippets(signalIds: string[])` already exists in the codebase and queries that table. The citation extraction step runs after synthesis completes inside the consume route. The work is additive: no existing schema changes, no flag needed beyond the namespace declared above for rollback labeling.

Depends on R7-S1 (conversation rename/delete wiring) and R7-S2 (sidebar Logo + mobile citation panel collapse) being merged or at minimum non-conflicting on the branch, since all three share `ConsumeChatV2.tsx` as a touch surface.

---

## Files in scope

### Backend
- `platform/src/app/api/chat/consume/route.ts` — primary change site; locate the citation-extraction block post-synthesis and insert the `fetchMsrSnippets` call + enriched `data-citation` emission loop
- Wherever `fetchMsrSnippets` is currently defined (search `grep -r "fetchMsrSnippets" platform/src` to confirm path; likely `platform/src/lib/msr/` or `platform/src/lib/signals/`)
- If `fetchMsrSnippets` does not exist under that name, check for `getMsrSnippets`, `lookupSignals`, or any function that queries `l25_msr_signals` — adapt the call accordingly and note the actual name in the commit message

### Frontend
- `platform/src/components/consume/ConsumeChatV2.tsx` — `useMemo` for `citationRichMap` inside `V2AssistantText`; confirm it destructures `snippet` and `layer` from each `data-citation` part
- `platform/src/components/consume/CitationSidePanel.tsx` — add a `layer` badge element next to each signal ID; render the full `snippet` text body when the panel is expanded for a citation

### Types / shared
- Any TypeScript interface or Zod schema that defines the shape of a `data-citation` stream part — add `snippet: string | null` and `layer: string | null` fields if not present

---

## Files must not touch

- `platform/src/components/consume/ConsumeChatLegacy.tsx` — deleted at §M.16; must not be re-created
- `platform/src/lib/feature_flags.ts` — no new flags; `MARSYS_FLAG_R7_CITATION` is a namespace label for rollback identification only, not a runtime feature-flag entry
- `01_FACTS_LAYER/` — no L1 data changes in this session
- `025_HOLISTIC_SYNTHESIS/` — no synthesis artifact changes in this session
- `00_ARCHITECTURE/CANONICAL_ARTIFACTS_v1_0.md` — registry not touched; this brief is not a canonical artifact requiring registry entry
- Any file under `platform/src/app/api/chat/consume/` other than `route.ts` unless the snippet-fetch helper lives there
- `platform/tests/e2e/chat-v2/round6-walkthrough.spec.ts` — do not modify existing smoke spec; new assertions go in a separate R7 spec file if needed

---

## Acceptance criteria

### AC-1 — Stream parts carry snippet and layer (primary)
Send a request to a test conversation that produces at least one citation against a known MSR signal (e.g. `SIG.MSR.001`). Inspect the raw SSE stream (curl or browser DevTools Network tab). Every `data-citation` event in the stream must have the shape:
```json
{ "signal_id": "SIG.MSR.NNN", "snippet": "<non-empty string>", "layer": "L2.5", "index": <number> }
```
`snippet` must not be `null` for signal IDs that exist in `l25_msr_signals`. `layer` must not be `null` for those same IDs.

### AC-2 — Null-safe degradation
Cause a lookup failure by requesting a signal ID that does not exist in the MSR store (e.g. a synthetic `SIG.MSR.99999`). The stream must still complete with HTTP 200. The emitted `data-citation` part for the missing signal must have `snippet: null` and `layer: null` without throwing or producing a 500. All other citations in the same response must be unaffected.

### AC-3 — CitationSidePanel layer badge visible
Open a conversation with citations in the browser. Open `CitationSidePanel`. Each citation entry must display a visible layer badge (e.g. a small `<span>` or `<Badge>` element containing the string `"L2.5"` or the actual layer value returned). The badge must be adjacent to the signal ID, not below it.

### AC-4 — CitationSidePanel snippet text rendered
For a citation whose MSR signal has a non-empty snippet, expanding or viewing that citation in the panel must show the full snippet text in a readable block. The text must not be truncated to a single line in the default panel-open state (overflow: visible or scroll is acceptable; `overflow: hidden` with `whitespace: nowrap` is not).

### AC-5 — No TypeScript errors on changed files
`tsc --noEmit` (or the project's equivalent type-check command) passes with zero new errors introduced by this session's changes.

### AC-6 — No regression on existing smoke markers
The seven GREEN markers from the R6 smoke run (B1, O1, L1, L2, L3, B6, N1) must remain GREEN. Do not break citation rendering that was previously working (even if only `signal_id` was shown).

---

## Pre-commit gates

Run these in order before committing. All must pass:

```bash
# 1. Type check
cd /Users/Dev/Vibe-Coding/Apps/MadhavR7/platform
npx tsc --noEmit

# 2. Lint
npx eslint src/app/api/chat/consume/route.ts \
           src/components/consume/ConsumeChatV2.tsx \
           src/components/consume/CitationSidePanel.tsx \
           --max-warnings 0

# 3. Unit tests (if any exist for the snippet-fetch helper)
npx jest --testPathPattern="msr|signal|citation" --passWithNoTests

# 4. Manual stream inspection (document output in commit body)
# curl -N -X POST http://localhost:3000/api/chat/consume \
#   -H "Content-Type: application/json" \
#   -d '{"chartId":"<test_chart_id>","message":"<query that triggers citations>"}' \
#   | grep "data-citation"
# Paste ≥1 sample data-citation line into the commit body as evidence.

# 5. Drift detector (governance gate)
cd /Users/Dev/Vibe-Coding/Apps/MadhavR7
python platform/scripts/governance/drift_detector.py --manifest 00_ARCHITECTURE/CAPABILITY_MANIFEST.json
# Must exit 0 or exit 3 (known_residuals only)

# 6. Schema validator
python platform/scripts/governance/schema_validator.py
# Must exit 0 or exit 3
```

If gate 1 or 2 fails, fix before committing. If gate 3 fails with a test error (not "no tests found"), fix before committing. Gate 4 is a manual evidence step — paste the captured output into the commit message body. Gates 5–6 failures at exit code ≠ 0 and ≠ 3 block commit.

---

## Commit message template

```
feat(chat-v2/r7-s3): enrich data-citation stream parts with snippet + layer from MSR store

R6.3 fix-forward. After synthesis, call fetchMsrSnippets() for all
extracted signal IDs and emit data-citation parts with shape:
  { signal_id, snippet, layer, index }

Missing signals degrade to snippet: null / layer: null without blocking
the stream. CitationSidePanel updated to render layer badge and full
snippet text.

AC-1 stream evidence:
  data: {"signal_id":"SIG.MSR.NNN","snippet":"<paste>","layer":"L2.5","index":0}

Gates: tsc PASS | eslint PASS | jest PASS | drift PASS | schema PASS

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
```
