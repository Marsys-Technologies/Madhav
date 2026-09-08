# STATE_l2 — L2 Bodha lane (v2.5 overnight) — rewritten 2026-09-08T22:52Z (≈2026-09-09T04:22+05:30) — cycle #82

## POSITION

**bo_laksana remains FROZEN (cycle #81).** This cycle started the NEXT-in-DAG chain per
RESOLUTION_L2 v5 priority #2: **bo_bimba's W1 (`asset_analysis_accepted`) is now submitted and
independently DB-confirmed** — `event_id=38e49cca-2151-4476-b718-8c04f4a96fec`,
`definition_revision=t1-2026-09-08-be255ffe`, `source_kind=git_commit`,
`source_ref=git:04e6c0eeb...` (the currently-serving Cloud Run revision's commit-sha label,
independently confirmed live). **bo_bimba is now IN the chain (W1 done, W2/W3/build/W4/verify all
still ahead).** `bo_samskara` remains genuinely BLOCKED (see below) — do not attempt it as-is.

**PR hygiene (STEP 1):** `is:queued` empty (own PRs). #2472 (migration 934) and #2473 (migration
935) are both OPEN, auto-merge ARMED, `mergeStateStatus=BLOCKED` only because CI is still
IN_PROGRESS (not a real block — "Build Check (PR only)" and "Governance Gates" were both
IN_PROGRESS mid-run, everything else SUCCESS/SKIPPED as expected). No action needed, will
auto-merge once CI finishes. Re-check next cycle; if still not merged after several cycles,
investigate for real (don't just re-poll).

**Fleet slot: FREE.** No build_run dispatched this cycle — this cycle was evidence-submission
only (W1 for bo_bimba), no build.

## WHAT CYCLE #82 DID

1. Read RESOLUTION_L2 v5 + this file (cycle #81's write) fresh.
2. STEP 1 PR hygiene: confirmed `is:queued` empty; checked #2472/#2473 merge status — both
   auto-merge-armed, CI in progress, not actionable.
3. Checked issue #2450 (bookkeeping-only per STATE #81) — nothing new requiring action; the v2
   per-asset digest scoping ruling is already merged (#2461) and is exactly what this cycle's
   digest computation relied on.
4. **Read `STATE_l1.md` for contract status** (RESOLUTION v5 explicitly says re-check, don't
   assume v4's claim still holds) — found the L1 lane had, THIS SAME NIGHT, closed bo_bimba's
   `asset_output_digest_specs` gap (PR #2474, migrations renumbered 937/938 to avoid the
   collision with this lane's own 935 — confirmed no actual collision landed on `origin/main`,
   both lanes' numbering self-corrected) by proving `bo_bimba`'s `node_id` is a DETERMINISTIC
   identity (`assign_deterministic_node_ids()`, migration 714, D-CND-29/#1888) — safe to build a
   digest spec against. **L1 also found `bo_samskara` (+ bo_karanajala, bo_cgm_motifs,
   bo_cgm_paths, bo_sangati) still use a bare `uuid.uuid4()` for their primary identity column at
   every emit site — the SAME defect class #1888 already fixed for bo_bimba — and flagged this
   needs a WRITER-CODE fix (out of L1's DB-only scope), posted to #1770 for L2 (writer owner) to
   prioritize.** This is new, real information: **bo_samskara is NOT ready for W1/build dispatch
   as-is** — a fresh identity-column fix (bo_samskara.py, `embedding_id` per L1's grep) is a
   prerequisite, not something to skip past.
5. Verified via psql: `bo_bimba`/`bo_samskara` both registry-active with zero evidence rows;
   `asset_output_digest_specs` has `bo_bimba` but NOT `bo_samskara` (matches L1's account).
6. **Dispatched a FOREGROUND subagent (per Trap 106) to submit bo_bimba's W1.** It read
   `definitions.ts` (`canonicalNirmanaAssetAnalysisDigestForRegistryRow`, the #2450-ruling v2
   per-asset-scoped digest, merged via #2461) and `dispatch_nirmana_campaign_wave.py`'s
   `_live_registry_fingerprint`/`_current_analysis_receipt_digests` helpers, imported them
   directly (not reimplemented), computed bo_bimba's `registry_fingerprint_sha256`/
   `analysis_digest` fresh against the live registry row + frozen manifest + writer-digest
   generated file, **cross-validated the algorithm by re-deriving bo_laksana's ALREADY-ACCEPTED
   W1 digest and matching it byte-for-byte** before trusting the bo_bimba computation, resolved
   `source_ref` via the live Cloud Run revision's `commit-sha` label (not a stale reused SHA —
   correctly avoided the `assertNirmanaGitCommitMatchesDeployment` staleness trap), and submitted
   via `nrec --as executor` → **HTTP 201**.
7. **Independently re-verified from the main session (not just trusting the subagent):** psql
   confirms the row exists with correct `entity_id`/`event_type`/`definition_revision`.

Wall-clock: ~15 min main-session orchestration + subagent runtime (~197s subagent tool time,
~182k subagent tokens). Correctly bounded to ONE concrete step (W1 only) per RESOLUTION v5's "do
not let a cycle end without advancing it one concrete step" — did not attempt W2/W3/build for
bo_bimba this cycle, and correctly did NOT attempt bo_samskara at all once its blocker surfaced.

## NEXT ACTION (in order)

1. **bo_bimba W2 (`optimization_verdict_accepted`), executor identity.** Same digest-computation
   pattern as W1 — reuse `dispatch_nirmana_campaign_wave.py` helpers, cross-validate against a
   known-accepted row first. Then, if a build obligation exists, `implementation_accepted`
   (executor) → dispatch build via `dispatch_nirmana_campaign_wave.py --commit` (dry-run first)
   → `accepted_rebuild_observed` (executor) → `integrity_verified`+`asset_frozen` (FOREGROUND
   verifier subagent — Trap 106, never background this). **Watch for Trap 105:** if for any
   reason a re-verdict lands after an `implementation_accepted` is already in, recompute
   `decision_digest` fresh before submitting `accepted_rebuild_observed`.
2. **bo_samskara: do NOT attempt W1/build dispatch as-is.** Its writer
   (`bo_samskara.py`, per L1's grep — verify the exact file/column yourself, don't just trust the
   secondhand account) emits a bare `uuid.uuid4()` for its primary identity column
   (`embedding_id`, per L1) at every write site — the #1888/D-CND-29 defect class. Building an
   `asset_output_digest_specs` row (or, likely, `integrity_check_sql` too) against a
   non-deterministic key would silently produce a digest that "changes" every rebuild even with
   byte-identical content — a broken check wearing a working one's clothes (§N.8). **This lane
   OWNS bo_samskara's writer** — the fix is: give `bo_samskara.py` a deterministic identity
   function analogous to `bodha_cgm_node_identity()`/`assign_deterministic_node_ids()` (migration
   714, used for bo_bimba's `node_id`), scoped to bo_samskara's own natural key (whatever
   uniquely identifies a signal-embedding row: likely `(chart_id, signal_id, embedding_kind)` or
   similar — read `bo_samskara.py` to find the real natural key before assuming). This is
   plausibly a substantial standalone unit (writer-code change + migration + redeploy), likely
   its own future cycle rather than squeezed into whatever's advancing bo_bimba. Consider filing
   it explicitly as this lane's next work item once bo_bimba's chain is further along, or sooner
   if bo_bimba stalls on something orthogonal.
3. **bo_karanajala, bo_cgm_motifs, bo_cgm_paths, bo_sangati:** same defect class per L1's account
   (`edge_id`/`motif_id`/`path_id`/`cell_id`+`triangulation_id` all bare uuid4) — same caveat as
   bo_samskara applies to all four. Re-verify each independently before dispatching (don't chain
   off L1's account without checking the writer source yourself, per this lane's own standing
   discipline).
4. **Check PRs #2472/#2473 merge status** — should auto-merge cleanly once CI finishes (was
   IN_PROGRESS this cycle, not stuck). Also check #2474 (L1's migrations 937/938 for bo_bimba's
   output_digest_spec) — not this lane's PR to merge-babysit, but worth noting its merge state
   since bo_bimba's chain depends on that spec staying live.
5. #2450: bookkeeping-only OPEN, structural fix live (#2461 merged) — no further action unless
   explicit Conductor closure comment. #2443/#2447/#2446/#2415 OPEN, unchanged, not this cycle's
   scope. #2434/#2467/#2406 CLOSED. #1770 RULED, fix LIVE — resolved (now also carrying L1's
   bo_samskara-class writer-defect note, informational for this lane).

## TRAPS (permanent — cite before every future dispatch)

**NEW learning (cycle #82) — cross-lane migration-number self-correction:** L1's PR #2474 was
titled "migration 935/936" but its actual files are numbered 937/938 — it silently renumbered to
avoid colliding with this lane's own #2473 migration 935. No actual collision landed on
`origin/main` (confirmed via `git ls-tree origin/main` before trusting either lane's claim) — but
this means **a PR's TITLE can lag its actual migration numbers** after a same-night renumber;
always check `gh pr view <n> --json files` for the REAL file list, never trust the title alone
when reasoning about migration-number collisions across lanes.
**NEW learning (cycle #82) — writer-identity-defect chain, one layer deeper than #1888:**
`bo_bimba`'s `node_id` was already fixed to a deterministic identity (#1888/D-CND-29, migration
714) — but FOUR more L2 writers (`bo_samskara`, `bo_karanajala`, `bo_cgm_motifs`, `bo_cgm_paths`)
plus `bo_sangati` were found by the L1 lane THIS SAME NIGHT to still use bare `uuid.uuid4()` for
their primary identity column at every emit site. This blocks not just `asset_output_digest_specs`
authorship but plausibly `integrity_check_sql` too, for any of these five assets. **Before
dispatching W1/build for ANY not-yet-frozen bo_* asset, grep its writer source for
`uuid.uuid4()`/`uuid4()` on the primary-key column first** — a digest or integrity check built
against a non-deterministic key is a defect masquerading as a passing gate (§N.8), not a shortcut.
**Trap 106 (cycle #81):** for a fresh-context-per-cycle autonomous lane, prefer FOREGROUND
verifier/executor subagents over background ones — a background agent's completion notification
will NOT reach a future cycle's fresh session if the dispatching session has already exited.
Reserve background dispatch for genuinely fire-and-forget work with no bearing on this cycle's
bounded unit. (Applied correctly this cycle — the W1 submission subagent ran foreground.)
**Trap 105 (cycle #81):** submitting a re-verdict (`optimization_verdict_accepted`) for an asset
AFTER an `implementation_accepted` has already been accepted for it silently STRANDS that
implementation binding — `accepted_rebuild_observed` will reject with HTTP 409 "must bind the
exact current optimization decision" because the implementation's stored `decision_digest` no
longer equals `canonicalNirmanaOptimizationVerdictDigest` of the now-current verdict. **Fix:**
recompute the digest fresh against the LATEST verdict's `evidence_payload` and resubmit
`implementation_accepted` with the SAME `implementation_digest` but the NEW `decision_digest`.
**NEW learning (cycle #81) — layered SQL function grants:** a `SECURITY INVOKER` SQL function that
calls OTHER functions internally requires the caller to have its OWN EXECUTE grant on every
function in the call chain, not just the top-level one. Diagnosing the REAL Postgres error
requires `gcloud logging read` against Cloud Run — the HTTP layer only returns a generic 500.
**Trap 104 (cycle #80):** `gh run view`/`gh api actions/runs/{id}` can hit a secondary rate limit
— fall back to gcloud revision→digest→artifact-tag method, don't loop-retry.
**Trap 103/102/101/100/99 (cycles #75-79), 98-80(b) (cycles #65-74):** see git history.
**Table-name note:** the campaign events table is `nirmana_evidence.nirmana_elevation_campaign_events`
(columns: `entity_id`/`entity_type`/`event_type`/`layer`, NOT `asset_id`) — NOT any
`public.*event*`/`public.*lifecycle*` table (none exists). `asset_provenance_receipts` (public
schema) holds `output_digest`/`output_digest_spec_sha256`/`receipt_state` keyed by `build_id`.
See git history of this file for traps 1-99 in full detail.

## STANDING CONSTRAINTS (carried forward, verify each cycle)

- Live deployed commit as of cycle #82: **`04e6c0eeb` (#2470)**, unchanged this cycle (no app
  deploy needed — this cycle was pure evidence submission, no code/migration deploy). RE-VERIFY
  if working on anything deploy-sensitive.
- **Lane main worktree (`/Users/Dev/nirmana-s/l2`) is on branch
  `l2-bo-laksana-migration-935-signal-identity-namespace-grant`**, clean, up to date with its
  remote. Unchanged this cycle (no commits made — pure evidence/DB work, no code). Safe to build
  from directly next cycle, or `git fetch && git checkout origin/main` fresh once #2472/#2473
  merge.
- `nrec` = `bash platform/scripts/nirmana/nrec`; `--as executor` for W1/W2/implementation/rebuild/
  authorization, `--as verifier` for integrity_verified/asset_frozen. Schemas in
  `platform/src/lib/nirmana-elevation/definitions.ts` and `evidence-command.ts`.
- ONE non-terminal build_run per chart (fleet cap 3). **Fleet slot FREE.** No build dispatched
  this cycle.
- `--definition-revision t1-2026-09-08-be255ffe` always explicit.
- DATABASE_URL export each cycle: `postgresql://amjis_app:50mii04kTKDUUu54CAKdS4Bv2gx1IoWy@localhost:5432/amjis`;
  explicit `timeout 30` on every psql/dispatch invocation. Never `git stash`. No heartbeat branches.
  Never self-certify capsules. **Prefer FOREGROUND verifier/executor subagents** (Trap 106).
  `gh pr merge <n> --auto` bare flag only.
- Issues ledger: **#2434 CLOSED**; **#2467 CLOSED**; **#1770 RULED, fix LIVE**; **#2450 OPEN**
  (bookkeeping only, structural fix #2461 merged); **#2447 OPEN**; **#2443 OPEN** (stale);
  **#2446 OPEN**; **#2415 OPEN**; **#2406 CLOSED**.
- PRs: **#2472 OPEN, auto-merge armed, CI in progress** (migration 934 — grant already live
  independent of merge); **#2473 OPEN, auto-merge armed, CI in progress** (migration 935 — grant
  already live independent of merge); #2474 is L1's PR (migrations 937/938, bo_bimba
  output_digest_spec) — not this lane's to babysit but relevant dependency, check its state.
  #2470/#2469/#2468/#2466/#2464/#2463/#2461/#2460/#2458/#2457/#2454/#2453/#2452/#2451 all
  MERGED+LIVE (older). #2471 CLOSED PERMANENTLY (do not reopen).
- **Frozen under live t1 (`t1-2026-09-08-be255ffe`): bo_nakshatra_semantic, bo_special_lagna,
  bo_vargottama_dhana, bo_laksana.** bo_arudha/bo_sudarshana frozen under an earlier
  definition_revision (not re-verified under t1).
  **bo_bimba: W1 (`asset_analysis_accepted`) DONE this cycle — W2 onward is next cycle's job.**
  **bo_samskara, bo_karanajala, bo_cgm_motifs, bo_cgm_paths, bo_sangati: NOT STARTED, and NOT
  READY as-is** — all five carry the bare-`uuid4()`-primary-identity defect (see TRAPS above);
  writer-code fixes needed before W1/build dispatch would produce a trustworthy digest/integrity
  check for any of them.
