---
title: KĀLA-YANTRA v3 owner decisions — Amendment A4 (one engine, no owner decisions, Wave 4 shortened)
version: 1.1
status: CURRENT
date: 2026-10-15
amends: Amendment A1 (D-12 enforcement, D-16), Amendment A3 (D-22.3, D-24), KALAYANTRA_RELAUNCH_PLAN_v2_7.md (§7 dispatcher lane, §16 close), the Wave 4 plan-model entries J-2c and J-2d, D-* items
precedence: where this amendment and any amended document disagree, THIS AMENDMENT GOVERNS. Amended files stay byte-identical, as A1–A3 did.
changelog:
  - "1.1 (2026-10-16): D-OWNER-TESTS-20261016 replaces the A2 review-cap reference."
  - "1.0 (2026-10-15): created on the owner direction of 2026-10-15 ~17:00Z (native, in chat): pick one engine and close the other gracefully without losing its work; stop routing decisions to the owner immediately; the Wave 4 shortening decision delegated to the owner's analysis session; everything else from the restriction audit approved."
---

# Amendment A4 — one engine, no owner decisions, Wave 4 shortened

**Written for:** the cockpit session, the owner surrogate, every fleet job, and whoever next audits the campaign. §2–§5 are rules; §6 is the evidence; §7 is how success is measured.

## §1 · Owner direction (verbatim in substance)

Pick one of the two engines for the highest implementation velocity; the one not picked is put to graceful closure, its work preserved, then exited; from that point one engine only. Stop routing decisions to the owner: the institutionalised owner surrogate decides; this stops immediately, without excuses. The owner is not the right person to decide the Wave 4 shortening and delegates that decision to the analysis session, with the constraint "without losing the quality of the outcome substantially". Everything else from the restriction audit is approved.

## §2 · D-28 — the fast lane is the engine; the dispatcher lane is closed gracefully

1. **Decision.** The cockpit's fast lane (`cx.sh` → Codex job → `cx_post.sh` commit/push/PR → independent review → merge queue) is the campaign's only model-job engine from this amendment on.
2. **Why.** Jobs launched: fast lane 133 on 14 Oct and 64 on 15 Oct; dispatcher lane 43 and 0. The dispatcher lane's remaining work (GitHub call failures, slot-database provisioning races, qualification receipts) closes no Kāla capability.
3. **Graceful closure, nothing lost.** (a) Live `J-*` jobs finish. (b) `kyctl.sh stop dispatcher`; `in.marsys.kalayantra.dispatcher` unloaded; the planner, conductor and veto loops stay off (A1 D-11). (c) The dispatcher's merged code, `run/jobs` records, journals and receipts stay untouched. (d) `B-DB-BASELINE` → `not_applicable`, reason "dispatcher lane retired, D-28". (e) `KV3-B-OPS-CONTRACT` (#3485) is executor work (production operations, A1 D-13) and finishes under [D-OWNER-TESTS-20261016](DECISION_TESTING_STANDARD_v1_0.md): one bounded review round, a second only for a BLOCKING finding; real defects fixed regardless. (f) Fleet-lane worktrees: clean ones removed under the owner policy; dirty ones bundled to `/Users/Dev/Archives/` first. (g) The executor, tracker, test cluster, watchdog and launcher are kept: the fast lane uses them.
4. **The fast lane gains the dispatcher's one missing function: launch on ready.** When the tracker shows an item `ready` with a packet or task template and no live job for it, the launcher starts its build job without waiting for the cockpit. Review, acceptance and merge stay with the cockpit and the merge queue.

## §3 · D-29 — no decision reaches the owner

1. Effective immediately. Every decision item (`D-VC`, `D-COMPACT`, `D-G2`, `D-TEARDOWN`, `D-G9`, `D-CLOUD`, `D-FLIP`, `D-T2`, `D-GOCHARA-TIMEOUT`) and every future owner-wait is decided by the owner surrogate as a **conditional approval** ("approved when evidence X is present", X named), recorded in `run/DECISIONS_SURROGATE.jsonl`, so the Wave 4 chain never pauses for a ruling.
2. Owner reports carry no decision asks. Only A1 D-12's hard stops may reach the owner: credentials, production data deletion or restore, a FROZEN-contract change, the global HOLD. The one open owner action, a dedicated Codex credential for the fleet, is named once and then not repeated.
3. The 15 Oct "approve test-data teardown" request to the owner was a breach of A1 D-12 and is the last of its kind.

## §4 · D-30 — Wave 4 shortened (decided by the analysis session on the owner's delegation)

1. **Small-test run 2 is conditional.** `J-2c` and `J-2d` run only if run 1 is not clean. **Clean** = run 1's readback matches the expected census exactly; teardown proves absence with zero residual rows; no retry, timeout or manual intervention in the dispatch; the dry run's plan matched the real run. If clean, `J-2c` and `J-2d` are marked `not_applicable` with the detector evidence attached. Repeatability is still proven: the measuring build (`J-3c`, `J-3d`) dispatches and tears down again.
2. **Measuring build before final build stays.** `D-G9`, `D-COMPACT` and `D-VC` are answered from the measuring build's readings, so the final build cannot start earlier without guessing them. The hand-offs are pre-staged instead: the final-build job, the protected-window dispatch and the qualification job are prepared while the measuring build runs, so each hand-off takes minutes.
3. **Gates pre-decided.** All nine `D-*` items are decided under D-29 before the chain reaches them.
4. **Kept unchanged:** qualification and independent verification (`J-5q`, `J-5s`), live readback (`J-6l`) and the flip review (`V-J6`). They are the production acceptance.
5. Expected saving: one to two days of wall-clock on the serial chain, with repeatability still proven once by a real build-and-teardown cycle.

## §5 · D-31 — the rest of the audit, approved

Automatic protected-migration window after any migration-bearing merge (done 15 Oct); tracker health guard with a kill threshold of at least five minutes and a root-cause fix that moves git calls off the request path; sharding of the 30-minute SAMĪKṢĀ suite when convenient; medium model effort for mechanical jobs (merge resolutions, CI repairs, plan edits).

## §6 · Evidence of the day

| Observation | Value |
|---|---|
| Fast-lane jobs 14 / 15 Oct | 133 / 64 |
| Dispatcher jobs 14 / 15 Oct | 43 / 0 |
| Open decision items holding Wave 4 items | 9, about 30 items |
| Owner asked for a decision after A1 D-12 | 15 Oct, teardown (pending from 15:55Z) |
| Tracker hangs | 15 Oct 12:40Z and 16:50Z; blocked on per-worktree git calls inside the tick |
| Migration merged but unapplied until the window automation | 1380 (#3518, merged 10:44Z) |

## §7 · Success (72 hours)

| Measure | Target |
|---|---|
| Model jobs launched by the dispatcher lane | 0 |
| Items `ready` for more than 15 minutes with no job | 0 |
| Decision asks in owner reports | 0 |
| Wave 4 chain pauses waiting for a ruling | 0 |
| Tracker unavailable for more than 5 minutes | 0 |
