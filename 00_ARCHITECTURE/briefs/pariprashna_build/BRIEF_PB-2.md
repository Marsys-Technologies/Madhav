---
artifact: BRIEF_PB-2
type: WAVE BRIEF (two-part: FROZEN + BIND-AT-OPEN) — WRITE WAVE
campaign: PB — Paripraśna Build
wave: PB-2 SMṚTI — the canonical store & memory
version: 1.0
status: FROZEN — opens when PB-1 closes green (or ship-degraded per Pratinidhi MEMO)
authored_by: Claude (Cowork) 2026-07-28
governing: CAMPAIGN_PB_MASTER_BRIEF_v1_0.md (its §2 amends the house protocols; Pratinidhi replaces every human gate)
design_authority: >
  PARIPRASHNA_TARGET_ARCHITECTURE_v0_1.md §11.1–§11.5 (canonical store, summaries,
  D-16 stamp) + design plan v0.3 §8.3–§8.5 (reducer laws) + J6/§5.3 states.
gate: §G — 12 assertions on the DEPLOYED flagged route + final proof + anti-gaming pass
blocks: PB-3 (the ledger's message_part_id FK targets this wave's table) and PB-4.
---

# PB-2 — SMṚTI: the canonical store & memory

## §0 — Objective

Protocol and storage become **one algebra**. Every turn streamed through
`/api/pariprashna` persists as canonical `conversation_messages` +
`message_parts` rows — versioned, kind-typed, model-visibility-flagged — such
that replaying the recorded event stream through PB-1's reducer reproduces
the persisted parts **byte-for-byte**. On that substrate: durable summaries
surviving restart and preserving citations; pgvector recall across a chart's
threads; `Last-Event-ID` resume making mid-stream server death a non-event;
the D-16 per-turn provenance stamp, written always, audit-drawer-only.

Scope boundaries: the MCP channel gets none of this (D-05); consult stays
UNTOUCHED (PC-3), keeping the legacy `parts_json` path until PB-4. Arch
§11.1's three named defects (SDK-pinned blob, context/UI conflation,
DB-opaque parts) are deleted — new route only.

## §1 — Lifecycle, state, git

Per master brief §1/§4. Branch `pb/2/<lane>`, worktree `Madhav-pb-2-<lane>`,
state shards `briefs/pariprashna_build/state/PB2_LANE_<lane>.md`, index
`STATE_PB-2.md`, commits `chore(pb-2/<lane>): … [PB-BOT]` at every transition.
Verification law per master §2.2, verbatim — no lane is done without its
fresh-context Verifier's (opus/high) ACCEPT receipt. **Migration guard
(opus/high) is a standing seat**: every migration additive-only with its own
ACCEPT; destructive = Pratinidhi-level with a written rollback path (§4).

## FROZEN §F1 — Lane map

### Lane M-1 — canonical schema ⭐ MERGES FIRST (the substrate)
**Implementer opus/high (master §3 pre-authorization) · Verifier opus/high · Migration guard opus/high**

- Green-field canonical shape per arch §11.1 target, additive migrations
  only: `conversation_messages` gains `schema_version int NOT NULL` (OUR
  format's version, from row one — no legacy corpus on the new route),
  `model_id`, `provider`, `metadata_json`; new `message_parts` (`id,
  message_id FK, seq int, kind NOT NULL, body jsonb NOT NULL, model_visible
  boolean NOT NULL`).
- `kind` is a CLOSED enum: `text | reasoning | tool_call | tool_result |
  citation | prediction_candidate | attachment` (DB CHECK + shared Zod).
- `tool_call.body = {call_id, tool_name (canonical), args, envelope_ref?}` —
  **never a provider function-call frame**; `reasoning.body = {text,
  signature?, provider_opaque?}`, opaque blobs storable, never replayed
  cross-provider; telemetry-only parts `model_visible: false` or unpersisted.
- DAL in `platform/src/lib/pariprashna/store/` (new): typed writers/readers
  + the **canonical serialization** (stable key order, seq-ordered parts)
  shared by M-2's byte-equality and every future consumer. One serializer.
- Legacy `parts_json` column and rows: RETAINED, untouched, unread (W-1).

**Acceptance:** migrations apply + roll back on a copy; Migration-guard ACCEPT
per file; DAL round-trips every kind; serializer identity property-tested.
```
may_touch: platform/migrations/** · supabase/migrations/** (additive only) ·
           platform/src/lib/pariprashna/store/** (new) ·
           briefs/pariprashna_build/**
```

### Lane M-2 — protocol↔storage same-algebra (sonnet/med; conductor may dial up)

- PB-1 S-1's `turn.commit` handler now writes canonical parts via M-1's DAL,
  transactionally (message row + all parts at commit); citations persist as
  `citation` parts, prediction candidates as `prediction_candidate` parts
  (state `detected` — PB-3 consumes); the existing-write-path call on this
  route is REMOVED.
- Upgrade PB-1 C-2's golden protocol scaffold to the **byte-equality gate**:
  recorded event stream → reducer → M-1 canonical serialization ≡ persisted
  parts' canonical serialization, byte-for-byte, per fixture AND against one
  real deployed reading — the wave's [integrity] centerpiece. Reducer↔writer
  divergence is a halt-worthy bug in one of them, never a test to loosen (W-2).

**Acceptance:** byte-equality green across the C-2 corpus; verifier reruns it
and independently diffs one real reading's DB rows against its stream.
```
may_touch: platform/src/app/api/pariprashna/** (persistence seam only) ·
           platform/src/lib/pariprashna/store/** ·
           platform/tests/pariprashna/** · briefs/pariprashna_build/**
```

### Lane M-3 — durable summaries (sonnet/med)

Replace arch §11.3's four-failure implementation (multipart-blind,
provider-pinned, `Map`-cached, cache-hostile), for the new route:
- `conversation_summaries` table (additive): `conversation_id`,
  `covers_through_message_id`, `summary_text`, `model_id`, `created_at` —
  written once per threshold crossing, reused across processes.
- Summarizer behind a family-worker interface (W-4); **canonical-store-aware**
  (tool parts render as "consulted ⟨reader label⟩ → ⟨envelope verdict line⟩",
  never `'[multipart content]'`); **citation-preserving** (fact_ids in
  summarized turns survive verbatim — the grounding gate's refs must not
  dangle); **prefix-stable splice** (summary occupies a fixed structural slot
  so the prompt prefix and its cache survive turn N→N+1).

**Acceptance:** restart reuses the row (zero re-summarize); fact_id-survival
and prefix-hash-stability fixtures green.
```
may_touch: platform/src/lib/pariprashna/summaries/** (new) ·
           platform/src/app/api/pariprashna/** (splice point only) ·
           platform/migrations/** · supabase/migrations/** (additive) ·
           platform/tests/pariprashna/** · briefs/pariprashna_build/**
```

### Lane M-4 — pgvector recall (sonnet/med; fan-out haiku/low)

- Extend `platform/scripts/backfill_conversation_embeddings.ts` to embed
  canonical `message_parts` text (a deterministic transform — §N.4);
  batch/offline only, never inline in the serve path (W-5).
- Per-chart recall ACROSS threads (arch §11.5), feeding the route's context
  assembly, ranked by recency + provenance freshness.
- **`prior_reading` citation kind** (arch §11.5, binding): a recalled
  conclusion carries its own grade, explicitly weaker than `verified`, and
  **never satisfies an acharya-floor requirement** — floor-rejection test
  proves it (the B.1-by-the-back-door defense).

**Acceptance:** cross-thread recall fixture ("what did we conclude about X?")
returns the prior thread's conclusion; the floor-rejection test is green.
```
may_touch: platform/scripts/backfill_conversation_embeddings.ts ·
           platform/src/lib/pariprashna/recall/** (new) · platform/migrations/**
           · supabase/migrations/** (additive) ·
           platform/tests/pariprashna/** · briefs/pariprashna_build/**
```

### Lane M-5 — resume: Last-Event-ID over a ring buffer (sonnet/med; conductor may dial up)

- Server retains each active turn's event log in a ring buffer keyed by
  turn_id (shared store if multi-instance — W-3); SSE events carry monotone
  ids; `Last-Event-ID` reconnect replays from seq; client discards
  already-applied seqs idempotently (reducer law, PB-1 C-2 scaffold).
- **Snapshot fallback with disclosure:** buffer evicted the needed seq →
  serve the committed-state snapshot, flagged `flag{resumed_via_snapshot}`,
  applied in one write, no replay animation (§5.7) — never silent loss,
  never a duplicate block.
- `visibilitychange` reconnect: a backgrounded tab returning mid-turn takes
  the same resume path (§9.2).
- **Half-committed turns:** server death past the grace window → turn
  `interrupted` per J6/§5.3 (tail kept, calm line, Continue) and **excluded
  from prediction detection** — a truncated claim never seeds the ledger.

**Acceptance:** C-2 disconnect fixtures + new `server-kill-mid-turn` /
`buffer-evicted` / `tab-background-return` green on the DEPLOYED route.
```
may_touch: platform/src/app/api/pariprashna/** · platform/src/lib/pariprashna/
           protocol/** · platform/src/components/pariprashna/** (reconnect
           surfaces only) · platform/tests/pariprashna/** · briefs/pariprashna_build/**
```

### Lane M-6 — provenance stamp, D-16 (sonnet/med)

- Every assistant turn writes the stamp into
  `conversation_messages.metadata_json`: `build_id · priors_version ·
  formula_versions · ranking_config · now_context_date` — provenance comes
  OUT with the answer, never an engine input (D-16, arch §11.4).
- **Drift = consecutive-turn comparison** (this stamp vs the previous turn's,
  no shared session state); on mismatch emit the §7.8 edge-state row
  `THE CHART HAS BEEN REBUILT — RE-READING` (lexicon landed in PB-1 S-2).
- **Surfacing: audit drawer ONLY** — ruling 8c amends arch §11.4's header
  rendering: provenance ambient NOWHERE (not header, not dock footer); zero
  streamed non-audit bytes (gate 11). PB-3 consumes: the stamp is COPIED into
  ledger rows, never referenced (D-16(d)); M-6 exposes the read API for that
  copy, writes no ledger.

**Acceptance:** stamp on every new-route assistant turn; drift fixture renders
the edge-state row; wire-tap: zero stamp fields outside the audit drawer.
```
may_touch: platform/src/lib/pariprashna/provenance/** (new) ·
           platform/src/app/api/pariprashna/** (stamp write) · platform/src/
           components/pariprashna/** (audit drawer only) ·
           platform/tests/pariprashna/** · briefs/pariprashna_build/**
```

### Lane Z-2 — synthesis & close (opus/high)
`REPORT_PB-2.md`; arch §11 annotated AS-BUILT (deltas Pratinidhi-memo'd);
SESSION_LOG append; STATE finalized; migration + rollback inventory recorded.

### §F1.9 — DAG
```
        M-1 (schema first — the substrate)
          │
   ┌──────┼──────┬──────┬──────┐
   M-2   M-3    M-4    M-5    M-6   (parallel; M-2 merges before M-5/M-6,
   └──────┼──────┴──────┴──────┘     which rebase — three lanes touch the
          ▼                          route file; conductor integrates in order)
      INTEGRATE → DEPLOY (flagged) → §G GATE → Z-2
```

## FROZEN §F2 — must_not_touch
```
platform/src/app/api/chat/** (consult UNTOUCHED — PC-3) ·
platform/src/components/consume/** · platform/src/components/chat*/** ·
platform-mcp/** (D-05: no MCP transcript; the root dispatcher NEVER) ·
the legacy parts_json path serving consult (kept until PB-4) · destructive
migrations of ANY kind · 00_ARCHITECTURE/llm_consumption_audit/** ·
CLAUDECODE_BRIEF.md · CLAUDE.md · the sealed pg1/pg2 trees
```

## §B — BIND-AT-OPEN
B-1 origin/main fetched+pinned; rollback image pinned. B-2 PB-1 gate receipts
confirmed green on the deployed flagged route. B-3 worktree isolation
verified. B-4 live `conversation_messages` snapshot recorded (columns, row
count, which rows are legacy `parts_json`) — the green-field claim re-verified
against reality. B-5 C-2 golden scaffold + fixture hashes pinned. B-6 deploy
topology recorded (instance count → W-3 buffer placement); retention window
proposed, Pratinidhi sizes it.

## §5 — Wave rulings (beyond master PCs)
| # | Fork | Ruling |
|---|---|---|
| W-1 | Legacy `parts_json` rows exist at open (PF-1 smoke, PB-1 readings) | Green-field applies to the NEW shape only. Legacy rows retained untouched and unread by the new path; no speculative backfill — Pratinidhi may schedule one later, MEMO'd. |
| W-2 | Byte-equality fails on semantically-equal serialization differences | The canonical serializer (M-1) is defined BEFORE the gate and shared by writer and test. After that, any mismatch is a bug in writer or reducer — fix the code, never loosen to deep-equal. Re-baselining this assertion is forbidden (master §2.1.4). |
| W-3 | Multi-instance deploy breaks in-process ring buffer | Buffer moves to a shared store keyed by turn_id; snapshot fallback is the designed degradation. Silent loss is never an option. Pratinidhi rules placement if infra cost is contested. |
| W-4 | No ModelPlane family-worker exists yet | M-3 ships the family-worker INTERFACE with one provider behind it; call sites depend on the interface only. Never a hardcoded provider at a call site; never block the wave on model-plane buildout (scope boundary). |
| W-5 | Embedding backfill is slow/costly | Batch offline, bounded; never in the serve path. Partial backfill is acceptable at gate if the recall fixture's corpus is covered — record coverage honestly. |

## §G — Gate (post-deploy, flagged route; fresh opus gate-runner + anti-gaming)
1 golden byte-equality: replay→reducer ≡ persisted parts, canonical
serialization, full fixture corpus AND one real deployed reading [integrity] ·
2 schema conformance on real rows: `schema_version` NOT NULL, closed `kind`
enum, `model_visible` NOT NULL, `tool_call.body` canonical name — zero
provider frames [integrity] · 3 zero UIMessage/`parts_json` writes on the new
route (write-path grep + DB assertion; legacy column untouched) [integrity] ·
4 every migration additive-only with Migration-guard ACCEPT [integrity] ·
5 disconnect/resume battery green on the DEPLOYED route: 10s drop non-event;
replay-from-seq idempotent (zero duplicate blocks); buffer-evicted → snapshot
fallback with disclosure flag per J6 · 6 `visibilitychange` reconnect green
at mobile viewport · 7 half-committed turn marked `interrupted`, provably
excluded from prediction detection · 8 summaries: threshold writes the row;
restart reuses it; splice prefix-stable (prefix hash unchanged) · 9
summarized-turn fact_ids survive verbatim · 10 cross-thread recall green;
`prior_reading` never satisfies an acharya floor (rejection test) · 11 stamp
on every assistant turn; drift fixture renders the edge-state row; stamp
fields in ZERO streamed non-audit bytes (wire-tap) [integrity] · 12 consult
route byte-identical to base pin [integrity].
**Final proof:** kill the server mid-turn on the DEPLOYED flagged route;
reconnect resumes with zero loss; at settle the persisted parts byte-equal
the replayed reducer state. **One byte of disagreement, no wave.**
Anti-gaming charge: find the byte-equality run only against fixtures, never
the deployed reading's DB rows — or the kill-test run against local dev.

## §C — Close
REPORT_PB-2.md sealed; memo index appended; worktrees cleaned; campaign
advances to PB-3 (which binds its `message_part_id` FK to this wave's table).

*End BRIEF_PB-2 v1.0.*
