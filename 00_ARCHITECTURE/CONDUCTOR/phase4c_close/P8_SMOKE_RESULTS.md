---
artifact: P8_SMOKE_RESULTS.md
canonical_id: P8_SMOKE_RESULTS
version: 1.0
status: COMPLETE
authored_by: Claude Sonnet 4.6
session: PHASE-4C-CLOSE
date: 2026-05-21
---

# P8 — Chrome Smoke Results

## Revisions under test

| Service  | Revision               | Commit      |
|----------|------------------------|-------------|
| amjis-web     | amjis-web-00312-wff    | 14fee006    |
| amjis-sidecar | amjis-sidecar-00278-hw2 | 14fee006   |

Note: commit `14fee006` includes the bonus fix from P8 itself —
`_score_breakdown()` returns numeric-only dict (`.toFixed` crash fix)
discovered during smoke and resolved before re-testing.

---

## F.1 — Muhurat Finder overload smoke

**Result: PASS**

Test: Vivah (Marriage), 2026-05-21 → 2026-08-18, lat=20.27, lon=85.84 (Bhubaneswar — within 10 km fence → cache path)

Observations:
- Response sub-second (cache path engaged; engine-direct would take ~30–90 s)
- "RESULTS FOR VIVAH (MARRIAGE)" — 10 windows returned
- `#1 · 85.75` — score renders with `.toFixed(2)` correctly
- Breakdown badges render: `Tithi +0.18`, `Nakshatra +0.38`, `Vara +0.05`, `Special Yoga +0.15`, `Planet strength +0.10`
- "Export to Calendar" + "Ask Madhav about this date" buttons present on every row
- No error boundary, no "Panchang Unavailable" state
- 0 console errors after fix

**Bonus fix committed during P8** (commit `14fee006`):
Root cause of prior `TypeError: e.toFixed is not a function` identified:
`_score_breakdown()` was returning a verbose diagnostic dict with non-numeric
values (`active_auspicious_yogas: list`, `jupiter_combust: bool/None`,
`inauspicious_windows: list`, etc.). The UI iterates all entries and calls
`.toFixed(2)` on each value. The fix returns only `{tithi, nakshatra, vara,
yoga, planet, tara_bala}: float` — matching `labelForBreakdownKey()` in
`MuhuratResultsList.tsx`. Bug was masked pre-F.1 because requests always timed
out (60 s sidecar limit) before results could render. 18/18 sidecar tests pass.

---

## F.2 — Ask-Madhav initialMessages prop smoke

**Result: CODE VERIFIED / E2E BLOCKED (pre-existing)**

**Code fix verification:** 5/5 source-level unit tests pass (commit `84b02408`).
Tests assert:
- `initialMessagesProp` present in destructuring
- `useState` seeded with `initialMessagesProp` not hardcoded `undefined`
- Prop wires through correctly on deeplink navigation

**E2E observation:**
Clicking "Ask Madhav about this date" from the Muhurat Finder navigates to:
```
/clients/abhisek_mohanty_primary/consume?prompt=Walk+me+through...&context={"_truncated":true,...}
```
Both `prompt` and `context` URL params are correctly populated — the deeplink
construction in `MuhuratResultsList.tsx` works. However the consume page fails
with "Something went wrong" (Server Component UUID cast error) because:

`NATIVE_CLIENT_ID = 'abhisek_mohanty_primary'` is used as the route `[id]`,
but the consume page expects a UUID. The actual native chart UUID is
`362f9f17-95a5-490b-a5a7-027d3e0efda0` (confirmed via dashboard CONSUME link).

This is a **pre-existing bug from 4C-8** (not introduced by F.2 fix).
`MuhuratResultsList.tsx` is outside `may_touch` scope for PHASE-4C-CLOSE.
The F.2 fix itself (`ConsumeChatV2.tsx` destructuring + `useState` seed) is
correct and verified at the unit-test level.

**Recommended follow-up (out of scope):** Update `NATIVE_CLIENT_ID` in
`MuhuratResultsList.tsx` from `'abhisek_mohanty_primary'` to
`'362f9f17-95a5-490b-a5a7-027d3e0efda0'`.

---

## R8 retroactive smoke

**Result: PASS**

Navigated to `/clients/362f9f17-95a5-490b-a5a7-027d3e0efda0/consume`.

Observations:
- Page loads: "Hi Abhisek, What's on your mind?"
- R8 chrome visible: Gemini Stack · 2M ctx · Acharya depth selector
- Depth modes: Life Events: On, Deep, Study, Brief
- Token estimate: `0 tokens · 0%` (R8 token estimate feature)
- Panel mode button present
- Reports / Aa- / Aa+ / Trace in top-right
- Composer functional
- 1 pre-existing 503 on `/api/folders` (R8 optional endpoint, not a regression)
- 0 regressions from Phase 4C changes

---

## Overall verdict

| Smoke         | Result  | Notes                                              |
|---------------|---------|----------------------------------------------------|
| F.1 Muhurat   | PASS    | Cache path engaged, results render, no JS error    |
| F.2 deeplink  | CODE OK | E2E blocked by pre-existing NATIVE_CLIENT_ID bug   |
| R8 retroactive| PASS    | Consume page clean; 1 pre-existing 503 on /folders |

P8 → **DONE** (with one noted follow-up item for NATIVE_CLIENT_ID fix).
