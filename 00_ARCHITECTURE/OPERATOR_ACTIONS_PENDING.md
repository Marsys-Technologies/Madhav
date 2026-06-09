---
artifact: OPERATOR_ACTIONS_PENDING.md
version: "1.4"
status: LIVING
produced_during: DOC_CLEANUP_2026-05-31
role: Single source of truth for all operator actions requiring human execution (GCP console, production DB, GitHub settings).
changelog:
  - v1.0 (2026-05-31, CI-cleanup): Initial file — smoke gate secrets provisioning only.
  - v1.1 (2026-05-31, DOC_CLEANUP): Consolidated all pending operator actions from MULTI_AYANAMSHA_BUILD_CLOSE §6, MCPT_CLOSE, PLATFORM_MODERNIZATION_CLOSE, and CI-cleanup session.
  - v1.2 (2026-06-01, PYJHORA-POSTMERGE-DEPLOY-B): A.1 chart build marked DONE; A.2 migrations 121/122/124 UNBLOCKED; A.3 build-trigger 401 HIGH item added; A.4 forensic render HIGH item added; A.5 jh-parity residue MEDIUM item added.
  - v1.3 (2026-06-08, pipeline-audit-closeout): Added HIGH item for iac-apply.yml GCS state bucket IAM (GATE 2 infra-blocked finding). Noted PA-01 flags baked and GATE 1 passed.
  - v1.4 (2026-06-09, L1-wipe): L1 Gaṇita data wipe executed (brief L1_DATA_WIPE_BRIEF v1.0). Added CRITICAL item 1b (14 absent tables = 13 l1_* + chart_facts confirmed missing from prod; build prerequisite before Brahma L1 build). chart_panchanga_cache pre/post: 91→0; all 6 existing tables now at 0 rows; backup pre-L1-wipe-20260609 confirmed in Cloud SQL.
---

# Operator Actions Pending

Last updated: 2026-06-09
Single source of truth for all operator actions that require human execution
(GCP console, production DB, GitHub settings). Updated at each session close.

---

## CRITICAL — Multi-Ayanamsha Build (blocks M6-A-S1 opening)

These must complete before M6-A-S1 can open. CURRENT_STATE v5.65 confirms
they are still pending.

Source: `00_ARCHITECTURE/MULTI_AYANAMSHA_BUILD_CLOSE_v1_0.md §6`

### 1. Apply migrations 140–153 to production DB (in order)

```
platform/migrations/140_sarvatobhadra_chakra.sql
platform/migrations/141_supplementary_chakras.sql
platform/migrations/142_bhrigu_bindu_transits.sql
platform/migrations/143_graha_aspects_lifetime.sql
platform/migrations/144_vedha_extended.sql
platform/migrations/145_time_synchronicity.sql
platform/migrations/146_phase_locked_anchors.sql
platform/migrations/147_varsha_digest.sql
platform/migrations/148_tajik_varsha_year_lords.sql
platform/migrations/149_utee_envelope_columns.sql
platform/migrations/150_vedha_anchor_interactions.sql
platform/migrations/151_temporal_unified_lattice_view.sql
platform/migrations/152_chart_lattice_mv.sql
platform/migrations/153_meta_beta_gamma_delta_epsilon.sql
```

Apply using psql or Cloud SQL proxy:
```bash
psql $DB_URL -f platform/migrations/140_sarvatobhadra_chakra.sql
# ... repeat for 141 through 153 in order
```

### 1b. ⚠️ BRAHMA L1 BUILD PREREQUISITE — 14 tables absent from prod (confirmed 2026-06-09)

L1 wipe execution (brief `L1_DATA_WIPE_BRIEF v1.0`, 2026-06-09) cross-checked the §2 kill
list against live prod schema. **14 of 19 target tables do not exist on prod:**

**13 `l1_*` tables (require migrations 140–153 from item 1 above):**
`l1_sarvatobhadra_positions`, `l1_sarvatobhadra_vedha`, `l1_vedha_extended`,
`l1_bhrigu_bindu_transits`, `l1_graha_aspects_lifetime`, `l1_time_synchronicity`,
`l1_phase_locked_anchors`, `l1_varsha_digest`, `l1_tajik_varsha_year_lords`,
`l1_kota_chakra`, `l1_kalanala_chakra`, `l1_ckn_chakra`, `l1_sapta_shalaka`

**`chart_facts` — absent (unexpected):**
Was reported populated (65 cells, 2026-06-01 native build) but does not appear in
`pg_tables` as of this check. Either the table was dropped, or the proxy resolves a
different DB instance than the one where the build ran. Verify before the Brahma L1 build:

```sql
-- Must return 1 row (not 0) and not error:
SELECT count(*) FROM pg_tables WHERE schemaname = 'public' AND tablename = 'chart_facts';
-- If present, check row count:
SELECT count(*) FROM chart_facts;
```

If absent: identify the migration that creates `chart_facts` and apply it before any L1
writer runs. The 13 `l1_*` tables are gated on migrations 140–153 (item 1 above).

**The Brahma L1 build cannot run its writers until all 14 tables exist on prod.**
The 5 existing Gaṇita tables (`ganita_positions`, `ganita_graha_sthana`, `ganita_dashas`,
`chart_divisionals`, `chart_panchanga`) are at 0 rows and schema-intact — no action needed
on those. `chart_panchanga_cache` was wiped: 91 rows → 0 (will rebuild from panchanga data).

---

### 2. Trigger native chart build — ✅ DONE 2026-06-01

Native chart `362f9f17-95a5-490b-a5a7-027d3e0efda0` built via `marsys-build-pipeline-job`
(build_id `a494ec15`) on the PyJHora engine (`amjis-sidecar-00511-pz7`). All 65
`(category × ayanamsha_id)` cells non-zero in `chart_facts`. Panchanga FORENSIC
spot-check 5/5. **NOTE:** triggered job-direct because the Cloud Tasks → `/api/build/task`
path 401'd (see new HIGH item below). `forensic` asset is still a 0-row stub (Stream F).

### 3. ACC1 — Run answer:eval after build job completes

```bash
python platform/scripts/answer_eval/run_eval.py
```

Run only after step 2 (chart build) has populated the native chart's facts.

### 4. ACC3 — Execute IS.8(b) red-team (native chart, post-build)

Execute per `00_ARCHITECTURE/RED_TEAM_MULTI_AYANAMSHA_BUILD_v1_0.md`.
Requires native participation — not fully automatable.

### 5. ACC4 + ACC5 — Run smoke tests post-deploy

**ACC4** (multi-tenant smoke):
```bash
pytest platform/tests/integration/test_multi_tenant_smoke.py --db-url=$DB_URL
```

**ACC5** (concurrent smoke — Cloud environment only):
Run concurrent smoke test manually in Cloud environment per the artifact's §4.

---

## HIGH — iac-apply.yml: GCS state bucket IAM not provisioned (GATE 2 infra-block)

The new dispatch-only `iac-apply.yml` workflow (merged 2026-06-08, commit `7c8d6621`) runs
`terraform plan`/`apply` against the `cloud_scheduler` Terraform module. On first run
(workflow run `27104108901`), Terraform failed at backend init:

```
Error 403: github-actions@madhav-astrology.iam.gserviceaccount.com does not have
storage.objects.list access to the Google Cloud Storage bucket.
Permission 'storage.objects.list' denied on resource
'//storage.googleapis.com/projects/_/buckets/madhav-astrology-tf-state'
```

**Required action (GCP console or gcloud):**

```bash
# Option 1: Grant objectAdmin on the TF state bucket to the GHA SA
gcloud storage buckets add-iam-policy-binding gs://madhav-astrology-tf-state \
  --member="serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

# Option 2 (narrower): Grant only the required operations
gcloud storage buckets add-iam-policy-binding gs://madhav-astrology-tf-state \
  --member="serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
gcloud storage buckets add-iam-policy-binding gs://madhav-astrology-tf-state \
  --member="serviceAccount:github-actions@madhav-astrology.iam.gserviceaccount.com" \
  --role="roles/storage.objectCreator"
```

If the bucket does not exist yet, create it first:
```bash
gcloud storage buckets create gs://madhav-astrology-tf-state \
  --project=madhav-astrology --location=asia-south1
```

After granting access, re-run GATE 2:
```bash
gh workflow run iac-apply.yml -f module=cloud_scheduler -f action=plan --ref main
```
Inspect the plan output. If ANY destroy/replace → do not apply; investigate before
proceeding. If plan shows only add/update → GATE 2 is clear to apply.

---

## HIGH — Build trigger path broken (Cloud Tasks → /api/build/task 401)

The autonomous build trigger 401s in production; native build was run job-direct as a
workaround. S1 OIDC fix (Design A queue-header auth) has been deployed to `amjis-web`
(`amjis-web-00494-jjd`). **STATUS: DEPLOYED — end-to-end smoke (Cloud Tasks → /api/build/task
→ job enqueue) not yet verified in production.** Fix brief:
`00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_BUILD_TASK_OIDC_401_FIX_v1_0.md`.
Likely cause: `amjis-web` is private, so Cloud Run strips the OIDC `Authorization` header
before the app's bearer parse — app should authorise on `X-CloudTasks-*` headers under
IAM (Design A). Operator IAM/env actions listed in the brief.

### Hygiene — remove BUILD_TASK_AUTH_BYPASS from amjis-web

The var grants nothing (code-neutralised + regression-tested) but trips a SECURITY log
alert. Remove it:
```bash
gcloud run services update amjis-web --region asia-south1 --project madhav-astrology \
  --remove-env-vars BUILD_TASK_AUTH_BYPASS
```

---

## HIGH — Forensic render still a stub (Stream F)

`forensic_writer.py` returns 0 rows. The PyJHora arc swapped the engine but did NOT
deliver the forensic (A2 Pratyaksha) render — its named primary target. Scoping brief:
`00_ARCHITECTURE/BRIEFS/STREAM_F_FORENSIC_RENDER_SCOPING_v1_0.md` (needs native decisions
Q1/Q3 before it becomes an executor brief).

---

## HIGH — MCP Transformation migrations 072–080

Status: **UNCONFIRMED** in governance docs after CLOSEOUT-2026-05-22.
Verify against production DB schema before applying; they may already be present.

Source: `00_ARCHITECTURE/MCPT_CLOSE_v1_0.md`

```
platform/supabase/migrations/072_mcp_bundle_cache.sql
platform/supabase/migrations/073_perf_log_extensions.sql
platform/supabase/migrations/074_audit_findings.sql
platform/supabase/migrations/075_prediction_outcomes.sql
platform/supabase/migrations/075b_prediction_outcomes_remediation.sql
platform/supabase/migrations/076_data_source_expected_and_caveats.sql
platform/supabase/migrations/077_mcp_alerts_config_and_tool_registry.sql
platform/supabase/migrations/078_multi_school_extensions.sql
platform/supabase/migrations/079_tajaka_and_convergence.sql
platform/supabase/migrations/080_classical_texts_work_column.sql
```

Verification before applying:
```sql
SELECT table_name FROM information_schema.tables
WHERE table_name IN (
  'mcp_bundle_cache', 'mcp_audit_findings', 'mcp_predictions',
  'data_source_expected', 'multi_school_stances', 'school_convergence_index'
);
```
If these tables exist, migrations are already applied — skip.

---

## MEDIUM — Platform Modernization residuals (v1.3 queue, BLOCKED)

Source: `CLAUDE.md §E Platform Modernization` + `00_ARCHITECTURE/PLATFORM_MODERNIZATION_CLOSE_v1_0.md`

### Migrations 121/122/124 — partition scaffolding

**UNBLOCKED 2026-06-01.** The native build wrote real per-`chart_id` rows to
`chart_facts`. The `chart_id`-100%-NULL precondition is cleared. Migrations 121/122/124
(`query_trace_steps` partitions) may now apply. Still a separate gated operator step —
verify `chart_id` non-NULL coverage on the target tables before applying.

```
platform/migrations/121_*.sql
platform/migrations/122_*.sql
platform/migrations/124_*.sql
```

### R1+R2 — Monitoring alerts and SLO configuration

**BLOCKED on log-based metrics + amjis-web monitoring registration.**

```bash
# Apply monitoring dashboards (Cloud Run must be deployed first):
gcloud monitoring dashboards create \
  --config-from-file=infra/monitoring/<dashboard>.json
```

Apply per `00_ARCHITECTURE/PLATFORM_MODERNIZATION_CLOSE_v1_0.md §8` IaC apply.sh.

---

## MEDIUM — jh-parity residue in platform/ code paths

PR #184 AC4/AC5 greps were scoped to python-sidecar/ only; residue remains in
`platform/scripts/hard_gates_check.sh` (G2 gate rewards jh_oracle.json), `acc2_hard_gates.json`,
`engine/current/route.ts` (`jh_parity_sha`), and a committed `_scratch/` file. Cleanup brief:
`00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_JH_PARITY_RESIDUE_CLEANUP_v1_0.md`.

---

## LOW — GitHub Actions smoke gate secrets

Provision `SMOKE_SESSION_COOKIE` + `SMOKE_CHART_ID` as GitHub Actions secrets.
Until provisioned, the chat-v2-smoke workflow exits 0 vacuously (no protection).

**Required actions (human, GCP/GitHub console):**

1. Mint a long-lived session cookie for the smoke test user:
   ```bash
   cd /Users/Dev/Vibe-Coding/Apps/Madhav/platform
   npx tsx scripts/mint_session_cookie.ts --uid <SMOKE_USER_UID> --chart-id 362f9f17-95a5-490b-a5a7-027d3e0efda0
   ```
   Copy the output `__session` cookie value.

2. In GitHub → repo Settings → Secrets → Actions, add:
   - `SMOKE_SESSION_COOKIE` = the __session cookie value from step 1
   - `SMOKE_CHART_ID` = 362f9f17-95a5-490b-a5a7-027d3e0efda0

3. In GitHub → repo Settings → Branches → main branch protection rule, add
   `chat-v2 smoke / smoke` as a required status check.

4. Rotate the session cookie every 90 days (it expires with Firebase session lifetime).

---

## Completed (archive)

- **2026-05-21**: Migrations 069 applied (panchanga_daily enrichment columns). Phase 4C close.
- **2026-05-22**: MCP v1 migrations 070–071 applied (mcp_api_keys, mcp_predictions_disagreements).
- **2026-05-23**: R9 migrations 110/111/112 applied; R9 flags flipped (PROJECTS, SEMANTIC_SEARCH, TOOL_FLOW).
- **2026-05-26**: GISMCP sidecar deployed (amjis-mcp-00017-6nl). MARSYS_REPO_ROOT=/app set on amjis-web.
- **2026-05-31**: schema_validator CI gate hardened (continue-on-error removed). SESSION_LOG entries repaired.
- **2026-06-08**: Pipeline Audit PA-01/04/05/06/07/08 completed (PRs #217 + #218). GATE 1 PASSED — all 5 NEXT_PUBLIC flags (`R9_PROJECTS`, `R9_SEMANTIC_SEARCH`, `R9_TOOL_FLOW`, `R11B_LOOK_AND_FEEL`, `R11V2_MULTI_PROVIDER_PARITY`) baked in revision `amjis-web-00536-6hg`. Terraform decoupled from auto-deploy (PA-06). GATE 2 infra-blocked (see HIGH section above).
