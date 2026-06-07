---
artifact: SCHEMAS/chunker_spec_v1_0.md
version: "1.0"
status: CURRENT
produced_by: Madhav_17_B0
date: 2026-04-24
implements: "PHASE_B_PLAN_v1_0.md §G B.2 Chunker Specification + B.0 Task 12"
---

# MARSYS-JIS Chunker Specification v1.0

Reference for Phase B.2 chunker implementation. Defines the 6 document types ingested
into `rag_chunks`, their chunk unit definitions, boundary detection methods, metadata
requirements, token limits, and stale propagation rules.

---

## §1 — Document Types (6 total)

### Doc-Type 1: MSR Signals (`MSR_v3_0.md`)

| Property | Value |
|---|---|
| `doc_type` | `msr_signal` |
| `layer` | `L2.5` |
| `source_file` | `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` |
| `source_version` | `3.0` |
| **Chunk unit** | One complete SIG.MSR.NNN YAML block |
| **Boundary detection** | Line starts with `SIG.MSR.` (regex: `^SIG\.MSR\.\d{3}:$`) — open; next `SIG.MSR.` line or EOF — close |
| **Maximum tokens** | 800 |
| **Token enforcement** | Hard truncation at 800 tokens with `truncation_note` field added to metadata if triggered |
| **Required metadata** | `signal_id`, `signal_name`, `signal_type`, `domains_affected`, `confidence`, `valence`, `temporal_activation`, `tags` (if present), `provenance` |

**Stale metadata propagation:** If the signal has `is_stale: true` in a future
STALENESS_REGISTER entry, set `is_stale: true` and `stale_reason`, `stale_since` in
`rag_chunks` at next re-ingestion. Stale signals are retained but flagged — they are
not deleted.

**Cross-cutting enforcement on write:** Validate P1 (signal layer = L2.5; no L1 facts
embedded in chunk content), P2 (classical_source present = citation requirement met),
P5 (signal_id must resolve in MSR_v3_0 header registry before write).

---

### Doc-Type 2: UCN Sections (`UCN_v4_0.md`)

| Property | Value |
|---|---|
| `doc_type` | `ucn_section` |
| `layer` | `L2.5` |
| `source_file` | `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md` |
| `source_version` | `4.0` |
| **Chunk unit** | One H2 Part section (e.g., `## Part I — ...` through the next `## Part` or EOF) |
| **Boundary detection** | Line matches `^## ` (H2 heading) — open; next `^## ` or EOF — close. Subsections (H3+) are included within the parent H2 chunk. |
| **Maximum tokens** | 1500 |
| **Token enforcement** | Split at H3 boundary if H2 block exceeds 1500 tokens; each H3 sub-chunk inherits H2 metadata with `sub_chunk_index` |
| **Required metadata** | `part_title`, `part_number`, `domains_mentioned` (extracted), `ucn_version` |

**Stale metadata propagation:** UCN is always current (v4.0 = canonical). No
`is_stale` expected at v4.0. If UCN is ever superseded (v5.0), all v4.0 chunks
set `is_stale: true` with `stale_since` = supersession date.

**Cross-cutting enforcement:** P1 (UCN = L2.5 synthesis; must not contain raw
ephemeris or chart data without L1 citation). P6 (UCN is authoritative; any chunk
that contradicts a domain report surfaces as a UCN-vs-L3 finding for P6 validator).

---

### Doc-Type 3: CDLM Cells (`CDLM_v1_1.md`)

| Property | Value |
|---|---|
| `doc_type` | `cdlm_cell` |
| `layer` | `L2.5` |
| `source_file` | `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md` |
| `source_version` | `1.1` |
| **Chunk unit** | One grid cell: a (row_domain, col_domain) pair with its cell content |
| **Boundary detection** | Parse markdown table row-by-row; each cell in the 9×9 grid is a discrete chunk. Row header = row_domain; column header = col_domain. |
| **Maximum tokens** | 400 |
| **Token enforcement** | Hard truncation at 400 tokens; CDLM cells that exceed this limit must be flagged as `requires_split: true` in metadata |
| **Required metadata** | `row_domain`, `col_domain`, `cell_id` (e.g., `CDLM.career.wealth`), `cdlm_version`, `cell_valence` (positive/negative/neutral/mixed if discernible) |

**Stale metadata propagation:** If CDLM is corrected (v1.2+), existing cell chunks
are marked `is_stale: true` for cells that changed. `stale_reason: "superseded_by_CDLM_v1_2"`.

**Cross-cutting enforcement:** P1 (CDLM cells are L2.5 synthesis, not L1 facts).
P2 (cell content should cite MSR signal IDs where applicable; P2 passes if citation
appears in cell content or metadata).

---

### Doc-Type 4: L1 Fact Groups (`FORENSIC_ASTROLOGICAL_DATA_v8_0.md`)

| Property | Value |
|---|---|
| `doc_type` | `l1_fact` |
| `layer` | `L1` |
| `source_file` | `01_FACTS_LAYER/FORENSIC_ASTROLOGICAL_DATA_v8_0.md` |
| `source_version` | `8.0` |
| **Chunk unit** | One H2 or H3 section (e.g., `## §10 — CHARA KARAKAS`, `### §10.1 Chara Karakas`) |
| **Boundary detection** | Line matches `^## ` (H2) or `^### ` (H3) — open; next heading at same or higher level or EOF — close. H4+ headings are included within the parent H3 chunk. |
| **Maximum tokens** | 1000 |
| **Token enforcement** | Split at H4 boundary if parent H3 exceeds 1000 tokens; sub-chunks inherit section metadata with `sub_chunk_index` |
| **Required metadata** | `section_id` (e.g., `§10.3`), `section_title`, `data_provenance` (extracted from `source:` tags within the section: `swiss_ephemeris\|jagannatha_hora\|manual_derivation\|external_astrologer\|UNKNOWN`) |

**Stale metadata propagation:** L1 is append-only; v8.0 is current. If v9.0 is
produced, all v8.0 chunks are stale unless their section content is unchanged
(content-hash match = skip stale flag; content-hash mismatch = `is_stale: true`).

**Cross-cutting enforcement:** P1 (L1 chunks MUST NOT contain interpretive content;
any sentence containing evaluative language triggers a P1 violation flag). P4
(if section contains `[EXTERNAL_COMPUTATION_REQUIRED]`, the chunk's metadata must
carry `external_computation_pending: true`).

---

### Doc-Type 5: Domain Report Parts (`03_DOMAIN_REPORTS/*.md`)

| Property | Value |
|---|---|
| `doc_type` | `domain_report` |
| `layer` | `L3` |
| `source_file` | `03_DOMAIN_REPORTS/<filename>.md` |
| `source_version` | per file frontmatter |
| **Chunk unit** | One H2 Part section (e.g., `## Part I — ...`) |
| **Boundary detection** | Line matches `^## Part` — open; next `^## Part` or EOF — close. Subsections (H3+) included within the Part chunk. |
| **Maximum tokens** | 1500 |
| **Token enforcement** | Split at H3 boundary if Part block exceeds 1500 tokens; sub-chunks carry `parent_part` metadata |
| **Required metadata** | `report_name` (filename), `part_title`, `part_number`, `domain` (from filename/frontmatter), `report_version` |

**Stale metadata propagation:** When a domain report is superseded (v2.0 > v1.0),
all v1.0 Part chunks are marked `is_stale: true` with `stale_since` = supersession
session date. The new version's chunks are ingested fresh. Stale L3 chunks are
retained for historical retrieval but filtered from primary discovery passes.

**Cross-cutting enforcement:** P1 (L3 interpretive — must cite L2.5 UCN/MSR/CDLM;
citation check passes if report section references at least one MSR signal ID or UCN
section). P3 (domain report queries must route through L2.5 first per Whole-Chart-Read).

---

### Doc-Type 6: CGM Nodes (`CGM_v9_0.md`, after B.3.5)

| Property | Value |
|---|---|
| `doc_type` | `cgm_node` |
| `layer` | `L2.5` |
| `source_file` | `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` |
| `source_version` | `9.0` (post-B.3.5) |
| **Chunk unit** | One CGM node property dict (planet node, house node, yoga node, domain node, etc.) |
| **Boundary detection** | Detect node blocks per CGM_v9_0 format — each node entry begins with `node_id:` key (YAML or markdown list item with node_id). |
| **Maximum tokens** | 600 |
| **Token enforcement** | If node block exceeds 600 tokens, truncate at the longest complete property boundary; add `truncation_note` |
| **Required metadata** | `node_id`, `node_type`, `node_label`, `domains`, `karaka_system` (7-karaka|8-karaka|both; required for KRK-type nodes) |

**Stale metadata propagation:** CGM_v9_0 is the first version produced post-B.3.5.
CGM_v2_0 nodes are deprecated at that point; their chunks (if ingested) are marked
`is_stale: true`. CGM_v9_0 nodes supersede per matching `node_id`.

**Cross-cutting enforcement:** P1 (CGM = L2.5 synthesis; node property values must not
contain raw chart positions without L1 citation). For KRK-type nodes: the `karaka_system`
field must be set; 7-karaka-alternative nodes carry both 7-karaka and 8-karaka readings
per GAP_13_RESOLUTION_v1_0.md §3.

---

## §2 — Cross-Cutting Rules (All Doc-Types)

### §2.1 — P1 Layer-Separation Enforcement

Every chunk write passes through `validators/p1_layer_separation.py`. A chunk fails P1 if:
- Layer is `L1` but content contains evaluative or interpretive language (heuristics:
  presence of `strong`, `weak`, `excellent`, `indicates`, `suggests` in non-quoted text).
- Layer is `L2+` but content lacks any reference to an L1 source ID
  (`PLN.`, `HSE.`, `SGN.`, `EVT.`, `SIG.MSR.`, etc.).

P1 failures block the chunk write and emit a validation error to the ingestion log.

### §2.2 — P2 Citation Enforcement

Every L2+ chunk must carry at least one citation in its content or metadata to a source
that can be traced to `FORENSIC_ASTROLOGICAL_DATA_v8_0.md` or a classical text with a
section reference. Chunks that fail P2 are written with `citation_valid: false` in
metadata and flagged for human review in `rag_feedback`.

### §2.3 — P5 Signal ID Resolution

For `msr_signal` chunks: the `signal_id` in metadata must resolve against the MSR_v3_0
signal header registry (verified at ingest time by reading the MSR file's SIG.MSR.NNN
entry list). Unresolvable signal IDs block write.

For all other doc-types: any SIG.MSR.NNN ID appearing in chunk content is validated against
the same registry. Dangling signal ID references emit a validation warning.

### §2.4 — `is_stale` Propagation

The `is_stale` flag in `rag_chunks` flows from the STALENESS_REGISTER (when created in B.1)
and from source-file version supersession events. The ingestion pipeline checks the
STALENESS_REGISTER on every re-ingestion run. A stale chunk:
- Remains in the database (not deleted).
- Has `is_stale: true`, `stale_reason`, `stale_since` populated.
- Is excluded from primary retrieval passes unless the query plan explicitly requests
  historical data (`include_stale: true` retrieval parameter).
- Is surfaced by the P4 validator if it is the only available chunk for a required node.

### §2.5 — Token Counting

Token counts use the `tiktoken` library with the `cl100k_base` encoding (consistent with
Voyage-3-large input tokenization approximation). The `token_count` field in `rag_chunks`
is the tokenized count of the `content` field only (not metadata).

---

*End of chunker_spec_v1_0.md — produced Madhav_17_B0 2026-04-24.*
*Reference implementation: Phase B.2. This document is the authoritative spec.*
