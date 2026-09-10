---
artifact: L5_W4_CANARY_RUNBOOK.md
canonical_id: NIRMANA_L5_W4_CANARY_RUNBOOK
version: "1.0"
status: CANARY 1 EXECUTED 2026-09-05T14:10Z — see §RESULT. Canaries 2/3 still READY.
session: L5
produced_on: 2026-09-05
---

# L5-W4 — canary dispatch runbook

Prepared during the W4 block (charter C8 item 5: pre-write, pre-compute, so the blocked
item moves instantly when it unblocks). **Nothing here has been executed.**

## Preconditions — ALL must be true before step 1

| # | gate | how to check | current |
|---|---|---|---|
| P1 | **#1715 / PR #1736 merged AND deployed** | Cloud Run revision `commit-sha` label CONTAINS the merge commit (C4 execution-safe rule — ancestry, not equality) | ✅ **merged**; re-verify the deploy before dispatch |
| P2 | **#1723 merged** (per-chart `count_sql` parameterisation) | needed for `integrity_verified`, not for the build itself | ✅ **merged** |
| P2b | **WP-6 live** (#1781) — dispatch refuses unacknowledged downstream destruction | ✅ merged. L5 needs **no** `--acknowledge-destroys`: its C13 cascade radius is measured EMPTY (see `L5_C13_BLAST_RADIUS_v1_0.md`). If WP-6 demands the flag for an L5 asset, **stop** — the measurement and the tool disagree and one of them is wrong. |
| P2c | **Migration 691 merged** (#1785) | **D-CND-09**: the registry window closes on the FIRST W2 acceptance. 691 carries the last of it (catalog_status sweep + the final 10 volume formulas). Accepting before it lands strands them and forces re-acceptance. | ✅ **merged** |
| P3 | E-gate OPEN for the asset | the C10 query, re-run — **never assume** | ✅ `mi_vistara` 0 unfrozen ancestors |
| P4 | W2 route recorded (C2.2) | `asset_analysis_accepted` + `optimization_verdict_accepted` exist for the asset | ✅ **both recorded live** 2026-09-05, independently re-verified by direct DB read and `egate.sql` |
| P5 | `NIRMANA_HOLD` absent at the shared checkout root | `ls /Users/Dev/Vibe-Coding/Apps/Madhav/NIRMANA_HOLD` | ✅ absent |
| P6 | A free run slot (C5: ≤3 campaign-wide) | read the latest SLOT LEDGER comment on **#1713** | check at dispatch |

## Why `mi_vistara` is canary 1

Cheapest execution in the entire campaign: **0.287 s mean over 39 timed runs** (measured, not
estimated), **zero dependencies**, **no code change needed to build**, and it has already
demonstrated an honest `lit`-at-0-rows termination. If the cross-layer gate has a defect, this is
the cheapest possible place to find it. It would also capture **the first provenance receipt any
`mi_*` asset has ever had** — `SELECT … FROM asset_provenance_receipts WHERE asset_id LIKE 'mi_%'`
returns zero rows today.

## THE DISPATCH TRAP — read before typing anything

`mi_vistara` is `domain='shared'`, `scope='global'`. WP-3's domain scoping is **live code**:
`isLayerSweepExcludedDomain` (`platform/src/lib/build/plan.ts` ~:191) returns true for
`domain='shared'`, and `computeLayerDispositions` (:441-444) assigns those rows the disposition
**`out_of_domain`** — enumerated, never built.

> **A `scope='layer'` / `scope_target='mimamsa'` dispatch will NOT build this asset.** It will
> report success having built 13 of 15. A canary that cannot be dispatched is not a canary.

Dispatch via **`--assets mi_vistara`** (the dispatcher's explicit subset path, which honours the
exact id named, shared or not). `runner.py:691` then forces `chart_id=None` for a `global`-scope
asset automatically, and :1096 takes the global-assets advisory lock. **No new code is needed —
only the correct selector.** Same applies to `mi_kula`.

## Credential path (native-authorized, already precedented)

Per `CAMPAIGN_STATE.md` "Rehearsal B credential blocker RESOLVED": the native explicitly
authorized direct GCP-CLI database access for this development-stage research system. The
established, reviewed path:

1. Cloud SQL Auth Proxy on a local port.
2. `gcloud secrets versions access` straight into an env var — **never printed, never logged,
   never written to a file** (hard floor §3.3).
3. Test with a harmless `SELECT current_user` before any real query.
4. Use **`amjis-db-password:3`** (the `amjis_app` role) — *not* a new or escalated credential; it
   is the same one the product already uses for every "click Build". `nirmana_campaign_control_writer`
   is deliberately SELECT-only on `build_runs`/`build_run_assets`, so it cannot do this by design.

## Sequence — CORRECTED against what canary 1 actually needed (three gaps found live)

**0. First, record the W2 acceptance events (C2.2) — they are NOT auto-recorded by anything.**
W2 "routing" in the decision docs is a documentation decision, not evidence. Compute
`registry_fingerprint_sha256` / `analysis_digest` via the REAL exported functions
(`registryContractFingerprintInput`, `canonicalRegistryContractDigest`,
`canonicalNirmanaAssetAnalysisDigestForRegistryRow` in `definitions.ts`) — never hand-reimplement.
`npm ci` under `platform/` first if `node_modules` is missing. A throwaway Vitest test (vitest
already stubs `server-only` and the `@` alias) is the easiest way to run them; delete it after.
Submit both events via `nrec --as executor` with `source_kind: git_commit`,
`source_ref: git:<live-deployed-sha>` (`gcloud run services describe amjis-web --region
asia-south1 --format="value(metadata.labels.commit-sha)"`). Verify with a direct DB read, not the
HTTP response alone.

**1. Claim the slot (C5) — BEFORE dispatch, never after.** Comment on #1713:
```
SLOT CLAIM
session: L5
asset: mi_vistara
weight: normal
run_kind: rebuild_only
claimed_at: <UTC ISO-8601>
```

**2. Take the fresh verified snapshot FIRST** (hard floor §3.5) — the precedent recipe
(`CAMPAIGN_STATE.md`, L0's `bg_vedha_malefic_scale` dispatch):
```
gcloud sql backups create --instance=amjis-postgres --project madhav-astrology
gcloud sql backups list --instance=amjis-postgres --limit=1   # confirm SUCCESSFUL, capture the id
```
`--snapshot-ref` = `cloudsql-backup:<id>`.

**3. Dry run WITH `--snapshot-ref` already included** — it is a hashed input to the manifest
digest, so a dry run without it produces a digest that will NOT match a `--commit` call that
includes it (`"runner manifest no longer matches the reviewed dry-run preview"`). Also needs
**three** things the original draft of this runbook got wrong:
```
DATABASE_URL="${DATABASE_URL}?options=-c%20search_path%3Dnirmana_evidence%2Cpublic" \
python platform/scripts/dispatch_nirmana_campaign_wave.py \
  --layer L5 --wave 0 --assets mi_vistara \
  --definition-revision t0-2026-09-01-0e5b06fb \
  --reviewed-deployment-sha <the exact sha used as source_ref in step 0> \
  --snapshot-ref cloudsql-backup:<id>
```
Corrections to the ORIGINAL draft (found live, not from docs):
  - **The `search_path` fix is required.** The script queries `nirmana_elevation_campaign_definitions`
    unqualified; `amjis_app`'s default `search_path` is `$user, public` and does not include
    `nirmana_evidence`. Without the `options=` query param the dry run fails with
    `relation "nirmana_elevation_campaign_definitions" does not exist`.
  - **`--reviewed-deployment-sha` is required for EVERY layer, not just L0** (post #1715/#1718
    generalisation — this runbook's original P1 note was stale). It must equal the exact sha used
    as `source_ref` on the step-0 evidence events, or the evidence-binding check silently treats
    them as not-current and reports "no accepted asset analysis found."
  - **`--snapshot-ref` must be present in the dry run too**, per the digest note above.
Review the printed `manifest_digest`. Confirm the previewed `run_id` did NOT persist
(`SELECT id FROM build_runs WHERE id = '<run_id>'` → 0 rows) — proves the dry run really is
rollback-only before trusting it as a preview.

**4. Commit the dispatch**, passing the digest from step 3 (the one WITH `--snapshot-ref` folded
in) verbatim:
```
DATABASE_URL="${DATABASE_URL}?options=-c%20search_path%3Dnirmana_evidence%2Cpublic" \
python platform/scripts/dispatch_nirmana_campaign_wave.py \
  --layer L5 --wave 0 --assets mi_vistara \
  --definition-revision t0-2026-09-01-0e5b06fb \
  --reviewed-deployment-sha <same sha> \
  --commit --confirm NIRMANA_CAMPAIGN_WAVE \
  --snapshot-ref cloudsql-backup:<id> \
  --expected-manifest-digest <digest from step 3>
```

**5. Verify against the JOB LOGS, not just the DB:**
```
gcloud run jobs executions describe <execution_name> --region asia-south1 --format=json
gcloud logging read 'resource.type="cloud_run_job" AND resource.labels.job_name="brahma-build-pipeline-job" AND labels."run.googleapis.com/execution_name"="<execution_name>" AND textPayload=~"<asset_id>"' --order=asc
```
Expect `rows_inserted=0` and an existence assertion; `mi_vistara` writes nothing by design. Then
cross-check `asset_throughput.state='lit'`, `build_run_assets.state='complete'`, and
`asset_provenance_receipts` for the asset (a zero-row write earns `receipt_state='unknown'`
honestly — nothing to fingerprint the output against, not a defect).

**6. Release the slot.** Comment on #1713 with `SLOT RELEASE` + outcome.

**7. W5:** run `l5_scripts/l5_w5_mechanical_checks.sql` + the asset's own
`integrity_check_sql` (migration 691). **A fresh-context verifier appends the capsule — not me.**
Implementer ≠ certifier is structural (C8, prompt §7.4).

## §RESULT — canary 1 (`mi_vistara`), executed 2026-09-05T14:10Z

`run_id=e45e343b-f9cd-4167-aeb5-061cab5ef6b2`, execution `brahma-build-pipeline-job-zv9gd`,
completed in 18.29s. Job log: `[mi_vistara] export ledger ready — 0 existing export records` →
`[orchestrator] asset mi_vistara complete — 0 rows`. `asset_throughput.state='lit'`,
`rows_written=0`. First `mi_*` `asset_provenance_receipts` row in the campaign
(`receipt_state='unknown'`, honestly — see caveat below). Snapshot: `cloudsql-backup:1788617073802`.
Full account: #1713 (SLOT CLAIM/RELEASE comments), `L5_STATE.md` heartbeat. **W5 not yet done —
awaiting a fresh-context verifier.**

## What the capsule may and may not claim

**May:** the build executed; `rows_inserted = 0`; the existence assertion passed; `state='lit'` is
**earned**, not assumed — `asset_runner.py:1026-1032`'s `zero_rows_is_complete` is satisfied on
*both* limbs (`chart_id IS NULL` **and** `target_floor = 0`); the first `mi_*` provenance receipt
was captured.

**Must NOT claim, and this sentence ships with it:** that `integrity_check_sql` verified anything
about content. `mimamsa_export_log` holds 0 rows, so its disclosure-present gate **passes
vacuously** — it constrains every future export and attests nothing today. A capsule reporting
that pass without this caveat is exactly the §N.8 defect the campaign exists to prevent.

## C13 statement (charter requirement, now measured)

`mi_vistara` writes `mimamsa_export_log`. **Cascade children: none. No-FK referrers: none. Live
rows: 0.** Its blast radius is empty in both directions — verified by the closure over all 27 L5
write-target tables, not assumed from its emptiness. It is the safest possible first dispatch in
the campaign, which is a second reason it is canary 1.

## Canaries 2 and 3

- **`lel_events`** — `static` route, `source_accepted` disposition. **Not dispatchable by the wave
  dispatcher at all** (it selects `execution_obligation == 'build'`; this asset is
  `source_acceptance`). Terminal evidence is a reconciliation + clear-protection proof, not an
  execution. **Zero precedent events in campaign history**, so expect it to surface something.
- **`mi_jivanaghatana`** — `changed`. Runs only after its W3 registry corrections land (migration
  690), because its `expected_volume_formula` is currently wrong on three counts and its capsule
  would otherwise assert a volume expectation that is false.
