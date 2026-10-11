---
artifact: KALAYANTRA_RELAUNCH_PLAN_v2_3_PROPOSED.md
status: PROPOSED — not approved. KALAYANTRA_RELAUNCH_PLAN_v2_2.md remains the only operating plan. Nothing here is in force until the owner either (A) records the two replacements below as owner decisions at the level of plan §15, or (B) approves a new source commit carrying a plan v2.3 with them.
version: 2.3-proposed
proposes_changes_to: KALAYANTRA_RELAUNCH_PLAN_v2_2.md §5 (CLAUDE_BIN line), §7 (launch line and its CLAUDE.md bullet)
authored_by: Claude Code (Opus 5.5, xhigh) — KĀLA-YANTRA v3 Planner, session local_ef70d1f5-345a-4255-847f-212971af5951
authored_on: 2026-10-11
written_under: planning prompt v2.2 — "A needed plan change is written to KALAYANTRA_RELAUNCH_PLAN_v2_3_PROPOSED.md; then stop and report."
evidence_root: /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/planner/probe/ and /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/reviews/triage-delta-r1/attempt1/
---

# Two launch defects found by running the plan's own launch line on this host

Both were found on 2026-10-11 while launching the independent reviewer of the B-0b triage delta. Neither
affects B-0a or B-0b. Both stop **every** headless job the plan describes (B-1 bootstrap builders, B-3
rehearsal jobs, all campaign jobs), so B-0c's launch-input template and B-1 cannot be written against v2.2 as
it stands.

## P-1 — the §7 launch line cannot sign in (`--bare`)

**Observed.** The plan §7 line, run under the same `env -i` environment with the staged empty MCP
configuration, ends at once with `Not logged in · Please run /login` and exit code 1. The identical line
without `--bare` answers normally (probe files `bare.out` / `nobare.out`). The installed program's own help
states that `--bare` never reads the stored sign-in and accepts only an API key. The plan forbids an API key
in a job's environment (§7: `kyjob.sh` exits 78 if `ANTHROPIC_API_KEY` is set) and the owner runs one
subscription (§18), so no configuration of v2.2 lets a `--bare` job start.

**Replacement — §7 launch line.** Remove `--bare`; add `--setting-sources project`:

```
  "$CLAUDE_BIN" -p --setting-sources project --permission-mode "$PERMISSION_MODE" \
    --model "$MODEL" --effort "$EFFORT" --max-turns "$MAX_TURNS" \
    --strict-mcp-config --mcp-config "$MCP_CONFIG" $DISALLOWED \
    --output-format stream-json --verbose --add-dir "$KY_ROOT" \
    < "$PROMPT_PATH" > "$STDOUT_PATH" 2> "$STDERR_PATH"
```

`PERMISSION_MODE` is always passed explicitly (`bypassPermissions` for builders, as today). Reason: on this
host the owner's user-level settings make `bypassPermissions` the default, and a session launched without the
flag inherited it (attempt1 `stdout.jsonl`, init event) — a verifier must never depend on a default.

**Replacement — §7 bullet "CLAUDE.md under `--bare` is unknown".**

> Without `--bare` the project `CLAUDE.md` of the job's worktree is loaded automatically; cards still carry
> the applicable §I/§N rules per COVERAGE and never rely on that load. Before the launch-input template is
> frozen (B-0c), one probe job per roster model records: sign-in works; the project `CLAUDE.md` is in context;
> no user-level hook, plugin, skill or MCP server is active; the fixed input-token overhead of an empty job.
> B-3's visibility fixture repeats the probe on the installed bundle and the result is recorded in the install
> receipt. A probe that cannot show an item reports it as unknown, never as absent.

**Cost to state honestly.** A one-line probe with `--setting-sources project` started with about 31,000
input tokens of fixed context (probe file `ss.out`, `cache_creation_input_tokens` 31363, Sonnet 5.5, empty
directory). `--bare` would have been smaller, but it cannot run. The per-job overhead is therefore a measured
quantity for §13, not the "small fixed context" v2.2 assumed; reducing it (for example with
`--disable-slash-commands`, which the probe accepted) is B-0c template work, verified by the same probe.

## P-2 — the pinned program is too old for Opus 5.5

**Observed.** `CLAUDE_BIN=/Users/Dev/.local/bin/claude` is version 2.1.239. Asked for `claude-opus-5-5` it
returns an API error saying version 2.1.280 or newer is required (attempt1 `stdout.jsonl`). Sonnet 5.5 works
on it. Every Opus role in §4 (bootstrap builder, verifier, authority, planner jobs) therefore fails at launch.
A 2.1.296 program exists inside the Antigravity extension folder and was used for the one review session of
B-0b; its path changes with every extension update, so it is not a suitable pinned `CLAUDE_BIN`.

**Owner action (one command, not a plan change):** update the installed program —

```bash
/Users/Dev/.local/bin/claude update
```

**Replacement — §5 `CLAUDE_BIN` line.**

> `CLAUDE_BIN=/Users/Dev/.local/bin/claude` (resolved on this host before any scrub, asserted executable, its
> version recorded in `run/INSTALL_RECEIPT.json`). Before any launch, and again at installation, a one-turn
> probe per roster model (§4) must succeed with the exact launch line; a model the program refuses is a launch
> refusal naming the required version, never a retry loop.

## What does not change

Roster, capacity, topology, dispatcher, packets, routing, gate, conductor, finalisation, measurement, waves
and owner decisions are untouched. The planning prompt's B-1 paragraph already says "with the plan §7 line"
and needs no new wording; the conductor prompt does not quote the launch line. Astra's KU-01…KU-03 are
unaffected.

## Recommended route

**(A) Owner decisions**, recorded the way the 2026-10-11 decisions were (a dated block in the next planner
paste and in the hand-off): "P-1 replacement adopted; P-2 program updated". The approved source commit and
both paste anchors stay valid; B-0c writes the launch-input template to the replacement line and its
independent review covers it. Route (B), a re-approved v2.3 bundle, costs a new Astra pass and new paste
anchors for the same two paragraphs.
