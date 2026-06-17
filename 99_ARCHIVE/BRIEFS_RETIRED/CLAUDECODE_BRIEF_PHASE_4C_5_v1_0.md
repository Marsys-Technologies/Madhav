---
artifact: CLAUDECODE_BRIEF_PHASE_4C_5_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Cowork 2026-05-19
session_id: 4C-5
session_name: 4C-5 — Personalise overlay (Tara Bala + Chandra Bala + localStorage)
executor: Claude Code sub-agent (Conductor)
worktree:
  branch: feature/phase-4c-panchang
  path_absolute: /Users/Dev/Vibe-Coding/Apps/Panchang
governing_plan: 00_ARCHITECTURE/PHASE_4C_PANCHANG_MASTER_PLAN_v1_0.md §4.3 + §5.4 (chart_id pass-through)
predecessor: 4C-4-S4 (Phase 4C.4 CLOSED)
---

# CLAUDECODE_BRIEF — Phase 4C-5
## Personalise Overlay: Tara Bala + Chandra Bala + Chart Selection

Wires the personalise dropdown to actual chart data. When user selects a chart, Panchang gets:
- Tara Bala badge on the Nakshatra row (Janma/Sampat/Vipat/Kshema/Pratyari/Sadhaka/Vadha/Mitra/Ati Mitra)
- Chandra Bala badge on the Moon row (favourable/unfavourable rashis relative to native's Moon)
- Native-aware annotations on special yogas (dasha-amplification flags)

Single session per master plan.

---

## §0 — Pre-flight
```bash
cd /Users/Dev/Vibe-Coding/Apps/Panchang
test -f 00_ARCHITECTURE/PHASE_4C_4_CLOSE_v1_0.md
test -f platform/src/app/panchang/components/PanchangHeader.tsx
test -f platform/src/app/panchang/components/PrimaryStrip.tsx
# Verify Chart table exists in Supabase migrations (existing project)
grep -l "CREATE TABLE.*chart" platform/supabase/migrations/ 2>/dev/null || true
```

## §2 — Mandatory reads
1. `CLAUDE.md` §C
2. Master plan §4.3 (personalise dropdown spec)
3. `platform/src/lib/retrieve/query_panchanga.ts` (chart_id param wiring)
4. Existing Chart model — search for `chart` in `platform/src/lib/db/` or Prisma schema
5. FORENSIC v8.0 §10.1 + §20.1 for Tara Bala / Chandra Bala source-of-truth example (native's birth Nakshatra + Moon sign)

## §3 — Scope (10 items)

### Item 1 — Tara Bala computation
Add `platform/src/lib/panchang/tara_bala.ts`. Function: `computeTaraBala(nativeBirthNakshatraId: number, currentNakshatraId: number) → TaraBalaName`. The 9 Taras cycle: count nakshatras from native's birth to current, modulo 9.

| Count (1-9, wrapping) | Tara |
|---|---|
| 1 | Janma |
| 2 | Sampat |
| 3 | Vipat |
| 4 | Kshema |
| 5 | Pratyari |
| 6 | Sadhaka |
| 7 | Vadha |
| 8 | Mitra |
| 9 | Ati Mitra |

Auspicious: Sampat, Kshema, Sadhaka, Mitra, Ati Mitra. Inauspicious: Vipat, Pratyari, Vadha. Mixed: Janma (own).

**AC.4C5.1:** Pure function tested for all 27×27 combinations; matches classical table.

### Item 2 — Chandra Bala computation
Add `platform/src/lib/panchang/chandra_bala.ts`. Function: `computeChandraBala(nativeMoonSignId: number, currentMoonSignId: number) → ChandraBalaStrength`. Returns one of `STRONG | MODERATE | WEAK`.

Convention: Moon transiting houses 1, 3, 6, 7, 10, 11 from natal Moon = strong; 2, 5, 9 = moderate; 4, 8, 12 = weak (chandrastama).

**AC.4C5.2:** Pure function tested for all 12×12 combinations.

### Item 3 — Chart loader hook
Add `platform/src/app/panchang/hooks/useChartList.ts`. Loads charts accessible to current user from Supabase. Returns `{ charts, isLoading, error }`. Mock auth user already on platform.

**AC.4C5.3:** Hook returns user's charts; respects RLS.

### Item 4 — Wire `PanchangHeader` personalise dropdown
Update `PanchangHeader.tsx` to use `useChartList`. Default: "Generic Panchang". Options: list of user's charts (e.g., "Abhisek (1984-02-05)"). On select, store `chart_id` in URL query string + localStorage. "Clear personalisation" option restores Generic.

**AC.4C5.4:** Dropdown is functional; switching populates chart_id state; localStorage persists across reloads.

### Item 5 — Pass chart_id through data fetch
Update `usePanchangDay` to include `chart_id` in the SWR cache key. Pass `chart_id` to `queryPanchanga`. The retrieval tool already accepts the param (per 4C-3); pass-through to sidecar.

**AC.4C5.5:** When chart selected, query rerun; sidecar receives chart_id (verify in network tab).

### Item 6 — Server-side chart hydration in sidecar
Update sidecar `/api/compute/panchanga` endpoint: when `chart_id` is non-null, fetch the chart from Supabase, compute native's birth Nakshatra + Moon sign, attach as `native_context` in response.

```python
class NativeContext(BaseModel):
    chart_id: str
    birth_nakshatra_id: int
    birth_nakshatra_name: str
    moon_sign_id: int
    moon_sign_name: str
    active_dasha_lord: Optional[str] = None  # for future dasha-aware muhurat in 4C-6

# In endpoint:
if req.chart_id:
    chart = await fetch_chart(req.chart_id, current_user)
    native_context = NativeContext(...)
else:
    native_context = None
```

Endpoint response gets a new optional `native_context` field.

**AC.4C5.6:** Sidecar correctly hydrates native_context; chart access respects user permissions (returns 403 if not authorized).

### Item 7 — Tara Bala / Chandra Bala badges in UI
Update `PrimaryStrip.tsx`:
- Nakshatra row: when `native_context` present, append a Tara Bala badge after the nakshatra name. Style: small pill, color-coded (success for auspicious Taras, warning for inauspicious, neutral for Janma).
- (Optional, since Moon isn't a primary-strip row) — Add Chandra Bala badge to the PlanetaryGrid's Moon row in `PlanetaryGrid.tsx`.

**AC.4C5.7:** With chart selected, Tara Bala badge appears on Nakshatra row; Chandra Bala on Moon row; correct color coding.

### Item 8 — Native-aware special yoga annotations (light touch)
In `SpecialYogasList.tsx`, when `native_context` present, add a small "for [native first name]" annotation when the yoga happens to align with native's birth Nakshatra (e.g., Sarvartha Siddhi where the nakshatra is the native's birth nakshatra). Full dasha-aware logic deferred to 4C-6's muhurat scoring; this is annotation only.

**AC.4C5.8:** When Sarvartha Siddhi on native's birth nakshatra, annotation appears.

### Item 9 — Component tests + visual review
Tests for `tara_bala.ts`, `chandra_bala.ts`, `useChartList`, badge rendering. Visual review: select Abhisek's chart on `/panchang` for today; verify Tara Bala + Chandra Bala badges render correctly relative to FORENSIC §10.1 + §20.1.

**AC.4C5.9:** All tests PASS; visual review documented.

### Item 10 — Close
CURRENT_STATE: 4C.5 CLOSED; SESSION_LOG appended; brief flipped; FINAL_SUMMARY. Queue: 4C-5 → passed; 4C-6-S1 next eligible.

**AC.4C5.10:** Close protocol complete.

---

## §5 — Constraints
**may_touch:** `platform/src/lib/panchang/{tara_bala,chandra_bala}.ts` (new); `platform/src/app/panchang/hooks/useChartList.ts` (new); `PanchangHeader.tsx`, `PrimaryStrip.tsx`, `PlanetaryGrid.tsx`, `SpecialYogasList.tsx`, `usePanchangDay.ts` (wiring); sidecar `main.py` (NativeContext + endpoint update); governance state files; this brief.
**must_not_touch:** engine internals (panchang_engine/* sealed); Phase 4C-3 RetrievalTool sealed; corpus; master plan; FORENSIC; other UI areas.

## §6 — Close checklist
- [ ] 10 ACs PASS; component + lib tests green
- [ ] Visual review with native's chart on today's Bhubaneswar Panchang documented
- [ ] Chart access security verified (RLS / auth)
- [ ] FINAL_SUMMARY emitted

## §7 — LLM stack
Gemini primary; Anthropic BANNED.

## §8 — Context carried
- Native's birth Nakshatra (from FORENSIC §10.1 area)
- Native's Moon sign (FORENSIC §20.1 area — Moon at 27°02' in D9 Gemini, D1 sign per natal chart)
- localStorage key: `panchang.personalise.chart_id`
- localStorage cleared by "Clear personalisation" option in dropdown

## §9 — Canary
Visual check with native (Abhisek) chart selected: Tara Bala and Chandra Bala badges must compute correctly relative to native's birth chart data. If incorrect, the classical table encoding has a bug.

*End — 4C-5.*
