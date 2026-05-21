---
gate: HUMAN_GATE_B
packet: B
blocking: false
emitted_at: 2026-05-21
status: AWAITING_OPERATOR
---

# Operator Gate B — Post-Merge Operator Actions

These actions require human execution. The orchestrator has continued past this gate
(it is **non-blocking**). Complete these when convenient; they are not required for the
governance hygiene PRs (C, D, E.2) to proceed.

---

## B.1 — Enable R8 feature flags in Cloud Run

The R8 capability-round flags are currently unset in production. Enable them with:

```bash
gcloud run services update amjis-web \
  --region asia-south1 \
  --update-env-vars \
    MARSYS_FLAG_R8_SLASH_ENABLED=true,\
    MARSYS_FLAG_R8_EXPORT_ENABLED=true,\
    MARSYS_FLAG_R8_TOKENS_ENABLED=true
```

## B.2 — Browser smoke: slash / export / tokens (after B.1)

After flipping R8 flags, open the chat UI and verify:
- `/` key in composer opens the slash command menu
- Export conversation button appears and produces a downloadable file
- Token estimate is visible in the composer footer

## B.3 — Trigger a fresh Cloud Build

This ensures the latest `main` (including PR #112 + PR #113 merges) deploys cleanly:

```bash
gcloud builds submit --config=platform/cloudbuild.yaml platform/
```

Monitor for a successful build + Cloud Run revision promotion.

## B.4 — Browser smoke: scroll discipline + validator failure bands (after B.3)

After the new revision goes live:
- Scroll the chat — verify scroll discipline (messages stay in view; no jump-to-bottom jank)
- Trigger a validator failure (e.g., submit a query with an invalid date range) and confirm
  the failure band renders correctly

## B.5 — Panchang bootstrap audit (from Phase 4C open follow-up)

The Phase 4C close-out documented an open follow-up:

> "audit `bootstrap_panchanga.py` build_manifests auto-registration (prior build needed manual
> rollback because the bootstrap writer didn't auto-register a build_manifests row)"

Current state: `panchanga_daily` is populated with 73,414 rows under
`build_id = phase-4c-enrich-20260521-r2` (production-live and correct). The follow-up
is to add auto-registration to the bootstrap script so future re-runs don't require
manual rollback. This is a **code change task** — it is not urgent and does not affect
the current live data.

---

## Checklist

- [ ] B.1 — R8 flags enabled in Cloud Run
- [ ] B.2 — Browser smoke: slash / export / tokens
- [ ] B.3 — Fresh Cloud Build submitted + revision promoted
- [ ] B.4 — Browser smoke: scroll discipline + validator bands
- [ ] B.5 — bootstrap_panchanga.py auto-registration audit (non-urgent)
