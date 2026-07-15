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
lanes:
  # CYCLE 1 (Binder-recommended staging): fact writers + astronomical core. Merge order B-5 -> B-2 -> B-1.
  - {lane: B-5, branch: wave/D-1.5b/B-5, status: implementing, agent_id: a0e2585e962da68fa, scope: "small L1 completions: karakamsha(CR-17), shadbala required_rupa+ratio(CR-18), D2 hora-class(CR-58), ph_nimitta anchor dedup(CR-46)"}
  - {lane: B-2, branch: wave/D-1.5b/B-2, status: implementing, agent_id: a01f9747c2c67140c, scope: "bhava bala(CR-103, 3-source per Binder w/ documented_approximation) + astakavarga sign-rekey+shodhana/pinda/kakshya(CR-99a, bindu VALUES frozen)"}
  - {lane: B-1, branch: wave/D-1.5b/B-1, status: implementing, agent_id: ad8c83defdb551e7b, scope: "HEADLINE: chalit + real Sripati/Placidus cusps(CR-98/DR-2), quarantine fake KP cusps(2 sites), sandhi_flag. Acceptance: Moon 29d46' Aquarius -> Sripati H12. 2 verifiers."}
  # CYCLE 2 (spawn after cycle 1 integrates): B-3 (Sudarshana), B-4 (Bhavat Bhavam), B-6 (serving hygiene), B-7 (governance+derived view). B-3/B-4 need the salience DR (Binder draft: sudarshana_agreement=1.15, frame_divergence=1.00, bhavat_bhavam_amplifier=0.85) formalized by conductor at cycle-2 open.
cycle: 1
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
  status: COMPLETE   # job completed clean: 64/64 per-chart assets lit, 0 error/stale/dormant. Health verified: bodha_signal_embeddings(47848)==bodha_msr_signals(47848) -> bo_samskara fully embedded, NO partial loss (the exact failure the local proxy kept causing); kala_obstruction=679 -> ka_vighnakara ran clean; chart_facts=136029 (~27554 x5 aya); 0 orphaned runs after cleanup.
  learning: >
    D-1.5b's OWN mandated FULL L1->L5 gate rebuild (brief §G) MUST use this same
    Cloud Run job path, NOT the laptop cloud-sql-proxy -- the proxy path cannot
    reliably complete bo_samskara's embedding loop. dispatch_d1_5b_precascade_job.py
    generalizes trivially (it plans the full non-lit closure); for the gate rebuild,
    reset the wave's touched layers to dormant, create the run row, dispatch the job.
gate: {run: false, green: [], red: []}
updated_at: "2026-07-15 (D-1.5b pre-lane blocker RESOLVED; estate 64/64 lit & healthy via Cloud Run job; ready to spawn cycle-1 lanes B-5/B-2/B-1)"
```
