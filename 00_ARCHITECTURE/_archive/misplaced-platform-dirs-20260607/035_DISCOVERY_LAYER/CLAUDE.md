# 035_DISCOVERY_LAYER — Instructions

This folder contains the L3 Discovery Layer artifacts: pattern, resonance, cluster, and contradiction registers.

## Structure

```
035_DISCOVERY_LAYER/
├── REGISTERS/           ← canonical JSON authoring sources (read-only for pipeline)
│   ├── PATTERN_REGISTER_v1_0.json
│   ├── PATTERN_REGISTER_v1_0.md       (human-readable companion; JSON is authoritative)
│   ├── RESONANCE_REGISTER_v1_0.json
│   ├── RESONANCE_REGISTER_v1_0.md
│   ├── CLUSTER_ATLAS_v1_0.json        (named ATLAS not REGISTER; table is cluster_register)
│   ├── CLUSTER_ATLAS_v1_0.md
│   ├── CONTRADICTION_REGISTER_v1_0.json
│   └── CONTRADICTION_REGISTER_v1_0.md
├── LEDGER/              ← derivation ledgers linking L3 claims to L1 fact_ids
├── PROMPTS/             ← discovery prompts used to generate register entries
├── QUERY_TAXONOMY/      ← LLM query routing taxonomy
├── RED_TEAM/            ← red-team findings against L3 layer
└── SCHEMAS/             ← JSON schemas for register validation
```

## STRUCTURED projection (Phase 14E, 2026-04-29)

All four registers are projected into Postgres tables via the pipeline:

| Register | Table | Rows | Tool |
|---|---|---|---|
| Pattern Register | `pattern_register` | 22 | `query_patterns` |
| Resonance Register | `resonance_register` | 12 | `query_resonances_l3` |
| Cluster Register (Atlas) | `cluster_register` | 12 | `query_clusters` |
| Contradiction Register | `contradiction_register` | 8 | `query_contradictions` |

Canonical spec: `00_ARCHITECTURE/L3_DISCOVERY_REGISTERS_v1_0.md`

Pipeline ingest:
```bash
cd platform/python-sidecar
DATABASE_URL=<url> python3 -m pipeline.ingest_l3_registers
```

## Authoring rules

1. **JSON is canonical.** The `.md` companions are human-readable views. If JSON and `.md` companion disagree, JSON wins. The pipeline reads JSONs only.
2. **Registers are append-only.** Do not remove entries from the JSON source — set `status: superseded` instead. The pipeline never deletes live rows; it adds new entries and updates existing ones (except `status=rejected` entries, which are protected from auto-revert).
3. **Must-not-touch during pipeline execution.** `035_DISCOVERY_LAYER/REGISTERS/*.json` and their `.md` companions are marked `must_not_touch` in all 14E+ exec briefs. Only update them deliberately in a doc-authoring session, never as a side-effect of pipeline work.
4. **Confidence labels.** Source JSONs use HIGH/MED/LOW labels (or raw numeric for cluster). Mapped to 0.85/0.60/0.35 at ingest. Do not change numeric mappings without updating both `register_loader.py` and this file.
