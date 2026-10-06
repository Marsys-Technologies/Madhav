---
artifact: KALAYANTRA_CHARTER_RECONCILIATION
version: "1.0"
status: CURRENT — the record of how the execution design v1.1 answers Astra's review of v1.0
date: 2026-10-06
reviews: 'reviews/ASTRA_REVIEW_KALAYANTRA_CHARTER_v1_0.md (verdict REWORK, 27 findings, 11 blocking; reviewed commit dee68bae)'
reconciled_by: 'Claude Code (Fable 5.1), the setup session'
result: '27 of 27 accepted (2 with a narrower remedy than the reviewer proposed, stated). 0 refuted. 9 further defects found by the setup session itself while applying the remedies (§3).'
---

# KĀLA-YANTRA execution design — reconciliation with Astra's review

**Written for:** the fleet's verifier and owner surrogate, and any later reviewer who needs to know why the design is what it is.

## §1 · Outcome in one paragraph

Astra's verdict on v1.0 was right: the fleet could start, but it could not guarantee exclusive ownership, review before merge, a safe Gochara sequence or an honest close. Every finding is accepted. The design changed in six places that matter: (1) the control plane becomes a work package with acceptance cases, and no implementation worker runs before it is reviewed, merged and accepted; (2) production credentials live in one operator-run executor that runs only merged code; (3) the Gochara absorption is re-cut into twelve ordered landing phases with the flip gate tightened; (4) the plan model is regenerated with a brief per item, a mandatory flag and a join over everything; (5) every merge carries a deploy-compatibility predicate; (6) the close is honest — a failed gate ends `CLOSED-PARTIAL`, not `CLOSED` and not a stall.

## §2 · Finding by finding

| Finding | Severity | Disposition | Where the remedy lives |
|---|---|---|---|
| **KY-01** specifications absent from the worktree | BLOCKING | Accepted. The five plan documents are committed on the campaign branch; their hashes are pinned in the charter frontmatter; `fleet/verify_specs.sh` checks them and is the first act of the kickoff and item B-0. | charter frontmatter; `fleet/verify_specs.sh`; item B-0 |
| **KY-02** claims neither exclusive nor per-worker | BLOCKING | Accepted. `claim/renew/release` with `worker_id`, lease, an exclusive lock on the event log and expiry recovery are B-1b deliverables with named tests. Until B-7, `run/KY_WORKERS` is 0 and one verifier runs, so no stream has two actors. | charter §4.1; item B-1b (16 named tests); `kalayantra_fleet.sh` (`wanted`) |
| **KY-03** completion bypasses review, dependencies, steps | BLOCKING | Accepted. `done` is a guarded conjunction (dependencies ∧ steps ∧ accepted verdict at the merged head ∧ detector); detectors are evidence, not state; packet exits are detected by a structured verdict file, never by a review's size. | charter §4.1, §4.4, §10; items B-1b, every `V-*` |
| **KY-04** credentials and file authority reach agents | BLOCKING | Accepted. Agents start under an allow-listed environment (`env -i`); the supervisor refuses to start with a secret in its environment; production operations go through `fleet/executor.py`, which reads its operations table and scripts from `origin/main` and runs a production operation in a private checkout of a merged commit. Residual same-account file access is stated, with the hardening path. | charter §3.2, §7, §15.1; `executor.py`; `kalayantra_fleet.sh` |
| **KY-05** bootstrap launches before its prerequisites | BLOCKING | Accepted. Bootstrap is items B-0 … B-8 in a fixed order; every K, L and J item has B-7 as an ancestor (asserted by the model generator); the kickoff is a short launch and never does bootstrap work itself. | plan model; charter §4.3; kickoff v1.1 |
| **KY-06** Gochara landing and test sequence invalid | BLOCKING | Accepted. J-0 is inventory and disposition; J-0m turns it into PR-sized children; twelve landing phases; nothing the small-test checklist keeps unmerged lands in phase 1; teardown and an absence proof follow each run. | charter §2.3; items J-0 … J-8 |
| **KY-07** G6 weakens flip eligibility | BLOCKING | Accepted. Every applicable protocol v2.3 co-primary endpoint and A5.7 gate must pass; `insufficient_evidence`, rank-unproven, VOID and UNVERIFIABLE do not authorise the flip; no retention alternative to a teardown. | surrogate charter G6, G7, KYD-7; items D-FLIP, D-TEARDOWN |
| **KY-08** seal and flip detectors wrong; migration 1236 blocks the flip | BLOCKING | Accepted. The reviewer's SQL is adopted (the seal predicate function; the authority join); the replacement CHECK migration is item J-6m; a live served response is required beside the SQL (J-6l). | items J-5s, J-6, J-6m, J-6l |
| **KY-09** final join incomplete | BLOCKING | Accepted. `JOIN-ALL` depends on every other item (asserted by the generator); a `coverage` block maps each algorithm card, each asset and each definition-of-done line to its items. | plan model `coverage`; item JOIN-ALL |
| **KY-10** deploys lack compatibility and lease gates | BLOCKING | Accepted, with a narrower remedy on leases: every item carries a deploy-compatibility predicate the verifier checks, and migration-carrying items need a post-deploy verdict; a lease is taken for production mutations the campaign performs, not for every ordinary merge, because deploy-on-merge is the repository's norm shared with other campaigns (stated as a residual risk). | charter §8 rule 8, §6 (4), §15.2; every item's `brief.compat` |
| **KY-11** no complete autonomous production path | BLOCKING | Accepted. Typed requests, a closed operations table, pre-acceptance receipts bound to the operation and the reviewed commit, post-operation readbacks, one production slot. Operations whose scripts are not yet reviewed are disabled and are enabled by named items (J-1a, J-3a, J-4b, J-4d, J-6m, J-6r, K9-3). | charter §7; `executor.py`; `executor_ops.json` |
| **KY-12** supervisor duplication and orphaning | HIGH | Accepted. Lane locks; a process-group controller that enforces the cap and reaps descendants; loops detached by double fork; supervisors run from a snapshot. | `kalayantra_fleet.sh` |
| **KY-13** budget and quota accounting incorrect | HIGH | Accepted. Atomic cycle reservations for every lane; the 80 % worker cap; quota markers read from the current cycle's log; a locked fleet-wide backoff. | `kalayantra_fleet.sh` (`reserve_cycle`, `mark_quota_backoff`) |
| **KY-14** "one generalisation" insufficient | HIGH | Accepted. B-1 is split into B-1a (the package), B-1b (eight capabilities) and B-1c (independent acceptance). | items B-1a, B-1b, B-1c |
| **KY-15** local database not a proven rehearsal environment | HIGH | Accepted. Seeded from a read-only production schema dump plus the applied-migrations ledger, then the project's own runner; assertions fail closed; all ten lane databases built and passed. | `local_db.sh`; charter §7; item B-3b |
| **KY-16** precheck not equivalent, not selective | HIGH | Accepted. Declared a fast local check, not the required checks; CI's accepted baselines (79 / 43, exit 3) honoured; explicit test manifest per item; real migration application. | `precheck.sh`; charter §6 (1) |
| **KY-17** value checkpoint precedes the full G1 | HIGH | Accepted. K5-G1a and K5-G1b land the full baseline and freeze it; VC-1 depends on K5-G1b. | items K5-G1a, K5-G1b, VC-1 |
| **KY-18** absorption misses inherited obligations | HIGH | Accepted. Authority replacement (J-6m), reader and rollback acceptance (J-6r), qualification (J-5q), upstream release (J-4a), protected window (J-4b), legacy retirement (J-7a), L5 hand-off (J-7b), Pravāha close (J-8a, J-8). | J lane |
| **KY-19** hand-over does not establish exclusive ownership | HIGH | Accepted. B-5 verifies no absorbed writer runs, extends the Pravāha model's streams, records the ruling, and is owned by the new steward. | charter §2.3 (a)–(f); item B-5 |
| **KY-20** handshake cannot truthfully satisfy governance | HIGH | Accepted. One campaign-level SESSION_OPEN as a YAML mapping with every required field, the real profile, a verified lease and enumerated globs; a CCD entry records the exception. | charter §8 rule 6; item B-4; SŪTRADHĀRA prompt |
| **KY-21** evidence paths and shutdown ownership inconsistent | HIGH | Accepted. Absolute runtime paths; the finalizer runs in the executor, outside the agents; lane `v1` is left running for the final acceptance and stops itself. | `finalize.sh`; charter §12; items C-3, C-4 |
| **KY-22** branch, PR and review protocol contradicts itself | HIGH | Accepted. One item, one branch, one PR; never rebase or force-push; workers never enable auto-merge; SŪTRADHĀRA queues only verdict-accepted heads; PR ownership by registered number. | charter §4.2; role prompts |
| **KY-23** units exceed the watchdog and verifier capacity | HIGH | Accepted. Known large items are split (K1-1, K2-1, K4-2, K5-G1, K7-1, J-2, J-3, J-4, K9-4); others are flagged "S splits" before any claim; long operations are dispatch, observe and accept children. | plan model |
| **KY-24** orientation underspecified | MEDIUM | Accepted. A fixed orientation set; every item carries a `brief` (`kybrief <ID>`). | charter §5; plan model `brief_keys` |
| **KY-25** dashboard can look healthy without progress | MEDIUM | Accepted. `ky audit` is a B-1b deliverable and the morning check; `status` says it is not proof of progress. | item B-1b; `fleet/README.md` |
| **KY-26** preflight incomplete and brittle | MEDIUM | Accepted. Two modes: `bootstrap` repairs local dependencies; `launch` requires every prerequisite and writes a receipt. | `preflight.sh`; item B-3 |
| **KY-27** stale descriptions and naming | LOW | Accepted, with a narrower remedy on file names: files keep `_v1_0` in their names by repository convention and carry the authoritative version in frontmatter. | all artefacts |

## §3 · Defects the setup session found itself while applying the remedies

1. **The absorbed campaign's tooling was not in git.** The tracker package, the Pravāha plan model, `MEASURING_BUILD_CONTRACT`, about sixty review records and the run directory's decision records were untracked files. The planned `git checkout origin/campaign/pravaha -- …` would have failed in the first hour. They are now copied onto the campaign branch (229 run-record files plus the package and model; two files flagged by the secret scan left on disk). The package's 29 tests pass once its model is present.
2. **The local secret scan could never pass.** With gitleaks installed the project scan reports 315 pre-existing findings that CI never sees, so every worker's precheck would have read red. Precheck now runs the scan as CI does and runs gitleaks on the diff's own files.
3. **The executor resolved script paths against the wrong folder** and required `requested_by: adhikarin` for every kind, which would have refused the conductor's finalize request and the verifiers' readbacks. Both corrected; requesters are per kind.
4. **The executor trusted the working tree.** It read its operations table and scripts from files any agent could edit. It now reads both from `origin/main` and runs production operations at a merged, reviewed commit.
5. **Running processes shared files with the editors.** The tracker, the supervisor and the executor now each run from a snapshot.
6. **A stuck join.** With no `not_applicable` state, a refused decision would have left its dependants, and the close, waiting forever. Decision outcomes are now final or open, and a dependant of a final other outcome becomes `not_applicable`.
7. **`ff-only` after a squash merge cannot work.** After the bootstrap PR merges, `wt/campaign` is detached at `origin/main` and only ever follows it.
8. **Database-backed tests would have been skipped silently in CI.** The required job collects sidecar tests by discovery but has no database; database suites run only from explicit lists. Item K0a-0 adds one additive job that runs the campaign's database tests with a skip counted as a failure.
9. **Facts corrected by the Suvarṇa campaign on 2026-10-06:** the criterion registry is at revision 26 on `main` (the plan was written against 25) — item K8-R26 reconciles the gate table first; `bg_parihara_rules` is pinned at 60 rows — L0-M coordinates one reseal; the L1 "settled" check is a line Suvarṇa posts on the coordination branch — J-4a's detector reads it.

## §4 · What is not claimed

The control-plane capabilities of B-1b do not exist yet: they are the fleet's first work, with tests named in advance and an independent acceptance. The J lane's children do not exist until J-0's inventory. Several executor operations are disabled until the items that land their reviewed scripts. Whether the empirical evaluation passes is unknown and is not promised.
