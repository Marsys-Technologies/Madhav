# Build Orchestrator — Operator + Developer Guide

## Overview

The MARSYS-JIS Multi-Ayanamsha Deterministic Build Orchestrator populates per-chart deterministic assets
across 22 asset types (A1-A22) × 5 ayanamshas, plus 6 META synthesis layers.

## How to Trigger a Chart Build

### 1. Start a build via API

```bash
curl -X POST https://amjis-web-<revision>.a.run.app/api/build/start \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SESSION_TOKEN" \
  -d '{"chart_id": "<chart-uuid>", "ayanamshas": ["lahiri","true_chitra","krishnamurti","raman","yukteshwar"]}'
```

### 2. The system queues build tasks via Cloud Tasks → Cloud Run Job

Response includes `build_id`. Monitor progress via `/admin/tracker`.

### 3. Monitor build progress

- Visit `/admin/tracker` in the web app
- Check `builds` table in PostgreSQL: `SELECT * FROM builds WHERE id = '<build_id>';`
- Check `build_events` table for step-by-step progress

## Build Pipeline Architecture

```
/api/build/start (Next.js API route)
  → Cloud Tasks queue (amjis-build-queue)
    → /api/build/task (per-ayanamsha task)
      → Cloud Run Job (marsys-build-pipeline-job)
        → build_chart.py --chart-id <id> --ayanamsha <name>
          → 22 asset writers (sequential, dependency-ordered)
          → 6 META synthesis writers
          → chart_facts population
```

## Asset Writers (Build Order)

| Asset | Table | Description |
|---|---|---|
| A1 | chart_facts | FORENSIC natal chart facts |
| A2 | chart_facts | Raw chart data from FORENSIC_ASTROLOGICAL_DATA |
| A3-A5 | chart_facts | L2.5 synthesis (MSR, CDLM, CGM, RM) |
| A6 | chart_facts | Varga positions (30+ vargas) |
| A7 | chart_dashas | 7 dasha systems |
| A8 | chart_facts | T1 structural yogas/doshas/strengths |
| A9 | chart_facts | Sade Sati phases |
| A10 | l25_msr_signals | MSR signal computation |
| A11 | l25_cdlm_cells | CDLM domain linkage |
| A12 | l25_cgm_nodes/edges | CGM motif graph |
| A13 | chart_facts | RM remedy bundles |
| A15 | l1_time_synchronicity | Time-synchronicity convergence windows |
| A16 | l1_phase_locked_anchors | Phase-locked prediction anchors |
| A17 | l1_sarvatobhadra_* | Sarvatobhadra Chakra |
| A18 | l1_vedha_extended | Extended vedha (6 systems) |
| A19 | l1_bhrigu_bindu_transits | Bhrigu Bindu lifetime transits |
| A20 | l1_tajik_varsha_year_lords | Tajik Hadda + Muntha year lords |
| A21 | l1_graha_aspects_lifetime | Next-exact-aspect per graha |
| A22 | l1_varsha_digest | Per-varsha yearly digest |
| META-α | l25_chart_lattice_snapshots | Structural timeline lattice |
| META-β | l25_pattern_catalog | Unified pattern catalog |
| META-γ | l25_divergence_ledger | Cross-system divergence audit |
| META-δ | l25_negative_space_map | Absence-as-feature map |
| META-ε | l25_derivation_graph_nodes/edges | L1→L2.5 derivation DAG |
| META-ζ | vw_temporal_unified_lattice | Temporal unified lattice view |

## Monitoring Builds

### Via tracker dashboard

Navigate to `/admin/tracker` in the web app.

### Via PostgreSQL

```sql
-- Build status
SELECT id, chart_id, status, created_at FROM builds ORDER BY created_at DESC LIMIT 10;

-- Build steps
SELECT step_name, status, completed_at FROM build_steps WHERE build_id = '<id>' ORDER BY created_at;

-- chart_facts count per ayanamsha
SELECT ayanamsha_id, count(*) FROM chart_facts WHERE chart_id = '<id>' GROUP BY ayanamsha_id;
```

### Via Cloud Run logs

```bash
gcloud run jobs executions list --job=marsys-build-pipeline-job --region=asia-south1 --limit=10
```

## Troubleshooting

### Build stuck in "dispatched" state

Check Cloud Tasks queue:

```bash
gcloud tasks list --queue=amjis-build-queue --location=asia-south1
```

### Cloud Run Job failing immediately

Check DB_URL secret:

```bash
gcloud secrets versions access latest --secret=amjis-pipeline-db-url
```

### Wrong ayanamsha data returned

Verify `ayanamsha_id` filter in all queries — every query must include `AND ayanamsha_id = '<name>'`.

### Stale build data

Run: `SELECT * FROM builds WHERE chart_id = '<id>' ORDER BY created_at DESC LIMIT 5;`
Latest `build_id` with status='complete' is authoritative. Older builds are superseded.

## Migrations (apply to production after each stream merge)

| Migration | File | Description |
|---|---|---|
| 139 | 139_g29_timing_rules.sql | Classical Timing Rules |
| 140 | 140_sarvatobhadra_chakra.sql | SBC chakra |
| 141 | 141_supplementary_chakras.sql | Sapta-Shalaka + Kalanala + Kota + CKN |
| 142 | 142_bhrigu_bindu_transits.sql | A19 Bhrigu Bindu |
| 143 | 143_graha_aspects_lifetime.sql | A21 exact aspects |
| 144 | 144_vedha_extended.sql | A18 extended vedha |
| 145 | 145_time_synchronicity.sql | A15 time-synchronicity |
| 146 | 146_phase_locked_anchors.sql | A16 phase-locked anchors |
| 147 | 147_varsha_digest.sql | A22 per-varsha digest |
| 148 | 148_tajik_varsha_year_lords.sql | A20 Tajik Hadda |
| 149 | 149_utee_envelope_columns.sql | UTEE columns on 7 tables |
| 150 | 150_vedha_anchor_interactions.sql | BRIDGE vedha-anchor table |
| 151 | 151_temporal_unified_lattice_view.sql | META-ζ view |
| 152 | 152_chart_lattice_mv.sql | META-α lattice snapshots |
| 153 | 153_meta_beta_gamma_delta_epsilon.sql | META-β/γ/δ/ε tables |

Apply in order: `psql $DB_URL -f platform/migrations/<file>.sql`
