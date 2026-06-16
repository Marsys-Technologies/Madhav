---
artifact: CLAUDECODE_BRIEF_PHASE_4C_4_S3_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-05-19
session_id: 4C-4-S3
session_name: 4C-4-S3 — Active Special Yogas List + Choghadiya/Hora Panels
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/phase-4c-panchang
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §4.2 + §5.5
predecessor: 4C-4-S2
---

# CLAUDECODE_BRIEF — Phase 4C-4-S3
## Special Yogas List + Choghadiya/Hora Collapsible Panels

S3 of the /panchang UI build. Adds the active special yogas list (Sarvartha Siddhi, Guru Pushya, Bhadra, etc.) and the collapsible Choghadiya + Hora panels.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
test -f platform/src/app/panchang/components/TimingsPanel.tsx
test -f platform/src/app/panchang/components/PlanetaryGrid.tsx
```
Halt with HALT_NEEDS_HUMAN on miss.

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. Master plan §4.2 (mockup) + §5.5 (component list)
3. `platform/python-sidecar/panchang_engine/special_yogas.py` (9 detection functions — these populate the data)
4. S1/S2 component siblings for style consistency
5. The Panchang dataclass `special_yogas`, `choghadiya`, `hora` fields

## §3 — Scope (8 items)

### Item 1 — `SpecialYogasList` component
Create `platform/src/app/panchang/components/SpecialYogasList.tsx`. Renders a list of active special yogas for the day:
- Each entry: yoga name + Sanskrit + start-end window + star rating (1-5 stars) + auspicious/inauspicious color
- Auspicious yogas (Sarvartha Siddhi, Amrit Siddhi, Ravi Pushya, Guru Pushya, Tripushkar, Dwipushkar, Siddha) styled with success color + star icons
- Inauspicious markers (Bhadra, Panchaka) styled with warning color + ⚠ icon
- Empty state: "No special yogas active today."

**AC.4C4S3.1:** Component renders all active yogas with correct star ratings and color coding for any test date.

### Item 2 — `ChoghadiyaPanel` component (collapsible)
Create `platform/src/app/panchang/components/ChoghadiyaPanel.tsx`. Collapsed by default. When expanded: two sub-sections:
- Day Choghadiya: 8 segments (Amrit/Shubh/Labh/Char/Rog/Kal/Udveg + their times)
- Night Choghadiya: 8 segments

Each segment shows label + time window + color-coded by quality (Amrit/Shubh/Labh = good; Rog/Kal/Udveg = bad; Char = neutral).

**AC.4C4S3.2:** Panel toggles open/close; 16 segments render correctly when expanded.

### Item 3 — `HoraPanel` component (collapsible)
Create `platform/src/app/panchang/components/HoraPanel.tsx`. Collapsed by default. When expanded: 24 planetary hours starting from sunrise, each labeled with planet name + time window.

**AC.4C4S3.3:** Panel toggles open/close; 24 horas render in Chaldean order starting from vara lord.

### Item 4 — Reusable `Collapsible` primitive (if not already in shadcn)
If `platform/src/components/ui/collapsible.tsx` doesn't exist, add it (use shadcn pattern with Radix UI under the hood). If it does exist, reuse.

**AC.4C4S3.4:** Collapsible primitive present; chevron rotation animation works; accessible (aria-expanded).

### Item 5 — Star rating component
Create `platform/src/components/ui/star-rating.tsx` (reusable; used by SpecialYogasList here and Muhurat Finder in 4C-6). Props: `value` (1-5), `max` (default 5), `size` (sm/md/lg). Uses Tabler `ti-star` icons.

**AC.4C4S3.5:** Star rating renders correctly for 1-5 values.

### Item 6 — Page wiring
Update `platform/src/app/panchang/page.tsx` to insert SpecialYogasList below the TimingsPanel/PlanetaryGrid two-column section, then ChoghadiyaPanel and HoraPanel collapsed below that.

**AC.4C4S3.6:** Full page now matches the §4.2 mockup vertical order: header → primary strip → timings/planetary → special yogas → choghadiya/hora.

### Item 7 — Component tests + visual parity
Tests for SpecialYogasList (active/inactive states, multiple yogas, empty state), ChoghadiyaPanel (toggle, 16-segment data), HoraPanel (24-hour data, planet rotation). Visual parity check vs Drik's display for special yogas + Choghadiya on today's Bhubaneswar date.

**AC.4C4S3.7:** All tests PASS; visual parity documented.

### Item 8 — Session close
CURRENT_STATE, SESSION_LOG, brief flip, FINAL_SUMMARY.

**AC.4C4S3.8:** Close protocol complete.

---

## §5 — Constraints
**may_touch:** `platform/src/app/panchang/components/{SpecialYogasList,ChoghadiyaPanel,HoraPanel}.tsx`, `platform/src/components/ui/{collapsible,star-rating}.tsx`, `platform/src/app/panchang/page.tsx` (wiring only), governance state files, this brief.
**must_not_touch:** sidecar, retrieve/, S1/S2 component internals (only ADD via page.tsx wiring), corpus, master plan.

## §6 — Close checklist
- [ ] 8 ACs PASS; component tests green
- [ ] Visual parity vs Drik documented
- [ ] CURRENT_STATE + SESSION_LOG updated; FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- Special-yoga star ratings from `special_yogas.py detect_all_special_yogas` output (already encoded there)
- Choghadiya/Hora data come directly from engine; UI is presentation-only

## §9 — Canary
For today's Bhubaneswar date: SpecialYogasList output set-equality with Drik's display; ChoghadiyaPanel 16-segment time windows ±2 min vs Drik; HoraPanel sequence starts at correct vara lord.

*End — 4C-4-S3.*
