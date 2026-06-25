---
subsystem: prashna_ga
gate: Gate-2 IN PROGRESS
timestamp: 2026-06-17
tier: Tier-1 (auto-resolved)
---

# Prashna-ga Gate-2 Pass Notes

## Gate-1 → Gate-2 transition
- Gate-1 commits:
  - 88174749 (Śilpī — 7 files, 18 tests)
  - 6d3c6433 (spec-review gap fix — CANONICAL_AYANAMSHAS import)
- Spec-review verdict: SPEC_COMPLIANT_MINOR_GAPS → 1 MINOR gap

## Gap resolutions

### MINOR fix
1. **MINOR [A] (CANONICAL_AYANAMSHAS duplication)**: Removed local `CANONICAL_AYANAMSHAS` list from `ga_prashna.py`; now imported from `ga_writers.ga_prashna_writer` — single source of truth, eliminates maintenance risk.

## Architecture notes

- `prashna_charts` is an INFRASTRUCTURE table (not an asset): links a chart_id (cast for the question-moment using the standard chart-build pipeline) to horary question metadata.
- `ga_prashna` is a per-chart heavy writer (5 ayanamshas × 1 judgment per ayanamsha).
- **Early return pattern**: When `chart_id` is not in `prashna_charts`, the writer returns 0 rows without error. This is correct for all natal chart builds (including `482012f1`).
- **No FORENSIC assertion**: Prashna charts are dynamic (question-moment driven); there is no canonical prashna chart_id to assert against.
- **Natural significators used** (not house lords): Moon = querent; natural karaka for question_class = quesited. House lord computation requires house cusps (not stored separately from ga_positions) — deferred to a future enhancement.

## All fixes in commit: 6d3c6433 — 18 tests pass

## PR
- PR #291: feature/subsystem-prashna → main
- CI: running (all checks pending)

## Gate-2 acceptance criteria
- [ ] CI green (18 tests pass)
- [ ] PR merged
- [ ] Surgical migration apply: 288 → 289 → 290 → 291
- Gate-3: ga_prashna_judgment has 0 rows for chart_id 482012f1 (natal chart → expected early return)
- Gate-3: ga_prashna_lagna has 0 rows for chart_id 482012f1 (same reason)
- Gate-3: cockpit tile for ga_prashna shows 0 rows (correct for natal build; will show rows when first prashna chart is registered)
