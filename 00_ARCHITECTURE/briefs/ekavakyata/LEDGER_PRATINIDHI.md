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

## COUNTERSIGN LOG

<!-- Night-close countersign goes here ONLY after:
  1. ekv_gate.py verify exit 0 output pasted
  2. SENTINEL's independent re-run pasted
  3. PRATINIDHI's own spot-check of 3 random LIVE lanes' evidence
-->

## ESCALATION LOG

<!-- Self-escalations to maximum deliberation for irreversible calls -->
