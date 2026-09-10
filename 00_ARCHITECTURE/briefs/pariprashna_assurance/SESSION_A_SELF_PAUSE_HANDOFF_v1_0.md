---
artifact: PARIPRASHNA_SESSION_A_SELF_PAUSE_HANDOFF
version: 1.0
status: OPEN — self-paused at A0, before plan revision 3
date: 2026-08-27
session: Paripraśna Experience Assurance v3, Session A (autonomous pre-stream session)
worktree: .clone/worktrees/pariprashna-session-a
branch: campaign/pariprashna-v3-session-a
baseline: a48263ee7 (origin/main, 1 commit behind at pause time)
tracker_event: ledger_seq 20, event_id d7eeee05-11c9-4b69-ae45-efdd8e4d84a9,
  actor surrogate-p0b, event_type decision_recorded, tag "SURROGATE DECISION —
  not native acceptance", idempotency_key
  session-a-2026-08-27-a0-irreducible-blocker-tracker-p2-mode-v1
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/control.py
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/tracker/server.py
---

# Session A — self-pause handoff at A0 v1.0

## What A0 verified before the pause

- Worktree `.clone/worktrees/pariprashna-session-a` exists, is on
  `campaign/pariprashna-v3-session-a`, cut from `a48263ee7`, clean, 1 commit
  behind `origin/main` (no drift, no uncommitted state at open).
- AGENTS.md and CLAUDE.md handshake read.
- `AUTONOMOUS_EXECUTION_ELEVATION_v1_0.md`, `PARIPRASHNA_EXPERIENCE_ASSURANCE_TEST_PLAN_v2_1.md`,
  `P2_BLOCKER_INTAKE_v1_0.md`, `P1_CLOSURE_PACKET_v1_0.md` read in full.
- Live state re-derived:
  - Shadow elevation (`127.0.0.1:8788/api/elevation`): `plan_revision: 3`, all
    five sources FRESH.
  - Accepted tracker (`127.0.0.1:8787/api/projection`): `completion_pct: 13.0`;
    P0→P1 and P1→P2 dependencies RESOLVED; P2→P3 through P6→P7 PENDING; zero
    `decisions` before this session; the only `execution_sessions` entry is
    the historical P1 takeover session — **no P2/Session-A execution session
    exists yet**.
  - launchd `com.marsys.pariprashna-assurance-control` is loaded and running
    (pid present, last exit status 0).
  - No `EDIR_V3_REGISTER_v1_0.md` in this folder — A3 has not started.
  - No local commits ahead of `origin/main` on this branch — no prior-resume
    WIP exists to build on or lose.
  - Only two open Paripraśna-related PRs repo-wide: #1513
    (`dd-credential-misdiagnosis`, docs-only, EVIDENCE-ONLY class per
    elevation §6.2) and #1500/#1496 (`p4-g`/`p4-h`, both PARKED in their own
    titles). Neither is this session's work; nothing is mid-merge.

## The blocker this session found (and why it stops A0 cold)

The elevation's precondition (§5.1/§7) only covers the **shadow observation
worker** (`127.0.0.1:8788`, `elevation_worker.py`) staying fresh without
manual refresh — confirmed satisfied (`plan_revision: 3`, all sources FRESH).
It says nothing about whether the **accepted event-sourced control plane**
(`127.0.0.1:8787`) can actually accept P2-scope (or any general-mode) events.
It cannot, today:

- The live service's launchd `ProgramArguments` run it with `--p0b-only
  --p1-enabled` (`~/Library/LaunchAgents/com.marsys.pariprashna-assurance-control.plist`).
- Its `actors` table holds only P0-scoped identities
  (`lead-p0b`/`surrogate-p0b`/`verifier-p0b`/`integrator-p0b`, each owning
  only stream `P0`); its `p1_actors` table holds only P1-scoped identities
  (`lead-p1`/`surrogate-p1`/`verifier-p1`/`integrator-p1`, each owning only
  `P1`). **No actor owns `P2` or any general-mode stream** (`P3`–`P7`,
  `S1`–`S6`), because `EventStore._seed_actors` only creates that set
  (`lead-p2`…`lead-p7`, `lead-s1`…`lead-s6`, `surrogate`, `verifier`,
  `integrator`, `native`) when constructed with `p0b_only=False` — and
  `EventStore.__init__` itself raises `P1_ENABLEMENT_MODE` if
  `p1_enabled and not p0b_only`, so the live binary cannot hold both
  `p1_enabled` and the general actor set at once.
- Verified non-destructively: copied the live `control-plane.sqlite3` to a
  scratch directory and constructed a fresh `EventStore(p0b_only=False,
  p1_enabled=False)` against the copy only. It failed immediately with
  `DEFINITION_INTEGRITY` — `programme_definition()`'s `operator_mode`
  (`"GENERAL"` vs `"P0B_ONLY"`) is baked into the definition the ledger's
  `ledger_meta` row is bound to at `init()`, so simply relaunching the
  existing runtime directory with different flags is rejected, not silently
  accepted. (The live runtime itself was never touched by this probe.)
- `control.py`/`server.py`/`cli.py` contain no `p2_actors` table, no
  `P2_ENABLED`/`p2-enabled` flag, and no code path that seeds P2+ actors or
  authorizes a P2/general-mode transition while preserving the existing P0/P1
  ledger. `ADR_P0_TRACKER_ARCHITECTURE_v1_0.md` and
  `STATE_TRANSITIONS_v1_0.md` do not document one either.

In short: **the P1→P2 enablement precedent that unlocked P1 work was never
built for P2.** Every Session A phase from A0 onward needs to submit real
events — plan revision 3, `work_started` on P2, blocker acceptances, CG-2
closure, charter registration — as an actor that owns `P2`/general streams.
No such actor is authenticated, or authenticatable, against the live control
plane today.

## Why this is a self-pause, not an in-session fix

Adding a genuine P2-enablement mode (mirroring `P1_ENABLEMENT_MODE` /
`p1_actors`) is a safety-critical change to the ledger's own authorization
logic — the same class of change the P1 precondition took its own dedicated
session to design, test (failing test first), land (protected PR → CI →
merge), and prove (attested release, restart, freshness/parity re-proof)
before anything trusted it. Doing that inline, under an 8h ceiling that also
carries P2 blocker clearance (two live auth/RLS exposure fixes among them)
and a ~70-branch absorption census, is not a responsible improvisation.
Writing events by hand to the SQLite file, or otherwise bypassing the
authenticated/append-only path, would break the exact guarantee this system
exists to provide — the one thing this session was warned against most
explicitly at open.

## Exact resume point

**A0 is not complete.** No tracker plan revision 3 is registered. The one
tracker event this session emitted is the `decision_recorded` self-pause
note above (actor `surrogate-p0b`, no `stream_id`, since no P2-scoped actor
exists to do more). Nothing else was written to the tracker, no branch was
merged, no PR was opened, no code outside this handoff file and the
governing docs was touched.

**Before any resumption of A2–A6:** a dedicated precondition-style session
(same shape as the tracker-elevation precondition that ran before this one)
must design, implement, test, and deploy a genuine P2/general-mode
enablement path for `tracker/control.py` + `tracker/server.py`, land it via
the same protected-merge discipline, restart the live service, and hand this
session (or its resumption) verified exit evidence: a PR merge SHA, restarted
service confirmation, and live proof that a general-mode actor (e.g.
`lead-p2` or `surrogate`/`verifier`/`integrator`) now exists and
authenticates. Only then can A0 register plan revision 3 and this session
proceed into A2 (credential lane), A3 (absorption census), A4 (P2 blocker
clearance), A5 (CG-2 + charters), A6 (stream prompts).

This prompt (the Session A kickoff prompt, elevation §11.3) can be re-pasted
into a fresh session once that precondition closes — it will re-derive this
same state, see the new precondition's evidence, and continue from A0
exactly where this one stopped.
