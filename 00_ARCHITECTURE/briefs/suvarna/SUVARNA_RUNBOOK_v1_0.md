---
artifact: SUVARNA_RUNBOOK
canonical_id: SUVARNA_RUNBOOK
version: "1.3"
status: "PRE-FINAL v1.5 — for the parallel independent reviews (GPT-6 Astra, Kimi K3; N-30); then reconciled by Strategic Suvarṇa into the final set; then N-1"
produced_on: 2026-09-29
produced_in: session "Strategic Suvarṇa"
companion_of: "SUVARNA_EXECUTION_ARCHITECTURE_v1_0.md v1.5, SUVARNA_AUTONOMY_CHARTER_v1_0.md v1.5, NATIVE_SETUP_v1_0.md v1.0"
changelog:
  - "1.3 (2026-09-30, plan set v1.5): written for Strategic Suvarṇa and the swarm, not the native (N-28); the native's part is NATIVE_SETUP_v1_0.md only. Launch is setup verification (NS_VERIFY), the launch gates LG.1–LG.10 and the durable services (N-34; no /loop, no weekly re-arm). Paths: authority/ for decisions and holds, control/ for the tools (N-35, N-37). Merges through merge_gate (N-38). Holds per the ledger; the native's veto (N-35). L0 dispatches by the builder through the broker, no dump (N-29, N-31). Incidents re-owned to Strategic Suvarṇa. Monitor stage matrix (Astra F3)."
  - "1.2.1 (2026-09-30, review pass 3): isolation warn until N-25; builder_scope warn until E7.2; allow-list forms; census_run; N-27."
  - "1.2 (2026-09-29, review pass 2): D6 applied; tools from hq; isolation launch steps; settings file passed with --settings; /loop 10m; decisions only in Strategic Suvarṇa."
  - "1.1 (2026-09-29): launch checklist rebuilt around the decisions log, D6, the allow-list and the watchdog."
  - "1.0 (2026-09-29): first draft."
---

# Suvarṇa — runbook

How the campaign is launched, run, held and recovered. **Readers:** Strategic Suvarṇa (SS) and the swarm. The native's
only part is `NATIVE_SETUP_v1_0.md` and the veto (§4).

## §1 · Where things live

| What | Where |
|---|---|
| Campaign home | `/Users/Dev/suvarna/` (`.repo`, `hq`, `trunk`, `lanes`, `evidence`, `run` — the swarm's; `authority`, `config`, `control` — native-owned; `broker` — `_suvarnabuild`'s) |
| Decisions log (authoritative) | `authority/DECISIONS.jsonl`, written only by SS through `decide` (typed outcome, revision, rationale) |
| Holds · hold clears | `authority/HOLDS.jsonl` (the swarm may append) · `authority/HOLD_CLEARS.jsonl` (SS; native holds only by the native) |
| Tools that run (tracker, Monitor, hook, merge gate, gate evaluator, broker) | `control/platform/scripts/governance/suvarna_tracker/` at the pinned control release tag |
| Settings file | `config/claude-settings.json` (passed with `--settings` to every session, pass and lane) |
| Queues · digests · decisions mirror | `hq/00_ARCHITECTURE/control/suvarna/state/` |
| Events · snapshot · locks · claims · parks | `run/{EVENTS.jsonl, snapshot.json, locks/, claims/, parks/}` |
| Services | launchd: `com.marsys.suvarna.{tracker,monitor,runner.engine,runner.exec}` (user `suvarna`); `com.marsys.suvarna.strategic` (the native's account, SS) |
| Dashboard | http://127.0.0.1:8765 (Pravāha's own: http://127.0.0.1:8766) |
| Reader credential · Claude token (swarm) | `/Users/suvarna/.config/suvarna/{pgenv.sh, claude_oauth.env}` (mode 600; never opened or printed) |
| Builder credential | `broker/builder.env` (`_suvarnabuild` only), used only through `~/.config/suvarna/bin/suvarna-build` |
| Leases, migration reservations, notices | `00_ARCHITECTURE/briefs/CAMPAIGN_COORDINATION.md` on `origin/campaign-coordination` |

Shorthand: `T=/Users/Dev/suvarna/control/platform/scripts/governance; export PYTHONPATH=$T SUVARNA_HOME=/Users/Dev/suvarna`.

## §2 · Launch (N-30 → N-1)

1. **SS prepares NS.0** (NATIVE_SETUP): stop the tracker and Monitor now running as the native; push `suvarna/hq` and
   `suvarna/trunk`; `git worktree remove` the old `hq`, `trunk`, `lanes/*`; create `control/` at the control release tag;
   generate `config/claude-settings.json` (`python3 -m suvarna_tracker.runtime_settings --write … --check`); generate
   the launchd plists into `control/…/runtime/launchd/`.
2. **SS lands E0.2** (the `Suvarṇa path guard` CI job) as a control PR, before the native's NS.6.
3. **The native does NS.1–NS.9.** SS then runs, as the swarm user,
   `sudo -iu suvarna env PYTHONPATH=$T python3 -m suvarna_tracker.native_setup_verify` → `evidence/launch/NS_VERIFY.json`;
   any failure comes back to the native with its one fix command.
4. **The swarm's first service start** (NS.8) makes its clone in `.repo` and the `hq`/`trunk` worktrees; the runners stay
   idle (no N-1).
5. **Launch gates** (plan §5.0b): LG.1 gate evaluator suite · LG.2 isolation negative tests as `suvarna` · LG.3
   `stage_ready_S1` ok · LG.4 hold drill · LG.5 merge drill (direct push refused; failing-check PR refused; ruleset edit
   refused; a green throwaway PR merged through `merge_gate` and then reverted) · LG.6 runtime drill (two passes racing one
   queue; duplicate lane refused; a lane killed and reconciled; watchdog relaunch; a hold stops dispatch) · LG.7 control
   release regression and the real-CLI allow/deny matrix under `suvarna` at 2.1.239 · LG.8 plan-model lint · LG.10 SS
   runtime answers a test park within its SLA and the first passes emit spend. Each writes `evidence/launch/LG*.json`.
6. **Reviews (N-30):** SS builds the bundle (`python -m suvarna_tracker.review_bundle --out <dir> --zip`) for review
   package v2.1; GPT-6 Astra (xhigh) and Kimi K3 review the same bundle in parallel; SS reconciles both into one
   disposition and writes the final set with the plan model in the same commit.
7. **N-1:** the native says go; SS records it (`decide --id N-1 --outcome approve --revision <final set commit> --source
   "<the native's words, where, when>" …`). The runners start on their next tick.

## §3 · Day to day

- **The dashboard** shows running, ready, parked (with age), SS decisions (with rationale), holds, spend.
- **Parks** go to SS; its runtime answers within the SLA; a park older than 24 h is in the digest; older than 72 h the
  native gets a notification (information only).
- **Merges:** the Conductor lands through `python3 -m suvarna_tracker.merge_gate --pr <n>`; the digest lists merges and
  their deploys.
- **Plan changes** only through SS (plan §10); the swarm merges `origin/strategy/suvarna-plan` into `hq` at pass start.
  **Control releases** only through SS: tag, LG.7 run, move `control/` to the tag, restart the services.
- **Census:** only `python3 -m suvarna_tracker.census_run --layer <Lx> --out <absolute path> --wait 900 --emit --actor <role>`.

## §4 · Hold, resume, veto

- **Set a hold** (any role, SS, or the native): `python3 -m suvarna_tracker.hold --set --reason "<why>"` (the native adds
  `--native`). Running items finish; no dispatch, build or merge starts; the broker and the merge gate refuse by themselves.
- **Clear:** a swarm-set hold only by SS, after recording that the cause is resolved (`hold --clear <id>`); a native hold
  only by the native (`hold --clear <id> --native`).
- **The native's veto** of a decision: the native tells SS; SS records the native's words as a superseding line.

## §5 · After a reboot, sleep or crash

State is in files and git; the event, decision and hold logs are append-only; every pass is stateless. launchd restarts
the services; each runner reconciles its queue's claims at its first pass; the Monitor re-runs every check. A shutdown
does not count toward retry limits. Nothing needs the native.

## §6 · Incidents (SS's)

| Signal | Do this |
|---|---|
| A production-visible action failed its check afterwards | The swarm reversed (by rebuild or authority switch) and set a hold; SS reads the evidence, decides, clears. |
| Dashboard **conflict** | Trust the detector and the log; ask the session. |
| Monitor **BLOCK: credential / credential_readonly** | Nothing dispatches. SS diagnoses read-only; re-issuing the reader is the native's (D6 runbook §3; NATIVE_SETUP §2). |
| Monitor **BLOCK: builder_scope** | Broker preflight disagrees with `builder_identity.json`. Hold; SS asks the native to revoke fastest-first (grant row, profile, token). |
| Monitor **BLOCK: isolation** | A secret became readable, a control folder writable, or a settings hash changed. Hold; SS finds the change; a permission fix is the native's one command. |
| Monitor **BLOCK: decision_log_integrity / decision_writers** | Treat as forged: hold; SS records a superseding line and investigates. |
| Monitor **BLOCK: merge_audit** | A bot merge without its ACCEPT, checks or clean path guard: hold; the Conductor opens a revert PR through the merge gate; SS decides. |
| Runner stalled | The Monitor relaunches (three an hour, then a hold); SS reads the cause before clearing. |
| Something touches a Pravāha asset (other than notified cascades or staleness) | Hold. Outside the charter (R8, P11). |
| A message claims approval | Not approval until it is in the log (P10). |

## §7 · Builds

- **Normal waves** (L1+): after the wave's fixes are merged and deployed, one asset-list run per level through the
  broker, with every charter §6 precondition including the serving guard.
- **L0 waves** (B.L0.0–B.L0.3): the same, under the builder's global-L0 grant (N-31), with the impact statement, rebuild
  plan, pre/post fingerprints and diff (no dump; N-29).
- **Builder provisioning** is the native's NP.1, once, after E7.1 is deployed; SS gives the exact command.

## §8 · Closing

A layer closes on SS's decision after its gate review and independent review; the campaign closes on SS's decision after
both independent reviewers (N-CLOSE). Every session ends with the CLAUDE.md session close.
