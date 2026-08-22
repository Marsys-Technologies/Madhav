---
artifact: OVERNIGHT_DECISION_LEDGER
canonical_id: PARIPRASHNA_OVERNIGHT_DECISION_LEDGER_2026_08_22
version: 1.0
status: LIVE — append-only, written throughout the 2026-08-23 overnight run
authority: PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md §3.4
role: >
  Every decision the NATIVE-SURROGATE made in the native's absence during the P3+P4 combined
  overnight run, plus every conductor operational judgment worth the native's morning review.
  All entries are labelled DELEGATED-OVERNIGHT, native review pending — none is presented as
  the native's own decision. Reviewing this file IS the native's asynchronous verdict on the
  night.
---

# Overnight decision ledger — Paripraśna P3+P4, 2026-08-23

Format per §3.4: sequence · timestamp · question as asked · decision · precedent cited or
principle applied · reversibility note · the falsifier (what would change the native's mind).

---

## D-001 — 2026-08-22T21:28:50Z — CONDUCTOR (operational, not a surrogate ruling)

**Question as asked:** `tracker-health-check` reports OBSERVATORY UNHEALTHY at run open — an
unacknowledged 170s blind window (2026-08-22T20:44:27Z → 20:47:17Z). Acknowledge it and proceed,
or treat an unhealthy observatory as a run-open blocker?

**Decision:** Acknowledged via `tracker-ack-blind` and proceeded. Recorded here and in the
run-open coordination entry rather than left silent.

**Precedent / principle:** The tracker README's own §(d) makes acknowledgement an explicit
operator action, and the gap's provenance is known and benign — it is the daemon restart from
this run's own environment setup (~02:14–02:17 IST), not an unexplained observability hole. The
alternative (silently ignoring a red health check) is the failure class `tracker-health-check`
exists to prevent. Recording the acknowledgement is what keeps it honest (§N.8: a signal that
can never read false is not a signal; this one read false, correctly, and was cleared by a
named human-equivalent action, not by a self-clearing timer).

**Reversibility:** Fully reversible — the acknowledgement is a flag in
`~/.pariprashna-tracker/BLIND_WINDOW.json`; the measured gap itself is preserved in the file
and in this ledger regardless.

**Falsifier:** If the native's own review finds that the 02:14–02:17 gap was NOT the setup
restart — i.e. the daemon was down for an unexplained reason — the acknowledgement was
premature and the window needs re-investigation from `~/.pariprashna-tracker/logs/`.

