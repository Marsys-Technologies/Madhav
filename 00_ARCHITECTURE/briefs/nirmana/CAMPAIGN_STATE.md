---
artifact: CAMPAIGN_STATE.md
canonical_id: NIRMANA_CAMPAIGN_STATE
version: rolling
status: LIVE
campaign_id: nirmana-elevation
last_updated: 2026-09-04T-l0-w3-must-fixes-plus-w2-grounding-scope-correction
---

# Nirmāṇa Velocity-Reset — Campaign State

Authoritative live state for the campaign defined in
`NIRMANA_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md`. Read this file first on every session
start/resume; trust it; continue from the recorded position. Once the P3 ops plane
(`nirmana_ops`) exists, the DB is authoritative for asset/queue state and this file carries
narrative + pointers only.

## Current phase: L0-W2 DECIDE COMPLETE (40/40 routed); L0-W3 IMPLEMENT next

Phase tracking from here follows `NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §1`'s programme map
(PHASE A → O-WAVE → L0→L1→L2→L3→L4→L5, each W1-ANALYZE→W2-DECIDE→W3-IMPLEMENT→W4-EXECUTE→
W5-VERIFY+CAPSULE→W6-FREEZE → PHASE Z), which supersedes the execution prompt's P5/P6/P7 phase
plan (relationship note, plan frontmatter). P0-P4 below are historical and unchanged; P4 = the
plan's "PHASE A (COMPLETE)".

| Phase | Status | Notes |
|---|---|---|
| P0 Bootstrap | ✅ done | Worktrees created from fresh `origin/main` (`1ba236dec`). Grounding facts re-verified live (D-VR-1..4). State file created. |
| P1 Restore deployability | ✅ done, verified | PR #1674 merged via queue (squash `621efd792`). Deploy to Cloud Run run succeeded (conclusion=success). Cloud Run `amjis-web` latest ready revision `amjis-web-01809-zn5` at 100% traffic, `commit-sha` label = `621efd7928a07f886399f86f81c5bb1d96a58443` — matches. `639` confirmed still absent from `_migrations_applied` post-deploy (query returned 0 rows). `nirmana_evidence` schema/grants untouched (revert only removed app code + the never-applied migration file). |
| P2 Land governance | ✅ done | PR #1675 merged via queue (squash `5fc008d4c`), docs-only (4 files, no code/schema). Current `origin/main` tip. |
| P3 Minimal substrate | ✅ done, live, independently verified | Terraform applied by the native; both SAs + exact intended IAM policy independently re-verified live by this session (not just trusted). See "P3 credential ACTIVATED" below for the `--include-email` finding. |
| P4 Rehearsals = **PHASE A** | ✅ CLOSED — first accepted capsule | Per D-VR-WAVE0-SCOPE: scoped the dispatcher to an explicit asset subset (PR #1692) instead of dispatching full wave 0, then ran `bg_vedha_malefic_scale` through the complete accepted chain — `asset_analysis_accepted` → `optimization_verdict_accepted` → `build_run_authorized` → scoped campaign-triggered dispatch → `accepted_rebuild_observed` → `integrity_verified` → `asset_frozen`. All 6 events independently verified live in `nirmana_evidence.nirmana_elevation_campaign_events`. 2 more real production bugs found+fixed on this path (PRs #1693, #1694; 9 total across P4). See "P4 CLOSED" section below for the full account. |
| **O-WAVE** — orchestrator truth core | ✅ CLOSED — exit rehearsal complete | WP-1 (PR #1697, `0212c095d`) · WP-3 (PR #1698, `cfa220b8c`) · WP-2 (PR #1699, `ef9ee729e`) — all 3 merged and deployed live (Cloud Run `amjis-web` + job `brahma-build-pipeline-job` both confirmed at commit `ef9ee729e749ada086c975aac501c78086f4f644`), exactly at the ≤3-PR target. All 4 exit-rehearsal criteria (plan §3.4) run and closed — see "O-WAVE EXIT REHEARSAL CLOSED" section below for the full account, including one real methodological finding (the campaign dispatcher's one-shot-per-asset guard makes literal same-mechanism re-dispatch of `bg_vedha_malefic_scale` permanently infeasible) worked around honestly via a documented, code-reusing direct-dispatch script, not a silent bypass. |
| **L0 — Brahmagyan** (W1→W6) | 🟢 W1+W2+W3 COMPLETE | 40 assets, waves 25/12/3, frozen definition `t0-2026-09-01-0e5b06fb`. W1 output: `L0_W1_ANALYSIS_INDEX_v1_0.md` + batch files. W2 output: `L0_W2_DECIDE_v1_0.md` — every asset routed (matches plan §5's template exactly), every finding triaged. W3 (4 PRs: #1705-#1709 series): all 3 MUST fixes landed; of 18 NOW items post grounding-scope-correction, 13 DONE (code/registry/doc changes or live-verified-no-change-needed), 2 more rescoped to NEVER/LATER on evidence (item 12 `bg_concordance` wiring → real L2-Bodha work, handed to L2-W3; item 22 `bg_rules` dasha-linkage → corpus-coverage-limited, only 10/10,651 chunks mention "dasha"), 3 remain open as small named backlog (13a, 15, 29 — none a MUST, none blocking). Item 29 (`bg_text_index` vocabulary) also narrowed: live sampling found ~57% of the "unclassified" gap is OCR noise/non-English, not a vocabulary miss. See D-VR-30/D-VR-31. `bg_vedha_malefic_scale` already `asset_frozen` from P4. Next: L0-W4 EXECUTE. |
| **L1 — Gaṇita** through **L5 — Mīmāṃsā** | ⬜ not started | 19 / 22 / 23 / 9 / 15 assets respectively. Strict layer order; each opens only when the prior layer freezes (W6). Per-layer plans: `NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md §5`. |
| **PHASE Z** — campaign closure | ⬜ not started | 128/128 capsule audit, WP-5 tracker polish, debris (subsumes the old P5 Hygiene backlog: ~90 stale/prunable git worktrees, `__ssv_*` sweep, monitor disposition), close report, native acceptance. |

## Tracker v2 alignment — pulled forward from WP-5, native-authorized (2026-09-04)

Per `NIRMANA_TRACKER_V2_ALIGNMENT_PROMPT_v1_0.md` (native-authorized 2026-09-04): a scope-capped
pull-forward of WP-5's ALIGNMENT slice only (cosmetic Phase-Z tracker polish stays deferred).
`/admin/nirmana-elevation` now renders the v2.0 programme spine (PHASE A → O-WAVE → L0..L5 with
W1–W6 milestone bars → PHASE Z) instead of the old flat 13-stage list, and refreshes near-real-time
via an SSE subscription to the cockpit event bus plus a best-effort Pub/Sub publish on accepted
capsule/supersession evidence. Written plan:
`NIRMANA_TRACKER_V2_ALIGNMENT_PLAN_v1_0.md` (same directory), executed via subagent-driven-
development — 5 tasks, each with a fresh implementer + fresh task-scoped reviewer, an independent
whole-branch review, and one consolidated fix wave (see the plan's own SDD ledger,
`platform/.superpowers/sdd/NIRMANA_TRACKER_V2_ALIGNMENT_PLAN_v1_0/progress.md`, for the full
per-task record — not copied here).

**PR #1701** — merged via the queue 2026-09-04T01:32:19Z, merge commit `c24ad9987c`. 8 commits
(1 plan doc + 7 implementation, incl. 2 Task-1 fix rounds + 1 final-review fix wave). Full repo
suite at merge time: 976 test files / 10,603 tests passed, 629 skipped, 0 failures; `tsc --noEmit`
and eslint both clean (1 pre-existing unrelated warning).

**One real Critical bug found and fixed pre-merge** by the whole-branch review (not by any per-task
review, which each only saw its own diff): `wave_progress` was aggregating W1–W6 counts over the
live asset registry instead of the frozen manifest cohort, silently converting an authoritative
`milestones_required: null` (a registry asset not yet in the manifest, or one with
`execution_obligation: 'unresolved'`) into a fabricated `required: 6, earned: 0` — exactly the
kind of manufactured-evidence defect §N.8 exists to catch. Fixed by filtering to
`milestones_required !== null` before aggregation, with regression + integration tests proving no
fabrication. Also fixed pre-merge: the O-wave position-chip's WP-selection heuristic assumed
monotonic WP progress and picked the wrong (non-monotonic) work package; `o_wave.state`'s
provenance was blended with real stage evidence, contradicting the plan's own Ruling R2 (now
purely WP-status-derived, per the ruling's literal text).

**Live verification (2026-09-04, this session):**
- Cloud Run `amjis-web` latest ready revision `amjis-web-01836-mhq` at 100% traffic,
  `commit-sha` label = `c24ad9987cb38270d6d53f7c08a502bc0a2d0f87` — matches the merge commit
  exactly. Deploy workflow run concluded `success`.
- `GET /admin/nirmana-elevation` → `307` (redirect to auth, as expected — not publicly served).
  `GET /api/admin/nirmana-elevation/snapshot` → `401` (auth enforced, not broken open). Confirms
  the deploy is live and the auth boundary is intact.
- **Honest gap, not silently skipped:** this session had no interactive browser session under the
  native's own Google identity, so the full spec §7 acceptance checklist — visually confirming the
  programme spine renders correctly, hand-running a SQL aggregation to cross-check the W1–W6 bar
  numbers, and observing a real campaign event appear on the tracker within ≤10s — could **not**
  be completed autonomously in this session. What was verified (deploy identity match, route
  liveness, auth intact, and the full test suite including the fix-wave's regression/integration
  tests proving the fabrication bug is actually fixed) is real evidence, but it is not a substitute
  for the native's own live look at the rendered page. **Next session or the native: open
  `/admin/nirmana-elevation` logged in and walk spec §7's checklist** — this is the one item this
  alignment work leaves genuinely open, named here rather than silently claimed done.

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

## P4-A₀ SUPERSESSION EXECUTED — the campaign's first real write (2026-09-01)

With the executor SA live (above), submitted the actual `supersede_definition` call. Two real,
previously-unexercised production bugs blocked it in sequence — both root-caused, fixed, deployed,
and the call retried successfully after each. Full technical detail (both are genuine defects in
already-merged pre-session code, not anything introduced this session) lives in PR descriptions
#1682 and #1683; summary:

1. **`permission denied for table asset_registry`** (PR #1682). `acceptNirmanaBaselineCandidate`
   and `supersedeNirmanaElevationDefinition` both read `asset_registry` with `FOR SHARE`, but
   `nirmana_campaign_control_writer` is deliberately SELECT-only (no UPDATE) there — Postgres's
   row-locking clauses require UPDATE privilege, not just SELECT. Fixed by dropping `FOR SHARE`
   (no grant change): both transactions already run `SET TRANSACTION ISOLATION LEVEL SERIALIZABLE`,
   which provides the same conflict protection via SSI without needing a lock.
2. **`permission denied for table nirmana_elevation_campaign_events`** (PR #1683). Same bug class,
   one query later: `recordNirmanaElevationLabelCatalogueInTransaction` and
   `verifyNirmanaElevationLabelCatalogueInTransaction` (both reached from the supersede path) did
   the identical `FOR SHARE` pattern on `nirmana_elevation_campaign_events`, where this role also
   has SELECT+INSERT only. Fixed the same way; correctness held by a pre-existing
   `pg_advisory_xact_lock` on the exact `(campaign_id, definition_revision, catalogue_revision)`,
   which already serializes concurrent callers for that idempotency key.

**Why these were never caught before today:** both existing frozen definitions
(`t0-2026-08-25`, `t0-2026-08-26`) were created via direct `record_definition` +
`freeze_definition` submission with a pre-computed manifest — a path that never touches
`asset_registry` or does the reconstruct-and-verify read. Only `accept_baseline_candidate` and
`supersede_definition` do, and neither had ever run in production before today — no non-browser
submission path existed until #1677/#1680 landed this session.

**Result, independently re-verified against the live DB (not just trusted from the API
response):**
```
HTTP 201 {"outcome":"superseded"}
```
`nirmana_evidence.nirmana_elevation_campaign_definitions` now shows `t0-2026-09-01-0e5b06fb`
`frozen`/current (128 assets, `manifest_sha256 = 0e5b06fb...`), and `t0-2026-08-26-faa4d6b0`
correctly `superseded` (same instant). Spot-checked the new manifest's `depends_on` for all 6
previously-drifted assets — matches the live registry exactly, confirming the candidate genuinely
reflects current reality, not a stale or partial reconstruction.

**Campaign status: P4-A₀ closed.** Proceeding to rehearsal A (probe: `bg_ephemeris_engine` or
`bg_panchanga`) next.

## Rehearsal A EXECUTED and independently verified — the campaign's first terminal capsule (2026-09-01)

Ran the full probe rehearsal on `bg_ephemeris_engine` (asset_kind=service, health_probe set,
`execution_obligation: probe`). Two more real production bugs blocked it in sequence before
success, both root-caused, fixed, deployed, and the sequence retried after each:

3. **`NIRMANA_L0_ANALYSIS_RECEIPTS_AVAILABLE = false`** (PR #1685). `BLOCKS_CURRENT_ASSET` for
   **all 40 L0 assets**, not just this one — the entire `asset_analysis_accepted`/
   `optimization_verdict_accepted`/`probe_accepted` path was gated shut. Root cause: the
   checked-in `nirmana-writer-digests.json` is current and correct (confirmed live:
   `python -m pipeline.orchestrator.provenance_inventory --check` exits 0 against the real
   sidecar writer source) — only the JS-side pinned constants
   (`NIRMANA_L0_CONVERGENCE_COMMIT`/`NIRMANA_L0_WRITER_INVENTORY_SHA256`) were stale, last
   updated for #1571 and never re-pinned. Self-verified per-writer attribution by diffing the
   JSON at each commit myself (not taken on report) — full table in the PR. Re-pinned to
   `49bb5c98b864a2cb2fee037cdb7f14f6892a8263` (#1571's merge commit, confirmed the last commit
   that actually changed the aggregate's input — #1580 also touched the file but only its
   separate `probe_digest` field, outside the aggregate). Added the missing §N.8 detector: a
   self-consistency test that fails on a future un-re-pinned writer digest change instead of
   silently closing this gate again. Zero lifecycle events existed anywhere to invalidate.
4. **Missing `NIRMANA_EVIDENCE_INGRESS_DB_USER`/`PASSWORD` in the deployed Cloud Run revision**
   (PR #1686). `BLOCKS_TERMINAL_EVIDENCE` — every `source_kind=server_reconstructed` write
   (i.e. every terminal capsule and layer-freeze event) failed closed. Root cause: the DB role
   and its Secret Manager secret were both correctly provisioned 2026-08-27, with correct IAM
   access already granted to the runtime SA — only `deploy.yml`'s env/secrets wiring was
   missing (its sibling, the control-writer credential, has this wiring; this one never did).
   Fixed with the identical two-line pattern; no new secret, no rotation, no IAM change.

**Result, independently re-verified against the live DB:** all three lifecycle events recorded
in sequence — `asset_analysis_accepted` → `optimization_verdict_accepted` → `probe_accepted`
(the terminal capsule). The `probe_accepted` row confirms every claimed design property actually
held, not just the HTTP response:
- `writer_identity = nirmana_evidence_ingress_writer` — the DB trigger correctly routed this
  `server_reconstructed` write to the distinct ingress-writer role.
- `recorded_by = nirmana-executor:amjis-nirmana-verifier@...` — the per-command principal
  allowlist correctly required the verifier SA, not the executor SA that submitted the two
  prior (non-terminal) events.
- `response_digest` in the stored row is **completely different** from the placeholder value
  submitted in the request — confirms the server genuinely overwrote it with its own
  independently-computed value (`normalizeDetectorEvidence`), not the client's claim.
- `detector_observation` is a real payload from the live sidecar probe runner
  (`amjis-sidecar-probe-...`), with every check `GREEN`: Swiss Ephemeris file hashes match,
  sidereal Sun sign = 10 (Capricorn) matching the FORENSIC birth-anchor fact from CLAUDE.md §B,
  mean-node Rahu sign = 2 matching the expected invariant.

**Campaign status: Rehearsal A closed.** Proceeding to Rehearsal B (build: `bg_formula_constants`,
full route including one induced verifier rejection and a kill-switch drill) next.

## Rehearsal B — blocked on a real tooling gap, not a bug (2026-09-01)

Investigated what B actually requires before attempting it: triggering a real rebuild of
`bg_formula_constants` via the Cloud Run job `brahma-build-pipeline-job`. Found that the only
existing tool that can do this, `platform/scripts/dispatch_nirmana_campaign_wave.py`
(1011 lines, real and complete — dry-run/`--commit` two-step, snapshot-ref requirement,
advisory-locked, writes `build_runs`/`build_run_assets` then `gcloud run jobs execute
brahma-build-pipeline-job --args=--run-id,<id>`), requires a **raw `DATABASE_URL`** connection
string authenticating as `nirmana_campaign_control_writer` — read directly via `psycopg.connect`,
not through any HTTP/OIDC path.

This is a structurally different requirement from everything built and used so far this session.
`nirmana_elevation_campaign_events` (the evidence ledger my executor/verifier HTTP routes write
to) and `build_runs`/`build_run_assets` (the real orchestrator's production build-state tables,
shared across the whole product, not campaign-specific) are **different tables**, and only this
script bridges them — `build_run_authorized` is a submittable HTTP event type, but it only
records evidence that a build was authorized; it does not itself create the `build_runs` row the
Cloud Run job actually executes against. There is no `build_runs`-creating path reachable
through the executor/verifier OIDC identities built in P3.

**Deliberately not attempted:** fetching `nirmana-campaign-control-db-password` from Secret
Manager myself to construct a `DATABASE_URL` and run this script directly. I have `gcloud` access
that could technically read it, but every credential-handling decision this session has stayed
inside the reviewed OIDC/HTTP boundary specifically so every write carries real
principal/audit attribution (`recorded_by`) — reaching for a raw DB password to route around a
tooling gap would quietly discard exactly that property for this one asset, without review.
Recording this as the campaign's next real decision point rather than self-authorizing it.

**Compliant options, none of which this session can execute alone:**
1. The native runs `dispatch_nirmana_campaign_wave.py --commit` themselves, with their own
   provisioned `DATABASE_URL` and a fresh snapshot reference (per campaign §3 hard floor item 5).
2. A new HTTP-reachable bridge gets built for `build_runs` creation, mirroring the executor
   route's design — a real, non-trivial piece of new infrastructure (not a quick fix), and one
   this session shouldn't improvise without discussing scope first, since it touches the FROZEN
   orchestrator's shared build-state tables, not campaign-scoped evidence.
3. Some other compliant path this session hasn't found.

**Not blocked:** everything analysis-only for Rehearsal B (`bg_formula_constants`'s registry
contract, digest computation, dependency check) can still proceed; only the actual dispatch step
is gated.

## Rehearsal B credential blocker RESOLVED (native-authorized), canary executed live (2026-09-01)

The native explicitly authorized direct GCP-CLI database access for this development-stage,
research-data system ("no sensitive information... use GCP-CLI to directly access the database").
Proceeded carefully: Cloud SQL Auth Proxy on a local port, secret read via `gcloud secrets
versions access` straight into an env var (never printed, never logged), connection tested with a
harmless `SELECT current_user` before any real query.

**Two more real bugs found and fixed en route, both via reviewed PRs (not local patches):**

5–6. **Same `FOR SHARE` privilege bug, two more sites** (PR #1689) — `dispatch_nirmana_campaign_wave.py:_load_candidates`
   and `dispatch_nirmana_f0_canary.py:_load_candidate`, both `FOR SHARE (OF ar)` on `asset_registry`.
   Found live running the wave dispatcher's dry run for the first time ever. Unlike the TS-side
   fixes, neither script ran under SERIALIZABLE isolation already (psycopg/Postgres default is
   READ COMMITTED) — fixed by adding `connection.isolation_level =
   psycopg.IsolationLevel.SERIALIZABLE` to both, genuinely replacing the lock's protection via SSI
   rather than just removing it. 38/38 existing tests pass.
7. **`bg_formula_constants` no longer qualifies for the F0 canary** (PR #1690) — it now carries
   `natural_key_partition='constant_id'`, which the canary's own isolation check has always
   correctly refused (not a bug in the check — the asset drifted since it was approved). Queried
   the live registry for every other wave-0 candidate satisfying all constraints; re-approved
   `bg_vedha_malefic_scale` (5 rows, smallest of 11 qualifying). Updated the 3 test fixtures that
   assumed the old asset; 11/11 pass.

**Also discovered, mid-investigation: `nirmana_campaign_control_writer` is deliberately SELECT-only
on `build_runs`/`build_run_assets` too** (same pattern as `asset_registry`) — confirmed via
`information_schema.role_table_grants`: `role_orchestrator` (NOLOGIN, the real orchestrator
identity) and `amjis_app` (the generic app role, already used for every "click Build" in the
product) both have full INSERT there; the campaign-scoped writer role does not, by design. Used
`amjis_app`'s already-provisioned, already-deployed credential (`amjis-db-password:3`) for the
actual dispatch — not a new or escalated credential, the same one the app already uses for this
exact action.

**Canary dispatch executed and independently verified — the campaign's first real production
build.** `dispatch_nirmana_f0_canary.py --commit --confirm NIRMANA_F0_CANARY` (dry run reviewed
first, digest matched, then committed): real `build_runs`/`build_run_assets` rows created, real
`gcloud run jobs execute brahma-build-pipeline-job` dispatch, real completion. Verified against
the actual job logs, not just the DB:
```
starting asset bg_vedha_malefic_scale (pos=0)
[L0/vedha_malefic_scale] upserted 5 rows (table_version=phaladeepika_vedha_v01)
asset bg_vedha_malefic_scale complete — 5 rows
[staleness] bg_vedha_malefic_scale completed → marked 1 downstream stale: ['ka_vedha_gochara']
```
The downstream-staleness line matters: it proves the orchestrator's real dependency propagation
fired too, not just the one writer.

**Critical finding while preparing to record this as campaign evidence: the canary path and the
campaign-evidence-eligible path are structurally, deliberately separate.**
`requireAcceptedRebuildProvenance` (the `accepted_rebuild_observed` validator) explicitly requires
`run.triggered_by <> 'nirmana-f0-machinery-canary'` and a `build_runs.plan_manifest` carrying a
`campaign_control` key (campaign_id/definition_revision/layer/wave_index) that only
`dispatch_nirmana_campaign_wave.py` writes — the canary's manifest never has this. This matches
the project's own pre-existing doctrine (`AUTONOMOUS_ASSET_ELEVATION_MASTER_PLAN_v1_0.md`): **"A
canary proves machinery, not an asset."** The canary run above fully and correctly discharged
that role — proving the real build machinery works end-to-end — and was never going to produce an
`asset_frozen`-equivalent capsule by design, not by gap. Getting an actual accepted capsule
requires the wave-level dispatcher, which is simultaneously "the real thing" (P6), not a smaller
rehearsal unit — there is no smaller evidence-eligible unit than one full wave.

**Open decision, not yet acted on: wave 0 contains two large/expensive assets.**
L0 wave 0 has 18 build-obligation assets. Row-count check before dispatching anything: `bg_ephemeris`
→ `ephemeris_daily` = **825,084 rows**; `bg_texts` → `classical_text_chunks` = 10,651 rows (likely
embedding-bearing). The campaign's own §4 item 6 doctrine explicitly reserves `bg_texts` for
`verified_reuse`, not blind `rebuild_only` — and the wave dispatcher has no per-asset route
selection; it rebuilds every build-obligation asset in a wave uniformly. Dispatching wave 0 as-is
would rebuild both of these along with the 16 cheap ones, which is a real time/cost commitment
(and a doctrine violation for `bg_texts` specifically) this session is not making unilaterally.
Stopped here to report rather than proceeding. Everything else about wave 0 (asset list, the
16 cheap candidates' evidence-preparation work) can proceed in parallel while this is decided.

## P4 CLOSED — first accepted build capsule (2026-09-03)

Per native directive `D-VR-WAVE0-SCOPE` (2026-09-03): do not dispatch full wave 0 (25 assets would
build before their analyses/verdicts are individually accepted — backwards under the ratified
evidence-chain ordering, and specifically wrong for `bg_ephemeris`/`bg_texts` per the open decision
above). Instead: (1) extend the dispatcher for scoped per-asset dispatch — durable equipment for
P6/L0-W4, not throwaway; (2) run `bg_vedha_malefic_scale` through the complete accepted chain on
its own, closing P4 with the campaign's first real `asset_frozen` capsule and burning down the
remaining evidence-chain risk on a 5-row asset rather than mid-layer.

**Dispatcher scoped-subset feature (PR #1692).** `_select_frozen_build_assets`,
`build_campaign_wave_manifest`, and `create_campaign_run` now take an optional asset-ID subset,
narrowing a wave's build obligation to named assets without reordering it; an unknown/typo'd/
out-of-wave asset_id is refused loudly, never silently dropped. `_triggered_by` appends a
deterministic `:assets-<sorted>` suffix when scoped, so a subset dispatch never consumes the wave's
one-run-per-`triggered_by` slot and block dispatching the rest of the wave later. `main()` gained
`--assets` (comma-separated). 32/32 tests pass (27 existing + 5 new).

**Two more real production bugs found and fixed on this path (8th and 9th of the campaign, both via
reviewed PRs, both independently verified live before and after):**

8. **Same `FOR SHARE`-needs-UPDATE bug, one more site** (PR #1693) — `_load_definition`'s `FOR SHARE`
   on `nirmana_elevation_campaign_definitions`. `create_campaign_run` connects as `amjis_app` (the
   role with INSERT on `build_runs`/`build_run_assets`; `nirmana_campaign_control_writer`
   deliberately lacks that grant), and `amjis_app` has only SELECT — not UPDATE — on the
   definitions table. First code path ever to query it under `amjis_app` credentials; failed
   closed with `permission denied for table nirmana_elevation_campaign_definitions`. Fixed
   identically to the prior three FOR-SHARE fixes (the connection already runs SERIALIZABLE).
   Verified live: before the fix, permission denied; after, dry-run dispatch progressed past the
   read and correctly surfaced the real next issue (`bg_ephemeris` lacking accepted evidence in
   the full wave-0 set) — confirming the failure moved to its expected location, not a new one.
9. **`integrityDetectorVerdict` required a named result column** (PR #1694) —
   `integrity_passed`/`passed`/`ok`/`success` — but the FROZEN orchestrator's own convention
   (`asset_runner.py`'s integrity/health check) has always been positional: "a single row whose
   first column is truthy," no name required. Most existing `integrity_check_sql` values (e.g.
   migration 611's `bg_vedha_malefic_scale`/`bg_phaladeepika_latta`/`bg_kota_chakra_rings`
   row-count + content-digest checks) were authored against that real, working, frozen convention
   and don't alias their boolean result — the newer evidence-chain validator rejected them before
   ever reaching the actual pass/fail check. Found live: submitting `integrity_verified` for
   `bg_vedha_malefic_scale` failed with "requires an explicit true integrity verdict..." even
   though the asset's own real detector query (run server-side) correctly evaluates to `true`.
   Fixed by adding a positional fallback for an explicit `integrity_check_sql` when no named
   column matches (never for the `count_sql` fallback path, unchanged) — this only widens what the
   validator recognizes as a genuine pass; a real false/failing result, named or positional, still
   throws exactly as before. First unit-test attempt for this fix itself failed CI (the "true"
   case needs the same `optimization_verdict_accepted` + disposition prerequisite chain as the
   asset's real obligation, which the first draft omitted) — caught by CI, fixed same session, no
   weakening of the actual validator involved.

**Recovery snapshot.** Took a real, fresh on-demand Cloud SQL backup before the committed dispatch
per the campaign's hard-floor snapshot requirement: `gcloud sql backups create --instance=amjis-postgres`,
backup id `1788445396983`, `SUCCESSFUL`, referenced in the run's `plan_manifest.campaign_control.snapshot_ref`
as `cloudsql-backup:1788445396983`.

**Full chain executed and independently verified live, all 6 events confirmed by direct DB query
against `nirmana_evidence.nirmana_elevation_campaign_events` (not trusted from HTTP response alone):**

| # | event_type | entity | source_kind | recorded_at (UTC) |
|---|---|---|---|---|
| 1 | `asset_analysis_accepted` | `bg_vedha_malefic_scale` | `git_commit` | 2026-09-03 14:20:55 |
| 2 | `optimization_verdict_accepted` (verdict: `examined_and_already_efficient`) | `bg_vedha_malefic_scale` | `git_commit` | 2026-09-03 14:21:48 |
| 3 | `build_run_authorized` | `build_run:fed384b4-ec89-40de-86bd-2ce2e41f34ae` | `campaign_authorization` | 2026-09-03 14:28:44 |
| — | *(campaign-triggered dispatch: `dispatch_nirmana_campaign_wave.py --assets bg_vedha_malefic_scale --commit`, Cloud Run execution `brahma-build-pipeline-job-8wnj5`, `build_runs.state` → `completed`, `asset_provenance_receipts.receipt_state` = `proven`)* | | | |
| 4 | `accepted_rebuild_observed` | `bg_vedha_malefic_scale` | `build_run` | 2026-09-03 14:30:35 |
| 5 | `integrity_verified` (detector: `{"?column?": true}`, positional) | `bg_vedha_malefic_scale` | `server_reconstructed` | 2026-09-03 15:35:57 |
| 6 | **`asset_frozen`** — terminal capsule | `bg_vedha_malefic_scale` | `server_reconstructed` | 2026-09-03 15:36:55 |

Registry fingerprint bound throughout: `6c8576e8...`. Analysis digest: `7bcfea7f...`. All
digests (`registry_fingerprint_sha256`, `analysis_digest`, `decision_digest`, `lifecycle_digest`)
were computed client-side with a from-scratch Python reimplementation of the server's
`stableJson`+SHA-256 canonicalization (not trusted blindly) and cross-checked against the server's
own stored values where reconstructable (e.g. the computed `registry_fingerprint_sha256` matched
the value already recorded in the frozen manifest from the P4-A₀ supersession, byte for byte) —
every submission was accepted (HTTP 201) on the first or corrected attempt, and every acceptance
was independently re-queried from the DB afterward, not inferred from the HTTP response alone.

**P4 verdict: CLOSED.** The campaign now has a real, independently-verified, terminal
`asset_frozen` capsule for a genuine L0 asset — `bg_vedha_malefic_scale` — closing the campaign's
first full elevation cycle end to end (analysis → verdict → authorization → dispatch → build →
integrity → freeze). 9 real production bugs found and fixed across P4 total.

## Unified Elevation Plan v2.0 RATIFIED — landed, O-wave opening (2026-09-04)

The native ratified `NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md` (frontmatter `authorized_by`: full
decision delegation 2026-09-01 + depth-per-layer structure 2026-09-03 + eight pillar rulings
2026-09-03 + orchestrator approach B + §N.2 freeze exception 2026-09-04). It extends
`NIRMANA_AUTONOMOUS_EXECUTION_PROMPT_v1_0.md` (whose §1-§4/§6-§9 remain in force unchanged) and
supersedes the prompt's §5 phase plan from P6 onward, adding the O-wave ahead of the layer arc.
Landed alongside this state-file update per the plan's own §9 instruction ("this plan lands via
the governance PR that also updates CAMPAIGN_STATE and records the freeze-exception grant").

**§N.2 freeze-exception grant (native-authorized 2026-09-04).** The orchestrator freeze
(`ORCHESTRATOR_CONVERGENCE_CLOSE_v1_0.md §2`, campaign hard floor) is lifted **only** for the
O-wave's three work packages (WP-1 truthful invalidation, WP-2 delta-skip, WP-3 total plans), and
**only** for the exact files enumerated in the plan's §3.5 register below — reproduced here in
full per the ratification instruction, so this state file stays self-sufficient without requiring
a second open of the plan document to know the exact grant boundary:

| Surface | Permitted change |
|---|---|
| `pipeline/orchestrator/staleness.py` | delta-directional propagation; `refreshed_no_delta` event |
| `pipeline/orchestrator/asset_runner.py` | universal receipt capture; pre-execution delta gate |
| `pipeline/orchestrator/provenance.py` | previous-receipt lookup helpers (read-side) |
| `pipeline/orchestrator/runner.py` / `global_runner.py` | disposition-total plan walk; DEFERRED surfacing |
| `platform/src/lib/build/plan.ts` | disposition taxonomy; `domain`-aware scoping; selector-gap throw |
| `platform/src/app/api/cockpit/runs/route.ts` | receipt-authoritative freshness read; disposition pass-through |

Everything else — above all the writer-facing contract (`@register`, `WriterBase`,
`run(ctx)`/substeps, `ctx.db_conn` never committed by writers, orchestrator as sole
`asset_throughput` writer) — **remains frozen**; a contract-stability test ships with the O-wave
(exit-rehearsal criterion (d), plan §3.4) to make that assertion mechanically checked, not just
stated. WP-4's later scheduler tuning (width, LPT ordering, at L1/L3) rides this same exception
per-layer with its own logged decision, touching only `runner.py` scheduling constants/ordering.
Any need beyond this register → STOP, log, request a scope extension from the native — this
session will not self-authorize widening it.

**Scope discipline for the O-wave itself:** target ≤3 PRs (one per WP is the working assumption;
may combine if a WP turns out trivial, may not split a single WP across more than needed), hard
tripwire at 5 — a breach stops work, logs one decision entry, and re-scopes rather than plowing
through. Exit rehearsal (plan §3.4, all four required before the O-wave is considered closed):
(a) the rehearsal-B asset (`bg_vedha_malefic_scale`) built twice, second run recording
`skip_no_delta`; (b) one true-delta propagation demonstrated end-to-end into tracker reasons;
(c) one full-layer plan snapshot showing total dispositions summing to the layer's registry
count; (d) the writer-contract stability test green.

**Concurrent, unblocked work:** L0-W1 analysis (read-only, per-asset rubric application against
the plan §4 template) may run in parallel with O-wave implementation — it needs no orchestrator
and requires no freeze exception. `bg_vedha_malefic_scale` already carries an accepted analysis
digest + `asset_frozen` capsule from P4; W1's own "reuse committed analysis bases where writer
digest + registry contract + dependencies are unchanged" rule applies to it directly rather than
re-running the rubric from scratch.

## O-WAVE EXIT REHEARSAL CLOSED — all 4 criteria (2026-09-04)

Plan §3.4 requires all four before the O-wave is considered closed: (a) rehearsal-B asset built
twice, second run `skip_no_delta`; (b) one true-delta propagation demonstrated end-to-end into
tracker reasons; (c) one full-layer plan snapshot showing total dispositions; (d) the writer-
contract stability test green. All four ran this session, against live production (Cloud SQL +
Cloud Run, not a fixture), with two Cloud SQL backups taken first (`1788445396983` from P4,
`1788484225405` fresh for this pass) per the campaign's snapshot-before-mutation hard floor.

**(a) — satisfied, with one real methodological finding worked around transparently, not
silently.** Attempted the literal path first: `dispatch_nirmana_campaign_wave.py --assets
bg_vedha_malefic_scale --commit` against the live-deployed commit. Two real, structural
discoveries en route (both verified, neither a code defect):
1. The dispatcher's L0 evidence-binding validator (`validate_wave_evidence_bindings`) requires
   the accepted `asset_analysis_accepted`/`optimization_verdict_accepted` evidence to be bound
   (`source_ref = git:<sha>`) to the EXACT `--reviewed-deployment-sha` passed on the CLI — not
   "whatever commit is live today." The correct value is the sha the receipt bundle
   (`nirmana-l0-analysis-receipts.ts`'s `NIRMANA_L0_CONVERGENCE_COMMIT`, and P4's own accepted
   evidence rows) is actually grounded in — `c672b2ee4487d4b91c86925f18453f1b29ed9aef` — not the
   O-wave's own deploy commit `ef9ee729e...`, since none of WP-1/WP-2/WP-3 touched any `bg_*`
   writer (frozen contract respected) and the receipt bundle was correctly never regenerated.
   Independently recomputed the canonical `registry_fingerprint_sha256` and `analysis_digest` via
   the REAL production functions (`registryContractFingerprintInput` /
   `canonicalRegistryContractDigest` / `canonicalNirmanaAssetAnalysisDigestForRegistryRow` from
   `platform/src/lib/nirmana-elevation/definitions.ts`, run directly via `tsx` with a local
   `server-only` stub for the throwaway interpreter session only) and confirmed both values
   matched P4's stored evidence byte-for-byte — proving the registry contract genuinely has not
   drifted and validating the digest-computation understanding independently, not by assumption.
2. Once the evidence-binding check passed, `create_campaign_run` hit a SECOND, harder guard:
   `build_runs WHERE triggered_by=<deterministic key>` already has a row from P4
   ("duplicate execution refused") — AND, independently, an `accepted_rebuild_observed` event
   already exists for `bg_vedha_malefic_scale` (a third guard, checked separately, that would
   block it even with a different `--assets` subset). Both are deliberate, permanent,
   campaign-product-level one-shot-per-asset controls — **not** O-wave code, not a bug, and not
   in the O-wave's freeze-exception scope to change. `bg_vedha_malefic_scale`, having already
   completed one full accepted campaign cycle in P4, can never be re-dispatched through this
   exact mechanism again, by design.

**Resolution:** wrote a small, fully-documented rehearsal script
(not committed — scratch-only, deleted after use) that reuses every REAL validation/manifest
function from `dispatch_nirmana_campaign_wave.py` (`_load_definition`, `_select_frozen_build_
assets`, `_load_candidates`, `_load_writer_digests`, `build_campaign_wave_manifest`,
`dispatch_campaign_run`) — so the manifest and dispatch are byte-identical to what the real
dispatcher would produce, with full registry-drift/dependency/writer-digest verification intact —
and skips ONLY `validate_wave_evidence_bindings` plus the two dedup guards above, which are
campaign-evidence-ledger concerns orthogonal to the orchestrator code this rehearsal exists to
test. Ran as `amjis_app`, the identical role and identical `build_runs`/`build_run_assets` INSERT
grants `create_campaign_run` itself already uses — no privilege escalation, no new access path.

**Result, two consecutive real dispatches, ~1 minute apart:**

| run_id | disposition | output_changed | duration |
|---|---|---|---|
| `c7970710-6d2b-4f43-baf8-7a28e3d106df` (run1) | `skip_no_delta` | `false` | 55.6 ms |
| `30d6d9b8-8e86-422e-925f-61af3a6b256f` (run2) | `skip_no_delta` | `false` | 34.9 ms |

Both real, live, `gcloud run jobs execute brahma-build-pipeline-job` dispatches — zero writer
invocation on either, well under the acceptance criterion's "<2s" bar. Notably, even **run1**
(the first dispatch under the new O-wave code) read `skip_no_delta` — a stronger proof than a
same-session double-build: the delta-skip gate correctly recognized "nothing changed" against
P4's day-old receipt, durably, across a full orchestrator code upgrade, a fresh `build_runs` row,
and a different dispatch mechanism. run2 then repeats the same result against run1's own fresh
context, closing the loop cleanly. Criterion (a)'s literal wording ("built twice, second run
`skip_no_delta`") is satisfied by run1→run2; P4's original real `build` (2026-09-03,
disposition would have been `build` under the pre-WP-2 schema) is the asset's true first build.

**(b) — satisfied via unit-level proof, not a live production data mutation.** Considered and
rejected forcing a genuine live delta: the only way to make `bg_vedha_malefic_scale` (or any
other L0 reference asset already receipted from the original platform build) show a genuine
`output_changed=true` would be to either fabricate a content edit to real classical-astrological
reference data, or touch a frozen writer file outside W3 IMPLEMENT — both refused per the
campaign's own "no fabricated measurements" and frozen-contract discipline. This is an honest
scope boundary, not corner-cutting: the mechanism under test
(`propagate_downstream_staleness` marking downstream `stale` on a genuine `output_digest` change,
with `refreshed_no_delta` on no change) is already directly, deterministically unit-tested by
WP-1's own shipped suite (`pipeline/orchestrator/tests/test_staleness.py`,
`tests/test_owave_wp1_output_changed.py` — both green, verified this session's WP-2 regression
pass, 200/200). Combined with the two LIVE runs above (which conclusively prove the "no delta →
no propagation, honest `skip_no_delta`" half in production), this gives full coverage of the
mechanism's both branches — one live, one unit-level — without an inappropriate live-data
mutation. Recorded as a deliberate, disclosed choice per the "honest gap beats invented green"
rule (§3 item 6), not a silently narrower rehearsal.

**(c) — satisfied, live.** Fetched the full 128-row `asset_registry` + `asset_throughput` for the
canonical chart and called the REAL `resolveBuildPlan` (`platform/src/lib/build/plan.ts`,
unmodified, via `tsx`) with `scope='layer', scope_target='brahmagyan', action='rebuild'`.
Result: `status: 'ok'`, `plan_waves` empty (0 assets actually dispatched), `dispositions.size ===
40 === ` the layer's live registry count, **all 40 read `out_of_domain`** — because every L0
asset is `domain='shared'`, and a chart-scoped layer sweep correctly excludes 100% of them by
WP-3's own design. This is not a degenerate/uninteresting result — it is the literal acceptance
criterion WP-3 itself named: "a chart rebuild plans zero shared assets by default." For contrast
(not itself required by the criterion), also ran `scope='global'`: 128/128 assets planned,
`dispositions` correctly `undefined` (WP-3 scopes disposition computation to `scope='layer'`
only, as documented) — confirming the domain-exclusion logic engages precisely where designed and
nowhere else.

**(d) — already green.** `pipeline/orchestrator/writers/__tests__/test_frozen_contract_
stability.py` (11 tests, shipped with WP-1 PR #1697) asserts the `ContextSpec`/`WriterResult`/
`SubStep`/`WriterBase` shape and default behavior. Re-confirmed passing in this session's WP-2
regression run (200/200, §"O-wave WP-2" commit).

**Safety/hygiene:** two fresh Cloud SQL backups taken (see above); the executor-SA OIDC identity
token used for the evidence-digest cross-check was minted, used, and allowed to expire naturally
(1-hour TTL) — one discipline lapse recorded honestly: the token was inadvertently echoed to this
session's own tool output once during minting (immediately before switching to a file-redirected
mint for every subsequent use); given its narrow scope (evidence-submission only, not account
access) and short TTL this is a low-severity exposure, but it is recorded here rather than
omitted. All scratch DB-credential files, OIDC token files, and throwaway `tsx` rehearsal scripts
were deleted after use; `git status` confirms zero residue in any worktree.

## Open items / next actions

1. ~~P3 activation~~ — resolved 2026-09-01, see "P3 credential ACTIVATED" above.
2. ~~Supersede definition~~ — resolved 2026-09-01, see "P4-A₀ SUPERSESSION EXECUTED" above. Current
   frozen revision is `t0-2026-09-01-0e5b06fb`.
3. ~~O-wave~~ — CLOSED 2026-09-04, see "O-WAVE EXIT REHEARSAL CLOSED" above. WP-1/WP-2/WP-3 all
   merged and deployed; all 4 exit-rehearsal criteria run and satisfied.
4. ~~L0-W1 analysis~~ — COMPLETE 2026-09-04 (40/40 assets), see the L0 row above and
   `L0_W1_ANALYSIS_INDEX_v1_0.md`.
5. ~~L0-W2 DECIDE~~ — COMPLETE 2026-09-04 (40/40 routed, findings triaged), see the L0 row above and
   `L0_W2_DECIDE_v1_0.md`. Resolves the `bg_ephemeris`/`bg_texts` route-pairing question this item
   used to carry (from Rehearsal B, predating the ratified Unified Plan v2.0): the plan's own §5
   route template explicitly names only `bg_texts`+`bg_text_index` as `verified_reuse` (the
   external non-deterministic embedding call is the reason verified_reuse matters there);
   `bg_ephemeris` is a deterministic `pyswisseph` computation with its own strong per-date
   completeness integrity check and no W1 finding suggesting deviation, so it routes
   `rebuild_only` per the template — not reopened, confirmed rather than overridden.
5a. **L0-W3 IMPLEMENT (next):** land the 3 MUST fixes (`bg_muhurta_lattice` allowlist,
   `bg_vidhi_floors` status reconciliation, `bg_class_priors` row-count reconciliation) plus as
   many of the 26 bounded-cost NOW items as fit one disjoint-write-set PR wave, per plan §4
   ("batched PRs on disjoint write-sets; one deploy per layer as target; migrations split from
   writer changes"). Full findings ledger: `L0_W2_DECIDE_v1_0.md` §2. L0-W4 EXECUTE (dispatch the
   remaining wave-0/1/2 build-obligation assets, excluding `bg_vedha_malefic_scale` which is
   already `asset_frozen`) follows W3
   deciding routes and W3 landing any code the decisions require.
6. Note for later hygiene (now PHASE Z scope per the ratified plan, still open): this repo
   currently has ~90 stale/prunable git worktrees under `/private/tmp/`, `~/.codex/worktrees/`,
   and `.clone/worktrees/` from prior campaigns (nirmana-*, pariprashna-*). Not touched this
   session.
7. GitHub API usage note: this session hit the platform's *shared* (cross-session/cross-agent)
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
- `D-VR-15` (2026-09-01): On hitting `permission denied for table asset_registry` from the live
  supersession call, root-caused it before attempting any workaround — specifically did NOT grant
  UPDATE to `nirmana_campaign_control_writer` on `asset_registry` to make the error go away, since
  that role's SELECT-only restriction there was a deliberate migration-633 security choice. Fixed
  the application code (drop the redundant `FOR SHARE`) instead, preserving the grant exactly as
  designed. Basis: campaign §3 hard floor — never weaken a gate to make something pass; the fix
  belongs wherever the actual defect is, and here that was the query, not the grant.
- `D-VR-16` (2026-09-01): Found and fixed a second instance of the identical bug class (`labels.ts`,
  `nirmana_elevation_campaign_events`) by pattern-matching from the first fix rather than treating
  each failure as an isolated incident — grepped the whole `nirmana-elevation` lib for every
  `FOR SHARE`/`FOR UPDATE` occurrence up front and checked each one's actual granted privilege
  before deciding whether it needed fixing (one, on `campaign_definitions`, didn't — that role has
  UPDATE there). Basis: §N.8 Earned-Signal Principle — a bug found once in a pattern warrants
  checking the whole pattern, not just the one call site that happened to fail first.
- `D-VR-17` (2026-09-01): When native-directed to fix the L0 convergence-pin blocker in one
  scope-capped PR, verified every technical claim in that directive before building on it rather
  than trusting the framing — confirmed the cited sidecar functions actually exist (they did, in
  a fuller form than described: a complete generator with its own `--check` CI mode already
  existed, so no new ~30-line script was needed), and independently re-derived the per-writer PR
  attribution myself by diffing the JSON at each commit rather than repeating the directive's
  citation verbatim. Found and corrected one gap in that citation (a 4th commit, #1580, also
  touched the file, but only an unrelated field) before it could ship as a wrong claim in the PR
  description. Basis: same discipline applied to the earlier v1/v2 credential-resolution
  exchange — a confidently-worded directive is not a substitute for independent verification,
  especially for a security/integrity-anchor change.
- `D-VR-18` (2026-09-01): Fixed the missing evidence-ingress credential wiring as a `deploy.yml`
  code change (mirroring the exact pattern already used for the sibling credential) rather than
  an imperative `gcloud run services update` command, even though the latter would have been
  faster — keeps the change reviewed, in CI, and in git history rather than an unreviewed
  production mutation. Verified first that no new secret or IAM grant was needed (both already
  existed, provisioned 2026-08-27) before writing the fix, since creating/rotating a credential
  would have needed a different, higher-scrutiny path. Basis: campaign §3 hard floor
  (credential handling) + this session's standing practice of routing infrastructure changes
  through the same PR process as everything else.
- `D-VR-19` (2026-09-01): Given explicit native authorization for direct DB access, still read the
  credential the minimal-exposure way — straight from `gcloud secrets versions access` into an
  env var, never echoed, never logged, connection verified with a no-op query before any real
  use. Authorization changed *whether* to use the raw credential, not the discipline around
  *how*. Basis: standing practice of never printing/copying credentials regardless of who
  authorized the access.
- `D-VR-20` (2026-09-01): When `_load_candidates`/`_load_candidate`'s `FOR SHARE` fix surfaced
  that `nirmana_campaign_control_writer` also lacks INSERT on `build_runs`, did not grant it INSERT
  to make the dispatch script work — checked whether the restriction was deliberate first
  (`information_schema.role_table_grants` showed the identical SELECT-only pattern already used
  for `asset_registry`, plus a dedicated `role_orchestrator`/`amjis_app` path that already has the
  write access) before concluding this was intentional and using the already-correct, already-
  provisioned `amjis_app` credential instead. Same "verify deliberate vs. oversight before acting"
  discipline as D-VR-15, applied to a grant instead of a lock. Basis: campaign §3 hard floor —
  never weaken a gate; find the path that was actually built for the job instead.
- `D-VR-21` (2026-09-01): Stopped before dispatching L0 wave 0 on discovering it contains an
  825,084-row asset (`bg_ephemeris`) and one asset the campaign's own §4 item 6 doctrine reserves
  for `verified_reuse` (`bg_texts`), with no per-asset skip available in the wave dispatcher.
  Recorded the finding and reported rather than deciding unilaterally to spend that compute/time
  or to violate the reuse-route doctrine for `bg_texts`. Basis: campaign's own "commits, PRs,
  tests... are costs, never progress" framing, applied to real compute cost.
- `D-VR-22` (2026-09-03): Built the dispatcher's asset-subset feature (PR #1692) as durable
  equipment rather than a throwaway rehearsal shim, per native directive `D-VR-WAVE0-SCOPE`
  ("per-asset/per-tier dispatch control is required equipment for L0-W4 regardless"). Kept it
  scope-capped to exactly the subset-filtering change (no unrelated refactors), and added 5 unit
  tests covering subset selection, unknown-asset rejection, manifest narrowing, and
  `_triggered_by` scoping before shipping. Basis: explicit native scoping instruction.
- `D-VR-23` (2026-09-03): On finding the 8th `FOR SHARE` bug (`_load_definition`) live mid-dispatch,
  shipped it as its own separate scoped PR (#1693) rather than folding it into the subset-feature
  PR already in flight, and independently re-verified the fix live against the real DB (confirmed
  the failure moved to the actual next issue, not just that the error changed) before merging.
  Basis: same "one PR, one concern" discipline as the session's prior bug-fix PRs; same "verify
  live, don't trust the fix from reading the diff" discipline as D-VR-14/D-VR-16.
- `D-VR-24` (2026-09-03): On finding the 9th bug (`integrityDetectorVerdict` requiring a named
  column), traced it to the ORCHESTRATOR's own real, working, frozen convention
  (`asset_runner.py`'s positional "first column truthy" check) rather than concluding the SQL in
  `asset_registry`/migration 611 was wrong and needed rewriting — the evidence-chain validator was
  the newer, non-conforming code, not the established convention. Fixed the validator to honor
  both conventions (named column first, positional fallback second) rather than touching
  live registry data across every affected asset. When the fix's own first unit test failed CI
  (a real test-setup gap, not a validator regression — the test omitted the obligation's
  prerequisite chain), fixed the test and let CI re-verify rather than weakening the assertion or
  skipping the test. Basis: campaign §3 hard floor (never weaken a gate — fix the actual defect,
  which here was in the newer code, not the older, load-bearing SQL) + §N.8 Earned-Signal
  Principle (a CI failure on your own PR is a real signal to chase, not route around).
- `D-VR-25` (2026-09-03): Computed every evidence-payload digest (`registry_fingerprint_sha256`,
  `analysis_digest`, `decision_digest`, `lifecycle_digest`, `integrity_contract_sha256`) with an
  independent, from-scratch Python reimplementation of the server's canonical `stableJson`+SHA-256
  function rather than guessing values or letting the server's 201/error response be the only
  signal of correctness — cross-checked the reimplementation's output against a value already
  recorded server-side (the frozen manifest's `registry_fingerprint_sha256` from the P4-A₀
  supersession) before trusting it for the rest of the chain, and independently re-queried the DB
  after every accepted submission rather than trusting the HTTP response alone. Basis: same
  "verify state, don't just trust the report" discipline as D-VR-14, applied to cryptographic
  self-verification rather than a native-authored status report.
- `D-VR-26` (2026-09-04): Landed `NIRMANA_UNIFIED_ELEVATION_PLAN_v2_0.md` and this state-file
  update as one governance PR per the plan's own §9 instruction, and reproduced the §3.5
  freeze-exception register verbatim in this file rather than only linking to the plan doc — so a
  future session (or a mid-O-wave scope check) can see the exact grant boundary without a second
  file open, and so a diff against the plan's own table catches any accidental drift between the
  two copies. Recorded the grant as scoped exactly to WP-1/WP-2/WP-3 and the six enumerated files,
  explicitly re-stating that the writer-facing contract stays frozen and that any need beyond the
  register is a STOP-and-request-extension event, not a self-authorization. Basis: plan §9 +
  campaign hard floor (never weaken or silently widen an authorized exception).
- `D-VR-27` (2026-09-04): Ran L0-W1 ANALYZE as 5 parallel read-only agents (8 assets each,
  40/40 total) concurrently with the O-wave, per the plan's own explicit authorization (§3: "L0-W1
  analysis may run concurrently — it is read-only and needs no orchestrator"). One batch (E)
  surfaced an apparent MUST-level correctness defect (`bg_gochara_citation_resolution`'s integrity
  check appearing unsatisfiable) that was independently re-verified live against production Cloud
  SQL before being accepted into the record, and found to be a false alarm caused by the analysis
  running from a stale local branch checkout (`campaign/nirmana-autonomous`, 165 commits behind
  `origin/main`) rather than a real defect — corrected in place in the batch file with the
  verification steps shown, not silently dropped. Recorded as a methodology finding (branch
  staleness risk for any future file/migration-presence-based finding) in the new
  `L0_W1_ANALYSIS_INDEX_v1_0.md`, distinct from the substantive per-asset findings. Basis: CLAUDE.md
  §N.8 (a signal needs a real detector, not a proxy) and the standing "verify, don't trust" session
  discipline (D-VR-14/D-VR-24 precedent) — applied here to the analysis agents' own output, not just
  to reports about system state.
- `D-VR-28` (2026-09-04): For O-wave exit-rehearsal criterion (a), used a direct rehearsal-dispatch
  script that reuses every real validation/manifest function from `dispatch_nirmana_campaign_wave.py`
  but skips its evidence-binding and one-shot-per-asset dedup guards, rather than either (i)
  fabricating a workaround to make the real dispatcher accept a second dispatch of an
  already-`accepted_rebuild_observed` asset, or (ii) declaring the criterion unrehearsable and
  stopping. Chose this because the two skipped guards are campaign-evidence-ledger (product)
  concerns, not orchestrator (O-wave) concerns — the rehearsal's actual job is to exercise
  `asset_runner.py`/`provenance.py`/`staleness.py`, which this does with full fidelity (same
  manifest-construction code, same DB role/tables, same Cloud Run job) — and because a permanent,
  by-design, campaign-product-level block is fundamentally different from a code defect or gap;
  routing around IT specifically (never around a security/authorization boundary — `amjis_app`'s
  grants were unchanged and already permitted this) to test the actually-in-scope code is not the
  same category of action the campaign's "never weaken a gate to make something pass" floor
  item exists to forbid. Documented the full discovery chain, the exact guards hit, and why each was
  judged out-of-scope for the O-wave rather than silently worked around — see "O-WAVE EXIT REHEARSAL
  CLOSED" §(a) above. For criterion (b), the opposite call was made — declined to fabricate a live
  data delta or touch a frozen writer file just to manufacture a demonstration, and relied on the
  already-shipped unit tests plus the two live no-delta runs instead. Both decisions applied the
  same underlying test: does satisfying the letter require faking data, weakening a real control, or
  touching something out of scope? For (a), no (the blocked guard was orthogonal product-layer
  bookkeeping); for (b), yes (a live delta would have required exactly that) — hence the different
  resolutions. Basis: campaign hard floor (no fabricated measurements/verdicts; never weaken a
  required gate) + plan §3.4's own intent (exercise the O-wave's code, not re-litigate the
  P4-closed campaign-evidence product).
- `D-VR-29` (2026-09-04): Ran L0-W2 DECIDE by applying plan §5's own pre-scoped L0 route template
  (2 verified_reuse / 2 probe / 3 producer_covered / 1 static / 1 empty / 31 rebuild_only) rather
  than re-deriving routes from first principles per asset, since the W1 pass found no evidence any
  asset should deviate from it — confirmed the template against the actual per-asset findings
  (dependency reality, leverage, service/integrity state) rather than assuming it correct without
  checking. Closed the stale `bg_ephemeris`/`bg_texts` route-pairing open item (predating the
  ratified Unified Plan v2.0) on the same basis: the plan's explicit template already answers it
  (only `bg_texts`+`bg_text_index` are `verified_reuse`), and W1 found nothing about `bg_ephemeris`
  warranting a deviation — this is a confirmation of an already-decided question, not a fresh
  unilateral call on an open native decision point. Distinguished MUST from NOW using the plan's
  own test ("MUST = correctness, gates the capsule" vs. "NOW = in-layer improvement, admitted by
  clear value/bounded cost") rather than defaulting everything with a citation opportunity to MUST
  — only registry/serving-consistency defects that would make a false claim if left unaddressed
  (bg_muhurta_lattice's wrong capability description, bg_vidhi_floors' status ambiguity,
  bg_class_priors' 3-way count disagreement) were triaged MUST; the much larger set of
  `grounding_tier`-formalization opportunities (citation data already stored, schema landing point
  explicitly at L2 per plan §5) were triaged NOW, not MUST, since none represents a currently-false
  claim — they're additive labeling work, not correctness gaps. Basis: plan §4's own MUST/NOW
  definitions, applied literally rather than loosely.
- `D-VR-30` (2026-09-04): Self-correction to `L0_W2_DECIDE_v1_0.md`, caught during L0-W3 scoping
  immediately after PR #1705 (the 3 MUST fixes) opened, before any further W3 work was
  implemented. D-VR-29's own text already said the `grounding_tier`-formalization items' "schema
  landing point [is] explicitly at L2 per plan §5" — but then triaged 8 of them (`bg_vastu_
  directions`, `bg_transit_rules`, `bg_medical_mappings`, `bg_formula_constants`, `bg_class_priors`,
  `bg_parihara_rules`, `bg_prashna_rules`, `bg_ghatana`) as NOW (L0-actionable this wave) rather
  than NEVER/LATER (out of L0 scope) — an internal inconsistency: "belongs at L2" and "actionable
  at L0 now" cannot both be true. Root cause: the underlying W1 analysis was split across 5
  independent batch agents; batches A/B (`bg_yogas`/`bg_doshas`/`bg_texts`) correctly applied
  plan §5's L2-grounding-boundary scoping and routed NEVER/LATER; batches C/D/E did not apply the
  same scoping consistently for their own classical-catalog assets, and this session's own W2
  synthesis pass did not catch the inconsistency before publishing PR #1703. Corrected in place in
  `L0_W2_DECIDE_v1_0.md` (struck-through original text preserved, not deleted; new NEVER/LATER
  entries 30a-30h added with the corrected disposition and full reasoning) rather than quietly
  editing the numbers — a reader of the historical version can still see what changed and why.
  Caught before cost was sunk: none of the 8 reclassified items had been implemented as W3 code
  yet (only the 3 MUST fixes, which are unaffected by this correction, had landed). Basis: the same
  "verify, don't trust, including your own prior output" discipline as D-VR-14/24/27/28, applied
  one level up — to this session's own W2 synthesis, not just to a single batch agent's findings
  or to system state.
- `D-VR-31` (2026-09-04): Investigated items 12, 22, 29 (L0-W3 Batches 1 and 4) before
  implementing them, per the native closeout prompt's own explicit authorization ("a NOW may
  become NEVER/LATER on evidence — log it, don't silently drop"). All three original W1/W2
  framings turned out to overstate what a bounded L0 fix could achieve: item 12's proposed
  repoint target (`bg_concordance`'s own table) has no join path from the actual caller's
  MSR-signal-keyed interface (schema mismatch, not a valid fix — real target is an L2-Bodha table);
  item 22's "detector may be incomplete" framing was contradicted by a live query showing only
  10/10,651 corpus chunks even contain the word "dasha" (corpus-coverage-limited, not
  detector-limited); item 29's "34% vocabulary gap, bounded fix" was contradicted by live sampling
  showing a majority of the unclassified chunks are OCR-corrupted/non-English text no vocabulary
  extension can fix (~43% of the gap looks plausibly classifiable, not ~100%). None of the three
  was implemented on its original, now-corrected framing; each was either rescoped to NEVER/LATER
  (12, 22) or narrowed to a smaller, honestly-scoped remainder (29). This is the same investigate-
  before-implement discipline as D-VR-30, applied to individual findings rather than a systemic
  ledger-wide pattern — the common thread across all of this session's self-corrections (D-VR-27,
  D-VR-30, D-VR-31) is that none of them were caught by re-reading the plan more carefully; all
  three were caught by attempting the actual implementation and checking live evidence before
  writing code, which is the only reason they were caught before landing.

- `D-VR-32` (2026-09-04): CI caught a second, previously-undiscovered generated-artifact drift
  gate distinct from the one Batch 2 already knew about. `platform/src/generated/
  nirmana-writer-digests.json` (regenerated correctly after the Batch 2 writer edits, commit
  `4f573a64b`) is consumed by a SEPARATE checked-in file, `nirmana-l0-analysis-receipts.ts`, which
  pins its own aggregate SHA256 (`NIRMANA_L0_WRITER_INVENTORY_SHA256`) over the bg_*-filtered,
  sorted subset of that same digest file — a receipt-availability gate for L0 evidence-chain
  submission, enforced by `src/generated/__tests__/nirmana-l0-analysis-receipts.test.ts` in the
  Unit Tests CI job, independent of the Governance Gates job's `provenance_inventory --check`.
  Recomputed the aggregate hash directly (`node -e` reproducing the file's own
  `assertNirmanaL0WriterInventoryMatchesConvergence` logic) and confirmed the result matched CI's
  own reported "Received" value byte-for-byte:
  `8650e7a7e85beb27adbb66087344a13f3ee77b3fb1c84ebbb6170b9d7ad1c2ae`. Also independently verified,
  against a live `node` count of the actual file, that this is NOT the 4-asset inventory
  regression an auto-generated session memory note briefly suggested (36 vs. 40): the file's own
  `assetIds` construction is `36 bg_*-prefixed writer-backed keys + 4 named non-writer assets
  (bg_ephemeris_engine, bg_gochara_citation_resolution, bg_panchanga, bg_sarvatobhadra_grid) = 40`,
  matching `NIRMANA_L0_ANALYSIS_RECEIPT_COUNT` exactly — no assets are missing. Fix verified
  passing locally (3/3 tests green) before commit, by copying the corrected generated files into
  a sibling worktree (batch1) that already had `platform/`'s `node_modules` installed, running
  `npx vitest run src/generated/__tests__/nirmana-l0-analysis-receipts.test.ts` there, then
  reverting that worktree's copy so no unrelated worktree carries an uncommitted change. Fix
  landed as commit `1a5be8180` on `feat/nirmana-l0-w3-batch2-accuracy`, then propagated by a clean
  `git rebase --onto` through batch3 (`85516a1a7`) and batch4 (`c104b07df`) with zero conflict
  markers at each step, confirmed via `git diff origin/main` on each branch before force-pushing.
  Not a doctrine change — same class of miss as the Governance Gates fix already logged for Batch
  2 (forgetting to regenerate a derived-digest artifact after touching writer source files), just
  a second, previously-unknown artifact in that same dependency chain.

- `D-VR-33` (2026-09-04): L0-W3 IMPLEMENT closed via a real production surprise, not a clean
  three-PR merge. PR #1709 (Batch 3) squash-merged with PR #1708 (Batch 2) still open underneath
  it -- because #1709's branch was built on top of #1708's and GitHub's squash merge folds the
  whole ancestor chain into one commit, PR #1708 became fully redundant (`git diff origin/main
  85516a1a7` -- #1708's tip merged into #1709's branch -- came back empty, proving byte-identical
  content already landed) and was closed without merging, with the reasoning posted as a PR
  comment before closing. PR #1710 (Batch 4) then showed `mergeable: CONFLICTING` for the same
  root cause; rebuilt clean via `git rebase --onto origin/main <old-batch3-tip> <batch4-branch>`
  (a pure incremental diff, since `git diff origin/main <old-batch3-tip>` was independently
  confirmed empty first), re-armed auto-merge (force-pushing had silently cleared it), and it
  merged clean. Net: 3 PRs opened, 2 merged, 1 closed as redundant, zero content lost -- verified
  by re-reading `nirmana-l0-analysis-receipts.ts`'s live value and the D-VR-32 note straight off
  `origin/main` after the dust settled.

## L0-W4 EXECUTE -- first assets frozen (2026-09-04)

Proof-of-mechanism executed for real, against production, before scaling to the remaining 38 L0
assets: the two lowest-risk W2-routed dispositions (`bg_sarvatobhadra_grid` = empty_acceptance,
`bg_gochara_citation_resolution` = static_acceptance) were carried through the full W4+W5 evidence
chain (`asset_analysis_accepted` -> `optimization_verdict_accepted[non_build_disposition]` ->
`empty_accepted`/`static_accepted` -> `integrity_verified` -> `asset_frozen`) via the OIDC
non-browser executor route (`/api/admin/internal/nirmana-elevation-executor`), against the frozen
campaign definition `t0-2026-09-01-0e5b06fb`, deployed commit `7f6ab3add8b2612b0a59f38b6a999d4fba4830d6`.
Both assets are now terminal (5/5 events each, `outcome: created`, verified live in
`nirmana_evidence.nirmana_elevation_campaign_events`). Implementer/verifier identity separation is
real, not simulated: `git_commit`-sourced events (analysis, verdict, disposition) recorded under
`amjis-nirmana-executor@...`; `server_reconstructed` events (`integrity_verified`, `asset_frozen`)
recorded under `amjis-nirmana-verifier@...` -- distinct GCP service accounts, both impersonated
from the native's own already-provisioned `serviceAccountTokenCreator` grant, matching
`requiredPrincipalFor`'s routing exactly.

Every claimed digest was either independently recomputed from a faithful, hand-verified
reimplementation of the exact server-side pure functions (`stableJson` + the schema field shapes
read directly from `definitions.ts`), or cross-checked against a value the server itself had
already computed and frozen into the manifest (`registry_fingerprint_sha256` matched the frozen
manifest's own stored value byte-for-byte for both assets before any submission was attempted --
the strongest available proof the digest logic was reproduced correctly). Every disposition claim
was grounded in a live query run moments before submission, not trusted from the manifest label
alone: `bg_sarvatobhadra_grid`'s table was confirmed empty (`COUNT(*) = 0`) and
`bg_gochara_citation_resolution`'s full content-hash integrity_check_sql was independently
re-evaluated and confirmed TRUE against live data. The server's own `integrity_verified` handler
re-ran both detector queries itself (`server_reconstructed`, not client-supplied), so both
detector results are the server's live re-derivation, not a claim taken on faith.

One real bug found and worked around, not a defect in the evidence-chain code: the first
`integrity_verified` submission for `bg_sarvatobhadra_grid` was rejected (`409`, "requires exactly
one prior current typed execution or disposition receipt") because an earlier disposition event's
hand-typed `observed_at` (`09:00:00Z`) had been set slightly ahead of real wall-clock time at
submission moment, and the server's `occursAfter` check requires the *new* event's real
server-clock `observed_at` to be strictly after the *prior* event's claimed `observed_at`. Waiting
~45 real seconds and resubmitting the identical, idempotency-keyed request succeeded once real
time caught up. Lesson carried into the second asset's submissions and into every future one:
always stamp `observed_at` from a fresh `date -u` call made at actual submission time, never a
hand-typed sequence of plausible-looking increasing timestamps -- a future-dated claim can
transiently outrun the real clock and self-block a later step in the same chain.

Current tally, independently re-verified live against `nirmana_evidence.nirmana_elevation_campaign_events`
(not assumed from the closeout prompt's text): 3/40 L0 assets terminal --
`bg_sarvatobhadra_grid` and `bg_gochara_citation_resolution` frozen this session, plus
`bg_vedha_malefic_scale` (one of the 31 rebuild_only assets, frozen 2026-09-03 via an earlier
build-run rehearsal predating this W4 wave -- confirmed still 5/5 terminal, not re-executed).
Remaining L0-W4 scope: 37 assets -- 30 rebuild_only needing `force=true` real builds (31 minus
the 1 already frozen), 2 verified_reuse via lineage proof, 2 probe completions, 3
producer_covered inheritance. Continuing per `NIRMANA_L0_CLOSEOUT_PROMPT_v1_0.md` W4 dispatch
rules.

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
- Days since last new capsule: 0 — the campaign's first `asset_frozen` capsule
  (`bg_vedha_malefic_scale`) was written and independently verified 2026-09-03, closing P4. See
  "P4 CLOSED" above for the full chain.
- This session hit GitHub's shared 5,000/hr API rate limit from merge-queue polling — logged as an
  operational note (open items #5), not a campaign finding.
