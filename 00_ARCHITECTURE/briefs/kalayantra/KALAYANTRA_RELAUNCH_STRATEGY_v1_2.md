---
artifact: KALAYANTRA_RELAUNCH_STRATEGY_v1_2.md
status: APPROVED IN PRINCIPLE by the native 2026-10-11 (six decisions below); HISTORICAL RATIONALE ONLY after plan v2.1 (Astra KS-11): execution, routing, review, regeneration, measurement and hand-off rules are exclusively those of the approved relaunch plan and its paired prompts
version: 1.2
authored_by: Claude Code (Fable 5.1), token-economy audit session, worktree audit/token-economy
authored_on: 2026-10-11
audience: native (approver); the planning session that will build the relaunch plan and the two paired prompts
disposition: >
  Strategy only. No plan items, no prompts yet. Factors in: the token-economy audit
  (TOKEN_ECONOMY_AUDIT_v1_0.md), the KĀLA-YANTRA campaign as executed 10-06 → 10-10,
  its completed work, its hurdles, the waste analysis, and the Suvarṇa wrap-up.
evidence_base:
  - 00_ARCHITECTURE/TOKEN_ECONOMY_AUDIT_v1_0.md (F-1 … F-10, A§5, A§7)
  - scratch notes: notes_ky_state.md, notes_suvarna_state.md, notes_workflow.md
    (/Users/Dev/scratch.noindex/claude/madhav/20261011-token-economy/)
  - live tracker `ky status` v52675 (read-only), run/EVENTS.jsonl, run/CYCLES.jsonl
  - gh PR metadata 2026-10-10
owner_decisions_applied:
  - No local model; everything in Claude; no Codex.
  - Opus 5.5 high for the important roles; Sonnet 5.5 high for the rest.
  - Suvarṇa wraps up fully first; the hold window is used for planning.
  - The campaign is launched by pasting a prompt into an interactive Claude Code
    session (Antigravity extension).
---

# KĀLA-YANTRA relaunch — strategy

## 1. Where things stand (measured)

| fact | value | source |
|---|---|---|
| items done | 46 / 148 = 31.1 % plain (39 guarded completions + 1 join + 6 decisions; 37.6 % is the tracker's weighted progress); K-track 24/85, J 2/32, V 2/15 | `ky status` |
| real engine items merged | 20 (K0a-*, K0-SV, K1-*, K2-*, KA-*, K4-1, L0-K-RUNNER; PRs #3245–#3365) | EVENTS, gh |
| open Kāla PRs frozen by the hold | 15; 11 ACCEPTED (6 at exact head), 4 rejected/stale | gh, VERDICTS |
| unstarted | J lane after J-0c (30 items, 37 inherited Pravāha PRs), 21 K items, 4 READY exits never claimed, close C-1..C-4 | plan model vs EVENTS |
| items done per day | 5 / 10 / 2 / 3; zero since the hold | EVENTS |
| lead time claim → done | median 10.9 h (target ≤ 2 h); K0a-3 42 h, rejected 14× | EVENTS |
| fleet cycles | 3,946 in 4 days; 57 % idle; 70 % of events are heartbeat/note/ack | CYCLES, EVENTS |
| verdicts | 74 / 180 REJECTED; 29 duplicate verdicts at unchanged heads; 12 reversals | VERDICTS |
| rejection causes (keyword classes) | hash/pin 54, environment 24, deploy evidence 18 | VERDICTS |
| parks | 93 (58 cite `owns`, 17 the §2 reservation ceremony); 147 rulings, 98 on day one | EVENTS |
| bootstrap | ~19 h (charter priced "several hours") | LAUNCH_ACCEPTED vs charter §15.5 |
| hold cost so far | 197 cycles, 26.7 lane-h, 14.6 M footer tokens, 0 completions | CYCLES since 10-10 08:57Z |
| Suvarṇa state | certification closed 51/83 on 10-10; reopened for ONE rebuild 12–13 Oct, exclusive lease 13–19 h; 105 open PRs (74 draft, 52 held), 68 worktrees | OWNER_SUMMARY, RUNBOOK_SINGLE_REBUILD, gh |
| Token audit | interactive coordinators 34 B / 30 d; median 251 K context per call; fleet 50–60 % idle; 97 % of all tokens are cache re-reads | AUDIT F-1, F-3, B-1 |

**Reading.** The astronomy was never the bottleneck. The campaign's own words: "the slowness is machinery, not computation"; "~4 rejections found a real defect" among the first 27 (amendment §0); of 74 total, the share is not measured; 83 of 93 new-item reports were about tooling. The relaunch therefore changes the machinery, not the plan documents.

## 2–4. Strategic pillars, risks, deliverables — HISTORICAL RATIONALE ONLY

> **Operative rules are not here.** Execution, routing, review, regeneration,
> measurement and hand-off rules are exclusively those of the approved relaunch plan
> (KALAYANTRA_RELAUNCH_PLAN_v2_1.md or later) and its paired prompts. Where the text
> below differs (for example rebasing, verdict de-duplication, frozen-file routing,
> capacity, budgets, liveness, context thresholds), the plan governs. The owner
> decisions in §5 and the evidence in §1 remain valid.

### (historical) Strategic pillars

### P1 — Suvarṇa wrap-up is a gate with a written exit, not a background condition
- Let Suvarṇa run its single rebuild under its lease; Kāla makes no merge, DB write or
  rebuild until the exit signal (the existing hold already enforces this).
- **Exit signal (all five, posted in one place the conductor can read):**
  1. "certification-done" posted and `HOLD_MERGES` removed;
  2. the post-rebuild L1 pins (daśā build hash, registry revision) published once —
     Kāla re-pins once, never chases them again;
  3. generated files (census, writer digests) regenerated on main by script;
  4. Suvarṇa PR sweep: every open Suvarṇa/Pravāha PR is merged, parked with a
     written disposition, or closed; nothing "held" without an owner and a date;
  5. the long-lived Suvarṇa coordinator sessions close with hand-off notes and stop
     acting as conductors.
- Planning, bootstrap and fixtures proceed during the hold; **launch is gated on the
  signal, not on 13 Oct** (the runbook itself calls 13 Oct a target, not a release).

### P2 — Event-driven fleet: a worker starts only when a job exists
- Replace polling lanes with a deterministic dispatcher (PRAHARĪ as a script, no
  model). It watches the tracker and PR state and launches a worker for one named
  job: *build item X*, *verify PR Y at head Z*, *rule on question Q*, *rebase PR Y*.
- Workers are headless `claude -p` runs in their own worktree, launched lean
  (`--bare`, explicit `--effort`, no MCP/plugins unless the job needs chart data),
  run to completion, write their result to the tracker, exit. No lane "wakes up to
  look around". Claim renewal and heartbeats are dispatcher actions, not model turns.
- Size (owner decision): **3 builders + 2 verifiers** standing, scaling up on demand
  whenever ready work exceeds live builders. Basis for expecting no loss of output:
  8 builders + 3 verifiers delivered ≤ 10 items/day while 57 % idle. Estimate.
- Idle-share target < 10 % of worker tokens; it is measured daily (P6).

### P3 — Thin conductor, launched by you from a prompt, restarted by design
- The interactive session you start is SŪTRADHĀRA. It plans, dispatches, rules on
  routine blockers, and reports. It never builds, never verifies, never holds tool
  output, and never runs for days.
- Rules in its prompt: state lives in the tracker and files; bounded subagents
  return conclusions only; **hand-off on persisted counters** (60 wake-ups, 8 h, or the
  owner's word — a model cannot read its own context size) — it writes a ≤ 5 K
  hand-off note and you restart it with the same prompt (the paired-prompt rule:
  prompt and plan carry the same version stamp).
- This is the direct answer to F-1: the three coordinator sessions that ate 34 B
  tokens in 30 days ran 10–16 days each with context near 1 M.

### P4 — All-Claude roster
| role | model / effort | mode | note |
|---|---|---|---|
| Planner / brief author (one-time plan build, then per-wave packets) | Opus 5.5 **xhigh** (owner decision) | interactive or on-demand job | writes acceptance tests first |
| SŪTRADHĀRA (conductor) | Opus 5.5 high | interactive, you launch | thin, restartable |
| ADHIKĀRIN (rulings) | Opus 5.5 high | **on-demand job**, not a standing lane | last time 75 % idle; 98 of 147 rulings came on day one |
| KĀRAKA (builders) | Sonnet 5.5 high | headless job per item | replaces the local model |
| escalation builder | Opus 5.5 high | headless | after 2 red loops, 1 rejection, or a frontier-by-rule hit |
| PARĪKṢAKA (verifier) | Opus 5.5 high | headless job per PR head | diff + brief + gate output; one verdict per head |
| PRAHARĪ (monitor/dispatcher) | script, no model | always on | — |
| LEKHAKA (scribe) | none; ledger compiled by script | — | add Sonnet 5.5 only if the digest provably needs prose |
- Frontier-by-rule (always Opus): Gaṇita computation core, migrations, FROZEN
  orchestrator files, anything touching `'lit'` or `verification_pass_status`,
  security/auth, governance detectors (AUDIT A§7 globs).

### P5 — Work orders that remove the top rejection causes
- 96 of 180 verdict problems were pins/hashes, environment and deploy evidence. So
  every packet carries, inline: the exact pins for this wave, the environment
  recipe, the deploy-evidence template, the file list plus allowed side-files
  ("owns is a floor"), the signatures, the quoted spec excerpt with its anchor, and
  **an executable acceptance command** written by the planner before the build.
- Verifier packet = diff + packet + deterministic gate output. One verdict per head;
  a changed head is a new job (removes the 29 duplicate verdicts).
- Reuse as-is: the 5 hash-pinned plan docs, the 148 live item briefs, merged
  `kala_core` and its CI, the 11 accepted-unmerged PRs (they land first), the
  protected-window mechanism, `precheck.sh --item`, tracker v2 rules.
  Retire: Codex-era prompts/digests/kickoff, the 33 machinery PRs' pattern, charter
  §3/§5/§11 (superseded by the amendment), cancelled B-* items, the stale K-CERT
  brief.

### P6 — Decouple from Suvarṇa and from each other
- One settled L1 at launch; pins published once (P1.2).
- Generated files are never hand-merged: a scripted regenerate-on-conflict step; the
  dispatcher re-queues a rebase job instead of a builder cycle.
- One migration-number allocator in the tracker (renumbering happened 4×).
- DB-touching items are batched into one or two protected windows per week with one
  human grant each, instead of one-shot PRs that each wait on a grant (K0a-3: 42 h).
- Scope reservation is a tracker field, not a ceremony (17 parks were the ceremony).

### P7 — Measure from day one; the budget is a dial, not a hope
- Workers keep transcripts (no `--no-session-persistence`) or write stream-json
  results, so the corrected baseline meter sees them.
- Daily report: four-class tokens per role, per accepted item, idle share,
  rejections per verdict, lead time, items done. Targets: idle < 10 %, rejection
  rate < 20 %, lead time median ≤ 4 h, ≥ 8 items/day at steady state.
- Claude Max headroom is not readable locally. **Owner decision: no caps or budgets.**
  Usage is reported daily per role and per accepted item; the dispatcher pauses only
  when the subscription itself refuses a request, and reports it; the owner checks
  usage at two fixed times a day.
- Only one interactive coordinator per campaign at a time; coordinators compete with
  the fleet for the same subscription.

### P8 — Re-scope to the critical path; bootstrap before launch
- Triage the 102 remaining items into: (a) needed for "Kāla serves chart 482012f1
  end-to-end with certification mappings"; (b) valuable but deferrable; (c) inherited
  Pravāha material to be dispositioned, not rebuilt. The plan is (a) in dependency
  order, with the 11 accepted PRs as wave 0.
- Bootstrap (worktrees under the policy root, lane DB baseline, fixtures, pins,
  dispatcher dry-run) is done **during the hold**, so launch day builds.

### (historical) Risks
- **Quota concentration.** Everything on one Claude Max subscription whose headroom
  is unmeasured; the audit shows Claude already carried 81 % of tokens. Mitigation:
  P7 cap and pause rule; no second coordinator.
- **Sonnet on timing logic.** Quality risk for L3 computation. Mitigation:
  frontier-by-rule, tests-first packets, Opus verifier, escalation after 2 loops.
- **Suvarṇa slips.** Launch is gated on the exit signal; planning cost is spent
  either way and is not wasted.
- **Dispatcher bugs starve lanes.** Decision log per tick; a forced liveness job per
  lane every 2 h.

### (historical) What the plan will produce
1. The relaunch plan (waves, packets with tests, DAG, budget, exit signal).
2. Two pasteable prompts, version-paired to the plan: the **planning-session
   prompt** (builds packets and tests) and the **conductor prompt** (runs the
   campaign from the Antigravity Claude Code session, with the hand-off rule).
3. The dispatcher script and the daily token report.

## 5. Owner decisions (2026-10-11)

v1.1 note: operative passages corrected to the owner's decisions (3+2, xhigh, no
budgets, counter-based hand-off) and the progress figures corrected per Astra KR-12.
1. Roster as in P4; **planner at xhigh**.
2. **3 builders + 2 verifiers**, scaling up on demand whenever there is work.
3. **Re-scope approved:** critical path first, defer (b), disposition (c).
4. **The five-part Suvarṇa exit signal is the launch gate.**
5. **No token caps or budgets.** Usage is measured and reported daily; the dispatcher pauses only when the subscription itself refuses a request (P7 is amended accordingly).
6. **ADHIKĀRIN is an on-demand job.**
