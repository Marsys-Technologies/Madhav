---
artifact: PSHIP_CONFLICT_MAP.md
type: PSHIP_INTEGRATION_SPEC
version: 1.0
status: CURRENT
authored_by: Claude Code (PSHIP-S1)
authored_on: 2026-05-20
session_id: PSHIP-S1
merge_base: 47ccdbc792ffe800197cfd2b33daa1a2682c7413
source_branch: origin/feature/phase-4c-panchang
target_branch: feature/panchang-ship (cut from current main)
---

# PSHIP Conflict Map — Shared-File Integration Spec

Every M-classified file (exists on current main AND was modified on the source branch)
is documented here with:
- What Panchang changed
- What main changed since the merge-base
- A proposed integration for PSHIP-S2
- A risk flag: LOW / MED / HIGH

**22 shared files total** (19 original M-classified + 3 A-RECLASSIFIED → M discovered during cross-check).

---

## §1 — HIGH Risk Files (requires human judgment)

### 1.1 — `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md`

**Risk: HIGH**

**What Panchang added (at merge-base line 678, same insertion point as main):**
- Rule `R-TC` (TRANSIT-CONTEXT ROUTING — Panchang vs. Ephemeris disambiguation): ~60-line block explaining when to use `query_panchanga` vs `query_ephemeris` (R-TC.a, R-TC.b, R-TC.c co-selection rule).
- Few-shot example 4.25: "Panchang query — single date, auspicious timing" demonstrating `query_panchanga` at priority 1.
- Several additional few-shot examples (4.26, 4.27, etc.) for Panchang + personalisation queries.

**What main changed (at same line 678):**
- Rule `R-TC` (TRANSIT-CONTEXT ENRICHMENT): A DIFFERENT R-TC rule (~161 lines) about attaching `query_ephemeris` for temporal anchors; includes date-param selection, exclusions, and pairing with existing rules.
- Few-shot example 4.25 from main: "R-TC transit-context — historical LEL event" (Saturn at marriage) — also numbered 4.25, conflicting with Panchang's 4.25.
- Additional few-shot examples 4.26+ from main about transit-context enrichment.

**Conflict nature:** BOTH sides inserted at exactly `@@ -678,6` AND both sides authored a "R-TC" rule with the same label but **different content**. They also both added a "4.25" few-shot example with different content. The regions overlap structurally — this cannot be merged by simple ordering. The R-TC names clash. The 4.25 example numbers clash.

**Proposed integration for PSHIP-S2 (needs human decision):**
Human must decide:
1. **Rename/sequence the R-TC rules:** Main's R-TC is ephemeris enrichment; Panchang's R-TC is panchanga disambiguation. Suggest renaming:
   - Main's `R-TC` → keep as `R-TC` (Transit-Context enrichment, ephemeris)
   - Panchang's `R-TC` → rename to `R-PD` (Panchanga Disambiguation) to avoid name clash
2. **Renumber few-shots:** Main adds examples 4.25–4.N (transit-context). Panchang adds 4.25 (panchang query) — must renumber Panchang's as 4.(N+1), 4.(N+2), etc. after main's set.
3. **Merge the rule bodies at line 678:** Insert main's R-TC block first (since it applies more broadly to ephemeris), then insert Panchang's R-PD block immediately after.

**Human judgment needed:** The renaming of Panchang's R-TC to R-PD must be reflected in both PLANNER_PROMPT and any hardcoded references in the codebase.

---

## §2 — MED Risk Files (main changed nearby — verify no structural conflict)

### 2.1 — `platform/src/lib/retrieve/index.ts`

**Risk: MED**

**What Panchang added (at merge-base line 56 and line 89):**
- Import: `import * as queryPanchangaTool from './query_panchanga'` (single tool, labelled "tool 29")
- Registration: `queryPanchangaTool.tool` appended to `RETRIEVAL_TOOLS` array

**What main changed (same file):**
- Added a 4-tool block importing `queryEphemeris`, `queryPanchanga`, `queryTransitEvent`, `queryDashaPeriods` — and registering all four
- Main's version ALREADY includes `queryPanchanga` (same file Panchang is adding)

**Integration verdict:** Main's version is a SUPERSET of Panchang's change. The `query_panchanga.ts` file is now being transplanted by PSHIP-S1 (it's an A-classified file). Once transplanted, main's existing import/registration of `queryPanchanga.tool` will resolve correctly. **No integration needed for this file** — main already has the right state. Verify only that the import path and export name in the transplanted `query_panchanga.ts` match what main expects (`queryPanchanga.tool` not `queryPanchangaTool.tool` — note the naming difference).

**Action for PSHIP-S2:** Check import name in `query_panchanga.ts` — if it exports as `tool`, both naming styles work; just verify the transplanted file exports `tool` at top-level.

### 2.2 — `platform/python-sidecar/main.py`

**Risk: MED**

**What Panchang added (at merge-base line 3 and line 46):**
- Imports: `from routers import panchang as panchang_router` + `from routers import muhurat as muhurat_router`
- Router registrations: `app.include_router(panchang_router.router, prefix="/api/compute", ...)` + `app.include_router(muhurat_router.router, prefix="/api/compute", ...)`

**What main changed (same file, different import line):**
- Added `transit_search` to the router import line: `from routers import ..., transit_search`
- Registered `app.include_router(transit_search.router, dependencies=[...])`

**Conflict analysis:** These are different routers added at different lines. Main touches line 4 (import list) and line 43 (registration). Panchang touches after the existing import block (line 3+) and after all existing registrations (line 46+). NO overlap in the actual insertion regions — but the line numbers shift due to main's insertion. Simple sequential merge is possible.

**Proposed integration:**
```python
# Combined import line (merge both additions):
from routers import ephemeris, events, eclipses, retrogrades, sade_sati, jaimini, v7_additions, dasha_chain, transit_search
from routers import panchang as panchang_router
from routers import muhurat as muhurat_router

# Registration block (append Panchang's after main's transit_search):
app.include_router(transit_search.router, dependencies=[Depends(verify_api_key)])
app.include_router(rag_retrieve_router, prefix="/rag", dependencies=[Depends(verify_api_key)])
...
# Phase 4C-3 — Panchang compute endpoints
app.include_router(panchang_router.router, prefix="/api/compute", dependencies=[Depends(verify_api_key)])
# Phase 4C-6 — Muhurat Finder endpoint
app.include_router(muhurat_router.router, prefix="/api/compute", dependencies=[Depends(verify_api_key)])
```

**Risk qualifier:** MED because `transit_search` module will exist on main but not on the Panchang source branch — if the transplanted files cause any import issue, it would be in routers/__init__.py or missing module. Verify `routers/transit_search.py` exists on current branch before PSHIP-S2.

### 2.3 — `CLAUDE.md`

**Risk: MED**

**What Panchang added:**
- version bump: 2.6 → 2.7 → 2.8
- §E: "Five workstreams" → "Six workstreams" (adding Phase 4C and Conductor)
- Two new §E entries: Phase 4C Panchang + Conductor
- Footer amended with 4C/Conductor history

**What main changed:**
- version bump: 2.6 → 2.8 (same destination version but different content)
- §E: "Five workstreams" → "Seven workstreams" (adding R7, R8, R9)
- Three new §E entries: Chat V2 R7, R8, R9 (all COMPLETE)
- Footer amended with R7/R8/R9 history

**Conflict analysis:** Both sides version-bump to 2.8 with different content. Both modify §E workstream count. Different entries added — no semantic clash.

**Proposed integration:**
- Current main's CLAUDE.md is already the authoritative governing surface (v2.8 with R7/R8/R9 COMPLETE)
- Add Phase 4C and Conductor entries to §E as a new 8th/9th workstream
- Increment "Seven workstreams" → "Nine workstreams" (or however many after combining)
- Merge the footer changelogs

**Action for PSHIP-S2:** CLAUDE.md is a governance file — the native should review the merged §E and approve the workstream declarations before PSHIP-S2 commits it.

### 2.4 — `platform/src/lib/claude/system-prompts.ts`

**Risk: MED**

**What Panchang added:**
- A panchang-context awareness block appended to `systemPrompt` inside the main system prompt builder function:
  ```
  PANCHANG CONTEXT (when present): If <panchang_context> block present, treat as L1.5 data...
  ```

**What main changed:** No changes in main since merge-base (UNCHANGED_ON_MAIN).

**Integration verdict:** Clean insert — Panchang adds after the existing `reports.map(...)` block. Main hasn't touched this region. Integration is LOW complexity but MED risk because the insertion context (which closure/block it's appended inside) must be verified.

**Proposed integration:** Append the Panchang's addition directly — it goes after the reports-map line and before the `if (blindMode)` block. Verify that main's current `system-prompts.ts` still has the same `if (blindMode)` structure before inserting.

### 2.5 — `platform/src/lib/components/observatory/pages/OverviewClient.tsx`

**Risk: MED**

**What Panchang added:**
- Import: `import { PanchangLatencyPanel, PanchangCachePanel } from '../panchang'`
- JSX section: A `<section data-testid="observatory-panchang-section">` block with `<PanchangLatencyPanel />` and `<PanchangCachePanel />` inside a 2-col grid, appended before closing `</ObsPageShell>`.

**What main changed:** No changes in main since merge-base (UNCHANGED_ON_MAIN).

**Integration verdict:** Clean additive insert at the end of the component return. Main unchanged in this file. Transplanted files `PanchangCachePanel.tsx`, `PanchangLatencyPanel.tsx`, and `index.ts` are all A-classified and are being transplanted. Once transplanted, the import will resolve.

**Proposed integration:** Apply Panchang's diff directly. LOW mechanical risk — MED only because the closing JSX tag position must match.

### 2.6 — `platform/src/test-setup.ts`

**Risk: MED**

**What Panchang added:**
- A `vi.mock('next/navigation', ...)` global stub for unit tests so panchang components (that use AskMadhavLink → useRouter) don't throw in jsdom.

**What main changed:** No changes in main since merge-base (UNCHANGED_ON_MAIN).

**Integration verdict:** Clean additive insert. Main unchanged. MED risk only because if main already has a different `next/navigation` mock elsewhere, doubling it would conflict.

**Action for PSHIP-S2:** Grep current `platform/src/test-setup.ts` for any existing `next/navigation` mock before inserting.

### 2.7 — `platform/package.json` and `platform/package-lock.json`

**Risk: MED**

**What Panchang added:**
- `"ical-generator": "^10.2.0"` in dependencies

**What main changed:**
- `"gpt-tokenizer": "^3.4.0"` in dependencies

**Conflict analysis:** Different package additions to different lines in the dependencies section (alphabetical order). `ical-generator` comes before `js-yaml`; `gpt-tokenizer` comes before `js-yaml`. Both insert alphabetically in the same `framer-motion` → `js-yaml` range.

**Proposed integration:** Both packages must be in the final `package.json`. The lock file for each was generated independently — running `npm install` with both packages in `package.json` will regenerate the lockfile correctly. Do NOT try to manually merge `package-lock.json`.

**Action for PSHIP-S2:** Add `ical-generator` to main's `package.json` dependencies; run `npm install` in `platform/` to regenerate lock file. Verify `ical-generator@^10.2.0` resolves cleanly alongside existing deps.

### 2.8 — `00_ARCHITECTURE/CAPABILITY_MANIFEST.json`

**Risk: MED**

**What Panchang added:**
- A complete new entry for `PANCHANG_DAILY_v1_0` with all fields (canonical_id, path, version, status, layer, expose_to_chat, retrieval_tool, etc.)
- `entry_count` bumped from 162 to 163
- `last_updated_by: "4C-9"`, `last_session`, `last_updated: "2026-05-20"`

**What main changed:** No changes in main since merge-base (UNCHANGED_ON_MAIN).

**Integration verdict:** Main unchanged. Clean additive insert of a new manifest entry. MED risk only because JSON structure must remain valid and `entry_count` must be accurate.

**Proposed integration:** Apply Panchang's diff directly — insert the `PANCHANG_DAILY_v1_0` entry into the entries array and update `entry_count`. Validate JSON after insertion.

---

## §3 — LOW Risk Files (clean additive inserts, main unchanged in the modified region)

### 3.1 — `platform/src/components/shared/AppShellRail.tsx`

**Risk: LOW**

**What Panchang added:**
- `import type React from 'react'`
- `MoonCrescentIcon` SVG component function
- `NavItem` interface broadening `icon` type to `LucideIcon | React.ComponentType<...>`
- `NAV_ITEMS` type annotation updated to `NavItem[]`
- `/panchang` entry added to `NAV_ITEMS` array between `/dashboard` and `/cockpit`

**What main changed:** UNCHANGED on main since merge-base.

**Proposed integration:** Apply Panchang's diff directly. Low risk — additive-only to the nav array and component. Verify column alignment in the NAV_ITEMS table after insertion.

### 3.2 — `platform/src/components/shared/MobileNavSheet.tsx`

**Risk: LOW**

**What Panchang added:**
- `/panchang` entry added to `NAV_ITEMS` array (between `/dashboard` and `/cockpit`), with alignment formatting.

**What main changed:** UNCHANGED on main since merge-base.

**Proposed integration:** Apply Panchang's diff directly.

### 3.3 — `platform/.env.example`

**Risk: LOW**

**What Panchang added:**
- `SESSION_SECRET=<random-32+-char-string>` with comment about Panchang iCal HMAC signing.

**What main changed:** UNCHANGED on main since merge-base.

**Proposed integration:** Apply Panchang's diff directly — insert `SESSION_SECRET` block after `PIPELINE_IMAGE_URI` line.

### 3.4 — `platform/.env.local.example`

**Risk: LOW**

**What Panchang added:**
- `SESSION_SECRET=your-session-secret-here` with comment.

**What main changed:** UNCHANGED on main since merge-base.

**Proposed integration:** Apply Panchang's diff directly — insert after `PYTHON_SIDECAR_API_KEY` line.

### 3.5 — `.geminirules`

**Risk: LOW**

**What Panchang added:**
- Phase 4C Panchang workstream entry in the concurrent workstreams list
- Conductor workstream entry

**What main changed:** UNCHANGED on main since merge-base.

**Proposed integration:** Insert Panchang's new workstream entries. NOTE: main's CLAUDE.md already has R7/R8/R9 as workstreams but `.geminirules` (MP.1 mirror) does not have them — the mirror was not updated on main for R7/R8/R9. The PSHIP-S2 session should propagate both the Panchang entries AND the R7/R8/R9 entries to `.geminirules` to bring it to full parity with current CLAUDE.md §E.

### 3.6 — `.gemini/project_state.md`

**Risk: LOW**

**What Panchang added:**
- A full Phase 4C concurrent workstream block documenting all 4C sub-phase statuses, tests, etc.

**What main changed:** UNCHANGED on main since merge-base.

**Proposed integration:** Append Panchang's block. Same note as 3.5 — check whether main's CLAUDE.md updates (R7/R8/R9) need corresponding `.gemini/project_state.md` entries for MP.2 parity.

### 3.7 — `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`

**Risk: LOW**

**What Panchang added:**
- v5.26 entry documenting 4C-9 Wave 1 close outcomes
- Various v5.xx updates for prior 4C sessions

**What main changed:** UNCHANGED on main since merge-base.

**NOTE:** Current main's `CURRENT_STATE_v1_0.md` has its own version progression from the R7/R8/R9 work. The Panchang versions and main versions may conflict on the version number if both added v5.2x entries.

**Action for PSHIP-S2:** Read main's current CURRENT_STATE version number and the 4C entries' version number. If both used `v5.26`, one must be renumbered. Additive append of the 4C history entries only.

### 3.8 — `00_ARCHITECTURE/SESSION_LOG.md`

**Risk: LOW**

**What Panchang added:** 1607 lines of session log entries for 4C-0 through 4C-9 sessions.

**What main changed:** UNCHANGED on main since merge-base.

**Proposed integration:** Append 4C sessions to end of SESSION_LOG. Chronological ordering: main's sessions (R7/R8/R9) are more recent (2026-05-20 later) — append Panchang sessions (all 2026-05-19 to 2026-05-20 earlier) before main's most recent entry, or simply append all at end. Either ordering is acceptable as SESSION_LOG is not queried by date range in practice.

### 3.9 — `platform/src/app/clients/[id]/consume/page.tsx`

**Risk: LOW**

**What Panchang added:**
- `import type { UIMessage } from 'ai'`
- `buildPanchangInitialMessages()` helper function
- Integration of that helper into the page component to inject `?prompt`+`?context` URL params as initial chat messages

**What main changed:** UNCHANGED on main since merge-base.

**Proposed integration:** Apply Panchang's diff directly. Verify that `UIMessage` type from `ai` package is compatible with the current version of `@ai-sdk/*` on main's package.json (R7/R8/R9 may have bumped assistant-ui/ai versions).

---

## §4 — Summary Risk Table

| File | Risk | Main Changed? | Integration Complexity |
|---|---|---|---|
| `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md` | **HIGH** | YES — 322 lines, R-TC at same offset | Rename R-TC→R-PD; renumber 4.25 examples; human approval needed |
| `platform/src/lib/retrieve/index.ts` | MED | YES — 49 lines; main already has queryPanchanga | Verify import name; likely no action needed |
| `platform/python-sidecar/main.py` | MED | YES — 21 lines; different routers | Append both; verify transit_search exists |
| `CLAUDE.md` | MED | YES — 35 lines; both bump to v2.8 | Merge §E; bump count; human review of governance section |
| `platform/src/lib/claude/system-prompts.ts` | MED | NO | Clean insert; verify blindMode block still present |
| `platform/src/lib/components/observatory/pages/OverviewClient.tsx` | MED | NO | Clean additive insert at JSX end |
| `platform/src/test-setup.ts` | MED | NO | Grep for existing next/navigation mock first |
| `platform/package.json` | MED | YES — 12 lines; different package | Merge two package additions; run npm install |
| `platform/package-lock.json` | MED | YES — 25 lines | Regenerate via npm install; do not manually merge |
| `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` | MED | NO | Additive JSON entry; validate entry_count |
| `platform/src/components/shared/AppShellRail.tsx` | LOW | NO | Direct apply |
| `platform/src/components/shared/MobileNavSheet.tsx` | LOW | NO | Direct apply |
| `platform/.env.example` | LOW | NO | Direct apply |
| `platform/.env.local.example` | LOW | NO | Direct apply |
| `.geminirules` | LOW | NO | Insert; also add R7/R8/R9 entries for MP.1 parity |
| `.gemini/project_state.md` | LOW | NO | Append block; check MP.2 parity |
| `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` | LOW | NO | Append; check version numbering |
| `00_ARCHITECTURE/SESSION_LOG.md` | LOW | NO | Append 1607-line session history |
| `platform/src/app/clients/[id]/consume/page.tsx` | LOW | NO | Direct apply; verify UIMessage type |

**HIGH risk count: 1** (PLANNER_PROMPT — human judgment needed on R-TC naming + 4.25 renumbering)
**MED risk count: 9**
**LOW risk count: 9**

---

## §5 — PSHIP-S2 Recommended Execution Order

1. `platform/package.json` — add `ical-generator`; run `npm install` → regenerates lock file
2. `platform/python-sidecar/main.py` — append panchang + muhurat router imports/registrations
3. `platform/src/components/shared/AppShellRail.tsx` — apply Panchang diff
4. `platform/src/components/shared/MobileNavSheet.tsx` — apply Panchang diff
5. `platform/.env.example` + `platform/.env.local.example` — insert SESSION_SECRET
6. `platform/src/test-setup.ts` — insert next/navigation mock (after grep-check)
7. `platform/src/lib/claude/system-prompts.ts` — insert panchang context block
8. `platform/src/lib/components/observatory/pages/OverviewClient.tsx` — insert panel imports + JSX
9. `platform/src/lib/retrieve/index.ts` — verify only (main already has queryPanchanga; confirm import name)
10. `00_ARCHITECTURE/CAPABILITY_MANIFEST.json` — insert PANCHANG_DAILY entry
11. `platform/src/app/clients/[id]/consume/page.tsx` — insert buildPanchangInitialMessages
12. `.geminirules` + `.gemini/project_state.md` — insert workstream entries + full R7/R8/R9 parity sweep
13. `00_ARCHITECTURE/CURRENT_STATE_v1_0.md` — append 4C session history
14. `00_ARCHITECTURE/SESSION_LOG.md` — append 4C session entries
15. `CLAUDE.md` — merge §E; human-review
16. **MANUAL — `00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md`** — STOP, get human decision on R-TC→R-PD rename and 4.25 renumbering before committing

---

## §6 — A-RECLASSIFIED → M Files (discovered during cross-check)

These were A-classified on source vs merge-base but exist on current main. Treated as M.

### 6.1 — `00_ARCHITECTURE/PHASE_4_EPHEMERIS_ACCESSIBILITY_MASTER_PLAN_v1_0.md`

**Risk: LOW**

**What Panchang changed:** Sub-phase state tracker updated — 4C state added (IN_DEVELOPMENT → WAVE_1_COMPLETE); all 4C.0–4C.9 sub-phases documented.

**What main has:** Same file but without the 4C close-out — main has 4A CLOSED, 4B PENDING, 4C ACTIVE (not WAVE_1_COMPLETE).

**Proposed integration:** Append 4C sub-phase state updates. The Panchang source branch's version of this document is the more complete, accurate state — apply Panchang's 4C section over main's.

### 6.2 — `platform/src/lib/retrieve/query_panchanga.ts`

**Risk: MED**

**What Panchang has:** The complete Wave 1 implementation — engine-direct path calling sidecar `/api/compute/panchanga`, full field projection support, all Panchang types.

**What main has:** An earlier implementation (Phase 4C-3) with a simpler sidecar path.

**Proposed integration:** The Panchang source branch version is the AUTHORITATIVE final version (4C-9 Wave 1 close). PSHIP-S2 should replace main's version with the source branch version, since the transplanted `query_panchanga.ts` is the more complete implementation. Verify import/export compatibility with `retrieve/index.ts`.

### 6.3 — `platform/src/lib/retrieve/__tests__/query_panchanga.test.ts`

**Risk: LOW**

**What Panchang has:** Full test suite for the Wave 1 engine-direct implementation.

**What main has:** Earlier test suite (Phase 4C-3 era).

**Proposed integration:** Replace main's version with source branch's more complete test suite.

---

*End PSHIP_CONFLICT_MAP.md v1.0 — produced PSHIP-S1, 2026-05-20*
