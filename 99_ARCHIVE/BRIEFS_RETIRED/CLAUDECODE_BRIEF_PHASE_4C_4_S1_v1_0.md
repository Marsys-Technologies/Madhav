---
artifact: CLAUDECODE_BRIEF_PHASE_4C_4_S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-05-19
session_id: 4C-4-S1
session_name: 4C-4-S1 — /panchang route shell + Header + Primary Strip
executor: Claude Code sub-agent (Conductor)
execution_mode: autonomous, --dangerously-skip-permissions
worktree:
  branch: feature/phase-4c-panchang
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §4.1 + §4.2 + §5.5
predecessor: 4C-3 (queryPanchanga RetrievalTool live)
---

# CLAUDECODE_BRIEF — Phase 4C-4-S1
## /panchang route shell + Header + 5-anga Primary Strip

This is the first of four sessions building the /panchang page MVP. S1 lays the route, the AppShell-mounted layout, the date+location header, and the primary 5-anga strip. S2 adds timings + planetary grid; S3 adds special yogas + Choghadiya/Hora; S4 adds action bar + responsive polish + close.

---

## §0 — Pre-flight (Conductor sub-agent context)

```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
test -f platform/src/lib/retrieve/query_panchanga.ts
test -f platform/python-sidecar/panchang_engine/__init__.py
grep -q "queryPanchanga" platform/src/lib/retrieve/index.ts
ls platform/src/app/dashboard/ 2>/dev/null  # check existing app router structure
test -f platform/src/components/shared/AppShell.tsx
```

If pre-flight fails → halt with `HALT_NEEDS_HUMAN`.

---

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` §4.1, §4.2, §4.3, §5.5
3. `platform/src/lib/retrieve/query_panchanga.ts`
4. `platform/src/components/shared/AppShell.tsx` (existing nav + layout pattern)
5. `platform/src/app/dashboard/layout.tsx` (auth-gate pattern to mirror)
6. One existing shadcn component for style reference (find any existing card/header in `platform/src/components/ui/`)

---

## §3 — Scope (10 items)

### Item 1 — Route shell
Create `platform/src/app/panchang/layout.tsx` matching the dashboard auth-gate pattern. Wraps in `ZoneRoot` + `AppShell`. All authenticated roles allowed.

**AC.4C4S1.1:** Auth-gated layout exists; visiting `/panchang` anonymously redirects to login like `/dashboard` does.

### Item 2 — Page entry
Create `platform/src/app/panchang/page.tsx` as a server component. Imports `queryPanchanga` server-side, fetches today's Bhubaneswar Panchang (default location per D1), passes data to client components below.

**AC.4C4S1.2:** Page renders for today's date with default Bhubaneswar location; uses the SSR pattern from `dashboard/page.tsx`.

### Item 3 — Loading + error boundaries
Create `loading.tsx` (skeleton matching the primary strip layout from §4.2 mockup) and `error.tsx` (fallback with retry button).

**AC.4C4S1.3:** Loading skeleton shows during fetch; error boundary catches sidecar failures gracefully.

### Item 4 — `PanchangHeader` component
Create `platform/src/app/panchang/components/PanchangHeader.tsx`. Three elements per §4.2 mockup:
- Date picker (◀ / ▶ controls + click-to-pick calendar). Defaults to today.
- Location selector dropdown. Default: Bhubaneswar (20.27°N, 85.84°E). Options: Bhubaneswar, New Delhi, Mumbai, Bangalore, Chennai, Kolkata. Other = custom lat/lon input.
- Personalise dropdown placeholder (full implementation in 4C-5; here just renders the disabled dropdown shell).

**AC.4C4S1.4:** Header renders; date picker advances day; location dropdown changes lat/lon; persistence in URL query string (`?d=YYYY-MM-DD&loc=bhubaneswar`).

### Item 5 — `PrimaryStrip` component
Create `platform/src/app/panchang/components/PrimaryStrip.tsx`. Renders the 6-row primary strip per §4.2 mockup: Tithi, Nakshatra, Yoga, Karana, Vara, Paksha+Masa. Each row shows the Sanskrit name + ends_at time (in local TZ, HH:MM) for the angas that transition.

**AC.4C4S1.5:** Strip renders all 5 angas + Vara correctly for any test date; transition times match Drik to ±2 min.

### Item 6 — `usePanchangDay` SWR hook
Create `platform/src/app/panchang/hooks/usePanchangDay.ts`. Wraps `queryPanchanga` for client-side use. SWR cache key = `(date, lat, lon, chart_id)`. Stale-while-revalidate; refetch on focus disabled.

**AC.4C4S1.6:** Hook returns Panchang data; cache hits visible in network tab; date change triggers refetch.

### Item 7 — Sidebar nav entry
Update `platform/src/components/shared/AppShell.tsx` to add `/panchang` nav entry with a lunar-crescent SVG icon (gold tint matching brand `#fce29a`).

**AC.4C4S1.7:** Sidebar shows Panchang entry; click navigates to `/panchang`; active state highlights correctly.

### Item 8 — Brand styling pass
Ensure the page uses brand tokens: gold accents (`#fce29a`, `#d4af37`), dark background (`#1c1c1a`), Inter sans for labels, Source Serif 4 for anga names. No hardcoded colors — use existing CSS variables from the dashboard's theme.

**AC.4C4S1.8:** Visual review against existing /dashboard styling — same look-and-feel.

### Item 9 — Component unit tests
Tests for `PanchangHeader` (date controls, location switch) and `PrimaryStrip` (renders all 6 rows; handles missing data gracefully). Use the project's existing test harness (`vitest` or similar).

**AC.4C4S1.9:** All component tests PASS.

### Item 10 — Session close
Update CURRENT_STATE Phase 4C block: `last_session_id: 4C-4-S1`; append SESSION_LOG; flip brief to COMPLETE; emit FINAL_SUMMARY.

**AC.4C4S1.10:** Close protocol complete.

---

## §5 — Constraints

**may_touch:**
- `platform/src/app/panchang/**` (new)
- `platform/src/components/shared/AppShell.tsx` (nav entry only)
- `00_ARCHITECTURE/CURRENT_STATE_v1_0.md`, `SESSION_LOG.md`, this brief

**must_not_touch:**
- `platform/python-sidecar/**` (engine sealed)
- `platform/src/lib/retrieve/**` (Phase 4C-3 sealed)
- Corpus, master plan, other briefs
- `00_ARCHITECTURE/CONDUCTOR/**`

---

## §6 — Close checklist
- [ ] 10 ACs PASS
- [ ] Component tests green
- [ ] Visual review against §4.2 mockup OK
- [ ] CURRENT_STATE updated; SESSION_LOG appended
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; DeepSeek fallback; Anthropic BANNED.

## §8 — Context carried
- Default location: Bhubaneswar
- Brand: gold on dark (existing dashboard tokens)
- Personalise overlay is 4C-5 scope; this session ships disabled shell only
- All client-side data fetches go through `usePanchangDay` → `queryPanchanga` → sidecar

## §9 — Canary
Visual: open `/panchang` in dev mode — header + primary strip render with valid data for today's Bhubaneswar Panchang. Must match Drik's display for today within ±2 min on transition times.

*End — 4C-4-S1 first session of /panchang MVP buildout.*
