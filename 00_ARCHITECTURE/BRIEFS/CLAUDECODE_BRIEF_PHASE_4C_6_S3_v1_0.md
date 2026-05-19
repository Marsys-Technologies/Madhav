---
artifact: CLAUDECODE_BRIEF_PHASE_4C_6_S3_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-05-19
session_id: 4C-6-S3
session_name: 4C-6-S3 — Muhurat Finder modal UI + results list
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/phase-4c-panchang
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
predecessor: 4C-6-S2
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §4.4.1 (Output: top 10 windows)
---

# CLAUDECODE_BRIEF — Phase 4C-6-S3
## Muhurat Finder modal form + ranked results list + inline actions

S3 builds the UI surface. Modal form takes event + date range; submits to the muhurat endpoint; renders ranked results with star ratings, breakdown, and inline actions ("Export to Calendar" and "Ask Madhav").

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
test -f platform/python-sidecar/panchang_engine/muhurat.py
test -f platform/python-sidecar/panchang_engine/config/muhurat_weights.yaml
# Verify /api/compute/muhurat endpoint live
curl -s -X POST http://localhost:8000/api/compute/muhurat \
  -H "Content-Type: application/json" \
  -d '{"event":"vivah","date_from":"2026-06-01","date_to":"2026-06-15","lat":20.27,"lon":85.84,"tz_offset_minutes":330,"top_n":3}' | grep -q "ok"
```
Halt with HALT_NEEDS_HUMAN if pre-flight fails.

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. Master plan §4.4.1 — UI output spec ("Top 10 windows… each showing date, time window, star rating, breakdown, inline actions")
3. `platform/src/app/panchang/components/ActionBar.tsx` from 4C-4-S4 (the "Find Muhurat" button currently disabled — wire it here)
4. Existing modal pattern in shadcn: `platform/src/components/ui/dialog.tsx`
5. `platform/src/components/ui/star-rating.tsx` (from 4C-4-S3 — reuse)

## §3 — Scope (10 items)

### Item 1 — `MuhuratFinderModal` component
Create `platform/src/app/panchang/components/MuhuratFinderModal.tsx`. Modal triggered by ActionBar's "Find Muhurat" button. Form fields:
- Event dropdown (6 MVP events with Sanskrit + English: e.g., "Vivah (Marriage)")
- Date range: date_from (default: today) + date_to (default: today + 90 days). Date picker for each.
- Location (auto-filled from current page's location; editable)
- Personalise checkbox (auto-checked if chart selected; pass chart_id through)
- "Find Muhurat" submit button

**AC.4C6S3.1:** Modal opens; all fields functional; submit triggers fetch.

### Item 2 — Results fetch via SWR
Add `platform/src/app/panchang/hooks/useMuhuratFinder.ts`. On submit, posts to `/api/compute/muhurat` with the form params. Returns `{ windows, isLoading, error }`.

**AC.4C6S3.2:** Hook fetches; cached results visible; refetch on form re-submit.

### Item 3 — `MuhuratResultsList` component
Create `platform/src/app/panchang/components/MuhuratResultsList.tsx`. Renders the top-N windows from the fetch. Each row:
- Date (formatted: "Thursday, June 12, 2026")
- Star rating (from `MuhuratWindow.star_rating`)
- Time window (sunrise → sunset for MVP)
- Breakdown badges: "Pushya Nakshatra +0.95", "Guru Pushya Yoga +0.85", "Jupiter strong +0.50", etc. — pulled from `breakdown` dict
- Inline action buttons (Item 4)

Sorted by score descending. Loading skeleton during fetch. Empty state if no windows score > 0 (rare; usually means knockout on all days).

**AC.4C6S3.3:** Results list renders correctly; star ratings + breakdown badges all populated; sorted by score.

### Item 4 — Inline actions per window
For each window row:
- "📅 Export to Calendar" — disabled with "4C-7 coming" hint (full impl in 4C-7)
- "💬 Ask Madhav about this date" — opens chat with pre-loaded prompt: "Walk me through why <date> is ranked highest for <event>. The Panchang says: <tithi>, <nakshatra>, <vara>, plus <active yogas>." (4C-8 enhances with full context block)

**AC.4C6S3.4:** Ask-Madhav action works end-to-end; Calendar Export disabled with hint.

### Item 5 — Wire ActionBar trigger
Update `ActionBar.tsx` from 4C-4-S4: "Find Muhurat" button now enabled. Opens MuhuratFinderModal on click.

**AC.4C6S3.5:** Click "Find Muhurat" → modal opens.

### Item 6 — Personalisation pass-through
When user has a chart selected on /panchang, the modal auto-fills the personalise checkbox checked. chart_id is included in the API request. Backend applies native overlay scoring (per 4C-5 + 4C-6-S1).

**AC.4C6S3.6:** With chart selected → modal pre-checks personalise; results reflect Tara Bala / Chandra Bala overlay.

### Item 7 — Component tests
Tests for modal (open/close, form submission), results list (render with mock data, sorted, empty state, loading state), inline actions (correct URL params).

**AC.4C6S3.7:** Component tests PASS.

### Item 8 — Visual review
Manual review: open `/panchang`, click "Find Muhurat", select "Vivah", date range Apr 2026 → Jun 2026, submit. Verify:
- 10 results returned
- Sorted by star rating
- Top result is plausible (Thursday + Rohini/Mrigashira/Pushya nakshatra preferred)
- Breakdown badges visible and explain the ranking

**AC.4C6S3.8:** Visual review documented in `platform/tests/visual/4C6_S3_review.md`.

### Item 9 — Acharya sanity check pass
Run the Muhurat Finder for 3 events × 30-day range each (Vivah, Griha Pravesh, Vyapara). Manually inspect top 3 windows per event. Flag any that "feel wrong" to a senior acharya. Document in the visual review.

**AC.4C6S3.9:** Sanity check completed; flagged windows if any noted.

### Item 10 — Close
CURRENT_STATE; SESSION_LOG; brief flip; FINAL_SUMMARY.

**AC.4C6S3.10:** Done.

---

## §5 — Constraints
**may_touch:** `platform/src/app/panchang/components/{MuhuratFinderModal,MuhuratResultsList}.tsx`; `platform/src/app/panchang/hooks/useMuhuratFinder.ts`; `platform/src/app/panchang/components/ActionBar.tsx` (Find Muhurat wiring only); `platform/tests/visual/4C6_S3_review.md`; governance state files; this brief.
**must_not_touch:** sidecar; muhurat backend (S1/S2 sealed); UI components from prior sessions (only ActionBar wiring); engine; corpus.

## §6 — Close checklist
- [ ] 10 ACs PASS
- [ ] Component tests green
- [ ] Visual review + acharya sanity check documented
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- 6 MVP events
- Personalise pass-through from /panchang page state
- Breakdown badges come from backend's `breakdown` dict — UI is presentation only

## §9 — Canary
Acharya sanity check on 3 events. If any top-3 window for any event looks wrong (e.g., Vivah top result on a Saturday + Krishna Chaturdashi), backend has a bug or weights need tuning. Either way, halt and report rather than ship a misleading UI.

*End — 4C-6-S3.*
