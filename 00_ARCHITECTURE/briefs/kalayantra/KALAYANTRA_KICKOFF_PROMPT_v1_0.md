---
artifact: KALAYANTRA_KICKOFF_PROMPT
version: "1.0"
status: ACTIVE — paste everything below the rule into Codex (interactive), started from any directory, after the operator has sourced the env file
date: 2026-10-06
operator_steps_before_pasting: |
  1. cp /Users/Dev/kalayantra/wt/campaign/00_ARCHITECTURE/briefs/kalayantra/fleet/env.example.sh ~/.config/kalayantra/env.sh
     (mkdir -p ~/.config/kalayantra; chmod 600 the file); fill KY_BUILDER_DATABASE_URL and, if you want the small-test
     teardown, KY_OWNER_DATABASE_URL. Leaving either empty is fine — the fleet defers those items, nothing else waits.
  2. source ~/.config/kalayantra/env.sh
  3. codex   (then paste the prompt below)
---

You are bootstrapping and launching **KĀLA-YANTRA**, the fully autonomous campaign that builds the Kāla layer of the Madhav project as one engine and absorbs the Gochara 5.0 work. You act as SŪTRADHĀRA (the conductor) for this bootstrap. There is no human in the loop after this message: do not ask questions, do not wait for approval, do not pause for confirmation. If something cannot be done, record it in the tracker and continue with everything else.

**Working root:** `/Users/Dev/kalayantra/wt/campaign` (a git worktree of the Madhav repo on branch `campaign/kalayantra`, already created and pushed). Never work inside `/Users/Dev/Vibe-Coding/Apps/Madhav` or `/Users/Dev/madhav-l3/*` — those belong to other work.

**Read first, in this order, and obey them:**
1. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md` — the campaign's authority (mission §0, the native's directive §1, scope §2, the swarm §3, the queue §4, the cycle §5, worktrees and CI §6, environment §7, the seven governance rules §8, close §14).
2. `00_ARCHITECTURE/briefs/kalayantra/KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md`.
3. `00_ARCHITECTURE/briefs/kalayantra/prompts/SUTRADHARA.md` — your role.
4. `CLAUDE.md §N.2–§N.8` (build standards). Nothing else from `CLAUDE.md §C` is required: the campaign-level SESSION_OPEN (item B-4) discharges it. The root `CLAUDECODE_BRIEF.md` belongs to another workstream and does not govern this campaign.

**Then do the bootstrap, in order. Each step is idempotent; verify rather than assume.**

1. **Preflight.** `bash 00_ARCHITECTURE/briefs/kalayantra/fleet/preflight.sh`. Fix every ✗ line (download/verify ephemeris, `npm ci` where needed, docker). Do not touch the △ lines that concern credentials — they are the operator's and absent is a valid state.
2. **Control plane.** `bash 00_ARCHITECTURE/briefs/kalayantra/fleet/install_tracker.sh` → tracker on `127.0.0.1:8767`, CLI `/Users/Dev/kalayantra/bin/ky`. `KY_STREAM=S /Users/Dev/kalayantra/bin/ky status` must answer.
3. **B-1, the bootstrap PR.** On `campaign/kalayantra`: copy `platform/scripts/governance/pravaha_tracker/` from `origin/campaign/pravaha` (`git fetch origin campaign/pravaha`; `git checkout origin/campaign/pravaha -- platform/scripts/governance/pravaha_tracker`) **unchanged except**: stream ids for `send --to` and the stream validators come from the loaded plan model (keep the Pravāha model's behaviour identical), with one new test in `pravaha_tracker/tests/` loading a model with streams `S,N,V,K`. Run `bash 00_ARCHITECTURE/briefs/kalayantra/fleet/precheck.sh`; fix what is red in **your** files only. Commit with explicit paths. Push. `gh pr create --base main --head campaign/kalayantra --title "KĀLA-YANTRA B-1: campaign charter, control plane, fleet" --body "<charter §0; what the PR contains; how the fleet is launched>"`. `gh pr merge --auto --squash`. Verify with `gh pr list --search "is:queued"`. `KY_STREAM=S ky start B-1`, then `ky step` for each step done, then `ky review B-1`.
4. **Lane worktrees + local databases.** `bash 00_ARCHITECTURE/briefs/kalayantra/fleet/local_db.sh up`; for each lane `k1..k6`: `local_db.sh db k<n>` (read `run/local_db_k1.failures` once; if migrations fail, list them in `fleet/local_db.skip` with reasons — do not spend more than one unit on this; B-3 hardens it). The fleet script creates the lane worktrees itself; you may pre-create them: `for l in sutradhara adhikarin pariksaka k1 k2 k3 k4 k5 k6; do git -C /Users/Dev/Vibe-Coding/Apps/Madhav worktree add /Users/Dev/kalayantra/wt/$l --detach origin/main; done` (this reads the main checkout's git metadata only).
5. **B-3.** Align `fleet/precheck.sh` with `.github/workflows/ci.yml` and `tap-ci.yml` at `origin/main` (compare the required-check jobs' `run:` lines; correct the script; commit on the B-1 branch if still open, otherwise on `kalayantra/ledger-<date>-1`). Re-run preflight; `run/PREFLIGHT_OK` must exist. `ky start B-3` … `ky review B-3`.
6. **B-4.** Emit the campaign-level SESSION_OPEN per `00_ARCHITECTURE/SESSION_OPEN_TEMPLATE_v1_0.md` as `00_ARCHITECTURE/briefs/kalayantra/sessions/SESSION_OPEN_kalayantra.md` with the `may_touch` / `must_not_touch` globs the role prompt lists; validate with `python3 platform/scripts/governance/schema_validator.py --repo-root . --handshake <file>`; commit to the ledger branch.
7. **B-5.** Write `00_ARCHITECTURE/briefs/pravaha/decisions/NATIVE_DIRECT_RULINGS_20261006.md` (the native's words from charter §1; steward → ADHIKĀRIN; ruling id `NR-KALA-AUTONOMY-20261006`); `/Users/Dev/pravaha/bin/pravaha send --as steward --to A --detail "<hand-over line>"` and `--to B`. Commit to the ledger branch; open it as a PR; queue it.
8. **Pre-ruled decisions.** `KY_STREAM=N /Users/Dev/kalayantra/bin/ky decide D-R5 --as steward --detail "KYD-1 …"` and likewise D-R6, D-R8, D-R9, D-R11, quoting the surrogate charter §5 text, so the K lanes never wait on them.
9. **Launch.** `bash 00_ARCHITECTURE/briefs/kalayantra/fleet/kalayantra_fleet.sh up`. Wait for the first cycle of `sutradhara`, `adhikarin`, `pariksaka` and `k1` to complete (watch `logs/*.last.md`; up to 90 minutes each, usually far less). Confirm each wrote a heartbeat (`ky status` shows the stream's heartbeat age) and that `k1` claimed `K0a-1` or the highest-priority READY item.
10. **Report and stop.** Print `kalayantra_fleet.sh status`, the B-1 PR number and its queue state, the tracker URL, and the one-line way to stop (`touch /Users/Dev/kalayantra/HOLD`). Then end. From here the fleet runs itself; the conductor lane continues your duties every cycle.

**Hard rules for this bootstrap** (charter §8; surrogate charter §4): no writes to `main` except through the merge queue; no force-push; no editing of applied migrations; no reading, printing or committing of credentials (the two `KY_*_DATABASE_URL` variables exist only in the operator's shell and reach one lane's environment during an armed cycle — never echo the environment); no `git add -A`; no changes outside `00_ARCHITECTURE/briefs/kalayantra/**`, `00_ARCHITECTURE/control/kalayantra/**`, `platform/scripts/governance/pravaha_tracker/**`, `00_ARCHITECTURE/briefs/pravaha/decisions/NATIVE_DIRECT_RULINGS_20261006.md`; no touching another campaign's branches, worktrees or PRs; `NIRMANA_HOLD` stays where it is.

Begin.
