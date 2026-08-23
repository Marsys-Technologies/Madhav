# NIRMĀṆA AUTONOMOUS FLEET — RUNBOOK v1.0

Operator: Abhisek Mohanty. Campaign: Nirmāṇa elevation, chart `482012f1`, plan v4.2.
Nothing here is required of you once the fleet is up. This is how to start it, watch it if you
want to, and answer the only thing it will ever ask you for.

---

## 0 · One-time setup

```bash
export NIRMANA_REPO=/Users/Dev/Vibe-Coding/Apps/Madhav
cd "$NIRMANA_REPO"

# 1. Campaign branch — the fleet never writes to main (charter H2)
git checkout -b campaign/nirmana-autonomous

# 2. Environment the orchestrator needs (same vars your local dispatch already uses)
export DATABASE_URL='postgres://…'          # production, read/write
export BUILD_EXECUTOR=local                  # or unset to dispatch to Cloud Run
export GCP_PROJECT=…                         # only if dispatching to Cloud Run

# 3. Set the spend ceilings. Preflight REFUSES to launch while these are null —
#    an unset ceiling is a Reserved Power, not a default.
$EDITOR 00_ARCHITECTURE/autonomy/state/CAMPAIGN_STATE.json
#    → ceilings.tokens_campaign  and  ceilings.tokens_per_rung

# 4. Preflight
./00_ARCHITECTURE/autonomy/bin/preflight.sh
```

Preflight checks the repo, the plan version, the charter, the CLI, tmux, the venv,
`DATABASE_URL`, the campaign branch, **the 2026-08-23 snapshot** (the only recovery path for the
v1 gochara corpus, I2), and the ceilings. It refuses to launch on any failure. That refusal is
the design working.

## 1 · Launch

```bash
./00_ARCHITECTURE/autonomy/bin/nirmana-up.sh --dry-run    # see what it will do
./00_ARCHITECTURE/autonomy/bin/nirmana-up.sh              # do it
tmux attach -t nirmana
```

Six windows: `ops` (live heartbeat + parked tail) · `adhikarin` · `verifier` · `monitor` ·
`scribe` · `conductor` (active).

**Then set effort to high in the three Opus windows** — `adhikarin`, `verifier`, `conductor`:
focus the window, type `/model`, choose effort **high**. The launcher cannot do this for you;
CLI flags for effort vary by version, so it is a deliberate manual step. Verify with `/model`
that each reads Opus + high before walking away.

## 2 · tmux navigation

| Key | Does |
|---|---|
| `Ctrl-b d` | detach — **the fleet keeps running** |
| `tmux attach -t nirmana` | come back |
| `Ctrl-b w` | window list |
| `Ctrl-b n` / `p` | next / previous window |
| `Ctrl-b [` | scroll back (`q` to exit scroll) |
| `tmux kill-session -t nirmana` | stop the fleet |

Detaching is the normal state. The fleet is designed to be left alone for days.

## 3 · Watching, if you want to

```bash
A=$NIRMANA_REPO/00_ARCHITECTURE/autonomy/state
tail -f $A/DECISIONS.jsonl     # every ruling ADHIKĀRIN makes, with evidence
tail -f $A/VERDICTS.jsonl      # every verification PARĪKṢAKA returns
cat    $A/PARKED.jsonl         # the only thing that wants you
cat    $A/CAMPAIGN_STATE.json  # where the campaign is right now
ls     $A/DIGEST-*.md          # LEKHAKA's rung-boundary digests
```

## 4 · The only thing you have to do

Read `PARKED.jsonl` when you feel like it. Each entry is a question only you can settle, with
the evidence already gathered, the options laid out, ADHIKĀRIN's recommendation, and the work
around it already done. Answer by typing in the `conductor` window — it is interactive, your
word outranks the charter, and the ruling propagates to the whole fleet through
`DECISIONS.jsonl`.

Parked items never block the campaign. A full parked file and a healthy campaign are the
expected steady state.

## 5 · Intervening

Type in the `conductor` window at any time. Questions get answered from the fullest view of the
campaign; instructions are recorded as native rulings and inherited by every agent. You can
redirect, re-scope, or stop without breaking anything — all state is on disk.

## 6 · If something goes wrong

| Symptom | What it means | Do |
|---|---|---|
| A window shows a dead prompt | agent exited | PRAHARĪ restarts it within 30 min; or relaunch that window yourself from `bin/nirmana-up.sh` |
| `monitor` window dead | the watchdog died | SŪTRADHĀRA restarts it; if both are dead, `tmux kill-session` and relaunch — state is on disk |
| Nothing in HEARTBEAT for >30 min across all agents | the fleet is down | relaunch; the campaign reconstructs its position from `CAMPAIGN_STATE.json` + ledgers |
| PARKED growing fast | the campaign is hitting your reserved powers | read them; several may be pre-authorizable in one sitting |
| A build has been running for hours | probably normal — heavies run up to ~30 h | check `RUN_LEDGER.jsonl`; PRAHARĪ reaps genuinely stalled runs |

**Full stop:** `tmux kill-session -t nirmana`. Nothing is lost; every agent is restartable from
the ledgers alone (§18.8).

## 7 · What the fleet will never do

From the charter's hard prohibitions — no write to `main`, no history rewrite, no `DROP`/
`TRUNCATE` on the v1 gochara corpus or any snapshot, no disabling a gate to make something
pass, no `lit`/`complete`/`frozen` without its detector's verdict, no editing an applied
migration, no fabricated rows or verdicts, and no agent certifying its own work.

If you ever see one of those happen, that is a defect worth stopping the campaign for.
