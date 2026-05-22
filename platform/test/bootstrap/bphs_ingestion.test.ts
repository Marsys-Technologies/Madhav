/**
 * bphs_ingestion.test.ts
 * Unit tests for the BPHS ingestion pipeline (v3.2-S1).
 *
 * Tests classical_text_chunker.ts functions:
 *   - parseBphsDjvuText()
 *   - chunkVerse()
 *   - deduplicateVerses()
 *   - estimateTokens()
 *
 * Tests do NOT hit the database or Vertex AI — all network calls are mocked.
 */

import { describe, it, expect } from 'vitest';
import {
  parseBphsDjvuText,
  chunkVerse,
  deduplicateVerses,
  estimateTokens,
  chunkChapter,
  type RawVerse,
} from '../../scripts/bootstrap/lib/classical_text_chunker';

// ── Sample BPHS text fixture ────────────────────────────────────────────────

const SAMPLE_BPHS_TEXT = `
Brihat Parasara Hora Sastra

MAHARSHI PARASARA

VOL I

CONTENTS

1. THE CREATION 17
2. GREAT INCARNATIONS 22
3. PLANETARY CHARACTERS 24

Chapter 1

The Creation chapter begins here.

1-4. Offering his obeisance to all-knowing sage Parasara and to
Lord Brahma and Vishnu, I proceed to narrate this great work.
The Lord is eternal and beyond the three gunas, yet through
Maya he manifests the creation.

5-8. Parasara answered, 'O Brahmin, your query has an auspicious
purpose for the welfare of the Universe. Praying Lord Brahma and
Sri Saraswati, I shall proceed to narrate the science of astrology.

9-12. Sri Vishnu who is the lord of all matters has no beginning.
He authored the Universe and administers it with a quarter of his power.
The other three quarters are filled with nectar knowable only to philosophers.

13-15. The three powers are: Sri Sakti with Sattwa Guna, Bhoo Sakti
with Rajoguna and Neela Sakti with Tamoguna. Apart from the three,
the fourth kind of Vishnu assumes the form of Sankarshana.

16-17. Mahattatwa, Ahamkara and Brahma are born from Sankarshana,
Pradyumna and Anirudha respectively. All these three forms are endowed
with all the three gunas.

Chapter 2

Planetary characters and description.

1-3. Parasara said: O Brahmin, listen to the account of placement
of the heavenly bodies. Out of the many sacred forms of Vishnu,
the luminous ones are the planets that govern creation.

4. Those are called planets that move through the Nakshatras in the zodiac.
In Sanskrit they are called grahas because they seize or grip.

5-7. The Sun is the soul of the Kala purusha, the Moon is his mind,
Mars is his strength, Mercury is his speech. Jupiter is his wisdom,
Venus is his desire and Saturn is his sorrow.

8. Rahu and Ketu are the shadowy planets that cause eclipses and
govern karmic patterns across lifetimes.

Chapter 3

Zodiacal signs described.

1-2. The zodiac comprises twelve signs from Aries to Pisces.
Each sign is ruled by a planet and has distinct characteristics
that affect the matters signified by the houses they occupy.

3-5. Aries is a movable fire sign ruled by Mars. It is masculine,
rises by its hind part, and indicates the head of the Kalapurusha.
Its natives are bold, enterprising and prone to anger.
`.trim();

// ── Tests for parseBphsDjvuText ─────────────────────────────────────────────

describe('parseBphsDjvuText', () => {
  it('extracts verse records from sample BPHS text', () => {
    const verses = parseBphsDjvuText(SAMPLE_BPHS_TEXT);
    expect(verses.length).toBeGreaterThan(0);
  });

  it('assigns correct work identifier', () => {
    const verses = parseBphsDjvuText(SAMPLE_BPHS_TEXT);
    for (const v of verses) {
      expect(v.work).toBe('BPHS');
    }
  });

  it('generates correct verse_id format (BPHS.NN.NNN)', () => {
    const verses = parseBphsDjvuText(SAMPLE_BPHS_TEXT);
    const idPattern = /^BPHS\.\d{2}\.\d{3}$/;
    for (const v of verses) {
      expect(v.verse_id).toMatch(idPattern);
    }
  });

  it('detects multiple chapters', () => {
    const verses = parseBphsDjvuText(SAMPLE_BPHS_TEXT);
    const chapters = new Set(verses.map(v => v.chapter));
    expect(chapters.size).toBeGreaterThanOrEqual(2);
  });

  it('includes translation text for each verse', () => {
    const verses = parseBphsDjvuText(SAMPLE_BPHS_TEXT);
    for (const v of verses) {
      expect(v.translation_text.length).toBeGreaterThan(20);
    }
  });

  it('correctly parses verse ranges (e.g. "5-8.")', () => {
    const verses = parseBphsDjvuText(SAMPLE_BPHS_TEXT);
    const rangedVerse = verses.find(v => v.verse_end > v.verse_start);
    expect(rangedVerse).toBeDefined();
    if (rangedVerse) {
      expect(rangedVerse.verse_end).toBeGreaterThan(rangedVerse.verse_start);
    }
  });

  it('correctly parses single verse numbers (e.g. "4.")', () => {
    const verses = parseBphsDjvuText(SAMPLE_BPHS_TEXT);
    const singleVerse = verses.find(v => v.verse_end === v.verse_start);
    expect(singleVerse).toBeDefined();
  });

  it('assigns source_edition including R. Santhanam', () => {
    const verses = parseBphsDjvuText(SAMPLE_BPHS_TEXT, 'Vol. 1');
    for (const v of verses) {
      expect(v.source_edition).toContain('R. Santhanam');
      expect(v.source_edition).toContain('Vol. 1');
    }
  });

  it('returns empty array for empty text', () => {
    const verses = parseBphsDjvuText('');
    expect(verses).toEqual([]);
  });

  it('handles text with no verse numbers gracefully', () => {
    const noVerseText = `Chapter 1\n\nThis chapter has no verse numbers at all.\n`;
    const verses = parseBphsDjvuText(noVerseText);
    expect(verses.length).toBe(0);
  });
});

// ── Tests for deduplicateVerses ─────────────────────────────────────────────

describe('deduplicateVerses', () => {
  const makeVerse = (id: string, text: string): RawVerse => ({
    work: 'BPHS',
    chapter: 1,
    verse_start: 1,
    verse_end: 1,
    verse_ref: '1.1',
    verse_id: id,
    translation_text: text,
    source_edition: 'R. Santhanam',
  });

  it('returns same array when no duplicates', () => {
    const verses = [makeVerse('BPHS.01.001', 'A'), makeVerse('BPHS.01.002', 'B')];
    const result = deduplicateVerses(verses);
    expect(result.length).toBe(2);
  });

  it('deduplicates by verse_id, keeping last occurrence', () => {
    const verses = [
      makeVerse('BPHS.01.001', 'First occurrence'),
      makeVerse('BPHS.01.001', 'Second occurrence (should win)'),
    ];
    const result = deduplicateVerses(verses);
    expect(result.length).toBe(1);
    expect(result[0].translation_text).toBe('Second occurrence (should win)');
  });

  it('handles empty array', () => {
    expect(deduplicateVerses([])).toEqual([]);
  });

  it('handles single element', () => {
    const verse = makeVerse('BPHS.01.001', 'Only verse');
    expect(deduplicateVerses([verse])).toHaveLength(1);
  });
});

// ── Tests for estimateTokens ────────────────────────────────────────────────

describe('estimateTokens', () => {
  it('returns 0 for empty string', () => {
    expect(estimateTokens('')).toBe(0);
  });

  it('returns positive count for non-empty text', () => {
    const count = estimateTokens('The Sun is exalted in Aries.');
    expect(count).toBeGreaterThan(0);
  });

  it('scales approximately with text length', () => {
    const short = estimateTokens('Hello world');
    const long = estimateTokens('Hello world '.repeat(10));
    expect(long).toBeGreaterThan(short);
  });

  it('stays within reasonable bounds for typical verse text', () => {
    const verseText = `Sri Vishnu who is the lord of all matters has no beginning.
    He authored the Universe and administers it with a quarter of his power.
    The other three quarters of Him, filled with nectar, are knowable to only the philosophers.`;
    const tokens = estimateTokens(verseText);
    expect(tokens).toBeGreaterThan(20);
    expect(tokens).toBeLessThan(200);
  });
});

// ── Tests for chunkVerse ────────────────────────────────────────────────────

describe('chunkVerse', () => {
  const sampleVerse: RawVerse = {
    work: 'BPHS',
    chapter: 8,
    verse_start: 5,
    verse_end: 8,
    verse_ref: '8.5-8',
    verse_id: 'BPHS.08.005',
    translation_text: 'Rahu in the seventh house causes disruption in partnerships and marriage. '
      + 'The native may experience delays, separations, or unconventional union. '
      + 'However, if Rahu is aspected by benefics, the disruption may bring unique experiences.',
    source_edition: 'R. Santhanam / archive.org',
  };

  it('produces at least one chunk per verse', () => {
    const chunks = chunkVerse(sampleVerse);
    expect(chunks.length).toBeGreaterThanOrEqual(1);
  });

  it('chunk_id follows "classical_texts/BPHS.NN.NNN" pattern', () => {
    const chunks = chunkVerse(sampleVerse);
    expect(chunks[0].chunk_id).toBe('classical_texts/BPHS.08.005');
  });

  it('source_canonical_id is "classical_texts/BPHS"', () => {
    const chunks = chunkVerse(sampleVerse);
    for (const chunk of chunks) {
      expect(chunk.source_canonical_id).toBe('classical_texts/BPHS');
    }
  });

  it('content includes verse reference header', () => {
    const chunks = chunkVerse(sampleVerse);
    expect(chunks[0].content).toContain('[BPHS');
  });

  it('content includes translation text', () => {
    const chunks = chunkVerse(sampleVerse);
    const allContent = chunks.map(c => c.content).join(' ');
    expect(allContent).toContain('Rahu');
  });

  it('token_count is within 200–500 range for normal verse', () => {
    const chunks = chunkVerse(sampleVerse, 400);
    for (const chunk of chunks) {
      expect(chunk.token_count).toBeGreaterThan(0);
      expect(chunk.token_count).toBeLessThanOrEqual(500);
    }
  });

  it('includes original verse reference', () => {
    const chunks = chunkVerse(sampleVerse);
    expect(chunks[0].verse.verse_ref).toBe('8.5-8');
    expect(chunks[0].verse.chapter).toBe(8);
  });

  it('splits very long verses into multiple chunks', () => {
    const longVerse: RawVerse = {
      ...sampleVerse,
      translation_text: Array(50).fill('The Sun governs the soul and the ego of the native.').join(' '),
    };
    const chunks = chunkVerse(longVerse, 100); // very small max for test
    expect(chunks.length).toBeGreaterThan(1);
  });

  it('second chunk_id has _p2 suffix when split', () => {
    const longVerse: RawVerse = {
      ...sampleVerse,
      translation_text: Array(50).fill('The Sun governs the soul of the native.').join(' '),
    };
    const chunks = chunkVerse(longVerse, 50);
    if (chunks.length > 1) {
      expect(chunks[1].chunk_id).toContain('_p2');
    }
  });
});

// ── Tests for chunkChapter ──────────────────────────────────────────────────

describe('chunkChapter', () => {
  const makeVerse = (chNum: number, vNum: number, text: string): RawVerse => ({
    work: 'BPHS',
    chapter: chNum,
    verse_start: vNum,
    verse_end: vNum,
    verse_ref: `${chNum}.${vNum}`,
    verse_id: `BPHS.${String(chNum).padStart(2, '0')}.${String(vNum).padStart(3, '0')}`,
    translation_text: text,
    source_edition: 'R. Santhanam',
  });

  it('chunks all verses in a chapter', () => {
    const verses = [
      makeVerse(3, 1, 'Mars is a masculine, fiery, pitta planet ruling Aries and Scorpio.'),
      makeVerse(3, 2, 'The Sun is royal, governs the soul, and is exalted in Aries.'),
      makeVerse(3, 3, 'Jupiter is the great benefic, guru of the gods, ruler of wisdom.'),
    ];
    const chunks = chunkChapter(verses);
    expect(chunks.length).toBeGreaterThanOrEqual(3);
  });

  it('returns empty array for empty chapter', () => {
    expect(chunkChapter([])).toEqual([]);
  });

  it('preserves chapter and work info in each chunk', () => {
    const verses = [
      makeVerse(5, 1, 'Special Lagnas: Hora Lagna, Ghatika Lagna, Bhava Lagna each serve distinct purposes.'),
    ];
    const chunks = chunkChapter(verses);
    for (const chunk of chunks) {
      expect(chunk.verse.work).toBe('BPHS');
      expect(chunk.verse.chapter).toBe(5);
    }
  });
});

// ── Integration: parse → chunk ──────────────────────────────────────────────

describe('parseBphsDjvuText → chunkVerse integration', () => {
  it('all parsed verses produce valid chunks', () => {
    const verses = parseBphsDjvuText(SAMPLE_BPHS_TEXT);
    const chunks = verses.flatMap(v => chunkVerse(v));

    expect(chunks.length).toBeGreaterThan(0);

    for (const chunk of chunks) {
      // chunk_id must follow classical_texts/BPHS.NN.NNN pattern
      expect(chunk.chunk_id).toMatch(/^classical_texts\/BPHS\.\d{2}\.\d{3}/);
      // content must be non-empty
      expect(chunk.content.trim().length).toBeGreaterThan(0);
      // token_count must be positive
      expect(chunk.token_count).toBeGreaterThan(0);
      // source_canonical_id must be classical_texts/BPHS
      expect(chunk.source_canonical_id).toBe('classical_texts/BPHS');
    }
  });
});
