---
artifact: BPHS/OCR_QUALITY_NOTE.md
version: 1.0
status: CURRENT
authored: 2026-05-23
scope: BPHS chapter coverage analysis and OCR quality notes
---

# BPHS — OCR Quality and Chapter Coverage

## Coverage Summary

- **Total chapters in BPHS:** 97 (per R. Santhanam translation)
- **Chapters ingested (rag_chunks):** 88 (Ch. 2–97, with gaps noted below)
- **Coverage:** ~90%+ of text by chapter count; higher by word count (missing chapters are short)
- **Decision:** 88-chapter coverage accepted as final for MCPT. No re-chunk needed.

## Missing Chapters (9)

| Chapter | Subject | Root Cause | Recoverable? |
|---------|---------|------------|--------------|
| Ch. 1 | Introduction / Brahma's teaching to Parasara | OCR: likely merged with Vol 1 front matter | Low |
| Ch. 11 | Results of Planets in Houses | OCR: page merge or absent header | Low |
| Ch. 38 | Kalachakra Dasha | OCR artifact | Low |
| Ch. 78 | Lost Horoscopy (Nashtajatakam) | Regex header pattern mismatch | **HIGH — recoverable** |
| Ch. 85 | Special Lagnas | OCR artifact | Low |
| Ch. 87 | Mrityu Bhaga | OCR artifact | Low |
| Ch. 88 | Saham | OCR artifact | Low |
| Ch. 89 | Various Sphuta | OCR artifact | Low |
| Ch. 91 | Nabhasa Yogas | OCR artifact | Low |

## Chapter 78 (Nashtajatakam) Recovery

Chapter 78 on Lost Horoscopy (Nashtajatakam) is present in the source djvu.txt but
was missed by the chapter-detection regex. The chapter header uses a non-standard
transliteration that the pattern `CHAPTER\s+\d+` doesn't match. Recoverable with
a targeted regex adjustment.

Carry-forward: **RES.bphs.ch78** — MEDIUM priority for v3.7 corpus re-chunk.
Nashtajatakam is a practically important chapter (chart rectification methodology).

## OCR Source Quality

Source: R. Santhanam "Brihat Parasara Hora Sastra" Vol 1 + Vol 2 (archive.org).
OCR quality is good for prose passages but degrades at:
- Sanskrit verse transliterations (mixed script)
- Chapter heading formatting (inconsistent caps/punctuation)
- Diacritical marks (often stripped or mangled by OCR)

The 88-chapter result was produced by MCPT v3.2's `bootstrap_classical_texts_bphs.ts`
chunking pipeline. No manual correction applied. OCR artifacts in verse sections are
reflected in rag_chunks as-is.
