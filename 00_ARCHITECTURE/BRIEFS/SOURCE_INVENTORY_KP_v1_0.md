---
canonical_id: SOURCE_INVENTORY_KP
version: "1.0"
status: CURRENT
authored: "2026-05-22"
session: "MCPT-v3.2-S2 (WT-C)"
---

# Source Inventory: KP Reader (Volumes 1–4)

## §1 — Work Identification

| Field | Value |
|---|---|
| Work | Krishnamurti Padhdhati (KP) Reader Series |
| Author | Prof. K.S. Krishnamurti (Sothida Mannan, Jyotish Marthand) |
| Publisher | Krishman & Co., Chennai (various editions) |
| System | Stellar Astrology (Krishnamurti Padhdhati) — sub-lord and Nakshatra-based |

## §2 — Source Acquisition

| Volume | Title | Archive.org URL | Local Filename | File Size |
|---|---|---|---|---|
| Vol 1 | Casting the Horoscope | `kp-readers/J_KP reader_1_casting the horoscope_djvu.txt` | `kp_reader_vol1_djvu.txt` | 291,548 bytes |
| Vol 2 | Fundamental Principles of Astrology | `kp-readers/J_KP reader_2_fundamental Principles of Astrology_djvu.txt` | `kp_reader_vol2_djvu.txt` | 749,169 bytes |
| Vol 3 | Predictive Stellar Astrology | `kp-readers/J_KP reader_3_Predictive Stellar Astrology_djvu.txt` | `kp_reader_vol3_djvu.txt` | 966,177 bytes |
| Vol 4 | Marriage, Married Life & Children | `kp-readers/J_KP reader_4_Marriage-married-Life-Children_djvu.txt` | `kp_reader_vol4_djvu.txt` | 487,125 bytes |

- **Archive.org identifier**: `kp-readers`
- **Acquisition date**: 2026-05-22
- **Acquisition method**: Direct URL `https://archive.org/download/kp-readers/<filename>` with URL encoding

## §3 — Text Structure

KP Reader is **prose-based** (not verse/sutra numbered). The texts are organized as topic chapters with conceptual headings.

Structure characteristics:
- Page headers (e.g., "KRISHNAMURTI PADHDHATI") repeat every 2–4 pages
- ALL-CAPS section titles interspersed with prose content
- Content is explanatory prose, worked examples, case studies, and astrological rules

**Chunking strategy**: Paragraph-window chunking (not verse-level):
- OCR noise stripping removes lines appearing more than 5 times in the text (page headers)
- Remaining text split by blank lines into paragraphs (≥ 40 chars)
- Consecutive paragraphs grouped into windows of ≈ 300 tokens
- Each window assigned a sequential ID: `KP_VOL{n}.{idx:04d}`

## §4 — Ingestion Results

| Volume | Windows | Chunks | canonical_id |
|---|---|---|---|
| Vol 1 | 271 | 279 | `classical_texts/KP_VOL1` |
| Vol 2 | 671 | 671 | `classical_texts/KP_VOL2` |
| Vol 3 | 818 | 831 | `classical_texts/KP_VOL3` |
| Vol 4 | 443 | 456 | `classical_texts/KP_VOL4` |
| **Total** | **2203** | **2237** | — |

| Metric | Value |
|---|---|
| Total chunks produced | 2237 |
| Average tokens per chunk | ~250 |
| verse_id format | `KP_VOL{n}.{window:04d}` |
| Build ID | `mcpt-v32-kp-2026-05-22-1405` (approx) |

## §5 — Structural Quality Notes

1. **No sutra/verse numbering**: KP Reader uses prose chapters rather than numbered aphorisms. The paragraph-window approach assigns sequential IDs without semantic chapter awareness. This means the chunk boundaries are content-density-driven, not semantically anchored to chapter boundaries.

2. **OCR quality**: The djvu.txt files have significant OCR noise, especially in Vol 1 (small original print, scan quality). Common artifacts: character substitution (e.g., "Horos sc )pe" for "Horoscope"), run-together words, line-break artifacts. OCR quality improves in Vols 2–4. The overall text is semantically usable despite character-level noise.

3. **Page header noise**: "KRISHNAMURTI PADHDHATI" appears on virtually every page as a running header. The noise-stripping algorithm (removes lines appearing > 5 times with length < 60) effectively removes these. The chapter-title versions (appearing once per topic) are preserved.

4. **Vol 1 lower yield**: Vol 1 (291KB file → 279 chunks vs. ~7.5 chunks/KB for other volumes) has lower text density due to scan quality and OCR noise on the smaller-format print. The preface note in the file itself says "some pages are badly printed so is the PDF...sorry" — this is a known quality limitation of the archive.org scan.

5. **Volumes 5–8 not ingested**: KP published 8 volumes total. Only Vols 1–4 are available in the `kp-readers` archive.org collection. Vols 5–8 cover Horary astrology, medical astrology, electional astrology, and miscellaneous — relevant for future ingestion if scans become available.

6. **Work keys**: `KP_VOL1` through `KP_VOL4` (no period, underscore-separated). These are stored in both `canonical_id` (as `classical_texts/KP_VOL1` etc.) and `metadata->>'work'`.

## §6 — build_manifests

Skipped per brief specification (AC.S2.4 waived — `build_manifests` table lacks `asset_id` column).
