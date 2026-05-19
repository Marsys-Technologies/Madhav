---
artifact: PHASE_4C_6_CLOSE_v1_0.md
type: PHASE_CLOSE
version: 1.0
status: CLOSED
phase: 4C.6
phase_name: Muhurat Finder
closed_on: 2026-05-20
sealed_by: 4C-6-S4
worktree: /Users/Dev/Vibe-Coding/Apps/Panchang
branch: feature/phase-4c-panchang
sessions:
  - 4C-6-S1  # Muhurat backend: scoring engine + API endpoint
  - 4C-6-S2  # Weights YAML + S2 scoring tests
  - 4C-6-S3  # Muhurat Finder UI: modal + results + hook + ActionBar
  - 4C-6-S4  # E2E tests + acharya review + perf + docs + close
---

# Phase 4C.6 Close — Muhurat Finder

## §1 — Delivery Summary

Phase 4C.6 ships the complete Muhurat Finder: a tool that ranks calendar dates
by classical Jyotish auspiciousness criteria for 6 event types, end-to-end from
Python scoring engine to UI surface.

## §2 — What was shipped (all 4 sessions)

### Backend (4C-6-S1)

| Component | Path | Description |
|---|---|---|
| Shastra tables | `panchang_engine/shastra_tables.py` | 6 per-event quality tables (VIVAH, GRIHA_PRAVESH, VYAPARA, YATRA, PROPERTY_PURCHASE, MANTRA_INITIATION); EVENT_TABLES dispatch dict |
| Tara Bala | `panchang_engine/tara_bala.py` | Nava Tara Chakra (9-position × 3 cycles); Tara Bala + Chandra Bala native overlay |
| Muhurat engine | `panchang_engine/muhurat.py` | score_muhurat() → 0..100; knockout logic; _score_breakdown() explainability; find_muhurat() range scan |
| API endpoint | `python-sidecar/routers/muhurat.py` | POST /api/compute/muhurat; 90-day cap; chart_id→NatalChart |
| Tests | `panchang_engine/tests/test_muhurat_scoring.py` | 31 scoring tests PASS |

### Weights YAML (4C-6-S2)

| File | Description |
|---|---|
| `panchang_engine/config/muhurat_weights.yaml` | Auditable per-event weight overrides; defaults + 6 event blocks; classical source citations; avoid_penalty hard-locked at 1.0 |

### UI (4C-6-S3)

| Component | Path | Description |
|---|---|---|
| Hook | `src/app/panchang/hooks/useMuhuratFinder.ts` | POST /api/compute/muhurat; {windows, isLoading, error, search} |
| Modal | `src/app/panchang/components/MuhuratFinderModal.tsx` | Form: event + date range + location + personalise; 90-day cap validation |
| Results | `src/app/panchang/components/MuhuratResultsList.tsx` | Star rating + breakdown badges + Ask-Madhav deep link + Calendar (disabled 4C-7) |
| Star rating | `src/components/ui/star-rating.tsx` | Reusable 1–5★ display component |
| API proxy | `src/app/api/compute/muhurat/route.ts` | Next.js → sidecar proxy; auth-optional |
| ActionBar | `src/app/panchang/components/ActionBar.tsx` | "Find Muhurat" button wired to modal |

### Closure (4C-6-S4)

| Artifact | Path | Description |
|---|---|---|
| E2E test | `platform/tests/integration/test_muhurat_finder_e2e.test.ts` | 12/12 PASS against live sidecar |
| Acharya review | `platform/tests/visual/4C6_acharya_review.md` | 25 windows × 5 events; canary PASS |
| Perf baseline | `platform/tests/perf/4C6_S4_perf.md` | No regression; 87–97% of S1 baseline |
| README | `panchang_engine/README.md §9` | Muhurat Finder section: events, weights, breakdown, latency |

## §3 — Acceptance Criteria Status (master plan §8 AC.4C.6)

| AC | Description | Status |
|---|---|---|
| AC.4C.6.1 | Muhurat Finder returns ranked windows for all 6 MVP events | PASS (S1) |
| AC.4C.6.2 | Score breakdown per window (tithi/nakshatra/vara/yoga/planet/native) | PASS (S1) |
| AC.4C.6.3 | YAML weights auditable + per-event tunable | PASS (S2) |
| AC.4C.6.4 | UI: Find Muhurat modal with form + results | PASS (S3) |
| AC.4C.6.5 | Ask-Madhav deep link from result window | PASS (S3) |
| AC.4C6S4.1 | E2E test PASS | PASS (S4) |
| AC.4C6S4.2 | Acharya review: 25 windows documented | PASS (S4) |
| AC.4C6S4.3 | Weight tuning (if needed) | PASS — no changes needed |
| AC.4C6S4.4 | Perf within 110% of S1 | PASS — 87–97% of S1 |
| AC.4C6S5.5 | README Muhurat Finder section | PASS (S4) |

## §4 — Key Technical Facts

- **Scoring formula:** `score = Σ(weight[k] × quality[k]) × 100`; knockout → 0.0
- **Star rating:** 80=5★, 65=4★, 50=3★, 35=2★, <35=1★
- **Latency:** 7–8 ms/day; 30d≈0.22s, 90d≈0.68s (44× faster than brief estimate)
- **Engine version:** 1.0.0-S3
- **Classical sources:** Muhurta Chintamani, Brihat Samhita, Muhurta Martanda, Drik Panchang

## §5 — Known Issues + Deferred Items

| Issue | Severity | Deferred To |
|---|---|---|
| Issue I.1: yoga names serialized as empty strings (scoring correct) | Low | 4C-7 sidecar fix |
| Revati nakshatra score for property_purchase slightly generous (0.85 → 0.70 proposed) | Minor | 4C-9 acharya panel |
| Saturday vara for property_purchase slightly low (0.20 → 0.35 proposed) | Minor | 4C-9 acharya panel |
| Export to Calendar button disabled (UI stub with 4C-7 badge) | Feature gap | 4C-7 |
| Sub-day muhurta windows (v2 precision) | Enhancement | v2 (future) |

## §6 — Acharya Review Caveat

The 4C6_acharya_review.md contains LLM-derived provisional verdicts. The canary
passed (no systematic failure). Final acharya sign-off is a **Wave 1 close concern
(4C-9)**, not a 4C.6 deliverable. Do not treat the LLM-derived verdicts as final
acharya validation.

## §7 — Next Phase

**4C-7: iCal Export.** The "Export to Calendar" button in MuhuratResultsList.tsx
is currently disabled (4C-7 badge). 4C-7 scope: MuhuratWindow → .ics file generation,
download flow, and optional Google Calendar deep link.

---

*Phase 4C.6 CLOSED 2026-05-20. Sessions 4C-6-S1 through 4C-6-S4. Sealing commit: see SESSION_LOG.*
