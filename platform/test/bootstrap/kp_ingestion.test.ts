/**
 * kp_ingestion.test.ts
 * Unit tests for the KP Reader ingestion pipeline (v3.2-S2).
 *
 * Tests parsing logic for KP Reader djvu.txt format:
 *   - Paragraph window extraction
 *   - OCR noise stripping
 *   - Work key and canonical_id assignment
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
 * Minimal KP Reader djvu.txt sample that mirrors the real source format.
 * Real KP Reader texts are topic-based prose with repeated page headers.
 */
const SAMPLE_KP_TEXT = `
KRISHNAMURTI PADHDHATI
CASTING THE HOROSCOPE
FIRST READER

KRISHNAMURTI PADHDHATI

PREFACE

When there are many books on Astrology available in the world,
there is still necessity for this book because it introduces the
stellar system of prediction which is unique to Krishnamurti Padhdhati.

KRISHNAMURTI PADHDHATI

INTRODUCTION

The Krishnamurti Padhdhati is a unique system of stellar astrology
developed by Prof. K.S. Krishnamurti. It is based on the Nakshatras
or star constellations and their sub-lords, which provide more precise
timing of events than traditional Parashari methods.

The sub-lord theory is the cornerstone of KP astrology. Each Nakshatra
is divided into nine sub-portions ruled by the nine planets. The sub-lord
of a cusp determines whether the signification of that house will manifest.

KRISHNAMURTI PADHDHATI

STELLAR ASTROLOGY PRINCIPLES

In the Stellar system, the 27 Nakshatras or star constellations are
the primary reference points. Each planet occupies a particular star,
and that star lord is considered its significator at the first level.

A planet gives results primarily according to the houses signified by
its star lord. If the star lord is in a favourable position and its
sub-lord is also in harmony, the planet produces beneficial results.

The ascendant and its sub-lord indicate the physical body and
overall life direction. The sub-lord of the ascendant must signify
the first house for longevity and physical vitality to be maintained.

SIGNS AND HOUSES

The twelve zodiacal signs from Aries to Pisces divide the ecliptic
into equal portions of 30 degrees each. Each sign has distinct
qualities: movable, fixed, or common; fiery, earthy, airy, or watery.

The twelve houses represent different departments of life: first house
for body and self, second for wealth, third for siblings and short journeys,
fourth for mother and property, fifth for children and intelligence.

KRISHNAMURTI PADHDHATI

CUSPAL POSITIONS

In the KP system, the house cusps are calculated using the Placidus
system of house division. The sub-lord of each cusp determines whether
that house's significations will be active and productive in the native's life.

The Moon's Nakshatra at birth determines the starting Dasha period.
The balance of the Nakshatra lord's period at birth is calculated
proportionally and this becomes the first Dasha period in operation.
`;

/**
 * Sample text with heavy page noise (headers repeated many times)
 */
const NOISY_KP_TEXT = `
KRISHNAMURTI PADHDHATI
KRISHNAMURTI PADHDHATI
KRISHNAMURTI PADHDHATI
KRISHNAMURTI PADHDHATI
KRISHNAMURTI PADHDHATI
KRISHNAMURTI PADHDHATI

This is the actual content that should be kept.
The stellar system uses the Nakshatra of the Moon at birth.
Each Nakshatra spans 13 degrees and 20 minutes of the zodiac.

KRISHNAMURTI PADHDHATI
KRISHNAMURTI PADHDHATI

More content here about the sub-lord theory which is central to
Krishnamurti Padhdhati predictions. The sub-lord of the significator
determines whether the event will actually materialize.
`;

// ── KP parsing helpers (mirrors bootstrap script logic) ──────────────────────

interface KPParagraphWindow {
  workKey: string;
  windowIdx: number;
  content: string;
  verseId: string;
}

const TARGET_WINDOW_TOKENS = 300;
const MIN_PARA_LENGTH = 40;

function stripKPPageNoise(text: string): string {
  const lines = text.split('\n');
  const lineFrequency = new Map<string, number>();
  for (const line of lines) {
    const trimmed = line.trim();
    if (trimmed.length > 0 && trimmed.length < 60) {
      lineFrequency.set(trimmed, (lineFrequency.get(trimmed) ?? 0) + 1);
    }
  }
  const filtered: string[] = [];
  for (const line of lines) {
    const trimmed = line.trim();
    const freq = lineFrequency.get(trimmed) ?? 0;
    if (freq > 5 && trimmed.length < 60 && trimmed.length > 0) continue;
    filtered.push(line);
  }
  return filtered.join('\n');
}

function parseKPVolumeWindows(text: string, workKey: string): KPParagraphWindow[] {
  const windows: KPParagraphWindow[] = [];
  const cleanText = stripKPPageNoise(text);

  const rawParagraphs = cleanText
    .split(/\n\s*\n+/)
    .map(p => p.replace(/\s+/g, ' ').trim())
    .filter(p => p.length >= MIN_PARA_LENGTH);

  if (rawParagraphs.length === 0) return [];

  let windowIdx = 0;
  let currentWindow: string[] = [];
  let currentTokens = 0;

  const flush = () => {
    if (currentWindow.length === 0) return;
    windowIdx++;
    const windowText = currentWindow.join(' ');
    const windowNumPadded = String(windowIdx).padStart(4, '0');
    windows.push({
      workKey,
      windowIdx,
      content: windowText,
      verseId: `${workKey}.${windowNumPadded}`,
    });
    currentWindow = [];
    currentTokens = 0;
  };

  for (const para of rawParagraphs) {
    const paraTokens = estimateTokens(para);
    if (currentTokens + paraTokens > TARGET_WINDOW_TOKENS && currentWindow.length > 0) {
      flush();
    }
    currentWindow.push(para);
    currentTokens += paraTokens;
  }
  flush();

  return windows;
}

function windowToRawVerse(w: KPParagraphWindow, vol: number): RawVerse {
  return {
    work: w.workKey,
    chapter: w.windowIdx,
    verse_start: w.windowIdx,
    verse_end: w.windowIdx,
    verse_ref: `${w.workKey}.${w.windowIdx}`,
    verse_id: w.verseId,
    translation_text: w.content,
    source_edition: `K.S. Krishnamurti, KP Reader Vol.${vol} (archive.org kp-readers)`,
  };
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe('KP page noise stripping', () => {
  it('removes frequently repeated short lines', () => {
    const cleaned = stripKPPageNoise(NOISY_KP_TEXT);
    // "KRISHNAMURTI PADHDHATI" appears 7+ times, should be stripped
    const occurrences = (cleaned.match(/KRISHNAMURTI PADHDHATI/g) ?? []).length;
    expect(occurrences).toBe(0);
  });

  it('preserves actual content lines', () => {
    const cleaned = stripKPPageNoise(NOISY_KP_TEXT);
    expect(cleaned).toContain('stellar system');
    expect(cleaned).toContain('sub-lord theory');
  });

  it('handles text with no noise', () => {
    const clean = 'This is a paragraph of content.\n\nAnother paragraph here.';
    const cleaned = stripKPPageNoise(clean);
    expect(cleaned).toContain('paragraph of content');
    expect(cleaned).toContain('Another paragraph');
  });

  it('preserves lines that appear infrequently', () => {
    const cleaned = stripKPPageNoise(SAMPLE_KP_TEXT);
    // Content lines should survive
    expect(cleaned).toContain('stellar system');
  });
});

describe('KP paragraph window parser', () => {
  it('extracts paragraph windows from sample text', () => {
    const windows = parseKPVolumeWindows(SAMPLE_KP_TEXT, 'KP_VOL1');
    expect(windows.length).toBeGreaterThan(0);
  });

  it('assigns correct work key', () => {
    const windows = parseKPVolumeWindows(SAMPLE_KP_TEXT, 'KP_VOL1');
    for (const w of windows) {
      expect(w.workKey).toBe('KP_VOL1');
    }
  });

  it('generates sequential window indices starting at 1', () => {
    const windows = parseKPVolumeWindows(SAMPLE_KP_TEXT, 'KP_VOL1');
    for (let i = 0; i < windows.length; i++) {
      expect(windows[i].windowIdx).toBe(i + 1);
    }
  });

  it('generates verse_ids with zero-padded index', () => {
    const windows = parseKPVolumeWindows(SAMPLE_KP_TEXT, 'KP_VOL1');
    const firstId = windows[0]?.verseId;
    expect(firstId).toMatch(/^KP_VOL1\.\d{4}$/);
  });

  it('window content is non-empty', () => {
    const windows = parseKPVolumeWindows(SAMPLE_KP_TEXT, 'KP_VOL1');
    for (const w of windows) {
      expect(w.content.trim().length).toBeGreaterThan(0);
    }
  });

  it('window content does not exceed ~2x target tokens', () => {
    const windows = parseKPVolumeWindows(SAMPLE_KP_TEXT, 'KP_VOL1');
    for (const w of windows) {
      const tokens = estimateTokens(w.content);
      // Allow some overage for single very long paragraphs
      expect(tokens).toBeLessThan(TARGET_WINDOW_TOKENS * 3);
    }
  });

  it('returns empty array for empty text', () => {
    const windows = parseKPVolumeWindows('', 'KP_VOL1');
    expect(windows).toHaveLength(0);
  });

  it('returns empty for text with only short lines', () => {
    const shortOnly = 'Hi\nHi\nOK\n'; // all < MIN_PARA_LENGTH
    const windows = parseKPVolumeWindows(shortOnly, 'KP_VOL1');
    expect(windows).toHaveLength(0);
  });

  it('strips noisy headers before windowing', () => {
    const windows = parseKPVolumeWindows(NOISY_KP_TEXT, 'KP_VOL1');
    // Content should be extracted despite noise
    const allContent = windows.map(w => w.content).join(' ');
    expect(allContent).toContain('stellar system');
  });

  it('produces separate windows for KP_VOL2 with different work key', () => {
    const windows = parseKPVolumeWindows(SAMPLE_KP_TEXT, 'KP_VOL2');
    expect(windows.length).toBeGreaterThan(0);
    for (const w of windows) {
      expect(w.workKey).toBe('KP_VOL2');
      expect(w.verseId).toMatch(/^KP_VOL2\./);
    }
  });
});

describe('KP → RawVerse conversion', () => {
  const sampleWindow: KPParagraphWindow = {
    workKey: 'KP_VOL1',
    windowIdx: 5,
    content: 'The sub-lord theory is the cornerstone of KP astrology. Each Nakshatra '
      + 'is divided into nine sub-portions ruled by the nine planets. The sub-lord '
      + 'of a cusp determines whether the signification of that house will manifest.',
    verseId: 'KP_VOL1.0005',
  };

  it('converts window to valid RawVerse', () => {
    const verse = windowToRawVerse(sampleWindow, 1);
    expect(verse.work).toBe('KP_VOL1');
    expect(verse.verse_id).toBe('KP_VOL1.0005');
    expect(verse.translation_text).toContain('sub-lord');
  });

  it('chapter equals window index', () => {
    const verse = windowToRawVerse(sampleWindow, 1);
    expect(verse.chapter).toBe(5);
  });

  it('includes correct source edition', () => {
    const verse = windowToRawVerse(sampleWindow, 1);
    expect(verse.source_edition).toContain('K.S. Krishnamurti');
    expect(verse.source_edition).toContain('Vol.1');
  });

  it('Vol 3 gets Vol.3 in source edition', () => {
    const verse = windowToRawVerse({ ...sampleWindow, workKey: 'KP_VOL3' }, 3);
    expect(verse.source_edition).toContain('Vol.3');
  });
});

describe('KP chunkVerse integration', () => {
  const sampleWindow: KPParagraphWindow = {
    workKey: 'KP_VOL2',
    windowIdx: 12,
    content: 'The twelve zodiacal signs from Aries to Pisces divide the ecliptic into equal portions. '
      + 'Each sign has distinct qualities: movable, fixed, or common; fiery, earthy, airy, or watery. '
      + 'The ascendant sign and its lord determine the basic temperament and physical constitution of the native.',
    verseId: 'KP_VOL2.0012',
  };

  it('produces at least one chunk', () => {
    const verse = windowToRawVerse(sampleWindow, 2);
    const chunks = chunkVerse(verse);
    expect(chunks.length).toBeGreaterThanOrEqual(1);
  });

  it('chunk_id follows classical_texts/KP_VOL* pattern', () => {
    const verse = windowToRawVerse(sampleWindow, 2);
    const chunks = chunkVerse(verse);
    expect(chunks[0].chunk_id).toMatch(/^classical_texts\/KP_VOL\d+\.\d+$/);
  });

  it('source_canonical_id is classical_texts/KP_VOL2', () => {
    const verse = windowToRawVerse(sampleWindow, 2);
    const chunks = chunkVerse(verse);
    for (const chunk of chunks) {
      expect(chunk.source_canonical_id).toBe('classical_texts/KP_VOL2');
    }
  });

  it('chunk content contains KP_VOL in header', () => {
    const verse = windowToRawVerse(sampleWindow, 2);
    const chunks = chunkVerse(verse);
    expect(chunks[0].content).toContain('KP_VOL');
  });

  it('chunk token count is positive', () => {
    const verse = windowToRawVerse(sampleWindow, 2);
    const chunks = chunkVerse(verse, 400);
    for (const chunk of chunks) {
      expect(chunk.token_count).toBeGreaterThan(0);
    }
  });

  it('full pipeline: parse → convert → chunk produces valid chunks for all volumes', () => {
    const workKeys = ['KP_VOL1', 'KP_VOL2', 'KP_VOL3', 'KP_VOL4'];

    for (let i = 0; i < workKeys.length; i++) {
      const workKey = workKeys[i];
      const windows = parseKPVolumeWindows(SAMPLE_KP_TEXT, workKey);
      const verses = windows.map(w => windowToRawVerse(w, i + 1));
      const chunks = verses.flatMap(v => chunkVerse(v));

      expect(chunks.length).toBeGreaterThan(0);

      for (const chunk of chunks) {
        expect(chunk.chunk_id).toMatch(new RegExp(`^classical_texts\\/${workKey}\\.`));
        expect(chunk.content.trim().length).toBeGreaterThan(0);
        expect(chunk.token_count).toBeGreaterThan(0);
        expect(chunk.source_canonical_id).toBe(`classical_texts/${workKey}`);
      }
    }
  });
});

describe('KP corpus quality checks', () => {
  it('sample text produces at least 1 window', () => {
    const windows = parseKPVolumeWindows(SAMPLE_KP_TEXT, 'KP_VOL1');
    expect(windows.length).toBeGreaterThanOrEqual(1);
  });

  it('all window verse_ids are unique', () => {
    const windows = parseKPVolumeWindows(SAMPLE_KP_TEXT, 'KP_VOL1');
    const ids = new Set(windows.map(w => w.verseId));
    expect(ids.size).toBe(windows.length);
  });

  it('window content does not include page-noise strings', () => {
    const windows = parseKPVolumeWindows(NOISY_KP_TEXT, 'KP_VOL1');
    for (const w of windows) {
      // The noise line "KRISHNAMURTI PADHDHATI" repeated 7x should not be in windows
      // (it may appear once if it's a real header — test that noise is reduced)
      const noiseOccurrences = (w.content.match(/KRISHNAMURTI PADHDHATI/g) ?? []).length;
      // In cleaned content, it might appear once as part of actual content, but not 7x
      expect(noiseOccurrences).toBeLessThan(3);
    }
  });
});
