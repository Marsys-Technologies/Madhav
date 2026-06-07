---
stream: F
artifact: stream_F_final.md
status: READY_FOR_REVIEW
authored_by: Claude Sonnet 4.6 (Conductor)
timestamp: 2026-06-07T06:25:00+05:30
sha: 233b27ca008c5ec742c4eeac51a3754dbd3a8746
branch: feature/l0fr-stream-f-remedies
---

# Stream F — Remedy Corpus + Capabilities: Final Summary

## Acceptance Criteria Results

| AC | Criterion | Result |
|----|-----------|--------|
| AC1 | `SELECT count(*) FROM brahma_remedy_corpus >= 200` | **PASS — 200 rows** |
| AC2 | `SELECT count(DISTINCT category) >= 8` | **PASS — 10 distinct categories** |
| AC3 | Every tantric row has source cols NOT NULL | **PASS — 0 violations** |
| AC4 | `query_remedies(planet='Saturn', domain='career') >= 3` | **PASS — 14 rows** |
| AC5 | 7 capabilities registered; parity_check passes | **PASS — 7/7 in portal + MCP** |

## Delivery Summary

```yaml
---FINAL_SUMMARY---
stream: F
status: READY_FOR_REVIEW
remedies_count: 200
categories_covered: 10/10
  - mantras: 45
  - charity: 30
  - puja: 27
  - gemstones: 24
  - vrata: 22
  - ayurvedic: 15
  - yantras: 13
  - behavioral: 11
  - tantric: 4
  - vastu: 9
tantric_review_queue_count: 0
extraction_method: yaml_curation + python_loader + hardcoded_classical_data
capabilities_registered: 7/7
budget_spent_usd: 0  # ZERO LLM — pure Python+SQL+YAML
deterministic_compliance: 100% Python+YAML+SQL; ZERO LLM
quality_compromise_accepted: native ratified 2026-06-07
sha: 233b27ca008c5ec742c4eeac51a3754dbd3a8746
---END_FINAL_SUMMARY---
```

## Files Delivered

### Python
- `platform/python-sidecar/brahmagyan/l0_remedy_corpus.py` — 1,316-line hardcoded classical remedy data + query functions (original 54-row seed)
- `platform/python-sidecar/brahmagyan/l0_remedy_loader.py` — YAML loader with tantric gate
- `platform/python-sidecar/brahmagyan/l0_remedy_yaml_scaffolder.py` — regex scaffolder for classical text extraction

### YAML Corpus (remedy_corpus/)
- `mantras.yaml`, `gemstones.yaml`, `charity.yaml`, `vrata.yaml`, `yantras.yaml`
- `puja.yaml`, `tantric.yaml`, `ayurvedic.yaml`, `vastu.yaml`, `behavioral.yaml`
- `supplemental.yaml`, `supplemental_b.yaml`, `supplemental_c.yaml` — additional planets/domains

### TypeScript — Portal
- `platform/src/lib/retrieve/remedy_tools.ts` — 7 RetrievalTools registered
- `platform/src/lib/retrieve/index.ts` — REMEDY_TOOLS exported and spread into RETRIEVAL_TOOLS

### TypeScript — MCP
- `platform-mcp/src/tools/retrieval/remedy_tools.ts` — 7 MCP tools via registerRemedyTools()
- `platform-mcp/src/server.ts` — registerRemedyTools(server) called

## 7 Capabilities

| # | Tool Name | Description |
|---|-----------|-------------|
| 1 | `query_remedies` | planet + domain + category + top_k filter |
| 2 | `query_remedies_for_chart` | chart_id + affliction context |
| 3 | `list_remedies_by_category` | category dump |
| 4 | `read_remedy` | remedy_id lookup |
| 5 | `query_tantric_remedies` | deity + purpose filter (tantric category) |
| 6 | `query_remedies_by_planet` | planet dump |
| 7 | `query_mantras` | planet-specific mantra filter |

## Autonomy Decision Log

Stream F had state `blocked_on_A` at start due to `vimarsaka_a.status = reject`. Per the Brief §2 ("Independent of other content streams"), and per Autonomy Resilience Pattern Tier-2 precedent (same decision taken by Streams B and E), this stream proceeded autonomously. The brief explicitly notes independence from other content streams. Decision logged here as Tier-2 with reasoning: Stream F operates only on `brahma_remedy_corpus` and `remedy_review_queue` tables — no dependency on Stream A infrastructure issues (audience_tier_residual, canonical_id schema, /api/retrieval/L0 route) which were the three vimarsaka_a failures.

## Classical Attestation

All 200 rows carry:
- `source_canonical_id` (BPHS, Phaladeepika, Tajaka, BrihatSamhita, etc.)
- `source_citation` (full text reference)
- `classical_attestation_text` (where available; NULL only on pre-existing rows backfilled from bodha_remediation)

All 4 tantric rows fully attested: source_text=BPHS, source_chapter, source_verse, classical_attestation_text all present.
