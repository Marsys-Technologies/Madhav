---
artifact: BNN_ENGINE_SPEC_v1_0.md
version: "1.0"
status: CURRENT
produced_during: M9-B-S1
produced_on: 2026-05-14
school: bnn
engine_file: platform/src/lib/schools/bnn_engine.ts
pending_flag: CF.M9.2 [TRANSIT_DATA_PENDING]
---

# BNN Engine Specification — M9-B-S1

## §1 — School Philosophy
Bhrigu Nandi Nadi (BNN) operates through sequential transit analysis: "Jupiter contacts planet X; then Saturn contacts the same planet/node; the sequence activates a specific outcome." This makes BNN inherently time-bound — it requires live transit positions to function. BNN is the only school among the 7 that is purely transit-driven rather than natal-dominant.

## §2 — Signal Coverage
- Primary: 24/573 (4.2%) — SIG.MSR.515–538
- Secondary: 5 (Nadi-BNN overlap)
- Silent: 544 (all natal signals — BNN trigger requires sequential transits, not natal placements)

## §3 — CF.M9.2 [TRANSIT_DATA_PENDING]
BNN requires Swiss Ephemeris live transit positions for 2026-05-14:
- Jupiter transit position: [EXTERNAL_COMPUTATION_REQUIRED]
- Saturn transit position: [EXTERNAL_COMPUTATION_REQUIRED]
- Specification: `swisseph.calc_ut(jd_for_2026_05_14, SE_JUPITER, SEFLG_SIDEREAL | SEFLG_LAHIRI)`
- Until provided: natal positions used as placeholder with confidence multiplier 0.45 (vs 0.85 live)

## §4 — Engine Logic
- `getTransitPositions(chartData)`: returns live or placeholder transit data
- Signal scoring: Jupiter/Saturn position relative to natal chart planets/houses
- Confidence multiplier: 0.45 (pending) vs 0.85 (live)

## §5 — Key Sequential Transit Patterns
- Jupiter contacts Ketu → spiritual liberation activation (SPIRITUAL highest)
- Jupiter contacts 10H → career elevation chain
- Saturn stabilizes 2H → family structure consolidation
