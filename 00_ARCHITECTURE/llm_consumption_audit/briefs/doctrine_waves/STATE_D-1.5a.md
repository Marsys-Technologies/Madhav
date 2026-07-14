---
artifact: STATE_D-1.5a
type: WAVE STATE LEDGER (CONDUCTOR_PROTOCOL §6.1)
---

```yaml
wave: D-1.5a
lifecycle_step: 3   # 1=OPEN done, 2=SPAWN done, now IMPLEMENT ∥ VERIFY
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
  - {lane: A-0, branch: wave/D-1.5a/A-0, status: receipted, receipt_ref: "verifier afbeca6133e46621e ACCEPT, diff_base 4bebb622, canonical_baseline_match EXACT, scope_warden pass", agent_id: a1d4e2a584592cf56, commit: b1b086bb}
  - {lane: A-alpha, branch: wave/D-1.5a/A-alpha, status: claimed, receipt_ref: null, agent_id: aa3b218b1e1a235db, commit: f83475df, claim: "A1: compute_valence gated on classify_actor's primary (trikona before dusthana); Jupiter 9L/12L->H2 now benefic not strong_malefic. A2: aspect_parashari + aspect_parashari_per_varga wired into VicharaFactIndex (were dead-on-arrival, fact_subject never read into tags); heuristic retired for lord-link+aspect populations, kept honestly for Rahu/Ketu (no lordship = no fabricated row per B.10). 6 stale comments reconciled (brief cited 3). 23 vichara tests pass (was 19); full suite 3322 passed/0 failed"}
  - {lane: A-beta, branch: wave/D-1.5a/A-beta, status: claimed, receipt_ref: null, agent_id: ac262d840c1f3aaa1, commit: f10a7b70, claim: "root cause: capability route double-wraps handler response, callRegistryCapability read past real payload -> starved both CR-93 (PMP false not-formed) and CR-94 (coverage.served:0) identically; fixed unwrap once in-scope. bearing_yogas now reads ga_yoga_firings (MSR demoted to corroboration); composite formula adds yogaTerm; on 482012f1/wealth composite 1.15->~2.79 (convergent_moderate->convergent_strong). Stale description fixed. B9-preview guard added. platform: tsc clean, npm test 5522/0 failed. platform-mcp: tsc clean, vitest 423 passed/75 failed byte-identical to baseline (zero regressions)."}
  - {lane: A-gamma, branch: wave/D-1.5a/A-gamma, status: claimed, receipt_ref: null, agent_id: a8c232edeee142ef7, commit: 08af39bf, claim: "A7 offset fix (opposition/special aspects now 1.0, was 0.0); A5 9-case two-chart parametrized divergence test; 36 new tests pass; full suite 3352 passed/0 failed (net +36, zero regressions); diff scope-clean (3 files, all in may_touch)"}
notes: "A-beta merges last (A-gamma -> A-alpha -> A-beta); A-0 harness landed, Phase-1 verifiers spawned for A-0/A-alpha/A-gamma."
verifiers:
  - {lane: A-0, model: opus, agent_id: afbeca6133e46621e, status: running}
  - {lane: A-alpha, model: opus, agent_id: a9b35558d8a18d91b, status: running}
  - {lane: A-gamma, model: opus, agent_id: aaac709386bfc4cbf, status: running}
  - {lane: A-beta, model: opus, agent_id: afa4ab53cd20e012f, status: running}
deploy: {done: false, sha: null}
rebuild:
  "482012f1-710e-4a25-994a-93821f5871aa": pending
  "1c826d5a-41cb-4450-b4dc-59d440e5f75a": pending
gate: {run: false, green: [], red: []}
updated_at: "2026-07-15 (session open, post-Binder)"
```
