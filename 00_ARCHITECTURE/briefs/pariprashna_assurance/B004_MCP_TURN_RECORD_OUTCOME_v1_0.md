---
artifact: B-004 MCP turn record outcome (P2-B-004 / E-119)
version: "1.0"
status: RESOLVED_EXPLICIT_BOUNDED_LIMITATION
as_of: "2026-08-28T00:40:00Z"
session: "Claude Code session, P2 blocker B-004 fix (test-driven, isolated worktree)"
relates_to:
  - 00_ARCHITECTURE/briefs/pariprashna_assurance/P2_BLOCKER_INTAKE_v1_0.md (P2-B-004 row)
  - platform/src/app/api/mcp/prashna_ask/route.ts
  - platform/src/lib/pariprashna/protocol/stream_capture.ts
  - PR https://github.com/Marsys-Technologies/Madhav/pull/1599
---

# B-004 MCP turn record outcome (P2-B-004 / E-119) v1.0

## Verdict

**Took the "explicit bounded limitation" branch of the P2-B-004 acceptance
criterion, not the "fresh reproducible record" branch.** The MCP door
(`/api/mcp/prashna_ask`) now discloses, on every terminal envelope it emits, an
honest `persistence: { status: 'none', detail: '...' }` field stating that this
door's turns (reading, judgment_flags, completeness) are not durably persisted
anywhere. No new durable-storage mechanism was built.

## The confirmed gap (unchanged from the investigation handed to this session)

`/api/mcp/prashna_ask` assembles a full `readingEnvelope` (`reading`,
`judgment_flags`, `completeness`) around route.ts:721-740 (line numbers as of
this session; the route has since grown by ~48 lines) and streams it as the
NDJSON `final` event. Nothing durable is written for it:

- `platform-mcp/src/lib/job_registry.ts`'s `JobRegistry` is a
  `Map<string, Job>` held **in-memory only** — its own comment: "Jobs are held
  in memory only — they do not survive a process restart." 15-minute TTL,
  actively evicted.
- The one durable row per turn, `pariprashna_safety_decisions` (written by
  `recordDecision`/`appendSafetyDecision` in
  `src/lib/pariprashna/safety/{gate,audit}.ts`), is **pre-dispatch
  classification only** — no `reading`, `judgment_flags`, or `completeness`
  column exists on it.
- No `job_id` column exists in any migration.

## What was assessed: reusing `stream_capture.ts` (the larger path)

`platform/src/lib/pariprashna/protocol/stream_capture.ts` is an already-built,
off-by-default (`PARIPRASHNA_STREAM_CAPTURE`), privacy-safe (no user text, no
`as any`), bounded-retention (14-day default) durable sink, currently wired
into the Portal door (`/api/pariprashna/route.ts` lines ~123/126) via
`beginTurnCapture` → `captureEvent` per emitted event → `endTurnCapture`.

Read in full, plus its Portal integration point and the MCP route in full, the
reuse does **not** reduce to "a few lines calling the existing capture
function":

1. **Type mismatch at the call boundary.** `captureEvent(turnId, event:
   PariprashnaEvent)` requires the strictly Zod-typed, discriminated-union wire
   protocol from `protocol/events.ts` (`turn.open` / `phase` / `block.commit` /
   … , each carrying a monotonic `seq` + timestamp `t`). The MCP door's NDJSON
   lines are a structurally different, untyped shape:
   `{event:'progress'|'final'|'error', ...}` — field name `event` not `type`,
   no `seq`/`t` envelope on any line, and the `final` payload
   (`readingEnvelope` + `results`) has no counterpart anywhere in the
   `PariprashnaEvent` union.
2. **No `conversation_id`.** The MCP door has no multi-turn conversation
   concept at all — it's a single-request-response RPC-style call keyed on
   `trace_id`/`queryId`, not a chat turn keyed on `(conversation_id, turn_id)`.
   `stream_capture.ts`'s table schema and `beginTurnCapture` signature both
   require it.
3. **Downstream semantics don't transfer.** The tooling this table exists to
   feed (BRIEF_PB-2 §G-1's byte-equality gate) replays a captured event stream
   against the SAME turn's persisted `message_parts` row to prove wire-vs-DB
   byte-equality. The MCP door never writes `message_parts` at all — there is
   nothing on the other side of that equality check for an MCP turn.

Forcing a fit would mean inventing synthetic events (and likely widening the
`PariprashnaEvent` union or bypassing its Zod validation with a cast) to shoehorn
a one-shot RPC call into a chat-turn capture mechanism built for a different
shape of interaction — a new capture mechanism wearing an old one's name, not
reuse. Per the task's own decision framework ("do not force it" if the larger
path requires substantial new infrastructure), this was not pursued further as
working code.

## What was implemented (the smaller path)

`platform/src/app/api/mcp/prashna_ask/route.ts`: a new module-level constant
`MCP_TURN_PERSISTENCE_NONE` (`{ status: 'none', detail: '<full honest
explanation, see route.ts>' }`), documented with a doc comment recording the
`stream_capture.ts` assessment above so a future session doesn't have to
re-derive it. Wired onto all three terminal envelopes this route can emit that
carry a `reading`:

- the HS-2/seal-pending `safety_withheld` early return (pre-planner),
- the plan-time-escalated `safety_withheld` return (post-planner),
- the `final` `readingEnvelope` (the one named directly in the finding).

This follows CLAUDE.md §N.7 item 6 ("an honest null beats an invented
judgment") and §N.8 (a status must be backed by a real detector or be null) —
`status: 'none'` is a true, checkable statement about what the code currently
does, not a promise about what it might do later.

## Demonstrated-can-fail proof (TDD)

Added two tests to the existing
`platform/src/app/api/mcp/prashna_ask/__tests__/route.test.ts` BEFORE the fix,
confirmed failing against pre-fix `route.ts`:

```
FAIL … discloses persistence:none on the final reading envelope — this door writes no durable record of the turn
  AssertionError: expected undefined to be defined
    ❯ expect(body.persistence).toBeDefined()

FAIL … discloses persistence:none on the HS-2 hard-stop safety_withheld envelope too
  AssertionError: expected undefined to be defined
    ❯ expect(body.persistence).toBeDefined()
```

After the fix: both pass, the full `route.test.ts` suite passes 33/33, and the
broader regression run

```
npx vitest run src/lib/pariprashna src/app/api/pariprashna src/app/api/mcp/prashna_ask
→ Test Files  96 passed | 8 skipped (104)
  Tests  1505 passed | 69 skipped | 1 todo (1575)
```

is green. `eslint` on both touched files is clean. `tsc --noEmit` shows zero
errors attributable to the touched file (this fresh worktree's `pnpm install
--frozen-lockfile` has pre-existing, unrelated missing-module errors —
`uuid`, `json-schema`, `ajv-formats` — in files this change never touches).

## Where the work happened

Isolated worktree `.clone/worktrees/pariprashna-b004-fix`, branch
`pariprashna/p2-b004-mcp-turn-record`, created fresh off `origin/main`
(`cc6b1a55e`). Never touched the shared checkout or any other worktree.

## PR

**https://github.com/Marsys-Technologies/Madhav/pull/1599** — open, not
merged. Explicitly requests independent verification before merge, naming
three things a reviewer should double-check:

1. Whether the "stream_capture reuse doesn't fit" structural assessment above
   holds up (no working prototype of the larger path was attempted, only the
   shape comparison).
2. Whether the `persistence` field belongs on the two `safety_withheld`
   envelopes too (added for consistency — they're also completed "reading"
   turns with the same gap) or is out of the finding's literal scope (which
   names only the final `readingEnvelope`).
3. Whether this satisfies P2-B-004/E-119's acceptance bar as the native or an
   independent verifier reads it — this session worked from the investigation
   summary and the one-line acceptance criterion in `P2_BLOCKER_INTAKE_v1_0.md`
   ("Fresh reproducible record, or an explicit bounded limitation"), not a
   longer original finding text.

## Disposition

P2-B-004 intake row's acceptance criterion offers two branches; this PR
satisfies the second ("an explicit bounded limitation") pending independent
review and merge. The row should not be marked closed until that review lands
and the PR merges — this document records what was done and why, not a
unilateral closure.
