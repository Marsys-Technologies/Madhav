# Nirmāṇa autonomous fleet — setup prompt for Claude Code (v2, plan v5.0)

Paste everything below the rule into a Claude Code session started from the repo root, with
`NIRMANA_REPO` and `DATABASE_URL` already exported in that shell.

Re-runnable: every task is idempotent, so this is also the recovery path after any reset.

---

You are preparing the Nirmāṇa autonomous campaign for launch. This is setup and verification
only — do NOT build, repair, or touch any asset data, and do NOT launch the fleet. Work the
tasks in order, with a task list. Some may already be done from a previous run; verify rather
than assume, and say which ones were already satisfied.

## Context

- Repo root is the current directory. The plan is `00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v4_0.md`
  — the filename says v4_0, the frontmatter says `version: 5.0`. That is deliberate (repo
  convention: `v2_0.md` held v2.2). Read its §18 (the fleet), §19 (the efficiency pillar), and
  `00_ARCHITECTURE/autonomy/CHARTER.md` before you start.
- Scope is one chart: `482012f1`. Never widen it.
- The charter's hard prohibitions H1–H8 bind you: no writes to `main`, no history rewrite, no
  fabricated results, no disabling a check to make it pass.

## Task 1 — Campaign branch

Create and switch to `campaign/nirmana-autonomous` (switch to it if it exists). Confirm with
`git branch --show-current`. If this fails, stop — everything after depends on it.

## Task 2 — Protect secrets and junk from the campaign's commits

Ensure `.gitignore` contains, appended idempotently without duplicating existing lines:

```
.clone/worktrees/
.codex/config.toml
00_ARCHITECTURE/autonomy/mailbox/
```

`.codex/config.toml` holds an unrotated production MCP key. Do not open it, print it, or fix it —
just make sure git never sees it. Verify with `git status --short` that neither it nor
`.clone/worktrees/` still appears, and report the before/after untracked counts.

## Task 3 — Verify the autonomy artifacts

Under `00_ARCHITECTURE/autonomy/`, confirm each exists and is non-empty:

```
CHARTER.md  RUNBOOK.md  SETUP_PROMPT.md
bin/nirmana-up.sh  bin/preflight.sh  bin/heartbeat.sh
prompts/_common.md prompts/adhikarin.md prompts/conductor.md
prompts/karaka.md  prompts/verifier.md  prompts/monitor.md prompts/scribe.md
state/CAMPAIGN_STATE.json  state/PRICING.json  state/STANDING_QUEUE.jsonl
state/DECISIONS.jsonl state/VERDICTS.jsonl state/PARKED.jsonl
state/HEARTBEAT.jsonl state/WORK_QUEUE.jsonl state/RUN_LEDGER.jsonl
mailbox/to_conductor/ mailbox/to_adhikarin/ mailbox/to_verifier/
mailbox/to_scribe/ mailbox/to_monitor/
```

Then `chmod +x bin/*.sh`, `bash -n` each script, validate every JSON and JSONL file parses.
Create any missing empty ledger or mailbox directory. Do NOT invent content for CHARTER.md,
RUNBOOK.md, PRICING.json or any prompt file — if one is missing or truncated, stop and report it
as a blocker rather than writing your own.

## Task 4 — Verify the plan

- Frontmatter reads `version: 5.0`.
- Invariants I1 through I18 are all present.
- Sections §0 through §19 exist with no gaps; §19 is Pillar IV (per-asset implementation
  efficiency).
- The generated block between `<!-- ASSET_PLANS:BEGIN -->` and `<!-- ASSET_PLANS:END -->` is
  present and well over a thousand lines — it was regenerated from live measurement and must not
  have been clobbered.

Report the file's line count and the ASSET_PLANS block's line count.

## Task 5 — Build the spend meter

**This is the substantive task.** The ceilings in `state/CAMPAIGN_STATE.json` are already set,
each beside a written definition. What does not yet exist is the meter that makes them
enforceable — and a ceiling with no meter is precisely the unearned-green defect this whole
campaign exists to cure. Preflight now fails without it.

Write `00_ARCHITECTURE/autonomy/bin/spend_meter.py`:

**Source.** Claude Code transcripts for this repo. Discover the actual layout under
`~/.claude/projects/` rather than assuming a glob — report what you find. Sum `message.usage`
across all four classes: `input_tokens`, `output_tokens`, `cache_creation_input_tokens`,
`cache_read_input_tokens`.

**Window.** Read `campaign_started_ts` from `CAMPAIGN_STATE.json` and count only sessions whose
first message is at or after it. If it is null, count everything and say so explicitly in the
reading's `note`. Transcripts do not record a git branch — do not implement or imply a branch
filter you cannot actually perform.

**Breakdown.** By token class AND by model. Three Opus panes, two Sonnet, plus spawned KĀRAKA — a
blended number cannot say which agent is burning, and the cost ceiling needs the per-model split.

**Cost.** Read `state/PRICING.json`. If rates are filled, compute USD per model per class and
total. If any needed rate is null, emit `"cost_usd": null` and `"pricing_state": "unfilled"`.
**Never estimate a cost.** A guessed number is charter H6.

**Output.** Append exactly one reading line to `state/SPEND.jsonl`:

```json
{"ts":"<ISO8601Z>","window_from":"<ts|null>","sessions":<n>,
 "by_class":{"input":<n>,"output":<n>,"cache_creation":<n>,"cache_read":<n>},
 "by_model":{"<model-id>":{"input":<n>,"output":<n>,"cache_creation":<n>,"cache_read":<n>}},
 "totals":{"tokens_all":<n>,"output_tokens":<n>},
 "cost_usd":<n|null>,"pricing_state":"filled|unfilled","note":"<one line>"}
```

Also print a short human summary to stdout.

**Failure behaviour.** If no transcripts are found or they cannot be parsed, write nothing to
SPEND.jsonl, print why, and exit non-zero. A meter that reports zero when it simply cannot see is
worse than one that admits it is blind.

**Self-test before you call it done.** Run it twice; confirm two readings appended and the numbers
are stable and non-zero. Then report the same convention spread you measured before — output only,
input+output+cache_creation, and all four summed — so the reading is auditable against the numbers
already in evidence. If your meter's all-four total is wildly inconsistent with the ~1.195B you
measured over 24h, something is wrong with the meter, not with the earlier measurement.

## Task 6 — Verify the ceilings are coherent

Do not change them. Read `CAMPAIGN_STATE.json` and confirm `ceilings` carries, as positive
integers: `tokens_campaign` (15,000,000,000), `tokens_per_rung` (4,000,000,000),
`output_tokens_campaign` (60,000,000), `output_tokens_per_rung` (16,000,000); a
`_token_definition` and `_output_definition` string beside them; and `cost_usd_campaign` /
`cost_usd_per_rung` as null with `_cost_note` explaining why.

Then, using your meter's actual reading, report what fraction of each ceiling is already consumed
and roughly how many fleet-days each implies. If any ceiling looks obviously wrong against real
data, say so — but do not edit it. That is the native's call.

## Task 7 — Verify the I2 snapshot

`00_ARCHITECTURE/control/snapshots/20260823_pre_protection_removal/` must exist and be non-empty.
It is the only recovery path for 38,287 rows no writer can regenerate. Report file count and total
size. Missing or empty is a launch blocker — say so plainly and do not work around it.

## Task 8 — Environment check

Report, without printing any secret value: `claude --version`, `tmux -V`, whether
`.venv/bin/python` exists and is executable, whether `DATABASE_URL` is set (set/unset only, never
echo it), and whether a postgres client is available (`psql` on PATH, or `psycopg`/`psycopg2`
importable). If `DATABASE_URL` is unset, note it as a manual step and continue.

## Task 9 — Commit

Stage and commit, on the campaign branch only, using `git add` with **explicit paths** — never
`git add -A` or `git add .`, because the working tree holds material that must not be swept in:

- `00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v4_0.md`
- `00_ARCHITECTURE/autonomy/` (mailbox is gitignored; state ledgers are committed — they are the
  audit trail)
- the `.gitignore` change
- `00_ARCHITECTURE/control/NIRMANA_ASSET_CONTROL_WORKBOOK_v4_1.xlsx` if present

Run `git status --short` after staging and confirm nothing unexpected is staged BEFORE committing.

```
Nirmāṇa v5.0: autonomous fleet, efficiency pillar, and spend meter

Plan v5.0 adds §19 (per-asset implementation efficiency) and I18, on top of
v4.2's §18 autonomous execution and I15-I17. Adds 00_ARCHITECTURE/autonomy/:
charter, six agent prompts, coordination state, spend meter, preflight, launcher.

Setup only — no asset data touched, campaign not started.
```

Do not push. Do not merge. Do not touch `main`.

## Task 10 — Preflight and dry run

```
NIRMANA_REPO="$PWD" ./00_ARCHITECTURE/autonomy/bin/preflight.sh
NIRMANA_REPO="$PWD" ./00_ARCHITECTURE/autonomy/bin/nirmana-up.sh --dry-run
```

Report both verbatim. Preflight now parses `CAMPAIGN_STATE.json` properly, requires the meter to
exist and to have produced a reading, and requires plan version ≥ 5.0. If it fails on something
you can legitimately fix — a missing directory, a permission, malformed JSON, a meter bug — fix it
and re-run. If it fails on something only the native can supply, leave it failing and list it.
**Do not edit preflight.sh to make a check pass.**

## Task 11 — Report

A short status table: every check, PASS or the specific blocker. Then exactly what remains for the
native to do by hand, in order. Do not launch the fleet.

Two standing rules for this whole job: never report a check as passing that you did not actually
run, and if any instruction here conflicts with the plan or the charter, follow the plan or the
charter and tell me about the conflict.
