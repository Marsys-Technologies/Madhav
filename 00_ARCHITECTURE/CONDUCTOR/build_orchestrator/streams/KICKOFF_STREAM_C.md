# KICKOFF — Stream C (Supplementary + Temporal Spine)

You are the **Stream C Conductor**. You run fully autonomously with `--dangerously-skip-permissions`. No human gates. No questions to the user.

## Your identity

- Worktree: `/Users/Dev/Vibe-Coding/Apps/MadhavStream-C`
- Branch: `feature/build-orch/stream-c`
- Owned backlog: A17 (Chakras), A18 (Vedha), A19 (Bhrigu transits), A20 (Tajik per-chart — coordinated with Stream B), A21 (next-exact-aspect), A15 (Time-Synchronicity), A16 (Phase-Locked Anchors), A22 (Per-Varsha Digest), G29 (Classical Timing Rule Catalog — JIT)

## Mandatory pre-flight (do this FIRST)

1. Read in order:
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/STREAM_COORDINATION_v1_0.md` (master playbook)
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CLAIM_LEDGER.yaml`
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/session_queue.yaml`
   - Asset specs:
     - `00_ARCHITECTURE/A17_A21_SUPPLEMENTARY_SPEC_v1_0.md` (consolidated for A17-A21)
     - `00_ARCHITECTURE/A15_TIME_SYNCHRONICITY_SPEC_v1_0.md`
     - `00_ARCHITECTURE/A16_PHASE_LOCKED_EVENT_ANCHORS_SPEC_v1_0.md`
     - `00_ARCHITECTURE/TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md` (for A22 + UTEE + bridges — UTEE/bridges owned by Stream D, but you need to know the schema you write toward)

2. Confirm worktree clean + on `feature/build-orch/stream-c`:
   ```
   git status
   git branch --show-current
   git pull origin feature/build-orch/stream-c --rebase
   ```

3. Confirm `cloud-sql-proxy` is running on :5433.

## Execution loop

Same as STREAM_COORDINATION §2.

## Stream C priority ordering

```
Wave 1 (JIT brief + supplementary that have no cross-stream deps):
  G29-S0  JIT-AUTHOR G29 Classical Timing Rule Catalog brief at 00_ARCHITECTURE/G29_CLASSICAL_TIMING_RULES_v1_0.md
          (~200 timing rules from BPHS dasha-phala + Phaladeepika + Jaimini Sutram + Tajik + KP + Saravali + Nadi)
  G29-S1  Implement G29 corpus seeding (1 rule per row in g29_timing_rules table)
  A17-S1  Chakras writer — Sarvatobhadra (28-nakshatra 9×9 grid)
  A17-S2  Chakras writer — Sapta-shalaka + Kalanala + Kota + Chandra Kala Nadi
  A17-S3  Two-pass + acceptance

Wave 2 (after A17 + waits for Stream A G* if any deps):
  A18-S1  Vedha calculations — nakshatra vedha (Sarvatobhadra-based)
  A18-S2  Vedha — tajik year-lord + dasha sub-lord + transit chakra + sapta-shalaka + argala extension
  A18-S3  Cancellation chains + two-pass + acceptance

Wave 3 (independent of others — can run in parallel with A17/A18):
  A19-S1  Bhrigu Bindu lifetime transit table (partition by hit_iso)
  A19-S2  Two-pass + acceptance

  A21-S1  Per-graha next-exact-aspect lifetime — Parashari aspects (3/7/10) + classical 0/60/90/120/180
  A21-S2  Per-graha next-exact-aspect lifetime — Tajik aspects (ithasala etc.)
  A21-S3  Two-pass + acceptance

Wave 4 (A20 — coordinate with Stream B on A8 schema):
  A20-S1  Wait for STREAM_B A8-S6 confirmation in CROSS_STREAM_NOTIFICATIONS.md
  A20-S2  Implement l1_tajik_varsha_year_lords writer (year-lord per varsha, Muntha, etc.)
  A20-S3  Implement Hadda lord data — write into A8 chart_summary columns added by Stream B
  A20-S4  Two-pass + acceptance

Wave 5 (waits for A17 + A18 + A19 + A21 — own queue):
  A15-S1  Time-Synchronicity writer — key-date enumeration
  A15-S2  Active cycle determination + convergence_intensity decomposition
  A15-S3  Cross-system divergence flagging + cluster detection
  A15-S4  Per-window pgvector embedding + multi-chart cross-resonance hook
  A15-S5  Two-pass + dual-source ephemeris audit + acceptance

Wave 6 (waits for A15 + G29):
  A16-S1  Phase-Locked Anchors writer — rule engine evaluation
  A16-S2  Cross-rule corroboration + per-tradition variants
  A16-S3  Falsifiability + structured outcome ontology + alternative scenarios
  A16-S4  Anchor-to-anchor causal chain DAG + A15 cross-reference
  A16-S5  Per-anchor embedding + two-pass + acceptance

Wave 7 (waits for A15 + A16 + A18 + A19 + A20 + A21):
  A22-S1  Per-Varsha Yearly Digest aggregation — all 5 temporal sources + dashas + Sade Sati
  A22-S2  UTEE envelope columns (depends on Stream D's UTEE_STANDARD work; coordinate)
  A22-S3  Per-varsha embedding + two-pass + acceptance
```

## Coordination with Stream B on A20 + A8 amendment

A20 adds 2 JSONB columns to A8 chart_summary (`tajik_hadda_lords_jsonb`, `tajik_hadda_classifications_jsonb`):

- Stream B owns the A8 schema change (in their A8-S6 session)
- You (Stream C) write the Hadda data INTO those columns once Stream B confirms via CROSS_STREAM_NOTIFICATIONS.md
- You own the new `l1_tajik_varsha_year_lords` table independently

## Coordination with Stream D on UTEE columns

A15, A16, A18, A19, A20, A21, A22 need UTEE envelope columns. Per TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md §1.C:
- You implement writers that POPULATE these columns
- Stream D's UTEE_STANDARD session adds the schema (ALTER TABLE)
- Convention: you author writer code expecting the columns exist; Stream D's session adds columns before yours runs
- Coordinate via CROSS_STREAM_NOTIFICATIONS.md — Stream D notifies when ALTER TABLE complete

## Hard constraints

- NEVER run gcloud commands (deploy boundary §11)
- NEVER skip cherry-pick-to-main
- NEVER spawn more than 4 pytest workers
- NEVER halt on CI red without 3 auto-fix attempts
- ALWAYS coordinate with Stream B on A20 + with Stream D on UTEE
- ALWAYS JIT-author G29 brief BEFORE attempting G29-S1 implementation
- ALWAYS update tracker after each session

## Begin

Read STREAM_COORDINATION_v1_0.md NOW. Start with G29-S0 (JIT brief author — no deps). Do not respond to me unless hard halt. Run continuously.

GO.
