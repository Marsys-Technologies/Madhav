---
artifact: OVERNIGHT_TMUX_RUNBOOK
canonical_id: OVERNIGHT_TMUX_RUNBOOK
version: 1.0
status: CURRENT — companion to PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md
role: >
  The launch and survival mechanics for running the combined P3+P4 overnight autonomous
  run inside tmux on the native's machine, with no sleep and no idle time. The charter
  says WHAT the run does; this runbook says HOW it stays alive doing it.
---

# Overnight tmux runbook — P3 + P4

## 1. What you are launching

One tmux session, **`prp-night`**, four windows:

| Window | Runs | Purpose |
|---|---|---|
| `conductor` | `caffeinate -dims claude --model opus --dangerously-skip-permissions "<boot>"` | The run itself. `caffeinate -dims` blocks display, idle, disk, and system sleep for as long as the conductor process lives — the machine cannot sleep out from under the run. |
| `sentinel` | `sentinel.sh` | The anti-idle loop. Captures the conductor pane every 5 min and hashes the tail. 15 min of visible stillness → types a WATCHDOG NUDGE into the conductor. Dead pane → respawns Claude Code with `--continue` (resumes its own transcript) and issues a CRASH-RESUME orientation line. It restores motion; it never decides. |
| `pulse` | `pulse.sh` | Agent-free external health record, every 30 min: `origin/main` HEAD, last 5 CI runs, production HTTP status (if `PROD_URL` is set), disk headroom → `logs/pulse.log`. If the morning report and the pulse log disagree, the pulse log wins. |
| `logs` | `tail -F` | Live view of `sentinel.log` + `pulse.log`. |

`--dangerously-skip-permissions` is what makes the run genuinely autonomous — no
permission prompt can stall the night. That is exactly the authority §0 of the charter
grants, and exactly why the charter's hard-nevers, the surrogate's MUST-PARK list, and
the STOP conditions exist: the guardrails are in the charter, not in prompts.

## 2. One-time setup (you, tonight, ~3 minutes)

1. Place the kit **outside the repo** (X-4 — the launcher refuses to run from inside it):

   ```bash
   mkdir -p ~/pariprashna_night && cd ~/pariprashna_night
   # put here: overnight_p3p4.sh, PARIPRASHNA_P3_P4_OVERNIGHT_AUTONOMOUS_RUN_v2_0.md,
   #           CONDUCTOR_BOOT_PROMPT.md, OVERNIGHT_TMUX_RUNBOOK_v1_0.md
   chmod +x overnight_p3p4.sh
   ```

2. Confirm the prerequisites the launcher will check anyway: `tmux`, `claude`, `git`,
   `gh` (authed: `gh auth status`), and that the repo at
   `/Users/Dev/Vibe-Coding/Apps/Madhav` can `git fetch origin`.

3. Optional but recommended — export the production URL so the pulse window probes it:

   ```bash
   export PROD_URL="https://<amjis-web Cloud Run URL>"
   ```

4. Launch, watch the first minutes, then walk away:

   ```bash
   bash overnight_p3p4.sh
   tmux attach -t prp-night      # watch the run-open sequence begin
   # Ctrl-b d to detach — detaching stops nothing
   ```

   Watch until the conductor has: fetched, read the lease log, announced the run in
   campaign-coordination, and opened Wave P3-1 + the P4 fillers. That is your signal the
   night is properly underway.

## 3. During the night (nothing — but if you happen to wake)

```bash
bash overnight_p3p4.sh status     # one-shot: windows, last pulse, conductor tail
tmux attach -t prp-night          # full view; Ctrl-b 0..3 switches windows; Ctrl-b d leaves
```

Never type into the conductor window casually — anything you type is a native directive
and the run will treat it as one. The one directive that is always safe:

```bash
bash overnight_p3p4.sh stop       # asks the conductor for the charter §7 clean halt
```

## 4. In the morning

1. `tmux attach -t prp-night` — the conductor window's last screen states the end state.
2. Read, in this order: the **morning report**
   (`00_ARCHITECTURE/briefs/pariprashna_swarm/OVERNIGHT_RUN_REPORT_2026-08-22.md`, on
   `main` via the run's PRs) — its first line says whether THE FLIP executed, its second
   whether THE DELETION executed · the **decision ledger** (everything decided in your
   name, each entry with its falsifier) · the **pulse log** (`logs/pulse.log` — the
   agent-free cross-check).
3. Your asynchronous verdicts, whenever you choose: review the DELEGATED-OVERNIGHT
   decisions; AC-15 remains open per the seam-compression record — a NO from your week
   of use spawns a remediation wave against the then-current state, exactly as always
   ruled.
4. Tear down: `tmux kill-session -t prp-night` (only after reading — the session costs
   nothing while detached, and the scrollback is evidence).

## 5. Failure modes this design already covers

- **Mac tries to sleep** → `caffeinate -dims` holds it awake while the conductor lives.
- **Conductor goes quiet** → sentinel nudge at ~15 min; unanswered nudges escalate
  inside the run (charter §11.3 → DIAGNOSTICIAN).
- **Conductor process dies** → sentinel respawns with `--continue`; the charter's
  crash-resume protocol re-orients from derived state (fetch → leases → tracker →
  budget-vs-actual → prod revision), never from memory.
- **Terminal/SSH disconnects** → tmux is the terminal; nothing was attached to your TTY.
- **API throttling** → conductor scales concurrency down on 429s and logs N (charter §2).
- **Budget exhaustion** → subtotal park (one phase) or clean STOP at $400 (charter §7).
- **The other campaign lands mid-night** → per-merge lease re-reads, separate narrow
  scopes announced at run open, census re-check before any deletion (charter §10.3).
- **Genuinely stuck** → STOP conditions produce end state 6: production stable, rollback
  pinned, resume state written — a halt you can resume tomorrow, not a mess.

*End OVERNIGHT_TMUX_RUNBOOK v1.0.*
