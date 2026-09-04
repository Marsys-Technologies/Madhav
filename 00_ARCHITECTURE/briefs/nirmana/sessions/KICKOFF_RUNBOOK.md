# v2.1 KICKOFF RUNBOOK — six terminals, then sleep

## Launch order (order matters only for the first two)

Open six terminals. In each:

```bash
cd /Users/Dev/Vibe-Coding/Apps/Madhav
claude --dangerously-skip-permissions
```

Then paste, per terminal, the ENTIRE contents of one file from
`00_ARCHITECTURE/briefs/nirmana/sessions/`:

1. `PROMPT_CONDUCTOR.md`  ← first (it opens the coordination issue and lands the governance PR)
2. `PROMPT_L2.md`         ← second (critical path; its W3 starts immediately)
3. `PROMPT_L1.md`
4. `PROMPT_L3.md`
5. `PROMPT_L4.md`
6. `PROMPT_L5.md`

The existing **L0 session keeps running untouched** — it finishes L0 and ends. Seven total.

## Notes for the night

- Permission bypass is required in every terminal — a permission prompt is a human gate.
- Sessions never ask you anything (charter C3). Questions become `nirmana-adjudication`
  issues; the Conductor rules them.
- Emergency stop for everything: `touch /Users/Dev/Vibe-Coding/Apps/Madhav/NIRMANA_HOLD`
- Morning routine: read root `CAMPAIGN_STATE.md` + the Conductor's coordination issue. If any
  session died overnight, its lane simply paused — re-paste that one prompt into a fresh
  terminal; charter C9 makes every prompt safely re-pasteable at any moment.
- Optional resilience wrapper (auto-relaunch a session if its process exits) — use per
  terminal instead of plain launch if you prefer:
  ```bash
  cd /Users/Dev/Vibe-Coding/Apps/Madhav
  while [ ! -f NIRMANA_HOLD ]; do
    claude --dangerously-skip-permissions "$(cat 00_ARCHITECTURE/briefs/nirmana/sessions/PROMPT_L2.md)"
    sleep 60
  done
  ```
  (C9 resumability makes restarts safe; the state file carries continuity.)

## What tomorrow's evidence should show

- Coordination issue live, slot claims flowing, ≤3 concurrent runs at all times.
- L0 frozen 40/40 + its close report; L1 executing behind it; L2's W3 PRs through the queue;
  6 cross-layer canaries (ga_positions · ka_gochara_resonance · ka_graha_sancara ·
  lel_events · mi_jivanaghatana · mi_vistara) frozen or in W5.
- Zero adjudication issues waiting > a few hours; zero questions addressed to you.
