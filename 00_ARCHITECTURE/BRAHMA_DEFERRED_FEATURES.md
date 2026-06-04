---
artifact: BRAHMA_DEFERRED_FEATURES.md
canonical_id: BRAHMA_DEFERRED_FEATURES
version: 1.0
status: LIVING (rolling list — features intentionally deferred during Brahma cleanup; rebuild plan per item)
project_codename: Brahma
authored_by: Claude (Cowork) 2026-06-04
purpose: >
  Record of features that existed in the pre-Brahma codebase, were intentionally removed during
  Brahma cleanup (WS-0 / WS-0B / hot-patches), and are scheduled for proper rebuild under a
  Brahma-native layer rather than restoration of the legacy implementation. Distinguishes
  "deferred" from "lost" — the surface is gone, the requirement is not.
---

# Brahma — Deferred Features

## 1. AIOps LLM-quality observability (model health probes + admin surface)

**Removed:** 2026-06-04, WS-0B hot-patch, Option A-extended.

**What it was.** Per-model health probing (`platform/src/lib/aiops/health/prober.ts` +
`bulk.ts`) writing latency, error, last-probe timestamps to `llm_model_health`; a cron
script (`platform/scripts/aiops/probe_health_cron.ts`) intended to run on a regular
cadence; three admin routes reading the table (`/api/admin/aiops/health`,
`/health/summary`, `/state`); UI components surfacing per-stack health
(`StackPickerCards`, `HealthPip`).

**Why removed.** WS-0 dropped `llm_model_health` as part of the AIOps-stack purge. The
admin surface was silently broken for hours with no observable failure — confirming it
was not on any daily-driven path. gcloud scheduler + gcloud run jobs both confirmed no
live external cron trigger. Restoring the legacy table would re-introduce exactly the
dead-code-on-living-table pattern WS-0/WS-0B were cleaning up. Surface deleted in full
instead of stubbed. WS-0B reverse-citation gate confirmed full blast radius: 5 originally-
known files + cron script + batch wrapper + route test + 2 UI components.

**Where it goes.** When Mīmāṃsā/L5 (Learning) is built, the LLM-quality calibration
concern is a natural fit: track per-model behaviour against outcomes the same way the
corpus-level learning multiplier tracks rules/signals/techniques. The rebuild lives under
`mimamsa_*` tables + Brahma-native tools, not a port of the legacy admin surface.

**Rebuild trigger.** When Mīmāṃsā work begins (per BRAHMA_COMPLETION_PLAN WS-3 +
downstream L5 implementation), spec LLM-health observability as a Mīmāṃsā sub-asset.
Do not rebuild it as a standalone admin tool.
