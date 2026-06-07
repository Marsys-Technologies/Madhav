---
artifact: BRAHMA_L0_FOUNDATION_REBUILD_v1_2.md
canonical_id: L0FR_MASTER_PLAN
version: 1.2
status: READY_FOR_AUTONOMOUS_EXECUTION
authored_by: Cowork (planning) 2026-06-07
supersedes: v1.0, v1.1
v1.2 changes: fully autonomous; operator review gates replaced with Vimarśaka review agents; only Tier-3 $5k cap surfaces to native; all 7 stream briefs authored as committed artifacts; source data file authored; launch paste orchestrates the swarm without human intervention until seal
---

# Brahma L0 Foundation Rebuild — Master Plan v1.2 (FULLY AUTONOMOUS)

## §1 — Mission

Same as v1.1. Build production-quality L0 Brahma Jñāna + unified L0-L5 retrieval layer (three primitive types, four adapter implementations, full agentic loop, OpenAI/ChatGPT first-class, no audience tier).

## §2 — Locked decisions

Same as v1.1 §2.

## §3 — Classical text corpus (15 texts)

Same as v1.1 §3. **Source data file** at `00_ARCHITECTURE/L0FR_SOURCE_DATA_v1_0.md` lists per-text edition URLs, manual-upload flags, and license verification.

## §4 — Remedy corpus

Same as v1.1 §4.

## §5 — Sūtravali extraction

Same as v1.1 §5.

## §6 — Unified retrieval registry

Same as v1.1 §6.

## §7 — Four adapter implementations

Same as v1.1 §7.

## §8 — Per-stream capability registration

Same as v1.1 §8.

## §9 — Stream topology — fully autonomous

```
                  Stream A (Infrastructure)
                          ↓
                  Vimarśaka-A reviews
                  (autonomous, programmatic)
                          ↓
              APPROVE? → continue; REJECT? → rework loop
                          ↓
       ┌──────────────────┼──────────────────┐
       │       │          │         │        │
   Stream B  Stream C  Stream E  Stream F  Stream G
   (Ephem)   (Texts)   (Panch)   (Remedy)  (PyHora)
       │       │          │         │        │
       │  Stream C mid    │         │        │
       │       ↓          │         │        │
       │  Vimarśaka-C     │         │        │
       │  (chunk quality) │         │        │
       │       ↓          │         │        │
       │  APPROVE? → continue C + spawn Stream D
       │       ↓          │         │        │
       │  Stream D (Sūtravali)      │        │
       │       │          │         │        │
       └───────┴──────────┴─────────┴────────┘
                          ↓
                  Vimarśaka-Z (seal)
                  (autonomous, comprehensive)
                          ↓
              APPROVE? → SEAL; REJECT? → delta-deploy loop
                          ↓
                       L0 SEALED
```

**Only escape valves to native:**
- Per-stream Tier-3 catastrophic-runaway cap ($5k absolute)
- Total wave Tier-3 cap ($10k absolute)
- Vimarśaka-Z escalation if 3 consecutive delta-deploy attempts fail

Otherwise the swarm runs autonomously until SEAL.

## §10 — Vimarśaka review agents (NEW in v1.2)

Specifications at `00_ARCHITECTURE/L0FR_VIMARSAKA_SPECS_v1_0.md`. Three specialized review agents replace the v1.1 operator gates:

| Gate | Agent | Authority | Decision rules |
|---|---|---|---|
| Post-Stream A | **Vimarśaka-A** (Architecture) | APPROVE / REJECT_WITH_FEEDBACK / ESCALATE_TIER3 | Programmatic checks on schema, kill-list audit, adapter compile, OAuth round-trip, parity, 5 initial capabilities |
| Mid-Stream C | **Vimarśaka-C** (Content Quality) | APPROVE / REJECT_WITH_FEEDBACK | Random sample of 50 chunks scored on 6-criterion rubric; ≥0.85 mean = APPROVE; <0.85 = REJECT with specific chunk-level feedback for rework |
| Pre-seal | **Vimarśaka-Z** (Integration Seal) | SEAL / DELTA_DEPLOY / ESCALATE_TIER3 | Full integration: all 4 adapters smoke-test each registered capability; ChatGPT MCP roundtrip; first global-build; first per-chart build; corpus completeness floors met |

Each Vimarśaka has full read access to: master plan, source data, stream briefs, smoke test outputs, prod DB state, Smṛti history. Each has authority to invoke up to 3 rework loops per stream before tier-3 escalation.

## §11 — Stream brief artifacts

All 7 stream briefs are committed canonical artifacts at:
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_L0FR_STREAM_A_v1_0.md` (Infrastructure)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_L0FR_STREAM_B_v1_0.md` (Ephemeris)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_L0FR_STREAM_C_v1_0.md` (Text ingestion)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_L0FR_STREAM_D_v1_0.md` (Sūtravali)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_L0FR_STREAM_E_v1_0.md` (Pañcāṅga)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_L0FR_STREAM_F_v1_0.md` (Remedies)
- `00_ARCHITECTURE/BRIEFS/CLAUDECODE_BRIEF_L0FR_STREAM_G_v1_0.md` (PyHora)

Each brief is self-contained: worktree path, branch, dependencies, scope (numbered steps), capability registrations, AC checks, Vimarśaka readiness checklist, budget cap, Tier-3 escalation conditions.

## §12 — Cost model (revised 2026-06-07 — DETERMINISTIC-FIRST)

Per memory `feedback_deterministic_first_for_data_build`: build-time LLM use is eliminated wherever Python suffices. The only LLM use remaining is **Vertex AI text embeddings** for the text_index — these are deterministic transformations (not generative LLM) and are explicitly permitted under the deterministic-first rule.

**LLM cost by stream:**

| Stream | LLM use | Estimated cost |
|---|---|---|
| A | None | $0 |
| B | None | $0 |
| C | Vertex AI embeddings only (deterministic transform) | ~$0.63 |
| D | NONE (pure Python regex extraction) | $0 |
| E | None | $0 |
| F | NONE (YAML + Python loader) | $0 |
| G | None | $0 |
| Vimarśaka-A | None (pure Python script) | $0 |
| Vimarśaka-C | None (pure Python structural checks) | $0 |
| Vimarśaka-Z | None (pure Python structural + smoke tests) | $0 |
| **Total LLM** | **~$1 one-time** | |

Plus minor Cloud Run compute (~$5), Document AI OCR only if PyMuPDF fails (~$0-5).

**Total per-stream Tier-3 caps:** A=$500, B=$150, C=$200, D=$50, E=$250, F=$50, G=$150. **Total wave cap: $1,350** (down from $2,250 in v1.1).

**Quality trade-offs explicitly accepted** (per native 2026-06-07):
- Sūtravali corpus: ~800-2,000 rules instead of 5,000-10,000 (Python regex covers templated patterns only; non-templated rules are SKIPPED, not LLM-fallback'd)
- Text chunks: some parked to `/tmp/l0fr_chunks_parked.txt` for native review (not LLM-completed)
- Remedy corpus: ~200-500 instead of 500-1,000 (YAML hand-curation pace-limited)
- Vimarśaka reviews: structural validation only (no semantic quality judgment); some semantically-flawed but structurally-valid content may pass through
- Cross-text deduplication: catches exact + Levenshtein-fuzzy duplicates; misses synonym/semantic dupes

These trade-offs preserve full reproducibility: re-running the L0FR build produces byte-identical output (modulo timestamps).

## §13 — Cross-stream signal protocol

Streams signal completion + readiness via git tags + shared YAML state file at `00_ARCHITECTURE/CONDUCTOR/l0fr/state.yaml`:

```yaml
streams:
  A: { status: pending|running|review|approved|sealed, tag: null|<sha> }
  B: { status: blocked|running|review|approved|sealed }
  C: { status: blocked|running|midway_review|midway_approved|running|review|approved|sealed }
  D: { status: blocked|running|review|approved|sealed }  # blocks on C.midway_approved
  E, F, G: same shape
gates:
  vimarsaka_a: { status: pending|pass|fail|escalated, attempts: 0 }
  vimarsaka_c: same shape
  vimarsaka_z: same shape
budget_spent_usd_per_stream: { A: 0, B: 0, ... }
```

The master Conductor (Sūtradhāra) polls state.yaml every minute and spawns next-eligible streams when conditions met. No human input required.
