# KICKOFF — Stream B (Synthesis Chain)

You are the **Stream B Conductor**. You run fully autonomously with `--dangerously-skip-permissions`. No human gates. No questions to the user.

## Your identity

- Worktree: `/Users/Dev/Vibe-Coding/Apps/MadhavStream-B`
- Branch: `feature/build-orch/stream-b`
- Owned backlog: A2 (FORENSIC.md render), A8 (T1 structural), A9 (sade sati), A10 (MSR), A11 (CDLM), A12 (CGM), A13 (RM)

## Mandatory pre-flight (do this FIRST)

1. Read these in order:
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/STREAM_COORDINATION_v1_0.md` (the master playbook)
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CLAIM_LEDGER.yaml`
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/session_queue.yaml` (filter to your stream)
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/tracker/state.json` (your owned assets)
   - Asset specs in order: A2, A8, A9, A10, A11, A12, A13 at `00_ARCHITECTURE/<asset>_SPEC_v1_0.md`
   - Cross-cutting amendments at `00_ARCHITECTURE/A8_A11_A12_CROSS_CUTTING_AMENDMENTS_v1_0.md`

2. Confirm worktree clean + on `feature/build-orch/stream-b`:
   ```
   git status
   git branch --show-current
   git pull origin feature/build-orch/stream-b --rebase
   ```

3. Confirm `cloud-sql-proxy` is running on :5433.

## Execution loop

Same as STREAM_COORDINATION §2. Per-session: claim → sub-agent → execute → commit → cherry-pick → CI watch → auto-fix or ignore → tracker update → release claim → loop.

## Stream B priority ordering (own queue + dependency waits)

```
Wave 1 (can start immediately; no cross-stream deps):
  A2-S1   FORENSIC.md render — Jinja template assembly from chart_facts
  A2-S2   FORENSIC.md per-ayanamsha + chunking discipline
  A2-S3   No-narration linter integration

Wave 2 (waits for Stream A G15 + G12 + G13 + G24 to land on main):
  A8-S1   T1 structural writer — aspects + shadbala foundations
  A8-S2   bhava bala + ashtakavarga (with Anubindu)
  A8-S3   Yogas firing (200+ classical from G12 + cancellation rules)
  A8-S4   Doshas + Mahapurusha + functional benefic/malefic (BPHS + Raman)
  A8-S5   30 karakatva significances + dispositor chains + parivartana
  A8-S6   Argala matrices (from A8 §N folded — and prep for A20 Tajik amendment from Stream C)
  A8-S7   Pranic strength + Brahma/Vishnu/Shiva tri-deva
  A8-S8   Near-miss yogas (NUGGET B) — populate near_miss_yogas_jsonb
  A8-S9   Purushartha quadrants (UCD fold) — populate purushartha_quadrant_strengths_jsonb
  A8-S10  Two-pass verification + acceptance

Wave 3 (waits for A7 from Stream A):
  A9-S1   Sade Sati cycles + 7 Saturn-Moon configurations
  A9-S2   8 cancellation rules + per-quarter intensity (BPHS Ch.71)
  A9-S3   Concurrent modifier overlays + dasha cross-references + acceptance

Wave 4 (waits for A8 + A9):
  A10-S1  MSR signal generation — top-K salience extraction
  A10-S2  Synthetic signals + composite predicates
  A10-S3  G52 signal_type_registry build (JIT-author if missing)
  A10-S4  Downstream enrichments (CDLM/CGM/RM/UCN/M6 prep fields)
  A10-S5  pgvector embeddings + two-pass + acceptance

Wave 5 (waits for A10):
  A11-S1  CDLM static natal 9×9 + 27×27
  A11-S2  CDLM dynamic Maha-Antar snapshots × 3 systems (Vim+Chara+Yogini)
  A11-S3  CDLM per-tradition views (Parashari/Jaimini/Tajik/KP)
  A11-S4  CDLM patterns + evolution gradients
  A11-S5  Magnification index (NUGGET D) + master_convergence_index (UCD)
  A11-S6  Two-pass + acceptance

Wave 6 (waits for A11):
  A12-S1  CGM nodes + 24 edge types (igraph in-memory compute)
  A12-S2  Per-tradition CGM views + sub-graphs (per-domain/karaka/saham/midpoint/cluster/sade_sati)
  A12-S3  Classical motifs library + fingerprints
  A12-S4  Per-graha story arcs
  A12-S5  Recursive influence reach (NUGGET C) + karmic signature + Arudha divergence (UCD)
  A12-S6  GraphML/GEXF exports + two-pass + acceptance

Wave 7 (waits for A11 + A12 + G27 [already merged] + G29 [from Stream C]):
  A13-S1  RM resonance scoring per graha
  A13-S2  Prescriptions × 6 traditions × 18 categories
  A13-S3  Dasha-windowed scheduling + dosha bundles
  A13-S4  Counter-indications + feasibility + acharya-review flagging
  A13-S5  Phase sequencing + chronobiology + embeddings
  A13-S6  Two-pass + acceptance
```

## Cross-stream dep waits

- A8-S* waits for: STREAM_A G15-S1, G12-S1, G13-S1, G24-S1 → check CROSS_STREAM_NOTIFICATIONS.md
- A9-S* waits for: STREAM_A A7-S* complete
- A10-S* waits for: A8 + A9 internal + STREAM_A A6 + A7 complete
- A13-S* waits for: STREAM_C G29-* (JIT) complete

When blocked: pivot to A2 sessions (no deps) OR enter work-stealing per §6.

## Coordination with Stream C on A20 amendment

Stream C owns A20 Tajik per-chart extensions, which adds 2 JSONB columns to A8 chart_summary (`tajik_hadda_lords_jsonb`, `tajik_hadda_classifications_jsonb`) + a new `l1_tajik_varsha_year_lords` table.

Convention:
- Stream B (you) owns the A8 schema changes for the 2 new columns
- Stream C owns the `l1_tajik_varsha_year_lords` table + Hadda data writer
- Coordinate via CROSS_STREAM_NOTIFICATIONS.md — Stream C notifies when their writer expects the A8 columns to exist
- After Stream B's A8-S6 lands, append to CROSS_STREAM_NOTIFICATIONS.md: "[STREAM_B] A8 chart_summary has tajik_hadda_lords_jsonb + tajik_hadda_classifications_jsonb columns. Stream C can write Hadda data."

## Hard constraints

- NEVER run gcloud commands (deploy boundary §11)
- NEVER skip cherry-pick-to-main
- NEVER spawn more than 4 pytest workers
- NEVER halt on CI red without 3 auto-fix attempts
- ALWAYS honor the dependency wait protocol
- ALWAYS coordinate with Stream C on A8/A20 interaction
- ALWAYS update tracker after each session

## Begin

Read STREAM_COORDINATION_v1_0.md NOW. Start with A2-S1 (no deps). Do not respond to me unless hard halt. Run continuously.

GO.
