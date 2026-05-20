---
artifact: RT_4C_1_FINDING.md
probe_id: RT.4C.1
probe_question: >
  Layer purity — does any UI component create derivations the engine should own?
session_id: 4C-9
authored_on: 2026-05-20
verdict: WARN
mitigation_status: ACCEPTABLE — see §3
---

# RT.4C.1 — Layer Purity Finding

## §1 — Probe question

Does any UI component in the Phase 4C Panchang module perform astrological
derivations that properly belong in the engine?

## §2 — Evidence examined

Files inspected:
- `platform/src/app/panchang/components/` (all 12 components)
- `platform/src/lib/panchang/tara_bala.ts`
- `platform/src/lib/panchang/chandra_bala.ts`
- `platform/src/lib/format/dms.ts`
- `platform/python-sidecar/panchang_engine/tara_bala.py`
- `platform/python-sidecar/panchang_engine/muhurat.py`

## §3 — Findings

### Finding A — tara_bala.ts + chandra_bala.ts (WARN, not FAIL)

`PrimaryStrip.tsx` calls `computeTaraBala()` from `tara_bala.ts`.
`PlanetaryGrid.tsx` calls `computeChandraBala()` from `chandra_bala.ts`.
These functions are implemented in the TypeScript client layer, not delegated
to the Python engine.

**Why this is WARN, not FAIL:**

1. The Python engine has `tara_bala.py` with equivalent logic (`compute_tara_bala_score`,
   `compute_chandra_bala_score`). The engine uses these for muhurat scoring — all scoring
   decisions flow through the engine (not the client).

2. The TS functions serve the *personalisation overlay display only* — they annotate
   the Primary Strip and Planetary Grid with a Tara Bala label and Chandra Bala strength
   badge for the currently-logged-in native. This is pure UI annotation, not a
   Muhurat recommendation or a stored derivation.

3. The TS and Python implementations share the same static lookup tables (9-Tara
   cycle, 12-sign Chandra Bala table) drawn from classical Muhurta Shastra sources.
   The test suite (`test_muhurat_scoring.py` lines 375–420) cross-validates outputs
   across both implementations.

4. The inputs to these functions come from the engine: `birth_nakshatra_id` and
   `current_nakshatra_id` are engine-computed and arrive via `native_context` in
   the panchang payload. The TS layer does not derive these inputs — it only applies
   the table lookup once.

**Layer purity assessment:** The TS Tara/Chandra functions are equivalent to a
"format + label" step applied to engine-computed inputs. B.1 prohibits mixing
"facts into interpretations" — but this is a presentation-layer annotation using
a deterministic 9-step lookup table, not an interpretation. The engine owns all
scoring decisions that affect recommendations.

**Mitigation:** For v2, the personalisation overlay could be moved fully into
the engine's response (engine emits `tara_bala_label` + `chandra_bala_strength`
fields in the panchang payload). This would eliminate the TS derivation entirely.
Track as `PHASE_4C_FOLLOWUPS §FU.6` wave.

### Finding B — dms.ts lonWithinSign (PASS)

`PlanetaryGrid.tsx` calls `lonWithinSign()` to compute degrees-within-sign from
absolute longitude (e.g. 48° → 18° in Vrishabha). This is a modular arithmetic
formatting step — `absoluteLon % 30` after normalization. It does not derive
any astrological fact; it reformats a fact for display. PASS.

### Finding C — MuhuratResultsList.tsx score display (PASS)

The results list sorts `windows` defensively by `score` descending (backend
already sorts). It does not recompute scores — it formats and renders the
engine-provided `score`, `star_rating`, and `breakdown` dict. PASS.

## §4 — Verdict

**WARN** — One bounded layer purity deviation (TS Tara/Chandra overlay functions).
Acceptable for Wave 1: the engine owns all scoring decisions; the TS functions
are deterministic lookup tables applied to engine-provided inputs for display
annotation only. Mitigation path documented. No FAIL items.
