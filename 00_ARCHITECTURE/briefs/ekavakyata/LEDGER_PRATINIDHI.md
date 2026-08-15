---
campaign: EKAVAKYATA
role: PRATINIDHI (native's decision proxy)
model: claude-opus-4-6
session_start: 2026-08-16T00:05+05:30
origin_main_at_start: 63049a6e327e46a552496d7fc3a66f87a67d5ee8
authority: EKAVAKYATA_EXECUTION_PLAN_v1_0.md section 3.2
law_order: >
  (1) Plan section 0 invariants (immutable),
  (2) CLAUDE.md section N standards (N.4/N.6/N.7/N.8/B.10/B.1),
  (3) Paripurna-2 corpus as factual record,
  (4) House precedents (PR#1287 counting rule; PURNATA admin-merge; S7 stall rule; PP2 write-race)
boundary: Cannot change section 0 invariants. SENTINEL verifies; PRATINIDHI decides — never both on one question.
---

# EKAVAKYATA — PRATINIDHI LEDGER (native's proxy rulings)

Sole writer: PRATINIDHI. One file, one writer — PP2 write-race lesson.
Every ruling below is final unless reversed by a later EKV-R citing new evidence.
Reversibility is noted per ruling.

## STANDING POSITIONS (pre-ruled; apply directly without a numbered ruling)

These positions derive from the plan's invariants and house doctrine. Any agent
may cite them by tag (SP-n). They do not consume an EKV-R number.

- **SP-1 SCOPE CREEP:** Refuse. Tonight ships the plan's lanes; new ideas go to
  HANDOFF notes for the morning session. Cite: plan section 0 "goal fixed, path
  adaptive" — agents may re-sequence but NOT change end-state.

- **SP-2 AMBIGUOUS CLASSICAL QUESTIONS:** Follow bg_dignity_reference data + BPHS
  citations already in-repo. If genuinely contested, choose the option that
  DISCLOSES more, never the one that claims more. Cite: CLAUDE.md B.10 (no
  fabricated computation) + section N.8 (earned signal).

- **SP-3 TEST SKIPPING / LEASE WIDENING / COUNTING UNMERGED AS DONE:** Refuse in
  all cases. Cite: plan section 0 invariant 1 (merged-and-live-verified, nothing
  less) + PR#1287 counting rule (authored != shipped).

- **SP-4 DEPLOY RED:** Revert first, diagnose second — always. Cite: plan section 8
  (deploy red -> revert-first). Revert is always safe; forward-fix requires a
  numbered EKV-R ruling.

- **SP-5 DB WRITES BEYOND SPEC:** Refuse any DB write not in C-01/C-02/C-04/E-03
  as specced in the plan. Cite: plan section 4 item 5.

- **SP-6 SENTINEL vs STREAM LEAD DISAGREEMENT:** Evidence wins. Order re-derivation
  from the source (code, DB, live tool call). Neither party's assertion substitutes
  for evidence. Cite: plan section 0 invariant 3 (FM-09).

- **SP-7 ADMIN MERGE:** Only by numbered EKV-R ruling with evidence of
  branch-protection livelock. Precedent: PURNATA admin-merge. Never preemptive;
  only after 2 real failed attempts via the normal path.

- **SP-8 STALE HEARTBEAT (stream crash):** SENTINEL detects (20min stale per plan
  section 8). Conductor relaunches. No PRATINIDHI ruling needed unless the relaunch
  itself raises a scope or isolation question.

## RULINGS

<!-- Format:
### EKV-R-<n>: <title>
- **Asked by:** <role/stream>
- **Question:** <what needs deciding>
- **Options considered:** <A/B/C with tradeoffs>
- **Ruling:** <the decision>
- **Rationale:** <specific rule from law_order cited>
- **Reversibility:** <reversible/irreversible + what reversal looks like>
- **Timestamp:** <ISO>
-->

### EKV-R-1: C-01 Migration DB Write Authorization — AUTHORIZED

- **Asked by:** CONDUCTOR (via C-01 kickoff, relaying Stream C / RTA-LEAD request)
- **Question:** May Stream E merge `origin/ekv/c-01-ledger-repair` to `main`, which DELETEs 6 rows from and ADDs a CHECK constraint to `brahma_prospective_ledger` (a product table requiring PRATINIDHI sign-off per LEASES.json `db_rules`)?
- **Evidence reviewed:**
  - Commit `216fb0024` on `origin/ekv/c-01-ledger-repair`: migration `572_ekv_c01_ledger_empty_daterange_repair.sql` + writer fix in `w45_post_fit_rebuild.py`.
  - Migration SQL inspected line-by-line: DELETE scoped to `isempty(observation_window) AND filed_by = 'w45_post_fit_rebuild' AND generator_class = 'engine' AND filing_method = 'explicit_filing_tool'`. Safety abort if any unexpected empty-range rows remain post-DELETE. CHECK constraint `NOT isempty(observation_window)` added via `IF NOT EXISTS` guard.
  - Root cause is sound: `daterange(d, d)` with default `[)` bounds produces an empty range; PostgreSQL CHECK semantics treat `NULL > NULL` as a pass, letting these through the existing `shape_fields_check`. Six such rows confirmed garbage (zero-length observation windows that crash `standing_predictions_read` and can never be matched or resolved).
  - Writer fix (C-02 bundled): `if window_end <= window_start: window_end = window_start + timedelta(days=1)` — prevents recurrence at INSERT time.
  - Idempotency: DELETE WHERE is safe on already-deleted rows; constraint creation guarded by `IF NOT EXISTS`. Re-apply safe. Compliant with CLAUDE.md §N.4 ("never edit a migration after it has been applied").
  - All 57 w45 unit tests pass per commit message.
  - Post-deploy verification contract documented in migration header (4 assertions for Stream E to run).
- **Ruling:** AUTHORIZED. Stream E (SANGAMA) may merge `origin/ekv/c-01-ledger-repair` to `main`.
- **Conditions:**
  1. Stream E MUST run all 4 post-deploy assertions documented in migration 572's header and record results in LEDGER_E.md before marking this lane LIVE.
  2. Per §N.4: migration file `572_ekv_c01_ledger_empty_daterange_repair.sql` MUST NOT be edited after it has been applied. Any correction requires a new migration number.
  3. The PR description must cite this ruling number (EKV-R-1) as the PRATINIDHI authorization.
- **Rationale:** Plan §2-C-01 specifies this repair. LEASES.json `db_rules` require PRATINIDHI sign-off for product-table writes. The migration is conservative (scoped DELETE, safety abort, idempotent), the root cause is diagnosed and prevented by the bundled writer fix, and the existing rows are confirmed garbage that actively break a serving surface. Low risk, high value.
- **Reversibility:** Reversible. The 6 deleted rows are garbage (empty dateranges that crash application code and can never match). The CHECK constraint can be dropped by a subsequent migration if needed. However, reversal would require evidence that (a) any of the 6 rows carried real observational value (they cannot — empty ranges contain no dates), or (b) the CHECK blocks a legitimate future use case (it would not — `NULL` observation_window for chain-shape rows still passes, and any non-empty range passes).
- **Timestamp:** 2026-08-16T01:15+05:30

### EKV-R-2: Gate PROD-SYNC Check Fix — APPROVED (Option A)

- **Asked by:** STREAM E / SANGAMA-LEAD (EKV-R-01 in LEDGER_E.md)
- **Question:** The `ekv_gate.py` PROD-SYNC check is broken — it extracts a 12-char suffix from `catalog_version`'s `+r` field and compares it against `git rev-parse origin/main`, but the `+r` value is `SHA256(tool_names).slice(0,12)`, not a git SHA. This check always fails. How should it be fixed?
- **Evidence reviewed:**
  - Live `catalog_version`: `catalog-1+t152+r653c2a1a98c8` (from `mcp_server_info` call, documented in LEDGER_E.md SS2).
  - `origin/main` at session start: `63049a6e327e46a552496d7fc3a66f87a67d5ee8`.
  - Source: `mcp_catalog_version.ts:catalogContentHash()` = `SHA256(JSON.stringify(tool_names)).slice(0,12)` — this is a content fingerprint of the tool registry, never a git commit SHA.
  - `"63049a6e327e...".startsWith("653c2a1a98c8")` = FALSE. The check is structurally broken — it compares two unrelated hash domains.
  - This is an §N.8 defect class: the PROD-SYNC signal claims "deployed code matches origin/main" but the detector behind it checks a proxy (catalog content hash) that has no relationship to the claim (git commit identity). The signal is null, not green — and worse, it is always-false, making it a gate blocker for every merge.
- **Ruling:** APPROVED — Option A. The gate fix is the correct approach.
- **Implementation guidance:**
  1. `ekv_gate.py`'s PROD-SYNC check MUST be changed to compare `ekv_manifest.json`'s `deployed_main_sha` field against `git rev-parse origin/main`.
  2. Stream E (sole writer of `ekv_manifest.json`) writes `deployed_main_sha` to the manifest after each successful merge+deploy cycle, recording the actual git SHA that was deployed.
  3. The gate check becomes: `manifest["deployed_main_sha"] == subprocess.check_output(["git", "rev-parse", "origin/main"]).strip()` (or equivalent). This checks the actual claim (deployed code = origin/main tip) with evidence from the actual domain (git SHAs on both sides).
  4. The CONDUCTOR owns `ekv_gate.py` and makes this fix. Stream E owns `ekv_manifest.json` and writes the `deployed_main_sha` field.
  5. No source code changes are needed — this is a gate-tooling fix only.
- **Rationale:** §N.8 (Earned-Signal Principle): "every status, grade, or PASS must be computed by a detector that measures the specific claim it asserts; a signal without such a detector is null, not green." The current PROD-SYNC check asserts "deployed code matches main" while comparing a catalog content hash against a git SHA — two unrelated namespaces. Option A replaces the broken proxy with a direct claim-matching check: git SHA on both sides.
- **Reversibility:** Fully reversible. The fix changes gate tooling only (no production code, no DB, no migrations). Reverting to the old check would restore the always-failing state, which is strictly worse. Reversal would only be warranted if `deployed_main_sha` proved unreliable as a signal — in which case the fix is to improve the signal source, not to restore the broken check.
- **Timestamp:** 2026-08-16T01:15+05:30

### EKV-R-3: C-01 Retroactive Merge Legitimacy Audit — LEGITIMATE, NO REMEDIATION

- **Asked by:** GUARDIAN DESK (via supervised relaunch prompt, 21:30Z)
- **Question:** C-01 (migration 572 — DELETE 6 rows + CHECK constraint on `brahma_prospective_ledger`) has ALREADY been merged and marked LIVE. Was this legitimate given PRATINIDHI authority was never obtained? What remediation is required?
- **Evidence reviewed:**
  - EKV-R-1 (this ledger, above) was issued at 2026-08-16T01:15+05:30 (= 2026-08-15T19:45Z), explicitly authorizing Stream E to merge `origin/ekv/c-01-ledger-repair`.
  - `ekv_manifest.json` records `pratinidhi_signoff: "EKV-R-1"` with note `"AUTHORIZED 2026-08-16T01:15+05:30; 4 post-deploy assertions required"`.
  - Merge occurred at ~20:28Z per manifest merge_log — 43 minutes AFTER EKV-R-1 authorization.
  - All 4 post-deploy assertions passed at 20:50Z per manifest: `ekv_r1_assertions_passed: true`, note: `"All 4 passed at 2026-08-15T20:50Z: migration=1, empty_rows=0, CHECK fires, open_count=29"`.
  - EKV-R-1's 3 conditions verified met: (1) assertions run and recorded, (2) migration file not edited post-apply, (3) PR #1295 exists and cites EKV-R-1.
- **Ruling:** LEGITIMATE. No remediation required.
- **Rationale:** The guardian's concern ("your authority was never obtained") is factually incorrect — EKV-R-1 IS the authority, issued 43 minutes before the merge. The timeline is clean: authorization (19:45Z) → merge (20:28Z) → post-deploy verification (20:50Z). All 3 conditions from EKV-R-1 were satisfied. The lane's LIVE status is earned per §N.8. This is not a rubber-stamp — I independently verified the sequence from `ekv_manifest.json`'s own merge_log timestamps and the EKV-R-1 ruling timestamp in this ledger.
- **Reversibility:** N/A — no action required. If a future finding shows the migration caused harm, a remediation migration (new number per §N.4) would be the path, but no evidence of harm exists: the 6 deleted rows were confirmed garbage, and the CHECK constraint only blocks future empty-range inserts.
- **Timestamp:** 2026-08-16T02:55+05:30

### EKV-R-4: C-04 Degraded Scope — ACCEPTED AS PARTIAL; LANE STATUS = HANDOFF

- **Asked by:** GUARDIAN DESK (relaying Stream C / RTA-LEAD's request from LEDGER_C.md §C-04)
- **Question:** C-04's full lifecycle proof (`open -> matched -> resolved -> dismissed`, DB clean after) is structurally impossible — `withdraw`, `resolve`, and `dismiss` have zero write paths in the codebase. Stream C proposed a degraded scope: read-path proof post-deploy + match-path dry_run. Does this satisfy the W1 gate, or must C-04 be parked as HANDOFF?
- **Options considered:**
  - (A) Accept degraded scope as LIVE — mark C-04 as if the exit test passed with the reduced scope.
  - (B) Accept degraded scope as PARTIAL/HANDOFF — acknowledge the read+match proof but honestly record that the full lifecycle was never proven.
  - (C) Reject entirely — mark C-04 as FAILED.
- **Evidence reviewed:**
  - LEDGER_C.md §C-04 documents the block: `fileProspectivePrediction` works (FILE step), `standing_predictions_read` works post-C-03 (READ step), `matchOpenPredictionsForLelEvent` works (MATCH step). But `resolve`, `dismiss`, `withdraw` — zero write paths anywhere in the codebase. `mimamsa_outcome_record` routes to a RETIRED no-op. No `withdraw` action in `ALLOWED_ACTIONS`.
  - The manifest's exit_test for C-04 says: `"synthetic prediction driven open->resolved->dismissed; DB clean after"` — this is structurally impossible given the codebase tonight.
  - C-03 (the parseDaterange null guard) is itself HANDOFF status — it was ejected from the merge queue and not re-queued. Without C-03 deployed, even the READ-path proof would fail on the comparison chart's 2 empty-window rows.
- **Ruling:** Option B — ACCEPTED AS PARTIAL. C-04's status in the manifest MUST be `HANDOFF`, not `LIVE` or `VERIFIED`.
  - The degraded scope (read-path + match-path dry_run post-deploy) is the maximum achievable proof tonight and is valuable evidence.
  - However, the exit test as written (`open -> resolved -> dismissed; DB clean after`) was NEVER met — the write paths do not exist. Per SP-3 (no counting unachieved as done) and §N.8 (earned signal), the lane cannot be LIVE.
  - The missing write paths (resolve/dismiss/withdraw) are a real product gap, not a campaign failure. They should be recorded as a HANDOFF note for the morning session.
- **Rationale:** §N.8 (Earned-Signal Principle): "every status, grade, or PASS must be computed by a detector that measures the specific claim it asserts." The C-04 exit test claims a full lifecycle was driven; no code path exists to drive the resolve/dismiss steps. Recording LIVE for this lane would be an unearned signal. SP-3: "counting unmerged [or unachieved] as done: refuse."
- **Gate impact:** C-04 will count as HANDOFF, not LIVE, in any wave-closure tally. The wave can still close PARTIAL if all other W1 criteria are met.
- **Reversibility:** Fully reversible. When the resolve/dismiss/withdraw write paths are implemented (future session), C-04 can be re-run as a new lane that exercises the full lifecycle.
- **Timestamp:** 2026-08-16T02:55+05:30

### EKV-R-5: CL-00 Unrunnable — NOT-RUN; Wave Closes PARTIAL

- **Asked by:** GUARDIAN DESK (verified independently: `ekv_controls.py` exists only on `origin/ekv/lead-dharma`)
- **Question:** `platform/scripts/governance/ekv_controls.py` (the CL-00 cheap-subset gate) exists only on `origin/ekv/lead-dharma`, never merged to main. Stream D is dead. What is the acceptable path: (a) E merges `ekv/lead-dharma` to main first, (b) E runs `ekv_controls.py` directly from the dharma worktree, or (c) CL-00 is honestly recorded as NOT-RUN and the wave closes PARTIAL?
- **Options considered:**
  - (A) E merges `ekv/lead-dharma` to main. **Problem:** this merges ALL of Stream D's work (5 new governance lints + a CI workflow + the CL-00 harness) in one shot without review or CI verification. Stream D's own status is `BUILT`, not `VERIFIED` — no SENTINEL or PRATINIDHI review has occurred on D-01's content. This would violate SP-3 (counting unverified work as done) and the plan's own merge protocol (VERIFIED → MERGE_QUEUE → MERGED, not BUILT → skip-straight-to-MERGED).
  - (B) E runs `ekv_controls.py` from the dharma worktree path. **Problem:** the control checks the codebase it runs against. Running from the dharma worktree checks dharma's files, not main's deployed code. The CL-00 gate claims "these invariants hold on the deployed codebase" — running it against a different branch measures a different claim. Per §N.8, a detector must measure the specific claim it asserts: a PASS from a non-main worktree is not evidence about main.
  - (C) CL-00 is honestly recorded as NOT-RUN. The wave closes PARTIAL. **Cost:** the campaign cannot claim full gate coverage. **Benefit:** no false signal, no unreviewed merge, no measurement of the wrong target.
- **Ruling:** Option C — CL-00 is NOT-RUN. The manifest's `cl00_cheap_subset_last_run.result` stays `null`.
- **Rationale:** §N.8 (Earned-Signal Principle): a CL-00 PASS recorded without the control actually running against the correct target (main) is an unearned signal. Option A bypasses the VERIFIED gate. Option B measures the wrong codebase. Option C is the only path that does not produce a false signal. The wave closes PARTIAL — this is honest and the correct terminal state when a gate cannot be satisfied.
- **Standing position applied:** SP-3 — refuse to count unverified or unachieved work as done.
- **Reversibility:** Trivially reversible. When `ekv_controls.py` is properly merged to main via the normal VERIFIED → MERGE_QUEUE → MERGED flow, CL-00 can be run and the result recorded. The PARTIAL can be upgraded to a future campaign's clean gate if warranted.
- **Timestamp:** 2026-08-16T02:55+05:30

### EKV-R-6: Merge-Quiescence — DECLARE FREEZE; B-01 and A-09 PARKED

- **Asked by:** GUARDIAN DESK (verified independently: deployed_main_sha `33dfb2ba1` trails origin/main `44d5ff5a7`)
- **Question:** Should the conductor declare a merge freeze to let `deployed_main_sha` converge with `origin/main` so the W0 gate can run? What happens to in-flight W1 lanes (B-01 rebase, B-05 queue) during the freeze?
- **Options considered:**
  - (A) Declare freeze immediately, let no more PRs merge. E deploys current main tip, updates `deployed_main_sha`, runs gate.
  - (B) Let all currently-queued, CI-green PRs drain through the merge queue first, THEN freeze. Deploy the resulting main tip.
  - (C) No freeze — keep merging and hope the deploy catches up. **Problem:** this is a race condition that can never resolve; each merge moves the target.
- **Evidence reviewed:**
  - `deployed_main_sha` in manifest: `33dfb2ba1a2a900ef641d82755f8cc14426c2104` (A-02 deploy confirmed 21:03Z)
  - `origin/main` tip: `44d5ff5a76094aac4deaa148f1f3f3b43bd7845e` (B-04 merged 21:20Z)
  - Multiple PRs in auto-merge queue: A-07, A-08, A-09, A-11, A-12, A-13, A-15, A-16, A-17, B-05
  - B-01: CI_FAILED, needs rebase — Stream B is dead; no one alive to rebase
  - A-09: CI_FAILED — Stream A is dead; no one alive to fix
  - B-05: CI-green, in merge queue
- **Ruling:** Option B — DRAIN-THEN-FREEZE.
  1. **Let the merge queue drain naturally.** All currently-queued PRs with passing CI (A-07, A-08, A-11, A-12, A-13, A-15, A-16, A-17, B-05) merge via the existing auto-merge mechanism. No new PRs are queued after this ruling.
  2. **PARK B-01 and A-09.** Neither has a live agent to fix their CI failures. B-01 needs a rebase that requires resolving semantic merge conflicts in `ga_vargas_writer.py` and `test_dignity_oracle.py` — this is not mechanical work and cannot be safely assigned to Stream E (wrong domain expertise). A-09 has a CI failure with no one to investigate. Both are honestly PARKED as HANDOFF.
  3. **After the last queued PR merges and CI passes on main:** Stream E triggers a deploy, waits for deploy success, records the new `deployed_main_sha` in the manifest, and IMMEDIATELY runs the gate. No new merges between deploy-complete and gate-run.
  4. **Gate window:** The freeze holds from the moment the last queued PR merges until the gate has run and its output is recorded. After the gate run, the freeze lifts (the campaign is either closing or the conductor declares next steps).
- **Rationale:** Option C is structurally impossible (race condition). Option A wastes the already-queued, already-CI-green W1 work that can merge unattended. Option B maximizes merged lanes while still guaranteeing a convergence window. B-01 and A-09 are PARKED per SP-3 (refuse to count unmerged as done) — their lanes' value is real but they cannot be LIVE tonight.
- **Reversibility:** Fully reversible. The freeze can be lifted at any time by a new EKV-R ruling. Parked lanes can be unparked in a future session.
- **Timestamp:** 2026-08-16T02:55+05:30

### EKV-R-7: Close Criteria Pre-Statement — CONFIRMED WITH AMENDMENTS

- **Asked by:** GUARDIAN DESK (pre-close discipline)
- **Question:** State now — in writing, before the close — exactly what PRATINIDHI requires to countersign the night's close, and what the honest terminal marker should be if those requirements are not met.
- **Pre-statement of close/countersign requirements:**

  **To countersign CLOSED (full success), ALL of the following must be pasted into this ledger's COUNTERSIGN LOG section:**

  1. **Gate output** — the full stdout/stderr of `ekv_gate.py verify` (or equivalent), showing exit code 0. Every check must PASS or be explicitly accounted for by a numbered EKV-R ruling that authorizes the deviation.
  2. **SENTINEL's independent re-run** — SENTINEL's own verification of all LIVE lanes' evidence, run independently of the conductor and stream leads. Must cover: (a) every LIVE lane's evidence file exists and is non-empty, (b) a sample of exit-test claims are independently re-derivable from the evidence, (c) no LIVE lane has a failing CI on its merged SHA.
  3. **PRATINIDHI's spot-check** — I will independently verify 3 randomly-selected LIVE lanes by: reading their evidence file, confirming the exit-test claim matches the evidence content, and confirming the merged SHA is reachable from `origin/main`.

  **If any of the above cannot be satisfied, the terminal marker is CLOSED-PARTIAL with:**

  - An honest tally: N lanes LIVE / M lanes MERGED / P lanes VERIFIED / Q lanes PARKED-HANDOFF
  - A named disposition for every non-LIVE lane (HANDOFF reason, blocking condition, what is needed to complete)
  - The gate output as-is (even if non-zero), with each failure annotated by its EKV-R ruling or honest gap

  **Known items that will prevent CLOSED (full) tonight, per rulings above:**
  - CL-00 NOT-RUN (EKV-R-5) — gate will report this as a failure
  - C-04 HANDOFF (EKV-R-4) — lifecycle proof not achievable
  - B-01 PARKED (EKV-R-6) — CI-failed, no alive agent to rebase
  - A-09 PARKED (EKV-R-6) — CI-failed, no alive agent to fix
  - C-03 HANDOFF (manifest: ejected from merge queue, not re-queued)
  - Missing evidence: `a02_whitelist_probe.json` (guardian's finding #3)

  **Therefore the expected terminal marker is CLOSED-PARTIAL.** This is not a failure — it is an honest close. The campaign achieved a substantial volume of merged, deployed, verified work (W0: 7+ lanes LIVE; W1: 3 B-lanes merged, multiple A-lanes in queue). The PARTIAL disposition honestly records what was not achieved and why.

  **What I will NOT countersign:**
  - A CLOSED marker with any LIVE lane whose evidence I cannot independently verify
  - A gate PASS achieved by suppressing, skipping, or re-defining checks without a numbered EKV-R
  - Any lane promoted from HANDOFF to LIVE without new evidence that the blocking condition was resolved

- **Timestamp:** 2026-08-16T02:55+05:30

## COUNTERSIGN LOG

<!-- Night-close countersign goes here ONLY after:
  1. ekv_gate.py verify exit 0 output pasted
  2. SENTINEL's independent re-run pasted
  3. PRATINIDHI's own spot-check of 3 random LIVE lanes' evidence
-->

## ESCALATION LOG

<!-- Self-escalations to maximum deliberation for irreversible calls -->
