/**
 * tajaka_ingestion.test.ts
 * Unit tests for Tajaka Neelakanthi ingestion (v3.2-S3).
 */

import { describe, it, expect } from 'vitest';
import { TAJAKA_CORPUS } from '../../scripts/bootstrap/lib/tajaka_corpus.js';
import { chunkVerse, estimateTokens, type RawVerse } from '../../scripts/bootstrap/lib/classical_text_chunker.js';

// ── Corpus integrity ────────────────────────────────────────────────────────

describe('TAJAKA_CORPUS structure', () => {
  it('has at least 200 entries', () => {
    expect(TAJAKA_CORPUS.length).toBeGreaterThanOrEqual(200);
  });

  it('covers at least 10 chapters', () => {
    const chapters = new Set(TAJAKA_CORPUS.map(e => e.chapter));
    expect(chapters.size).toBeGreaterThanOrEqual(10);
  });

  it('every entry has chapter, verse, and non-empty content', () => {
    for (const entry of TAJAKA_CORPUS) {
      expect(typeof entry.chapter).toBe('number');
      expect(entry.chapter).toBeGreaterThan(0);
      expect(typeof entry.verse).toBe('number');
      expect(entry.verse).toBeGreaterThan(0);
      expect(typeof entry.content).toBe('string');
      expect(entry.content.trim().length).toBeGreaterThan(20);
    }
  });

  it('chapter numbers are positive integers ≤ 30', () => {
    for (const entry of TAJAKA_CORPUS) {
      expect(entry.chapter).toBeGreaterThanOrEqual(1);
      expect(entry.chapter).toBeLessThanOrEqual(30);
    }
  });

  it('verse numbers are positive integers', () => {
    for (const entry of TAJAKA_CORPUS) {
      expect(entry.verse).toBeGreaterThanOrEqual(1);
    }
  });

  it('no duplicate chapter+verse combinations', () => {
    const seen = new Set<string>();
    for (const entry of TAJAKA_CORPUS) {
      const key = `${entry.chapter}.${entry.verse}`;
      expect(seen.has(key), `Duplicate: ${key}`).toBe(false);
      seen.add(key);
    }
  });

  it('content strings are meaningful prose (≥ 40 chars)', () => {
    const short = TAJAKA_CORPUS.filter(e => e.content.trim().length < 40);
    expect(short.length).toBe(0);
  });
});

// ── RawVerse conversion ─────────────────────────────────────────────────────

function toRawVerse(entry: (typeof TAJAKA_CORPUS)[0]): RawVerse {
  const verseId = `TAJAKA.${String(entry.chapter).padStart(2, '0')}.${String(entry.verse).padStart(3, '0')}`;
  return {
    work: 'TAJAKA',
    chapter: entry.chapter,
    verse_start: entry.verse,
    verse_end: entry.verse,
    verse_ref: `${entry.chapter}.${entry.verse}`,
    verse_id: verseId,
    translation_text: entry.content,
    source_edition: 'MARSYS-JIS-M9-extraction',
  };
}

describe('RawVerse conversion', () => {
  it('produces correct verse_id format', () => {
    const entry = { chapter: 3, verse: 7, content: 'test content here for the verse body' };
    const rv = toRawVerse(entry);
    expect(rv.verse_id).toBe('TAJAKA.03.007');
  });

  it('verse_ref format is chapter.verse', () => {
    const entry = { chapter: 12, verse: 4, content: 'test content body for the verse' };
    const rv = toRawVerse(entry);
    expect(rv.verse_ref).toBe('12.4');
  });

  it('work is TAJAKA', () => {
    const rv = toRawVerse(TAJAKA_CORPUS[0]);
    expect(rv.work).toBe('TAJAKA');
  });

  it('source_edition is MARSYS-JIS-M9-extraction', () => {
    const rv = toRawVerse(TAJAKA_CORPUS[0]);
    expect(rv.source_edition).toContain('MARSYS-JIS-M9-extraction');
  });
});

// ── Chunker integration ─────────────────────────────────────────────────────

describe('chunkVerse for Tajaka', () => {
  const sampleEntry = TAJAKA_CORPUS[0];
  const sampleVerse = toRawVerse(sampleEntry);

  it('returns at least one chunk', () => {
    const chunks = chunkVerse(sampleVerse);
    expect(chunks.length).toBeGreaterThanOrEqual(1);
  });

  it('chunk_id starts with classical_texts/TAJAKA', () => {
    const chunks = chunkVerse(sampleVerse);
    expect(chunks[0].chunk_id).toMatch(/^classical_texts\/TAJAKA\./);
  });

  it('source_canonical_id is classical_texts/TAJAKA', () => {
    const chunks = chunkVerse(sampleVerse);
    expect(chunks[0].source_canonical_id).toBe('classical_texts/TAJAKA');
  });

  it('chunk content includes work header', () => {
    const chunks = chunkVerse(sampleVerse);
    expect(chunks[0].content).toContain('[TAJAKA');
  });

  it('chunk token_count is within 10–600 range', () => {
    for (const entry of TAJAKA_CORPUS.slice(0, 20)) {
      const rv = toRawVerse(entry);
      const chunks = chunkVerse(rv);
      for (const chunk of chunks) {
        expect(chunk.token_count).toBeGreaterThan(10);
        expect(chunk.token_count).toBeLessThan(600);
      }
    }
  });

  it('full corpus produces ≥ 200 chunks', () => {
    const allChunks = TAJAKA_CORPUS.flatMap(e => chunkVerse(toRawVerse(e)));
    expect(allChunks.length).toBeGreaterThanOrEqual(200);
  });

  it('all chunk_ids are unique', () => {
    const allChunks = TAJAKA_CORPUS.flatMap(e => chunkVerse(toRawVerse(e)));
    const ids = allChunks.map(c => c.chunk_id);
    const unique = new Set(ids);
    expect(unique.size).toBe(ids.length);
  });
});

// ── Token estimation ────────────────────────────────────────────────────────

describe('estimateTokens', () => {
  it('returns positive integer for non-empty text', () => {
    expect(estimateTokens('hello world')).toBeGreaterThan(0);
  });

  it('longer text has more tokens', () => {
    const short = estimateTokens('short text');
    const long = estimateTokens('a much longer text with many more words than the short one above');
    expect(long).toBeGreaterThan(short);
  });
});
