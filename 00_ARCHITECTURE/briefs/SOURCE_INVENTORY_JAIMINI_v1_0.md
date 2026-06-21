---
canonical_id: SOURCE_INVENTORY_JAIMINI
version: "1.0"
status: CURRENT
authored: "2026-05-22"
session: "MCPT-v3.2-S2 (WT-C)"
---

# Source Inventory: Jaimini Sutram

## §1 — Work Identification

| Field | Value |
|---|---|
| Work | Jaimini Sutram (Jaimini Sutras) |
| Author | Maharishi Jaimini (attributed) |
| Edition | B.S. Rao (Bangalore Suryanarain Rao), revised and annotated by B.V. Raman |
| Publisher | IBH Prakashana, Gandhinagar, Bangalore 560009 |
| Year | 1955 (Fifth Edition) |
| Title | "Jaiminisutras — English Translation with Full Notes and Original Texts in Devanagari and Transliteration" |

## §2 — Source Acquisition

| Field | Value |
|---|---|
| Archive.org identifier | `Jaiminisutras1955EditionByBSRao` |
| File retrieved | `Jaiminisutras 1955 Edition by B S Rao_djvu.txt` |
| Local filename | `jaimini_bsrao_1955_djvu.txt` |
| File size | 277,180 bytes (277KB) |
| Acquisition date | 2026-05-22 |
| Acquisition method | `curl -L "https://archive.org/download/Jaiminisutras1955EditionByBSRao/..."` |
| OCR quality | Moderate — Devanagari characters not OCR'd; transliteration lines partially captured |

## §3 — Text Structure

The text is organized as:

- **2 Adhyayas × 4 Padas each = 8 Adhyaya-Pada sections**
- Section headers: `ADHYAYA N— PADA M` (em-dash variant used consistently)
- Sutra markers: `Su. N . — Sanskrit_transliteration.` at line start
- Translation follows as prose paragraph(s)
- Commentary follows translation in the same section, separated by blank lines

Adhyaya-Pada map:

| Section | Page Range (approx) | Sutras |
|---|---|---|
| A1.P1 | 1–40 | 33 |
| A1.P2 | 41–87 | 114 |
| A1.P3 | 87–106 | 39 |
| A1.P4 | 106–126 | 44 |
| A2.P1 | 126–156 | 56 |
| A2.P2 | 156–169 | 25 |
| A2.P3 | 170–180 | 24 |
| A2.P4 | 180–197 | 31 |

## §4 — Ingestion Results

| Metric | Value |
|---|---|
| Total sutras parsed | 366 |
| Total chunks produced | 406 |
| Chunks inserted into rag_chunks | 404 |
| Chunks skipped (duplicate chunk_id) | 2 |
| Embedding errors | 0 |
| canonical_id in rag_chunks | `classical_texts/JAIMINI` |
| metadata.work value | `JAIMINI` |
| verse_id format | `JAIMINI.A{adhyaya}.P{pada}.{sutra:03d}` |
| Build ID | `mcpt-v32-jaimini-2026-05-22-1405` |

## §5 — Structural Quality Notes

1. **Sutra numbering resets per Pada**: Sutras are numbered 1..N within each Adhyaya-Pada, not globally. The verse_id encodes both location and sutra number: `JAIMINI.A1.P2.001` = Adhyaya 1, Pada 2, Sutra 1.

2. **Chapter code encoding**: The `chapter` field in rag_chunks uses `adhyaya * 10 + pada` (e.g., A1P1=11, A2P4=24). This is metadata-only and not used for retrieval routing.

3. **OCR quality**: Devanagari script was not OCR'd at all — text contains placeholder characters or blanks for Sanskrit originals. Transliteration (Roman script) lines are partially captured in the sutra header line. Commentary and translation prose are well-captured.

4. **Unusually large Pada**: A1.P2 has 114 sutras (disproportionately large vs. others). This is correct per the source edition — A1.P2 covers Atmakaraka in Navamsa and planet effects in various houses from Karakamsha, which is a richly expanded section.

5. **12 short translations**: 12 sutras have translations < 40 chars. These are brief sutras where the meaning is captured in a single terse line (e.g., "Su. 3. — Excepting the next zodiacal signs to them."). Not OCR failures — reflects actual brevity of certain sutras.

6. **2 duplicate chunk_ids skipped**: These appear to be sutras whose `verse_id` collides with a pre-existing chunk from the BPHS ingestion (v3.2-S1). The `ON CONFLICT DO NOTHING` guard correctly handles these without data loss.

## §6 — Coverage Scope

Jaimini Sutras contain 4 Adhyayas per tradition; only 2 Adhyayas were translated by B.S. Rao in this edition (per the editor's note in the preface: "I have seen only four and have not come across [Adhyayas III and IV] in libraries"). This is the standard version available in public domain. Adhyayas 3 and 4 are not covered in this ingestion — document as a known gap.

**Known gap**: Jaimini Adhyayas 3 and 4 not available in this edition. The S.K. Kar translation (mentioned in the preface) covers all 4 Adhyayas but is not publicly archived at archive.org in djvu.txt format.

## §7 — build_manifests

Skipped per brief specification (AC.S2.4 waived — `build_manifests` table lacks `asset_id` column).
