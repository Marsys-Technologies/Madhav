---
artifact: PHASE_4C_FOLLOWUPS_v1_0.md
version: 1.0
status: LIVING
authored_by: Claude Code (Sonnet 4.6, session 4C-9)
authored_on: 2026-05-20
session_id: 4C-9
purpose: >
  Deferred items from Phase 4C Wave 1 polish pass (Item 1 brief budget).
  These are non-blocking follow-up improvements for v2 of the Panchang module.
  Items are triaged: P1 (before production user promotion), P2 (next wave),
  P3 (nice-to-have).
---

# Phase 4C — Follow-up Items for v2

## §1 — Polish items deferred from 4C-9 budget

Items reviewed during the Item 1 engineering polish sweep. Surgical fixes within
the 2-hour budget were applied directly (h-8 → h-10 touch targets in PanchangHeader
date nav). The following items are beyond budget and deferred:

### FU.1 — 4C-2 SQL cache layer (P1 — blocked on Phase 4B)
**Status:** Skipped. Tracked in queue as `status: skipped` with `skip_reason:
Phase 4B not yet closed; engine-direct path via 4C-3 doesn't require the
panchang_daily SQL cache.`
**Action:** Reopen when Phase 4B closes (MEAN_NODE Rahu rebuild). Full spec in
the existing `CLAUDECODE_BRIEF_PHASE_4C_2_v1_0.md`.

### FU.2 — Mobile visual review at 375/768/1280 breakpoints (P1)
**Status:** Deferred — no active device or browser test harness in this session.
**Action:** Run Playwright/Chromium visual sweep at three breakpoints before
production user promotion. Key areas: ActionBar sticky bottom safe-area padding
on iOS, ChoghadiyaPanel + HoraPanel collapsed state on 375px, MuhuratResultsList
scrollability.
**Files to test:** `PanchangClientView.tsx`, `ActionBar.tsx`, `ChoghadiyaPanel.tsx`,
`HoraPanel.tsx`, `MuhuratFinderModal.tsx`.

### FU.3 — PanchangHeader custom lat/lon UX (P2)
**Status:** Deferred. The custom lat/lon inputs appear when "Custom…" is selected
but there is no "Confirm" button — the URL updates on blur. This is unintuitive
on mobile where blur behaviour differs.
**Action:** Add a small "Go" button next to the custom inputs. 40px min touch target.

### FU.4 — Location persistence (P2)
**Status:** Deferred. Location resets to Bhubaneswar on page reload if the user
selected a preset other than default.
**Action:** Persist selected location in `localStorage` with a 7-day TTL.
Initialise from localStorage before resolving from URL params.

### FU.5 — Muhurat Finder: "no results" state polish (P2)
**Status:** Deferred. When the 90-day window produces zero eligible muhurats for
an event, the UI shows a generic "No muhurats found" message. A more informative
message (e.g. "No auspicious windows were found in this 90-day range for Vivah.
Try expanding the window or consulting an acharya.") would improve UX.
**Files:** `MuhuratResultsList.tsx`.

### FU.6 — Observatory telemetry: real sidecar latency wiring (P2)
**Status:** Partially deferred. The 4C-9 Observatory panel shows latency as a
static info card (pending real per-request p50/p95/p99 aggregation).
**Action:** When the Observatory telemetry pipeline is extended for sidecar
routes, wire `/api/compute/panchanga` + `/api/compute/muhurat` into the existing
`LLMEvent` table or a new `SidecarEvent` table. The panel stub in
`platform/src/lib/components/observatory/panchang/PanchangLatencyPanel.tsx`
is ready to receive real data.

### FU.7 — iCal feed: full 30-day window (P3)
**Status:** Current iCal feed (`/api/panchang/feed.ics`) generates a 30-day
rolling window starting from today. A configurable window (7/30/90 days) would
help users who want a longer forward view.
**Action:** Add `?days=N` query param (max 365) to the feed route.

### FU.8 — Ask-Madhav: chart_id from session (P2)
**Status:** Deferred. The `NATIVE_CLIENT_ID` in `ActionBar.tsx` is hardcoded
(`'abhisek_mohanty_primary'`). For multi-native future, this should resolve from
the authenticated user's default chart, not a hardcoded constant.
**Action:** Read `chartId` from the Personalise dropdown selection (already in
URL as `&chart=`) and use that for the Ask-Madhav deep link, falling back to the
session user's default chart via API.

---

## §2 — Known validator residuals (pre-existing, not caused by 4C)

These failures in governance scripts were present before Phase 4C and are tracked
here for visibility. They do not block Wave 1 close.

| Script | Error | Root cause | Disposition |
|---|---|---|---|
| `schema_validator.py` | `ValueError: hour must be in 0..23` on SESSION_LOG.md YAML parse | A session_open or session_close block has a timestamp value that PyYAML auto-casts to `datetime` with out-of-range hour | Known residual; fix in next governance hygiene pass per ONGOING_HYGIENE_POLICIES §F |
| `drift_detector.py` | `IsADirectoryError: [Errno 21] Is a directory: .../08_CLASSICAL_CROSS_REFERENCE` | CANONICAL_ARTIFACTS_v1_0.md lists `08_CLASSICAL_CROSS_REFERENCE` as a file path but it is a directory | Known residual; documented in 4C-0 session close; fix in next governance hygiene pass |

Mirror enforcer and queue validator exit 0 cleanly.

---

*End PHASE_4C_FOLLOWUPS_v1_0.md v1.0 — authored 4C-9, 2026-05-20.*
