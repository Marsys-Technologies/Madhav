---
artifact: CP5_CUTOVER_REPORT_v1_0.md
status: PENDING_LIVE_RUN
authored_at: 2026-05-13
session_id: AIOPS_CP_5
---

# CP.5 Cutover Report

> **Status:** Smoke rows will be populated on first live `npm run aiops:cutover-smoke` run.
> The report schema, tooling, and all flags-off / flags-on rows auto-append to
> `platform/scripts/aiops/cutover_smoke_report.json`. Update §1 and §4 from that output.

---

## §1 — Smoke test summary

| Run | Pass | Total | Notes |
|---|---|---|---|
| Flag-off (`AIOPS_OVERRIDES_ENABLED=false`) | — | — | Populate from `npm run aiops:cutover-smoke` |
| Flag-on  (`AIOPS_OVERRIDES_ENABLED=true`)  | — | — | Populate from `npm run aiops:cutover-smoke` |

**Anthropic rows:** Expected `auth_fail` / `skipped_auth` if Anthropic API key not configured — not blocking.

---

## §2 — Catalog freshness (per provider)

Populate by running `GET /api/admin/aiops/catalog/<provider>` for each:

| Provider | Last fetch | Model count |
|---|---|---|
| NIM (nvidia) | — | — |
| Gemini (google) | — | — |
| DeepSeek | — | — |
| GPT (openai) | — | — |
| Anthropic | — | — |

---

## §3 — Override surface

Rows where the DB override differs from the registry default are listed here after running
`GET /api/admin/aiops/audit?limit=100` on the live DB. Populate locally.

*(No overrides seeded by Claude Code — all will be registry defaults at cutover time unless native has applied overrides via the Control Panel during acceptance testing.)*

---

## §4 — Health table snapshot

Populate by running `GET /api/admin/aiops/health` on the live DB after at least one `npm run aiops:health` cron run.

| model_id | status | latency_ms | last_probe_at |
|---|---|---|---|
| *(populate from live health endpoint)* | | | |

---

## §5 — Outstanding risks

- **Anthropic auth_fail:** Expected if no Anthropic API key configured. Not blocking for Phase 1 (Anthropic stack is opt-in behind cost-confirm dialog).
- **Live run required:** §1, §4 cannot be populated by Claude Code without a live DB + provider credentials. This is the native's responsibility during acceptance.
- **Schema match:** `llm_model_health`, `llm_config_audit`, `llm_stack_config`, `llm_stack_routing_override`, `llm_param_override`, `llm_catalog_snapshot` — all created by migrations 046–052 authored in CP.1. Confirm migrations ran before populating this report.
