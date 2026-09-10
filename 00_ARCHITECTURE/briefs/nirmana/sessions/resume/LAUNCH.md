# NIRMĀṆA v2.2 — RESUME LAUNCH RUNBOOK

Seven terminals. **Use the wrapper, not a bare `claude`** — that is the whole point of this revision.

## Why v2.2 exists

Four of seven lanes died overnight (L2 silent 4h05m, L5 3h42m, L4 3h39m, L3 2h57m). The CLI process
ended and nothing restarted it. Meanwhile the merge queue kept draining branches those lanes had
pushed hours earlier, so the campaign **looked** busy while its ledger sat frozen at 29/128 with
**no campaign event for five and a half hours**.

Three fixes, all baked into the prompts:

1. **A self-healing wrapper** — the process is relaunched 30s after any exit, and §R1 resumes from
   the session's own state file. Ending a turn stops being fatal.
2. **A no-idle ladder (§R2)** — an explicit 8-step priority order, with *"blocked on the merge queue
   is NOT idle"* stated outright, since steps 5–7 never need the queue.
3. **Heartbeat measured at the PUSH (§R3)** — not at merges, which is what disguised the deaths.

## Launch — one per terminal

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
while [ ! -f NIRMANA_HOLD ]; do
  claude --dangerously-skip-permissions \
    "$(cat 00_ARCHITECTURE/briefs/nirmana/sessions/resume/RESUME_CONDUCTOR.md)"
  echo "[$(date -u +%FT%TZ)] session exited; relaunching in 30s" >&2
  sleep 30
done
```

Swap the filename per terminal. **Order matters — launch top to bottom:**

| # | file | why this order |
|---|---|---|
| 1 | `RESUME_CONDUCTOR.md` | rules the adjudication backlog; triage-first is its §C1 |
| 2 | `RESUME_L2.md` | critical path — owes the `_idempotency.py` fix and deterministic `signal_id`; the cascade ordering is built around its dispatch |
| 3 | `RESUME_L1.md` | owns **#1736**, the evidence spine — until it merges no L1–L5 asset can record a W2 acceptance and the ledger cannot move |
| 4 | `RESUME_L5.md` | has a granted ruling it never saw (#1787) and a DIRTY PR |
| 5 | `RESUME_L4.md` | DIRTY PR; deterministic `anchor_id` still unlanded, so D-CND-04's hold stands |
| 6 | `RESUME_L3.md` | its CI blocker is fixed; **L2's dispatch waits on its answer to #1770** |
| 7 | `RESUME_L0.md` | already alive and self-recovered — relaunch under the wrapper so it stays that way |

## For the night

* **Emergency stop, everything:** `touch /Users/Dev/Vibe-Coding/Apps/Madhav/NIRMANA_HOLD`
  The wrapper checks it before each relaunch, and every session checks it at each loop top.
* **Sessions never ask you anything** (charter C3). Questions become `nirmana-adjudication` issues;
  the Conductor rules them. If the Conductor stalls, sessions are now instructed to escalate on
  #1713 and say so by name.
* **Morning check, in one command:**
  ```bash
  gh issue view 1713 --comments | tail -80
  ```
  Then last-push-per-lane (the Conductor posts this every loop, and §C2 of its prompt has the query).

## What "working" should look like by morning

* Every lane pushing at least every ~20 minutes (§R3 heartbeat).
* **#1781 (WP-6) and #1736 (evidence spine) merged and deployed** — together they lift the
  destructive-dispatch hold *and* make a non-L0 W2 acceptance possible. **Until both land, the
  29/128 number cannot move except by L0.**
* The first non-L0 capsule: `ga_positions` is the intended canary — ancestor-clear, and blocked only
  on the spine.
* Zero adjudication issues unruled for more than one loop.
