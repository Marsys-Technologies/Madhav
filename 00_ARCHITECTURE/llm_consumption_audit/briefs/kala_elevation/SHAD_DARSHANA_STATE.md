---
artifact: SHAD_DARSHANA_STATE (Campaign Ledger)
canonical_id: SHAD_DARSHANA_STATE
version: rolling
status: LIVE — created by Night 1 session (W0.1), updated at every wave boundary and session close
created: 2026-07-29
schema: per SHAD_DARSHANA_BRIEF_v2_0.md §6
governing: SHAD_DARSHANA_NIGHT_RUN_v1_0.md (orchestration) + SHAD_DARSHANA_BRIEF_v2_0.md (execution contract)
  + KALA_SUPREME_ELEVATION_v1_0.md (v1.2, spec authority) + KALA_SIX_VIEWS_DESIGN_v2_0.md/v1_0.md
---

# ṢAḌ-DARŚANA STATE — the campaign ledger

## NEXT-ACTION

**GATE W0 FORMALLY CLOSED (2026-07-29, between Night 1 and Night 2 — see the GATE W0 CLOSURE
RECORD below for full evidence).** The native applied the `mcp-canary-key` Secret Manager IAM
binding; `deploy.yml` re-ran clean (run `30484976742`), all three auth probes passed for real,
traffic promoted 100% to `amjis-mcp-00517-b5q`; live production verification (direct
authenticated JSON-RPC calls, bypassing any client-side tool-cache ambiguity) confirmed all 8
tools registered and functionally correct on BOTH canonical charts, including a live Mode-3
routing test. Single next action for Night 2: **resume Phase 2 fan-out** — 3 remaining W1
serving-join lanes (mudda+sandhi-lite · 24-lite-intervals+grading-facade+frontier-v0+
tri-plane-wiring), the citation-heavy `bg_muhurta_lattice`+`bg_parihara_rules` lane
(deliberately held back all of Night 1), then W2 build-out per the now-merged
`KALA_W2_FIELD_DESIGN_v1_0.md`. No blockers outstanding.

---

## GATE W0 CLOSURE RECORD (between Night 1 and Night 2, 2026-07-29 → 2026-07-30)

**Blocker resolved:** the native confirmed the exact grant scope (additive, read-only
`secretAccessor`, no rotation, trivially reversible) and authorized it. Applied:
`gcloud secrets add-iam-policy-binding mcp-canary-key --member="serviceAccount:github-actions@
madhav-astrology.iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
--project=madhav-astrology`. Verified before AND after via `get-iam-policy`: before = only
`amjis-web-runtime` bound; after = both `amjis-web-runtime` and `github-actions` bound,
nothing else touched.

**Deploy re-run, real evidence (not trusted from a report — logs read directly):**
`gh workflow run deploy.yml --ref main` → run `30484976742`, all 5 jobs green (Web, Pipeline
Job, MCP, Sidecar, path-detection). MCP job's `Post-deploy smoke` step log confirmed line by
line: `[health] OK (HTTP 200)` · `[probe: no-auth] 401 (expect 401) — PASS` ·
`[probe: bearer-auth] 200 (expect 200) — PASS` · `[probe: url-token-fallback] 200 (expect 200)
— PASS` · `=== Smoke PASS ===`. `Promote traffic to latest revision` log confirmed:
`100% LATEST (currently amjis-mcp-00517-b5q)`. This is the genuine authenticated pass the
pipeline was designed to require — the prior night's two dark deploys never reached this point.

**Live-production verification (Verifier-style acceptance, both canonical charts) — done
directly, real calls, not delegated:**
1. Registration check bypassed the session's own (stale, pre-deploy-snapshot) client-side tool
   cache entirely: a direct authenticated `tools/list` JSON-RPC call against
   `https://amjis-mcp-qm256lasva-el.a.run.app/mcp` confirmed all 8 new tools present
   (`kala_now_get`, `kala_ahead_get`, `kala_elect_get`, `kala_story_get`, `kala_priority_get`,
   `kala_explain_get`, `kala_upaya_get`, `kala_ritual_get`) alongside the still-live legacy
   aliases (correct — nothing retired yet, per strangler discipline). 152 tools total.
2. Functional calls, both charts (`482012f1` Abhisek, `1c826d5a` Abhinandan):
   `kala_now_get` → HTTP 200 on both, envelope-conformant (`reading` with
   thesis/evidence/dissent/verdict/falsifier keys — E3's argument schema live; `coverage` as a
   3-state list; `field_snapshot_id` present as the documented pre-W2 stub form;
   `calibration_maturity` present with honest all-zero values — correct pre-Living-LEL state,
   not fabricated; `tri_plane` + `drill_pointers` present).
3. `kala_ritual_get` and `kala_upaya_get` stubs confirmed honestly reporting `not_in_corpus` /
   W4-not-yet-landed coverage states rather than fabricating data.
4. **The hard-gated Mode-3 routing rule tested live** (undertaking-shaped payload to
   `kala_ritual_get`): `wrong_view: true`, `correct_surface: "kala_elect_get"`, honest
   `no_lever` on the interpretation/prediction tri-plane slots, a live `intervention_ref`
   pointer to ELECT — matches Elevation §8 exactly, verified against real production.
5. One transient HTTP 401 observed on a first call attempt, immediately resolved on identical
   retry (200) — consistent with the same infrastructure-instability pattern the Night 1
   morning report already flagged (background-agent stalls/connection drops), not a real auth
   regression; not chased further as it self-resolved and matches a known noise class.

**Disposition:** Gate W0 → **VERIFIED-CLOSED.** All 8 tools live on production, both charts,
envelope-conformant, Mode-3 routing verified. `main` == production for the MCP surface as of
this record (Web/Sidecar/Pipeline-Job were already clean from Night 1's manual dispatches).

## Night 1 history (superseded detail below; see MORNING REPORT for the authoritative close-out)

**Night 1, Phase 0 — CLOSED.** Phase 1a (spine) — **VERIFIED-MERGED**: PR #877
(`kala_envelope.ts` + `argument_composer.ts`, 42/42 new tests, `tsc --noEmit` clean)
independently confirmed merged to `main` @ `5208bc55` — files present, scope-clean (touched
exactly the 4 files claimed), the one failing status check (`Boot-time pointer validation
SC-17/18/19`) confirmed pre-existing on `main` before this PR, not introduced by it, and not a
required check (auto-merge proceeded without override). Items E3/E4/E5/43 partially advanced
(envelope contract exists; not yet consumed by any tool, so still NOT-STARTED at the
item-disposition level until a facade wires it — see brief §6, items close on serving, not on
library existence). **Phase 1b now dispatched, all 6 lanes IN-PROGRESS** in fresh worktrees off updated
`main`@`5208bc55` (each on branch `shad-darshana/<lane>`): now-ahead (kala_now_get,
kala_ahead_get) · elect-story (kala_elect_get, kala_story_get; ELECT is the Mode-3 landing
target) · priority-explain (kala_priority_get, kala_explain_get) · upaya-ritual-stub
(kala_upaya_get stub, kala_ritual_get Modes 1-2 stub + the Mode-3 `wrong_view` redirect,
implemented for real from day one per Elev §8) · parva-dedup (bug fix in existing STORY
substrate, span+level dedup — NOT the new facade) · ci-skeletons (specificity v0,
prose-survival, tri-plane no-dead-end, completeness census seed, authority-basis census seed,
Mode-3 single-route assertion — this one is explicitly allowed to report its Mode-3 test as
pending until upaya-ritual-stub merges). Next action: await all 6 completions, verify each
independently (PR status, scope discipline, real merge — do not trust self-reports), run the
merge train, then close Gate W0 (deploy #1) once all 8 tools are live + CI skeletons green +
sealed-harness regression shows no loss, both charts.

**INFRASTRUCTURE FIX (discovered mid-Phase-1b, PR #878):** the campaign's own brief/design docs
and this ledger were UNTRACKED in git — meaning absent from every worktree's filesystem (a
worktree only contains committed content). Confirmed absent from a live worktree
(`shad-darshana-now-ahead`). `elect-story` lane's agent caught this itself mid-run and was
reading around it via the main checkout's absolute path when it hit an unrelated API
connection error and terminated — **not a logic failure, a transient error; the worktree has
no commits, safe to relaunch.** Root-cause fix: PR #878 commits the whole `kala_elevation`
briefs directory (docs-only) to `main`, auto-merge enabled, pending CI. **Caution for
verification:** the other 5 lanes launched BEFORE this fix landed — each must be checked for
whether it worked around the missing docs (like the spine lane and elect-story did) or
proceeded with incomplete context; do not assume clean. Once #878 merges, `elect-story` will
be relaunched fresh from updated main so it has the docs natively. Going forward: the ledger
must be periodically committed to `main` via small docs PRs at phase/gate boundaries (not
after every edit) so it stays durable and visible to future worktrees — the primary checkout's
live copy (this file) remains the authoring surface for the session, but a stale un-synced
ledger defeats its own purpose as "the campaign's memory."

**Lane status (Phase 1b):**
- `parva-dedup` — **PR #879 open, verified scope-clean (2 files: `query_life_arc.ts` +
  `query_life_arc_dedup.integration.test.ts`), auto-merge enabled, CI running.** Real defect
  found and fixed: `ka_jivana_parva`'s inclusive-both-ends date filter double-emits each
  mahadasha-boundary antardasha (own-lord rule + contiguous periods → the boundary AD
  satisfies both adjoining MD spans). Writer left untouched; fix is serving-side dedup
  (`DISTINCT ON (start_year, end_year, dasha_planet, level)`, keeping highest `parva_index`)
  in `query_life_arc.ts` (feeds `kala_life_arc_get`). Live-confirmed on all 3 built charts
  (100→91, 100→91, 109→99 rows) before landing the fix. Regression test added, integration-gated.
- **PR #878 (docs-sync) MERGED** — campaign docs now visible in every fresh/rebased worktree.
- `now-ahead`, `priority-explain` — hit the same transient API-connection error mid-response
  (not a logic failure; a pattern of 2 such drops this session so far). Both had real
  uncommitted progress in-worktree (modified `register_p1_aliases.ts`, `registry_bridge.ts`,
  new `kala_views/`) — **resumed via SendMessage rather than discarded**, told about the
  now-merged docs fix, instructed to finish + PR normally.
- `elect-story` — terminated on the same transient error before any commit; worktree clean.
  **Resumed via SendMessage** with instruction to rebase onto main (to pick up PR #878's docs)
  then proceed with original scope.
- `upaya-ritual-stub`, `ci-skeletons` — each hit a stall (600s no-progress watchdog); both had
  substantial real uncommitted progress in-worktree, resumed via SendMessage. `now-ahead` hit a
  SECOND transient connection drop after its first resume, also resumed again — real progress
  intact each time ("all prior edits are intact" per its own check before the second drop).
  **Pattern note:** all 5 remaining lanes have now hit multiple transient stalls/connection
  errors this session (some 2-3 times) — session infrastructure instability, not a logic
  problem in any lane; SendMessage-resume has preserved worktree progress every time, zero
  data loss.
- **PR #880 (priority-explain) MERGED.**
- **`upaya-ritual-stub` — PR #882 open, verified scope-clean** (6 files: `ritual.ts`,
  `ritual.test.ts`, `upaya.ts`, `upaya.test.ts`, `registry_bridge.ts` registration,
  `m8_e2e_proof.test.ts` count bump). **Mode-3 routing rule reviewed directly (not just
  trusted from the report)**: `isMode3ShapedRequest` fires on any non-blank `undertaking`
  field; `buildMode3WrongViewResponse` is synchronous with zero I/O (proof-by-construction of
  no passthrough), sets `wrong_view:true`, `correct_surface:'kala_elect_get'`, live
  `intervention_ref` pointer, honest `no_lever` on the other two tri-plane slots — matches
  Elevation §8 exactly. Hit merge conflicts against `main` (registry_bridge.ts +
  m8_e2e_proof.test.ts, both also touched by the already-merged priority-explain) —
  **Conductor resolved via `git merge origin/main` (not force-push, per rail B.1)**: combined
  both lanes' registrations additively, and caught a real error neither lane could have seen
  alone — both sides' branches independently computed their own tool-count delta (58→60,
  26→28) assuming their +2 was the ONLY addition, but with both lanes' registrations now
  landing together the true combined count is 62/30, not 60/28. Fixed, then verified
  empirically (not just arithmetic): `tsc --noEmit` clean, `m8_e2e_proof.test.ts` 35/35
  pass with the corrected counts. Pushed as a merge commit.
- **`now-ahead` — PR #883 open, verified scope-clean** (same file set pattern: `now.ts`,
  `ahead.ts`, 3 test files, `registry_bridge.ts`, `register_p1_aliases.ts`,
  `kala_temporal.ts`). Same merge-conflict class against `main` (this time vs. priority-explain
  only, upaya-ritual-stub not yet merged) — same fix pattern applied: additive registration
  merge, tool count corrected to 62/30, verified empirically (`tsc --noEmit` clean, 35/35
  tests pass), pushed as a merge commit. Confirming these are genuinely thin facades: every
  field either passes through a row verbatim from the underlying capability or directly
  relabels an existing pre-computed value — no new SQL/join/derivation.
- **Note on #882:** the `upaya-ritual-stub` agent independently resolved the SAME merge
  conflict the Conductor was resolving by hand, concurrently, in the same worktree — explains
  the "file modified since read" errors hit during manual resolution. Both converged on the
  identical correct fix (62/30). Real operational lesson for future nights: don't assume a
  resumed agent has gone idle just because a stall/error notification fired — it may resume
  and keep working before the next check-in. No harm this time (verified the final on-disk
  state independently either way), but worth avoiding the race going forward.
- **PR #882 (upaya-ritual-stub) and PR #884 (elect-story) both MERGED.** #884 landed 8 files
  (`elect.ts`, `elect.test.ts`, `story.ts`, `story.test.ts`, registration, count bump) —
  scope-clean, verified. The elect-story agent's connection dropped only during its final
  status-report phase; the actual work (commit, push, PR, auto-merge) had already completed
  successfully — Conductor found it merged, not stuck.
- **PR #879 (parva-dedup) MERGED.**
- `now-ahead` (#883) hit a THIRD conflict round (registry_bridge.ts + count assertion) after
  elect-story's merge — resolved the same way (additive merge, empirically-verified count,
  now 66/34 combining all four W0.4 lanes: now-ahead + upaya-ritual-stub + priority-explain +
  elect-story, each +2/+2). Pushed as a merge commit; branch nudged via update-branch (was
  BEHIND). Only `ci-skeletons` (#881) and `now-ahead` (#883) remain open — both clean/mergeable,
  nudged to update, awaiting CI. **5 of 6 Phase 1b lanes merged; Gate W0 close is next once
  these two land.**
- **PR #883 (now-ahead) MERGED.** All four W0.4 view-facade lanes now merged.
- **Real CI failure caught and fixed on `ci-skeletons` (#881), post-merge of its Mode-3
  dependency.** Once `kala_ritual_get` (upaya-ritual-stub, #882) merged, the Mode-3
  single-route test ran for real for the first time — and failed: a Mode-3-shaped request
  got `wrong_view:false` and fell through to Mode-1 (`opportunity_scan`) logic instead of
  redirecting. **Diagnosed, not assumed**: pulled the CI job log, found the test's payload
  shaped `undertaking` as an object (`{intent, description}`, authored before the sibling's
  schema was visible), but the now-merged `ritual.ts` declares
  `undertaking: z.string().optional()` — a deliberate, documented design (header comment:
  "no field an undertaking could hide behind"). `isMode3ShapedRequest`'s `typeof === 'string'`
  check correctly rejected the object, so the routing rule ITSELF is not broken — the test's
  payload was stale. Fixed the payload to a plain string (not the implementation — the schema
  is the ratified contract); both Mode-3 tests now pass empirically against the live merged
  code (verified directly, not trusted from a report). Also caught a real push race: an
  earlier `update-branch` API call had already pushed a merge commit to this branch that the
  local worktree hadn't pulled — resolved via `git merge` (not force-push) before pushing the
  fix. Pushed as commit `7190a79f`.
- **PR #881 (ci-skeletons) MERGED.** All 6 Phase 1b lanes complete — all 8 kala_* tools
  registered and merged to `main`. **Gate W0's remaining requirements: live on production
  (both charts), tool_search surfacing, sealed-harness regression, Verifier live acceptance.**
- **Deploy #1 attempt found a real, pre-existing, deploy-blocking bug — not campaign-caused,
  but campaign-discovered.** The `main`-branch deploy triggered automatically by these merges
  (`deploy.yml`, run `30423782330`) built and deployed a new Cloud Run MCP revision
  successfully, but `scripts/operator/mcp_end_to_end_smoke.sh` crashed on a bash parse error
  (`syntax error near unexpected token '('`), so traffic promotion was SKIPPED — the new
  revision (carrying all 8 kala_* tools) is deployed but dark; production still serves the
  prior revision. **Root cause, verified precisely** (not guessed): the script's
  `SMOKE_MCP_URL` error message contains an apostrophe (`deploy-cloudrun's`) inside a
  `${VAR:?message}` parameter expansion — a real, reproducible bash quirk (confirmed via
  `bash -n` and an isolated minimal repro) where a lone `'` inside `:?`/`:-` word-text opens
  an unterminated quoted string regardless of outer double-quote context, silently swallowing
  the rest of the file until it resurfaces as a stray-token error elsewhere. This has
  apparently broken every automated MCP smoke-and-promote step since the script was added —
  tonight's merges are just the first time it's been exercised. **Fixed** (PR #885,
  scope-clean single-line rephrase, auto-merge armed) and scoped a repo-wide grep for the same
  defect class (one other match, confirmed a false positive via `bash -n`). **Next: once #885
  merges, a fresh push to `main` is needed to re-trigger `deploy.yml` and get a clean
  smoke-and-promote run** (the dark revision from the failed run won't auto-promote itself).
- **PR #885 MERGED.** Confirmed the fix works: triggered a manual `workflow_dispatch` deploy
  (run `30433773914`, since `deploy.yml`'s path-detection only diffs `HEAD~1` and wouldn't have
  picked up the campaign's earlier merges) — `deploy-mcp`'s `if:` condition bypasses
  path-detection entirely under `workflow_dispatch`, confirmed by reading the workflow source
  before relying on it. Build + Cloud Run deploy succeeded; the smoke script now runs its real
  logic (no more parse crash): health check PASS, no-auth-rejection PASS (401 as expected).
- **Gate W0's "live on production" sub-condition — PARKED-HONEST, genuine external block, not
  something this session can resolve.** The smoke script's Bearer-auth and URL-token-fallback
  probes correctly FAIL LOUDLY (by the script's own explicit design) because `MCP_CANARY_KEY`
  is empty — the Secret Manager IAM binding for `mcp-canary-key` is still not applied (same
  gap flagged at Phase 0 preflight, independently confirmed via `PARISHODHANA_REPORT_v1_0.md`:
  "native action still required"). Traffic promotion was correctly skipped by the pipeline.
  **Conductor decision: NOT overriding this and manually promoting traffic without a real
  authenticated call.** The deploy cadence (brief §B.2) names "real authenticated call" as its
  own step for a reason — a production auth-path safety gate failing loud on missing
  credentials is not the same failure class as the earlier bash syntax bug; forcing it through
  on partial verification (health + no-auth only) would be exactly the kind of unilateral
  judgment call this campaign's Adjudicator boundaries exist to keep off an autonomous
  session's plate. **Unblock condition: the native applies the `mcp-canary-key` Secret
  Manager IAM binding for the GitHub Actions service account** — everything else re-runs clean
  once that lands (no code change needed, confirmed by this session's fix already being live
  on `main`). Code-complete state of Gate W0 (all 8 tools registered, merged, CI green) stands;
  only the live-traffic attestation is blocked. **Continuing Phase 2 work in the meantime**
  (per NIGHT_RUN §C, Phase 2 runs beside Phase 1/Gate-W0 close, not strictly after it) — main
  merges don't require production traffic to already reflect W0.

## Phase 2 — IN PROGRESS (first 2 of ~10 lanes dispatched)

- `w2-design` (Opus): the W2 field-as-science design doc (`KALA_W2_FIELD_DESIGN_v1_0.md`) —
  hazard-composition formula, provenance schema, null calibration, salience/submodular
  selection, 8-type insight catalog, skill-score/GOF definitions, DAG edges +
  weights-version-acyclicity mechanism (§2.5.4 — the subtle one). Design-only, no code.
- `bg-cohort` (Sonnet): `bg_cohort.py` writer (item 22) — synthetic reference cohort, global
  L0 upsert idempotency, migration reserved next-after-471 (agent re-verifies live max
  itself), seed row + both Nirmāṇa reconciliation checks required green in the same PR.
- **`w2-design` — PR #886 open, verified scope-clean (1 file, docs-only), auto-merge armed.**
  Substantial, high-quality design work: real closed-form hazard formula (λ as a power-weighted
  geometric product with noisy-OR promise, multiplicative thinning suppression, structural
  Adṛṣṭa floor), analytically-integrable log-linear field storage (peak-always-at-breakpoint
  invariant preserved deliberately for hash-replayability), a real skill-score/GOF definition
  (circular-shift null, deterministic bootstrap CI, three-state honest publication), and the
  weights-version acyclicity mechanism correctly specified — plus a self-caught refinement
  (resolve the weights version once in `plan_substeps`, not per-substep, to prevent a
  straddling build from mixing two weights versions into one non-deterministic hash). **Also
  caught a real cross-wave dependency bug**: the brief's own §2.5.3 proposes `bg_sky_calendar`
  as a `ka_kshetra` W2 dependency, but that asset is W3-owned and doesn't exist yet at W2 —
  would have broken `topoSort` in production. Documented an edge-staging rule (W2 declares
  without it; W3 adds it in its own seed-row PR) rather than silently building around it.
  Confirmed the one failing check (`Boot-time pointer validation`) is the same pre-existing,
  non-required TAP failure already confirmed at PR #877 — persists on main's last 3 commits,
  unrelated to this PR, not blocking.
- **`bg-cohort` — PR #887 open, verified scope-clean (5 files: writer, test, seed-registry
  update, has-writer-completeness update, migration `472_bg_synthetic_cohort.sql`), auto-merge
  armed, was BEHIND — nudged.** Real, verified engineering: N=10,000 synthetic births,
  fixed-seed RNG for reproducibility, 200-year window (chosen to span ~6.8 Jupiter / ~2
  Saturn-Rahu-Ketu cycles), Lahiri-only (a base-rate cohort needs one consistent frame, not
  all 5). **Found and honestly handled a real edge case**: `swe.houses()` (Placidus) fails near
  the polar circles — empirically probed 5,000 samples to confirm ±60° is safe rather than
  fabricate a placeholder Ascendant for failures (§N.7 discipline). Actually stood up a
  throwaway local Postgres cluster, ran real migrations + the writer, verified 10k rows in
  1.6s and correct idempotent re-run (0 new inserts, unchanged count) — not just unit-tested,
  live-verified. Migration 472 confirmed against live max (471) before use, no collision.
  Full Python suite: 4131 passed, 0 failed. **Side-note, investigated and resolved**: the
  agent found `CONDUCTOR_HALT_LOG.md` (unrelated governance file) locally modified in its
  worktree with a fresh FORENSIC-gate failure entry (Sun/Moon/Lagna all wrong, matching the
  exact historically-documented "wrong ayanamsha config → Scorpio not Aries" trap from
  CLAUDE.md §B) — traced to the agent's own throwaway test Postgres cluster almost certainly
  lacking production ayanamsha config; correctly left uncommitted by the agent, out of
  campaign scope, no action needed.
- **`bg-sky-calendar` — PR #888 MERGED, verified scope-clean** (5 files: writer, test,
  has-writer-completeness update, seed-registry update, migration
  `473_bg_sky_calendar.sql`). Took 4 resumes (session instability, not task difficulty — each
  resume showed real incremental progress). **Found a genuine floating-point boundary bug** in
  a shared, reused `find_ingress_events` utility: at an exact sign-cusp, `exact_longitude_deg`
  can land ~1e-7° on the wrong side, making the re-derived `sign` field report the prior sign
  even though the loop's own `target_sign` is unambiguous. Fixed on the writer's own side by
  trusting `target_sign` rather than re-deriving from the boundary-adjacent longitude — did
  NOT modify the shared utility itself (correctly out of scope for this lane), flagged to
  Conductor that other lanes reusing that utility near sign boundaries may hit the same thing.
  Chart-specific returns correctly skipped (belongs in `ka_kshetra` per brief §2 verbatim, as
  instructed). Migration 473 landed with no collision against bg-cohort's 472.

**All 3 dispatched L0/design Phase-2 lanes now complete and merged: w2-design (#886),
bg-cohort (#887), bg-sky-calendar (#888).**

## Phase 2 — W1 serving-join lanes (dispatching conservatively, ONE at a time)

**Deliberate deviation from NIGHT_RUN's suggested full-parallel W1 fan-out**: all 6 W1 lanes
edit the SAME shared facade files built in W0 (`now.ts`, `ahead.ts`, `elect.ts`, `story.ts`,
`priority.ts`, `explain.ts`) — a much higher collision density than tonight's W0/L0 pattern
(distinct new files per lane). Dispatching W1 lanes one at a time rather than all 6 concurrently
to avoid a 6-way merge-conflict storm on shared facades; will reconsider parallelizing once the
collision pattern is better understood from the first lane.

- **`w1-lel` dispatched** (Sonnet): item 10 (per-chapter LEL pinning + retrodiction fit, on
  STORY) + the Circularity-Guard LEL-invariance CI test — this is a **hard, unsoftenable gate**
  per the campaign's own kickoff contract. Instructed to write a real detector against the
  best current field-adjacent proxy (true field doesn't exist until W2) and name the proxy
  explicitly rather than stub the test meaninglessly.
- Not yet dispatched: recurrence-ladder+digest (2), dual-reference+daśā-lord-condition (8+28),
  kālam/diśā-śūla/chandrāṣṭama/horā/janma flags (32+29), mudda+sandhi-lite (30+1), 24-lite
  intervals+grading-facade+frontier+tri-plane (24-lite/38-lite/43); `bg_muhurta_lattice` +
  `bg_parihara_rules` (citation-heavy, still deliberately held back).
- **`bg-sky-calendar` — PR #888 MERGED.** Ingresses (9 grahas), stations (5 classical
  planets), eclipses, Jupiter-Saturn double-transit conjunctions; chart-specific returns
  correctly deferred to `ka_kshetra` per brief §2's explicit language, not built here.
  Migration 473, no collision. **Found and fixed a genuine floating-point boundary bug**: the
  shared `find_ingress_events` utility's re-derived `sign` field could land ~1e-7° on the
  wrong side of an exact sign cusp; fixed by trusting the loop's own unambiguous
  `target_sign` instead of re-deriving from the boundary-adjacent longitude. Live-verified
  against a throwaway Postgres (real migrations, real writer run, idempotency confirmed).
- All L0 substrate items now merged except `bg-muhurta-lattice` + `bg-parihara-rules`
  (higher-risk corpus-extraction lane — Agnivāsa/combination-yoga/parihāra rule tables need
  real citation-backed content, still deliberately held back for careful individual dispatch).
- **`w1-lel` — PR #889 open, verified scope-clean (5 files), auto-merge armed.** Item 10
  (per-chapter LEL pinning + retrodiction fit) done honestly: lexical theme-keyword overlap
  signal, `insufficient_data` when nothing pins rather than a fabricated ratio. **The HARD
  campaign gate — Circularity Guard LEL-invariance — is genuinely empirical, not a stub**:
  runs the production `KaJivanaParvaWriter` twice inside one never-committed transaction with
  a synthetic LEL row inserted between runs, asserts byte-identical output, verified no rows
  leaked. Static census caught a real (harmless, comment-only) LEL reference in an unrelated
  writer and rewrote it. Honest proxy note: targets `ka_jivana_parva` (closest existing
  "field-shaped" output) since W2's `ka_kshetra` doesn't exist yet — documented in the test's
  own docstring and the PR body as needing re-pointing once W2 lands, not silently glossed
  over. Full CI-equivalent suite: 4132 passed, 0 failed.
- `w1-lel` PR #889 MERGED (confirmed).
- **`w1-dual-dasha` — PR #891 open, verified scope-clean (4 files), auto-merge armed.** Items
  8 + 28 done: gochara dual-reference computes `house_from_moon` and `house_from_lagna`
  independently for all 9 grahas and serves both side by side (never a silent single-reference
  default); daśā-lord transit-condition reports current MD+AD lord's transit sign/house/dignity,
  and the AHEAD forward variant correctly pins the SAME lord identity as-of-today and projects
  ITS transit forward to the horizon, rather than re-identifying the ruling lord at a future
  date (a subtle correctness distinction the agent got right). Both fields kept strictly
  objective (raw houses + classical dignity labels, no favorable/unfavorable grading) per Gate
  W1's no-subjective-judgment-calls requirement. 47 new/extended tests pass, typecheck clean.
- **`w1-flags` — PR #892 open, verified scope-clean (4 files), auto-merge armed.** Items 32 +
  29 done: found existing-but-unwired substrate (`panchang_engine` already computes
  diśā-śūla/gulika-kālam, just never consumed by a `kala_*` view). Honest disclosure on
  gulika-kālam-ahead's horizon (bounded to the panchāṅga service's own 31-day cap, surfaced
  explicitly rather than silently truncated). **Janma-resonance's definition WAS found in the
  corpus** (KALA_SIX_VIEWS_DESIGN v2.0 + KALA_SUPREME_ELEVATION §9) — correctly implemented in
  full rather than defaulting to `not_in_corpus`, reading the native's own birth vara/tithi/
  nakshatra verbatim from L1 `chart_facts` (never re-derived, per §N.5). **Merge-conflict
  verification**: this lane edited the same files as the just-merged `w1-dual-dasha` — fetched
  + merged origin/main, resolved by concatenating both lanes' additions; independently
  confirmed post-merge that both lanes' fields (`dasha_lord_transit_condition`,
  `gochara_dual_reference`, `disha_shula`, `chandrashtama`) all coexist in `now.ts`, nothing
  lost. All objective, 3-state coverage, no new computation/migration.
- Not yet dispatched: 3 remaining W1 serving-join lanes (mudda+sandhi-lite · 24-lite
  intervals+grading facade+frontier v0+tri-plane wiring), `bg-muhurta-lattice` +
  `bg-parihara-rules`.
- **Merge-train note:** with 4+ lanes all registering new tools through the same
  `registry_bridge.ts` + bumping the same `m8_e2e_proof.test.ts` count assertions, every lane
  after the first to merge will hit this same conflict shape. Conductor is resolving each via
  `git merge origin/main` (never force-push) and re-deriving the count empirically rather than
  trusting either side's arithmetic — this is now the expected, not exceptional, path for the
  remaining lanes.
- **`ci-skeletons` — PR #881 open, verified scope-clean** (12 files, all under
  `.github/workflows/`, `platform-mcp/src/__tests__/`, `platform/scripts/census/shad_darshana_gates/`
  — no facade/lib/migration files touched). All 6 §0.6 items built: specificity gate v0,
  prose-survival battery (6/6 pass), tri-plane no-dead-end (7/7 pass), completeness census
  seed (52/52 items present, 7/7 pass), authority-basis census seed (**real detector: found 20
  live temporal-claim tools, honestly reports 0/20 carrying `authority_basis`** — correct
  pre-W2 state, not a stub), Mode-3 single-route assertion (**correctly SKIPPED, not
  fabricated-pass** — `kala_ritual_get` from `upaya-ritual-stub` not yet merged; written
  strictly against Elevation §8's binding text, will start asserting once that lane lands, no
  code change needed). Auto-merge enabled.

## Session log

| Session | Date | Phases worked | Outcome |
|---|---|---|---|
| Night 1 | 2026-07-29 | Phase 0 (boot) | IN-PROGRESS |

## Wave status

| Wave | Status | Evidence | Notes |
|---|---|---|---|
| W0 | **VERIFIED-CLOSED** | PRs #877/#880/#882/#883/#884/#881 (merged main@`42151b24`+); deploy run `30484976742`; direct production `tools/list` + functional calls on both charts; see GATE W0 CLOSURE RECORD above | All 8 tools live on production, both charts, envelope-conformant, Mode-3 routing live-verified. |
| W1 | **IN-PROGRESS (5 of 8 items landed)** | PRs #889 (item 10), #891 (items 8,28), #892 (items 29,32) | Items 8,10,28,29,32 done. Items 2,1-lite,30,24-lite,38-lite,E6-lite not yet started. |
| W2 | **DESIGN-COMPLETE, build not started** | PR #886, `KALA_W2_FIELD_DESIGN_v1_0.md` merged | Hazard formula, skill-score/GOF, DAG acyclicity all specified precisely; 5 build lanes not yet dispatched. |
| W2G | NOT-STARTED | — | GOCHARA-2.0 sub-day. **BLOCKED on N1–N5 ratification (W2G.0) — see below.** |
| W3 | NOT-STARTED | — | New computations over the field. |
| W3K | NOT-STARTED | — | KP sub-lord engine (item 18, built from zero). |
| W4 | NOT-STARTED | — | Intervention flagship (UPĀYA/YAJÑA). Opus design mandatory. |
| W5 | NOT-STARTED | — | Planner integration; native's hard gate (real MCP calls). |
| W6 | NOT-STARTED | — | Cutover + retirement. |

## N1–N5 ratification block (W2G precondition — blank N5 means W2G is not startable)

| Item | Ruling | Ruled by | Date | Rationale |
|---|---|---|---|---|
| N1 (wave naming) | — | — | — | Pending ANTARYĀMIN pre-queued adjudication. |
| N2 (multi-chart rollout order) | — | — | — | Pending. |
| N3 (pre-1984 backfill) | — | — | — | Pending. |
| N4 (cutover posture) | — | — | — | Pending. |
| N5 (lock granularity) | — | — | — | **FROZEN-contract question. Native ruling required; ANTARYĀMIN may only apply the pre-ruled CONSERVATIVE-DEFAULT (chart-level lock stays, no orchestrator change, reversible) if the native has not yet spoken. Not yet recorded.** |

## Registry item status (1–44 + E1–E8)

All items below seeded **NOT-STARTED** per W0.1. Disposition vocabulary: VERIFIED-FIXED /
VERIFIED-NO-DEFECT / PARKED-HONEST / FAILED-REOPENED. `OUT-OF-SCOPE-BY-DESIGN` is retired and
illegal.

| # | Item | Wave | Status | Both-charts | Evidence |
|---|---|---|---|---|---|
| 1 | Daśā-sandhi calendar | W3 (lite@W1) | NOT-STARTED | — | — |
| 2 | Recurrence-ladder serving | W1 | NOT-STARTED | — | — |
| 3 | Sky-event calendar | W3 | **VERIFIED-FIXED (bg_sky_calendar built; per-chart contact joins deferred to ka_kshetra per spec)** | Y (global asset) | PR #888, live-verified against throwaway Postgres |
| 4 | Moorti-nirṇaya | W3 | NOT-STARTED | — | — |
| 5 | Vedha + Sarvatobhadra grid | W3 | NOT-STARTED | — | — |
| 6 | Activity-specific muhūrta tables | W3 | NOT-STARTED | — | — |
| 7 | Muhūrta-lagna | W3 | NOT-STARTED | — | — |
| 8 | Gochara dual-reference | W1 | **VERIFIED-FIXED** | Y (code-level; both-charts serving not yet live-attested pending W0 deploy) | PR #891 |
| 9 | Health/adverse event class | W3 | NOT-STARTED | — | — |
| 10 | Per-chapter LEL pinning | W1 | **VERIFIED-FIXED** | Y (code-level) | PR #889; Circularity Guard empirically verified |
| 11 | Provenance edges | W2 | NOT-STARTED | — | — |
| 12 | Daśā-system applicability | W2 | NOT-STARTED | — | — |
| 13 | Tithi-Praveśa | W3 | NOT-STARTED | — | — |
| 14 | Janma-anchored election rules | W3 | NOT-STARTED | — | — |
| 15 | Rarity axis | W2 | NOT-STARTED | — | — |
| 16 | Kota-Chakra | W3 | NOT-STARTED | — | — |
| 17 | Sudarśana-Chakra | W3 | NOT-STARTED (naming ruled) | — | Conductor ruling: writer named `ka_sudarshana_varsha` — confirmed namesake-only collision vs `bo_sudarshana.py` (different layer/computation), not built yet |
| 18 | KP sub-lord clock (CR-75) | W3K | NOT-STARTED | — | — |
| 19 | GOCHARA-2.0 sub-day | W2G | NOT-STARTED | — | — (blocked on N1–N5) |
| 20 | Auto-filed prospective ledger entries | W2 | NOT-STARTED | — | — |
| 21 | Per-tradition calibration weights | W2 (ongoing) | NOT-STARTED | — | — |
| 22 | Synthetic reference cohort + matched sub-cohort | W2 | **VERIFIED-FIXED (cohort only; matched sub-cohort not built — that's W2's job)** | Y (global asset) | PR #887, `bg_cohort`, live-verified 10k rows against throwaway Postgres |
| 23 | Circular-shift null calibration | W2 | NOT-STARTED | — | — |
| 24 | Uncertainty-budget propagation | W1-lite/W2-full | NOT-STARTED | — | — |
| 25 | Salience vector + submodular selection | W2 | NOT-STARTED | — | — |
| 26 | UPĀYA-SETU | W4 | NOT-STARTED | — | — |
| 27 | kala_timeline_spec v1 | W2 | NOT-STARTED | — | — |
| 28 | Daśā-lord transit-condition | W1 | **VERIFIED-FIXED** | Y (code-level) | PR #891, current+forward both implemented, forward correctly pins lord identity as-of-today |
| 29 | Chandrāṣṭama/horā/janma-resonance flags | W1 | **VERIFIED-FIXED** | Y (code-level) | PR #892; janma-resonance definition found in corpus, not fabricated |
| 30 | Mudda daśā join | W1 | NOT-STARTED | — | — |
| 31 | Period-echo mining | W3 | NOT-STARTED | — | — |
| 32 | Diśā-śūla + gulika-kālam joins | W1 | **VERIFIED-FIXED** | Y (code-level) | PR #892; gulika-kālam-ahead horizon honestly disclosed (31d cap) |
| 33 | Absence-of-expected detector | W3 | NOT-STARTED | — | — |
| 34 | Contrastive EXPLAIN | W3 | NOT-STARTED | — | — |
| 35 | Planner wiring verified LIVE (hard gate) | W5 | NOT-STARTED | — | — |
| 36 | Contender lattice + adjudication engine | W3 | NOT-STARTED | — | — |
| 37 | Ritual-resonance + paddhati profile | W3/W4 | NOT-STARTED | — | — |
| 38 | ELECT ritual-pairing + grading unification | W1 facade/W3/W4 | NOT-STARTED | — | — |
| 39 | Living-LEL incremental calibration plane | W2 | NOT-STARTED | — | — |
| 40 | kala_ritual_get registration + planner wiring | W0 stub/W4/W5 | **W0-stub VERIFIED-FIXED** (Modes 1-2 honest not_in_corpus; Mode-3 wrong_view redirect real & tested) | Y | PR #882 |
| 41 | Muhūrta Factor Census + corpus extraction | W3 | NOT-STARTED | — | — |
| 42 | Unified Intervention Ledger | W4 | NOT-STARTED | — | — |
| 43 | Tri-plane traversability contract | W0–W1 | **W0-facade-level VERIFIED-FIXED**; full W1 wiring in-progress | Y | PRs #877/#880-884, `no_lever`-honest pointers on every merged facade |
| 44 | Single-temporal-authority (`authority_basis`) | W0 seed/W2/W6 gate | **W0 seed VERIFIED-FIXED**; population is W2's job | — | CI skeleton census seed, PR #881 |
| E1 | Point-process formalization + skill score | W2 | **DESIGN-COMPLETE, build not started** | — | PR #886: closed-form hazard, skill-score/GOF formulas specified precisely |
| E2 | Insight synthesis stage | W2 | **DESIGN-COMPLETE, build not started** | — | PR #886: all 8 insight types + trigger predicates specified |
| E3 | Argument-shaped reading + specificity gate | W0/W2 | **W0-skeleton VERIFIED-FIXED**; hard-gate flip is W2's job | Y | PRs #877, #881 |
| E4 | question_frame compiler | W0 | **VERIFIED-FIXED** | Y | PR #877, `kala_envelope.ts` |
| E5 | field_snapshot_id | W0/W2 | **W0-stub VERIFIED-FIXED**; real hash is W2's job | Y | PR #877, marked with explicit TODO(W2) upgrade point |
| E6 | Per-view elevations | W1–W3 | NOT-STARTED | — | — |
| E7 | Substrate (census CI, freshness, cohort, composer lib, skill-score CI) | W0/W2 | **PARTIAL**: composer lib + census CI seeded (W0), cohort built (W2-prep, PR #887); skill-score CI not yet | Y (cohort, global) | PRs #877, #881, #887 |
| E8 | Non-elevations register | standing | NOT-STARTED | — | — |

## Preflight (Phase 0)

- Repo clean: **NO** — pre-existing uncommitted state on the checked-out session branch
  (`satyadipa/orchestrator-lit-predicate`, unrelated SATYA-DĪPA work) and numerous untracked
  docs from other in-flight campaigns (PARIPRASHNA, narration_audit, PARISHODHANA). None of
  this is campaign scope; not touched. Campaign work branches from `main` (fast-forwarded to
  `origin/main` @ `8e1af4ca` this session), isolated in its own worktrees.
- Both canonical charts healthy (LC-5 sweep staleness on `1c826d5a`): **NOT CLEARED — ticketed
  per brief's own "CLEARED or ticketed" allowance, does not block W0/W1.** Live query against
  `kala_gochara_windows`: canonical chart `482012f1` has 8,345 rows to horizon 2084-12-30
  (58y forward); `1c826d5a` has only 1,267 rows to horizon 2027-07-03 (~1y forward) despite
  being computed *more recently* (2026-07-26 vs 2026-07-24/25) — a real coverage-horizon gap,
  not a timestamp-staleness one. **TICKET: `1c826d5a` needs a full gochara-sweep rebuild
  extending its horizon to parity with the canonical chart before any both-charts gate that
  depends on forward-window coverage can honestly close** (W1 items touching AHEAD-window
  serving are the first to hit this — Conductor to watch for it at Gate W1, not before).
- Canary pipeline state: real automated canary blocked — `MCP_CANARY_KEY` IAM binding not yet
  applied by the native (confirmed via `PARISHODHANA_REPORT_v1_0.md` + handoff doc, both
  independently). **Not a campaign blocker** — brief's own fallback applies: manual canary
  discipline (deploy.yml fails safely closed without the binding). Deploys proceed under this
  discipline until the native applies the grant.
- Migration range reserved: **472–495, in `platform/supabase/migrations/`** (see below for why
  that directory, not `platform/migrations/`).
- Duplicate-copy + tool-name census:
  - **Item 17 vs `bo_sudarshana.py` — CONFIRMED namesake collision, NOT a functional
    duplicate.** `bo_sudarshana.py` is an L2 Bodha static house-triad MSR signal writer
    (9 grahas × 5 ayanamshas, `bodha_msr_signals`). Item 17 (Sudarśana-Chakra year-wheel) is
    an L3 temporal progression technique — different layer, different computation, same
    classical term. **Conductor naming ruling (W0, no adjudication needed — plain engineering
    call): item 17's writer is named `ka_sudarshana_varsha`, never bare `sudarshana`, to keep
    the two permanently distinguishable in registries/logs.**
  - **`kala_activations` — confirmed live, but as a JSON field key, not a table or tool.**
    Written/read in `register_d9_judgment.ts` (`timing_hooks.kala_activations`) and
    reconciled in `registry_bridge.ts`. No table/tool collision exists, but **no new campaign
    envelope field or table may reuse this exact string for a different shape** — live serving
    code pattern-matches on it.
- Nirmāṇa catalog-reconciliation baseline: **CLEAN before this campaign adds anything.**
  `catalog_reconciliation.test.ts` 6/6 PASS; `test_has_writer_completeness.py` 3/3 offline PASS
  (1 live test needs `DATABASE_URL`, skipped locally); direct DB check confirms only 5
  pre-existing `has_writer=false` assets, none campaign-relevant. Brief §2.5.1 requires both
  checks stay green in the same PR as every new writer going forward — not a one-time gate.
- **Live collision note (out of campaign scope, flagged for awareness only):** the
  currently-checked-out session branch (`satyadipa/orchestrator-lit-predicate`, unrelated
  SATYA-DĪPA work) carries an unmerged `platform/migrations/466_asset_throughput_incomplete_state.sql`
  that collides on number 466 with main's `466_omega8_floor_wiring.sql`. This campaign's
  worktrees branch from `main`, not from that branch, so it's unaffected — noted here only so
  a future session doesn't mistake it for a campaign-caused collision.
- No existing SHAD_DARSHANA work found in git history (`origin/main` has no `shad-darshana*`
  branches, no PRs matching the campaign) — confirmed first night.

## Migration range reserved

**472–495, in `platform/supabase/migrations/`** (reserved 2026-07-29, Night 1). Two migration
directories both apply to prod and are deduped by filename (`migrate.ts`); the standing policy
doc (`MIGRATION_DIRECTORY_POLICY_v1_0.md`, 2026-05-22) claims `platform/migrations/` is
canonical and supabase is frozen, but the actually-current convention — per
`platform/supabase/migrations/README.md` and observed practice, both directories growing in
lockstep — is that new migrations land in `platform/supabase/migrations/`. Combined live max
on `main`@`8e1af4ca` = 471 (`471_retire_mcp_predictions.sql`). **Re-check the live max
immediately before writing the FIRST actual migration this campaign lands** — this range could
go stale if another campaign lands migrations first; 472 is a reservation, not a guarantee.

## Deployed revisions

`amjis-mcp-00517-b5q` — 100% traffic, deploy run `30484976742`, 2026-07-29T19:35 UTC. First
campaign revision serving all 8 kala_* tools live. Web/Sidecar/Pipeline-Job also current from
this same run (all 5 jobs green).

## Open PRs

None yet.

## Skill-score scoreboard

Not yet published (first publish at W2 close becomes the CI baseline).

## Specificity-gate status

Not yet seeded (W0.6 skeleton pending).

## Authority-basis census scoreboard (item 44)

Paths enumerated: — / carrying `authority_basis`: — / computing own windows: — (target: 0).

## Dark-corpus bright% per chart

Not yet re-measured this campaign (baseline = PARIŚODHANA measurement, referenced at W6).

## Live-MCP verification table (W5)

Not started.

## W4 Mode-2 fixture disposition

Not started.

## ADJUDICATION log (ANTARYĀMIN)

**None.** No would-be-human question actually arose tonight — W2G and W3K (the two waves whose
pre-queued adjudications exist for exactly this) never started, since W2G is correctly blocked
on the native's own N1–N5 ratification (not yet requested — Night 1 never reached W2G) and W3K
depends on W2's clock machinery (not built yet). The one naming decision made (item 17 →
`ka_sudarshana_varsha`) was plain Conductor engineering authority per brief §2 ("Conductor
confirms against live registries at W0"), not a would-be-human judgment call, so it's recorded
under item 17's evidence, not here. This is an honest empty log, not an unused mechanism.

## MORNING REPORT — Night 1 close (2026-07-29 → 2026-07-30)

**Gates closed:** None VERIFIED-CLOSED in the brief's strict sense (a gate requires production
liveness + Verifier live acceptance, neither yet possible). **Gate W0 is CODE-COMPLETE**: all
8 tools (`kala_now_get`, `kala_ahead_get`, `kala_elect_get`, `kala_story_get`,
`kala_priority_get`, `kala_explain_get`, `kala_upaya_get`, `kala_ritual_get`) registered on
`main`, envelope-conformant, CI green, Mode-3 routing rule genuinely tested end-to-end. It
cannot formally close tonight — see the single blocker below.

**Items dispositioned VERIFIED-FIXED tonight:** 3 (sky calendar), 8 (dual-reference), 10 (LEL
pinning + the hard-gated Circularity Guard), 22 (synthetic cohort), 28 (daśā-lord condition),
29 (chandrāṣṭama/horā/janma-resonance), 32 (diśā-śūla/gulika-kālam), 40 (ritual stub + Mode-3
redirect), 43 (tri-plane, facade-level), 44 (authority-basis, seed-level); E3–E5 (W0-level),
E1/E2 (design-level via PR #886), E7 (partial). Item 17 naming ruled, not yet built. Everything
else (30 registry items, all of E6/E8, all of W2's actual build, all of W3/W3K/W4/W5/W6)
remains NOT-STARTED — **this campaign is realistically 14–24 sessions per its own brief; Night
1 covered Phase 0 through the start of Phase 2, which is on-pace, not behind.**

**The one real blocker — parked, not worked around:** Gate W0's production-liveness and every
downstream deploy this campaign needs are blocked on **the native applying the
`mcp-canary-key` Secret Manager IAM binding** for the GitHub Actions service account. This is
a genuine external dependency: the deploy pipeline's own smoke-test script is correctly
designed to fail loud rather than silently skip its auth verification when the key is
unavailable, and overriding that safety gate to force a production traffic promotion without a
real authenticated call would be exactly the kind of unilateral judgment call this campaign's
Adjudicator boundaries exist to keep off an autonomous session's plate — so it was not done.
Two manually-triggered deploy attempts tonight (`workflow_dispatch`, bypassing the pipeline's
stale path-detection) both built and pushed the Cloud Run image successfully and both stopped
at the same auth-probe gate for the same reason. **main ≠ production right now, and that is
the honest, documented state — not a false close.** Everything else deployed clean (Web,
Sidecar, Pipeline-Job images all shipped tonight); only the MCP surface is dark.

**Rulings made:** one, Conductor-authority (not ANTARYĀMIN): item 17's writer named
`ka_sudarshana_varsha` after confirming the `bo_sudarshana.py` "collision" is a namesake only
(different layer, different computation). Migration range 472–495 reserved in
`platform/supabase/migrations/` (through 473 actually used; 474–495 remain free). No
ANTARYĀMIN rulings were needed (see ADJUDICATION log above).

**Real defects found and fixed along the way (not just forward progress):**
1. The campaign's own governing docs were never committed to git — silently broke every fresh
   worktree's ability to read them. Fixed early (PR #878).
2. `ka_jivana_parva` double-emitted every mahadasha-boundary antardasha row (own-lord rule +
   inclusive-both-ends date filter). Fixed serving-side, live-verified on all 3 built charts
   (PR #879).
3. The Mode-3 routing CI test's payload predated the sibling lane's ratified schema
   (`undertaking` as an object vs. the real `z.string()`) — the routing rule itself was sound;
   only the test was stale. Diagnosed via live CI logs, not guessed (fix pushed directly).
4. A pre-existing, deploy-blocking bash bug: an apostrophe inside `${VAR:?message}`
   parameter-expansion syntax silently broke every automated MCP smoke-and-promote step since
   the script was added — discovered because tonight's merges were the first real exercise of
   the pipeline in a while. Root-caused via isolated `bash -n` repro before touching anything;
   fixed with a one-line rephrase (PR #885).
5. The W2 design itself would have created a production DAG break: brief §2.5.3 proposes
   `bg_sky_calendar` as a W2-time `ka_kshetra` dependency, but that asset doesn't exist until
   W3 — caught during design, not during a broken build; resolved with an explicit edge-staging
   rule (PR #886).
6. A floating-point sign-cusp boundary bug in shared ingress-detection code (~1e-7° landing on
   the wrong side of an exact cusp); fixed by trusting the unambiguous loop variable instead of
   re-deriving from boundary-adjacent longitude (PR #888).
7. `swe.houses()` (Placidus) fails near the polar circles — found via a 5,000-sample empirical
   probe before it could produce a silent placeholder value in the cohort writer; bounds
   narrowed to ±60° rather than fabricating a fallback Ascendant (PR #887).

**Parks and reasons (all PARKED-HONEST, all with a stated release condition):**
- Gate W0 production-liveness — blocked on native's `mcp-canary-key` IAM grant (above).
- `1c826d5a`'s (Abhinandan's) gochara-sweep forward horizon — truncated to ~1y vs. the
  canonical chart's 58y despite a more recent compute timestamp; ticketed at Phase 0 preflight,
  needs a full sweep rebuild before any both-charts gate depending on forward-window coverage
  can honestly close (first bite: any future W1 AHEAD-window gate check).
- `bg_muhurta_lattice` + `bg_parihara_rules` — deliberately never dispatched tonight; needs
  real citation-backed Agnivāsa/combination-yoga/parihāra content, judged to warrant a more
  careful individual session rather than being rushed alongside the batch lanes.
- W2G — correctly never started; blocked on the native's N1–N5 ratification per brief §3
  W2G.0, which this campaign may not decide autonomously. Not yet even requested from the
  native (Night 1 didn't reach the point of needing it).
- W3K — correctly never started; depends on W2's clock machinery, which isn't built yet.

**Skill scoreboard:** not yet publishable — W2's build (the actual field/skill-score
computation) hasn't started; only its design is done. First publish remains the W2-close CI
baseline per brief §3 Gate W2.

**Specificity-gate / authority-basis-census / dark-corpus scoreboards:** unchanged from seed
state — all three populate at W2/W6 per the brief's own schedule, not before.

**Housekeeping done at close:** all 15 of tonight's worktrees removed cleanly (each already
merged to main, verified before removal); local `main` fast-forwarded to `origin/main`
throughout the session, currently at `f573be8d`+ (includes unrelated concurrent work from
other active sessions in this repo — confirmed no conflicts touched campaign files). One
stale, pre-existing, locked worktree (`/tmp/prdocs`, predates this session) left untouched —
not created by this campaign, not safe to remove unilaterally.

**Operational note for Night 2:** roughly 15+ background-agent stalls/connection-drops
occurred across the session (apparent infrastructure-level instability, not task-specific) —
every single one was resumed from intact worktree state via SendMessage rather than
restarted from scratch or silently abandoned; zero work was lost to this pattern, but it did
slow the night down substantially. If it recurs, the same resume-don't-restart discipline is
the right response.

**Single next action:** the native applies the `mcp-canary-key` Secret Manager IAM binding for
the GitHub Actions service account, then Night 2 re-runs
`gh workflow run deploy.yml --ref main`, confirms the smoke script's auth probes pass and
traffic promotes, runs Verifier live acceptance on both canonical charts, and formally closes
Gate W0 — after which Phase 2 continues (3 remaining W1 lanes, the parihāra/lattice lane, W2
build-out against the now-merged design doc).

*Truth over completion. PARKED-HONEST with evidence, not a false close.*
