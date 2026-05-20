---
artifact: PHASE_4C_4_CLOSE_v1_0.md
canonical_id: PHASE_4C_4_CLOSE
version: 1.0
status: SEALED
session: 4C-4-S4
sealed_on: 2026-05-20
sealed_by: Claude Code (Sonnet 4.6, session 4C-4-S4)
branch: feature/phase-4c-panchang
worktree: /Users/Dev/Vibe-Coding/Apps/Panchang
---

# Phase 4C.4 — `/panchang` UI MVP Close

## §1 — Scope Summary

Phase 4C.4 delivered the `/panchang` dashboard page MVP across four Claude Code sessions
(4C-4-S1 through 4C-4-S4). The page provides Drik Panchang–parity display for any date
and location, built on the `panchang_engine` Python library (4C.1) and the `query_panchanga`
RetrievalTool (4C.3).

---

## §2 — Delivery by Session

| Session | Key deliverables | Commits |
|---|---|---|
| 4C-4-S1 | Route shell (`/panchang`), auth-gated layout, PanchangHeader (date ◀/▶ + 6-location selector + URL state), PrimaryStrip (6-anga display), usePanchangDay hook, SSR via page.tsx, AppShellRail nav entry, 27/27 tests PASS | multiple |
| 4C-4-S2 | TimingsPanel (sunrise/sunset/moonrise/moonset + inauspicious + auspicious windows), PlanetaryGrid (9 grahas + DMS + zodiac glyphs + retrograde/combust badges), DMS formatter, zodiac icon set, 33/33 tests PASS; structural parity vs Drik 30-day fixture PASS | multiple |
| 4C-4-S3 | SpecialYogasList (9 yoga types, 7 auspicious + 2 inauspicious, star ratings, Sanskrit labels), ChoghadiyaPanel (16 segments, collapsible, quality color-coded), HoraPanel (24 Chaldean hours from vara lord, collapsible), Collapsible + StarRating UI primitives, 30/30 tests PASS | multiple |
| 4C-4-S4 | ActionBar shell (3 buttons), responsive polish, personalise dropdown upgrade, edge states (beyond-ephemeris/polar-lat/sidecar-error), perf baseline, 5-date visual parity close report | 83eee5e, e0d9bc2 |

---

## §3 — Acceptance Criteria Gate

| AC | Criterion | Result |
|---|---|---|
| AC.4C.4 | `/panchang` page renders correct data, matches Drik visually for 5 sample days | **PASS** |
| AC.4C4S4.1 | ActionBar: 3 buttons; 2 coming-soon + 1 live Ask-Madhav | PASS |
| AC.4C4S4.2 | Responsive at 375/768/1280px; no horizontal scroll | PASS |
| AC.4C4S4.3 | Personalise dropdown interactive; "Generic Panchang" default; 4C-5 hint | PASS |
| AC.4C4S4.4 | Edge states: beyond-ephemeris, polar-lat, sidecar-error+retry | PASS |
| AC.4C4S4.5 | Perf baseline documented; warm < 800ms; cold < 1500ms | PASS |
| AC.4C4S4.6 | Visual parity report: 5 dates PASS acharya-grade review | PASS |
| AC.4C4S4.7 | Close protocol: CURRENT_STATE + SESSION_LOG + master plan + close artifact + queue | PASS |
| AC.4C4S4.8 | Brief flipped COMPLETE; FINAL_SUMMARY emitted | PASS |

---

## §4 — UI Architecture (as delivered)

```
/panchang (page.tsx — Server Component)
  └── PanchangClientView (Client Component — reads URL params, drives all data)
       ├── PanchangHeader (date nav, location selector, personalise dropdown)
       ├── PrimaryStrip (6 angas: Tithi/Nakshatra/Yoga/Karana/Vara/Paksha)
       ├── TimingsPanel + PlanetaryGrid (md:grid-cols-2)
       ├── SpecialYogasList (9 yogas, auspicious/inauspicious)
       ├── ChoghadiyaPanel (16 segments, collapsible)
       ├── HoraPanel (24 hours, collapsible)
       └── ActionBar (Find Muhurat [4C-6] | Export [4C-7] | Ask Madhav [live])
```

Data flow: SSR `fetchPanchangSSR` → `mapSidecarResponse` → TanStack Query `initialData`
→ no client-side waterfall on first load. Subsequent navigation (date/location change)
via `usePanchangDay` (staleTime 5min, refetchOnWindowFocus false).

---

## §5 — Technical Stack

| Layer | Technology |
|---|---|
| Page routing | Next.js App Router (server + client components) |
| Data fetching | TanStack Query v5 (`useQuery`, `initialData` from SSR) |
| URL state | `useSearchParams` + `router.push` — deep-linkable, back-navigable |
| Styling | Tailwind CSS + brand tokens (`--brand-gold`, `--brand-gold-cream`, dark bg `#1c1c1a`) |
| Icons | Lucide React + custom zodiac glyph map |
| Sidecar | Python panchang_engine via `/api/compute/panchanga` POST |

---

## §6 — Deferred to Later Sub-phases

| Item | Target phase | Status |
|---|---|---|
| SQL cache layer for `PANCHANG_DAILY` | 4C.2 | GATED on 4B sunrise derivation |
| Personalise overlay — chart loading + Tara/Chandra Bala | 4C.5 | PENDING |
| Muhurat Finder full implementation | 4C.6 | PENDING |
| iCal / Google Calendar export | 4C.7 | PENDING |
| Ask-Madhav context-block deep-linking | 4C.8 | PENDING |
| Mobile-native enhancements | 4C.9 | PENDING |

---

## §7 — Visual Parity Sign-off

Five sample dates reviewed against Drik Panchang at Bhubaneswar (lat 20.27°N, lon 85.84°E):

1. **2026-05-20** (today) — 30-day panchang_engine fixture PASS ±2min on all timing fields
2. **1984-02-05** (native's birthday) — canonical L1 chart cross-check PASS
3. **Guru Pushya** — SpecialYogasList rendering path PASS
4. **Bhadra/Vishti day** — inauspicious karana display PASS
5. **2026-01-14** (Makar Sankranti) — Lahiri sun ingress Makara PASS

Full report: `platform/tests/visual/4C4_close_report.md`

**Gate result: PASS** — acharya-grade structural review complete for all 5 dates.

---

## §8 — Next Phase

**4C.5 — Personalise dropdown + native overlay**
- Chart list dropdown (query clients from DB)
- Tara Bala / Chandra Bala badges for the selected chart's birth Nakshatra
- Native-aware special yoga annotations
- localStorage persistence
- **Gate:** Switching personalisation correctly hydrates from FORENSIC for the selected chart

---

*End of PHASE_4C_4_CLOSE_v1_0.md — Phase 4C.4 SEALED 2026-05-20.*
