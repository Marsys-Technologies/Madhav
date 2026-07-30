---
artifact: SAMAPTI_MERGE_LEDGER
canonical_id: SAMAPTI_MERGE_LEDGER
version: 1.8
status: LIVE
created: 2026-07-30
governed_by: 00_ARCHITECTURE/briefs/samapti/SAMAPTI_DVARAPALA_LEDGER.md (Ruling 50)
---

<!--
CHANGELOG
1.8 (2026-07-30, INT) — merge #8 (B-MIG-HASH-DISCLOSURE round 2, PR #943 -> 29d98dc6). PIPELINE
    UNBLOCKED after 4 consecutive failed deploys. Integrator independently re-derived the blocking
    set by two methods before merging (set-compare of pinned vs blocking = exact 25/25 match, zero
    either direction; plus each pin's current_sha256 re-verified against live on-disk content) --
    the cross-check whose absence caused round 1. Rebase resolved an add/add collision with #942
    (which had landed 165_chart_panchanga alone) by taking round 2's 25-entry superset, verified a
    true superset with byte-identical shared pin values. Real deploy confirmed end-to-end through
    the migration step and back into the DB, not CI green.
1.7 (2026-07-30, INT) — merge #7 (B-MIG-HASH-DISCLOSURE round 1, PR #941 -> 3e05ef17) recorded as
    MERGED-BUT-DEPLOY-FAILED. Mechanism sound, coverage short (16 pinned of 25 blocking). Records
    the Integrator's own enumeration error that caused the undercount (regex assumed the sha256
    column always holds a sha256; 17 rows are MD5 or free-text sentinels), the corrected figures,
    the 9 files round 2 must add, and the cross-campaign spread to SAD-DARSANA's #940. Also files
    the shared-shape method lesson: two silent-drop scoping bugs in one night.
1.6 (2026-07-30, INT) — merge #6 (B-MIGGUARD, PR #921 -> 81af26b7) recorded as MERGED-BUT-DEPLOY-
    FAILED, deliberately not health-verified. Its own new migrate.ts sha256 guard fail-closed on
    first live run against a real pre-existing integrity violation; smoke+promote skipped, so
    production was never degraded (still serving d93ea6d1) but is now behind main. Full 349-row
    scope enumerated read-only: 326 match / 16 mismatch / 7 applied-but-missing. Merge queue HALTED
    per DVA Ruling 73; disclosed-residual allowlist authorized, 16-file reconciliation parked.
    Resume bar is a REAL end-to-end deploy success, not CI green.
1.5 (2026-07-30, INT) — merge #5 (B-HALT-LOG-ROOTCAUSE, PR #935 -> d93ea6d1). Required an
    authorized 3-line fix first: the branch inserts 16 lines into ga_sade_sati_writer.py, shifting
    three already-allowlisted §5 C.7 violations by exactly +16 and orphaning their {file,line}
    allowlist entries -- a coordinate-staleness false positive, not a new violation (gate was green
    on main). Coordinates bumped 1349->1365 / 1383->1399 / 1535->1551 per DVA Ruling 72; diff is
    exactly 3 lines. Residual filed: re-key the allowlist on `pattern` (already supported by its
    schema) instead of `line`, since any edit above an entry reproduces this.
1.4 (2026-07-30, INT) — merge #4 (A7-N8-AUDIT, PR #904 -> 97f82e8a) recorded. Confirms the
    Ruling 65 A1-before-A7 sequencing was load-bearing: A7's register cites A1-preserved artifacts 5
    times and those citations resolve on main only because A1 landed first. Governance held at 216/45
    -- the new 1144-line register introduced zero schema violations.
1.3 (2026-07-30, INT) — merge #3 (A4-LOOP-G1, PR #902 -> 95340d32) recorded: §5 migration renumber
    474 -> 486 (the authored 474 would have collided with an existing platform/migrations/474_*),
    applied in 3 places incl. the COMMENT ON COLUMN that becomes production data; migration verified
    live via pg_constraint (ON DELETE SET NULL) and col_description ("migration 486"); DVA Ruling 5+71
    orphan deletion discharged with a pre-delete hash re-check. Also reports a pre-existing duplicate
    migration number 484 on main (ṢAḌ-DARŚANA #930/#932), not corrected by this lane.
1.2 (2026-07-30, INT) — merge #2 (A1-PRESERVE, PR #896 -> 0d919718) recorded, with three
    read-together notes: (a) schema 43->45 is Ruling 4's pre-identified +2, verified to be exactly
    those two files and no third; (b) 19/19 blob-SHA preservation proof at three checkpoints, and
    Ruling 5's deletion trigger now ARMED and proven reversible; (c) a manual workflow_dispatch
    deploy that bypassed the CI gate and every path gate, logged as deploy-on-red class for DVA.
1.1 (2026-07-30, INT, per DVA Ruling 64) — two corrections to the v1.0 backfill:
    (a) unmerged-lane count corrected 25-of-26 -> 30-of-31 (PRs #895–#935), now carried as a
        timestamped as-of measurement because the figure moves during the run;
    (b) amjis-mcp health row annotated with the 2026-07-30T07:30Z SIGABRT crash window, so a
        point-in-time 200 is not read as continuous health. Row 1 (A2-CI-POINTERS) re-verified
        field-by-field against live state and left unchanged — all values confirmed accurate.
1.0 (2026-07-30, PERFECT CLOSURE pass) — file created, A2-CI-POINTERS row backfilled.
-->


# SAMAPTI_MERGE_LEDGER

One row per SAMĀPTI lane merged into `main`. Populated by INT at each merge per DVA
Ruling 50 ("record BOTH counts in SAMAPTI_MERGE_LEDGER.md at EACH merge — the tools
already run, this is transcription, not computation"). This file was mandated at
Ruling 50 but not actually created until the PERFECT CLOSURE pass (2026-07-30,
backfilled retroactively for the one merge that had already happened, going forward
from here in real time).

Governance counts (`drift_detector.py` / `schema_validator.py`) are measured against
the merge commit itself, in an isolated worktree, per the practice INT and DVA have
both used throughout this campaign.

---

## Merges

| # | Lane | PR | Merge commit | Merged at (UTC) | Drift findings | Schema violations | Deploy triggered | Health-verified |
|---|---|---|---|---|---|---|---|---|
| 1 | A2-CI-POINTERS | #901 | `ea6497ff815666c644209dc43f1b5504a0f4dfbd` | 2026-07-30T05:16:04Z | 216 | 43 | web (unconditional) + mcp (path-gated, touched `platform-mcp/**`); sidecar correctly skipped | **Yes** — deploy run `30516643607`: web `/api/health`=200, mcp `/health`=200 + 3/3 auth-shape probes PASS, sidecar dependency probe=200; traffic promoted 100%; `commit-sha` label = `ea6497ff8` on both web and mcp. TAP CI (SC-17/18/19), red on main for 4 consecutive prior commits, confirmed green after this merge. |
| 2 | A1-PRESERVE | #896 | `0d919718f26f8623c042852b32aa7a00397385bf` | 2026-07-30T08:00:18Z | 216 | **45** (see note — by design) | web only via `workflow_run` (correct: A1 is docs-only, so mcp/sidecar/pipeline correctly skipped). **Separately**, a manual `workflow_dispatch` at 08:02 force-deployed all four services at this same commit — see note. | **Yes** — `workflow_run` deploy `30525700749` success (migrations ✓, post-deploy smoke ✓, promote ✓). All three services at `commit-sha=0d919718`, 100% traffic, `ready=True`; 9/9 health probes 200 (`amjis-web` `/api/health`, `amjis-mcp` `/health`, `amjis-sidecar` `/health`, 3× each). |
| 3 | A4-LOOP-G1 | #902 | `95340d32474277ec50917c4602ba94a919154fe0` | 2026-07-30T09:16:05Z | 216 | 45 (unchanged from #2 — A4 adds no governance artifacts) | web only (correct: A4 touches `platform/src/**` + a migration, not `platform-mcp/**` or `python-sidecar/**`, so mcp/sidecar/pipeline correctly skipped) | **Yes** — deploy `30530639062` success (migrations ✓, smoke ✓, promote ✓). `amjis-web-01295-b9c` @ `95340d32`, 100%; mcp/sidecar correctly remain @ `0d919718`. 9/9 probes 200; 0× 5xx across all three services in the following 15m. **Migration verified applied in production** — see note. |
| 4 | A7-N8-AUDIT | #904 | `97f82e8ab0884c806dd2b908970567015c013f23` | 2026-07-30T10:38:14Z | 216 | 45 (unchanged — the new register adds **zero** violations; its frontmatter is clean) | web only (docs-only lane; mcp/sidecar/pipeline correctly skipped) | **Yes** — deploy `30535931966` success (migrations ✓ no-op, smoke ✓, promote ✓). `amjis-web-01296-svq` @ `97f82e8a` 100%; mcp/sidecar correctly remain @ `0d919718`. 9/9 probes 200; 0× 5xx across all three services in the following 15m. |
| 5 | B-HALT-LOG-ROOTCAUSE | #935 | `d93ea6d1eb7002c09b7774d0f756777576fd3e61` | 2026-07-30T11:39:40Z | 216 | 45 | web + **sidecar** + **pipeline-job** (correct: touches `platform/python-sidecar/ga_writers/**`, which matches both the sidecar and pipeline path filters); mcp correctly skipped | **Yes** — deploy `30539883878` success (migrations ✓, smoke ✓, promote ✓). `amjis-web-01297-89s` and `amjis-sidecar-00937-9jt` both @ `d93ea6d1` 100%; mcp correctly remains @ `0d919718`. 9/9 probes 200; 0× 5xx across all three in the following 12m. |
| 6 | B-MIGGUARD | #921 | `81af26b743a5d00c659313eb18a9cf3c209e5fcf` | 2026-07-30T12:10:40Z | 216 | 45 | web only attempted; mcp/sidecar/pipeline correctly skipped | **NO — DEPLOY FAILED.** Run `30541991123` failed at `Run database migrations`. `Post-deploy smoke` and `Promote traffic` both SKIPPED, so no revision was promoted and no migration applied even partially. **Production not degraded** (still serving `amjis-web-01297-89s` @ `d93ea6d1`, 9/9 probes 200) but is now BEHIND main. See note. |
| 7 | B-MIG-HASH-DISCLOSURE (round 1) | #941 | `3e05ef174fdd011010aa565c3ba79492006e45fd` | 2026-07-30T13:01:36Z | — | — | web only attempted | **NO — DEPLOY FAILED (incomplete fix).** Disclosure mechanism worked (pinned files correctly skipped) but coverage was short: threw on unpinned `165_chart_panchanga.sql`. Round 2 dispatched. Production not degraded. See note. |
| 8 | B-MIG-HASH-DISCLOSURE (round 2) | #943 | `29d98dc615f30c8e8b038a10e6fbfe5db1f14661` | 2026-07-30T14:16:26Z | 216 | 45 | web via `workflow_run`; mcp/sidecar/pipeline also deployed via a separate manual `workflow_dispatch` at 14:21 | **YES — PIPELINE UNBLOCKED.** Deploy `30551628423` success: `Run database migrations` ✓ (25 disclosed skips, 0 applied — nothing pending, 0 throws), smoke ✓ (`Smoke PASS`), promote ✓. `amjis-web-01299-nx2` @ `29d98dc6` = origin/main tip, 100%; mcp `00525-hrd` and sidecar `00940-8k6` also @ `29d98dc6`. 9/9 probes 200. DB re-verified: 366 applied rows, migration 486 present, its `ON DELETE SET NULL` effect still live. |

T0 baseline (DVA Ruling 4, immutable for the run): 216 drift findings / 43 schema violations,
measured at `origin/main` HEAD pre-A1. Merge #1 introduced zero new violations — exactly at baseline.

### Merge #2 (A1-PRESERVE) — three things that need to be read together

**(a) Schema 43 → 45 is BY DESIGN, not a regression.** A1 is the merge that commits the two files
DVA Ruling 4 pre-identified as KNOWN-TRANSIENT: `00_ARCHITECTURE/PARIPRASHNA_DESIGN_ENGINEERING_PLAN_v0_1.md`
and `03_DOMAIN_REPORTS/REPORT_WHOLE_CHART_SYNTHESIS_AND_MCP_DIAGNOSTIC_v1_0.md`. Both were untracked
before this merge, so the validator could not see them; committing them makes them countable.
Verified rather than assumed: of the 45 violations at `0d919718`, **exactly 2** name those two files —
no unexpected third. `45 = 43 (immutable T0) + 2 (Ruling 4, owned by B-DOCS-GOVERNANCE, PR #928)`.
Drift held at **216**, unchanged. Per Ruling 4, T0 stays 216/43 for measurement; these +2 are
itemized and attributed, never absorbed into the baseline.

**(b) Preservation proof — A1's actual product.** Blob SHAs recorded for all 19 files at the
pre-rebase commit `a5cc942d`, re-checked after a 3-commit rebase onto `d5c4b359`, and re-checked
again on `origin/main` post-merge. **All 19 identical at all three points** — byte-exact preservation
confirmed end-to-end, not merely asserted. DVA Ruling 5's deletion trigger is now ARMED: the recovered
draft is on main (`…/ledgers/RECOVERED_BRIEF_PB-3_PRIOR_DRAFT_fuse_hidden0000000500000001.md`,
16220 bytes / 279 lines) and is `git hash-object`-identical to the surviving orphan at
`00_ARCHITECTURE/briefs/pariprashna_build/.fuse_hidden0000000500000001`, so deleting the orphan is
now trivially reversible — Ruling 5's own stated condition. Not executed at merge #2: Ruling 5 named
no owner. **RESOLVED at merge #3** — DVA Ruling 71 authorized it and assigned it to INT's next lock;
the orphan was deleted on 2026-07-30 after re-confirming `git hash-object` identity against the
on-main copy *immediately before* the `rm` (not relying on the earlier check). No `.fuse_hidden*`
remains anywhere in the checkout. Recoverable via
`git show origin/main:00_ARCHITECTURE/briefs/pariprashna_build/ledgers/RECOVERED_BRIEF_PB-3_PRIOR_DRAFT_fuse_hidden0000000500000001.md`.

### Merge #3 (A4-LOOP-G1) — migration renumber 474 → 486, and its production proof

**The §5 renumber was not cosmetic — the authored number would have collided.** PR #902 authored its
migration as `474_samiksha_ledger_part_fk_on_delete_set_null.sql`. Recomputed fresh from `origin/main`
at lock time: `max(platform/migrations/) = 474`, `max(platform/supabase/migrations/) = 485` → **486**
(matching Ruling 70's prediction, but derived independently rather than taken on trust). `474` is
already occupied by `platform/migrations/474_asset_throughput_incomplete_state.sql`, so shipping as
authored would have put two different migrations at 474 across the two directories. Renumbered in
**three** places, not just the filename: the `-- Migration NNN:` title, the header's number-provenance
paragraph, and — easily missed — the `COMMENT ON COLUMN` string at line 71, which is written into the
database as durable data. Re-verified at every rebase: still 486 at each new tip, and no open PR held
484–499. Guard `825084` was correctly excluded from the max (it is a trailing token in
`182_bg_ephemeris_target_floor_825084.sql`, not a migration number).

**Applied and verified in production, not merely "the step exited 0":**
- Deploy log: `Applied: 486_samiksha_ledger_part_fk_on_delete_set_null.sql`
- Live DB, `pg_constraint`: `brahma_mimamsa_prediction_ledger_message_part_id_fkey` → `ON DELETE SET NULL`
  (was `NO ACTION`) referencing `message_parts` — the migration's actual intended effect.
- Live DB, `col_description`: the column comment reads "…claim kept (**migration 486**)…" — confirming
  the renumber propagated all the way into production data, not just the repo.

**Pre-existing defect found while computing the max, NOT introduced here and NOT corrected here:**
`484` is duplicated on `origin/main` — both `484_bg_muhurta_lattice.sql` and
`484_bg_synthetic_cohort_md.sql` exist in `platform/supabase/migrations/`. That collision arrived via
ṢAḌ-DARŚANA's #930/#932 and means the migration-numbering discipline has already been broken on main
independently of this run. Reported rather than silently renumbered — renumbering another campaign's
already-applied migration is not an Integrator action.

### Merge #4 (A7-N8-AUDIT) — the A1-before-A7 sequencing paid off, measurably

Ruling 65 sequenced A1 ahead of A7 because VER found A7's register cites A1's then-unmerged content.
Verified post-merge rather than assumed: A7's register
(`SAMAPTI_N8_EARNED_SIGNAL_REGISTER_v1_0.md`, 1144 lines / 77398 bytes) cites
`SAMAPTI_IMPLEMENTATION_BRIEF_v2_0.md` **4×** and `session_queue_SAMAPTI.yaml` **1×**. Both now resolve
on `origin/main` — they exist there only because A1 (merge #2) landed first. Had A7 merged ahead of A1,
those 5 citations would have been dangling for anyone checking the register out. Sequencing validated.

Rebase note: 4 commits replayed onto `95340d32`, zero conflicts, and the register's blob SHA
(`9c631543…`) is **identical pre- and post-rebase** — the rebase moved the base, not the content.

### Merge #6 (B-MIGGUARD) — the deploy pipeline is BLOCKED. Read this before merging anything.

**Status: merged to main, deploy failed, merge queue HALTED.** This row is deliberately not marked
health-verified. CI was fully green (27 pass) — including the lane's own new
`MIG-1 — migration number guard` step, which went green on main. The deploy then failed anyway.
That gap between "CI green" and "deploy succeeded" is the lesson of this row.

**What failed.** #921 adds `assertAppliedHashMatches()` to `platform/scripts/migrate.ts`, which
verifies an already-applied migration's on-disk sha256 still matches what was recorded when it ran.
On its **first live execution** it refused to proceed:

```
MigrationHashMismatchError: "0000_seed_legacy_applied.sql" is already recorded as applied
in _migrations_applied, but its SQL content on disk no longer matches the sha256 recorded
when it was applied.   stored 72e9b22a…   current 4320a1cf…
```

Independently confirmed: the on-disk hash recomputed locally from `origin/main` equals CI's
`4320a1cf…` exactly, and the stored `72e9b22a…` was read directly from `_migrations_applied`.
The edit traces to commit `751ce3b8` ("seed all 86 pre-tracking legacy migration files"), which
modified a migration *after* it had been applied. **The guard is correct — it found real drift.**

**Scope: it is not one file.** The runner fails fast, so CI reported only the first mismatch. A
read-only enumeration of all 349 `_migrations_applied` rows against their `origin/main` content:

- **326 match** · **16 MISMATCH** (each will block the runner in turn) · **7 applied but absent from disk**

The 16: `0000_seed_legacy_applied`, `002_ganita_divisionals`, `158_classical_texts_schema`,
`215_chart_facts_formula_id`, `229_reap_orphaned_building_throughput`, `231_bg_target_floor_fix`,
`237_drop_signal_type_registry`, `250_bg_dignity_reference`, `294_ga_vastu_target_floor`,
`314_bo_samskara_count_sql_scope_fix`, `322_fix_asset_registry_names_and_status`,
`358_bodha_orphaned_writer_registry`, `370_has_writer_completeness`,
`377_ka_dasha_kala_target_floor`, `v13_pyramid_layers`, `ws2_l0_ontology`.

**This blocks every campaign, not just SAMĀPTI** — any merge to `main` by anyone now fails the same
way. As of this writing `main` has not moved since #921, so ṢAḌ-DARŚANA has not yet hit it.

**Disposition — DVA Ruling 73:** adopt the disclosed-residual allowlist (the same mechanism this very
lane built for the 484 duplicate, extended to the sha256 check): freeze the 16 as itemized/dated/
attributed entries, fail on any NEW mismatch. Explicitly NOT reverting #921 (that would neuter a
guard that just proved its worth) and explicitly NOT reconciling the 16 files tonight (real
investigative work, parked). Builder dispatched at elevated priority. The 7 applied-but-missing
files are a separate, currently-unchecked class — a second tranche if the guard is ever extended.

**Standing instruction until cleared:** no further merges, and the bar for resuming is a REAL
end-to-end deploy success, not CI green — tonight is precisely why those are different claims.

### Merge #7 (B-MIG-HASH-DISCLOSURE round 1) — incomplete fix, and an enumeration error worth recording

The disclosure mechanism itself is **sound** — the deploy log shows pinned files correctly skipped
with the two-sided pin (`stored_sha256` + `current_sha256_at_disclosure`). It failed only on
**coverage**: it pinned 16 files, and there are 25 blocking ones.

**Root cause of the undercount was the Integrator's, and is recorded here rather than absorbed.**
The scoping enumeration that fed this fix parsed `_migrations_applied` with a regex requiring
`[0-9a-f]{64}` — assuming the `sha256` column always contains a sha256. It does not:

| stored length | rows | example |
|---|---|---|
| 64 (real sha256) | 349 | `72e9b22a…` |
| 32 (MD5) | 7 | `87aba81910f35280b52f359301a0ec84` |
| 18 / 6 / 37 / 42 | 10 | `applied-2026-06-16`, `manual`, `applied-directly-via-proxy-2026-06-10` |

**17 rows are not sha256 at all** — MD5s and free-text sentinels from historical manual
applications. The regex silently dropped every one, and "16" looked plausible enough to escape
scrutiny. Corrected figures, recomputed with no length filter: **32 stored-hash mismatches total ·
7 not on disk (runner never reaches them) · 25 blocking · 16 pinned · 9 unpinned.**

The 9 that round 2 must add: `165_chart_panchanga`, `216_chart_facts_partial_indexes`,
`232_drop_ganita_positions`, `233_bg_throughput_dormant_to_lit`,
`234_activate_romanize_service_engines`, `235_all_dormant_throughput_to_lit`,
`323_ga_structural_graph_theoretic_floor_update`, `ws2_l0_reference`, `ws2_l0_texts`.

**For the parked reconciliation work:** 17 of the 32 never had a content hash recorded, so
"restore the file to its applied content" is *impossible* for them — there is nothing to restore
to. That subset needs a different disposition than the true sha256 drifts.

**Blast radius widened.** ṢAḌ-DARŚANA merged #940 (`2cba21c5`) into the blocked pipeline; both its
deploys failed on the same `165_chart_panchanga.sql`, one of them a manual `workflow_dispatch`
bypass attempt — which failed correctly, confirming fail-closed holds even against deliberate
override. Four consecutive failed deploys on main; production three merges behind but healthy
throughout (fail-closed: nothing promoted, no partial migration).

**Method lesson for the close report:** two Integrator scoping errors tonight shared one shape —
a tool silently dropping rows that did not match an assumed-universal pattern (`git show --stat`
truncating long paths to a false zero; this regex filtering non-64-char hashes). The first was
caught because a zero looked suspicious; the second was not, because 16 looked reasonable. An
enumeration that a fix will be built on should be cross-checked by a second method before anyone
depends on it — the plausible-looking count is precisely the one that escapes review.

**(c) A manual `workflow_dispatch` deploy bypassed the CI gate.** Run `30525058905`
(`event=workflow_dispatch`, actor `amonty84`) ran **08:02:19 → 08:09:30**, entirely inside Ganga CI's
window for this commit (**08:00:21 → 08:11:17**). Because `workflow_dispatch` short-circuits every
`needs.changes.outputs.*` path gate *and* the `workflow_run.conclusion == 'success'` gate, it deployed
web + sidecar + mcp + pipeline-job — including the `Run database migrations` step — roughly two minutes
before CI passed. Outcome benign (CI subsequently passed; A1 carries no migrations), but the mechanism
is the `deploy-on-red` risk class that manual §4 routes to DVA. Recorded, not adjudicated here.

---

## Retroactive current-state check (2026-07-30, PERFECT CLOSURE pass)

Independent of the above table: `main` has since advanced past merge #1 through 30+ unrelated
ṢAḌ-DARŚANA commits (not SAMĀPTI's to log here — see that campaign's own tracking). Current
`origin/main` HEAD `8f896784`. Live production check this session:

| service | revision | commit-sha label | probe |
|---|---|---|---|
| amjis-web | `amjis-web-01290-4cb` | `8f896784...` (= current HEAD) | `/api/health` → 200 `{"status":"ok"}` |
| amjis-mcp | `amjis-mcp-00521-ldr` | `8f896784...` (= current HEAD) | `/health` → 200 `{"status":"ok",...,"tools":88}` — **but see crash-window note below; a point-in-time 200 does not mean the service was continuously healthy** |
| amjis-sidecar | `amjis-sidecar-00934-bqb` | `a5945b17...` (PR #930, last sidecar-path-touching merge) | `/health` → 200 `{"status":"ok"}` |

Sidecar lags HEAD only because `deploy.yml`'s `deploy-sidecar` job is path-gated on
`platform/python-sidecar/**` and no later merge has touched that path — expected behavior,
not staleness or a rollback. (Verified: `a5945b17`/#930 touched 5 files under
`platform/python-sidecar/`, so `deploy-sidecar` correctly fired for it.)

### amjis-mcp crash window, 2026-07-30T07:30Z — transient, recovered, NOT SAMĀPTI's

The `/health` → 200 above is a steady-state reading taken after a real outage window. Recording
it so the ledger does not imply continuous health it never measured:

- `07:30:23.115Z` `ERROR Uncaught signal: 6, pid=1, tid=1, fault_addr=0` (SIGABRT)
- `07:30:23.944Z` `WARNING Container terminated on signal 6`
- `07:30:24.949Z` `[mcp:server] MARSYS-JIS MCP server listening on :8080` — auto-restart, ~1s
- **22 requests returned 5xx across a ~9s window**, including real client `/mcp` traffic, not
  only health probes. Zero 5xx in the preceding 3h and none since; 8/8 follow-up probes 200;
  revision reports `Ready`/`ContainerHealthy`/`MinInstancesProvisioned` = True.

**Not attributable to any SAMĀPTI merge.** The crash is on revision `amjis-mcp-00521-ldr`
@ `8f896784` (a ṢAḌ-DARŚANA merge). SAMĀPTI's merge #1 ran on `amjis-mcp-00519-c5l`, whose
entire service life (05:28–07:16Z) sits inside the zero-5xx window.

Hypothesis, **explicitly unproven**: V8 heap exhaustion at `--memory=512Mi` — signal 6 with
`fault_addr=0` is the classic Node fatal-abort signature. Not asserted as root cause.
Disposition: DVA Ruling 64 — observation only, does not hard-stop the merge queue; carried to
the close report as a transient production incident.

## Status of the other dispatched SAMĀPTI lanes

**30 of 31** dispatched lanes (`samapti/*` / `preserve/*` branches, PRs #895–#935) have
**not yet merged** — still open, in verification, or in the DVA ruling queue.
Measured 2026-07-30T07:3xZ: 31 total = 1 MERGED (#901, row 1 above) + 30 OPEN + 0 CLOSED.
This figure is live and moves during the run — a new lane PR appeared between two consecutive
reads while this correction was being written. Treat it as an as-of measurement, not a
fixed total; re-measure at E1-SAMGATI rather than trusting this number at close.
(Corrects an earlier "25 of 26" in this section, which undercounted.)
"Deploy triggered / health-verified" is not yet applicable to any of them; each gets a row here
the moment INT lands it, per Ruling 50's standing instruction. Do not backfill hypothetical
rows for unmerged lanes — an empty ledger entry for unmerged work is the honest state, not a gap.
