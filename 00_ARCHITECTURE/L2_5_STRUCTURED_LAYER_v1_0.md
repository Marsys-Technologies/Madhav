---
artifact: L2_5_STRUCTURED_LAYER_v1_0
canonical_id: L2_5_STRUCTURED_LAYER
version: 1.0
status: CURRENT
phase: 14D
authored_at: 2026-04-28
authored_by: Claude Sonnet 4.6 (Phase 14D Stream G)
description: Canonical spec for L2.5 structured Postgres tables — MSR signals, UCN sections, CDLM links, CGM nodes/edges, RM resonances
---

# L2.5 Structured Layer — Canonical Specification v1.0

## §1 — Mission

Phase 14D projects the five L2.5 Holistic Synthesis markdown artifacts into structured Postgres tables that the LLM router can query deterministically. Prior to 14D, queries like "find every MSR signal involving Saturn in the 7th house with negative valence" required embedding-search over chunked text. After 14D, they hit indexed tables with exact filters.

The projection is **additive and complementary** to the existing chunk/embedding pipeline:
- **Vector search (`rag_chunks`)** handles semantic similarity queries ("find anything related to X")
- **Structured queries (`l25_*`)** handle deterministic attribute filters ("find all signals where planet=SATURN and house=7")

Both surfaces are served by the same pipeline; the LLM router selects per query type.

## §2 — Source artifacts

All tables are projected from these L2.5 markdown files (authoritative; do not modify):

| Source file | Layer | Rows |
|---|---|---|
| `025_HOLISTIC_SYNTHESIS/MSR_v3_0.md` | L2.5 | 499 signals |
| `025_HOLISTIC_SYNTHESIS/UCN_v4_0.md` | L2.5 | 134 unique sections |
| `025_HOLISTIC_SYNTHESIS/CDLM_v1_1.md` | L2.5 | 81 cells (9×9) |
| `025_HOLISTIC_SYNTHESIS/CGM_v9_0.md` | L2.5 | 234 nodes, 21 edges |
| `025_HOLISTIC_SYNTHESIS/RM_v2_0.md` | L2.5 | 28 resonance pairs |

## §3 — Table schemas

Six live tables + six staging counterparts. All created in migration 018
(`platform/supabase/migrations/018_l2_5_structured.sql`). All prefixed `l25_` to
maintain clean separation from the existing `msr_signals` table (migration 009,
different schema, used by `msr_sql.ts` in the live query pipeline).

### `l25_msr_signals` (499 rows)

| Column | Type | Notes |
|---|---|---|
| `signal_id` | TEXT UNIQUE | `SIG.MSR.001` … `SIG.MSR.499` |
| `signal_number` | INTEGER | 1–499 |
| `name` | TEXT | signal display name |
| `category` | TEXT | `planetary`/`house`/`sign`/`aspect`/`yoga`/`dasha`/`transit`/`cross` |
| `valence` | TEXT | `positive`/`negative`/`neutral`/`mixed`/`context-dependent` |
| `weight` | NUMERIC | optional numeric weight |
| `planets_involved` | TEXT[] | `{SATURN}`, `{VENUS,MERCURY}` — full caps names |
| `houses_involved` | INTEGER[] | `{7}`, `{1,7}` |
| `signs_involved` | TEXT[] | `{LIBRA}` |
| `description` | TEXT | signal body text |
| `source_section` | TEXT | source section reference |
| `build_id` | TEXT | FK→build_manifests |
| `provenance` | JSONB | source file + parsing metadata |

Indexes: `(category, valence)`, GIN on `planets_involved`, GIN on `houses_involved`.

### `l25_ucn_sections` (134 unique sections)

| Column | Type | Notes |
|---|---|---|
| `section_id` | TEXT UNIQUE | `UCN.I.3`, `UCN.II`, `UCN.II.1` |
| `parent_section_id` | TEXT | self-reference for hierarchy |
| `domain` | TEXT | `career`/`relationships`/`wealth`/`spirit`/… |
| `title` | TEXT | section heading |
| `content` | TEXT | section body |
| `derived_from_signals` | TEXT[] | MSR signal IDs cited in body |
| `source_lines` | TEXT | line range in source file |
| `build_id` | TEXT | FK→build_manifests |

Note: Extractor produces 153 sections but 19 have duplicate section_ids (concurrent H2/H3 IDs for
same structural position). ON CONFLICT DO UPDATE collapses to 134 unique rows. This is a
known extractor finding, not a data loss.

Indexes: `(domain)`, GIN on `derived_from_signals`.

### `l25_cdlm_links` (81 rows — complete 9×9 matrix)

| Column | Type | Notes |
|---|---|---|
| `link_id` | TEXT UNIQUE | `CDLM.career.wealth` |
| `from_domain` | TEXT | source domain |
| `to_domain` | TEXT | target domain |
| `link_type` | TEXT | `feeds`/`contradicts`/`reinforces`/`neutral` (actual data values) |
| `strength` | TEXT | `strong`/`moderate`/`weak`/`nil` |
| `source_signals` | TEXT[] | MSR signal IDs driving the link |
| `notes` | TEXT | prose justification |
| `source_section` | TEXT | CDLM cell reference |
| `build_id` | TEXT | FK→build_manifests |

Domains (actual 9): `career`, `children`, `health`, `mind`, `parents`, `relationships`, `spirit`, `travel`, `wealth`.

UNIQUE constraint on `(from_domain, to_domain)`.

### `l25_cgm_nodes` (234 rows)

| Column | Type | Notes |
|---|---|---|
| `node_id` | TEXT UNIQUE | `PLN.SATURN`, `HSE.7`, `SGN.LIBRA` |
| `node_type` | TEXT | `PLN`/`HSE`/`SGN`/`KRK`/`NAK`/`DVS`/`SEN`/`DSH`/`YOG` |
| `display_name` | TEXT | human-readable name |
| `properties` | JSONB | structured properties (house, sign, retrograde, etc.) |
| `source_section` | TEXT | CGM source reference |
| `build_id` | TEXT | FK→build_manifests |

Node type counts: PLN=9, HSE=12, SGN=12, KRK=18, NAK=15, DVS=77, SEN=42, DSH=30, YOG=19.

### `l25_cgm_edges` (21 rows)

| Column | Type | Notes |
|---|---|---|
| `edge_id` | TEXT UNIQUE | `CGM_EDGE_001` |
| `source_node_id` | TEXT | FK→`l25_cgm_nodes.node_id` (plain text, no FK enforced) |
| `target_node_id` | TEXT | FK→`l25_cgm_nodes.node_id` (plain text, no FK enforced) |
| `edge_type` | TEXT | `DISPOSITED_BY`/`NAKSHATRA_LORD_IS`/etc. |
| `strength` | NUMERIC | optional |
| `notes` | TEXT | optional |
| `source_section` | TEXT | CGM source reference |
| `build_id` | TEXT | FK→build_manifests |

Note: CGM v9 cross-domain manifests reference UCN section IDs and synthetic IDs not present in
the CGM node set. 105 of 127 raw edges are orphaned (82.7%) and dropped; only 22 internal
CGM-to-CGM edges survive, minus 1 self-loop (Venus→Venus), leaving 21 live edges. This drop
rate is expected and documented per Phase 14D finding F.05.

Source node IDs and target node IDs are TEXT (no FK) to allow the swap to proceed
without dependency on insertion order.

### `l25_rm_resonances` (28 rows)

| Column | Type | Notes |
|---|---|---|
| `resonance_id` | TEXT UNIQUE | `RM.10.SIG.MSR.001.SIG.MSR.015` |
| `signal_a_id` | TEXT | SIG.MSR.NNN |
| `signal_b_id` | TEXT | SIG.MSR.NNN |
| `resonance_type` | TEXT | `reinforce`/`amplify`/`modulate`/`cancel`/`tension` |
| `strength` | TEXT | `strong`/`moderate`/`weak` |
| `theme` | TEXT | short label |
| `notes` | TEXT | prose |
| `source_section` | TEXT | RM block reference |
| `build_id` | TEXT | FK→build_manifests |

UNIQUE constraint on `(signal_a_id, signal_b_id, resonance_type)`.

## §4 — Pipeline integration

The six structured writers are integrated into the existing 14B orchestrator:

```
pipeline/
  extractors/
    msr_extractor.py      — extract_msr_signals(repo_root) → 499 rows
    ucn_extractor.py      — extract_ucn_sections(repo_root) → 153 rows (134 unique)
    cdlm_extractor.py     — extract_cdlm_links(repo_root) → 81 rows
    cgm_extractor.py      — extract_cgm_nodes(repo_root) → 234 rows
                          — extract_cgm_edges(repo_root, node_ids) → 21 rows
    rm_extractor.py       — extract_rm_resonances(repo_root) → 28 rows
  writers/
    msr_signals_writer.py   — MSRSignalsWriter(IBuildWriter)
    ucn_sections_writer.py  — UCNSectionsWriter(IBuildWriter)
    cdlm_links_writer.py    — CDLMLinksWriter(IBuildWriter)
    cgm_nodes_writer.py     — CGMNodesWriter(IBuildWriter)
    cgm_edges_writer.py     — CGMEdgesWriter(IBuildWriter)
    rm_resonances_writer.py — RMResonancesWriter(IBuildWriter)
```

All six writers follow the IBuildWriter interface (Phase 14C Stream F) with the
staging-then-swap pattern and 0.5× safety gate. Writers are invoked as step 8b in
`pipeline/main.py` after the RAGChunksWriter staging step.

Extractors reuse the existing `rag/chunkers/` parsing logic — no re-implementation.

## §5 — LLM tool surface

Five TypeScript tools at `platform/src/lib/tools/structured/`, registered in
`platform/src/lib/claude/consume-tools.ts`:

| Tool | Query surface | Key inputs |
|---|---|---|
| `query_msr_signals` | `l25_msr_signals` | `category?`, `valence?`, `planet?`, `house?`, `sign?` |
| `query_ucn_section` | `l25_ucn_sections` | `section_id?`, `domain?`, `include_children?` |
| `query_cdlm_link` | `l25_cdlm_links` | `from_domain?`, `to_domain?` |
| `query_cgm` | `l25_cgm_nodes` + `l25_cgm_edges` | `node_id?`, `node_type?`, `include_edges?` |
| `query_resonance` | `l25_rm_resonances` | `signal_id` (required), `resonance_type?` |

Planet names in queries use full caps: `SATURN`, `SUN`, `MOON`, `MARS`, `MERCURY`,
`JUPITER`, `VENUS`, `RAHU`, `KETU`.

CGM node IDs: `PLN.SATURN`, `HSE.7`, `SGN.LIBRA` (not `CGM.PLN.SAT` as the exec brief
suggested — that was an idealized example; actual data matches chunker output).

## §6 — Architectural commitments

1. **Reuse chunker parsing.** Extractors call the existing `rag/chunkers/` functions.
   Chunkers are not modified; only consumed as libraries.
2. **Dual surface.** Both rag_chunks (embedding) and l25_* (structured) are produced
   from the same source files. The router selects per query type.
3. **Provenance per row.** Every row carries `source_section` and `build_id`.
4. **Idempotent migration.** All `CREATE TABLE IF NOT EXISTS`; safe to re-apply.
5. **l25_ prefix.** Separates 14D tables from the existing `msr_signals` table
   (migration 009, different schema, actively used by `msr_sql.ts`).

## §7 — Known findings

| ID | Finding | Status |
|---|---|---|
| F.01 | UCN extractor produces 153 sections but 19 have duplicate section_ids; live count = 134 unique | Documented; deferred to UCN authoring follow-up |
| F.02 | CGM edge orphan rate 82.7% (105/127); cross-domain manifests use UCN section IDs not CGM node IDs | Documented; expected; 21 valid internal edges |
| F.03 | RM blocks RM.13 and RM.25 use numbered-list YAML syntax incompatible with PyYAML strict parse; regex fallback applied | Documented; source authoring follow-up |
| F.04 | RM.26 and RM.27 produce duplicate pair (SIG.MSR.335, SIG.MSR.402, amplify); dedup guard skips second occurrence | Documented; source authoring follow-up |
| F.05 | CGM edge self-loop: Venus→Venus NAKSHATRA_LORD_IS (astrologically correct but structurally excluded) | Documented; dropped |
| F.06 | Exec brief's idealized node/domain naming (`CGM.PLN.SAT`, `self/partner` domains) differs from actual data format | Tools updated with correct naming post-verification |

## §8 — Changelog

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-04-28 | Initial — Phase 14D complete |
