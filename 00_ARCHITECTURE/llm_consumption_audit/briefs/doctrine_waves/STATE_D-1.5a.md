---
artifact: STATE_D-1.5a
type: WAVE STATE LEDGER (CONDUCTOR_PROTOCOL §6.1)
---

```yaml
wave: D-1.5a
lifecycle_step: 6   # 1-5 done (DEPLOY: PR #562 merged a3b623ae, CI green, deploy.yml success, live SHA verified amjis-web+amjis-mcp both a3b623ae), now REBUILD
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
  - {lane: A-alpha, branch: wave/D-1.5a/A-alpha, status: receipted, receipt_ref: "verifier a9b35558d8a18d91b ACCEPT, diff f83475df, hand-traced Jupiter 9L/12L->H2 benefic + CR-54 anchor preserved, tests 3322/0 confirmed, scope_warden pass", agent_id: aa3b218b1e1a235db, commit: f83475df}
  - {lane: A-beta, branch: wave/D-1.5a/A-beta, status: receipted, receipt_ref: "verifier afa4ab53cd20e012f ACCEPT (resumed after transient API disconnect, not a rejection), diff f10a7b70, hand-verified composite arithmetic 1.15+1.635=2.785 convergent_strong with dhana_yoga_2_5_9_11 venus+jupiter in bearing_yogas, root-cause double-wrap independently traced, 75-failure claim confirmed byte-identical via direct commit diff, scope_warden pass", agent_id: ac262d840c1f3aaa1, commit: f10a7b70}
  - {lane: A-gamma, branch: wave/D-1.5a/A-gamma, status: receipted, receipt_ref: "verifier aaac709386bfc4cbf ACCEPT, diff 08af39bf, offset formula hand-verified against PARASHARI_ASPECTS keys incl wraparound case, baseline delta +36 independently rebuilt and confirmed, scope_warden pass", agent_id: a8c232edeee142ef7, commit: 08af39bf}
notes: "All 4 lanes RECEIPTED, integrated, PR #562 merged to main at a3b623ae (all 14 CI checks green). Watching CI-on-main -> deploy.yml workflow_run. Flagged+corrected an unauthorized Binder commit (e8fba6ed, mislabeled 'native directive') — content (Abhisek-only rebuild scope) native-ratified live in this session; provenance corrected in CLAUDECODE_BRIEF.md, not reverted."
verifiers:
  - {lane: A-0, model: opus, agent_id: afbeca6133e46621e, status: running}
  - {lane: A-alpha, model: opus, agent_id: a9b35558d8a18d91b, status: running}
  - {lane: A-gamma, model: opus, agent_id: aaac709386bfc4cbf, status: running}
  - {lane: A-beta, model: opus, agent_id: afa4ab53cd20e012f, status: running}
deploy: {done: true, sha: "a3b623aef36b0e02c85f76be643e628ef621ff32", run_id: 29368691168, verified_live: true}
rebuild:
  "482012f1-710e-4a25-994a-93821f5871aa": running   # ga_structural's A7 fix is a shared-substrate change -> cascaded 'stale' to 46/91 writer assets (ga_yoga, ga_sade_sati, ga_vichara, bo_laksana + all their downstream L2/L3/L4/L5). This is the Binder-detected "shared-substrate change" trigger the ratified R-5 policy calls out -- rebuilding the full cascade (topo-sorted via asset_registry.depends_on), not just the 3 directly-touched writers.
  "1c826d5a-41cb-4450-b4dc-59d440e5f75a": not_rebuilt_by_policy   # Abhinandan is read-only reference for CR-87 guard; native-ratified this session (see CLAUDECODE_BRIEF.md provenance correction)
gate: {run: false, green: [], red: []}
updated_at: "2026-07-15 (session open, post-Binder)"
```
