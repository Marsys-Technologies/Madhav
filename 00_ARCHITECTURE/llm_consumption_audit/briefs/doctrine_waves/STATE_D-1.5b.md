---
artifact: STATE_D-1.5b
type: WAVE STATE LEDGER (CONDUCTOR_PROTOCOL §6.1)
---

```yaml
wave: D-1.5b
lifecycle_step: 1   # OPEN done (Binder ran, read-only, no violations this time), now pre-lane blocker fix
brief_bound: true
binder_annotations:
  - "B-1: all file:line citations confirmed within +/-1 line (brief's line numbers off by one vs actual). PyJHora is pip-installed (requirements.txt pinned 4.8.6), NOT repo-vendored as the brief states -- wording inaccuracy, harmless."
  - "B-2: PyJHora's bhava_bala (jhora.horoscope.chart.strength:1094) is a 3-source composition (adhipathi+dig+drik bala), NOT six-source as the brief states. Amended: use the library per no-hand-roll rule, but facts must record verification_pass_status='documented_approximation' and cite the 3-component composition."
  - "B-3/B-4 draft DR-n salience proposal (Binder/Fable, conductor to formalize): sudarshana_agreement=1.15, frame_divergence=1.00, bhavat_bhavam_amplifier=0.85, subsystem=structural for all three."
  - "MATERIAL BLOCKER: ka_vighnakara ForeignKeyViolation (carried forward from D-1.5a REPORT) blocks 23 error + 19 stale assets in the L3->L5 cascade. D-1.5b's brief mandates a FULL L1->L5 rebuild for Gate B -- this cannot go green with the defect unfixed. Must be fixed BEFORE the wave's rebuild+gate step, even though outside the original 7 lanes' declared scope."
  - "Also found: 1 orphaned build_run (5580b8a5, state=planned) needs cleanup before dispatching, same class of issue D-1.5a hit with _MAX_CONCURRENT_RUNS."
  - "Scope recommendation: stage lane spawn in 2 cycles given wave size (7 lanes + only full-rebuild wave + live library integration). Cycle 1: B-5 -> B-2 -> B-1 (fact writers + astronomical core). Cycle 2: B-3 -> B-4 -> B-6 -> B-7 (consumers/serving/governance). Single rebuild+gate after cycle 2, per brief's own merge order."
rollback_pin:
  images:
    amjis-web: "d64bc575f72335cbd8b756a5a1768a2aa4d93f26"
    amjis-mcp: "53b4b44cf3381bba3eb1cb59e8edeeac529e03ab"
    brahma-pipeline: "2271c32e647d52f7be77447343038468d0ef74bd"
  build_ids:
    "482012f1-710e-4a25-994a-93821f5871aa": "5bdd933f-86b2-4609-ba7d-177f30ea1675"
prerequisite_check: {d1_5a_gate: green, note: "13/15 + 2 documented PARKs per REPORT_D-1.5a.md; brief's hard-block (gate GREEN) satisfied"}
lanes: []   # not yet spawned -- pre-lane blocker fix in progress
precascade_rebuild:
  ka_vighnakara_fk: RESOLVED   # was NOT a code bug -- purely the orphaned-concurrent-build_runs race from D-1.5a (cleaned up). ka_sangam/ka_vighnakara/full Kala cascade rebuilt lit once the pileup was cleared.
  local_proxy_diagnosis: >
    Repeated local-rebuild failures ROOT-CAUSED (not a product bug): the laptop
    cloud-sql-proxy path is unreliable -- proxy intermittently drops (fresh
    connect() fails in logs) AND bo_samskara's ~2-min/ayanamsha Vertex AI embed
    loop holds an idle DB conn long enough that a drop mid-embed kills the whole
    run, restarting embedding from scratch (Sisyphus loop). Product code already
    fully resilient (keepalives, idle-txn timeout=0 x2, batch-level embed
    tolerance) and completes fine in prod. Fix: stop using the laptop proxy for
    the build -- dispatch the Cloud Run job (protocol §8.2 canonical mechanism),
    which runs inside GCP with a direct Cloud SQL connection.
  method: "gcloud run jobs execute brahma-build-pipeline-job --args=--run-id,<id> (build_runs row created via scripts/dispatch_d1_5b_precascade_job.py; execution brahma-build-pipeline-job-h5c7l; run_id 585d4a9c-8341-4b40-a116-0f063c3855c0; 23 remaining assets, bo_samskara first)"
  status: running
gate: {run: false, green: [], red: []}
updated_at: "2026-07-15 (D-1.5b -- ka_vighnakara resolved as concurrency-race not code bug; local-proxy fragility root-caused, rebuild moved to Cloud Run job)"
```
