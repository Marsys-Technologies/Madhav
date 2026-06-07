"""
brahmagyan.l0_text_chunker — L0FR Stream C: Classical Text Chunker
==================================================================

Deterministic-first per brief §0.5: pure Python regex chunking, NO LLM.
Verse markers extracted via regex patterns; parked chunks logged for review.

Texts targeted (Phase 1): BPHS, Phaladeepika, Jataka Parijata
"""
from __future__ import annotations

import hashlib
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Data model ────────────────────────────────────────────────────────────────

@dataclass
class Chunk:
    text_id: str
    chapter: int
    verse_start: int
    verse_end: int
    verse_ref: str
    content_en: str
    content_sa: Optional[str]
    source_citation: str
    tradition_school: str
    translator: str
    topics: list[str]
    content_sha256: str
    chunk_id: str
    park_reason: Optional[str] = None


# ── Text registry ─────────────────────────────────────────────────────────────

TEXT_META = {
    "bphs": {
        "title": "Brihat Parashara Hora Shastra",
        "author": "Maharishi Parasara",
        "tradition_school": "parashari",
        "translator": "R. Santhanam",
        "edition": "Ranjan Publications, 2 vols",
        "source_url": "https://archive.org/details/BPHSEnglish",
        "license": "public_domain",
    },
    "phaladeepika": {
        "title": "Phaladeepika",
        "author": "Mantreswara",
        "tradition_school": "parashari",
        "translator": "V. Subrahmanya Sastri",
        "edition": "2nd Ed. 1950, Aruna Press, Bangalore",
        "source_url": "https://archive.org/details/Phaladeepika2ndEd.1950ByVSubrahmanyaSastri",
        "license": "public_domain",
    },
    "jataka_parijata": {
        "title": "Jataka Parijata",
        "author": "Vaidyanatha Dikshita",
        "tradition_school": "parashari",
        "translator": "V. Subrahmanya Sastri",
        "edition": "2 vols, Motilal Banarsidass",
        "source_url": "https://archive.org/details/JatakaParijataVolIOfIIByVSubrahmanyaSastri",
        "license": "public_domain",
    },
}

# ── Verse marker patterns ─────────────────────────────────────────────────────
# Order matters: try patterns from most specific to least specific.
# Each pattern must capture (verse_start, verse_end?) before the verse content.

VERSE_PATTERNS = [
    # Pattern 1: "1-3. TITLE TEXT" — range verse numbering (most common in BPHS djvu.txt)
    re.compile(
        r'^\s*(\d+)-(\d+)\.\s+([A-Z][A-Z\s\',&:()./-]{2,})\s*:?\s*(.+?)(?=^\s*\d+[-\d]*\.\s+[A-Z]|\Z)',
        re.MULTILINE | re.DOTALL
    ),
    # Pattern 2: "1. TITLE TEXT" — single verse number + title
    re.compile(
        r'^\s*(\d+)\.\s+([A-Z][A-Z\s\',&:()./-]{2,})\s*:?\s*(.+?)(?=^\s*\d+[-\d]*\.\s+[A-Z]|\Z)',
        re.MULTILINE | re.DOTALL
    ),
    # Pattern 3: Chapter + verse pattern "CH.N, V.N" inline
    re.compile(
        r'(?:Shloka|Sloka|Verse|Sl\.)\s+(\d+)[-–]?(\d*)\.?\s*(.+?)(?=(?:Shloka|Sloka|Verse|Sl\.)\s+\d|\Z)',
        re.DOTALL
    ),
]

# Devanagari and Sanskrit verse end markers to identify bilingual chunks
SANSKRIT_END_MARKER = re.compile(r'[॥।॥]|\\\\|\|\|')

# Chapter header patterns
CHAPTER_PATTERNS = [
    re.compile(r'(?:CHAPTER|Chapter|Ch\.)\s+(\d+)', re.IGNORECASE),
    re.compile(r'^(\d+)\.\s+(?:EFFECTS|EVILS|ASPECTS|EVALUATION|YOGA|NABHASA|PLANETARY|JUDG|BHAVA|ARGALA|LUNAR|SOLAR|RAJA|LONGEVITY|MARAKA|AVASTA|DIVISIONAL|ZODIACAL|SPECIAL|CREATION|GREAT|EIGHT|ANTIDOTE)',
               re.MULTILINE),
]

# ── Chapter extractor ─────────────────────────────────────────────────────────

def _detect_chapters(text: str) -> list[tuple[int, int, str]]:
    """
    Returns list of (char_start, chapter_num, chapter_title).
    Heuristic: look for numbered chapter headers.
    """
    chapters = []
    # Pattern: "Ch. N" or "CHAPTER N" or numbered uppercase headings
    ch_pat = re.compile(
        r'(?:^|\n)\s*(?:Ch(?:apter)?\.?\s+(\d+)|(\d+)\.\s+((?:EFFECTS\s+OF|ASPECTS|YOGAS?|CREATION|GREAT|EVILS|ANTIDOTE|PLANETARY|EVALUATION|BHAVA|DIVISIONAL|ZODIACAL|SPECIAL|LUNAR|SOLAR|RAJA|YOGA\s+K|LONGEVITY|MARAKA|AVAST|JUDG)[A-Z\s]+))',
        re.MULTILINE | re.IGNORECASE
    )
    for m in ch_pat.finditer(text):
        ch_num = int(m.group(1) or m.group(2) or 0)
        if ch_num > 0:
            chapters.append((m.start(), ch_num, (m.group(3) or '').strip()))
    return chapters


def _extract_sanskrit(content: str) -> tuple[str, Optional[str]]:
    """
    Try to separate Sanskrit lines from English lines.
    Lines that are predominantly non-ASCII are treated as Sanskrit.
    Returns (content_en, content_sa).
    """
    lines = content.split('\n')
    sa_lines = []
    en_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Count non-ASCII characters
        non_ascii = sum(1 for c in stripped if ord(c) > 127)
        ratio = non_ascii / max(len(stripped), 1)
        if ratio > 0.4:  # >40% non-ASCII → Sanskrit line
            sa_lines.append(stripped)
        else:
            en_lines.append(stripped)

    content_en = '\n'.join(en_lines).strip()
    content_sa = '\n'.join(sa_lines).strip() if sa_lines else None
    return content_en, content_sa


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def _normalize_text(text: str) -> str:
    """Light cleanup: collapse multiple blank lines, strip control chars."""
    # Remove form-feed and other control chars
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', ' ', text)
    # Collapse 3+ newlines to 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


# ── Primary chunker ───────────────────────────────────────────────────────────

def chunk_text(
    raw_text: str,
    text_id: str,
    chapter: int,
    chapter_title: str = "",
) -> tuple[list[Chunk], list[Chunk]]:
    """
    Split raw chapter text into verse chunks.
    Returns (good_chunks, parked_chunks).

    Good chunks: properly extracted with verse_ref, content ≥50 chars, ≤2000 chars.
    Parked chunks: failed validation; logged for native review.
    """
    meta = TEXT_META.get(text_id, {})
    tradition_school = meta.get("tradition_school", "parashari")
    translator = meta.get("translator", "unknown")
    source_prefix = f"{text_id.upper()} Ch.{chapter}"

    good: list[Chunk] = []
    parked: list[Chunk] = []

    text = _normalize_text(raw_text)

    # ── Try verse extraction patterns in order ────────────────────────────────
    chunks_raw: list[tuple[int, int, str, str]] = []  # (verse_start, verse_end, content, match_type)

    # Pattern: numbered verses like "1-3. TITLE : content" or "1. TITLE : content"
    verse_pat = re.compile(
        r'^\s*(\d+)(?:-(\d+))?\.\s+(.+?)(?=^\s*\d+(?:-\d+)?\.\s|\Z)',
        re.MULTILINE | re.DOTALL
    )

    for m in verse_pat.finditer(text):
        v_start = int(m.group(1))
        v_end = int(m.group(2)) if m.group(2) else v_start
        content = m.group(3).strip()
        chunks_raw.append((v_start, v_end, content, 'numbered'))

    # Fallback: if no numbered verses found, try paragraph chunking
    if not chunks_raw:
        paragraphs = re.split(r'\n\s*\n', text)
        for idx, para in enumerate(paragraphs, start=1):
            para = para.strip()
            if len(para) > 50:
                chunks_raw.append((idx, idx, para, 'paragraph'))

    # ── Validate and classify chunks ─────────────────────────────────────────
    if len(chunks_raw) < 3:
        # PARK entire chapter
        park_chunk = Chunk(
            text_id=text_id,
            chapter=chapter,
            verse_start=0,
            verse_end=0,
            verse_ref=f"CH{chapter}:UNEXTRACTED",
            content_en=text[:500] if text else "(empty)",
            content_sa=None,
            source_citation=f"{source_prefix} (unextracted)",
            tradition_school=tradition_school,
            translator=translator,
            topics=[],
            content_sha256=_sha256(text),
            chunk_id=f"{text_id}_ch{chapter:03d}_park",
            park_reason=f"<3 chunks found from pattern matching (got {len(chunks_raw)})",
        )
        parked.append(park_chunk)
        return good, parked

    for v_start, v_end, content, match_type in chunks_raw:
        content_en, content_sa = _extract_sanskrit(content)

        # Quality gates
        park_reason = None
        if len(content_en) < 50:
            park_reason = f"content_en too short ({len(content_en)} chars)"
        elif len(content_en) > 2500:
            park_reason = f"content_en too long ({len(content_en)} chars)"

        verse_ref = f"CH{chapter}:V{v_start}" + (f"-V{v_end}" if v_end != v_start else "")
        chunk_id = f"{text_id}_ch{chapter:03d}_v{v_start:04d}"
        source_citation = f"{source_prefix} v.{v_start}" + (f"-{v_end}" if v_end != v_start else "")

        # Extract topics from content (simple keyword detection)
        topics = _extract_topics(content_en)

        chunk = Chunk(
            text_id=text_id,
            chapter=chapter,
            verse_start=v_start,
            verse_end=v_end,
            verse_ref=verse_ref,
            content_en=content_en if content_en else content[:2000],
            content_sa=content_sa,
            source_citation=source_citation,
            tradition_school=tradition_school,
            translator=translator,
            topics=topics,
            content_sha256=_sha256(content_en or content),
            chunk_id=chunk_id,
            park_reason=park_reason,
        )

        if park_reason:
            parked.append(chunk)
        else:
            good.append(chunk)

    return good, parked


# ── Topic extractor (keyword-based, deterministic) ────────────────────────────

_TOPIC_KEYWORDS = {
    "sun": ["sun", "solar", "surya", "ravi"],
    "moon": ["moon", "lunar", "chandra", "soma"],
    "mars": ["mars", "kuja", "mangal", "mangala"],
    "mercury": ["mercury", "budha", "budh"],
    "jupiter": ["jupiter", "guru", "brihaspati"],
    "venus": ["venus", "shukra"],
    "saturn": ["saturn", "shani"],
    "rahu": ["rahu", "dragon's head", "north node"],
    "ketu": ["ketu", "dragon's tail", "south node"],
    "lagna": ["lagna", "ascendant", "rising"],
    "yoga": ["yoga", "combination"],
    "dasha": ["dasha", "antardasha", "mahadasha", "vimshottari"],
    "navamsa": ["navamsa", "navamsha", "d9"],
    "house": ["house", "bhava", "bhav"],
    "strength": ["strength", "bala", "shadbala", "dig bala"],
    "exaltation": ["exalt", "uccha"],
    "debilitation": ["debilitat", "neecha"],
    "aspect": ["aspect", "drishti"],
    "transit": ["transit", "gochara"],
    "karma": ["karma", "karmik"],
    "marriage": ["marriage", "spouse", "husband", "wife", "kalatra"],
    "children": ["children", "progeny", "putra"],
    "wealth": ["wealth", "dhana", "money", "riches"],
    "health": ["health", "disease", "illness", "sickness"],
    "longevity": ["longevity", "lifespan", "ayus"],
    "remedy": ["remedy", "remedial", "upaya", "puja"],
}


def _extract_topics(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for topic, keywords in _TOPIC_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            found.append(topic)
    return found[:8]  # cap at 8 topics


# ── Full text processor ───────────────────────────────────────────────────────

def process_text_file(
    text_id: str,
    source_files: list[str],
    park_log_path: str = "/tmp/l0fr_chunks_parked.txt",
) -> tuple[list[Chunk], int, int]:
    """
    Process one or more source files for a single text_id.
    Returns (good_chunks, good_count, parked_count).
    """
    all_good: list[Chunk] = []
    all_parked: list[Chunk] = []

    for src_path in source_files:
        logger.info("[l0_chunker] Processing %s from %s", text_id, src_path)
        path = Path(src_path)
        if not path.exists():
            logger.warning("[l0_chunker] File not found: %s", src_path)
            continue

        raw_text = path.read_text(encoding='utf-8', errors='replace')
        raw_text = _normalize_text(raw_text)

        # Split into chapters
        chapter_segments = _split_into_chapters(raw_text, text_id)
        logger.info("[l0_chunker] %s: found %d chapters", text_id, len(chapter_segments))

        for ch_num, ch_title, ch_text in chapter_segments:
            # JP uses "Sloka N" pattern; other texts use numbered verse pattern
            if text_id == "jataka_parijata":
                good, parked = chunk_jp_slokas(ch_text, text_id, ch_num, ch_title)
            else:
                good, parked = chunk_text(ch_text, text_id, ch_num, ch_title)
            all_good.extend(good)
            all_parked.extend(parked)
            if parked:
                logger.debug(
                    "[l0_chunker] %s Ch%d: %d good, %d parked",
                    text_id, ch_num, len(good), len(parked)
                )

    # Write parked chunks to log
    if all_parked:
        _write_park_log(all_parked, park_log_path)

    logger.info(
        "[l0_chunker] %s TOTAL: %d good, %d parked",
        text_id, len(all_good), len(all_parked)
    )
    return all_good, len(all_good), len(all_parked)


def _split_into_chapters(text: str, text_id: str) -> list[tuple[int, str, str]]:
    """
    Split a full text into (chapter_num, chapter_title, chapter_text) segments.
    Uses heuristics based on text_id.
    """
    segments = []

    # Jataka Parijata: uses "Adhyaya N." chapter markers
    if text_id == "jataka_parijata":
        return _split_jp_adhyayas(text)

    # Try explicit chapter markers first
    ch_pat = re.compile(
        r'(?:^|\n)\s*(?:Ch(?:apter)?\.?\s+(\d+)|(\d{1,3})\.\s+(?=EFFECTS|EVILS|ASPECTS|YOGAS?|CREATION|GREAT|PLANETARY|EVALUATION|BHAVA|DIVISIONAL|ZODIACAL|SPECIAL|LUNAR|SOLAR|RAJA|LONGEVITY|MARAKA|AVAST|JUDG|ANTIDOTE|ARGALA|ISHTA|UPAGRAHA|KARAK|NABHASA))',
        re.MULTILINE | re.IGNORECASE
    )

    matches = list(ch_pat.finditer(text))
    if len(matches) >= 3:
        # Good chapter detection
        for i, m in enumerate(matches):
            ch_num = int(m.group(1) or m.group(2) or 0)
            if ch_num == 0:
                continue
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            ch_text = text[start:end].strip()
            # Extract chapter title from first line
            first_line = ch_text.split('\n')[0].strip()
            segments.append((ch_num, first_line[:80], ch_text))
    else:
        # Fallback: split by double-blank-line blocks, assign sequential chapter nums
        # Find numbered sections (like "12. EFFECTS OF FIRST HOUSE")
        sec_pat = re.compile(
            r'(?:^|\n)(\d{1,3})\.\s+(EFFECTS\s+OF|ASPECTS|EVALUATION|YOGAS?|CREATION|GREAT|PLANETARY|EVILS|BHAVA|DIVISIONAL|ZODIACAL|SPECIAL|LUNAR|SOLAR|RAJA|YOGA\s+K|LONGEVITY|MARAKA|AVAST|JUDG|ANTIDOTE|ARGALA|ISHTA|UPAGRAHA|KARAK|NABHASA)',
            re.MULTILINE | re.IGNORECASE
        )
        sec_matches = list(sec_pat.finditer(text))
        if len(sec_matches) >= 3:
            for i, m in enumerate(sec_matches):
                ch_num = int(m.group(1))
                title = (m.group(2) or '').strip()
                start = m.start()
                end = sec_matches[i + 1].start() if i + 1 < len(sec_matches) else len(text)
                ch_text = text[start:end].strip()
                segments.append((ch_num, title[:80], ch_text))
        else:
            # Last resort: treat whole text as single chapter
            segments.append((1, "Full Text", text))

    return segments


_ROMAN = {
    'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
    'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10,
    'XI': 11, 'XII': 12, 'XIII': 13, 'XIV': 14, 'XV': 15,
    'XVI': 16, 'XVII': 17, 'XVIII': 18, 'XIX': 19, 'XX': 20,
}


def _parse_adhyaya_num(raw: str) -> int:
    """Parse Adhyaya number — Arabic digit or Roman numeral."""
    s = raw.strip().rstrip('.').upper()
    if s.isdigit():
        return int(s)
    return _ROMAN.get(s, 0)


def _split_jp_adhyayas(text: str) -> list[tuple[int, str, str]]:
    """
    Split Jataka Parijata text by Adhyaya markers.
    JP vol1 uses Arabic digits; vol2 uses Roman numerals (X, XI, XII…).
    """
    segments = []
    # Match "Adhyaya N" or "Adh. N" — Arabic OR Roman numerals at line start
    adh_pat = re.compile(
        r'(?:^|\n)\s*Adh(?:yaya)?\.?\s+([IVXLCDM\d]+)\.?\s*([A-Za-z ,\-]*)',
        re.MULTILINE
    )
    matches = list(adh_pat.finditer(text))

    # Filter to entries where we can parse a valid chapter number
    valid_matches = []
    for m in matches:
        ch_num = _parse_adhyaya_num(m.group(1))
        if ch_num > 0:
            valid_matches.append((ch_num, m))

    if len(valid_matches) >= 3:
        for i, (ch_num, m) in enumerate(valid_matches):
            title = (m.group(2) or '').strip()[:80]
            start = m.start()
            end = valid_matches[i + 1][1].start() if i + 1 < len(valid_matches) else len(text)
            ch_text = text[start:end].strip()
            segments.append((ch_num, f"Adhyaya {ch_num}: {title}", ch_text))
    else:
        # JP fallback: use Sloka-based global chunking
        segments.append((1, "Full Text", text))

    return segments


def chunk_jp_slokas(
    raw_text: str,
    text_id: str,
    chapter: int,
    chapter_title: str = "",
) -> tuple[list[Chunk], list[Chunk]]:
    """
    Special chunker for Jataka Parijata using "Sloka N" pattern.
    Returns (good_chunks, parked_chunks).
    """
    meta = TEXT_META.get(text_id, {})
    tradition_school = meta.get("tradition_school", "parashari")
    translator = meta.get("translator", "unknown")
    source_prefix = f"{text_id.upper()} Ch.{chapter}"

    good: list[Chunk] = []
    parked: list[Chunk] = []

    text = _normalize_text(raw_text)

    # JP Sloka pattern: "Sloka N content" or "Sloka N. content"
    sloka_pat = re.compile(
        r'Sloka\s+(\d+)\.?\s+(.+?)(?=Sloka\s+\d+|\Z)',
        re.DOTALL | re.IGNORECASE
    )

    chunks_raw = []
    for m in sloka_pat.finditer(text):
        v_start = int(m.group(1))
        content = m.group(2).strip()
        chunks_raw.append((v_start, v_start, content))

    if not chunks_raw:
        # No Sloka markers found — park the chapter
        park_chunk = Chunk(
            text_id=text_id,
            chapter=chapter,
            verse_start=0,
            verse_end=0,
            verse_ref=f"CH{chapter}:UNEXTRACTED",
            content_en=text[:500] if text else "(empty)",
            content_sa=None,
            source_citation=f"{source_prefix} (no slokas found)",
            tradition_school=tradition_school,
            translator=translator,
            topics=[],
            content_sha256=_sha256(text),
            chunk_id=f"{text_id}_ch{chapter:03d}_park",
            park_reason="No Sloka markers found",
        )
        parked.append(park_chunk)
        return good, parked

    for v_start, v_end, content in chunks_raw:
        content_en, content_sa = _extract_sanskrit(content)

        park_reason = None
        if len(content_en) < 50:
            park_reason = f"content_en too short ({len(content_en)} chars)"
        elif len(content_en) > 2500:
            park_reason = f"content_en too long ({len(content_en)} chars)"

        verse_ref = f"CH{chapter}:V{v_start}"
        chunk_id = f"{text_id}_ch{chapter:03d}_v{v_start:04d}"
        source_citation = f"{source_prefix} Sloka.{v_start}"
        topics = _extract_topics(content_en)

        chunk = Chunk(
            text_id=text_id,
            chapter=chapter,
            verse_start=v_start,
            verse_end=v_end,
            verse_ref=verse_ref,
            content_en=content_en if content_en else content[:2000],
            content_sa=content_sa,
            source_citation=source_citation,
            tradition_school=tradition_school,
            translator=translator,
            topics=topics,
            content_sha256=_sha256(content_en or content),
            chunk_id=chunk_id,
            park_reason=park_reason,
        )

        if park_reason:
            parked.append(chunk)
        else:
            good.append(chunk)

    return good, parked


def _write_park_log(parked: list[Chunk], path: str) -> None:
    """Append parked chunks to the park log."""
    lines = []
    for c in parked:
        lines.append(
            f"PARKED: {c.chunk_id} | {c.verse_ref} | reason={c.park_reason} | "
            f"content_preview={c.content_en[:80]!r}\n"
        )
    with open(path, 'a', encoding='utf-8') as f:
        f.writelines(lines)


# ── DB writer ─────────────────────────────────────────────────────────────────

def insert_chunks(conn, chunks: list[Chunk], dry_run: bool = False) -> int:
    """
    INSERT chunks into classical_text_chunks.
    Returns count of rows inserted.
    """
    if dry_run or not chunks:
        return len(chunks)

    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    inserted = 0

    with conn.cursor() as cur:
        for c in chunks:
            try:
                cur.execute("""
                    INSERT INTO classical_text_chunks
                      (text_id, chunk_id, verse_ref, chapter, verse_start, verse_end,
                       content_sa, content_en, topics, source_citation, ingested_at,
                       translator, tradition_school, content_sha256)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                      content_en = EXCLUDED.content_en,
                      content_sa = EXCLUDED.content_sa,
                      topics = EXCLUDED.topics,
                      source_citation = EXCLUDED.source_citation,
                      content_sha256 = EXCLUDED.content_sha256
                """, (
                    c.text_id, c.chunk_id, c.verse_ref,
                    c.chapter, c.verse_start, c.verse_end,
                    c.content_sa, c.content_en,
                    c.topics, c.source_citation, now,
                    c.translator, c.tradition_school, c.content_sha256,
                ))
                inserted += 1
            except Exception as exc:
                logger.warning(
                    "[l0_chunker] Failed to insert chunk %s: %s",
                    c.chunk_id, exc
                )
                conn.rollback()

    conn.commit()
    return inserted


def insert_classical_text(conn, text_id: str) -> None:
    """
    Insert or update classical_texts row — the parent table for the FK in
    classical_text_chunks.  Must be called BEFORE insert_chunks().
    """
    meta = TEXT_META.get(text_id, {})
    if not meta:
        logger.warning("[l0_chunker] No TEXT_META for %s — cannot insert classical_texts row", text_id)
        return

    tradition = meta.get("tradition_school", "parashari")
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO classical_texts
              (text_id, title_en, author, school, tradition, license, source_edition)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (text_id) DO UPDATE SET
              title_en = EXCLUDED.title_en,
              author = EXCLUDED.author,
              source_edition = EXCLUDED.source_edition
        """, (
            text_id,
            meta.get("title", text_id),
            meta.get("author"),
            tradition,
            tradition,
            meta.get("license", "public_domain"),
            meta.get("edition"),
        ))

    conn.commit()
    logger.info("[l0_chunker] Upserted classical_texts row for %s", text_id)


def insert_text_source(conn, text_id: str) -> None:
    """Insert or update classical_texts_source row."""
    meta = TEXT_META.get(text_id, {})
    if not meta:
        return

    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO classical_texts_source
              (text_id, title, author, edition, translator, source_url, license, citation_format)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            ON CONFLICT (text_id) DO UPDATE SET
              title = EXCLUDED.title,
              edition = EXCLUDED.edition,
              translator = EXCLUDED.translator
        """, (
            text_id,
            meta.get("title", text_id),
            meta.get("author"),
            meta.get("edition"),
            meta.get("translator"),
            meta.get("source_url"),
            meta.get("license", "public_domain"),
            f"{meta.get('title', text_id).upper()} Ch.N v.N",
        ))

    conn.commit()
