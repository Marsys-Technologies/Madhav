---
subsystem: transit
gate: Gate-2 IN PROGRESS
timestamp: 2026-06-17
tier: Tier-1 (auto-resolved)
---

# Transit Gate-2 Pass Notes

## Gate-1 → Gate-2 transition
- Gate-1 commit: 1114f7c4 (Śilpī — 7 files, 19 tests)
- Spec-review verdict: SPEC_COMPLIANT_MINOR_GAPS → 4 real gaps (Gap 8 withdrawn — ayanamshas correct)

## Gap resolutions

1. **Gap 1 (idempotency contradiction)**: Removed ON CONFLICT DO UPDATE from `ga_transit_anchors` INSERT — pure §N.3 delete-then-insert; ON CONFLICT was dead code after DELETE but masked silent failures
2. **Gap 2 (FORENSIC silent skip)**: Changed `if moon_sign and moon_sign != 'aquarius'` → `if not moon_sign or moon_sign != 'aquarius'` — absent Moon now triggers FORENSIC halt
3. **Gap 3 (happy-path test weak)**: Added `assert result.rows_inserted > 0` to `test_forensic_moon_sign_passes_for_aquarius`
4. **Gap 5 (dry_run rows_inserted)**: `bg_transit_rules` writer was returning catalog size (50) as rows_inserted on dry_run; added early return with rows_inserted=0

All fixes in commit: acbe28c5 — all 19 tests pass

## Note on Gap 8 (withdrawn)
Reviewer flagged ayanamsha IDs as wrong, but _AYANAMSHAS list in ga_transit_anchors.py already
uses the CORRECT canonical IDs: lahiri_chitrapaksha, true_chitra, krishnamurti, raman, surya_siddhanta_classical.
These match CANONICAL_AYANAMSHAS in ga_positions_writer.py exactly.

## Migration 262 fix (concurrent)
PR #287: migration 262 (Prashna-L0 asset_registry) used nonexistent `display_name` column.
Direct fix on branch fix/migration-262-display-name — changed to english_name, fixed layer/storage_type,
added BEGIN/COMMIT.

## PR
- PR #288: feature/subsystem-transit → main
- CI: pending

## Gate-2 acceptance criteria
- [ ] CI green (19 tests pass)
- [ ] PR merged
- [ ] Surgical migration apply: 266 → 267 → 268
- Gate-3: ga_transit_anchors cockpit tile lit for chart 482012f1 (45 rows = 9 grahas × 5 ayanamshas)
- Gate-3: FORENSIC Moon=aquarius PASS
