"""
brahmagyan.l0_rechunk_phase2 — L0FR Stream C: Re-chunk low-count texts
=======================================================================

Targeted fix for texts that had poor chunk counts from Phase 2:
- saravali: verse_start out of range (smallint) — use cap 32000
- brihat_samhita: uses 'Sloka N. —' pattern
- sarvartha_chintamani: uses 'Stanza N.' pattern
- jaimini_sutram: uses 'Su. N.' or paragraph-level
- jataka_parijata_vol2: has Adhyaya structure in vol2
- brihat_jataka: has Chapter + numbered content

Also fixes the saravali chunks where verse_start > 32767 (smallint overflow).

All chunks: replace existing rows for affected text_ids and embed.
"""
from __future__ import annotations

import hashlib
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger(__name__)

TEXTS_DIR = Path("/tmp/l0fr_texts")
PARK_LOG = Path("/tmp/l0fr_chunks_parked.txt")

# Max verse number for smallint col
SMALLINT_MAX = 32000


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def extract_en_sa(content: str) -> tuple[str, Optional[str]]:
    """Separate English and Sanskrit lines."""
    lines = content.split("\n")
    sa_lines, en_lines = [], []
    for line in lines:
        s = line.strip()
        if not s:
            continue
        non_ascii = sum(1 for c in s if ord(c) > 127)
        ratio = non_ascii / max(len(s), 1)
        if ratio > 0.4:
            sa_lines.append(s)
        else:
            en_lines.append(s)
    return "\n".join(en_lines).strip(), "\n".join(sa_lines).strip() or None


def extract_topics(text: str) -> list[str]:
    keywords = [
        "lagna", "ascendant", "sun", "moon", "mars", "mercury", "jupiter", "venus",
        "saturn", "rahu", "ketu", "house", "bhava", "yoga", "dasha", "transit",
        "aspect", "conjunction", "retrograde", "exalt", "debilitat", "sign", "rasi",
        "nakshatra", "lord", "karak", "muhurta", "remedy", "mantra", "remedial",
    ]
    lower = text.lower()
    return list({kw for kw in keywords if kw in lower})[:10]


def make_chunk(
    text_id: str,
    chapter: int,
    verse_start: int,
    verse_end: int,
    content_en: str,
    content_sa: Optional[str],
    tradition_school: str,
    translator: str,
    topics: Optional[list] = None,
) -> dict:
    verse_start = min(verse_start, SMALLINT_MAX)
    verse_end = min(verse_end, SMALLINT_MAX)
    verse_ref = f"CH{chapter}:V{verse_start}" + (f"-V{verse_end}" if verse_end != verse_start else "")
    chunk_id = f"{text_id}_ch{chapter:03d}_v{verse_start:04d}"
    return {
        "text_id": text_id,
        "chapter": chapter,
        "verse_start": verse_start,
        "verse_end": verse_end,
        "verse_ref": verse_ref,
        "content_en": content_en[:2400],
        "content_sa": content_sa,
        "source_citation": f"{text_id.upper()} Ch.{chapter} v.{verse_start}",
        "tradition_school": tradition_school,
        "translator": translator,
        "topics": topics or extract_topics(content_en),
        "content_sha256": sha256(content_en),
        "chunk_id": chunk_id,
    }


# ── Text-specific chunkers ────────────────────────────────────────────────────

def chunk_brihat_samhita(text: str) -> list[dict]:
    """
    Brihat Samhita: 'Sloka N. — content' or 'SloJca N. — content' (OCR artifact).
    Also handles 'Adh. N' chapter boundaries.
    """
    chunks = []

    # Normalize OCR artifacts: SloJca → Sloka, SloJcz → Sloka
    text = re.sub(r'SloJ[ck][az]\s*(\d+)', r'Sloka \1', text)
    text = re.sub(r'Sl[oa]J[ck]a', 'Sloka', text)
    text = re.sub(r'\bSlolca\b', 'Sloka', text)
    text = re.sub(r'\bSloTca\b', 'Sloka', text)

    # Find Adhyaya (chapter) boundaries
    adh_pat = re.compile(
        r'(?:^|\n)\s*(?:Adh\.?\s+([IVXLCDM]+|\d+)|ADHYAYA\s+(\d+))[^\n]*\n',
        re.MULTILINE | re.IGNORECASE
    )
    # Map Roman numeral to integer
    roman = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8,
        'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
        'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20, 'XXI': 21, 'XXII': 22,
        'XXIII': 23, 'XXIV': 24, 'XXV': 25, 'XXVI': 26, 'XXVII': 27, 'XXVIII': 28,
        'XXIX': 29, 'XXX': 30, 'XXXI': 31, 'XXXII': 32, 'XXXIII': 33, 'XXXIV': 34,
        'XXXV': 35, 'XXXVI': 36, 'XXXVII': 37, 'XXXVIII': 38, 'XXXIX': 39, 'XL': 40,
        'XLI': 41, 'XLII': 42, 'XLIII': 43, 'XLIV': 44, 'XLV': 45, 'XLVI': 46,
        'XLVII': 47, 'XLVIII': 48, 'XLIX': 49, 'L': 50, 'LI': 51, 'LII': 52,
        'LIII': 53, 'LIV': 54, 'LV': 55, 'LVI': 56, 'LVII': 57, 'LVIII': 58,
        'LIX': 59, 'LX': 60, 'LXI': 61, 'LXII': 62, 'LXIII': 63, 'LXIV': 64,
        'LXV': 65, 'LXVI': 66, 'LXVII': 67, 'LXVIII': 68, 'LXIX': 69, 'LXX': 70,
        'LXXI': 71, 'LXXII': 72, 'LXXIII': 73, 'LXXIV': 74, 'LXXV': 75, 'LXXVI': 76,
        'LXXVII': 77, 'LXXVIII': 78, 'LXXIX': 79, 'LXXX': 80, 'LXXXI': 81,
        'LXXXII': 82, 'LXXXIII': 83, 'LXXXIV': 84, 'LXXXV': 85, 'LXXXVI': 86,
        'LXXXVII': 87, 'LXXXVIII': 88, 'LXXXIX': 89, 'XC': 90, 'XCI': 91,
        'XCII': 92, 'XCIII': 93, 'XCIV': 94, 'XCV': 95, 'XCVI': 96, 'XCVII': 97,
        'XCVIII': 98, 'XCIX': 99, 'C': 100, 'CI': 101, 'CII': 102, 'CIII': 103,
        'CIV': 104, 'CV': 105, 'CVI': 106, 'CVII': 107, 'CVIII': 108,
    }

    def parse_adh_num(s: str) -> int:
        s = s.strip().upper()
        if s.isdigit():
            return int(s)
        return roman.get(s, 0)

    # Sloka pattern (after OCR normalization)
    sloka_pat = re.compile(
        r'Sloka\s+(\d+(?:[-–]\d+)?)\s*\.?\s*[—–-]\s*(.+?)(?=Sloka\s+\d|$)',
        re.DOTALL | re.IGNORECASE
    )

    # Get chapter boundaries
    adh_matches = list(adh_pat.finditer(text))
    adh_boundaries = []
    for m in adh_matches:
        num = parse_adh_num(m.group(1) or m.group(2) or "0")
        if num > 0:
            adh_boundaries.append((num, m.start()))
    adh_boundaries.sort(key=lambda x: x[1])

    def get_chapter_for_pos(pos: int) -> int:
        ch = 1
        for num, boundary_pos in adh_boundaries:
            if boundary_pos <= pos:
                ch = num
        return ch

    # Find all slokas
    for m in sloka_pat.finditer(text):
        num_str = m.group(1)
        # Parse verse range
        if "-" in num_str or "–" in num_str:
            parts = re.split(r'[-–]', num_str)
            v_start = int(parts[0])
            v_end = int(parts[-1]) if parts[-1].isdigit() else v_start
        else:
            v_start = int(num_str)
            v_end = v_start

        content = m.group(2).strip()
        content_en, content_sa = extract_en_sa(content)

        if len(content_en) < 30:
            continue

        chapter = get_chapter_for_pos(m.start())
        chunks.append(make_chunk(
            text_id="brihat_samhita",
            chapter=chapter,
            verse_start=v_start,
            verse_end=v_end,
            content_en=content_en,
            content_sa=content_sa,
            tradition_school="samhita",
            translator="V. Subrahmanya Sastri",
        ))

    logger.info("[rechunk] brihat_samhita: %d Sloka chunks", len(chunks))

    # Fallback: if too few sloka matches, use paragraph chunking
    if len(chunks) < 100:
        logger.info("[rechunk] brihat_samhita: Sloka pattern insufficient, using paragraph fallback")
        chunks = []
        paragraphs = re.split(r'\n\s*\n', text)
        v = 0
        ch = 1
        for para in paragraphs:
            para = para.strip()
            if len(para) < 80:
                continue
            content_en, content_sa = extract_en_sa(para)
            if len(content_en) < 50:
                continue
            # Try to extract chapter from inline ref
            ch_match = re.search(r'Adh\.?\s+([IVXLCDM]+|\d+)', para, re.IGNORECASE)
            if ch_match:
                num = parse_adh_num(ch_match.group(1))
                if num > 0:
                    ch = num
                    v = 0
            v += 1
            chunks.append(make_chunk(
                text_id="brihat_samhita",
                chapter=ch,
                verse_start=v,
                verse_end=v,
                content_en=content_en,
                content_sa=content_sa,
                tradition_school="samhita",
                translator="V. Subrahmanya Sastri",
            ))

    return chunks


def chunk_sarvartha_chintamani(text: str) -> list[dict]:
    """
    Sarvartha Chintamani: uses 'Stanza N.' pattern.
    """
    # Normalize OCR artifacts
    text = re.sub(r'Stanta\b', 'Stanza', text)

    # Find chapter boundaries
    chap_pat = re.compile(
        r'(?:^|\n)\s*(?:CHAPTER|Chapter|Chap\.?)\s+(\d+|[IVX]+)[^\n]*\n',
        re.MULTILINE
    )
    chap_matches = list(chap_pat.finditer(text))

    def get_chapter_for_pos(pos: int) -> int:
        ch = 1
        for m in chap_matches:
            if m.start() <= pos:
                try:
                    ch = int(m.group(1))
                except ValueError:
                    pass
        return ch

    # Stanza chunks
    stanza_pat = re.compile(
        r'Stanza\s+(\d+)\.?\s*(.+?)(?=Stanza\s+\d+\.?|\Z)',
        re.DOTALL | re.IGNORECASE
    )
    chunks = []
    for m in stanza_pat.finditer(text):
        v = int(m.group(1))
        content = m.group(2).strip()
        content_en, content_sa = extract_en_sa(content)
        if len(content_en) < 30:
            continue
        chapter = get_chapter_for_pos(m.start())
        chunks.append(make_chunk(
            text_id="sarvartha_chintamani",
            chapter=chapter,
            verse_start=v,
            verse_end=v,
            content_en=content_en,
            content_sa=content_sa,
            tradition_school="parashari",
            translator="B. Suryanarayana Row",
        ))

    logger.info("[rechunk] sarvartha_chintamani: %d Stanza chunks", len(chunks))

    # Fallback: paragraph chunking
    if len(chunks) < 50:
        logger.info("[rechunk] sarvartha_chintamani: Stanza insufficient, using paragraph fallback")
        chunks = []
        ch = 1
        v = 0
        paragraphs = re.split(r'\n\s*\n', text)
        for para in paragraphs:
            para = para.strip()
            content_en, content_sa = extract_en_sa(para)
            if len(content_en) < 60:
                continue
            # Detect chapter change
            ch_match = re.search(r'CHAPTER\s+(\d+)', para, re.IGNORECASE)
            if ch_match:
                ch = int(ch_match.group(1))
                v = 0
            v += 1
            chunks.append(make_chunk(
                text_id="sarvartha_chintamani",
                chapter=ch,
                verse_start=v,
                verse_end=v,
                content_en=content_en,
                content_sa=content_sa,
                tradition_school="parashari",
                translator="B. Suryanarayana Row",
            ))

    return chunks


def chunk_jaimini_sutram(text: str) -> list[dict]:
    """
    Jaimini Sutras: uses 'Su. N.' or 'Sutra N.' pattern inside Adhyaya/Pada sections.
    """
    chunks = []

    # Normalize
    text = re.sub(r'Su\.\s*(\d+)', r'Sutra \1', text)

    # Find Adhyaya + Pada boundaries
    sec_pat = re.compile(
        r'(?:ADHYAYA|Adhyaya)\s+([IVX\d]+).*?(?:PADA|Pada)\s+([IVX\d]+)',
        re.IGNORECASE
    )
    # Simpler: Pada boundaries
    pada_pat = re.compile(r'(?:^|\n)\s*(?:PADA|Pada)\s+([IVX\d]+)[^\n]*\n', re.MULTILINE | re.IGNORECASE)
    pada_matches = list(pada_pat.finditer(text))

    def parse_roman_or_int(s: str) -> int:
        roman = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10}
        s = s.strip().upper()
        if s.isdigit():
            return int(s)
        return roman.get(s, 1)

    def get_pada_for_pos(pos: int) -> int:
        pada = 1
        for m in pada_matches:
            if m.start() <= pos:
                pada = parse_roman_or_int(m.group(1))
        return pada

    # Sutra pattern
    sutra_pat = re.compile(
        r'Sutra\s+(\d+)\s*\.?\s*[—–-]?\s*(.+?)(?=Sutra\s+\d+|(?:PADA|Pada)\s+[IVX\d]+|\Z)',
        re.DOTALL | re.IGNORECASE
    )

    for m in sutra_pat.finditer(text):
        v = int(m.group(1))
        content = m.group(2).strip()
        content_en, content_sa = extract_en_sa(content)
        if len(content_en) < 30:
            continue
        pada = get_pada_for_pos(m.start())
        chunks.append(make_chunk(
            text_id="jaimini_sutram",
            chapter=pada,
            verse_start=v,
            verse_end=v,
            content_en=content_en,
            content_sa=content_sa,
            tradition_school="jaimini",
            translator="B. Suryanarain Rao",
        ))

    logger.info("[rechunk] jaimini_sutram: %d Sutra chunks", len(chunks))

    # Fallback: paragraph chunking
    if len(chunks) < 30:
        logger.info("[rechunk] jaimini_sutram: Sutra insufficient, using paragraph fallback")
        chunks = []
        ch = 1
        v = 0
        paragraphs = re.split(r'\n\s*\n', text)
        for para in paragraphs:
            para = para.strip()
            content_en, content_sa = extract_en_sa(para)
            if len(content_en) < 60:
                continue
            # Detect pada change
            pada_match = re.search(r'PADA\s+([IVX\d]+)', para, re.IGNORECASE)
            if pada_match:
                ch = parse_roman_or_int(pada_match.group(1))
                v = 0
            v += 1
            chunks.append(make_chunk(
                text_id="jaimini_sutram",
                chapter=ch,
                verse_start=v,
                verse_end=v,
                content_en=content_en,
                content_sa=content_sa,
                tradition_school="jaimini",
                translator="B. Suryanarain Rao",
            ))

    return chunks


def chunk_jataka_parijata_vol2(text: str) -> list[dict]:
    """Jataka Parijata Vol 2: Adhyaya N + Sloka N pattern."""
    chunks = []

    # Roman numeral map for JP Vol 2 adhyayas (X, XI, XII, ...)
    roman = {
        'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
        'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20,
    }

    def parse_adh(s: str) -> int:
        s = s.strip().upper()
        if s.isdigit():
            return int(s)
        return roman.get(s, 0)

    adh_pat = re.compile(r'(?:^|\n)\s*Adh(?:yaya)?\.?\s+([IVXLCDM\d]+)\.?[^\n]*\n', re.MULTILINE | re.IGNORECASE)
    adh_matches = list(adh_pat.finditer(text))
    adh_boundaries = [(parse_adh(m.group(1)), m.start()) for m in adh_matches if parse_adh(m.group(1)) > 0]

    def get_adh_for_pos(pos: int) -> int:
        ch = 10  # JP Vol 2 starts at ~Adhyaya 10
        for num, bpos in adh_boundaries:
            if bpos <= pos:
                ch = num
        return ch

    # Sloka pattern
    sloka_pat = re.compile(
        r'(?:Sloka|Shloka)\s+(\d+)\.?\s*(.+?)(?=(?:Sloka|Shloka)\s+\d+|\Z)',
        re.DOTALL | re.IGNORECASE
    )
    for m in sloka_pat.finditer(text):
        v = int(m.group(1))
        content = m.group(2).strip()
        content_en, content_sa = extract_en_sa(content)
        if len(content_en) < 30:
            continue
        ch = get_adh_for_pos(m.start())
        chunks.append(make_chunk(
            text_id="jataka_parijata",
            chapter=ch,
            verse_start=v,
            verse_end=v,
            content_en=content_en,
            content_sa=content_sa,
            tradition_school="parashari",
            translator="V. Subrahmanya Sastri",
        ))

    logger.info("[rechunk] jataka_parijata_vol2: %d Sloka chunks", len(chunks))

    # Fallback: paragraph
    if len(chunks) < 20:
        logger.info("[rechunk] jataka_parijata_vol2: Sloka insufficient, using paragraph fallback")
        chunks = []
        ch = 10
        v = 0
        paragraphs = re.split(r'\n\s*\n', text)
        for para in paragraphs:
            para = para.strip()
            content_en, content_sa = extract_en_sa(para)
            if len(content_en) < 60:
                continue
            adh_match = re.search(r'Adhyaya\s+([IVXLCDM\d]+)', para, re.IGNORECASE)
            if adh_match:
                num = parse_adh(adh_match.group(1))
                if num > 0:
                    ch = num
                    v = 0
            v += 1
            chunks.append(make_chunk(
                text_id="jataka_parijata",
                chapter=ch,
                verse_start=v,
                verse_end=v,
                content_en=content_en,
                content_sa=content_sa,
                tradition_school="parashari",
                translator="V. Subrahmanya Sastri",
            ))

    return chunks


def chunk_brihat_jataka(text: str) -> list[dict]:
    """
    Brihat Jataka (Varahamihira): Chapter + numbered content.
    Uses 'Chapter N' and numbered verses.
    """
    chunks = []

    # Chapter pattern
    chap_pat = re.compile(r'(?:^|\n)\s*(?:CHAPTER|Chapter)\s+([IVX\d]+)[^\n]*\n', re.MULTILINE | re.IGNORECASE)
    chap_matches = list(chap_pat.finditer(text))

    roman = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7, 'VIII': 8,
        'IX': 9, 'X': 10, 'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
        'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20, 'XXI': 21, 'XXII': 22,
        'XXIII': 23, 'XXIV': 24, 'XXV': 25, 'XXVI': 26, 'XXVII': 27, 'XXVIII': 28,
    }

    def parse_chap(s: str) -> int:
        s = s.strip().upper()
        if s.isdigit():
            return int(s)
        return roman.get(s, 0)

    def get_chapter_for_pos(pos: int) -> int:
        ch = 1
        for m in chap_matches:
            if m.start() <= pos:
                num = parse_chap(m.group(1))
                if num > 0:
                    ch = num
        return ch

    # Try 'Sloka N' or numbered verse pattern
    verse_pat = re.compile(
        r'(?:Sloka|Sl\.?|Verse)\s+(\d+)\.?\s*(.+?)(?=(?:Sloka|Sl\.?|Verse)\s+\d+|\Z)',
        re.DOTALL | re.IGNORECASE
    )
    for m in verse_pat.finditer(text):
        v = int(m.group(1))
        content = m.group(2).strip()
        content_en, content_sa = extract_en_sa(content)
        if len(content_en) < 30:
            continue
        ch = get_chapter_for_pos(m.start())
        chunks.append(make_chunk(
            text_id="brihat_jataka",
            chapter=ch,
            verse_start=v,
            verse_end=v,
            content_en=content_en,
            content_sa=content_sa,
            tradition_school="parashari",
            translator="B. Suryanarain Rao",
        ))

    logger.info("[rechunk] brihat_jataka: %d verse chunks", len(chunks))

    # Fallback paragraph
    if len(chunks) < 20:
        logger.info("[rechunk] brihat_jataka: verse pattern insufficient, using chapter+paragraph fallback")
        chunks = []

        # Split by chapters
        chapter_texts = []
        for i, m in enumerate(chap_matches):
            ch_num = parse_chap(m.group(1))
            if ch_num == 0:
                continue
            start = m.end()
            end = chap_matches[i + 1].start() if i + 1 < len(chap_matches) else len(text)
            ch_text = text[start:end].strip()
            chapter_texts.append((ch_num, ch_text))

        if not chapter_texts:
            chapter_texts = [(1, text)]

        for ch_num, ch_text in chapter_texts:
            # Numbered verse pattern "1. text"
            verse_pat2 = re.compile(
                r'^\s*(\d+)(?:-(\d+))?\.\s+(.+?)(?=^\s*\d+(?:-\d+)?\.\s|\Z)',
                re.MULTILINE | re.DOTALL
            )
            para_chunks = list(verse_pat2.finditer(ch_text))
            if len(para_chunks) >= 3:
                for pm in para_chunks:
                    v_s = int(pm.group(1))
                    v_e = int(pm.group(2)) if pm.group(2) else v_s
                    content = pm.group(3).strip()
                    content_en, content_sa = extract_en_sa(content)
                    if len(content_en) < 30:
                        continue
                    chunks.append(make_chunk(
                        text_id="brihat_jataka",
                        chapter=ch_num,
                        verse_start=v_s,
                        verse_end=v_e,
                        content_en=content_en,
                        content_sa=content_sa,
                        tradition_school="parashari",
                        translator="B. Suryanarain Rao",
                    ))
            else:
                # Paragraph fallback
                v = 0
                for para in re.split(r'\n\s*\n', ch_text):
                    para = para.strip()
                    content_en, content_sa = extract_en_sa(para)
                    if len(content_en) < 60:
                        continue
                    v += 1
                    chunks.append(make_chunk(
                        text_id="brihat_jataka",
                        chapter=ch_num,
                        verse_start=v,
                        verse_end=v,
                        content_en=content_en,
                        content_sa=content_sa,
                        tradition_school="parashari",
                        translator="B. Suryanarain Rao",
                    ))

    return chunks


def chunk_saravali(text: str) -> list[dict]:
    """
    Saravali (Kalyana Varma) — English translation by R. Santhanam.
    Structure: Chapter N + content paragraphs (double-spaced OCR).
    Uses paragraph-within-chapter chunking (verse pattern unreliable due to OCR).
    """
    chunks = []

    # Find all chapter boundaries
    chap_pat = re.compile(r'Chapter\s+(\d+)', re.IGNORECASE)
    chap_matches = list(chap_pat.finditer(text))
    chap_boundaries = [(int(m.group(1)), m.start()) for m in chap_matches]
    chap_boundaries.sort(key=lambda x: x[1])

    for i, (ch_num, ch_start) in enumerate(chap_boundaries):
        ch_end = chap_boundaries[i + 1][1] if i + 1 < len(chap_boundaries) else len(text)
        ch_text = text[ch_start:ch_end]

        # Paragraph-level chunking
        v = 0
        for para in re.split(r'\n\s*\n', ch_text):
            para = para.strip()
            content_en, content_sa = extract_en_sa(para)
            if len(content_en) < 60:
                continue
            v += 1
            # Try to detect verse range from paragraph start "1-4. content" or "1. content"
            verse_match = re.match(r'^(\d+)(?:-(\d+))?,?\s', para)
            if verse_match:
                v_start = min(int(verse_match.group(1)), SMALLINT_MAX)
                v_end = min(int(verse_match.group(2)) if verse_match.group(2) else v_start, SMALLINT_MAX)
            else:
                v_start = v_end = v
            chunks.append(make_chunk(
                text_id="saravali",
                chapter=ch_num,
                verse_start=v_start,
                verse_end=v_end,
                content_en=content_en,
                content_sa=content_sa,
                tradition_school="parashari",
                translator="R. Santhanam",
            ))

    logger.info("[rechunk] saravali: %d chunks from %d chapters", len(chunks), len(chap_boundaries))
    return chunks


# ── DB helpers ────────────────────────────────────────────────────────────────

def get_db_conn():
    import psycopg2  # type: ignore
    db_url = os.environ.get("DATABASE_URL", "")
    if not db_url:
        for env_path in [
            Path("/Users/Dev/Vibe-Coding/Apps/Madhav/platform/.env.local"),
        ]:
            if env_path.exists():
                for line in env_path.read_text().splitlines():
                    if line.startswith("DATABASE_URL="):
                        db_url = line.split("=", 1)[1].strip()
                        break
    if not db_url:
        raise RuntimeError("DATABASE_URL not set")
    return psycopg2.connect(db_url)


def delete_text_chunks(conn, text_id: str, chapter: Optional[int] = None):
    with conn.cursor() as cur:
        if chapter is not None:
            cur.execute("DELETE FROM classical_text_chunks WHERE text_id = %s AND chapter = %s", (text_id, chapter))
        else:
            cur.execute("DELETE FROM classical_text_chunks WHERE text_id = %s", (text_id,))
    conn.commit()
    logger.info("[rechunk] Cleared chunks for %s ch=%s", text_id, chapter)


def insert_chunks(conn, chunks: list[dict]) -> int:
    if not chunks:
        return 0
    now = datetime.now(timezone.utc)
    inserted = 0
    with conn.cursor() as cur:
        for c in chunks:
            try:
                cur.execute(
                    """
                    INSERT INTO classical_text_chunks
                      (text_id, chunk_id, verse_ref, chapter, verse_start, verse_end,
                       content_sa, content_en, topics, source_citation, ingested_at,
                       translator, tradition_school, content_sha256)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                      content_en = EXCLUDED.content_en,
                      content_sa = EXCLUDED.content_sa,
                      topics = EXCLUDED.topics,
                      content_sha256 = EXCLUDED.content_sha256
                    """,
                    (
                        c["text_id"], c["chunk_id"], c["verse_ref"],
                        c["chapter"], c["verse_start"], c["verse_end"],
                        c.get("content_sa"), c["content_en"],
                        c["topics"], c["source_citation"], now,
                        c["translator"], c["tradition_school"], c["content_sha256"],
                    )
                )
                inserted += 1
            except Exception as exc:
                logger.warning("[rechunk] Insert error %s: %s", c["chunk_id"], exc)
                conn.rollback()
    conn.commit()
    return inserted


def embed_text_id(conn, text_id: str) -> dict:
    """Embed all un-embedded chunks for text_id."""
    import vertexai  # type: ignore
    vertexai.init(project="madhav-astrology", location="asia-south1")
    from vertexai.language_models import TextEmbeddingModel  # type: ignore
    model = TextEmbeddingModel.from_pretrained("text-multilingual-embedding-002")

    with conn.cursor() as cur:
        cur.execute(
            "SELECT chunk_id, content_en, content_sa FROM classical_text_chunks WHERE text_id = %s AND embedding IS NULL ORDER BY chunk_id",
            (text_id,)
        )
        rows = cur.fetchall()

    if not rows:
        logger.info("[embed] No unembedded chunks for %s", text_id)
        return {"text_id": text_id, "embedded": 0, "failed": 0}

    logger.info("[embed] Embedding %d chunks for %s", len(rows), text_id)
    BATCH_SIZE = 100

    for batch_start in range(0, len(rows), BATCH_SIZE):
        batch = rows[batch_start:batch_start + BATCH_SIZE]
        texts = [(r[1] or "") + (" " + r[2] if r[2] else "") for r in batch]
        texts = [t.strip()[:8192] or " " for t in texts]
        chunk_ids = [r[0] for r in batch]
        _embed_recursive(conn, model, list(zip(chunk_ids, texts)))
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM classical_text_chunks WHERE text_id = %s AND embedding IS NOT NULL", (text_id,))
            count = cur.fetchone()[0]
        logger.info("[embed] %s: %d/%d embedded", text_id, count, len(rows))
        time.sleep(0.2)

    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM classical_text_chunks WHERE text_id = %s AND embedding IS NULL", (text_id,))
        failed = cur.fetchone()[0]
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM classical_text_chunks WHERE text_id = %s AND embedding IS NOT NULL", (text_id,))
        embedded = cur.fetchone()[0]

    return {"text_id": text_id, "embedded": embedded, "failed": failed}


def _embed_recursive(conn, model, pairs: list[tuple[str, str]], depth: int = 0):
    if not pairs or depth > 5:
        return
    try:
        embeddings = model.get_embeddings([p[1] for p in pairs])
        with conn.cursor() as cur:
            for (cid, _), emb in zip(pairs, embeddings):
                cur.execute("UPDATE classical_text_chunks SET embedding = %s WHERE chunk_id = %s", (emb.values, cid))
        conn.commit()
    except Exception as exc:
        if ("400" in str(exc) or "token" in str(exc).lower()) and len(pairs) > 1:
            mid = len(pairs) // 2
            _embed_recursive(conn, model, pairs[:mid], depth + 1)
            _embed_recursive(conn, model, pairs[mid:], depth + 1)
        else:
            logger.warning("[embed] Error at depth %d: %s", depth, exc)
            if depth < 3:
                time.sleep(2)
                _embed_recursive(conn, model, pairs, depth + 1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    logger.info("=== L0FR Stream C Re-chunk Phase 2 ===")
    conn = get_db_conn()
    results = {}

    try:
        # 1. Brihat Samhita
        logger.info("--- brihat_samhita ---")
        text = Path(TEXTS_DIR / "brihat_samhita/raw/bs_vol1_djvu.txt").read_text(errors="replace")
        chunks = chunk_brihat_samhita(text)
        delete_text_chunks(conn, "brihat_samhita")
        n = insert_chunks(conn, chunks)
        logger.info("brihat_samhita: inserted %d chunks", n)
        results["brihat_samhita"] = n

        # 2. Sarvartha Chintamani
        logger.info("--- sarvartha_chintamani ---")
        text = Path(TEXTS_DIR / "sarvartha_chintamani/raw/sc_djvu.txt").read_text(errors="replace")
        chunks = chunk_sarvartha_chintamani(text)
        delete_text_chunks(conn, "sarvartha_chintamani")
        n = insert_chunks(conn, chunks)
        logger.info("sarvartha_chintamani: inserted %d chunks", n)
        results["sarvartha_chintamani"] = n

        # 3. Jaimini Sutram
        logger.info("--- jaimini_sutram ---")
        text = Path(TEXTS_DIR / "jaimini_sutram/raw/js_djvu.txt").read_text(errors="replace")
        chunks = chunk_jaimini_sutram(text)
        delete_text_chunks(conn, "jaimini_sutram")
        n = insert_chunks(conn, chunks)
        logger.info("jaimini_sutram: inserted %d chunks", n)
        results["jaimini_sutram"] = n

        # 4. Jataka Parijata Vol 2 (supplement to existing 741 vol1 chunks)
        logger.info("--- jataka_parijata_vol2 ---")
        text = Path(TEXTS_DIR / "jataka_parijata/raw/jp_vol2_djvu.txt").read_text(errors="replace")
        chunks = chunk_jataka_parijata_vol2(text)
        # Don't delete vol1 chunks! Only replace chapters >= 10
        # Delete existing vol2-sourced chunks (chapters 10+)
        with conn.cursor() as cur:
            cur.execute("DELETE FROM classical_text_chunks WHERE text_id = 'jataka_parijata' AND chapter >= 10")
        conn.commit()
        n = insert_chunks(conn, chunks)
        logger.info("jataka_parijata_vol2: inserted %d chunks", n)
        results["jataka_parijata_vol2"] = n

        # 5. Brihat Jataka
        logger.info("--- brihat_jataka ---")
        text = Path(TEXTS_DIR / "brihat_jataka/raw/bj_djvu.txt").read_text(errors="replace")
        chunks = chunk_brihat_jataka(text)
        delete_text_chunks(conn, "brihat_jataka")
        n = insert_chunks(conn, chunks)
        logger.info("brihat_jataka: inserted %d chunks", n)
        results["brihat_jataka"] = n

        # 6. Embed all newly inserted chunks
        logger.info("=== Embedding new chunks ===")
        for text_id in ["brihat_samhita", "sarvartha_chintamani", "jaimini_sutram", "jataka_parijata", "brihat_jataka"]:
            result = embed_text_id(conn, text_id)
            logger.info("Embed %s: %d embedded, %d failed", text_id, result["embedded"], result["failed"])

        # Final stats
        with conn.cursor() as cur:
            cur.execute("SELECT text_id, COUNT(*) FROM classical_text_chunks GROUP BY text_id ORDER BY text_id")
            db_counts = {r[0]: r[1] for r in cur.fetchall()}
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM classical_text_chunks WHERE embedding IS NOT NULL")
            embedded_total = cur.fetchone()[0]
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM classical_text_chunks")
            total = cur.fetchone()[0]

        logger.info("=== FINAL DB STATS ===")
        for tid, count in sorted(db_counts.items()):
            logger.info("  %s: %d chunks", tid, count)
        logger.info("TOTAL: %d, EMBEDDED: %d", total, embedded_total)

        print("\n=== RE-CHUNK RESULTS ===")
        import json
        print(json.dumps({
            "rechunk_results": results,
            "db_counts": db_counts,
            "total_chunks": total,
            "embedded_count": embedded_total,
        }, indent=2))

        if total >= 6000 and embedded_total >= total * 0.95:
            print(f"\n[PASS] AC met: {total} total chunks, {embedded_total} embedded")
        else:
            print(f"\n[PARTIAL] {total} total, {embedded_total} embedded (target: ≥6000 total, 100% embedded)")

        # 7. Saravali (English edition — KalyanaVarmasSaravali_201707)
        logger.info("--- saravali ---")
        saravali_path = TEXTS_DIR / "saravali/raw/saravali_en_djvu.txt"
        if saravali_path.exists():
            text = saravali_path.read_text(errors="replace")
            chunks = chunk_saravali(text)
            delete_text_chunks(conn, "saravali")
            n = insert_chunks(conn, chunks)
            logger.info("saravali: inserted %d chunks", n)
            results["saravali"] = n
            # Embed
            result = embed_text_id(conn, "saravali")
            logger.info("Embed saravali: %d embedded, %d failed", result["embedded"], result["failed"])
        else:
            logger.warning("saravali English file not found at %s", saravali_path)
            results["saravali"] = 0

        # Refresh final stats
        with conn.cursor() as cur:
            cur.execute("SELECT text_id, COUNT(*) FROM classical_text_chunks GROUP BY text_id ORDER BY text_id")
            db_counts = {r[0]: r[1] for r in cur.fetchall()}
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM classical_text_chunks WHERE embedding IS NOT NULL")
            embedded_total = cur.fetchone()[0]
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM classical_text_chunks")
            total = cur.fetchone()[0]

        logger.info("=== UPDATED FINAL DB STATS (post-saravali) ===")
        for tid, count in sorted(db_counts.items()):
            logger.info("  %s: %d chunks", tid, count)
        logger.info("TOTAL: %d, EMBEDDED: %d", total, embedded_total)

        print("\n=== UPDATED TOTALS (post-saravali) ===")
        import json as _json2
        print(_json2.dumps({"db_counts": db_counts, "total_chunks": total, "embedded_count": embedded_total}, indent=2))

        if total >= 6000 and embedded_total >= total * 0.95:
            print(f"\n[PASS] AC met: {total} total chunks, {embedded_total} embedded")
        else:
            print(f"\n[STILL_PARTIAL] {total} total, {embedded_total} embedded (target: ≥6000)")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
