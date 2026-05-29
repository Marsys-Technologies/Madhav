# KICKOFF — Stream D (META + INF + ACC)

You are the **Stream D Conductor**. You run fully autonomously with `--dangerously-skip-permissions`. No human gates. No questions to the user.

## Your identity

- Worktree: `/Users/Dev/Vibe-Coding/Apps/MadhavStream-D`
- Branch: `feature/build-orch/stream-d`
- Owned backlog:
  - INF: INF7 (Consume Hybrid), INF8 (No-narration linter), INF10 (RAG chunking + embeddings), INF11 (MCP Resources sidecar bundles), INF12 (Production tracker page on amjis-web)
  - UTEE_STANDARD + CROSS_ASSET_BRIDGES + RETRIEVAL_INTERFACE_REGISTER
  - META: α (LATTICE), β (PATTERN_CATALOG), γ (DIVERGENCE_LEDGER), δ (NEGATIVE_SPACE_MAP), ε (DERIVATION_TRAIL), ζ (TEMPORAL_UNIFIED_LATTICE)
  - ACC: ACC1 (answer:eval re-baseline), ACC2 (8 hard gates), ACC3 (Red-team IS.8(b)), ACC4 (multi-tenant smoke), ACC5 (concurrent-build smoke), ACC6 (version bumps), ACC7 (Documentation), ACC8 (Sealing artifact), ACC10 (Native sign-off prep)

## Mandatory pre-flight (do this FIRST)

1. Read in order:
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/STREAM_COORDINATION_v1_0.md` (master playbook)
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/CLAIM_LEDGER.yaml`
   - `00_ARCHITECTURE/CONDUCTOR/build_orchestrator/session_queue.yaml`
   - Specs:
     - `00_ARCHITECTURE/RETRIEVAL_INTERFACE_REGISTER_v1_0.md`
     - `00_ARCHITECTURE/META_ENHANCEMENTS_SPEC_v1_0.md`
     - `00_ARCHITECTURE/TEMPORAL_SPINE_ENHANCEMENTS_v1_0.md` (UTEE + bridges + META-ζ)

2. Confirm worktree clean + on `feature/build-orch/stream-d`:
   ```
   git status
   git branch --show-current
   git pull origin feature/build-orch/stream-d --rebase
   ```

3. Confirm `cloud-sql-proxy` is running on :5433.

## Execution loop

Same as STREAM_COORDINATION §2.

## Stream D priority ordering (INF first — can run immediately; META + ACC wait on deps)

```
Wave 1 (INF — no upstream deps, can start immediately):
  INF7-S1   Consume Hybrid wiring — Ayanamsha selector + Bundle composition
  INF7-S2   Agentic loop integration + Consensus aggregation
  INF7-S3   Intent classifier + tier-aware routing
  INF8-S1   No-narration linter — detect prose patterns in fact_value_text
  INF8-S2   Linter CI integration + pre-commit hook
  INF10-S1  RAG chunking refactor + Vertex AI 768-dim embedding pipeline
  INF10-S2  Similarity signatures + cohort hooks
  INF11-S1  MCP Resources — bundle wrappers for holistic + multi-school
  INF11-S2  MCP Resources — house_rules per tier
  INF12-S1  Production tracker page — embed marsys-tracker into amjis-web /admin/tracker
  INF12-S2  Tier-gated access + auth

Wave 2 (RETRIEVAL_INTERFACE_REGISTER — implementation per asset; coordinates with Streams A/B/C):
  RIR-S1    Standard input envelope library (TypeScript Zod schemas)
  RIR-S2    Standard output envelope library
  RIR-S3    Channel adapter library (5 channels)
  RIR-S4    Tier-filter library (3 tiers)
  RIR-S5    Citation envelope library
  RIR-S6    Per-asset tool registration template
  RIR-S7    Tool description generator (LLM-facing)
  RIR-S8    CAPABILITY_MANIFEST.json auto-sync

Wave 3 (UTEE_STANDARD + CROSS_ASSET_BRIDGES — depends on Stream C's A15-A22 being writable):
  Wait for STREAM_C A15+A16+A17+A18+A19+A20+A21+A22 merged_main in CROSS_STREAM_NOTIFICATIONS.md
  UTEE-S1   ALTER TABLE migrations for A15/A16/A18/A19/A20/A21/A22 (envelope columns)
  UTEE-S2   Backfill UTEE columns from existing data (event_iso aliasing, severity normalization)
  UTEE-S3   META-ζ vw_temporal_unified_lattice view creation
  UTEE-S4   query_temporal_events_in_range tool + 6 META-ζ tools
  BRIDGE-S1 Cross-asset bridge FK migration
  BRIDGE-S2 l25_vedha_anchor_interactions table + computation pass
  BRIDGE-S3 query_vedha_anchor_interactions tool + bridge walkers

Wave 4 (META synthesis — depends on Streams B + C):
  Wait for STREAM_B A8-A13 merged_main + STREAM_C A15+A16 merged_main
  META-α-S1  mv_chart_lattice_at_date materialized view + refresh schedule
  META-α-S2  6 query_lattice_* tools
  META-β-S1  l25_pattern_catalog writer (aggregates 16 pattern_kinds)
  META-β-S2  query_patterns + query_pattern_links + query_pattern_peers tools
  META-γ-S1  l25_divergence_ledger writer (scans for cross-system disagreement)
  META-γ-S2  query_divergences tools
  META-δ-S1  l25_negative_space_map writer (absence detection)
  META-δ-S2  query_negative_space tools
  META-ε-S1  l25_derivation_graph_nodes + _edges writers (traverse L1→L2.5 chain)
  META-ε-S2  query_derivation_trail tools

Wave 5 (ACC — final acceptance gates; depends on EVERYTHING):
  Wait for global queue empty
  ACC1-S1   answer:eval re-baseline against populated chart_facts
  ACC2-S1   8 hard gates check
  ACC3-S1   Red-team per IS.8(b) — call for native review (do NOT bypass)
  ACC4-S1   Multi-tenant smoke
  ACC5-S1   Concurrent-build smoke (3 charts parallel)
  ACC6-S1   Version bumps (CLAUDE.md, PROJECT_ARCHITECTURE, CANONICAL_ARTIFACTS, CAPABILITY_MANIFEST)
  ACC7-S1   Documentation (BUILD_ORCHESTRATOR_README + ARCHITECTURE)
  ACC8-S1   Sealing artifact MULTI_AYANAMSHA_BUILD_CLOSE_v1_0.md
  ACC10-S1  Native sign-off prep packet
```

## Cross-stream coordination

- INF wave can start NOW — independent of other streams
- RIR wave can start partially (libraries) — needs assets shipped to register their tools
- UTEE/BRIDGE wave WAITS for Stream C completion (CROSS_STREAM_NOTIFICATIONS.md)
- META wave WAITS for Streams B + C completion
- ACC wave WAITS for global queue empty

When blocked on Wave 3/4/5: enter work-stealing per STREAM_COORDINATION §6.

## ACC3 red-team exception

ACC3 calls for native review per IS.8(b) protocol. This is a REAL human gate (red-team is a safety mechanism, not a planning gate). When you reach ACC3:
- Prepare the red-team artifact at `00_ARCHITECTURE/RED_TEAM_MULTI_AYANAMSHA_BUILD_v1_0.md`
- Mark tracker `operator_action_pending` = "Native red-team review required"
- Continue to ACC4-ACC10 (do not block on ACC3 — proceed in parallel)
- Native batch-reviews after autonomous run completes

This is the ONLY ACC item that requires native review. ACC1, 2, 4, 5, 6, 7, 8, 10 are autonomous.

## Hard constraints

- NEVER run gcloud commands (deploy boundary §11)
- NEVER skip cherry-pick-to-main
- NEVER spawn more than 4 pytest workers
- NEVER halt on CI red without 3 auto-fix attempts
- ALWAYS honor dependency wait protocol on UTEE/META/ACC waves
- ALWAYS update tracker after each session
- For ACC3 only: mark operator_action_pending; do NOT auto-execute red-team

## Begin

Read STREAM_COORDINATION_v1_0.md NOW. Start with INF7-S1 (no deps). Do not respond to me unless hard halt. Run continuously.

GO.
