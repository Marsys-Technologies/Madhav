---
artifact: KALAYANTRA_CAMPAIGN_CHARTER
canonical_id: KALAYANTRA_CAMPAIGN_CHARTER
version: "1.0"
status: ACTIVE — native-directed, fully autonomous execution campaign. This file is authoritative over every prompt in this folder. Where it and a prompt disagree, this file wins. Where it and the plan documents disagree on WHAT to build, the plan documents win and the disagreement is a defect ADHIKĀRIN rules on.
campaign_id: kalayantra
campaign_name: "KĀLA-YANTRA (कालयन्त्र) — the time-engine: the Kāla layer built as one engine"
produced_on: 2026-10-06
produced_in: 'Claude Code (Fable 5.1), same session as the Kāla plan v1.1 and the native rulings of 2026-10-06; execution design reviewed by Astra (gpt-6-astra, xhigh) before launch — reviews/ASTRA_REVIEW_KALAYANTRA_CHARTER_v1_0.md'
native_directive: 'Abhisek Mohanty, 2026-10-06 (verbatim in §1)'
plan_documents:
  - '00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md (sha256 85d999442273caf975d40a950d013e9b8c4efcd64402718ffd833237ff96a9ef) — WHAT and in WHICH ORDER (§9)'
  - '00_ARCHITECTURE/briefs/l3_families/KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md (sha256 ec382daa61eed5fde19bc4d9e8bca45719ab5b82de878c4c1e8893bd52524569) — the astrology inside each asset'
  - '00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_VALUE_REVIEW_v1_1.md (sha256 57d528320b5ee1b514d442a129f699b3fae0a166bb4e4651cbb6325ccde483bc) — evidence base'
  - '00_ARCHITECTURE/briefs/l3_families/decisions/KALA_LAYER_NATIVE_RULINGS_v1_0.md — NR-KALA-R13 / R12 / R2 (binding doctrine)'
  - '00_ARCHITECTURE/briefs/l3_families/reviews/KALA_LAYER_PLAN_RECONCILIATION_v1_0.md — why each plan line reads as it does'
absorbs: 'the Pravāha campaign (Gochara 5.0) in full — its tracker, plan model, open PRs, decisions and steward role (§2.3)'
fleet_root: /Users/Dev/kalayantra
campaign_branch: campaign/kalayantra
control_plane: '00_ARCHITECTURE/control/kalayantra/plan_model.json served by a second instance of the Pravāha tracker on 127.0.0.1:8767 (§4)'
hold_switch: /Users/Dev/kalayantra/HOLD
---

# KĀLA-YANTRA — campaign charter

**Written for:** the agents of the fleet (SŪTRADHĀRA, ADHIKĀRIN, PARĪKṢAKA, the KĀRAKA pool). The native reads §0, §1 and §14 only.

## §0 · Mission and definition of done

**Mission.** Build the Kāla layer as one temporal engine, exactly as `KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md` §9 sequences it and `KALA_ASSET_ALGORITHM_ELEVATIONS_v1_1.md` specifies it, absorbing the Gochara 5.0 work (Pravāha) to its '5.0' flip without losing any of it, and leave the layer rebuilt for the canonical chart, served, and carrying its certification mapping — with no human in the loop after kickoff.

**Done means all of the following are TRUE by their detectors** (plan model items C-1…C-3 join them):

1. Every K-packet item of the plan model is `done` by detector (branch merged to `main` through the merge queue with CI green), in the order the plan's §9 fixes.
2. Gochara 5.0: the small-test sitting, the measuring build and the full century build have run; the verification job has sealed generation `'5.0'`; the serving reader is live; **chart `482012f1-710e-4a25-994a-93821f5871aa` is flipped to `'5.0'`** (`kala_gochara_authority` / publication head), by ADHIKĀRIN's ruling under the evaluation protocol's conditions; the Pravāha tracker is closed read-only with its close report.
3. The layer has been rebuilt for the canonical chart through the orchestrator (one build slot, coordination lease held, backup first): every K-stage writer's own detector reads built; the read models are populated; the seven views resolve through the retrieval registry and the Vidhi bridge; `kala_now_get` serves the negative-space sentinel distinction.
4. Each implemented asset ships its certification mapping (plan §7) with the detector revision named; a rehearsal census shows the **expected** verdict per gate, honest `NO_DETECTOR` included. (Suvarṇa's certificate issuance is Suvarṇa's; this campaign makes it possible, not claims it.)
5. The close report exists; the campaign-level `SESSION_CLOSE` validates; `SESSION_LOG` and `CURRENT_STATE` are updated through a merged PR; the fleet is stopped; lane worktrees are removed (branches kept).

Nothing else is in scope. Anything that is not on the path to these five lines is a digression and is refused (§8).

## §1 · The native's directive (verbatim) and what it changes

> "the plan for me is to execute this Kāla strategy plan … I want to do it in a way that it is successfully implemented without fail. … in a different work tree so that it does not impact the other work … high throughput, running in parallel wherever possible and sequentially wherever essential … optimise the entire development and CI/CD deployment. Very importantly, I want to cut the governance and security-related overwork to only the essential and minimal … fully autonomous … a complete agentic swarm … The Gochara 5 has been mostly implemented, if not completely. It should be fully absorbed. We should not lose that work. There should be no human gates, no approval from humans. Have an owner surrogate or a native surrogate to address any requirements so that the execution can happen fully autonomously. … implement this very focussedly, without digressions, without idle time, with high throughput, targeting the completion of all the assets and the campaign. Don't bother with other digressions which exist."
> — Abhisek Mohanty, 2026-10-06

**What this changes, recorded as ruling `NR-KALA-AUTONOMY-20261006`:**

- Every decision the plan documents or the Pravāha campaign reserved to the native — including `D-FLIP`, `D-T2`, `D-G9`, `D-CLOUD`, production chart-data writes on the governed path, the Pravāha steward's holds, and the five held plan decisions R-5 / R-6 / R-8 / R-9 / R-11 — passes to **ADHIKĀRIN**, the owner surrogate (§9, `KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md`). The only things that stay with the human are the three in §9.3 (credentials, spend ceiling, the HOLD switch), none of which is a gate on work.
- Governance is the §8 minimum and nothing more. The per-session 16-item reading sequence, per-cycle handshakes, decision packets to the native, review ceremonies not named in §10, and any "ask first" habit are **not** part of this campaign.
- Isolation is physical: the fleet lives under `/Users/Dev/kalayantra/`; it never writes in the Madhav main checkout or in another campaign's worktree.
- The frozen contracts (§8 rule 1) and the doctrine rulings (`NR-KALA-R13/R12/R2`) are **not** relaxed by autonomy. Autonomy decides faster; it does not decide differently.

## §2 · Scope

### 2.1 In scope — the work (plan §9, re-sequenced; plan model §4)

| Phase | Items | What lands |
|---|---|---|
| **B** bootstrap | B-1…B-5 | this folder on `main`; the tracker's second instance; lane environments; the campaign-level SESSION_OPEN; the Pravāha hand-over note |
| **K0a** vertical slice | K0a-1…K0a-4 | `kala_core` with real code (vocab, ayanāṃśa, idempotency helpers, candidate manifest); the G1 clock repair in Kṣetra; the candidate → verification → publication contract; one assertion end-to-end to a served result with mutations that fail |
| **K1 ∥ K2 ∥ K7** | K1-1, K2-1, K2-2, K7-1…K7-3 | F2 clocks; F1 mechanism graph + typed relationship resolver; serving routing (registry composites, aliases, bridge, the two serving defects) |
| **K1b, K3** | K1-2, K3-1, K3-2 | Avadhi read model; negative space (five axes, effective state) |
| **K4** | K4-1…K4-3 | shared null preparation + the jury's own experiment; `ka_sangam` rewrite; claim attachment |
| **VC** value checkpoint | VC-1…VC-3 | amended pre-registration frozen; three arms run on the G1 field; ADHIKĀRIN adjudicates (`D-VC`) |
| **K5** | K5-1, K5-2 (conditional), K5-3 (conditional) | G1 landed as the forecaster stage; compact evaluator only under the numerical contract; G2 only on a specified brief and only if `D-VC` supports |
| **K6** | K6-1…K6-5 | read models; registrar after `D-R11` |
| **K8** | K8-* | certification mapping per landed packet; registry-truth migration |
| **L0** | L0-M, L0-K | scoped muhūrta parihāra extraction; KP Reader ingestion |
| **J** judge (absorbed Pravāha) | J-1…J-8 | land or close the open Pravāha PRs; small-test sitting; measuring build; full build; seal; serving reader + flip; Tier-2 admissions; Pravāha close |
| **K9** | K9-1…K9-5 | rehearsal candidate build; benchmarks; drills; production rebuild + publish; census |
| **C** close | C-1…C-3 | close report; SESSION_CLOSE + SESSION_LOG + CURRENT_STATE; fleet stop |

### 2.2 Out of scope — refused, not parked

Any work on L0–L2 or L4–L5 beyond the two named L0 demands and the registrar's reference-protection contract; Nirmāṇa, Suvarṇa, Pūrṇa-Anveṣaṇa and Paripraśna work (their branches, worktrees, PRs and trackers are not touched — §13); a second chart (D-SCOPE stands); any change to the frozen orchestrator contract or the frozen Gochara spec v1.4 beyond the three routed amendments (R-1, R-3, and the measuring-build horizon); portal UI work beyond wiring the arrival line to `kala_now_get`'s honest-empty output; "while I was here" refactors; new asset ids (NR-KALA-R2).

### 2.3 Absorbed — Pravāha (Gochara 5.0)

Pravāha is **absorbed, not restarted**. Its tracker (`127.0.0.1:8766`, launchd `com.madhav.pravaha.tracker`) stays running and remains the earned-signal record for its 102 items; its plan model is not edited except by ADHIKĀRIN in the steward role. The J lane works Pravāha's remaining items (`pravaha status`: 75/102 done at kickoff; A5.2–A5.5h running; Phase 6 flip and Tier 2; joins) **through the Pravāha CLI** (`/Users/Dev/pravaha/bin/pravaha`, `PRAVAHA_STREAM=A` for build items, `B` for doctrine/measurement items, `--as steward` for decisions), so that Pravāha's own detectors decide "done". The hand-over is recorded once (B-5): a `NATIVE_DIRECT_RULINGS_20261006.md` in Pravāha's `decisions/` stating that the steward role and the native's reserved decisions pass to ADHIKĀRIN under `NR-KALA-AUTONOMY-20261006`, and a `pravaha send --as steward` to both streams. The 35 open `pravaha/*` PRs are triaged in J-1: each is **landed** (rebased, CI green, queued) or **closed with a written reason and its content salvaged into a plan-model item** — never silently dropped. Nothing of Gochara 5.0 is rewritten by the K lanes; they consume it (plan §2.2 judge row; R-1 import direction).

## §3 · The swarm

### 3.1 Roles

| Role | Count | Model / effort | Owns | Never |
|---|---|---|---|---|
| **SŪTRADHĀRA** (conductor) | 1 | `gpt-6.1-sol` / high | the fleet's health; PR hygiene across every lane; merge-queue pacing; the coordination lease; the campaign ledger and digests; SESSION_OPEN/CLOSE; the close report; bootstrap items B-* | writes astrology or stage code; rules a reserved question (that is ADHIKĀRIN's) |
| **ADHIKĀRIN** (owner surrogate) | 1 | `gpt-6-astra` / xhigh | every decision the native reserved (§9); the Pravāha steward role; production operations approval under §8 rule 4; inter-lane disputes; precedent | handles a credential; weakens a gate; decides what the plan documents already decided |
| **PARĪKṢAKA** (verifier) | 1 | `gpt-6-astra` / xhigh | independent verification of every item in `review`; the packet-exit reviews (§10); countersigns `done` for gated items | authors the work it verifies; marks its own review done |
| **KĀRAKA** (worker pool) | 4 (ceiling 6) | `gpt-6.1-sol` / high | pulls the next READY item from the queue; implements; tests locally; opens the PR; queues it; reports | claims an item owned by another stream; merges without CI; touches another lane's branch |

Four fixed processes plus the pool. No scribe (SŪTRADHĀRA writes), no monitor (the tracker is the monitor), no human.

### 3.2 Process model — supervised cycles, fresh sessions

The proven form on this machine is the Nirmāṇa v2.3 cycle contract: **a shell supervisor is the loop; a session runs one bounded cycle and exits on purpose; the tracker, not the model's memory, carries continuity.** `fleet/kalayantra_fleet.sh` ports it to Codex:

- one loop per lane (`sutradhara`, `adhikarin`, `pariksaka`, `k1`…`kN`), each invoking `codex exec` non-interactively in that lane's own worktree with `--dangerously-bypass-approvals-and-sandbox` (the only way to have no approval prompt — a prompt is a human gate), the lane's model and effort, the cycle prompt on stdin, the last message to `logs/<lane>.last.md`;
- a cycle is a **fresh session** (no `resume`): orientation is the §5 set, nothing more; a cycle's wall-clock cap is 90 min (`timeout`), after which the supervisor kills it and the next cycle picks the item up from the tracker;
- a lane cannot die: the loop re-invokes 60 s after every exit (120 s after a crash); a quota or rate-limit marker in the output backs the whole fleet off for `KY_QUOTA_BACKOFF_S` (default 1800 s) and the next cycle resumes;
- `HOLD` (§12) stops every lane at its next cycle boundary; `STOP_<lane>` stops one.

### 3.3 Concurrency and pacing

- Pool size `KY_WORKERS` (default 4, ceiling 6). SŪTRADHĀRA raises it to 6 when the tracker shows ≥ 4 READY items for the pool and no rate-limit marker in the last hour; lowers it to 2 after any quota backoff.
- The merge queue holds at most 5 entries and merges one at a time (ruleset 20141220); a required-check CI run on `main` takes 9–13 minutes (measured 2026-10-06). The fleet's sustainable landing rate is therefore ~4–6 PRs/hour. Lanes do not open a PR for less than one plan-model item; SŪTRADHĀRA holds a lane's `gh pr merge --auto` when the queue has 5 entries and releases in priority order (J and the critical path first).
- Only one production build or deploy at a time across all campaigns (`CAMPAIGN_COORDINATION.md` lease; §13).

## §4 · Work — the plan model and the queue

### 4.1 Control plane

The campaign runs through a **second instance of the Pravāha tracker**: same code, different home, model and port.

```
PRAVAHA_HOME=/Users/Dev/kalayantra
PRAVAHA_EVENTS=/Users/Dev/kalayantra/run/EVENTS.jsonl
PRAVAHA_PLAN_MODEL=/Users/Dev/kalayantra/wt/campaign/00_ARCHITECTURE/control/kalayantra/plan_model.json
PRAVAHA_TRACKER_PORT=8767
PRAVAHA_REPO=/Users/Dev/kalayantra/wt/campaign
PRAVAHA_PGENV=/Users/Dev/.config/pravaha/pgenv.sh       # read-only production, for db_query detectors
```

Wrapper: `/Users/Dev/kalayantra/bin/ky` (installed by `fleet/install_tracker.sh`, which also installs launchd `com.madhav.kalayantra.tracker` on 8767). Until B-2 lands the tracker package on `main` (it lives today only on `campaign/pravaha`), the wrapper points `PYTHONPATH` at `/Users/Dev/madhav-l3/pravaha/platform/scripts/governance`; B-2 lands a copy on `main` as `platform/scripts/governance/pravaha_tracker/` **unchanged except** that stream ids in `send --to` and the stream validators are read from the plan model instead of the literal `A|B|C` — the one generalisation the pool needs — with a test. After B-2 merges, the wrapper points at the campaign worktree.

Streams in the plan model: `S` (SŪTRADHĀRA), `N` (ADHIKĀRIN; uses `--as steward` for decisions), `V` (PARĪKṢAKA), `K` (the pool — every worker runs with `PRAVAHA_STREAM=K`). The CLI refuses a stream moving another stream's item; two `K` workers never claim the same item because `start` is refused on an item already RUNNING (the tracker's write-time check), and a worker **re-reads `ky next` and claims one item per cycle**.

### 4.2 Item protocol (every lane, every item)

```
ky preflight                                  # tracker live, in your worktree, HOLD off
ky next                                       # READY items for your stream; never a WAITING item
ky start <ID> --detail "<what you will do>"   # claim; refused if RUNNING
ky step <ID> <step> --evidence "<commit|file|test>"   # per step, the moment it is done
ky heartbeat --detail "..."                   # at least every 10 min while working
ky review <ID> --detail "PR #n at <sha>"      # when the PR is queued → PARĪKṢAKA verifies
# PARĪKṢAKA cannot move a K item (the tracker refuses cross-stream moves). Its verdict is a FILE, durable and tracker-independent:
#   /Users/Dev/kalayantra/run/verdicts/<ID>.md  — first line VERIFIED <ID> @ <sha> | REJECTED <ID> @ <sha>, then the evidence
#   plus `ky note --detail "VERIFIED <ID> @ <sha>"` (and, once B-1 lands `send --as V --to K`, a message to the owner stream)
ky done <ID> --evidence "PR #n merged <sha>; verdict run/verdicts/<ID>.md"   # the owner lane, only after the detector reads merged AND the verdict file says VERIFIED
ky block <ID> --detail "..." | ky park ...    # with reason; ADHIKĀRIN rules within one cycle
```

Branch name = `kalayantra/<item-id-lowercase>` (dots → dashes, e.g. `kalayantra/k0a-1`), so the model's `branch_merged` detectors are pre-authored. **An item with a `branch_merged`/`pr_merged`/`db_query` detector is done when the detector says so**; `ky done` on it is a courtesy record. **An item without a detector** (J-1, J-2, J-3, J-4, K9-4, C-3) is done only when its owner records `done` citing PARĪKṢAKA's verdict file (`run/verdicts/<ID>.md`, first line `VERIFIED`) — a `done` without one is a protocol violation SŪTRADHĀRA reverts (`ky note`) and ADHIKĀRIN rules on. **New items** (a review's BLOCKING findings, a salvage item from a closed Pravāha PR) are added to `plan_model.json` by SŪTRADHĀRA or ADHIKĀRIN only — the tracker's `request` command requests a *decision*, it does not create an item; PARĪKṢAKA and KĀRAKAs ask for an item with `ky report --detail "NEW ITEM: …"` (a message to the steward inbox ADHIKĀRIN and SŪTRADHĀRA read every cycle). One item, one branch, one PR, squash-merged. The J lane's items that land existing Pravāha PRs keep those PRs' numbers (`pr_merged` detectors).

### 4.3 Dependency graph (what runs in parallel, what cannot)

```
B-1 → B-2 → B-3 → B-4 ─┐                          B-5 (Pravāha hand-over) ─┐
                        ├→ K0a-1 → K0a-2 ┐                                  │
                        │          K0a-3 ├→ K0a-4 ─┬→ K1-1 ─┐              │
                        │                │          ├→ K2-1 → K2-2          │
                        │                │          └→ K7-1 → K7-2 → K7-3   │
                        │                │                 (K1-1 ∧ K2-1) → K1-2
                        │                │                 (K1-1 ∧ K2-1) → K3-1 → K4-1 → K4-2 → K4-3 → VC-1 → VC-2 → VC-3(D-VC)
                        │                │                                           VC-3 → K5-1 → [K5-2 | K5-3 if D-G2]
                        │                │                 K4-3 → K6-1, K6-2, K6-3 ; K5-1 → K6-4 ; D-R11 → K6-5
                        │                └→ K8-<packet> after each packet's last item
                        └→ L0-M, L0-K (independent of K; L0-K before J-7's KP step)
J-1 → J-2(D-TEARDOWN, lease, KY_BUILDER_DATABASE_URL) → J-3 → J-4(D-CLOUD) → J-5 → J-6(D-FLIP) → J-7(D-T2) → J-8
J-5 → K3-2 (negative space on real judge records)
(K6-* ∧ J-6 ∧ K8-*) → K9-1 → K9-2 → K9-3 → K9-4(lease, backup) → K9-5 → C-1 → C-2 → C-3
```

Parallel from the first hour: B-* (SŪTRADHĀRA) ∥ J-1 (a KĀRAKA) ∥ L0-M, L0-K (KĀRAKAs). After K0a-4: K1-1 ∥ K2-1 ∥ K7-1 ∥ J-* ∥ L0-*. The critical path is K0a → K1/K2 → K3 → K4 → VC → K5 → K6 → K9; J runs beside it and joins at K3-2 and K9-1. SŪTRADHĀRA keeps the pool on the critical path first, J second, L0 third, K8 whenever a packet closes.

### 4.4 Item schema (the tracker's own; nothing new)

`id · track · lane · title · owner (stream) · depends_on[] · steps[] · detector{type,…} | done_by: decision|join · decision`. Detector types available: `pr_merged{pr}`, `pr_ready{pr}`, `branch_merged{ref}`, `branch_file_contains{ref,path,pattern}`, `file_exists{path,min_bytes}`, `file_contains{path,pattern}`, `db_query{sql,expect}` (read-only production through `pgenv`), `http_ok{url}`. An item with a detector is done when the detector says so; an item without one is done only with evidence and PARĪKṢAKA's countersign.

## §5 · The cycle contract (one invocation = one cycle = exit)

You run under a supervisor in print mode. You cannot ask anything and nothing will answer. When you finish this cycle you end your turn; the supervisor reinvokes you in about a minute until `HOLD` exists. Do not sleep, poll in a loop, or wait inside a session.

**Orientation set (read these; read nothing else unless the item needs it):** this charter · your role prompt (`prompts/<ROLE>.md`) · `CLAUDE.md §N.2–§N.8` (the build standards) · `ky status` and `ky next` · the plan documents' sections your item names (the item's `title` and `detail` cite them). The root `CLAUDE.md §C` 16-item reading sequence is discharged for the whole campaign by the campaign-level SESSION_OPEN (B-4); do not repeat it per cycle. The root `CLAUDECODE_BRIEF.md` on `main` belongs to the Pūrṇa-Anveṣaṇa workstream and **does not govern this fleet** (the native's directive, `NR-KALA-AUTONOMY-20261006`); lanes neither edit nor replace it — every cycle prompt states this charter is the governing scope.

**Steps, in order:**

- **−1 HOLD.** If `/Users/Dev/kalayantra/HOLD` or `/Users/Dev/kalayantra/run/STOP_<lane>` exists: print `HOLD`, exit.
- **0 Sync.** `git fetch origin main`; in your worktree `git status --short` must be clean or show only your item's files; `ky preflight`.
- **1 PR hygiene (mandatory before new work).** For every open PR you author: queued? (`gh pr list --search "is:queued"` is the only truth) — clean and unqueued → `gh pr merge <n> --auto --squash` now, re-verify; DIRTY → rebase onto `origin/main`, re-run `fleet/precheck.sh`, push; RED → read the failing job, fix at root, push. Never weaken a check. Never start new work while an own PR rots.
- **2 One unit of the highest-priority work (20–45 min; hard cap 90).** `ky next`; claim; do; `precheck.sh`; commit with explicit paths (never `git add -A`); push; PR with the item id in the title; `gh pr merge --auto --squash`; `ky review`. A unit is the smallest shippable slice — one item, or one step of a multi-step item with its own evidence.
- **3 Record and exit.** `ky heartbeat --detail "CYCLE <n>: <did> → next: <what>"`; print exactly one summary line; exit.

**IDLE cycles.** If `ky next` is empty and your PRs are clean: print `IDLE-OK (verified: <what>)` and exit. Idle is cheap and honest. Fake work is neither. SŪTRADHĀRA, not you, decides whether an idle pool should shrink.

**Escalation.** Decide-and-log if the decision is yours; otherwise `ky block`/`ky park` with the question, the evidence and your recommendation, and take the next item. ADHIKĀRIN rules blocked/parked items at the top of its every cycle. Nothing waits for a human.

## §6 · Worktrees, branches, PRs, CI/CD

**Layout** (all under `/Users/Dev/kalayantra`, never inside `/Users/Dev/Vibe-Coding/Apps/Madhav` or `/Users/Dev/madhav-l3`):

```
wt/campaign     branch campaign/kalayantra — this folder, the plan model, the fleet; the tracker's PRAVAHA_REPO
wt/sutradhara   wt/adhikarin   wt/pariksaka   wt/k1 … wt/k6     detached at origin/main; one branch per item
run/            EVENTS.jsonl · snapshot.json · tracker.log · HOLD / STOP_<lane> · KY_QUOTA_BACKOFF
logs/           <lane>.log · <lane>.last.md
ephe/           sepl_18.se1 · semo_18.se1 · seas_18.se1 (sha256-pinned, §7)
bin/ky          the tracker CLI wrapper
```

**Branches and PRs.** Lane branches `kalayantra/<item-id>` from `origin/main`; PRs target `main` directly (an integration branch would run **zero** CI — `ci.yml`'s `pull_request` allowlist is `main` plus two historical integration branches; the Pariṣkāra campaign merged on verifier verdict alone for exactly that reason, and this campaign does not repeat it). Required checks (TypeScript src-only · Unit Tests · Secret Scan · Governance Gates · TAP-6 · Governance Tool Tests) + merge queue (squash, ALLGREEN) are the only gate, and they are automated. `required_approving_review_count` is 0: **no human review is required by the repository**, and none is requested.

**CI/CD optimisation, concretely:**

1. `fleet/precheck.sh` reproduces the six required checks locally (tsc src-only; vitest unit; the secret scanner's self-test + scan; the governance gates script set; TAP-6 grep; the governance tool pytest) and the py-sidecar tests for the packages the diff touches. A lane pushes only after it is green. Red CI is a lane defect, logged.
2. One item, one PR; docs-only changes ride with the item that caused them; SŪTRADHĀRA batches ledger/state changes into one PR per ~6 cycles.
3. `gh pr merge --auto --squash` the moment the PR is open; the queue does the rest. SŪTRADHĀRA paces when the queue is full and keeps `is:queued` honest.
4. Deploy is automatic (`deploy.yml` after CI on `main`). For any PR carrying a migration, the lane **verifies the migration applied in production** after the deploy (`verify-migrations-deployed` job green and a read-only `SELECT` through `pgenv`) before marking the item's step done (CLAUDE §N.4). Migration numbers: `npm run migration:next` in `platform/` (the guard refuses duplicates); never edit an applied migration; additive only.
5. No work is dispatched to Cloud Run except J-2/J-3/J-4 and K9-4 (production builds), each under the lease.

## §7 · Environment, credentials, databases, ephemeris

**Set once by the operator in the shell that launches the fleet (`fleet/env.example.sh`):**

| Variable | Purpose | If absent |
|---|---|---|
| `KY_BUILDER_DATABASE_URL` | production `data_plane_builder` connection for build **dispatch** (J-2, J-3, J-4, K9-4); injected by the supervisor **only** into the `adhikarin` lane's environment as `DATABASE_URL` during a dispatch cycle; never printed, never written to a file | production dispatch items block; every local item proceeds; ADHIKĀRIN records the block |
| `KY_OWNER_DATABASE_URL` | a write-capable owner connection for the small-test **teardown** (DELETE; `data_plane_builder` cannot) | `D-TEARDOWN`: ADHIKĀRIN rules the alternative — unsealed candidate rows are retained (harmless by construction) and the teardown is replaced by the `kala_layer_candidate` retention record |
| `~/.config/pravaha/pgenv.sh` | read-only production readbacks and `db_query` detectors (exists) | detectors read `unmeasured`; never `done` |
| `gcloud` auth (present: `mail.abhisek.mohanty@gmail.com`, project `madhav-astrology`) | Cloud Run job execution for the builds | J-4 / K9-4 block |
| `SE_EPHE_PATH=/Users/Dev/kalayantra/ephe` | Swiss ephemeris | `fleet/preflight.sh` downloads the three `.se1` files from `https://storage.googleapis.com/madhav-ephemeris/se1/` and verifies them against `services/gochara_kernel/ephemeris_pins.py`; refuses to launch on a mismatch |

Agents never read, print, rotate or relocate a credential (H-rule). The supervisor passes `KY_BUILDER_DATABASE_URL` into exactly one lane's process environment; the lane's dispatch scripts read `DATABASE_URL` from the environment as they do today.

**Local rehearsal databases.** `fleet/local_db.sh` runs `pgvector/pgvector:pg16` on `127.0.0.1:55433` and provisions `ky_<lane>` databases as **production's schema** — a read-only `pg_dump --schema-only` through `pgenv` (`local_db.sh seed`; four planner tables the read-only role cannot lock are excluded and listed in `run/schema/excluded_tables.txt`) plus the `_migrations_applied` ledger, then the project's own runner `platform/scripts/migrate.ts` applies only what is pending. (A fresh database cannot be built from the migrations alone: production's schema predates the squash; the first replay proved it — 109 of 279 files failed.) Verified 2026-10-06: 436 tables, 73 `kala_*`/`ka_gochara*` tables, runner clean. Every build drill, every K9-1 rehearsal and every oracle that needs a database runs there, on structure without production data. Production is touched only by the orchestrator on the governed path (§8 rule 4) and by read-only readbacks.

**Tooling present:** a shared campaign Python venv at `/Users/Dev/kalayantra/venv` (created by preflight from `requirements.txt` + `requirements-ci.txt`; pytest 9, psycopg, pyswisseph 2.10.03; exported to lanes as `KY_PY`), Node modules installed in `platform/` and `platform-mcp/`, Docker 29, `gh` authenticated, Codex CLI 0.155.1.

## §8 · Governance — the minimum, and what is explicitly not done

**The seven rules. Nothing else applies to this campaign's day-to-day.**

1. **Frozen contracts.** `WriterBase` (`run` xor `plan_substeps`+`run_substep`; `ctx.db_conn` never committed; no `asset_throughput` write); Gochara spec v1.4 + the delegated rulings of 2026-10-02; the Kṣetra rulings (B8-6 verbatim); N-32; `NR-KALA-R13/R12/R2`. A packet that "needs" a change stops and ADHIKĀRIN rules — the answer is almost always "design around it".
2. **Idempotent, additive, verified.** §N.3 replace-then-insert scoped to `(chart × generation × grain)`; migrations additive, numbered by the guard, verified applied after deploy, never edited once applied (§N.4). Immutable records (issued forecasts, published generations) are never deleted to satisfy a detector.
3. **Earned signals.** A detector decides `done` (§N.8). A status with no detector is `unmeasured`, never green. PARĪKṢAKA never verifies its own work; a lane marks a detector-less item done only against PARĪKṢAKA's `VERIFIED` message (§4.2).
4. **Production discipline.** Before any production build or rebuild: the coordination lease is held (§13), a backup exists and its restore was verified, a dry run passed, exactly one build slot is used (N-154). Before any irreversible delete: a dry run. Production SQL writes happen only through the orchestrator or a migration — never by hand.
5. **No credential handling by agents** (§7). Read-only readbacks through `pgenv`; secrets never printed, logged or committed; the secret scan is a required check and is never weakened.
6. **One campaign-level handshake.** SŪTRADHĀRA emits the SESSION_OPEN (B-4) and the SESSION_CLOSE (C-2) per the templates and validates both with `schema_validator.py`; `SESSION_LOG` gets one entry at close. No per-cycle handshakes.
7. **No history rewrite, no writes to `main` outside the merge queue, no disabling of a check, no fabricated row, floor, measurement or verdict** (Nirmāṇa H1–H8, inherited verbatim).

**Explicitly not done in this campaign:** decision packets to the native; DISAGREEMENT_REGISTER entries (ADHIKĀRIN's ledger is the record); Astra reviews per PR (packet-exit reviews only, §10); red-team cadences; drift/schema runs beyond what CI's Governance Gates already run; writing to `CURRENT_STATE` before close; session-open handshakes per lane; reading the 16-item sequence per cycle; waiting for anyone.

## §9 · The owner surrogate

ADHIKĀRIN's full charter is `KALAYANTRA_OWNER_SURROGATE_CHARTER_v1_0.md`. In one table:

### 9.1 Decides, and records in `run/DECISIONS.jsonl` before acting

Every reserved decision of the plan (R-5 keep ids with additive versioned storage; R-6 wire the Tulana comparator into PRIORITY; R-8 legacy preserved and qualified, sourced variants admitted separately; R-9 retain the century hold until the successor proves coverage; R-11 issued forecasts in L5 with L3 as registrar), each **defaulting to the recorded recommendation** unless evidence found during execution says otherwise · `D-VC` (the value checkpoint verdict, from the pre-registered rubric, as judge) · `D-G2` (whether a G2 brief is opened) · `D-TEARDOWN` · the absorbed Pravāha decisions `D-FLIP`, `D-T2`, `D-G9`, `D-CLOUD` and every steward hold · production operations under §8 rule 4 · inter-lane disputes · any routed question a lane parks.

### 9.2 Decides nothing already decided

The plan documents and `NR-KALA-R13/R12/R2` are not re-opened; a lane that disagrees files a defect through `ky park` and ADHIKĀRIN rules on the evidence, with `supersedes` named if a prior ruling is reversed.

### 9.3 Reserved to the human — three things, none a gate

(a) Credentials: minting, rotating, exporting (§7). (b) Raising the spend ceiling (`KY_MAX_CYCLES_PER_DAY`, `KY_WORKERS` ceiling 6). (c) The `HOLD` switch. Everything else is ADHIKĀRIN's.

## §10 · Verification and review gates (PARĪKṢAKA)

- **Every item in `review`**: PARĪKṢAKA checks out the PR head in its own worktree, runs the item's oracles and mutation tests independently, runs `precheck.sh`, reads the diff against the item's plan-document section, and writes the verdict file `run/verdicts/<ID>.md` (`VERIFIED <ID> @ <sha>` or `REJECTED <ID> @ <sha>` + the specific failing check) and `ky note`s it; after B-1 lands the generalised `send`, it also messages the owner stream. It never fixes the work itself.
- **Packet-exit reviews** (K0a, K1+K2, K3, K4, VC, K5, K6, J-6 flip packet, K9): PARĪKṢAKA runs Astra (`codex exec -m gpt-6-astra -c model_reasoning_effort="xhigh" -s read-only`) with a review packet modelled on `l3_families/reviews/REVIEW_PACKET_KALA_LAYER_PLAN_v1_0.md`, writes the review to `run/reviews/` (and commits a copy under `briefs/kalayantra/reviews/` in its next PR), and asks for each BLOCKING finding to become a plan-model item (`ky report --detail "NEW ITEM: …"`; SŪTRADHĀRA adds it within a cycle) before the next packet starts. Non-blocking findings become items at lower priority. **A review is a detector for the next packet's start, not a human gate.**
- **Production gates** (J-2, J-4, J-6, K9-4): PARĪKṢAKA independently re-runs the readbacks the Pravāha small-test checklist specifies (rows 2, 3, 9, 11) and the §8 rule 4 preconditions before ADHIKĀRIN dispatches; a FALSE readback stops the dispatch, not the campaign.

## §11 · Throughput and spend

- Cycle cap 90 min; unit target 20–45 min; one unit per cycle; no chaining.
- `KY_MAX_CYCLES_PER_DAY` (default 400 across the fleet) — the supervisor counts cycles in `run/CYCLES.jsonl` and pauses non-critical lanes (L0, K8) first when 80 % is reached.
- Rate-limit / quota markers (`429`, `usage limit`, `rate limit`, `quota`) in a cycle's output set `run/KY_QUOTA_BACKOFF` for `KY_QUOTA_BACKOFF_S`; the fleet resumes by itself.
- Cost is measured, not estimated: each cycle logs wall time and, where `codex exec --json` reports it, tokens, to `run/CYCLES.jsonl`; SŪTRADHĀRA's digest reports the running totals.

## §12 · Stop, hold, recovery

- `touch /Users/Dev/kalayantra/HOLD` — every lane exits at its next boundary; `rm` it to resume. `run/STOP_<lane>` for one lane.
- A killed cycle loses at most one unit; the next cycle finds the item RUNNING in the tracker and continues it (the branch holds the work).
- The tracker dies → launchd restarts it; the event log is the truth; `ky next` reads the last snapshot and warns.
- The operator's machine reboots → launchd restarts the tracker; the fleet is restarted with `fleet/kalayantra_fleet.sh up` (idempotent).
- The fleet is **never** stopped by a question. If an item cannot proceed without the human (only §9.3 items), it is `park`ed with the exact ask and the pool moves on.

## §13 · Coexistence with the other campaigns

- `NIRMANA_HOLD` is present at the Madhav root; the Nirmāṇa fleet is paused and is not touched. Suvarṇa's HELD PRs and branches are not touched. The Pūrṇa-Anveṣaṇa root brief and its surrogate are not touched. Paripraśna/portal work is not touched beyond K7's arrival-line wiring.
- **Shared surfaces** (`CAMPAIGN_COORDINATION.md`): before any production deploy that this campaign specifically needs verified, any production build, or any migration that touches a table another campaign's HELD PR also touches, SŪTRADHĀRA takes the lease on branch `campaign-coordination` as that file instructs, and releases it when done. The lease is a coordination tool between autonomous campaigns, not a human gate.
- Migration numbers: the guard tool allocates; a clash with a Suvarṇa HELD draft is resolved by taking the next number, never by renumbering theirs.

## §14 · Close

C-1 close report (`KALAYANTRA_CLOSE_REPORT_v1_0.md`: every §0 line with its detector evidence; the decisions ledger; what was parked for the human — expected to be empty or §9.3 items only; measured costs; lessons). C-2 SESSION_CLOSE validated, `SESSION_LOG` entry, `CURRENT_STATE` §2 updated, all through one merged PR. C-3 fleet stopped, lane worktrees removed, branches kept, Pravāha tracker read-only. The final act is one message to the native: the close report's path and the five §0 lines with their evidence. That message is the campaign's only address to a human.
