# Operator Actions Pending

Last updated: 2026-05-31
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

### 2. Trigger native chart build (Cloud Run Job build_chart.py)

Chart ID: `362f9f17-95a5-490b-a5a7-027d3e0efda0`

```bash
# Via API endpoint (post-deploy):
curl -X POST https://<amjis-web-url>/api/build/start \
  -H "Authorization: Bearer $OPERATOR_TOKEN" \
  -d '{"chart_id": "362f9f17-95a5-490b-a5a7-027d3e0efda0"}'
```

This populates `chart_facts` for all ayanamshas. Must complete before ACC1.

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

**BLOCKED on `chart_id` 100% NULL in partition key column.**
Do NOT attempt until the Multi-Ayanamsha chart build (CRITICAL §2 above) has
written per-chart rows to `chart_facts`. The chart_id column must be non-null
before partition migration can succeed.

After chart build:
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
