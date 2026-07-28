---
artifact: FIXTURE_REGISTER (not real — check_reconciliation_cadence.py --self-test only)
---

# Fixture Register

## §A — fixture rows

| ID | Finding | Status |
|---|---|---|
| FIX-1 | closed in both cr_status.ts copies but this row was never flipped | OPEN |
| FIX-2 | copy A says open, copy B says closed (dual-copy drift) | OPEN — ELEVATED |
| FIX-3 | code still lists this open in both copies, but the fix shipped and this row was flipped | CLOSED_WITH_EVIDENCE [fixture: shipped commit deadbeef, live-verified] |
| FIX-4 | self-contradictory in copy A (both OPEN_CRS and CLOSED_CRS) | OPEN |
| FIX-5 | known_gap cites this even though copy A already closed it | OPEN |
| FIX-6 | closed everywhere, register correctly flipped — the clean case | CLOSED — fixture, no divergence expected |
