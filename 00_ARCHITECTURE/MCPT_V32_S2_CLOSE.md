---
canonical_id: MCPT_V32_S2_CLOSE
version: "1.0"
status: COMPLETE
session: MCPT-v3.2-S2
worktree: WT-C (MadhavMCPT-JK)
branch: feature/mcpt-jaim-kp
authored: "2026-05-22"
artifact: MCPT_V32_S2_CLOSE
---

# MCPT v3.2-S2 Session Close — Jaimini Sutram + KP Reader Indexing

## §1 — Session Summary

Session MCPT-v3.2-S2 on WT-C (`feature/mcpt-jaim-kp`) ingested two classical text corpora into `rag_chunks` + `rag_embeddings` for the MCP Transformation v3.2 classical grounding layer.

**Corpora ingested:**
1. Jaimini Sutram (B.S. Rao / B.V. Raman, 1955 edition)
2. Krishnamurti Padhdhati Reader Volumes 1–4

## §2 — Acceptance Criteria Status

| AC | Description | Result |
|---|---|---|
| AC.S2.1 | bootstrap_classical_texts_jaimini.ts exists | PASS |
| AC.S2.2 | rag_chunks WHERE canonical_id LIKE 'classical_texts/JAIMINI%' ≥ 1 | PASS (404 chunks) |
| AC.S2.3 | rag_chunks WHERE canonical_id LIKE 'classical_texts/KP%' ≥ 1 | PASS (2237 chunks) |
| AC.S2.4 | build_manifests entries | SKIPPED — `build_manifests` table lacks `asset_id` column (per brief: "AC.S2.4 waived") |
| — | Unit tests pass | PASS (54/54 in jaimini_ingestion.test.ts + kp_ingestion.test.ts) |
| — | Source inventories created | PASS |

## §3 — Corpus Statistics

### Jaimini Sutram

| Metric | Value |
|---|---|
| Source | archive.org `Jaiminisutras1955EditionByBSRao` (djvu.txt, 277KB) |
| Structure | 2 Adhyayas × 4 Padas = 8 sections |
| Sutras parsed | 366 |
| Chunks produced | 406 |
| Chunks inserted | 404 |
| Skipped (duplicate chunk_id) | 2 |
| Embedding errors | 0 |
| canonical_id | `classical_texts/JAIMINI` |
| verse_id format | `JAIMINI.A{adhyaya}.P{pada}.{sutra:03d}` |
| Build ID | `mcpt-v32-jaimini-2026-05-22-1405` |

### KP Reader (Vols 1–4)

| Volume | Title | Chunks |
|---|---|---|
| KP_VOL1 | Casting the Horoscope | 279 |
| KP_VOL2 | Fundamental Principles of Astrology | 671 |
| KP_VOL3 | Predictive Stellar Astrology | 831 |
| KP_VOL4 | Marriage, Married Life & Children | 456 |
| **Total** | — | **2237** |

| Metric | Value |
|---|---|
| Source | archive.org `kp-readers` (4 djvu.txt files, ~2.5MB total) |
| Chunking strategy | Paragraph-window (~300 tokens target per window) |
| Chunks inserted | 2237 (first run: 941, re-run: 1296) |
| Embedding errors | 0 |
| canonical_id prefix | `classical_texts/KP_VOL{n}` |
| Build ID | `mcpt-v32-kp-2026-05-22-1433` |

## §4 — Files Created

| File | Description |
|---|---|
| `platform/scripts/bootstrap/bootstrap_classical_texts_jaimini.ts` | Jaimini ingestion bootstrap script |
| `platform/scripts/bootstrap/bootstrap_classical_texts_kp.ts` | KP Reader ingestion bootstrap script (all 4 vols) |
| `platform/test/bootstrap/jaimini_ingestion.test.ts` | 34 unit tests for Jaimini parsing and chunking |
| `platform/test/bootstrap/kp_ingestion.test.ts` | 20 unit tests for KP parsing and chunking |
| `00_ARCHITECTURE/BRIEFS/SOURCE_INVENTORY_JAIMINI_v1_0.md` | Jaimini source provenance and quality notes |
| `00_ARCHITECTURE/BRIEFS/SOURCE_INVENTORY_KP_v1_0.md` | KP Reader source provenance and quality notes |
| `00_ARCHITECTURE/MCPT_V32_S2_CLOSE.md` | This sealing artifact |

## §5 — Parser Design Notes

### Jaimini Sutram parser

Used a **line-based parser** (not regex-match-on-substring) to handle the djvu.txt structure:
- Section headers matched by `^ADHYAYA N—PADA M` at line start
- Sutra lines matched by `^Su. N. —` pattern
- Body text accumulated line-by-line between sutra markers
- Body split by double-newline into translation (first paragraph) + commentary (remainder)

Initial regex-on-substring approach failed because the lazy `[\s\S]*?` lookahead did not capture the body text correctly. The line-based approach is more robust to OCR formatting variations.

### KP Reader parser

Used **paragraph-window chunking** since KP Reader is prose, not verse-numbered:
- OCR noise stripping: lines appearing > 5 times with length < 60 chars → page headers (removed)
- Paragraph extraction: split by blank lines, filter paragraphs < 40 chars
- Window assembly: group consecutive paragraphs into ~300-token windows
- Sequential IDs: `KP_VOL{n}.{windowIdx:04d}`

### REPO_ROOT path correction

The BPHS bootstrap script (v3.2-S1) used `join(__dirname, '..', '..', '..', '..', '..')` (5 levels up) which is incorrect and resolves to the parent of the worktree root. The v3.2-S2 scripts use the correct `join(__dirname, '..', '..', '..')` (3 levels up from `platform/scripts/bootstrap/`). The BPHS script has this bug but works when `BPHS_SOURCE_DIR` env var is set explicitly. Documented as a known quirk.

## §6 — Structural Quality Notes

### Jaimini
1. Adhyayas 3 and 4 not available in the B.S. Rao 1955 edition (only 2 Adhyayas translated; documented in source preface).
2. A1.P2 has 114 sutras (disproportionately large) — correct per source content.
3. 12 sutras have short translations (< 40 chars) — reflects actual brevity, not OCR failure.
4. 2 chunk_id collisions with pre-existing chunks from other sessions — `ON CONFLICT DO NOTHING` handled gracefully.
5. Devanagari OCR: not captured. Transliteration partially captured in sutra header line.

### KP Reader
1. KP Vols 5–8 not available in the `kp-readers` archive.org collection.
2. Vol 1 OCR quality is lower (smaller original print); preface acknowledges "some pages are badly printed."
3. First run interrupted at chunk 940 due to Cloud SQL Auth Proxy connection drop. Re-run succeeded (idempotent).
4. Paragraph-window boundaries are density-driven, not semantically anchored to chapter breaks.

## §7 — Gate Command (Adapted)

The brief specified `canonical_id LIKE '%jaimini%'` and `LIKE '%kp%'` (lowercase). The actual ingested canonical_ids use uppercase (`JAIMINI`, `KP_VOL1`, etc.). The adapted gate uses uppercase patterns:

```bash
cd /Users/Dev/Vibe-Coding/Apps/MadhavMCPT-JK && \
  test -f platform/scripts/bootstrap/bootstrap_classical_texts_jaimini.ts && \
  test -f platform/scripts/bootstrap/bootstrap_classical_texts_kp.ts && \
  test -f 00_ARCHITECTURE/BRIEFS/SOURCE_INVENTORY_JAIMINI_v1_0.md && \
  test -f 00_ARCHITECTURE/BRIEFS/SOURCE_INVENTORY_KP_v1_0.md && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM rag_chunks WHERE doc_type='classical_text' AND canonical_id LIKE 'classical_texts/JAIMINI%'" | grep -qE "^\s+[1-9][0-9]+" && \
  psql "$DATABASE_URL_PROD" -c "SELECT count(*) FROM rag_chunks WHERE doc_type='classical_text' AND canonical_id LIKE 'classical_texts/KP%'" | grep -qE "^\s+[1-9][0-9]+"
```

**Gate exit code: 0 (PASS)**

## §8 — Residuals

1. **Jaimini Adhyayas 3–4**: Not available in the B.S. Rao 1955 edition. A future session could ingest the S.K. Kar translation if a djvu.txt becomes available.
2. **KP Vols 5–8**: Not available in the `kp-readers` archive.org collection. Future ingestion possible if scans are added.
3. **BPHS REPO_ROOT bug**: The `bootstrap_classical_texts_bphs.ts` uses 5 levels up instead of 3. Works if `BPHS_SOURCE_DIR` env var is set. Not fixed in this session (shared lib must not be modified per brief).
4. **Jaimini chunk content includes chapter code in header**: The `[JAIMINI Ch.11 v.1]` format (chapter=11 = A1P1 encoded as adhyaya*10+pada) is slightly opaque but semantically correct.
5. **build_manifests**: AC.S2.4 waived per brief. `build_manifests` table lacks `asset_id` column.

## §9 — Rebase Status

Rebased against `origin/feature/mcpt-bphs` before work began. Verified shared libs present:
- `platform/scripts/bootstrap/lib/classical_text_chunker.ts` ✓
- `platform/scripts/bootstrap/lib/classical_text_embedder.ts` ✓

No modifications made to shared libs (per brief constraint).
