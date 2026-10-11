# Bootstrap launch input — how to fill the template
One file per Wave B job (relaunch plan v2.7 §7 "Bootstrap (B-1) launches" and KV-06, §14 B-0c). Copy
`BOOTSTRAP_LAUNCH_INPUT.template.json` to `<JOB_SCRATCH>/launch_input.json`, replace every `<PLACEHOLDER>`, then
run `python3 -I -B <reviewed source>/fleet/kyboot.py check <file>`. Every value is read from disk or from a command
at the time of filling, never from memory. A missing, unfilled or untrue input refuses launch; nothing is defaulted.

| field | how it is obtained |
|---|---|
| `schema`, `claude_min_version`, `plan_version` | constants of the template; do not edit |
| `job_id` | new per launch, one path component (it names `ACT-launch-<job_id>`), e.g. `J-$(date -u +%Y%m%dT%H%M%SZ)-b1` |
| `item` | the `KV3-B-*` id in the packet's front matter; one live supervisor per item |
| `kind` | `BUILD` · `REWORK` · `ARTIFACT` · `VERIFY` · `PRE-ACCEPT` · `RULING` · `SURROGATE` · `PLAN` |
| `role` | `bootstrap-builder` · `bootstrap-reviewer` · `surrogate` · `planner`: names the qualification receipt |
| `worktree` | absolute top level of the job's worktree, under `/Users/Dev/worktrees.noindex/madhav/claude/` |
| `branch` | `git -C <worktree> rev-parse --abbrev-ref HEAD` (detached, `main` and `suvarna*` are refused) |
| `base_sha` | the job's base: `git -C <worktree> rev-parse <base>`; must be an ancestor of HEAD |
| `claude_bin` | `/Users/Dev/.local/bin/claude`: the file the receipt binds by path and sha256; `--version` ≥ 2.1.296 |
| `model` | `claude-opus-5-5` or `claude-sonnet-5-5`, per the plan §4 roster for the job's role |
| `effort` | `xhigh` for `PLAN`, `high` for every other kind |
| `permission_mode` | always explicit: `bypassPermissions` for builders and bootstrap jobs (plan §7) |
| `max_turns` | ≤ BUILD 150 · REWORK 100 · VERIFY 60 · ARTIFACT 60 · PRE-ACCEPT 40 · RULING 30 · SURROGATE 30 · PLAN 300 |
| `mcp_config` | absolute path of the staged `fleet/mcp.none.json` (reviewed source or worktree); a manifest component |
| `mcp_config_sha256` | `shasum -a 256 <mcp_config>`; the content must parse to exactly `{"mcpServers":{}}` |
| `prompt_path` | `<job_scratch>/prompt.md`: the card's exact bytes + the packet's exact bytes + the job header |
| `prompt_sha256` | `shasum -a 256 <prompt_path>`, taken after the last edit |
| `card_path`, `card_sha256` | the reviewed role card (a manifest component) and its `shasum -a 256` |
| `packet_path` | the admitted packet file in `worktree` |
| `packet_sha256` | `shasum -a 256 <packet_path>` — the file's bytes, not the front-matter field of that name |
| `job_scratch` | exactly `$KY_SCRATCH/jobs/<job_id>`, written as the resolved path (no symlink in it) |
| `stdout_path`, `stderr_path` | files beneath `job_scratch`; they must not exist yet |
| `tmp_path` | a directory beneath `job_scratch`; it becomes the job's `TMPDIR` |
| `state_path` | exactly `$KY_RUN/jobs/<job_id>/state.json`; it must not exist yet |
| `env` | the job's whole environment (nothing is inherited); see below |
| `extra_lean_flags` | exactly the flags of the qualification receipt's launch line for this role and model, or `[]` |
| `disallowed_tools` | tool rules to deny (`--disallowedTools`), exactly as qualified; else `[]` |
| `deadline` | UTC ISO-8601 in the future and no later than now + the receipt's `deadline_seconds`; no default |
| `approved_source_commit` | the 40-hex commit in `$KY_RUN/VERSIONS.bootstrap.json`; it must exist in the repository |

**`env`.** Accepted names: `HOME PATH LANG TERM USER TMPDIR ZDOTDIR KY_ROOT KY_RUN KY_SCRATCH JOB_SCRATCH KY_FLEET
KY_STREAM KY_LANE KY_ITEM KY_PY SE_EPHE_PATH SWE_EPHE_PATH TESTS`; `HOME`, `PATH`, `KY_ROOT`, `TMPDIR`, `KY_SCRATCH`
and `JOB_SCRATCH` are required. The sorted names must equal the receipt's `env_names` (the template carries the
bootstrap-builder list) and `PATH` its `child_path`. Paths are absolute; `TMPDIR` equals `tmp_path`, `JOB_SCRATCH`
`job_scratch`, `KY_SCRATCH` the supervisor's resolved scratch folder, `KY_RUN` its `KY_RUN`, `KY_ITEM` the `item`,
`ZDOTDIR` `<KY_ROOT>/zdotdir`. A name matching `DATABASE_URL`, `*_DATABASE_URL`, `PGPASSWORD`, `ANTHROPIC_API_KEY`,
`*TOKEN*` or `*SECRET*` refuses launch. Never in `extra_lean_flags`: `--bare` (P-1), `--mcp-config`, `--settings`,
`--setting-sources`, `--dangerously-skip-permissions`, any flag the launch line sets itself.

**Gates that are not fields** (before every launch; a failed one stops the check and nothing is executed):
`kyboot.py` runs from the reviewed staged source, never from `fleet_live`, and it, `kyschema.py` and
`kymanifest.py` equal their manifest components; `kymanifest.py check` passes (`--manifest` defaults to
`$KY_RUN/VERSIONS.bootstrap.json`); `$KY_RUN/QUALIFICATIONS/<role>-<model>.json` is recorded in the manifest, says
`PASS`, was earned in the context the job runs in (under launchd: a real job goes through `submit`) and binds this
launch: program path and sha256 (compared before `--version` is run), version, model, effort, permission mode, turn
limit, MCP hash, environment names, `child_path`, the worktree's `.claude/settings.json`, `<KY_ROOT>/zdotdir`, the
harness `kyqualify.py`, the launch line. A credential variable in the supervisor's own environment exits 78.

**Then:** `check <file>` → `argv <file>` (the launch line) → `submit <file>` (a one-shot launchd agent; `status`,
`reap`) or `run <file>` (this shell; it needs `KY_SCRATCH`). `run` takes `$KY_RUN/locks/kyboot.<item>`, writes
`$KY_RUN/actions/ACT-launch-<job_id>.json` first, refuses a spent `job_id`, supervises to exit or `deadline`. The job
must leave `$JOB_SCRATCH/result.json`: without it `run` exits 5, never 0. Exit 0 is not acceptance.
