<!-- Source: /Users/Dev/scratch.noindex/claude/madhav/20261011-kalayantra-v3/engines/surrogate/SURROGATE_ANSWER_06_AUDIT_AND_SCHEMA2.md -->
<!-- Original sha256: 9bbbe55a3dd79fecded46b0f23923b4d8c358af29dcaa198b7b226e90408facb; date: 2026-10-14 -->
# Owner-surrogate answers 06 and 07 — audit reconciliation for B-2; KV3-SCHEMA-2

Authority: the owner's standing delegation (PLANNER_STATE `active.owner_direction_overnight_20261013`). Read-only; nothing merged, nothing production. Verified from the assembly (`kalayantra-kv3-b-assembly-all`), the live `run/` state and the preview at `scratch.noindex/claude/madhav/20261013-kalayantra-v3-fleet/logs/audit_preview.out`.

---

## QUERY 6 — audit reconciliation at install step 10

**DECISION** — No class stops the install. The lean procedure stands: let install.sh reach step 10, write `run/AUDIT_RECONCILIATION.json` from the findings preflight actually prints, one short independent reviewer job checks record-vs-findings and the two verifiable claims below, rerun (the installer resumes; qualifications already PASS). Prepare the 14 known entries now so the rerun is minutes, not an hour.

**FOR THE BUILDERS**

What the audit measures (`platform/scripts/governance/pravaha_tracker/completion.py:27–30`): an item completed under `v_exact_head_then_deploy_containment` must show a reviewed-head verdict and a deployment-containment observation in the event log; `expired_worker` is an active claim whose lease passed. None of the three classes is about the installation's own safety.

Record shape (`fleet/preflight.sh:186–235`): `{"schema":"ky.audit_reconciliation/1","entries":[{"code","ref","disposition","authority"}, …]}` — exactly one entry per finding present at step 10, none extra. Review file `run/AUDIT_RECONCILIATION.review.json`: `{"verdict":"ACCEPTED","inputs":"<sha256 of the record bytes>","reviewer_session_id":"<reviewer job>","author_session_id":"<cockpit>"}`; the two ids must differ.

**Class 1 — `missing_deployment_containment` (B-1a, B-1b, B-1, K0a-0, K0a-1a, K0a-1b, K0a-1c, K0-SV).** Containment is provable, not waived: every one of the eight merge commits is an ancestor of deployments the log did observe (checked read-only: `d1999ce7f`, `775ea1a0b`, `40c24fbc1`, `7083b7513`, `bdb6a36ba`, `b66bfbd0a` are each contained in `7f40f5b49…` deployed by run 37738277949 (recorded for K2-1a) and in `4a7bd85ef…` deployed by run 38248866100 (recorded for K7-1a)). Entry wording:
- `disposition`: `contained_by_observed_later_deployment: merge <40-hex> is an ancestor of deployed main <40-hex> (GitHub run <N>, observed for item <X>); git merge-base --is-ancestor exit 0 on <date>`
- `authority`: `tracker deployment observation for <X> in run/EVENTS.jsonl + git ancestry; plan §6 containment = ancestry of the merge commit in a successful main deployment`
The reviewer re-runs the ancestry command itself (eight lines). No per-item deployment event is fabricated; the v3 readback will record them properly when the executor runs.

**Class 2 — `rejected_or_stale_verdict` (K2-1a, KA-2, K0a-2, KA-1w, K2-1b, K2-2).** All six are guarded-done v2 completions (merged, five of them with deployment containment recorded) whose verdict file sits at an earlier PR head than the final one (e.g. `run/verdicts/K2-1a.155d55c77….md` vs final head `49b2e7c5a…`; K2-2's verdicts at `96ca7295…`/`bbae97c5…` vs final `a456a0fa…`). The new audit's `accepted_verdict` only inherits across heads when given `repo` and the shared reviewed-patch predicate holds; `ky audit` in preflight evidently runs without it. Before writing the entries, run the predicate read-only for each pair (`fleet/kyverdicts.py`, verdict head → final head). Entry wording:
- predicate holds: `disposition`: `inherited_verdict: ACCEPTED at head <H_v> (run/verdicts/<file>) inherited to final head <H_f> by the shared reviewed-patch predicate (kyverdicts, checked <date>); completed by guarded event <ts>`; `authority`: `plan §14 B-1 KYVERDICTS inheritance predicate; tracker guarded completion event`
- predicate fails or cannot run: `disposition`: `re_review_owed: ACCEPTED at head <H_v>, final head <H_f> not covered; item remains done per v2 guarded completion <ts>; v3 schedules VERIFY at <H_f> before any dependent item claims it`; `authority`: `tracker guarded completion event; this reconciliation (owner-surrogate answer 06)`
Never relabel a verdict to the final head.

**Class 3 — `expired_worker` (18 at preview; most will survive).** Step 7 releases only the claim each lane's single record file currently shows (`install.sh:1462–1520`, one record per worker), so at most eight of the eighteen clear; claims the log shows but no file does go to `legacy.unresolved[]` and stay findings. For every survivor:
- `disposition`: `legacy_lane_claim_expired: lane <k> is stopped by run/STOP_<k> and cannot renew; no process of the v2 fleet is alive (install.sh step 0 scan); the claim is void by lease and is superseded by the v3 dispatcher's own claim on re-dispatch; item state unchanged`
- `authority`: `owner pre-authorisation B-2 (PLANNER_STATE active.owner_preauthorisations_20261013: v2 fleet stopped); install.sh step 0 STOP files and process-absence evidence; receipt legacy section`
Twelve of the eighteen items are already done; the entry is bookkeeping, not a claim about work.

**Any new class at step 10** (one the preview did not show): do not write a generic entry; bring the line here before the rerun.

**Procedure, confirmed:** (1) draft the 14 class-1/2 entries now with the ancestry and predicate checks done; (2) run install; on `FAILED step 10: audit`, read preflight's FAIL lines; (3) complete the record to exactly those findings; (4) one reviewer job (Claude area-reviewer config or Codex), brief: verify entry set equals the finding set, re-run the eight ancestry commands and the six predicate checks, confirm every STOP file exists, write the review file with the record's sha256; (5) rerun install.sh with the same `--action` (`kyaction retry` first if the record reads FAILED) — it resumes, skips published actions, re-checks receipts, re-runs preflight, writes the receipt.

**FOR THE OWNER (morning note)**
Asked: how to answer the new fleet's self-audit, which lists 32 old-system loose ends before it will accept the installation. I ruled: none of them stops the install; eight "not seen deployed" items are provably deployed (their code is contained in later deployments the log did see); six "verdict not at final head" items were accepted by the old fleet under its rule for regenerated files — we record which, and schedule a fresh check for any the rule does not cover; the expired claims are the old lanes you stopped tonight. One short independent review of that record, then the installer resumes.

**WAITS FOR THE OWNER** — nothing.

---

## QUERY 7 — KV3-SCHEMA-2: generation / legacy coexistence for the field tables

**DECISION** — Not a blocker for tonight's B-2 or B-3; it is the schema prerequisite for seven campaign items (VC-1/2, K5-2/2b, K6-4, K8-REG, K9-1) after installation. The product-class part is ruled here; the storage pattern is not new — copy the one this campaign already accepted for `kala_avadhi` (migration 1341, K1-2). The exact metadata columns are one cockpit design job.

**FOR THE BUILDERS**

**Ruled (product / owner-class):**
1. Old and new coexist; nothing is replaced. Legacy rows of `kala_field`, `kala_field_null`, `kala_field_salience`, `kala_field_snapshots` are an immutable partition `generation = 'legacy'`; every new build writes a candidate partition keyed by its generation and never updates or deletes a legacy or published row (the K1-2 compat clause, verbatim in K5-G1a's brief).
2. The owner sees exactly one generation at a time: the published head (`kala_layer_head`, compare-and-swap via `kala_core.manifest.publish_candidate`). Until a candidate is published nothing he sees changes; after publication the previous generation is retained for rollback (`rollback_head`), labelled, never served as current. A candidate is never served. Every served response carries the generation it was read from.
3. Readers resolve the generation only through the served head or `candidate_generation(ctx)` (the K0a lint); `mi_bhara/db.py:80–116` and any other unfiltered reader get `WHERE generation = <served head, 'legacy' until first publication>` as part of this prerequisite — a reader that mixes generations is a wrong result, not a transition.
4. Field and null metadata are stored as typed nullable columns on the candidate partition, legacy rows NULL; no JSONB blob stands in for a contract; a missing value is a typed null with its reason (§N.7.6), never a default.

**Storage pattern (copy 1341, not invent):** `ADD COLUMN generation text NOT NULL DEFAULT 'legacy'`; drop the old natural-key UNIQUE; partial unique index on the legacy partition with the old key (`WHERE generation='legacy'`); partial unique index on candidates with `(chart_id, generation, <natural key>)`; `asset_registry.integrity_check_sql` re-scoped to the legacy partition plus the candidate invariants, exactly as 1341 does for `ka_avadhi`. Snapshot linkage: `kala_field_snapshots` gains `generation` and `candidate_build_id` referencing `kala_layer_candidate(build_id)`; field/null/salience rows keep `field_snapshot_id` and gain `generation`; the candidate's `kala_layer_candidate.conventions` pins as_of and the time origin (K5-G1a's "as_of and the time axis pinned").

**Technical, one cockpit design job (no owner input):** the exact column list and types for the persisted `Experiment(estimand, conditioning)` and `NullResult(preparation_digest, denominator, verdict, reason, surrogate_diagnostic)` plus as_of/time origin, units, risk-set, suppression-mask digest; which of those live on `kala_field` vs `kala_field_null` vs the snapshot row; the migration number (allocated at job start; protected window because of the constraint replacement, as 1341 was); the disposable-DB acceptance the writer already listed (absent-on-base/present-after, unchanged legacy counts and values, same natural key in two candidates, duplicate refusal within one partition, old reader unchanged on legacy, idempotent rerun). Output: the KV3-SCHEMA-2 packet, kind schema-prerequisite, built after installation, applied to production only in the owner's window.

**Blocking?** No: B-2 installs tooling; B-3 runs on fixtures; this unblocks campaign items in Wave 1+. Write the design job when the dispatcher is up.

**FOR THE OWNER (morning note)**
Asked: how the new forecast tables should hold old and new results side by side, and what you see meanwhile. I ruled: old rows stay untouched, new builds go into their own labelled generation, and you keep seeing exactly what you see today until a new generation is explicitly published; then the old one is kept for rollback but not shown. The detailed column design is a routine job after tonight's installation; it does not hold anything up tonight. Applying it to production stays in your window.

**WAITS FOR THE OWNER** — nothing (the production application of the migration is already his window).
