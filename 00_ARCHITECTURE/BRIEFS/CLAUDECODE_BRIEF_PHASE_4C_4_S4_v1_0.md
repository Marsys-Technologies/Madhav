---
artifact: CLAUDECODE_BRIEF_PHASE_4C_4_S4_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: READY
authored_by: Cowork 2026-05-19
session_id: 4C-4-S4
session_name: 4C-4-S4 — Action Bar shell + Responsive polish + /panchang MVP close
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/phase-4c-panchang
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §4.2 + §6 (4C.4 acceptance)
predecessor: 4C-4-S3
---

# CLAUDECODE_BRIEF — Phase 4C-4-S4
## Action Bar shell + Responsive polish + /panchang MVP close

Closing session for the /panchang UI sub-phase. Adds the action bar (3 buttons as shells — full Muhurat Finder logic is 4C-6, Calendar Export is 4C-7, Ask-Madhav is 4C-8), responsive breakpoints, and closes 4C.4 with visual parity sign-off vs Drik.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
test -f platform/src/app/panchang/components/SpecialYogasList.tsx
test -f platform/src/app/panchang/components/ChoghadiyaPanel.tsx
test -f platform/src/app/panchang/components/HoraPanel.tsx
```

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. Master plan §4.2 (mockup — bottom action bar) + §4.4 (the three actions — but their full implementations are deferred to 4C-6/7/8)
3. All S1/S2/S3 components for style consistency
4. Existing brand button patterns in `platform/src/components/ui/`

## §3 — Scope (8 items)

### Item 1 — `ActionBar` component (shells)
Create `platform/src/app/panchang/components/ActionBar.tsx`. Three buttons per §4.2 mockup:
- `🔎 Find Muhurat` — opens placeholder modal saying "Muhurat Finder coming in 4C-6"; for now disabled or shows "Phase 4C-6" coming-soon hint
- `📅 Export to Calendar` — disabled with "4C-7" hint
- `💬 Ask Madhav about this day` — opens chat at `/clients/[id]/consume` with a pre-loaded prompt "Tell me about today's Panchang and what it means for me." (this one works; 4C-8 enhances deep-linking with context block)

Sticky bottom on mobile (`position: sticky; bottom: 0` with safe-area-inset-bottom).

**AC.4C4S4.1:** ActionBar renders; 2 buttons disabled with coming-soon hints; Ask-Madhav button opens chat with pre-loaded prompt.

### Item 2 — Responsive breakpoints
Audit the full page at breakpoints: mobile (375px), tablet (768px), desktop (1280px). Ensure:
- PanchangHeader collapses to vertical stack on mobile
- TimingsPanel + PlanetaryGrid stack vertically on mobile (instead of side-by-side)
- SpecialYogasList wraps gracefully
- ChoghadiyaPanel/HoraPanel collapsed by default; full-width when expanded
- ActionBar sticky-bottom on mobile, inline on desktop

**AC.4C4S4.2:** Full page renders correctly at all three breakpoints; no horizontal scroll on mobile.

### Item 3 — Personalise dropdown shell (real shell, not just disabled)
Update the personalise dropdown in `PanchangHeader.tsx` to be functional as a UI but with empty options (until 4C-5 wires chart loading). "Generic Panchang" is the default; "(Personalise — coming in 4C-5)" as a disabled label below.

**AC.4C4S4.3:** Dropdown is interactive; default is "Generic Panchang"; future-state hint visible.

### Item 4 — Empty/error states polish
Handle:
- Date is in the future beyond ephemeris range → friendly message
- Sidecar 500 error → friendly message + retry button
- Polar latitude where sun doesn't rise → "Sunrise N/A — this location is currently in polar twilight"

**AC.4C4S4.4:** Edge-case states tested manually with curated bad inputs.

### Item 5 — Performance check
Verify `/panchang` first-render under 800ms on a warm sidecar; under 1500ms on cold. If beyond, profile (Server-Side React + sidecar call + render). Latency floor is set by sidecar compute (engine does 100-300ms per call). Cache layer is 4C-2 territory; this session just measures and documents.

**AC.4C4S4.5:** Latency budget documented in `platform/tests/perf/4C4_baseline.md`.

### Item 6 — Comprehensive visual parity check
Take screenshots of `/panchang` for FIVE sample dates: today, native's birthday (1984-02-05), a Guru Pushya day, a Bhadra day, and a Sankranti day. Compare side-by-side with drikpanchang.com for the same dates. This is the MVP close gate.

**AC.4C4S4.6:** Visual parity report in `platform/tests/visual/4C4_close_report.md` — all 5 dates pass acharya-grade visual review.

### Item 7 — Phase 4C.4 close protocol
- Update CURRENT_STATE: `4C.4 CLOSED 2026-05-19`; next: 4C-5
- Append SESSION_LOG with 4C-4-S4 atomic block
- Update Phase 4 master plan §B: 4C.4 row to CLOSED
- Author `00_ARCHITECTURE/PHASE_4C_4_CLOSE_v1_0.md` — one-page summary of MVP UI delivery
- Update queue: 4C-4-S4 → passed; 4C-5 next eligible

**AC.4C4S4.7:** All close-protocol steps complete.

### Item 8 — Brief flip + FINAL_SUMMARY
Flip this brief to COMPLETE; emit FINAL_SUMMARY.

**AC.4C4S4.8:** Done.

---

## §5 — Constraints
**may_touch:** `platform/src/app/panchang/components/ActionBar.tsx`, `platform/src/app/panchang/page.tsx` (wiring), `platform/src/app/panchang/components/PanchangHeader.tsx` (personalise shell only), `platform/tests/perf/**`, `platform/tests/visual/**`, governance state files, this brief, 4C-4-S4 close artifact.
**must_not_touch:** sidecar, retrieve/, prior session components' internals, corpus, master plan, other unrelated UI areas.

## §6 — Close checklist
- [ ] 8 ACs PASS
- [ ] Visual parity report at 5 dates documented
- [ ] Phase 4C.4 close protocol all 5 steps
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- Muhurat Finder, Calendar Export, Ask-Madhav full impls deferred to 4C-6/7/8; this session only ships shells
- Personalise overlay is 4C-5; shell only here
- /panchang MVP closes here regardless of cache layer (4C-2 deferred)

## §9 — Canary
Visual parity vs Drik for 5 sample dates is the close gate. Acharya-grade review: a senior practitioner looking at our /panchang and Drik's panchang for the same date should see the same answer to "what's the panchang today?"

*End — 4C-4-S4 closes Phase 4C.4.*
