---
artifact: WP7_REVIEW_REQUEST_12_5
packet_id: "§12.5-test-isolation"
version: "1.0"
status: REVIEWED_BY_ADHIKARIN
disposition: "REVIEWED_BY_ADHIKARIN 2026-09-27 per ADK-0013 — ACCEPT WITH CONDITION: the root cause is UNKNOWN and the fix is a guard, not a cure; the unknown root cause and the pre-existing test_wp6_ledger/test_wp7_sentinel ordering quirk remain recorded as open known-items, and any recurrence of either automatically reopens this packet rather than being absorbed as flake. NOT marked REVIEWED: K3/O-2 is separate and unaffected."
date: 2026-09-24
author: "subagent (l3/gochara-autonomous-wp0-7, §12.5 fix)"
design_file: "GOCHARA_REMAINDER_EXECUTION_BRIEF_v1_0.md §12.5"
commit: "see §12.5 commit series on l3/gochara-autonomous-wp0-7 (conftest earned-signal guard)"
---

# REVIEW REQUEST — §12.5: the test-isolation defect fix

## What landed

`test_wp3a_kernel.py::test_case_02_mean_node_convention` once failed in a full-suite run
("jd -0.001010 outside Moshier planet range") while passing alone. The cause is UNKNOWN
and recorded as such — the failure has not reproduced since, in any ordering, with or
without a reachable database.

What was made true instead (the brief's ask: a recurrence must identify itself):

- `tests/l3/gochara/conftest.py::assert_real_ephemeris()` — called first by
  real-ephemeris tests; fails LOUDLY if `swisseph` is not a real module or
  `swe.julday(2000,1,1,12.0) != 2451545.0` (stubbed/replaced ephemeris, finding F-31),
  instead of letting a stubbed global silently decide a ruled convention's test.
- The two guard self-tests (`test_guard_fires_when_the_ephemeris_is_stubbed`,
  `test_guard_fires_when_the_module_is_not_a_module`) prove the detector goes red.

## Tests

- Full battery green after the fix: **327 passed, 0 failed** (later 334 with §12.4),
  including pairwise orderings of the historically interacting tests.
- Known pre-existing quirk, verified at the pre-1087 baseline and NOT introduced here:
  `test_wp6_ledger.py::test_crash_mid_write_resume_cleanly` fails if
  `test_wp7_sentinel.py` runs before it in one pytest process; battery (alphabetical)
  order is green. Recorded so the reviewer does not attribute it to this fix.

## Notes for the reviewer

1. This is a guard, not a root-cause fix — the root cause is unknown and the note says so.
2. Nothing marked REVIEWED.
