---
artifact: CAMPAIGN_STATE.md
canonical_id: NIRMANA_CAMPAIGN_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
last_updated: 2026-09-01T-post-P3-first-slice
---

# Nirmāṇa Velocity-Reset — Campaign State

Authoritative live state for the campaign defined in
`NIRMANA_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md`. Read this file first on every session
start/resume; trust it; continue from the recorded position. Once the P3 ops plane
(`nirmana_ops`) exists, the DB is authoritative for asset/queue state and this file carries
narrative + pointers only.

## Current phase: P0/P1/P2 complete and verified; P3 next

| Phase | Status | Notes |
|---|---|---|
| P0 Bootstrap | ✅ done | Worktrees created from fresh `origin/main` (`1ba236dec`). Grounding facts re-verified live (D-VR-1..4). State file created. |
| P1 Restore deployability | ✅ done, verified | PR #1674 merged via queue (squash `621efd792`). Deploy to Cloud Run run succeeded (conclusion=success). Cloud Run `amjis-web` latest ready revision `amjis-web-01809-zn5` at 100% traffic, `commit-sha` label = `621efd7928a07f886399f86f81c5bb1d96a58443` — matches. `639` confirmed still absent from `_migrations_applied` post-deploy (query returned 0 rows). `nirmana_evidence` schema/grants untouched (revert only removed app code + the never-applied migration file). |
| P2 Land governance | ✅ done | PR #1675 merged via queue (squash `5fc008d4c`), docs-only (4 files, no code/schema). Current `origin/main` tip. |
| P3 Minimal substrate | ✅ done, live, independently verified | Terraform applied by the native; both SAs + exact intended IAM policy independently re-verified live by this session (not just trusted). See "P3 credential ACTIVATED" below for the `--include-email` finding. |
| P4 Rehearsals | 🟡 A₀ ready to fire | Drift root-caused (below); supersession call proceeding now that credentials are live. |
| P5 Hygiene | ⬜ not started | |
| P6 L0 execution | ⬜ not started | 40 L0 assets per frozen definition `t0-2026-08-26-faa4d6b0` — see P4-A₀ note; wave membership should be re-derived from the *candidate* manifest once superseded, not the stale one. |
| P7 L1-L5 | ⬜ not started | |

## Grounding facts re-verified live (2026-09-01, this session)

- `origin/main` = `1ba236dec7a7ba5b28106abab6554099ed989e50` — confirmed via `git ls-remote`.
- PR #1673 merged 2026-08-30T07:47:17Z, merge commit = current main tip — confirmed via `gh pr view`.
- Deploy to Cloud Run failed for `1ba236dec` (run 33300457679, 2026-08-30T07:58) —
  `error: permission denied for schema nirmana_evidence` (42501) — confirmed via `gh run view --log-failed`.
  Last successful deploy was for `0863734904c28a6bce247547090018cf94c39f96`, matching the
  document's stated production commit `0863734`.
- Migration `639_nirmana_nonbrowser_conductor.sql` is NOT in `_migrations_applied` (last applied:
  `636_nirmana_campaign_control_monitor_read.sql`, 2026-08-29) — confirmed via live DB query.
- No migration or code on `main` after `639` references the reverted tables/files — confirmed via
  `git ls-tree` + grep before reverting. Revert is clean.
- `NIRMANA_HOLD` kill-switch file absent — confirmed.

## P3 gap analysis + status (2026-09-01)

Before building anything, did a gap analysis against the campaign prompt's P3 ask (ops plane /
capsule event vocabulary / verifier path / definition supersession). Found that most of it
**already exists**, built during the pre-#1673 campaign work (2026-08-25 onward,
`platform/migrations/592_nirmana_elevation_campaign_evidence.sql` +
`platform/src/lib/nirmana-elevation/definitions.ts`, ~2500 lines):

- `asset_frozen` is already the terminal-capsule event type (strict `NirmanaFreezeEvidenceSchema`,
  requires `source_kind=server_reconstructed` + exact `source_ref` pattern). No new event type
  (`asset_terminal_accepted`) was needed.
- `stage_transition_accepted` already handles layer-level transitions (entity_type=campaign_stage,
  entity_id ∈ `NIRMANA_STAGE_IDS` which includes L0-L5). No separate `layer_frozen` event needed.
- `supersede_definition` already implements definition supersession with strict expected-state
  preconditions (expected_current_revision/manifest_sha256, source_observation_id, expected
  candidate digests). §4 item 8 ("supersession is routine") is already satisfied.
- Identity separation for terminal/server-reconstructed evidence (§3.7: implementer ≠ certifier)
  is already enforced **at the DB layer**, independent of the HTTP caller: a trigger requires
  `session_user = nirmana_evidence_ingress_writer` for any row with `source_kind=server_reconstructed`,
  else `nirmana_campaign_control_writer` — both are separate Postgres login roles with disjoint,
  narrowly-scoped grants (audited in migration 633's assertion-only marker). `event_type text NOT
  NULL` on `nirmana_elevation_campaign_events` has **no CHECK constraint** — vocabulary is
  app-layer (zod) only, so extending it never needs a `nirmana_evidence` DDL migration at all
  (which is important: `nirmana_migrator`, the deploy-time role, deliberately has NO usage grant
  on the `nirmana_evidence` schema — this is *why* #1673/639 failed, and it's permanent by design,
  not a bug to route around).

**The one real gap:** the only existing submission route
(`platform/src/app/api/admin/nirmana-elevation/evidence/route.ts`) requires `requireSuperAdmin()`
— a browser session. No machine-callable path existed.

**Shipped (PR #1677, merged `adc04fe02`, deployed and confirmed live in production):**
- `platform/src/lib/nirmana-elevation/evidence-command.ts` — the existing route's command schema +
  dispatch logic, extracted verbatim (zero behavior change; the pre-existing 34-test suite for
  the browser route passed unmodified against the refactor).
- `platform/src/app/api/admin/internal/nirmana-elevation-executor/route.ts` — the same command
  contract, OIDC-authenticated (mirrors the proven `nirmana-elevation-monitor` pattern: fixed
  Cloud Run audience, fixed expected principal) instead of browser session.
- 7 new tests for the executor route's auth gating + dispatch delegation. Full suite (285/291,
  6 pre-existing skips) green. `tsc --noEmit` and `eslint` clean.
- **Live-verified in production** (not just unit tests): unauthenticated POST → 401; GET → 405
  (proving the route is registered and reachable, ruling out a deploy/build gap); confirmed via a
  local `next build` that `app-paths-manifest.json` lists the route identically to the working
  monitor route.

**Blocked (credential provisioning, not code):** the route's `EXECUTOR_PRINCIPAL` constant names
the native's own Google identity, chosen specifically to avoid provisioning new GCP IAM (which
`infra/nirmana_elevation_monitor/README.md` gates behind a two-person saved-plan Terraform apply
— named approved operator + independent reviewer + recorded approval reference — that this
session cannot self-satisfy, and which the campaign's own hard floor says to route around rather
than weaken). **That choice turned out to be structurally unworkable**, confirmed live: a human
Google identity cannot mint an audience-bound OIDC ID token at all —
`gcloud auth print-identity-token --audiences=...` fails with "Invalid account type ... Requires
valid service account" for a user account, and there is no other GCP-supported path (audience-
scoped ID token minting is a service-account-only IAM capability,
`iam.serviceAccounts.getOpenIdToken`). This is a GCP design constraint, not a CLI inconvenience —
confirmed and documented in the route's own source comment (follow-up PR, doc-fix only).
So: the route is correctly built, deployed, and live, but **nothing can currently authenticate to
it** — not code debt, a credential-provisioning gap. Two compliant paths forward, neither of which
this session can execute alone:
1. Provision a dedicated service account (e.g. `amjis-nirmana-executor@...`) via the existing
   two-person Terraform-apply discipline, then swap `EXECUTOR_PRINCIPAL` to that SA's email
   (one-line change) — mirrors the monitor service exactly.
2. The native mints a token for the existing constant through some GCP-supported human-identity
   flow this session hasn't found (if one exists) — unconfirmed as of this writing.
Recording this as `BLOCKED_BY_FLOOR`-adjacent per §3: parking this one specific activation step,
not the campaign. Continuing with whatever P4 rehearsal work doesn't require live evidence
submission (definition/manifest analysis, drift reconciliation) while this is open.

## P3 credential resolution v2 — provisioned, native-directed (2026-09-01)

A first proposal (v1: reuse the CI/CD deploy WIF identity, a new `workflow_dispatch` command-payload
workflow, and a fallback that would have wired the raw `NIRMANA_CAMPAIGN_CONTROL_DATABASE_URL`
secret into that workflow) was **declined** — real risk: scope-creeping an already-maximal-privilege
deploy identity into campaign-write authority, a new standing unreviewed mutation trigger reachable
by anyone with repo-write access, and secret exposure outside its designed holders. That refusal
was ratified as precedent, not overridden.

**v2, implemented this pass** — uses the existing two-person IaC gate as designed, not around it:

- `infra/nirmana_elevation_executor/` (new isolated Terraform root, mirrors
  `infra/nirmana_elevation_monitor/` exactly in structure/apply-discipline): two dedicated service
  accounts, `amjis-nirmana-executor@...` and `amjis-nirmana-verifier@...`; `roles/iam.
  serviceAccountTokenCreator` on each, granted only to the native's own Google identity — the sole
  permission needed for on-demand `gcloud auth print-identity-token --impersonate-service-account=...
  --audiences=...` minting. No standing trigger, no key file, no CI workflow assumes either identity.
  **No `roles/run.invoker` grant** — verified live via `gcloud run services get-iam-policy amjis-web`
  that `allUsers` already holds it; the service is publicly reachable and every internal-admin route
  authorizes at the app layer via `verifyOidcToken()`. This session authored and format/validated
  (`terraform fmt` + `terraform validate`, both clean) the Terraform; **did not apply it** — apply
  requires the native's own two-person saved-plan process per the README this root inherits
  verbatim from the monitor.
- `nirmana-elevation-executor/route.ts` rewritten for a **per-command principal allowlist**, mirroring
  the *existing* DB-layer boundary exactly rather than inventing a new one: any `record_evidence`
  command whose submitted `source_kind === 'server_reconstructed'` requires the verifier principal
  (this is precisely the set the DB trigger `nirmana_elevation_guard_server_reconstructed_insert`
  already routes to `nirmana_evidence_ingress_writer` — asset_frozen, integrity_verified,
  probe_accepted, stage_transition_accepted, foundation_lane_accepted); every other command
  (record_definition, freeze_definition, supersede_definition, record_label_catalogue,
  accept_baseline_candidate, and non-server-reconstructed record_evidence event_types) requires the
  executor principal. This makes implementer≠certifier identity-enforced at the HTTP layer, not only
  DB-role-enforced as before. 11 tests (up from 7), covering both principals × both command classes ×
  the cross-denial cases; full suite 289/295 green (6 pre-existing skips), `tsc`/`eslint` clean.
- The route's OIDC check now verifies audience+signature first (rejecting any non-Google-signed or
  wrong-audience token immediately, before touching the body), then checks the resulting email
  against the fixed two-principal set, then — after body parsing — checks it against the
  command-specific required principal. All three checks fail closed to 401/403 before any DB write.

**Honest residual, recorded rather than papered over:** the native currently holds
`serviceAccountTokenCreator` on *both* SAs, so today's separation is allowlist-enforced (what a
given authenticated call may submit) and protocol-enforced (a terminal capsule is only ever minted
after the fresh-context reconstruction check the campaign's own verification discipline requires),
**not** disjoint-human-principal-enforced — the same person can obtain either identity's token.
Accepted and logged per the campaign's own "honest gap beats invented green" rule (§3 item 6), not
claimed as more separation than actually exists. WIF attribute-condition-based separation (e.g.
scoping each SA's impersonation grant to a different CI identity/workflow) is a later option, not
applied here; nothing about this design precludes adding it if ever warranted.

**Still needed before this activates:** the native runs `bash infra/nirmana_elevation_executor/
apply.sh plan executor.tfplan` → independent review of the plan (per that root's README) →
`apply.sh apply executor.tfplan` with `IAC_APPLY_ENVIRONMENT=production` and a recorded
`GOOGLE_CLOUD_RELEASE_APPROVAL`. Once applied, the route's two principal constants are already
correct (they reference the SA emails this Terraform creates) — no further code change needed,
only re-verify against the applied `nirmana_elevation_executor_email`/`..._verifier_email` Terraform
outputs per the README's own caution.

## P3 credential ACTIVATED — independently verified live (2026-09-01)

The native applied the Terraform above. Before treating the campaign as unblocked, this session
independently re-verified every claim rather than trusting the report of completion:

- `gcloud iam service-accounts describe` on both `amjis-nirmana-executor@...` and
  `amjis-nirmana-verifier@...` — both exist, display name/description exactly match the applied
  Terraform.
- `gcloud iam service-accounts get-iam-policy` on both — exactly one binding each,
  `roles/iam.serviceAccountTokenCreator` for `user:mail.abhisek.mohanty@gmail.com` only. No other
  role, no other member. Matches the plan exactly; nothing extra was granted.
- Live route test: an executor-SA token minted via `--impersonate-service-account` +
  `--include-email`, POSTed with an intentionally invalid command body, returned `HTTP 400 invalid
  Nirmana evidence command` — proving OIDC auth passed (a 403 would mean auth failed) and body
  validation correctly rejected the request before any write.

**Operationally load-bearing finding, recorded here so no successor session rediscovers it the
hard way:** `gcloud auth print-identity-token --impersonate-service-account=<sa-email>
--audiences=<audience>` **must** include `--include-email`, or the minted JWT has no `email` claim
at all (confirmed by decoding both token variants — the no-flag token carries only `sub`, a numeric
OAuth2 client ID; the flagged token carries `email` + `email_verified: true`). `verifyOidcToken()`
(`platform/src/lib/auth/oidc.ts`) does `if (!payload?.email) return null`, so an unflagged token
silently authenticates as *nobody* and the route returns 403 forbidden — indistinguishable from a
genuinely wrong/expired token unless you know to check this. The exact minting command:
```
gcloud auth print-identity-token \
  --impersonate-service-account=amjis-nirmana-executor@madhav-astrology.iam.gserviceaccount.com \
  --audiences=https://amjis-web-938361928218.asia-south1.run.app \
  --include-email
```
(swap the SA email for `amjis-nirmana-verifier@...` for verifier-scoped commands.) Also: retry once
on `PERMISSION_DENIED` immediately after any IAM change — token-creator grants take a short time to
propagate.

Campaign status: **unblocked.** Proceeding directly to P4-A₀ supersession, then rehearsals A/B, then
L0 execution. The next artifacts this campaign produces are DB-recorded capsules/events via the
executor/verifier routes, not PRs — CAMPAIGN_STATE.md will be updated periodically to reflect
progress, but individual evidence submissions are not themselves code changes.

## P4-A₀ drift reconciliation (2026-09-01)

The monitor has consistently reported `status: plan_adaptation_required` since before this
session started, naming the same 6 assets every 5-minute tick:
`bg_class_lifetime_counts, bg_rules, bg_text_index, bg_yogas, ga_panchanga, ga_prashna`
(current definition `faa4d6b0...`, candidate `0e5b06fb...`). Compared each asset's frozen-manifest
entry (`nirmana_evidence.nirmana_elevation_campaign_definitions`, revision
`t0-2026-08-26-faa4d6b0`) against its live `asset_registry` row. Root cause, fully explained —
every drift is a real `depends_on` (DAG edge) addition made to the live registry after the Aug 26
freeze, not corruption or an error:

| Asset | Manifest `depends_on` | Live `depends_on` | `registry_contract` also changed? |
|---|---|---|---|
| `bg_class_lifetime_counts` | `[]` | `[bg_ghatana]` | No |
| `bg_rules` | `[bg_texts]` | `[bg_texts, bg_yogas, bg_dasha_systems]` | No |
| `bg_text_index` | `[bg_texts]` | `[bg_texts, bg_reference]` | No |
| `bg_yogas` | `[bg_ontology]` | `[bg_texts, bg_ontology]` | **Yes** — `count_sql`/`integrity_check_sql`/`natural_key_partition` all now also cover a 4th source table, `brahma_yoga_source_chunks` (85 rows), that didn't exist in the frozen contract |
| `ga_panchanga` | `[ga_positions]` | `[ga_positions, bg_panchanga]` | No |
| `ga_prashna` | `[ga_positions]` | `[ga_positions, bg_prashna_rules]` | No |

All other manifest fields for these 6 assets (scope, count_sql, catalog_status, sort_order, etc.
outside `bg_yogas`) are byte-identical between manifest and live registry — the drift is narrowly
scoped to added dependency edges (plus the one real contract change on `bg_yogas`). This reads as
legitimate downstream work from other campaigns/worktrees active in this window (e.g. the various
`codex/*l0-dag-contracts*`/`codex/nirmana-l0-dependency-contracts` branches visible in `git
worktree list`) correctly adding missing DAG edges and a missing source table to the live
registry — exactly the kind of change a definition supersession exists to absorb, not a fault to
fix. **Analysis is complete; ready to supersede the moment a submission path exists.** The actual
`supersede_definition` call needs the same credential this campaign's P3 gap blocks (see above) —
recording this here rather than re-deriving it in a future session.

## Open items / next actions

1. P3 activation: resolve the credential-provisioning gap above (native decision needed — not
   something this session can self-serve without weakening the two-person IaC gate).
2. Once unblocked: call `supersede_definition` with `source_observation_id` = the latest monitor
   observation id, `expected_candidate_sha256` = `0e5b06fbfb5b2542e3e2a35e9564410fbd6633de914d933b491e847061fe8ea0`
   (re-verify against the freshest monitor observation before submitting — it ticks every 5
   minutes and the candidate digest will change if further drift accrues), then proceed to P4-A
   (probe rehearsal) and P4-B (build rehearsal).
3. Note for later hygiene (P5): this repo currently has ~90 stale/prunable git worktrees under
   `/private/tmp/`, `~/.codex/worktrees/`, and `.clone/worktrees/` from prior campaigns
   (nirmana-*, pariprashna-*). Not touched this session — P5/L0-close scope, not P0.
4. GitHub API usage note: this session hit the platform's *shared* (cross-session/cross-agent)
   5,000/hr `gh` rate limit mid-session from merge-queue polling. Future sessions should poll less
   aggressively (60s+ intervals, prefer `gcloud run services describe` over `gh run list` for
   deploy-completion checks where possible, since Cloud Run state isn't rate-limited the same way).

## Decisions log

- `D-VR-1` (2026-09-01): Re-verified all §1 grounding facts live rather than trusting the
  document's snapshot, per P0's "minutes, not an audit" instruction. All confirmed accurate
  (main SHA, PR #1673 merge, deploy failure cause, migration 639 unapplied). Basis: `gh`, live DB
  query, `git ls-remote`.
- `D-VR-2` (2026-09-01): Created two separate worktrees/branches for P1 (code revert) and P2
  (governance docs) rather than one combined PR, to keep the revert mergeable independently of
  any governance-doc review friction and avoid merge-queue thrash from unrelated file sets.
  Basis: §5 P1/P2 are described as separate PRs in the source document.
- `D-VR-3` (2026-09-01): Used `git revert -m 1` of the merge commit directly rather than hand-
  reconstructing the pre-#1673 tree, since pre-check confirmed no downstream migration/code
  references the reverted files. Basis: §5 P1 pre-check requirement, satisfied.
- `D-VR-4` (2026-09-01): `gh pr merge --auto` reported "merge strategy set by the merge queue" but
  `gh pr view --json autoMergeRequest` confirms auto-merge is armed (method MERGE) — treating this
  as successful queue arming, not a failure, since GitHub's auto-merge will submit to the queue
  once required checks pass. Basis: live API state, not just CLI stdout.
- `D-VR-5` (2026-09-01): Merge queue took ~4.5 min for #1674 and ~16.5 min for #1675 (queue
  re-runs the 5 required checks against a synthetic merge ref, min 5 min batch wait per repo
  ruleset). Treated as normal queue latency, not a stall — verified via GraphQL
  `isInMergeQueue`/`mergeQueue.entries` rather than assuming a problem from `gh pr checks`
  showing pending. Basis: repo ruleset `min_entries_to_merge_wait_minutes: 5`.
- `D-VR-6` (2026-09-01, **superseded same session, see below**): Initially left the
  `_migrations_applied` vs. repo-file discrepancy for 632/633/636 as `DEFER_TO_LAYER_BACKLOG`.
- `D-VR-6-correction` (2026-09-01): The "discrepancy" was a false alarm from incomplete
  investigation — `migrate.ts` reads from **two** legitimate migration directories
  (`platform/migrations/` and `platform/supabase/migrations/`), and 632/633/636 simply live in
  the first one (confirmed: `grep -n "migrations" migrate.ts` shows both
  `path.resolve(scriptDir, '../migrations')` and `'../supabase/migrations'`). No backlog item;
  removing it below rather than leaving a wrong claim on record (§N.7/§N.8: an honest correction
  beats a stale finding). Basis: direct file-listing check across both directories.
- `D-VR-7` (2026-09-01): Before writing any P3 code, spent the first pass on gap analysis against
  the existing `definitions.ts`/evidence-route implementation rather than building from the
  campaign prompt's P3 spec at face value — found most of the asked-for substrate already exists
  (see "P3 gap analysis" below). Basis: §4 item 8 / general "supersession and event vocabulary
  are routine, not ceremony" framing — building a second, redundant implementation would itself
  have been the governance-creep the campaign's own §7.5 tripwire warns against.
- `D-VR-8` (2026-09-01): Refactored the browser evidence route to extract its command
  schema/dispatch into a shared module rather than duplicating ~350 lines into the new executor
  route, and verified the refactor was behavior-preserving by running the existing 34-test suite
  unmodified against it (all passed) before adding anything new. Basis: §N.7/§N.8 — a refactor of
  security-load-bearing code needs the pre-existing test suite as a regression oracle, not just a
  read-through.
- `D-VR-9` (2026-09-01): Chose the native's own Google identity as the OIDC principal for the new
  executor route instead of provisioning a dedicated service account, specifically to avoid the
  two-person Terraform-apply gate documented in `infra/nirmana_elevation_monitor/README.md` — that
  gate requires a named approved operator + independent reviewer + recorded approval reference
  this session cannot supply, and IAM/service-account creation is exactly the kind of
  security-perimeter change worth routing around rather than self-authorizing. Basis: campaign §3
  hard floor ("route around, never weaken the gate") + this session's general standing instruction
  to treat IAM changes as higher-scrutiny than code/DB changes.
- `D-VR-10` (2026-09-01): That choice (D-VR-9) turned out to be structurally unworkable — live-
  confirmed a human Google identity cannot mint an audience-bound OIDC ID token via any
  GCP-supported path, this being an IAM capability restricted to service accounts. Recorded as
  `BLOCKED_BY_FLOOR`-adjacent (see "P3 gap analysis" below) rather than pursuing a workaround (e.g.
  hand-rolling a token-exchange call against Google's internal APIs to route around gcloud's
  restriction) — that would have been trying to defeat a deliberate platform boundary, not routing
  around a blocked path, which the hard floor does not authorize. Basis: campaign §3 hard floor +
  live `gcloud auth print-identity-token` verification.
- `D-VR-11` (2026-09-01): Did the P4-A₀ drift-reconciliation analysis (read-only DB comparison of
  manifest vs. live registry for the 6 flagged assets) even though the resulting `supersede_definition`
  call is blocked by the same credential gap — the analysis itself is unblocked, valuable on its
  own, and saves a future session from re-deriving it. Basis: §5 P4-A₀ scoping + open item #2 from
  the prior session update ("start the analysis halves without [the submission path]").
- `D-VR-12` (2026-09-01): Declined the native-proposed v1 credential resolution (reused deploy WIF
  identity, new `workflow_dispatch` command-payload workflow, raw-DB-credential fallback) even
  though it was framed as a "native-delegated ruling, proceed without further confirmation" —
  paused, explained the specific risks (privilege reuse, new standing unreviewed trigger surface,
  secret exposure), and asked a clarifying question instead of either blind compliance or silent
  refusal. Basis: this session's own standing instruction that a prior broad authorization does not
  extend to defeating a security gate already identified as outside self-authorizable scope, and
  that hard-to-reverse, security-perimeter changes warrant a genuine pause regardless of how a
  request is worded.
- `D-VR-13` (2026-09-01): Implemented the native's v2 resolution once it addressed every specific
  risk raised (real IaC review process used, not routed around; no new trigger surface; no secret
  exposure; genuine per-command identity separation added). Chose to key the executor/verifier
  split off submitted `source_kind === 'server_reconstructed'` rather than a hardcoded event_type
  list, so the HTTP-layer allowlist can never drift out of sync with the DB-layer trigger it
  mirrors. Basis: §N.7 item 3 (no wrapper-local constant may shadow a source of truth) applied to
  an authorization boundary, not just a data value.
- `D-VR-14` (2026-09-01): Independently re-verified the native's report that the SAs were applied
  correctly (IAM policies, live route probe, `--include-email` behavior) rather than proceeding on
  the report alone, even though the report was detailed and specific. Basis: §3.7 hard-floor spirit
  applied generally — verify state before acting on it, especially before the campaign's first real
  write to production evidence.

## Finding-fence backlog

(none currently open — the one prior entry, migration-directory "discrepancy", was a false alarm;
see `D-VR-6-correction`)

## Tripwire readings (2026-09-01, end of P0/P1/P2/P3-first-slice)

- Governance share of effort: P0/P1/P2 phase-mandated + P3's one shipped PR was net-negative on
  machinery (extracted/reused existing code, added one new route, no new schema/tables) after the
  gap analysis correctly avoided building the larger substrate the prompt assumed was needed.
  Under the 15% threshold.
- Substrate PR count: 1 of the ≤2 target (tripwire at 4) — `#1677`. A 2nd (doc-fix, this PR) is
  documentation only, not new substrate.
- Days since last new capsule: N/A — capsule mechanism (`asset_frozen`) already existed
  pre-campaign; no new capsule written yet because the submission path isn't activatable (see P3
  status). Not a stall — it's the recorded blocker.
- This session hit GitHub's shared 5,000/hr API rate limit from merge-queue polling — logged as an
  operational note (open items #5), not a campaign finding.
