---
artifact: OPERATOR_BRIEF_PYJHORA_POSTMERGE_v1_0.md
brief_id: PYJHORA_POSTMERGE
version: 1.0
status: READY
authored_at: 2026-06-01
authored_by: cowork-planner
authority: native_decision_2026-06-01
follows: CLAUDECODE_BRIEF_PYJHORA_IMPLEMENTATION_v1_0.md (PR #184)
audience: the native (operator) — human-gated actions only
surface: operator runs these by hand. NOT an Antigravity executor brief. No code edits here.
preconditions:
  - PR #184 (feature/pyjhora-direct-engine) MERGED to main
gates_crossed_by_operator:
  - production deploy (amjis-sidecar)
  - production build trigger (native chart)
  - production DB read (verification only — no writes)
hard_bans:
  - No schema migration in this step (121/122/124 are a SEPARATE later step, see §6)
  - No flag flip beyond confirming BUILD_TRIGGER_ENABLED (see §3)
---

# PyJHora post-merge — operator runbook

The PR is the code change. **The sidecar still runs the old image with `natal_engine/`
baked in until you roll a new `amjis-sidecar` revision.** PyJHora 4.8.6 is a *runtime
dependency* change (new pip package + Dockerfile), so a rebuild-and-deploy is mandatory —
code-on-main alone does nothing for the running engine.

Do these in order. Halt and inspect at any non-green step.

## 0 · Preconditions (confirm before starting)

- [ ] PR #184 is **merged to main**. `git log --oneline -1 origin/main` shows the squash/merge commit.
- [ ] Main is green in CI (the `build-check` PR job and any post-merge build).
- [ ] You have `gcloud` auth for project `madhav-astrology` (region `asia-south1`).

## 1 · Deploy the sidecar from main

Two ways. Prefer the workflow (it builds from the right context with the right runtime SA).

**Option A — GitHub Actions (recommended).** The `deploy-sidecar` job builds
`./platform/python-sidecar` (`Dockerfile` in that dir), pushes
`asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-sidecar:<sha>` + `:latest`, and
deploys service `amjis-sidecar` with `--timeout=300 --cpu=2 --memory=1Gi
--min-instances=1 --service-account=amjis-sidecar-runtime@madhav-astrology.iam.gserviceaccount.com`.

```bash
# trigger the deploy workflow against main (workflow_dispatch is enabled)
gh workflow run deploy.yml --ref main
gh run watch   # follow to completion; confirm deploy-sidecar is green
```

**Option B — direct (only if the workflow is unavailable).** Build from the sidecar
context so PyJHora + the Dockerfile changes are in the image:

```bash
SHA=$(git rev-parse --short origin/main)
gcloud builds submit ./platform/python-sidecar \
  --tag asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-sidecar:$SHA \
  --project madhav-astrology
gcloud run deploy amjis-sidecar \
  --image asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-sidecar:$SHA \
  --region asia-south1 --project madhav-astrology \
  --timeout=300 --cpu=2 --memory=1Gi --min-instances=1 \
  --service-account=amjis-sidecar-runtime@madhav-astrology.iam.gserviceaccount.com
```

## 2 · Verify the new image is live (engine actually rolled)

- [ ] New revision is serving:
  ```bash
  gcloud run services describe amjis-sidecar --region asia-south1 \
    --project madhav-astrology --format='value(status.latestReadyRevisionName,status.url)'
  ```
- [ ] The running image is PyJHora, not `natal_engine`. Hit the sidecar health/version
  endpoint (or check Cloud Run logs at boot) and confirm it imports
  `jhora.panchanga.drik` cleanly under `QT_QPA_PLATFORM=offscreen`. A clean boot with
  **no PyQt6 / Qt platform errors** in the first log lines is the signal.
- [ ] No `ModuleNotFoundError: natal_engine` anywhere (there shouldn't be — it's deleted).

If the boot logs show a Qt headless failure, the deploy did not honour
`QT_QPA_PLATFORM=offscreen`. Stop — that env/Dockerfile setting needs to be confirmed in
the image before proceeding.

## 3 · Confirm the build trigger is enabled on amjis-web

`/api/build/start` is gated by `BUILD_TRIGGER_ENABLED`. If it's off, the native e2e build
returns **503 `build_trigger_disabled`** and nothing runs.

```bash
gcloud run services describe amjis-web --region asia-south1 --project madhav-astrology \
  --format='value(spec.template.spec.containers[0].env)' | tr ',' '\n' | grep -i BUILD_TRIGGER
```

- [ ] `MARSYS_FLAG_BUILD_TRIGGER_ENABLED=true` is present on `amjis-web`.
  If not, set it (this is a flag flip — your gate to authorise):
  ```bash
  gcloud run services update amjis-web --region asia-south1 --project madhav-astrology \
    --update-env-vars MARSYS_FLAG_BUILD_TRIGGER_ENABLED=true
  ```

## 4 · Run the native chart end-to-end against production

Native chart_id: **`362f9f17-95a5-490b-a5a7-027d3e0efda0`**.
Default ayanamshas apply when omitted (lahiri, true_chitra, kp, raman, surya_siddhanta).

`/api/build/start` requires an authenticated session (`getServerUser` → `__session`
cookie). Mint one, then POST:

```bash
# mint a __session cookie for an authorised user
npx tsx platform/scripts/dev/mint_session_cookie.ts   # emits __session=...

curl -X POST https://amjis-web-938361928218.asia-south1.run.app/api/build/start \
  -H 'Content-Type: application/json' \
  -H 'Cookie: __session=<minted>' \
  -d '{"chart_id":"362f9f17-95a5-490b-a5a7-027d3e0efda0"}'
```

Expected: a build id back, not 401/503/422. Then watch it to `build_complete`:

```bash
# stream build events (substitute the returned buildId)
curl -N -H 'Cookie: __session=<minted>' \
  https://amjis-web-938361928218.asia-south1.run.app/api/build/events/<buildId>
# or poll the cockpit at /clients/362f9f17-.../build and watch Yantra Chitra to all-green
```

Watch for the **build orchestrator no-watchdog** gotcha: if a build wedges, it sits in
`builds` forever. If it doesn't reach `build_complete` in a few minutes, inspect rather
than re-fire. (`build_steps.status` allows `queued/running/complete/failed/skipped` only —
a stuck row won't self-cancel.)

## 5 · Verification queries (production DB, read-only)

Start the proxy, then assert every `(asset_id × ayanamsha_id)` cell is non-zero — this is
the brief's true AC6 (Phase 7), which the PR satisfied only at contract level.

```bash
./platform/scripts/start_db_proxy.sh   # port 5433
```

```sql
-- latest build for the native chart
WITH latest AS (
  SELECT build_id
    FROM builds
   WHERE chart_id = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
   ORDER BY queued_at DESC
   LIMIT 1
)
SELECT cf.asset_id, cf.ayanamsha_id, COUNT(*) AS rows
  FROM chart_facts cf, latest
 WHERE cf.chart_id = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
   AND cf.build_id = latest.build_id
 GROUP BY cf.asset_id, cf.ayanamsha_id
 ORDER BY cf.asset_id, cf.ayanamsha_id;
```

- [ ] **Every** row has `rows > 0`. Expected shape: 28 assets × 5 ayanamshas
  (minus any asset that is legitimately single-ayanamsha; cross-check
  `00_ARCHITECTURE/PARIKSHA/EXPECTED_ROW_COUNTS.yaml`).
- [ ] **`forensic` (A1 Pratyaksha) is non-zero** — the whole point of the arc. The old
  stub returned 0 rows; the new engine must populate it.

```sql
-- explicit forensic-writer guard (the primary target asset)
SELECT ayanamsha_id, COUNT(*) FROM chart_facts
 WHERE chart_id = '362f9f17-95a5-490b-a5a7-027d3e0efda0'
   AND asset_id = 'forensic'
 GROUP BY ayanamsha_id ORDER BY 1;
```

- [ ] (Optional, matches the in-PR spot-check) Panchanga under Lahiri at the native birth
  resolves to tithi=**Shukla Tritiya**, vara=**Ravivara**, nakshatra=**Purva Bhadrapada**,
  yoga=**Shiva**, karana=**Garaja**. Treat any drift here as an engine-config signal
  (ayanamsha/tz), not a parity failure — no JH oracle.

## 6 · Downstream — auto-unblocked AFTER this run (do not do now)

The first production run writing per-`chart_id` rows into `chart_facts` is the single fact
that unblocks **Platform Modernization v1.3** — migrations **121/122/124**
(`query_trace_steps` partitions), blocked on `chart_id` being 100% NULL since 2026-05-29.

Once §5 confirms real per-chart rows are landing, those partition migrations become
applicable. **That is a separate operator step with its own gate** — `must_not_touch` here.
Queue it; don't fold it into this runbook.

## 7 · Still deferred (queue, non-blocking)

- Governance-doc cleanup of the ~40 JH-parity grep hits across `00_ARCHITECTURE/`
  (the implementation brief's F2). Separate cleanup arc.
- **In-`platform/` jh-parity code-path residue** surfaced in the PR-184 review, which the
  AC4/AC5 greps missed by scoping to `platform/python-sidecar/` only:
  `platform/scripts/hard_gates_check.sh` G2 (`G2_jh_oracle_pinned`),
  `platform/evals/acc2_hard_gates.json` G2, the `jh_parity_sha` field in
  `platform/src/app/api/engine/current/route.ts`, and the committed
  `tests/test_pyjhora_adapter/_scratch/discover_api.py`. Decide: extend F2 to cover
  `platform/`, or accept as inherited debt.

## 8 · Operator acceptance checklist

- [ ] `deploy-sidecar` green; new `amjis-sidecar` revision serving (§2)
- [ ] Sidecar boots clean headless — no Qt/PyQt6 error, no `natal_engine` import (§2)
- [ ] `BUILD_TRIGGER_ENABLED=true` on amjis-web (§3)
- [ ] Native build kicked and reached `build_complete` (§4)
- [ ] Every `(asset_id × ayanamsha_id)` has `COUNT(*) > 0` (§5)
- [ ] `forensic` asset non-zero across all ayanamshas (§5)
- [ ] (optional) Lahiri panchanga spot-check holds 5/5 (§5)
- [ ] v1.3 partition step (121/122/124) queued as a follow-on, not done here (§6)

## 9 · Rollback

Code rollback is `git revert` on main, not a flag flip (no engine flag exists — clean cut).
To roll the *running* engine back without reverting code, redeploy the prior
`amjis-sidecar` revision:

```bash
gcloud run services update-traffic amjis-sidecar --region asia-south1 \
  --project madhav-astrology --to-revisions <PRIOR_REVISION>=100
```

Note the prior revision still carries `natal_engine` and the 0-row forensic stub — rollback
restores the *old broken state*, so prefer fixing forward unless the new image fails to boot.

---

*End of OPERATOR_BRIEF_PYJHORA_POSTMERGE_v1_0.md — point-in-time 2026-06-01. Re-verify
service URLs and the BUILD_TRIGGER flag against live `gcloud` before running.*
