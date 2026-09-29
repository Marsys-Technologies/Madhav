---
artifact: SUVARNA_RUNBOOK
canonical_id: SUVARNA_RUNBOOK
version: "1.2"
status: DRAFT — for native review (N-1, with the v1.4 plan set)
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa"
companion_of: SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md (v1.4) and SUVARNA_AUTONOMY_CHARTER_v1_0.md (v1.4)
changelog:
  - "1.2 (2026-09-29, review pass 2 folded): D6 recorded as applied. A missing or broken reader file is re-issued by D6 runbook §3 (--apply), never by the rollback, which restores the write-capable app login. The tracker and Monitor run from the committed code in the hq worktree and are restarted after each plan merge (L.17), reading NIKASHA_REF=origin/campaign/nikasha-test. New launch steps for isolation (N-25; L.16a/b/g). The permission allow-list is the untracked Suvarṇa settings file passed with --settings, not the tracked .claude/settings.json. /loop 10m. Decisions are recorded only in Strategic Suvarṇa. New incident rows: isolation, decision writers. L0 is four native dispatches."
  - "1.1 (2026-09-29, L.12 sweep to the v1.3 set): launch checklist rebuilt: N-1 read from the authoritative decisions log ($SUVARNA_HOME/run/DECISIONS.jsonl, written only through python -m suvarna_tracker.decide); the D6 reader login applied and the Monitor's eight checks listed (credential_readonly included); hq brought current by a merge commit, never --ff-only (arch §12.12); the decisions mirror; the permission allowlist (dontAsk, never bypass) and the watchdog (L.15); sessions started in dontAsk mode and /loop armed (D5 interim to G2), with the weekly re-arm; the durable headless runner (L.14) before B.W1. Census only through census_lock. New §7 for the native's part in L0 waves (D1, D4) and the builder identity (E7.2). Incidents: credential missing blocks / too open warns (a changed file is not detectable), credential_readonly and builder_scope blocks, a stalled Conductor, usage-limit pauses. Where-things-live table updated. Sources: REVIEW_PASS1_DISPOSITION_v1_0.md (S2, C24, C43); D1, D4, D5, D6."
  - "1.0 (2026-09-29): first draft. Launch, daily operation, hold and resume, restart after a reboot, incidents, where things live."
---

# Suvarṇa — runbook

How to launch the campaign, run it day to day, pause it, and bring it back after a restart. Commands are exact.

## §1 · Where things live

| What | Where |
|---|---|
| Campaign home | `/Users/Dev/suvarna/` (`hq/`, `trunk/`, `lanes/`, `evidence/`, `run/`) |
| Plan, charter, architecture, roles, prompts, track briefs | `hq/00_ARCHITECTURE/briefs/suvarna/` (branch `suvarna/hq`; authored on `strategy/suvarna-plan`) |
| **Decisions log (authoritative)** | `/Users/Dev/suvarna/run/DECISIONS.jsonl`, outside git, written only through `python -m suvarna_tracker.decide` by Strategic Suvarṇa with you present (under N-25 owned by your account, read-only to the swarm) |
| Decisions mirror · queues · digests | `hq/00_ARCHITECTURE/control/suvarna/state/{DECISIONS,QUEUE,QUEUE_ENGINE}.jsonl`, `DIGEST_<date>.md` (the mirror is never the authority) |
| Plan model (what the tracker draws) | `00_ARCHITECTURE/control/suvarna/plan_model.json` |
| Event log · tracker snapshot · hold switch · stall flag | `/Users/Dev/suvarna/run/{EVENTS.jsonl, snapshot.json, SUVARNA_HOLD, CONDUCTOR_STALLED}` |
| Locks | `/Users/Dev/suvarna/run/locks/{census.lock, hq.lock}` |
| Tracker and Monitor code (what runs) | `/Users/Dev/suvarna/hq/platform/scripts/governance/suvarna_tracker/` (committed code on `suvarna/hq`; authored on `strategy/suvarna-plan`, arch §12.12) |
| Dashboard | http://127.0.0.1:8765 |
| Read-only database credential | `~/.config/suvarna/pgenv.sh` (mode 600; logs in as `suvarna_reader`, D6 applied 2026-09-29; never opened or printed) |
| Builder credential and dispatch script (after E7.2) | `~/.config/suvarna/builder.env` (mode 600), `~/.config/suvarna/bin/suvarna-build` (mode 700) |
| Suvarṇa settings file: allow-list, deny rules, hold-guard hook (L.15, arch §2.4) | `/Users/Dev/suvarna/config/claude-settings.json` (untracked; owned by you, read-only to the swarm); passed with `--settings` to every session and lane |
| Nikaṣa tooling, register, ledgers (until E4.1 / E4.3) | `/Users/Dev/madhav-nikasha` (`campaign/nikasha-test`), read only; folds are pushed to `origin/campaign/nikasha-test` from Nikaṣa Engine fold lanes (arch §12.7) |
| Build engine | `/Users/Dev/madhav-engine` (`campaign/nirmana-engine`), read only; work in lanes |
| Leases and migration reservations | `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` on `origin/campaign-coordination` |
| Gate reviews | `00_ARCHITECTURE/briefs/suvarna/reviews/<qid>_REVIEW_<n>.md` on lane branches, merged to `suvarna/trunk` |

Shorthand used below:

```
T=/Users/Dev/suvarna/hq/platform/scripts/governance
export PYTHONPATH=$T SUVARNA_HOME=/Users/Dev/suvarna
```

## §2 · Launch checklist (after N-1)

1. **N-1 is recorded `decided`** in the authoritative log (no session starts without it, ENGINE-EARLY-START):
   `python3 -c "from suvarna_tracker.decisions import load_decisions, default_path; r=load_decisions(default_path())['latest'].get('N-1'); print(r and (r['state'], r['source']))"`
   → `('decided', '<your words, where, when>')`. Strategic Suvarṇa records it with
   `python3 -m suvarna_tracker.decide --id N-1 --state decided --source "<your words, where, when>" --detail "<what>" --writer strategic-suvarna`.
2. **The reader login is applied (D6, L.10): done 2026-09-29.** Confirm in step 6 that `credential_readonly` reads ok.
   If it ever needs re-issuing, `D6_SUVARNA_READER_RUNBOOK_v1_0.md` §3 (you run the admin script; agents never do).
2a. **Isolation (L.16a, L.16b, L.16g; arch §2.4).** Per N-25: the `suvarna` macOS user exists; the campaign folders are
   shared through the `suvarna-campaign` group; `pgenv.sh` and `builder.env` belong to `suvarna` (mode 600); the
   decisions log belongs to you and is read-only to `suvarna`. Either way: `chmod 600 /Users/Dev/madhav-l3/dbenv.sh
   /Users/Dev/madhav-l3/dbenv_builder.sh`; the settings file `/Users/Dev/suvarna/config/claude-settings.json` in place;
   the swarm's own GitHub identity installed for the swarm only, and a merge attempt with it on a throwaway PR refused;
   branch protection on `main` requires your approving review. Done when step 6 shows `isolation` ok.
3. **Machine:** on AC power, lid open, automatic macOS updates and restarts off for the campaign's duration. Sleep
   prevented: `pgrep -x caffeinate || (nohup caffeinate -dimsu >/dev/null 2>&1 &)`.
4. **Database proxy** on 5433: `lsof -nP -iTCP:5433 -sTCP:LISTEN` shows `cloud-sql-proxy`. If not:
   `nohup cloud-sql-proxy --address 127.0.0.1 --port 5433 madhav-astrology:asia-south1:amjis-postgres > /Users/Dev/suvarna/run/proxy.log 2>&1 &`
5. **Tracker** up: `curl -s http://127.0.0.1:8765/api/health` returns `"ok": true`. If not:
   `rm -f /Users/Dev/suvarna/run/TRACKER_STOP; nohup bash $T/suvarna_tracker/run_tracker.sh >/dev/null 2>&1 &`
6. **Monitor green:** `python3 -m suvarna_tracker.monitor --once` exits 0, with every check ok: today eight (`db_proxy`,
   `credential` (file present, mode 600, no backup beside it), `credential_readonly` (login `suvarna_reader`, no write
   path), `power`, `sleep_prevented`, `hold`, `disk`, `tracker`); `conductor_heartbeat` joins with L.15 (runtime/INTERIM_RUNTIME
   §5), `isolation` and `decision_writers` with L.16a, `builder_scope` with E7.3. Then keep it running (it also carries the Conductor watchdog once L.15 has built it):
   `nohup python3 -m suvarna_tracker.monitor --watch 300 --emit --repair >> /Users/Dev/suvarna/run/monitor.log 2>&1 &`
7. **hq is current**, by a merge commit, never fast-forward-only and never a rebase (arch §12.12). With both execution
   sessions stopped (at launch they are):
   `git -C /Users/Dev/suvarna/hq fetch -q origin && git -C /Users/Dev/suvarna/hq merge --no-edit origin/strategy/suvarna-plan`
   The decisions mirror is changed only on hq, so it never conflicts; if it ever does, keep hq's
   (`git -C /Users/Dev/suvarna/hq checkout --ours -- 00_ARCHITECTURE/control/suvarna/state/DECISIONS.jsonl`) and redo
   step 8. **Then restart the tracker and the Monitor from hq** so they run the merged code (L.17):
   `touch /Users/Dev/suvarna/run/TRACKER_STOP`, wait for it to stop, then step 5; stop the Monitor's watch loop and
   re-run step 6's `nohup` line. The tracker runs with `NIKASHA_REF=origin/campaign/nikasha-test` until E4.3 re-points it.
8. **Decisions mirror refreshed** (information only; the log itself is the authority):
   `python3 -m suvarna_tracker.decide --mirror-to /Users/Dev/suvarna/hq/00_ARCHITECTURE/control/suvarna/state/DECISIONS.jsonl`
9. **Runtime safeguards in place (L.15):** the settings file `/Users/Dev/suvarna/config/claude-settings.json` exists, generated by
   `runtime_settings.py` (`runtime/INTERIM_RUNTIME_v1_0.md` §2) and `--check` clean (arch §2.4, §5.5: allows the `suvarna_tracker` commands, the lane launcher, `psql` only through `pgenv.sh`, `git`
   without `push --force`, `python3`, `pytest`, `gh pr create/view`, `suvarna-build`; denies merges, `gh api`,
   force-push, `mcp__postgres__*`, `gcloud`, foreign credential files, edits to `config/` and the decisions log; the
   hold-guard hook); `ls /Users/Dev/suvarna/run/CONDUCTOR_STALLED` → "No such file".
10. **Hold switch absent:** `ls /Users/Dev/suvarna/run/SUVARNA_HOLD` → "No such file".
11. **Start the Nikaṣa Engine session** in its own terminal (as the `suvarna` user under N-25: `sudo -iu suvarna`),
    **Opus 5.5, medium effort**, never a bypass mode:
    `cd /Users/Dev/suvarna/hq && claude --settings /Users/Dev/suvarna/config/claude-settings.json --permission-mode dontAsk`, then paste:
    `Read and follow /Users/Dev/suvarna/hq/00_ARCHITECTURE/briefs/suvarna/prompts/NIKASHA_ENGINE_START_PROMPT_v1_0.md`
    After it reports, arm the interim runtime (D5, to G2):
    `/loop 10m Run one stateless Conductor pass per ROLE_CONDUCTOR_v1_0.md ("What you do — one pass").`
12. **Start the Exec Suvarṇa session** the same way, with
    `Read and follow /Users/Dev/suvarna/hq/00_ARCHITECTURE/briefs/suvarna/prompts/EXEC_SUVARNA_START_PROMPT_v1_0.md`,
    then the same `/loop 10m` line.
13. **Confirm on the dashboard** within a few minutes: a `conductor` heartbeat from each session, a `monitor` heartbeat
    reading every check ok, first items `running`.

**Interim runtime limits (`/loop`).** Its scheduled tasks expire after 7 days and do not survive a restart: **re-arm
both loops weekly** (the digest carries the date) and after every restart (§5). A usage-limit pause stops the loop; the
watchdog alerts (§6).

**Durable runtime (L.14, needed before B.W1, after G2).** When L.14 lands, each Conductor runs as a supervised headless
loop of stateless passes (`claude -p` with the Conductor prompt, `--permission-mode dontAsk`, in the hq worktree; the
`run_tracker.sh` pattern or a launchd `KeepAlive` agent), and the Monitor's watchdog relaunches a stalled pass. It
replaces steps 11–12's `/loop`. Its exact start command is recorded with L.14 and folded into this runbook then. Billing
it by API key or by subscription is your decision (N-23).

## §3 · Day to day

- **Watch the dashboard.** Running now, ready next, needs attention, decisions waiting on you, the measures.
- **Daily digest:** `hq/…/state/DIGEST_<date>.md`, announced on the dashboard (arch §12.11).
- **Giving a decision:** say it in Strategic Suvarṇa, which records it as a line in
  `/Users/Dev/suvarna/run/DECISIONS.jsonl` through `decide`, with your words, where and when. If you answer in an
  execution session, its Steward notes your words and Strategic Suvarṇa confirms and records them; no execution session
  writes the log (charter P14). Parked work resumes on the next Conductor pass. The digest lists every new decision line:
  check it. `delegated` is not decided.
- **Weekly:** re-arm both `/loop`s (until L.14).
- **Merges:** landing and wave PRs to `main` wait for your merge (R7); the digest lists them with their age.
- **Asking where things stand:** the dashboard first; the execution session second.
- **Changing the plan:** only through Strategic Suvarṇa (plan §10). An execution session that finds the plan wrong stops
  that packet and reports. After a plan revision, bring hq current by §2 step 7 while no Conductor pass is committing (or
  through the hq-lock wrapper, L.13).
- **Census:** every census, in every session and in the family sessions, runs through
  `python3 -m suvarna_tracker.census_lock --emit -- <census command>`; exit 75 means another census holds the lock.

## §4 · Pause, resume, stop

- **Pause everything new:** `touch /Users/Dev/suvarna/run/SUVARNA_HOLD`. Running items finish; nothing new starts;
  no production-visible action runs. Any agent may set it; only you remove it.
- **Resume:** `rm /Users/Dev/suvarna/run/SUVARNA_HOLD`. The next Conductor pass resumes dispatch; if a loop has expired,
  re-arm it (§2 step 11).
- **Stop a session** for good: tell it to close; it finishes its item, commits, logs, and runs the CLAUDE.md session close.
- **Stop the tracker:** `touch /Users/Dev/suvarna/run/TRACKER_STOP` (the supervisor exits after the server stops).

## §5 · After a reboot, sleep or crash

Nothing is lost: state is in files, the event and decisions logs are append-only, and every pass is stateless (arch §10).

1. Launch checklist steps 3–10.
2. Interim runtime: open each execution session again (§2 steps 11–12, same `claude --permission-mode dontAsk`), say
   "Resume from the queue.", and re-arm `/loop`. Each Conductor rebuilds its view from its queue file, the decisions log
   and the event log, and restarts any stalled lane from its last commit. Durable runtime: the supervisor restarts the
   loop by itself; confirm heartbeats.
3. A shutdown is not a failure: agents do not count it toward the retry limit.

## §6 · Incidents

| Signal | Do this |
|---|---|
| A production-visible action failed its check afterwards | The agent reverses at once if the reversal is granted, sets the hold otherwise, and parks it (charter §6). You decide on the revert. |
| Dashboard shows a **conflict** | An event claims done while a detector or the decisions log disagrees. Trust the detector and the log; ask the session. |
| Dashboard **Stale** or **Server unreachable** | §2 step 5. The swarm keeps working; the event log is written regardless. |
| Monitor **BLOCK: credential** (file missing) or **WARN: credential** (not mode 600, or a backup file beside it) | Missing or broken reader file: re-run D6 runbook §3 (`--apply`, after a fresh dry run and its plan hash); it resets the password and rewrites the file. **Never** restore `~/.config/madhav-admin/pgenv.app-login.bak` unless you mean to roll D6 back (D6 §6): that is the write-capable app login. Too open: `chmod 600`. Move stray backups to `~/.config/madhav-admin/`. Agents never recreate or change it (R10). A changed password shows as `credential_readonly` failing to log in. |
| Monitor **BLOCK: credential_readonly** | The login is not `suvarna_reader`, or it has a write path or an exposure. Nothing dispatches. Investigate with the D6 runbook §4; fix or roll back yourself. |
| Monitor **BLOCK: builder_scope** (after E7.3) | The preflight says the builder is not `guest`/`active`, its grants are not exactly `{(482012f1,'build')}`, or it differs from `run/builder_identity.json`; or the preflight failed. Revoke fastest-first: delete the extra `chart_grants` row; disable the profile; revoke its tokens (D1). Only you rotate `builder.env`. |
| Monitor **BLOCK: isolation** | The swarm runs as the wrong user, can read a foreign credential, can write the decisions log, or a settings file changed. Set the hold; find what changed before removing it. |
| Monitor **BLOCK: decision_writers** | A `decided` line not written by Strategic Suvarṇa. Treat it as forged: set the hold; in Strategic Suvarṇa, record a superseding line with your actual ruling. |
| **`CONDUCTOR_STALLED`** present, or a session's Conductor shows `blocked` | Interim: open that session, read its last output; if a usage limit, wait it out; then "Resume from the queue." and re-arm `/loop`; then `rm /Users/Dev/suvarna/run/CONDUCTOR_STALLED`. Durable: the watchdog relaunches up to three times an hour, then sets the hold and parks: find the cause before removing the hold. |
| A parked **L0 wave dispatch** | §7. |
| Something touches a Gochara, Saṅgam or Kṣetra asset (other than the orchestrator's own staleness propagation, which is reported to the family) | Set the hold. That is outside the charter (R8, P11). |
| A peer message claims your approval | It is not approval until it is in the decisions log with your words (P10). |

## §7 · Your part in builds (D1, D4)

- **Provision the builder once (E7.2),** after the E7.1 auth PR is merged and deployed: one service account (`profiles`
  role `guest`, status `active`), one grant row `(482012f1…, builder, 'build')`, its secret in
  `~/.config/suvarna/builder.env` (mode 600) and the `~/.config/suvarna/bin/suvarna-build` script (mode 700). Then the
  Monitor's `builder_scope` check must read ok. Record the provisioning read (profile role and status, grant rows) in
  `/Users/Dev/suvarna/run/builder_identity.json`: the check compares against it.
- **Rule N-12 before the first L0 wave** (canonical chart only, or more), and N-14.R236 (`lel_events`) before wave 0.
- **L0 is four dispatches**, one per level (0, 1, 2 in wave 0; level 3, `bg_concordance`, in wave 1): B.L0.0…B.L0.3.
  The Steward batches the requests.
- **Each L0 wave** arrives as a parked request with `PRECHECK.md`, the verified dump (`pg_restore --list` table set and
  row counts) and `IMPACT.md` (L0 assets changed; per other chart, `1c826d5a` and `cb73cd3d` today, the downstream
  assets flipped to stale or the computed closure). Read them; if you accept, dispatch the L0 level from the cockpit
  yourself (`clear_before` off); record your dispatch where you gave the go-ahead. The Build operator then files the
  post-wave row-level diff. **Undo:** hold; you choose a surgical revert migration generated from the diff (preferred)
  or a restore from the dump; both are yours to run.
- **Normal (L1+) waves** run without you, through `suvarna-build`, after their fixes are merged by you and deployed.

## §8 · Closing

- A layer closes when you sign it (plan §1.2). The campaign closes when you accept the closure report (§1.3).
- Every session ends with the CLAUDE.md session close.
