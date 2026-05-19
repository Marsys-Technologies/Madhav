---
artifact: CLAUDECODE_BRIEF_PHASE_4C_4_S2_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
authored_by: Cowork 2026-05-19
session_id: 4C-4-S2
session_name: 4C-4-S2 — Timings Panel + Planetary Grid
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/phase-4c-panchang
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §4.2 + §5.5
predecessor: 4C-4-S1
---

# CLAUDECODE_BRIEF — Phase 4C-4-S2
## Timings Panel + 9-Graha Planetary Grid

S2 of the /panchang UI build. Adds the timings panel (sunrise/sunset/moonrise/moonset + inauspicious + auspicious windows) and the 9-graha planetary positions grid.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
test -d platform/src/app/panchang
test -f platform/src/app/panchang/components/PanchangHeader.tsx
test -f platform/src/app/panchang/components/PrimaryStrip.tsx
test -f platform/src/app/panchang/hooks/usePanchangDay.ts
```
Halt with HALT_NEEDS_HUMAN if S1's outputs aren't present.

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. `00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md` §4.2 + §5.5
3. `platform/src/app/panchang/components/PrimaryStrip.tsx` (S1 sibling — match its style)
4. `platform/src/app/panchang/page.tsx` (server component data flow)
5. The Panchang dataclass fields: `inauspicious`, `auspicious`, `planets` (from sidecar response)

## §3 — Scope (8 items)

### Item 1 — `TimingsPanel` component
Create `platform/src/app/panchang/components/TimingsPanel.tsx`. Two-column layout per §4.2 mockup:
- Left column: Sunrise, Sunset, Moonrise, Moonset (with "—" for missing moon transitions); below that Rahu Kalam, Yamagandam, Gulika Kalam windows; below that Abhijit, Brahma Muhurta, Amrit Kalam windows.
- Right column: 9 grahas (handled in Item 2; this column space is reserved here).

All times displayed in local TZ (HH:MM). Inauspicious windows styled in warning color; auspicious in success color.

**AC.4C4S2.1:** TimingsPanel renders with all 10+ rows; warning/success color coding correct.

### Item 2 — `PlanetaryGrid` component
Create `platform/src/app/panchang/components/PlanetaryGrid.tsx`. Renders 9 grahas (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Rahu, Ketu) each with:
- Sanskrit name + English name
- Sign (Sanskrit + glyph if available)
- Longitude in DMS within sign (e.g., "Mesha 04°23'")
- Retrograde marker (R)
- Combust marker (C)

Layout: 3-column grid on desktop, single-column on mobile. Legend strip below grid: "R = retrograde · C = combust".

**AC.4C4S2.2:** PlanetaryGrid renders all 9 grahas correctly for today's chart; retrograde/combust flags visible where applicable.

### Item 3 — Sanskrit sign glyphs
Add 12 zodiac sign glyphs as inline SVGs in `platform/src/components/ui/icons/zodiac/`. Or use Unicode glyphs if simpler (♈♉♊♋♌♍♎♏♐♑♒♓). Choice depends on existing icon convention in the project.

**AC.4C4S2.3:** Sign glyphs render next to graha rows.

### Item 4 — DMS formatter
Add `platform/src/lib/format/dms.ts` — converts decimal degrees to "DD°MM'SS"" format. Reused across PlanetaryGrid + future components.

**AC.4C4S2.4:** DMS formatter tested with edge cases (0°, 360° wrap, negative).

### Item 5 — Page wiring
Update `platform/src/app/panchang/page.tsx` to render `TimingsPanel` and `PlanetaryGrid` below the `PrimaryStrip` from S1. Maintain the two-column layout from §4.2 mockup.

**AC.4C4S2.5:** Full page renders header + primary strip + timings + planetary grid stacked correctly.

### Item 6 — Component unit tests
Tests for `TimingsPanel` (renders all timing types, handles missing moon transitions) and `PlanetaryGrid` (9 grahas, retro/combust flags).

**AC.4C4S2.6:** All component tests PASS.

### Item 7 — Visual parity check
Take a screenshot of `/panchang` for today's Bhubaneswar Panchang. Compare against drikpanchang.com's display for the same date. Document any visual discrepancies > display-rounding tolerance.

**AC.4C4S2.7:** Visual comparison documented in `platform/tests/visual/4C4_S2_drik_compare.md` (or similar); discrepancies if any flagged.

### Item 8 — Session close
Update CURRENT_STATE; append SESSION_LOG; flip brief; emit FINAL_SUMMARY.

**AC.4C4S2.8:** Close protocol complete.

---

## §5 — Constraints
**may_touch:** `platform/src/app/panchang/**`, `platform/src/lib/format/dms.ts`, `platform/src/components/ui/icons/zodiac/**`, governance state files, this brief.
**must_not_touch:** sidecar, retrieve/, Phase 4C-3 sealed code, corpus, S1's existing components (only ADD to them via page.tsx wiring; don't edit S1's component internals).

## §6 — Close checklist
- [ ] 8 ACs PASS; component tests green
- [ ] Visual parity check documented
- [ ] CURRENT_STATE + SESSION_LOG updated; FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- Brand tokens from S1 inheriting
- Timing windows clipped to local-TZ display per §4.2 mockup
- Retrograde/combust flags come from the engine's PlanetState

## §9 — Canary
`/panchang` page for today's Bhubaneswar should match Drik's display for: 4 timings (Rahu/Yama/Gulika/Abhijit) and 9 graha positions. ±2 min on timings; exact match on graha signs.

*End — 4C-4-S2.*
