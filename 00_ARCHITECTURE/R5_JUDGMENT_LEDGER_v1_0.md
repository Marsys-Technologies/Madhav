---
canonical_id: R5_JUDGMENT_LEDGER
version: 1.0
status: LIVE — JL-001 recorded (W0a perf lane, r5/w0a-perf)
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

### JL-001 — S3 dual-output text-suppression size threshold

**question:** Design §21/S3 prescribes "structuredContent-only above a size threshold" for the MCP
dual-output helper (`dualOutput`/`errorOutput` in `registry_bridge.ts` and the four `register_p1_*.ts`
files) but does not name the threshold. Below what payload size should the text-fallback duplicate
still be sent, and above it suppressed?

**ruling:** 50,000 UTF-8 bytes (`Buffer.byteLength`, compact `JSON.stringify`, no pretty-print). Below
this, dual output (structuredContent + full compact-JSON text) is retained — small/typical responses
keep the MCP provider-spec text fallback for clients that don't consume structuredContent. At or above
it, the text fallback is replaced with a short pointer string and only structuredContent carries the
payload, eliminating the redundant second serialization for the responses where it costs the most
(the 174KB `ganita_yogas_get` case from the P3 probe would have transmitted a pretty-printed dual
payload materially larger than 174KB under the old code; now ~174KB structuredContent-only, no
duplicate text).

**basis:** Pillar order tiebreak (design doc names the mechanism, not the number) — this is a
latency/tokens vs. code-convenience question with no astrological content, so it resolves at tier (2)
without needing classical citation. 50KB was chosen as: (a) comfortably above the vast majority of
per-chart tool responses observed in the Phase-0 probe run (the healthy baseline responses were in the
sub-5KB to ~1KB range; only the known-oversized P3/P5 cases exceed it), so the common case is
unaffected; (b) well below the H-12 1.5MB hard truncation guard already present in `query_signals.ts`,
so it only engages the "large payload" path for genuinely large responses, not routine ones.

**reversibility:** reversible — a pure serving-layer constant; no envelope shape change, no persisted
state. A later wave can retune the threshold or drop the pointer-string convention without redoing any
other shipped work.

---

No further entries — this ledger reopens for W0b+ waves.
