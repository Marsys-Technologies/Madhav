# KĀLA-YANTRA hand-over runbook — 2026-10-08 morning (Codex → Claude, v2.0 rules)

**Written for:** the conductor session (Claude, owner present). Each step names its check; stop at a failed check.

## Stage 0 — take the conductor seat (~15 min)
1. `cd /Users/Dev/kalayantra; export PATH=$PWD/bin:$PATH KY_STREAM=S KY_LANE=sutradhara` · `ky status` (note done/running/ready).
2. Pause intake: `touch run/STOP_sutradhara` (already present); tell the Codex conductor chat "stop after this cycle"; `ky send --to K --detail "hand-over: finish the current step, no new claims for 20 minutes"`; same `--to V`, `--to N`.
3. Merge the amendment PR (CI only, it is docs/prompts/tracker/fleet): `gh pr merge <amendment PR> --auto`; wait for merge; `cd wt/campaign && git fetch -q origin main && git checkout -q --detach origin/main` (the live checkout follows main; discard the 9 pre-amendment working-tree edits first with `git checkout -- .` — they are all merged already).
4. Reinstall the tracker snapshot: `bash wt/campaign/00_ARCHITECTURE/briefs/kalayantra/fleet/install_tracker.sh --gov wt/campaign/platform/scripts/governance` → `curl -s 127.0.0.1:8767/api/health` ok, `ky status` answers.
5. Apply the model regrouping against the LIVE events: `python3 -I wt/campaign/00_ARCHITECTURE/briefs/kalayantra/fleet/regroup_model_v2.py wt/campaign/00_ARCHITECTURE/control/kalayantra/plan_model.json run/EVENTS.jsonl /tmp/pm_v2.json` → read the summary → copy over the model on a branch `kalayantra/model-v2-regroup`, PR, merge (CI only), fast-forward the checkout; `ky status` shows ~142 items, no `unmeasured`.
6. Fleet snapshot: `rsync -a --delete wt/campaign/00_ARCHITECTURE/briefs/kalayantra/fleet/ fleet_live/`.
7. Resume: `rm run/STOP_k* run/STOP_v* run/STOP_adhikarin`; keep `run/STOP_sutradhara`. Lanes pick up prompts v2 on their next cycle. Check: first builder cycle reads the amendment (log mentions `--item`); verifier cycle issues no full-suite rerun.

## Stage 1 — first two lanes on Claude (watch three cycles each)
1. In `~/.config/kalayantra/fleet.env` add: `export KY_AGENT_k8=claude; export KY_AGENT_v3=claude; export KY_CLAUDE_MODEL_WORKER=sonnet; export KY_CLAUDE_MODEL_CONTROL=opus`.
2. Restart just those lanes: `touch run/STOP_k8 run/STOP_v3`; wait for their loops to exit (`pgrep -f "lane k8"` empty); `source ~/.config/kalayantra/fleet.env; KY_INTERACTIVE_CONDUCTOR=1 bash fleet_live/kalayantra_fleet.sh up` (locks dedupe the running lanes; `up` starts the stopped ones with the new env).
3. Check per cycle (`logs/k8.<n>.log`, `logs/v3.<n>.log`): the system event shows `mcp_servers: []`, the model is `claude-*`, no credential-like text (`grep -iE 'postgres(ql)?://[^ ]*:[^ ]*@' logs/k8.*.log` empty), the cycle ends with a summary line, `ky` calls succeed, one real item claimed / one real verdict.
4. Way back: remove the two `KY_AGENT_*` lines, STOP and restart the two lanes.

## Stage 2 — the rest, one lane per hour at item boundaries
`KY_AGENT_k1..k7=claude`, then `v1`, `v2`, then `adhikarin` last (it holds rulings). Same STOP → wait → `up` per lane. When every lane runs Claude: `export KY_AGENT=claude` and drop the per-lane lines.

## Stage 3 — operate from this session
Duties: `prompts/SUTRADHARA.md` v2 (queue sweep incl. CI-only PRs; completion sweep; pacing; one-line decisions; model writer for real items only; fleet defects fixed directly; `run/DIGEST.md`). Watch daily: lead time per item, Kāla items done/day, rejection reasons, chatter ratio, built ÷ all builder cycles. Target after one day: lead time ≤ 2 h, ≥ 15 Kāla items/day.

## Checks that something is wrong
Builders idle with READY > 0 → pacing or claim rule; verifier rejections citing hash/snapshot/environment → prompt not loaded (check the cycle prompt names the amendment); a lane's cycle > 3 h → cap hit, claim resumes; `ky done` refused "deployment" → no `workflow_run` deploy yet (wait one deploy) or Trap 103 (dispatch-only deploys).
