---
artifact: CLAUDECODE_BRIEF_MCP_4_S2_v1_0.md
type: CLAUDECODE_BRIEF
version: 1.0
status: COMPLETE
authored_by: Claude Code sub-agent (MCP-0-AUTHOR)
authored_at: 2026-05-21
session_id: MCP-4-S2
session_name: MCP-4-S2 — Red-team pass per §IS.8(b)
executor: Claude Code sub-agent (general-purpose, spawned by MCP Conductor)
execution_mode: single autonomous session, --dangerously-skip-permissions
worktree:
  name: MadhavMCP
  branch: feature/mcp-server
  base: main
  path_absolute: /Users/Dev/Vibe-Coding/Apps/MadhavMCP
governing_plan: 00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md
reference_brief: 00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_1_S1_v1_0.md
predecessor_session: MCP-4-S1 (write tools complete)
next_session_anticipated: MCP-MERGE (push + PR + auto-merge)
---

# CLAUDECODE_BRIEF — MCP-4-S2
## Red-team pass per §IS.8(b) — MCP workstream security + governance audit

---

## §0 — How to start this session

You are a sub-agent spawned by the MCP Conductor. Your context is fresh.
You are in the MadhavMCP worktree at `/Users/Dev/Vibe-Coding/Apps/MadhavMCP`
on branch `feature/mcp-server`. The Conductor has already pasted your
session prompt; you are now reading this brief.

This is the **red-team pass** for the MCP workstream. You run a structured
checklist against the MCP surface, document findings in a report, and
classify each finding. The session is PASS if there are zero class-1
findings. Any class-1 finding (blocking) causes the session to emit
HALT_NEEDS_HUMAN.

**This is a verification-only session.** You do NOT fix any findings you
discover — fixes go to a follow-up brief authored after human review of
class-1 findings. If you find something you can fix in 2 lines without
risk, use your judgment, but do not restructure code to fix deeper issues.
Your job is to find and document, not to fix silently.

---

## §1 — Session identity

| Field | Value |
|---|---|
| Session ID | MCP-4-S2 |
| Branch | `feature/mcp-server` |
| Worktree path | `/Users/Dev/Vibe-Coding/Apps/MadhavMCP` |
| Execution mode | Single autonomous session, `--dangerously-skip-permissions` |
| Predecessor | MCP-4-S1 (all 19 tools complete: 16 read + 3 write) |
| Anticipated next | MCP-MERGE (if PASS) |

---

## §2 — Mandatory reads at session open (in order)

1. `CLAUDE.md` (§C mandatory list — full read, especially §M cadence +
   §IS.8 red-team obligations)
2. `00_ARCHITECTURE/BRIEFS/MCP_BRIEF_v1_0.md` — **focus on §6 governance
   carry-over (G1–G12), §8 risks (R1–R8), §7.4 Phase MCP-4 acceptance
   criteria**
3. `platform/src/lib/mcp/auth.ts` — read the auth implementation; test
   against the attack scenarios below
4. `platform/src/app/api/mcp/execute/route.ts` — read for B.11 floor
   enforcement, synthesis_audit accuracy, audience-tier stamping
5. `platform/src/app/api/mcp/primitives/[tool]/route.ts` — read for
   whitelist enforcement and surgical flag stamping
6. `platform/src/lib/mcp/rate_limiter.ts` — read for correctness
7. `platform/src/lib/mcp/ppl_writer.ts` — read for provenance field
   completeness and format correctness
8. `00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md` — read to understand
   the schema the disagreement_writer must match

---

## §3 — Scope (3 items — execute in order; commit after completion)

### Item 1 — Author `00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md` checklist document

**What:** Create the red-team report document with this structure:

```markdown
---
artifact: MCP_RED_TEAM_v1_0.md
version: 1.0
status: IN_PROGRESS  # → PASS or FAIL at session close
session_id: MCP-4-S2
red_team_date: 2026-05-21
---

# MCP Workstream — Red-Team Report v1.0

## Summary
- class-1 findings: <N>   ← gate checks for "class-1 findings: 0"
- class-2 findings: <N>
- class-3 findings: <N>
- red-team status: PASS | FAIL  ← gate checks for "red-team status: PASS"

## Findings

### RT-01 — <finding title>
**Class:** 1 | 2 | 3
**Test:** <what was tested>
**Result:** PASS | FAIL
**Evidence:** <what was observed>
**Remediation (if applicable):** <suggested fix>

... (one block per test, 9 tests minimum)
```

The report starts as a skeleton at the top of this item; you fill in each
finding block as you run the tests in Item 2.

**AC.MCP_4_S2.1:** `MCP_RED_TEAM_v1_0.md` exists; has the required
structure (frontmatter, summary block with both gate-required lines, ≥9
finding blocks).

**Why:** The gate command checks for the literal strings `"class-1 findings: 0"`
and `"red-team status: PASS"`. The report is the artifact that unlocks
MCP-MERGE.

Commit: `chore(mcp): MCP-4-S2 item 1 — author MCP_RED_TEAM_v1_0.md skeleton`

---

### Item 2 — Run the 9 red-team tests and fill the report

**What:** Execute each test below. For each, write the result into the
corresponding finding block in `MCP_RED_TEAM_v1_0.md`. Use Jest unit
tests where practical (mock the DB/file system); use code-reading for
tests that are structural rather than runtime.

#### RT-01 — Auth bypass: invalid key
**Test:** Call `validateMcpKey("Bearer invalid_key_here")`. Verify return
is `null`. Verify the `/api/mcp/execute` handler returns 401.
**Class:** 1 if it doesn't return null / doesn't reject. 3 if it does.
**Method:** Jest test or direct code inspection.

Author `platform/src/lib/__tests__/mcp/red_team/auth_bypass.test.ts`
to run this test programmatically.

#### RT-02 — Auth bypass: revoked key
**Test:** Verify that a key with `revoked_at IS NOT NULL` is rejected by
`validateMcpKey`. Inspect the SQL in `auth.ts` — the WHERE clause must
include `revoked_at IS NULL`.
**Class:** 1 if revoked keys can authenticate. 2 if the SQL is correct but
not tested. 3 if the SQL is correct AND there's a test.

#### RT-03 — Audience-tier leakage via primitive
**Test:** Inspect the primitives dispatcher — does it re-use the
`audience_tier` from `X-MCP-Audience-Tier` header? Verify it does NOT
let the caller set their own tier (the tier comes from the resolved
principal, not from the request body).
**Class:** 1 if caller can set own tier. 2 if tier comes from header but
header is trusted without verification. 3 if tier is resolved from DB only.

#### RT-04 — Primitive whitelist enforcement
**Test:** Author a Jest test that calls the dispatcher with
`toolName: "pattern_register"` (not in whitelist). Verify the response
is `{ok: false, error: {class: "validation"}}` with HTTP 400.
**Class:** 1 if non-whitelisted tools are callable. 3 if whitelist blocks.

Author this test in `platform/src/lib/__tests__/mcp/red_team/whitelist.test.ts`.

#### RT-05 — SQL injection via tool params
**Test:** Inspect how primitive tool params flow into the retrieval tools.
Do any params get string-interpolated into SQL? Check the 10 retrieval
tool implementations for parameterized query usage. Look specifically at
`chart_facts_query`, `msr_sql`, and `lel_query` — the three most
param-rich tools.
**Class:** 1 if any param is string-interpolated into SQL. 2 if params
flow through an ORM or parameterized query but no explicit test exists.
3 if parameterized + tested.
**Method:** Code inspection; cite specific line references.

#### RT-06 — Rate limit bypass
**Test:** Inspect the rate limiter implementation. Is it possible to bypass
by sending requests without a key_id? Does the in-process Map reset across
server restarts (yes, by design — document as known limitation, class 3).
Verify the limit fires at 61 RPM in the Jest test from MCP-3-S2.
**Class:** 1 if rate limiter can be bypassed by omitting key_id. 2 if it
resets on restart (known limitation, not a bypass). 3 if it works correctly.

#### RT-07 — PPL write tampering: record_outcome for unowned prediction
**Test:** Inspect `recordOutcome` — does it verify the `key_id` in the
outcome entry matches the `key_id` that originally logged the prediction?
If `prediction_id` is found but `key_id` doesn't match, should it be
blocked?
**Class:** 2 if outcomes can be recorded for predictions logged by a
different key (this is a governance issue but not a security breach — all
keys are admin-issued to trusted principals per D12). Class 3 if same-key
enforcement is present.
**Notes:** Per D12, all API keys are issued to trusted parties. Cross-key
outcome recording is a governance gap, not a security vulnerability.
Document as class-2 with a remediation suggestion.

#### RT-08 — Plan-edit privilege escalation via execute_plan
**Test:** Inspect `/api/mcp/execute` handler for `execute_plan` tool — does
it re-validate `plan.audience_tier` against the request's resolved principal
tier? Verify a `client`-tier caller cannot submit a plan with
`audience_tier: "super_admin"`.
**Class:** 1 if tier escalation is possible. 2 if validation exists but
is incomplete. 3 if re-validation is correct and tested.

Author a Jest test in `platform/src/lib/__tests__/mcp/red_team/plan_escalation.test.ts`.

#### RT-09 — B.11 floor bypass via ask_madhav
**Test:** Inspect the `/api/mcp/execute` handler for `ask_madhav` — does
the `synthesis_audit.holistic_read_passed` flag correctly reflect whether
at least one L2.5 tool fired? Inspect what happens when `mode: "factual"` —
does `holistic_read_passed` become `false` (which is expected and correct)?
Verify a `mode: "holistic"` call cannot return `holistic_read_passed: false`
without a warning in the envelope.
**Class:** 1 if holistic mode silently bypasses B.11 floor. 2 if bypass is
possible but logged as warning. 3 if floor enforced and synthesis_audit
correct.

**After all 9 tests:** Update the summary block in `MCP_RED_TEAM_v1_0.md`
with the actual counts. Set `status` to `PASS` (all class-1 findings = 0)
or `FAIL`.

**AC.MCP_4_S2.2:** All 9 tests run and documented; finding blocks complete
with class, test method, result, evidence; summary block accurate; red-team
test files authored (at least for RT-01, RT-04, RT-08).

**Why:** Red-team cadence per CLAUDE.md §M + MCP_BRIEF G12. Every
macro-phase close requires a red-team pass. The MCP workstream's phase
MCP-4 is the gating phase for the merge; the red-team is this phase's
close obligation.

Commit: `chore(mcp): MCP-4-S2 item 2 — red-team tests run; MCP_RED_TEAM_v1_0.md findings filed`

---

### Item 3 — Final status seal + gate verification

**What:**
1. Update `MCP_RED_TEAM_v1_0.md` frontmatter `status` from `IN_PROGRESS`
   to `PASS` or `FAIL`.
2. Run the gate command from `session_queue_MCP.yaml` MCP-4-S2:

```bash
test -f 00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md &&
grep -q "class-1 findings: 0" 00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md &&
grep -q "red-team status: PASS" 00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md
```

If class-1 findings exist → the gate fails → emit `HALT_NEEDS_HUMAN` in
FINAL_SUMMARY with a precise description of each class-1 finding and the
suggested remediation.

If zero class-1 findings → gate passes → emit `PASS` in FINAL_SUMMARY.

**AC.MCP_4_S2.3:** Gate command exits 0 (PASS) or session emits
HALT_NEEDS_HUMAN with class-1 details (FAIL path).

**Why:** The gate is binary. "class-1 findings: 0" AND "red-team status:
PASS" must both be in the document for the Conductor to proceed to
MCP-MERGE. Any other state is a halt.

Commit: `chore(mcp): MCP-4-S2 item 3 — red-team sealed; gate verified`

---

## §4 — Session-open handshake

You are a Conductor sub-agent. State briefly at start:

"MCP-4-S2 opening. Red-team pass per §IS.8(b). Will author
MCP_RED_TEAM_v1_0.md, run 9 tests (auth bypass, revocation, audience-tier
leakage, whitelist enforcement, SQL injection, rate-limit bypass, PPL
write tampering, plan escalation, B.11 floor). PASS only if 0 class-1
findings. HALT_NEEDS_HUMAN if any class-1."

---

## §5 — Scope constraints

### may_touch

```
00_ARCHITECTURE/MCP_RED_TEAM_v1_0.md                              # CREATE + UPDATE
platform/src/lib/__tests__/mcp/red_team/auth_bypass.test.ts       # CREATE
platform/src/lib/__tests__/mcp/red_team/whitelist.test.ts         # CREATE
platform/src/lib/__tests__/mcp/red_team/plan_escalation.test.ts   # CREATE
00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_MCP_4_S2_v1_0.md          # status flip PENDING → COMPLETE
```

### must_not_touch

```
platform/src/lib/mcp/**                                            # read-only in this session
platform/src/app/api/mcp/**                                        # read-only in this session
platform-mcp/**                                                     # read-only in this session
platform/src/lib/retrieve/**                                        # sealed
platform/src/lib/pipeline/**                                        # sealed
01_FACTS_LAYER/**                                                   # sealed
025_HOLISTIC_SYNTHESIS/**                                           # sealed
00_ARCHITECTURE/DISAGREEMENT_REGISTER_v1_0.md                      # sealed for this session
00_ARCHITECTURE/PLANNER_PROMPT_v2_0.md                             # sealed
00_ARCHITECTURE/CAPABILITY_MANIFEST.json                            # not in this session
CLAUDE.md                                                          # §E update is post-workstream-close
```

**Critical constraint:** This is a verification session only. Do not
restructure or rewrite any application code to fix findings. If you find
a 1-2 line obvious fix (e.g., missing `IS NULL` in a WHERE clause), use
judgment and note it in the finding. For anything larger, document and halt.

### Commit cadence

```
chore(mcp): MCP-4-S2 item <N> — <one-line summary>

<2-3 line description>
Acceptance criterion: AC.MCP_4_S2.<N>
```

---

## §6 — Session-close checklist (FINAL_SUMMARY)

After all 3 scope items are completed and the gate is run, emit:

```
---FINAL_SUMMARY---
session_id: MCP-4-S2
status: PASS | HALT_NEEDS_HUMAN
commits:
  - <sha_item_1>
  - <sha_item_2>
  - <sha_item_3>
scope_items_completed:
  - AC.MCP_4_S2.1   # MCP_RED_TEAM_v1_0.md skeleton authored
  - AC.MCP_4_S2.2   # 9 tests run; findings documented
  - AC.MCP_4_S2.3   # gate verified (PASS or FAIL)
scope_items_failed: []
gate_command_runs:
  - name: mcp_4_s2_red_team_gate
    result: PASS | FAIL
notes_for_orchestrator: >
  Red-team complete. <N> class-1, <N> class-2, <N> class-3 findings.
  <Summary sentence: "No blocking issues found" or "Class-1 finding in RT-0N
  blocks merge — see human_decision_needed.">
human_decision_needed: >
  <empty string if PASS>
  <If HALT: "Class-1 finding(s) in MCP_RED_TEAM_v1_0.md require human
  review before merge can proceed. Findings: [RT-NN <title> — <one-line
  description of the issue and why it is class-1>]. Suggested fix: [...]
  Please review MCP_RED_TEAM_v1_0.md and authorise a fix session or
  downgrade the finding if acceptable.">
---END_FINAL_SUMMARY---
```

---

*End of CLAUDECODE_BRIEF_MCP_4_S2_v1_0.md.*
