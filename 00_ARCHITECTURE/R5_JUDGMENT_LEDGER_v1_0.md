---
canonical_id: R5_JUDGMENT_LEDGER
version: 1.0
status: LIVE — empty shell, ready for Pratinidhi-R rulings
created: 2026-07-08
author: Claude Code (executing CLAUDECODE_BRIEF_R5_RETRIEVAL_3_0_AUTONOMOUS_RUN_v1_0.md Phase-0)
program: RETRIEVAL_3_0_FACETED_INSTRUMENTS_DESIGN_v1_0.md v1.6 (governing law)
---

# R5 JUDGMENT LEDGER

Every question, ambiguity, confirmation, or judgment call routed to Pratinidhi-R (the authority swarm;
see brief §1) during the R5 run lands here as an entry — never resolved silently by an implementation
lane, never routed back to the native mid-run. Append-only; entries are never edited after being
recorded, only superseded by a later entry that cites the one it revises.

Pratinidhi-R's constitution (strict precedence, per the brief): (1) design doc v1.6 as governing law;
(2) pillar order when in tension — ASTROLOGY > answer-correctness > honesty > latency/tokens > code
convenience; (3) classical citation required for any astrological call (canonical-or-floor — no
uncited substitute, floor with reason given); (4) mainstream-with-contested-flag for genuinely disputed
points. Every ruling here carries native retrospective veto (brief `ratification` clause) — the native
may overturn any entry after the fact; that does not retroactively invalidate work already gated on it,
but does obligate a follow-up entry recording the reversal.

## Entry schema

Each entry is a level-3 heading `### JL-<NNN> — <short title>` with these fields:

- **id** — `JL-<NNN>`, monotonically increasing across the whole R5 run (continues from this file's
  last entry; does not restart per wave).
- **question** — the exact ambiguity, conflict, or decision point a lane or verifier raised.
- **ruling** — Pratinidhi-R's decision, stated as an instruction an implementation lane can act on
  without further clarification.
- **basis** — which constitution tier resolved it (design doc §-citation; pillar-order tiebreak;
  classical citation; or mainstream-with-contested-flag), plus the specific evidence (dossier section,
  audit transcript, live probe result) that grounded the ruling.
- **reversibility** — one of: `reversible` (a later wave can undo this without re-litigating prior
  work), `hard-to-reverse` (undoing it means redoing shipped work), `irreversible` (a prod-visible
  contract change, e.g. an envelope shape or a response_format default flip). Ledger entries with
  `hard-to-reverse` or `irreversible` reversibility get flagged for explicit native attention in the
  next checkpoint report, even though the run does not wait for a reply.

No entries yet — this ledger opens empty at Phase-0 close. The first entry lands when W0a's first lane
raises its first question to Pratinidhi-R.
