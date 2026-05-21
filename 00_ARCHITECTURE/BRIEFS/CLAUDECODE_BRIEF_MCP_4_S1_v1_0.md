---
artifact: CLAUDECODE_BRIEF_MCP_4_S1_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: PENDING
authored_by: Claude Code sub-agent (MCP-0-AUTHOR)
authored_at: 2026-05-21
session_id: MCP-4-S1
session_name: MCP-4-S1 — Writes (log_prediction, record_outcome, flag_disagreement) + PPL interim path
executor: Claude Code sub-agent (general-purpose, spawned by MCP Conductor)
execution_mode: single autonomous session, --dangerously-skip-permissions
worktree:
  name: MadhavMCP
  branch: feature/mcp-server
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/MadhavMCP
governing_plan: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
reference_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md
predecessor_session: MCP-3-S2 (read_asset + observability + rate limiting)
next_session_anticipated: MCP-4-S2 (red-team pass)
---

# CLAUDECODE_BRIEF — MCP-4-S1
## Writes: log_prediction, record_outcome, flag_disagreement + PPL interim path

---

## §0 — How to start this session

You are a sub-agent spawned by the MCP Conductor. Your context is fresh.
You are in the MadhavMCP worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavMCP`
on branch `feature/mcp-server`. The Conductor has already pasted your
session prompt; you are now reading this brief.

This session ships Phase MCP-4 implementation: the **write tools** that
allow Claude (as an MCP client) to log predictions, record outcomes, and
flag disagreements. These are governance-critical tools — they feed the
Prospective Prediction Log (PPL) substrate and the DISAGREEMENT_REGISTER.

**PPL substrate status:** The formal `06_LEARNING_LAYER/` PPL scaffold is
not yet in place (per CLAUDE.md §E — it arrives later in the M-arc). The
interim path is the `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` prediction
subsection, per CLAUDE.md §E "sessions that emit time-indexed predictions
before Step 11 closes must still log them." This session documents the
interim path in code (TODO migration comment) and writes to it via a
careful append-only mechanism.

**Writes are the most sensitive category.** Every write carries full
provenance: `caller_session_id` (from the host chat), `key_id`, `trace_id`,
and `timestamp`. The `flag_disagreement` tool writes to
`DISAGREEMENT_REGISTER_v1_0.md`, which is a LIVING governance artifact.

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | MCP-4-S1 |
| Branch | `feature/mcp-server` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/MadhavMCP` |
| Execution mode | Single autonomous session, `--dangerously-skip-permissions` |
| Predecessor | MCP-3-S2 (all 16 read tools + rate limiting complete) |
| Anticipated next | MCP-4-S2 (red-team pass) |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read, especially §E Prospective
   Prediction Logging workstream + §E Concurrent workstreams)
2. `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md` — **focus on §4.1 (Phase
   MCP-4 write tools), §6 G4 (PPL discipline), §7.4 (Phase MCP-4
   acceptance criteria), §8 R9 (PPL substrate ambiguity)**
3. `01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md` — **read the prediction
   subsection format** (identify if one exists; if not, identify the
   section structure so you can append correctly without corrupting existing
   content). This is L1 data — you READ it but write ONLY to the prediction
   subsection via the `ppl_writer.ts` module.
4. `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` — read the LIVING
   document's current format; `flag_disagreement` must append in the same
   schema.
5. `platform/src/app/api/mcp/execute/route.ts` — understand where
   `predictions_logged[]` is currently assembled (empty array in MCP-1-S1);
   you will wire `ppl_writer.ts` here to populate it.
6. `platform/src/lib/mcp/auth.ts` — refresh on `key_id` field; writes
   carry it as provenance.

---

## §3 — Scope (6 items — execute in order; commit after each)

### Item 1 — PPL writer (`platform/src/lib/mcp/ppl_writer.ts`)

**What:** Author `platform/src/lib/mcp/ppl_writer.ts` that handles the
interim Prospective Prediction Log path.

```typescript
export interface PredictionEntry {
  prediction_id: string;           // generated: "PPL.MCP." + nanoid(8)
  logged_at: string;               // ISO timestamp
  horizon: string;                 // e.g. "2026-Q3" or "2026-09-30"
  domain: string;                  // e.g. "career", "health", "spiritual"
  prediction_text: string;         // the prediction in prose
  confidence: 'high' | 'medium' | 'low';
  falsifier: string;               // what observation would disprove it
  source: {
    key_id: string;
    trace_id: string | null;
    caller_context: string | null; // caller-provided context label
  };
}

export interface OutcomeEntry {
  prediction_id: string;           // links to a prior PredictionEntry
  recorded_at: string;
  outcome_text: string;
  verified: boolean;               // did the prediction come true?
  notes: string | null;
  source: { key_id: string; trace_id: string | null };
}

// Appends to the ## MCP Predictions subsection of LIFE_EVENT_LOG_v1_2.md
// If the subsection doesn't exist, creates it with a header comment.
// Returns the prediction_id.
export async function logPrediction(entry: PredictionEntry): Promise<string>

// Appends outcome under the matching prediction_id entry.
// Returns ok: true if the prediction_id was found; ok: false if not.
export async function recordOutcome(entry: OutcomeEntry): Promise<{ok: boolean}>
```

**Implementation notes:**
- The writer reads the LEL file, appends to a `## MCP Predictions` section
  (creating it if absent, placed at the end of the file before any closing
  separator), and writes back. This is file-system-level; no DB write.
- Each `PredictionEntry` is serialized as a YAML block inside a fenced
  code block under the predictions section, clearly separated by dividers.
- Each `OutcomeEntry` is serialized as a sub-entry under its `prediction_id`.
- Include a prominent `// TODO(MCP-MIGRATION): when 06_LEARNING_LAYER/ is
  scaffolded, migrate this writer to the formal PPL substrate. Migration
  path: read all entries from this section, POST to the new PPL API.`
  comment at the top of the file.

**AC.MCP_4_S1.1:** `ppl_writer.ts` exists; both `logPrediction` and
`recordOutcome` exported; includes migration TODO comment; the LEL
prediction section format is documented in a JSDoc comment; TypeScript
strict passes.

**Why:** PPL discipline (G4 per MCP_BRIEF §6) requires that prospective
predictions are logged BEFORE outcomes are observed. This interim writer
satisfies the governance requirement while the formal substrate is built.
Per CLAUDE.md §E: "Every time-indexed prediction a session emits is logged
with its confidence, horizon, and falsifier before the outcome is observed."

Commit: `feat(mcp): MCP-4-S1 item 1 — ppl_writer.ts (interim LEL prediction path)`

---

### Item 2 — Writes dispatcher (`platform/src/app/api/mcp/writes/[action]/route.ts`)

**What:** Author `platform/src/app/api/mcp/writes/[action]/route.ts` — a
POST handler dispatcher for `log_prediction`, `record_outcome`, and
`flag_disagreement`:

1. Validate service-to-service token + MCP headers (same pattern as other
   `/api/mcp/*` routes).
2. Read `params.action` from URL segment.
3. Validate `action` against `['log_prediction', 'record_outcome',
   'flag_disagreement']`; reject others with 400.
4. Route to the appropriate handler:
   - `log_prediction` → call `logPrediction(body.entry)`, return
     `{ok: true, result: {prediction_id}}`.
   - `record_outcome` → call `recordOutcome(body.entry)`, return
     `{ok: result.ok, result: {linked_to: body.entry.prediction_id}}`.
   - `flag_disagreement` → call the disagreement writer (Item 3), return
     `{ok: true, result: {disagreement_id}}`.
5. All write operations wrap in try/catch; errors return
   `buildErrorEnvelope({error_class: "orchestrator_error"})`.

Add rate limiter call (same as existing endpoints) to protect against
spam writes.

**AC.MCP_4_S1.2:** Dispatcher file exists; all 3 actions routable; rate
limiter called; unknown actions return 400; TypeScript strict passes.

**Why:** A dispatcher pattern (like the primitives dispatcher from MCP-3-S1)
consolidates auth + rate-limit checks into one file. Simpler than 3 separate
route files.

Commit: `feat(mcp): MCP-4-S1 item 2 — /api/mcp/writes/[action] dispatcher`

---

### Item 3 — Disagreement writer (inline in dispatcher or separate lib file)

**What:** Author the disagreement-writing logic, either as a function in
the dispatcher or as `platform/src/lib/mcp/disagreement_writer.ts`:

```typescript
export interface DisagreementEntry {
  disagreement_id: string;        // "DIS.MCP." + nanoid(8)
  class: 'factual' | 'interpretive' | 'structural' | 'mirror_desync' | 'scope';
  description: string;
  source_session: string;         // caller-provided session label
  proposed_resolution: string | null;
  source: { key_id: string; trace_id: string | null };
  logged_at: string;
}

export async function flagDisagreement(entry: DisagreementEntry): Promise<string>
// Returns disagreement_id; appends to DISAGREEMENT_REGISTER_v1_0.md
// in the same YAML schema as existing entries.
```

**Implementation:** Read `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md`,
append the entry in the document's existing format (inspect the LIVING
document to match the schema exactly — it has `canonical_id`, `class`,
`status`, `logged_at`, etc. entries). Write back. Include the same
`// TODO(MCP-MIGRATION)` comment noting that the disagreement register is
LIVING and these entries survive permanently.

**AC.MCP_4_S1.3:** `flagDisagreement` function exists and appends to the
DISAGREEMENT_REGISTER in the correct schema; disagreement_id follows the
`DIS.MCP.NNNN` format; TypeScript strict passes.

**Why:** Per CLAUDE.md §K, the DISAGREEMENT_REGISTER is a governance
surface for inter-agent conflicts. Allowing Claude (as MCP client) to
write to it creates a formal channel for Cowork sessions to surface
disagreements to the native without out-of-band communication.

Commit: `feat(mcp): MCP-4-S1 item 3 — disagreement_writer.ts (DISAGREEMENT_REGISTER append)`

---

### Item 4 — MCP tool wrappers for 3 write tools

**What:** Author three files in `platform-mcp/src/tools/`:

**`log_prediction.ts`** — §4.6-standard description (≥100 words):
```
What it does: Logs a prospective prediction to the MARSYS-JIS Prospective
Prediction Log (PPL). Must be called BEFORE the predicted outcome is
observed — PPL discipline requires predictions are logged with falsifier
and horizon before any outcome data is available.

When to prefer: Use whenever you are making a time-indexed, testable
astrological prediction in a session. This is a governance obligation, not
optional — any predictive ask_madhav call with mode="predictive" triggers
this automatically, but you can also call it directly.

Input shape hints: domain — one of ["career", "health", "relationships",
"spiritual", "finance", "relocation", "family"]. horizon — ISO date or
quarter string (e.g. "2026-Q3" or "2026-09-30"). falsifier — what specific
observation would falsify this prediction. confidence — "high", "medium",
or "low".

Output shape preview: {ok, result: {prediction_id: "PPL.MCP.XXXXXXXX"},
trace_id, epistemics}.

Example: log_prediction({domain: "career", horizon: "2026-Q3", prediction_text:
"Native transitions to a leadership role in current company", confidence: "medium",
falsifier: "No promotion or role change by 2026-09-30"}).
```

Input schema: `{ domain, horizon, prediction_text, confidence, falsifier, caller_context? }`

**`record_outcome.ts`** — §4.6-standard description (≥100 words):
Focus on: links to a prior `prediction_id`; call only after outcome is
observable; the `verified` field is factual — not an interpretation.

Input schema: `{ prediction_id, outcome_text, verified: boolean, notes? }`

**`flag_disagreement.ts`** — §4.6-standard description (≥100 words):
Focus on: use when you detect a contradiction between MSR signals, between
MARSYS output and your own assessment, or when this MARSYS session's output
conflicts with a prior session's finding. This is a formal governance
channel; the native reviews entries in the DISAGREEMENT_REGISTER.

Input schema: `{ class, description, source_session, proposed_resolution? }`

Each wrapper calls `callPlatformWrites(action, params, principal)` — add
this helper to `platform-mcp/src/client.ts` (POSTs to `/api/mcp/writes/{action}`).

Update `platform-mcp/src/server.ts` to register all 3 new tools. Total
tool count: 16 read + 3 write = 19.

**AC.MCP_4_S1.4:** All 3 tool files exist with §4.6-standard descriptions;
all 3 registered in `server.ts`; `client.ts` has `callPlatformWrites`
helper; TypeScript strict passes in `platform-mcp/`.

**Why:** Write tools are the PPL-discipline enforcement layer for MCP
callers. Without them, a Cowork session can use `ask_madhav` to produce
predictions without logging them — which violates PPL Discipline Rule #4
in CLAUDE.md §E.

Commit: `feat(mcp): MCP-4-S1 item 4 — log_prediction, record_outcome, flag_disagreement tool wrappers`

---

### Item 5 — Wire `ppl_writer` into `/api/mcp/execute` for predictive calls

**What:** Update `platform/src/app/api/mcp/execute/route.ts` to populate
the `predictions_logged[]` field in the envelope (currently an empty array
per MCP-1-S1). When `mode === "predictive"` or when the synthesis result
contains forward-looking signals, call `logPrediction()` and populate
`predictions_logged` with the returned `prediction_id`s.

The synthesis result from the orchestrator may include signals tagged
`forward_looking: true` from the MSR. If any such signals appear in
`synthesis_audit.dominant_signals`, auto-log one prediction entry per
forward-looking domain covered, with:
- `confidence` derived from the signal's `confidence` field
- `horizon` set to the signal's `horizon_days` if available, else `null`
  (native must fill in manually)
- `prediction_text` set to the synthesis answer truncated to 500 chars
- `falsifier` set to `"[AUTO_LOGGED — native to specify falsifier]"` as a
  placeholder, flagged for refinement

This is the "automatic PPL logging for predictive `ask_madhav` calls"
that MCP_BRIEF §4.1 specifies for the end-to-end tool.

**AC.MCP_4_S1.5:** `/api/mcp/execute` calls `logPrediction` when mode is
predictive or when forward-looking signals dominate; `predictions_logged`
array is non-empty for predictive queries; TypeScript strict passes.

**Why:** Per G4 (MCP_BRIEF §6) — PPL logging must happen before the
caller sees the prediction. Wiring it inside `/api/mcp/execute` ensures
logging happens server-side, before the response is returned, regardless
of what the MCP client does.

Commit: `feat(mcp): MCP-4-S1 item 5 — wire ppl_writer into /api/mcp/execute for predictive calls`

---

### Item 6 — Jest tests + full gate

**What:** Author `platform/src/lib/__tests__/mcp/ppl_writer.test.ts`
covering:
1. `logPrediction` returns a `PPL.MCP.*` prediction_id
2. `logPrediction` appends to the LEL file in the correct section (mock
   fs write; verify the section header and entry format)
3. `recordOutcome` with a valid `prediction_id` returns `{ok: true}`
4. `recordOutcome` with an unknown `prediction_id` returns `{ok: false}`
5. Provenance fields (key_id, trace_id) present in the logged entry

Author `platform/src/lib/__tests__/mcp/disagreement_writer.test.ts`:
1. `flagDisagreement` returns a `DIS.MCP.*` id
2. Appended entry is in the correct schema

Minimum: ≥7 tests total.

Then run the full gate command from `session_queue_MCP.yaml` MCP-4-S1:

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCP/platform &&
test -f src/app/api/mcp/writes/[action]/route.ts &&
test -f src/lib/mcp/ppl_writer.ts &&
npx tsc --noEmit &&
npx jest --testPathPattern="mcp/writes|mcp/ppl_writer" --passWithNoTests &&
cd ../platform-mcp &&
test -f src/tools/log_prediction.ts &&
test -f src/tools/record_outcome.ts &&
test -f src/tools/flag_disagreement.ts &&
npx tsc --noEmit
```

**AC.MCP_4_S1.6:** All tests pass; gate command exits 0.

**Why:** Write tools modify governance-critical files (LEL, DISAGREEMENT_REGISTER).
Unit tests with mocked file I/O verify the format without touching real
governance files during test runs.

Commit: `test(mcp): MCP-4-S1 item 6 — ppl_writer + disagreement_writer tests; full gate passes`

---

## §4 — Session-open handshake

You are a Conductor sub-agent. State briefly at start:

"MCP-4-S1 opening. Will implement write tools: ppl_writer.ts (interim LEL
prediction path), /api/mcp/writes/[action] dispatcher, disagreement_writer.ts,
3 MCP tool wrappers (log_prediction, record_outcome, flag_disagreement), PPL
auto-logging in /api/mcp/execute for predictive calls, and tests. 6 scope
items. Writes are governance-critical — will match LEL and DISAGREEMENT_REGISTER
schemas exactly."

---

## §5 — Scope constraints

### may_touch

```
platform/src/lib/mcp/ppl_writer.ts                              # CREATE
platform/src/lib/mcp/disagreement_writer.ts                     # CREATE (or inline in dispatcher)
platform/src/app/api/mcp/writes/[action]/route.ts               # CREATE
platform/src/app/api/mcp/execute/route.ts                       # UPDATE — wire ppl_writer for predictive calls
platform/src/lib/__tests__/mcp/ppl_writer.test.ts               # CREATE
platform/src/lib/__tests__/mcp/disagreement_writer.test.ts      # CREATE
platform-mcp/src/tools/log_prediction.ts                        # CREATE
platform-mcp/src/tools/record_outcome.ts                        # CREATE
platform-mcp/src/tools/flag_disagreement.ts                     # CREATE
platform-mcp/src/client.ts                                      # UPDATE — callPlatformWrites helper
platform-mcp/src/server.ts                                      # UPDATE — register 3 new write tools
01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md                           # READ to understand format; ppl_writer APPENDS to prediction subsection only
00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md                   # READ to understand format; writer APPENDs only
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_4_S1_v1_0.md        # status flip PENDING → COMPLETE
```

### must_not_touch

```
platform/src/lib/retrieve/**                                     # sealed
platform/src/lib/pipeline/**                                     # sealed
platform/src/app/api/chat/consume/**                             # sealed
platform/src/lib/mcp/auth.ts                                     # unchanged
platform/src/lib/mcp/epistemics.ts                               # unchanged
platform/src/lib/mcp/rate_limiter.ts                             # unchanged (from MCP-3-S2)
platform/src/lib/mcp/primitives_registry.ts                      # unchanged
platform-mcp/src/tools/ask_madhav.ts                             # unchanged
platform-mcp/src/tools/plan_query.ts                             # unchanged
platform-mcp/src/tools/execute_plan.ts                           # unchanged
platform-mcp/resources/**                                        # unchanged
01_FACTS_LAYER/LIFE_EVENT_LOG_v1_2.md                           # NO structural changes; prediction-subsection append only
00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md                   # NO structural changes; append only
025_HOLISTIC_SYNTHESIS/**                                        # sealed
06_LEARNING_LAYER/**                                             # PPL formal substrate is M-arc owned; do not touch
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md                          # sealed
00_ARCHITECTURE/CAPABILITY_MANIFEST.json                        # not in this session's scope
CLAUDE.md                                                       # §E update is post-workstream-close
```

### Commit cadence

```
<type>(mcp): MCP-4-S1 item <N> — <one-line summary>

<2-3 line description>
Acceptance criterion: AC.MCP_4_S1.<N>
```

---

## §6 — Session-close checklist (FINAL_SUMMARY)

After all 6 scope items are completed and the gate command passes, emit:

```
---FINAL_SUMMARY---
session_id: MCP-4-S1
status: PASS | HALT_NEEDS_HUMAN
commits:
  - <sha_item_1>
  - <sha_item_2>
  - <sha_item_3>
  - <sha_item_4>
  - <sha_item_5>
  - <sha_item_6>
scope_items_completed:
  - AC.MCP_4_S1.1   # ppl_writer.ts (interim LEL path)
  - AC.MCP_4_S1.2   # /api/mcp/writes/[action] dispatcher
  - AC.MCP_4_S1.3   # disagreement_writer.ts
  - AC.MCP_4_S1.4   # 3 write tool wrappers
  - AC.MCP_4_S1.5   # ppl_writer wired into /api/mcp/execute for predictive calls
  - AC.MCP_4_S1.6   # tests + full gate passes
scope_items_failed: []
gate_command_runs:
  - name: mcp_4_s1_writes_gate
    result: PASS | FAIL
notes_for_orchestrator: >
  Write tools implemented. PPL interim path uses LEL prediction subsection;
  migration TODO comment present in ppl_writer.ts pointing to 06_LEARNING_LAYER/.
  Disagreement writer appends to DISAGREEMENT_REGISTER_v1_0.md in correct schema.
  Total tool count is now 19 (16 read + 3 write). Next session: MCP-4-S2
  (red-team pass per §IS.8(b) — HALT_NEEDS_HUMAN if class-1 findings).
human_decision_needed: >
  <empty if PASS>
---END_FINAL_SUMMARY---
```

---

*End of CLAUDECODE_BRIEF_MCP_4_S1_v1_0.md.*
