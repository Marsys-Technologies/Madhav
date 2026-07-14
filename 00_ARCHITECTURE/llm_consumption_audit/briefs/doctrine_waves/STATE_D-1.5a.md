---
artifact: STATE_D-1.5a
type: WAVE STATE LEDGER (CONDUCTOR_PROTOCOL §6.1)
---

```yaml
wave: D-1.5a
lifecycle_step: 2   # 1=OPEN done, now SPAWN
brief_bound: true
binder_annotations:
  - "A2 narrows: bo_laksana vichara-lookup wiring pre-landed (2026-07-14); A2 = aspect_parashari ingestion + heuristic retirement + stale-comment reconciliation only"
  - "register_p1_ganita.ts anchor path corrected: platform-mcp/src/tools/register_p1_ganita.ts:636 (not platform/src/lib/retrieval/registry/layers/)"
  - "§8.7 health-check row counts are ayanamsha-scoped: canonical chart_facts=27,554 is per-ayanamsha; raw per-chart totals (~136k) are ~5x that (5 ayanamshas) — do not false-positive on raw totals"
rollback_pin:
  image_sha: "4bebb622658c3f3bf6918e74150cc78e3dabf620"
  images:
    amjis-web: "asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-web:4bebb622658c3f3bf6918e74150cc78e3dabf620"
    amjis-mcp: "asia-south1-docker.pkg.dev/madhav-astrology/amjis/amjis-mcp:4bebb622658c3f3bf6918e74150cc78e3dabf620"
    brahma-pipeline: "asia-south1-docker.pkg.dev/madhav-astrology/amjis/brahma-pipeline:4bebb622658c3f3bf6918e74150cc78e3dabf620"
  build_ids:
    "482012f1-710e-4a25-994a-93821f5871aa": "b97b6eb0-0166-4ed6-ad94-9af9423b9e65"   # Abhisek
    "1c826d5a-41cb-4450-b4dc-59d440e5f75a": "3a3682db-5434-4eca-8148-2c706c80380d"   # Abhinandan
canonical_baseline_reproduced: true   # B-2: reds #1-5,#7-9,#11; greens #10,#12; #6 split — all confirmed live
lanes:
  - {lane: A-0, branch: wave/D-1.5a/A-0, status: pending, receipt_ref: null}
  - {lane: A-alpha, branch: wave/D-1.5a/A-alpha, status: pending, receipt_ref: null}
  - {lane: A-beta, branch: wave/D-1.5a/A-beta, status: pending, receipt_ref: null}
  - {lane: A-gamma, branch: wave/D-1.5a/A-gamma, status: pending, receipt_ref: null}
deploy: {done: false, sha: null}
rebuild:
  "482012f1-710e-4a25-994a-93821f5871aa": pending
  "1c826d5a-41cb-4450-b4dc-59d440e5f75a": pending
gate: {run: false, green: [], red: []}
updated_at: "2026-07-15 (session open, post-Binder)"
```
