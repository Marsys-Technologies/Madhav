---
artifact: KALAYANTRA_VELOCITY_AMENDMENT
version: "1.0"
status: PREPARED — owner-approved 2026-10-08 ~00:30 IST (surrogate retained at the owner's direction); APPLIES at the morning hand-over (Stage 0 of the Codex→Claude transition). Until then the charter v1.1 rules stand.
amends: KALAYANTRA_CAMPAIGN_CHARTER_v1_0.md (v1.1) §3, §4.2, §4.4, §5, §6, §8, §9, §10, §11 — this file wins where they disagree; everything not named here is unchanged.
produced_on: 2026-10-08
produced_in: 'Claude Code (Fable 5.1), owner session, from the measured event log of 2026-10-06 16:30Z → 2026-10-08 00:00Z and the Suvarṇa delegate''s account of its own speed-up (2026-10-08 00:20 IST)'
---

# KĀLA-YANTRA — velocity amendment (charter v2.0 rules)

**Written for:** the agents of the fleet and the owner. Agents read §1–§8 as rules. The owner reads §0 and §9.

## §0 · Why — what the first 31 hours measured

| Measure | Value | Reading |
|---|---|---|
| Items done | 31 of 181 | 20 were the swarm's own machinery; 11 were Kāla-side, of which 5 PRs carried engine code (~1,700 lines) |
| Agent-hours since the owner reset | 44 | builders 27, verifiers 12, surrogate 4 |
| Builder cycles | 585 | ~300 built; ~250 waited, renewed or spun |
| PRs opened / merged | 36 / 19 | 9 of the 19 merged were the conductor's own ledgers, digests and evidence records |
| Verdicts / rejected | 65 / 27 | ~4 rejections found a real defect; the rest were environment mismatch, hash pins, a moved head, or a deploy that failed for reasons outside Kāla |
| Verdict events per Kāla item | 3 – 8 | the same item re-verdicted at every pushed head |
| `NEW ITEM` reports | 93 | 83 about tooling and control, 4 about Kāla |
| Surrogate rulings | 92 | in a day and a half |
| Chatter events (heartbeat, note, ack, message) | 3,571 of 4,629 | the swarm talks about itself far more than it builds |
| Cycles to finish one small foundation item | 80 – 100 | 5 – 9 h claim→done; ~4 h of it was building |
| Minimum lead time per item under v1.1 | 3 – 4 h | local full test run + verifier full test run + CI + merge-group CI + deploy + second verdict, for items averaging 2.9 files |

The slowness is machinery, not computation. Suvarṇa's own account of its speed-up says the same and this amendment takes its shape: three working roles plus the owner's stand-in, risk-scaled single review, mutation tests inside the PR, automatic proof of deployment, one-line ledger, short single-purpose work units.

## §1 · Roles

| Role | Decides | Does not |
|---|---|---|
| **SŪTRADHĀRA (conductor)** — from the hand-over, the owner's interactive Claude session | every ordinary matter in one line: item order, splits and merges of items, queueing, pacing, model edits for real Kāla items | wait for anyone; write ledgers, digests or evidence PRs (the digest is `run/DIGEST.md`, overwritten each cycle; the record is the event log) |
| **ADHIKĀRIN (owner surrogate)** — retained at the owner's direction | (a) what the charter reserves to the owner's judgement (§9 of the charter, surrogate charter §2–§3) and (b) **anything that has waited one cycle without a decision**, so nothing ever waits for the owner | per-item rulings on tooling; narration; model edits; opening items. One line per ruling in `run/DECISIONS.jsonl` (`KYD-n`, ≤ 3 sentences, `supersedes` named). It is the stand-in, not a gate |
| **PARĪKṢAKA (verifiers)** | one independent review per PR that **writes Kāla data, changes a writer/reader, adds a migration, or touches the production boundary**; packet-exit reviews (§7) | review docs, prompts, model, fleet or ledger PRs (CI alone gates those); re-run the whole test suite; re-verdict a head whose diff has not changed |
| **KĀRAKA (builders)** | the engineering inside their item | wait in a cycle; file control-plane items (file a one-line `ky report` only when a defect stops two or more builders) |

Lanes k1…k8 (ceiling 8, raised to 12 by the conductor when READY exceeds free builders), v1…v3 (ceiling 4, raised when review wait exceeds 30 min), adhikarin, and the conductor.

## §2 · Items — one unit of real work, not one file

An item is a coherent engineering unit of **300 – 800 changed lines**, one branch, one PR, delivered with its tests and the mutations that must fail. The per-file splits of the v1.1 model are regrouped before the next family opens; items already running keep their shape. The regrouping (model PR at hand-over, applied by the conductor):

| v1.1 items | v2.0 item(s) | Note |
|---|---|---|
| K0a-3a, K0a-3b, K0a-3c, K0a-3 (join) | **K0a-3** | one PR: candidate tables migration + both sides + attestation (K0a-3a already running keeps its branch; 3b/3c fold into it) |
| K7-1a-common … K7-1a-explain, K7-1a-register, K7-1a (join) | **K7-1a** | one PR: the seven service readers and their registration |
| KA-1-ephemeris … KA-1-coverage, KA-1-api, KA-1-facade, KA-1-writer, KA-1 (join) | **KA-1e** (engine: ephemeris, events, geometry, contacts, coverage, api) and **KA-1w** (facade + writer) | two PRs |
| K4-2a-schema … K4-2a-qualify, K4-2a (join) | **K4-2a** (schema + algebra + jaimini + groups + agreement + contests) and **K4-2aw** (writer + qualify) | two PRs |
| K6-1, K6-2, K6-3 | **K6-123** | one PR, three additive migrations |
| K8-K0a … K8-K7 (eight registration items) | folded into each packet's last K item as a declared step | K8-R26 and K8-REG stay |
| K9-2, K9-3 | **K9-23** | one PR |
| B-* backlog not yet claimed (B-WAKE, B-CLAIM-RECOVERY, B-K-INBOX, B-DB-BASELINE …) | **cancelled**, except B-DB-BASELINE (it blocks L0) | the control plane is finished (charter rule 10); fleet defects are fixed by the conductor's own session, not modelled |

Decisions `D-*` stay as they are (they are ADHIKĀRIN's). Packet exits `V-*` stay (§7).

## §3 · The work unit — take one item, finish it

Replaces charter §5. A builder cycle is **one item worked to its finished PR**, cap 3 hours, with `ky renew` and a one-line heartbeat every 20 minutes. There is no "one slice and exit". Orientation per cycle is the role prompt, `kybrief <ID>` and the plan sections the brief pins; the charter is read once per item, not once per cycle. A builder whose item is waiting (review, merge, ruling) takes the next READY item; the tracker allows one running claim plus one waiting claim per lane. `IDLE-OK` only when nothing is READY and nothing is owed.

## §4 · Tests run once

- Builders run **the item's own tests and mutations** locally (`fleet/precheck.sh --item` mode: secret scan on the diff, compile, the brief's tests). The whole-suite local run is retired; **required CI is the full gate**, as it always was.
- The lane test environment equals the CI environment (one `KALA_ADMIN_DSN` convention, one `KALA_REQUIRE_DB=1`); the environment-mismatch rejection class is closed by construction.
- Verifiers review the **diff** against the pinned plan sections and run the item's tests and mutations at the PR head. They do not re-run the suite CI already ran.
- Mutation checks live **inside the PR's own tests** ("fails on base, passes on head", one assertion per oracle); a separate mutation stage is not run.

## §5 · Verdicts and completion

- **One pre-merge verdict** for a reviewed PR (§1 scope). It stays **valid across pushes that only merge `main` into the branch**: the tracker treats a verdict at head H1 as current for head H2 when every commit in `H1..H2` is a merge commit (`git rev-list --no-merges H1..H2` is empty). A push that changes the diff needs a new verdict.
- **Completion of a code-only item** = accepted verdict (where required) ∧ PR merged through the queue ∧ **containment**: a successful `Deploy to Cloud Run` run on `main` whose deployed sha contains the merge commit. Containment is **checked by the tracker** from the live run list and the repository, not by a verifier cycle (R-COORD-7 a; the deployed sha, never the run's head sha).
- **Data-writing items** (brief has `migration` or `op`) keep the **second, post-deploy verdict**: migration applied in production (ledger readback), registry rows as declared, deploy green.
- **Docs, prompts, model, fleet and ledger PRs** complete by merge alone; no verdict, no item unless they are a real Kāla deliverable.
- A verdict names what was run and what failed; a rejection names the defect in one sentence and the file. Hash pins, snapshot byte-equality and "runtime adoption unproved" are not findings unless the item's brief declares them as its acceptance.

## §6 · The control plane is finished — and stays finished

- No new control-plane items. A fleet or tracker defect that stops two or more builders is reported once (`ky report`, one line) and fixed by the conductor's session directly, under the owner's standing authorisation; everything else is noted and ignored.
- The conductor writes no ledger, digest or evidence PRs. Model PRs only add, split or merge **real Kāla items**. The campaign-level SESSION_OPEN/CLOSE stay as the two bookends; nothing in between.
- One heartbeat per cycle; a note only for a hand-over another lane must read; acknowledgements only for directions actually acted on.
- Budgets: builders 900 starts a day (now mostly long cycles, so far fewer starts), control lanes 300.

## §7 · Packet exits run beside the work, not in front of it

`V-*` packet reviews (Astra) start when a packet's items are done and run **in parallel** with the next family's start; the next family does not wait for them. A packet verdict is a gate only for `K9-4a` (publication) and the close. Blocking findings become items with the normal priority; they are not a stop.

## §8 · Agents

Not the lever. Eight builders saturate the current READY queue; after this amendment review becomes the limit first, then builders. The conductor raises verifiers to 4 when review wait exceeds 30 minutes and builders to 12 when READY exceeds free builders, and lowers them back. Workers are **single-purpose**: one item, one PR, done.

## §9 · What stays — the floor that costs no time

Credentials never in an agent's reach (executor boundary, env allow-lists); production data operations only through the executor under the §1 lease (narrowed by R-COORD-7 to data operations); no history rewrite, no writes to `main` outside the merge queue, no disabling of a check; required CI; one independent review for data-writing and production-boundary PRs; mutation tests for engine code; the frozen contracts of charter rule 1; the surrogate as the owner's stand-in so nothing waits for the owner.

## §10 · Application at the morning hand-over (Stage 0)

1. Pause merges and new claims for ~15 minutes; Codex conductor writes its last digest and stops; this session becomes the conductor.
2. Merge, CI-only: this amendment; role prompts v2 (`prompts/*.md`); tracker rules (`pravaha_tracker/completion.py`, `verdicts.py`: verdict validity across merge-only pushes; containment check; post-deploy verdict only for data-writing items; one running + one waiting claim per lane); fleet (`precheck.sh --item`, Claude lane launcher); the model regrouping of §2.
3. Reinstall the tracker snapshot; restart lanes with the v2 prompts; switch lanes to Claude one at a time (k8, v3 first), each watched for three cycles.
4. Measures to watch daily, written to `run/DIGEST.md`: lead time per item (claim→done), Kāla items done per day, verdict rejection reasons (defect vs ceremony), chatter ratio (heartbeat+note+ack+message ÷ all events), builder cycles that built ÷ all builder cycles.

**Expected effect:** lead time per item from 5–9 h to ~2 h; Kāla code throughput 5–8× the first 31 hours; about half the agent spend on the same output.
