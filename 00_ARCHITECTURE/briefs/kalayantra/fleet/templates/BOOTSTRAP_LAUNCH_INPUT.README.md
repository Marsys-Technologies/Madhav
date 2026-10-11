# Bootstrap launch input — how to fill the template

One file per Wave B job (relaunch plan v2.7 §7 "Bootstrap (B-1) launches" and KV-06, §14 B-0c). Copy
`BOOTSTRAP_LAUNCH_INPUT.template.json` to `<JOB_SCRATCH>/launch_input.json`, replace every `<PLACEHOLDER>`, then
run `python3 <reviewed source>/fleet/kyboot.py check <file>`. Every value is read from disk or from a command
at the time of filling, never from memory. A missing, unfilled or untrue input refuses launch; nothing is defaulted.

| field | how it is obtained |
|---|---|
| `schema`, `claude_min_version`, `plan_version` | constants of the template; do not edit |
| `job_id` | new per launch, one path component, e.g. `J-$(date -u +%Y%m%dT%H%M%SZ)-b1`; never reused |
| `item` | the `KV3-B-*` id in the packet's front matter; one live supervisor per item |
| `kind` | `BUILD` · `REWORK` · `ARTIFACT` · `VERIFY` · `PLAN`, as the job is |
| `role` | `bootstrap-builder` · `bootstrap-reviewer` · `surrogate` · `planner`: names the qualification receipt |
| `worktree` | absolute top level of the job's worktree: `git -C <dir> rev-parse --show-toplevel` |
| `branch` | `git -C <worktree> rev-parse --abbrev-ref HEAD` (a detached HEAD is refused) |
| `base_sha` | the job's base: `git -C <worktree> rev-parse <base>`; must be an ancestor of HEAD |
| `claude_bin` | `/Users/Dev/.local/bin/claude` as it resolves now; `--version` must be at least 2.1.296 |
| `model` | `claude-opus-5-5` or `claude-sonnet-5-5`, per the plan §4 roster for the job's role |
| `effort` | `xhigh` for `PLAN`, `high` for every other kind |
| `permission_mode` | always explicit: `bypassPermissions` for builders and bootstrap jobs (plan §7) |
| `max_turns` | a positive integer, at most BUILD 150 · REWORK 100 · VERIFY 60 · ARTIFACT 60 · PLAN 300 |
| `mcp_config` | absolute path of the staged `fleet/mcp.none.json` (reviewed source or worktree); a manifest component |
| `mcp_config_sha256` | `shasum -a 256 <mcp_config>`; the content must parse to exactly `{"mcpServers":{}}` |
| `prompt_path` | the admitted prompt (card + packet + job header) written to `<job_scratch>/prompt.md` |
| `prompt_sha256` | `shasum -a 256 <prompt_path>`, taken after the last edit |
| `card_path`, `card_sha256` | the reviewed role card (a manifest component) and its `shasum -a 256` |
| `packet_path` | the admitted packet file in `worktree` |
| `packet_sha256` | `shasum -a 256 <packet_path>` — the file's bytes, not the front-matter field of that name |
| `job_scratch` | exactly `$KY_SCRATCH/jobs/<job_id>` (resolved; no symlink out of the scratch folder) |
| `stdout_path`, `stderr_path` | files beneath `job_scratch`; they must not exist yet |
| `tmp_path` | a directory beneath `job_scratch`; it becomes the job's `TMPDIR` |
| `state_path` | exactly `$KY_RUN/jobs/<job_id>/state.json`; it must not exist yet |
| `env` | the job's whole environment (nothing is inherited); see below |
| `extra_lean_flags` | exactly the flags of the qualification receipt's launch line for this role and model, or `[]` |
| `disallowed_tools` | tool rules to deny (`--disallowedTools`), exactly as qualified; else `[]` |
| `deadline` | UTC ISO-8601 in the future, e.g. `date -u -v+3H +%Y-%m-%dT%H:%M:%SZ`; there is no default |
| `approved_source_commit` | the 40-hex commit in `$KY_RUN/VERSIONS.bootstrap.json`; it must exist in the repository |

**`env`.** Only these names are accepted: `HOME PATH LANG TERM USER TMPDIR ZDOTDIR KY_ROOT KY_RUN KY_FLEET
KY_STREAM KY_LANE KY_ITEM KY_PY SE_EPHE_PATH SWE_EPHE_PATH TESTS`. `HOME`, `PATH`, `KY_ROOT` and `TMPDIR` are
required; the sorted names must equal the qualification receipt's `env_names`. Paths are absolute (`PATH` entry
by entry); `TMPDIR` equals `tmp_path`, `KY_RUN` the supervisor's `KY_RUN`, `KY_ITEM` the `item`. Any name matching
`DATABASE_URL`, `*_DATABASE_URL`, `PGPASSWORD`, `ANTHROPIC_API_KEY`, `*TOKEN*` or `*SECRET*` refuses launch.
Never accepted in `extra_lean_flags`: `--bare` (P-1), `--dangerously-skip-permissions`, `--mcp-config`,
`--settings`, `--setting-sources`, and any flag the launch line already sets.

**Gates that are not fields** (all before every launch; `--manifest` defaults to
`$KY_RUN/VERSIONS.bootstrap.json`): `kyboot.py` runs from the reviewed staged source, never from `fleet_live`,
and it, `kyschema.py` and `kymanifest.py` equal their manifest components; `kymanifest.py check` passes
(ACCEPTED review included); `$KY_RUN/QUALIFICATIONS/<role>-<model>.json` is recorded in the manifest, says `PASS`,
was earned in the context the job runs in (`shell` | `launchd`) and binds this launch (program path, hash and
version, model, effort, permission mode, turn limit, MCP hash, environment names, launch line). The supervisor's
shell needs `KY_SCRATCH` (under `/Users/Dev/scratch.noindex/`); `KY_RUN` defaults to `/Users/Dev/kalayantra/run`;
`DATABASE_URL`, `*_DATABASE_URL`, `PGPASSWORD` or `ANTHROPIC_API_KEY` set there exits 78.

**Then:** `kyboot.py check <file>` → `kyboot.py argv <file>` (the exact launch line) → `kyboot.py run <file>` (this
shell) or `kyboot.py submit <file>` (a one-shot launchd agent that outlives the session; `status` and `reap`
follow it). `run` takes `$KY_RUN/locks/kyboot.<item>`, writes `$KY_RUN/actions/ACT-launch-<job_id>.json` first,
refuses a spent `job_id`, supervises to exit or `deadline` and records the outcome. Exit 0 is not acceptance.
