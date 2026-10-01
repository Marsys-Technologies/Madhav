---
artifact: A2_5_BUILD_ORDERING_NOTE
version: "1.0"
status: CURRENT
date: 2026-10-02
source: "steward M20261001T194030-8c0f (Suvarṇa PR #2860 boundary-flip report on the canonical chart 482012f1)"
---

# A2.5 — build-ordering precondition: the L1 rebuild comes first

**Rule.** The `'4.1'` candidate build for 482012f1 (and any row that depends on the daśā
build — everything `step06a` pins through `chart_dashas`, including the A5.3 `'5.0'`
`period_running_at` / `p4_double_transit` prerequisites) MUST run **after** the L1
ephemeris-backend rebuild lands, never straddling it.

**Why.** Production L1 (`chart_facts`, `panchanga_daily`) was computed on the Moshier
fallback; Suvarṇa's `.se1` re-computation reports, for the canonical chart: zero class
flips, all seven FORENSIC birth anchors hold, largest input move 0.665″ (Moon) — and
**Vimshottari period starts shift by +6,993 s**. After the L1 rebuild the daśā build the
step06a pins read is a NEW build id with slightly different boundaries. A candidate built
before it cites a daśā generation that no longer exists; one built across it mixes two.

**Operational consequence.** The Cloud Run job (A2.5) must not be launched until the
steward confirms the L1 rebuild has landed. The writer's own gates already fail closed on
the backend (Moshier fallback ⇒ `EphemerisBackendError`, including the Moon's file-level
probe added with this note — `services/gochara_kernel/knots.py::_assert_moon_file_backend`),
but nothing in the writer can know whether the *L1 facts it cites* were computed before or
after the rebuild; that ordering is an operator precondition, recorded here.
