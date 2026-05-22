/**
 * jaimini_ingestion.test.ts
 * Unit tests for the Jaimini Sutram ingestion pipeline (v3.2-S2).
 *
 * Tests parsing logic for Jaimini Sutras djvu.txt format:
 *   - ADHYAYA-PADA section structure
 *   - Sutra numbering and content extraction
 *   - Chunking behavior using shared classical_text_chunker.ts
 *
 * No DB or Vertex AI calls — all tests are pure parsing/chunking.
 */

import { describe, it, expect } from 'vitest';
import {
  chunkVerse,
  estimateTokens,
  type RawVerse,
} from '../../scripts/bootstrap/lib/classical_text_chunker';

// ── Fixtures ────────────────────────────────────────────────────────────────

/**
 * Minimal Jaimini djvu.txt sample that mirrors the real source format:
 * - ADHYAYA N-PADA M headers
 * - Su. N. — transliteration\ntranslation paragraph\ncommentary
 */
const SAMPLE_JAIMINI_TEXT = `
Preliminary Observations

JAIMINISUTRAS— English Translation


ADHYAYA 1— PADA 1

This pada covers the fundamental principles.

Su. 1 . — Upadesam Vyakhyasyamah.

I shall now explain the teachings. This first sutra introduces the
entire work of Jaimini as a systematic exposition of predictive
astrology covering Rasi Dasas, Karakas and Arudha Lagnas.

NOTES

Upadesa means literally bringing one close to the object.

Su. 2 . — Abhipasyanti rikshani.

The zodiacal signs aspect each other (in their front). This principle
of Rasi Drishti differs fundamentally from Parashari graha aspects
and governs the special Jaimini aspect rules used in timing events.

Su. 3 . — Parswabhe cha.

Excepting the next zodiacal signs to them. Fixed signs aspect all
movable signs except the adjacent one; movable signs aspect all fixed
signs except the adjacent one; common signs aspect each other.

Su. 4 . — Thannishthascha tadvat.

Those planets which occupy such signs will also aspect the planets
found in such houses. This extends Rasi Drishti from signs to planets
within those signs, making Jaimini aspects sign-based rather than degree-based.

End of First Pads of the First Adhyaya

ADHYAYA 1-PADA 2.

This pada covers Atmakaraka in Navamsa.

Su. 1 . — Adhaswamsograhanam.

Among the planets, the one with the highest longitude becomes the
Atmakaraka. The Chara Karakas are determined by the degrees of planets
and signify specific relatives and life domains in Jaimini system.

Su. 2. — Panchamooshikamarjaraha.

Cat and rat are enemies. This sutra illustrates the principle of
natural enemies and its application to planetary relationships in the
Jaimini system of Char Karakas.

End of Second Pada of the First Adhyaya.
`;

// ── Jaimini-specific parsing helpers (mirrors the bootstrap script logic) ─────

interface JaiminiSutra {
  adhyaya: number;
  pada: number;
  sutraNum: number;
  transliteration: string;
  translation: string;
  commentary: string;
  verseId: string;
}

/**
 * Parse sutras from a block of section lines using the line-based approach.
 * Mirrors parseSutrasFromSectionLines() in the bootstrap script.
 */
function parseSectionLines(lines: string[], adhyaya: number, pada: number): JaiminiSutra[] {
  const sutras: JaiminiSutra[] = [];
  const sutraLinePattern = /^Su\.\s*(\d+)\s*\.?\s*[-—–.]+\s*(.*)/;

  let currentSutraNum: number | null = null;
  let currentTranslit = '';
  let bodyLines: string[] = [];

  const flush = () => {
    if (currentSutraNum === null) return;
    const bodyText = bodyLines.join('\n').trim();
    const paragraphs = bodyText
      .split(/\n\s*\n/)
      .map(p => p.replace(/\s+/g, ' ').trim())
      .filter(p => p.length > 20);
    const translation = paragraphs[0] ?? bodyText.replace(/\s+/g, ' ').trim();
    if (translation.length < 20) { currentSutraNum = null; bodyLines = []; return; }
    const commentary = paragraphs.slice(1).join(' ').trim();
    const sutraNumPadded = String(currentSutraNum).padStart(3, '0');
    const verseId = `JAIMINI.A${adhyaya}.P${pada}.${sutraNumPadded}`;
    sutras.push({ adhyaya, pada, sutraNum: currentSutraNum, transliteration: currentTranslit, translation, commentary, verseId });
    currentSutraNum = null; bodyLines = []; currentTranslit = '';
  };

  for (const rawLine of lines) {
    const line = rawLine.trim();
    const sutraMatch = sutraLinePattern.exec(line);
    if (sutraMatch) {
      flush();
      currentSutraNum = parseInt(sutraMatch[1], 10);
      currentTranslit = (sutraMatch[2] ?? '').trim();
      bodyLines = [];
    } else if (line.startsWith('End of') || /^ADHYAYA\s*\d+/.test(line)) {
      flush();
    } else if (currentSutraNum !== null) {
      bodyLines.push(rawLine);
    }
  }
  flush();
  return sutras;
}

/**
 * Parse Jaimini sections from sample text.
 * This mirrors the parseJaiminiDjvuText() function in the bootstrap script.
 */
function parseJaiminiSample(text: string): JaiminiSutra[] {
  const lines = text.split('\n');
  const sectionHeaderPattern = /^ADHYAYA\s*(\d+)\s*[-—–]+\s*PADA\s*(\d+)\b/;

  const sectionHeaders: Array<{ adhyaya: number; pada: number; lineIdx: number }> = [];
  for (let i = 0; i < lines.length; i++) {
    const m = sectionHeaderPattern.exec(lines[i].trim());
    if (m) {
      sectionHeaders.push({ adhyaya: parseInt(m[1], 10), pada: parseInt(m[2], 10), lineIdx: i });
    }
  }

  const allSutras: JaiminiSutra[] = [];
  for (let i = 0; i < sectionHeaders.length; i++) {
    const header = sectionHeaders[i];
    const startLine = header.lineIdx + 1;
    const endLine = i + 1 < sectionHeaders.length ? sectionHeaders[i + 1].lineIdx : lines.length;
    const sectionLines = lines.slice(startLine, endLine);
    allSutras.push(...parseSectionLines(sectionLines, header.adhyaya, header.pada));
  }
  return allSutras;
}

/**
 * Convert a JaiminiSutra to a RawVerse for chunking.
 */
function sutraToRawVerse(s: JaiminiSutra): RawVerse {
  const chapterCode = s.adhyaya * 10 + s.pada;
  return {
    work: 'JAIMINI',
    chapter: chapterCode,
    verse_start: s.sutraNum,
    verse_end: s.sutraNum,
    verse_ref: `A${s.adhyaya}P${s.pada}.${s.sutraNum}`,
    verse_id: s.verseId,
    sanskrit_text: s.transliteration || undefined,
    translation_text: s.translation,
    commentary_text: s.commentary || undefined,
    source_edition: 'B.S. Rao / B.V. Raman, IBH Prakashana 1955',
  };
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('Jaimini section parser', () => {
  it('finds ADHYAYA-PADA sections in sample text', () => {
    const sutras = parseJaiminiSample(SAMPLE_JAIMINI_TEXT);
    expect(sutras.length).toBeGreaterThan(0);
  });

  it('correctly identifies Adhyaya 1 Pada 1', () => {
    const sutras = parseJaiminiSample(SAMPLE_JAIMINI_TEXT);
    const a1p1 = sutras.filter(s => s.adhyaya === 1 && s.pada === 1);
    expect(a1p1.length).toBeGreaterThan(0);
  });

  it('correctly identifies Adhyaya 1 Pada 2', () => {
    const sutras = parseJaiminiSample(SAMPLE_JAIMINI_TEXT);
    const a1p2 = sutras.filter(s => s.adhyaya === 1 && s.pada === 2);
    expect(a1p2.length).toBeGreaterThan(0);
  });

  it('extracts sutra numbers correctly', () => {
    const sutras = parseJaiminiSample(SAMPLE_JAIMINI_TEXT);
    const sutraNums = sutras.filter(s => s.adhyaya === 1 && s.pada === 1).map(s => s.sutraNum);
    expect(sutraNums).toContain(1);
    expect(sutraNums).toContain(2);
    expect(sutraNums).toContain(3);
    expect(sutraNums).toContain(4);
  });

  it('extracts transliteration from sutra header', () => {
    const sutras = parseJaiminiSample(SAMPLE_JAIMINI_TEXT);
    const su1 = sutras.find(s => s.adhyaya === 1 && s.pada === 1 && s.sutraNum === 1);
    expect(su1).toBeDefined();
    expect(su1?.transliteration).toContain('Upadesam');
  });

  it('extracts translation text for each sutra', () => {
    const sutras = parseJaiminiSample(SAMPLE_JAIMINI_TEXT);
    for (const s of sutras) {
      expect(s.translation.length).toBeGreaterThan(20);
    }
  });

  it('generates correct verse_id format', () => {
    const sutras = parseJaiminiSample(SAMPLE_JAIMINI_TEXT);
    const idPattern = /^JAIMINI\.A\d+\.P\d+\.\d{3}$/;
    for (const s of sutras) {
      expect(s.verseId).toMatch(idPattern);
    }
  });

  it('sutra verse_id encodes adhyaya and pada correctly', () => {
    const sutras = parseJaiminiSample(SAMPLE_JAIMINI_TEXT);
    const su2 = sutras.find(s => s.adhyaya === 1 && s.pada === 2 && s.sutraNum === 1);
    expect(su2?.verseId).toBe('JAIMINI.A1.P2.001');
  });

  it('returns empty array for empty text', () => {
    const sutras = parseJaiminiSample('');
    expect(sutras).toHaveLength(0);
  });

  it('returns empty array for text without ADHYAYA-PADA headers', () => {
    const sutras = parseJaiminiSample('Some text without any headers or sutras.');
    expect(sutras).toHaveLength(0);
  });
});

describe('Jaimini → RawVerse conversion', () => {
  const sampleSutra: JaiminiSutra = {
    adhyaya: 1,
    pada: 1,
    sutraNum: 2,
    transliteration: 'Abhipasyanti rikshani.',
    translation: 'The zodiacal signs aspect each other in their front. This principle of Rasi Drishti governs timing of events in Jaimini system.',
    commentary: 'Movable signs aspect all fixed signs except the adjacent one.',
    verseId: 'JAIMINI.A1.P1.002',
  };

  it('converts sutra to valid RawVerse', () => {
    const verse = sutraToRawVerse(sampleSutra);
    expect(verse.work).toBe('JAIMINI');
    expect(verse.verse_id).toBe('JAIMINI.A1.P1.002');
    expect(verse.translation_text).toContain('zodiacal signs');
  });

  it('encodes chapter as adhyaya*10 + pada', () => {
    const verse = sutraToRawVerse(sampleSutra);
    expect(verse.chapter).toBe(11); // adhyaya=1, pada=1 → 1*10+1=11
  });

  it('encodes chapter for Adhyaya 2 Pada 3', () => {
    const su = { ...sampleSutra, adhyaya: 2, pada: 3 };
    const verse = sutraToRawVerse(su);
    expect(verse.chapter).toBe(23); // 2*10+3=23
  });

  it('includes transliteration in sanskrit_text', () => {
    const verse = sutraToRawVerse(sampleSutra);
    expect(verse.sanskrit_text).toContain('Abhipasyanti');
  });

  it('includes commentary when present', () => {
    const verse = sutraToRawVerse(sampleSutra);
    expect(verse.commentary_text).toContain('Movable signs');
  });

  it('omits commentary_text when empty', () => {
    const su = { ...sampleSutra, commentary: '' };
    const verse = sutraToRawVerse(su);
    expect(verse.commentary_text).toBeUndefined();
  });
});

describe('Jaimini chunkVerse integration', () => {
  const sampleSutra: JaiminiSutra = {
    adhyaya: 1,
    pada: 1,
    sutraNum: 4,
    transliteration: 'Thannishthascha tadvat.',
    translation: 'Those planets which occupy such signs will also aspect the planets found in such houses. '
      + 'This extends Rasi Drishti from signs to planets within those signs, '
      + 'making Jaimini aspects sign-based rather than degree-based as in Parashari system.',
    commentary: 'The principle means that if Aries aspects Scorpio, then any planet in Aries '
      + 'also aspects any planet in Scorpio, regardless of the longitudinal degree difference.',
    verseId: 'JAIMINI.A1.P1.004',
  };

  it('produces at least one chunk for Jaimini sutra', () => {
    const verse = sutraToRawVerse(sampleSutra);
    const chunks = chunkVerse(verse);
    expect(chunks.length).toBeGreaterThanOrEqual(1);
  });

  it('chunk_id follows classical_texts/JAIMINI.* pattern', () => {
    const verse = sutraToRawVerse(sampleSutra);
    const chunks = chunkVerse(verse);
    expect(chunks[0].chunk_id).toMatch(/^classical_texts\/JAIMINI\./);
  });

  it('source_canonical_id is classical_texts/JAIMINI', () => {
    const verse = sutraToRawVerse(sampleSutra);
    const chunks = chunkVerse(verse);
    for (const chunk of chunks) {
      expect(chunk.source_canonical_id).toBe('classical_texts/JAIMINI');
    }
  });

  it('chunk content includes sutra reference', () => {
    const verse = sutraToRawVerse(sampleSutra);
    const chunks = chunkVerse(verse);
    expect(chunks[0].content).toContain('JAIMINI');
  });

  it('chunk content includes translation text', () => {
    const verse = sutraToRawVerse(sampleSutra);
    const chunks = chunkVerse(verse);
    const allContent = chunks.map(c => c.content).join(' ');
    expect(allContent).toContain('Rasi Drishti');
  });

  it('token count is positive and reasonable', () => {
    const verse = sutraToRawVerse(sampleSutra);
    const chunks = chunkVerse(verse, 400);
    for (const chunk of chunks) {
      expect(chunk.token_count).toBeGreaterThan(0);
      expect(chunk.token_count).toBeLessThanOrEqual(500);
    }
  });

  it('full pipeline: parse sample → convert → chunk produces valid chunks', () => {
    const sutras = parseJaiminiSample(SAMPLE_JAIMINI_TEXT);
    const verses = sutras.map(sutraToRawVerse);
    const chunks = verses.flatMap(v => chunkVerse(v));

    expect(chunks.length).toBeGreaterThan(0);

    for (const chunk of chunks) {
      expect(chunk.chunk_id).toMatch(/^classical_texts\/JAIMINI\./);
      expect(chunk.content.trim().length).toBeGreaterThan(0);
      expect(chunk.token_count).toBeGreaterThan(0);
      expect(chunk.source_canonical_id).toBe('classical_texts/JAIMINI');
    }
  });
});

describe('Jaimini corpus quality checks', () => {
  it('total sutras from sample is at least 6 (2 sections × ~3 each)', () => {
    const sutras = parseJaiminiSample(SAMPLE_JAIMINI_TEXT);
    expect(sutras.length).toBeGreaterThanOrEqual(6);
  });

  it('all sutra translations are non-empty after trimming', () => {
    const sutras = parseJaiminiSample(SAMPLE_JAIMINI_TEXT);
    for (const s of sutras) {
      expect(s.translation.trim().length).toBeGreaterThan(0);
    }
  });

  it('verse_ids are unique within sample', () => {
    const sutras = parseJaiminiSample(SAMPLE_JAIMINI_TEXT);
    const ids = new Set(sutras.map(s => s.verseId));
    expect(ids.size).toBe(sutras.length);
  });

  it('all translated chunks have content containing the work name', () => {
    const sutras = parseJaiminiSample(SAMPLE_JAIMINI_TEXT);
    const verses = sutras.map(sutraToRawVerse);
    const chunks = verses.flatMap(v => chunkVerse(v));
    for (const chunk of chunks) {
      expect(chunk.content).toContain('JAIMINI');
    }
  });
});
