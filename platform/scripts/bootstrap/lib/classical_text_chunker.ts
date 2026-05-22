/**
 * classical_text_chunker.ts
 * Shared verse-level chunker for BPHS, Jaimini, KP Reader, and Tajaka ingestion.
 * MCP Transformation v3.2 — MARSYS-JIS project.
 *
 * Design:
 *  - Each verse (or verse range) becomes one chunk.
 *  - Chunks contain: verse identifier + translation text (+ sanskrit when available).
 *  - Target size: 200–400 tokens per chunk per brief §5.
 *  - Long verses are split at sentence boundaries to stay within token budget.
 */

export interface RawVerse {
  /** Work identifier, e.g. 'BPHS', 'JAIMINI', 'KP_VOL1', 'TAJAKA' */
  work: string;
  /** Chapter number (integer) */
  chapter: number;
  /** First verse number in the range */
  verse_start: number;
  /** Last verse number in the range (same as verse_start for single verses) */
  verse_end: number;
  /** Human-readable verse reference, e.g. "8.5-8" */
  verse_ref: string;
  /** Canonical verse identifier, e.g. "BPHS.08.005" */
  verse_id: string;
  /** Sanskrit text (may be empty or OCR artefact) */
  sanskrit_text?: string;
  /** English translation text */
  translation_text: string;
  /** Commentary text (optional) */
  commentary_text?: string;
  /** Source edition string */
  source_edition: string;
}

export interface ClassicalChunk {
  /** Canonical chunk ID for rag_chunks.chunk_id, e.g. "classical_texts/BPHS.08.005" */
  chunk_id: string;
  /** source_canonical_id for rag_chunks, e.g. "classical_texts/BPHS" */
  source_canonical_id: string;
  /** Combined content for embedding */
  content: string;
  /** Token count estimate */
  token_count: number;
  /** Raw verse this chunk was produced from */
  verse: RawVerse;
}

/**
 * Rough token count using whitespace splitting (< 5% error vs tiktoken for prose).
 * Avoids adding tiktoken as a dependency to the bootstrap scripts.
 */
export function estimateTokens(text: string): number {
  return Math.ceil(text.split(/\s+/).filter(Boolean).length * 1.35);
}

/**
 * Build a chunk's combined content from a verse's fields.
 * Format: "[WORK Ch.N v.X] translation | commentary"
 */
function buildVerseContent(verse: RawVerse): string {
  const header = `[${verse.work} Ch.${verse.chapter} v.${verse.verse_ref.split('.').slice(1).join('.')}]`;
  const parts: string[] = [header];

  if (verse.translation_text?.trim()) {
    parts.push(verse.translation_text.trim());
  }
  if (verse.commentary_text?.trim()) {
    parts.push(`Commentary: ${verse.commentary_text.trim()}`);
  }

  return parts.join(' ');
}

/**
 * Split long content at sentence boundaries to fit within maxTokens.
 * Returns an array of content strings (usually 1, sometimes 2 for very long verses).
 */
function splitAtSentences(content: string, maxTokens: number): string[] {
  if (estimateTokens(content) <= maxTokens) {
    return [content];
  }

  // Split at sentence boundaries
  const sentences = content.split(/(?<=[.!?])\s+/);
  const chunks: string[] = [];
  let current = '';

  for (const sentence of sentences) {
    const candidate = current ? `${current} ${sentence}` : sentence;
    if (estimateTokens(candidate) > maxTokens && current) {
      chunks.push(current);
      current = sentence;
    } else {
      current = candidate;
    }
  }
  if (current) chunks.push(current);

  return chunks.length > 0 ? chunks : [content];
}

/**
 * Convert a raw verse into one (or rarely two) ClassicalChunk objects.
 *
 * @param verse - parsed verse from the classical text parser
 * @param maxTokens - maximum tokens per chunk (default 400)
 * @returns array of chunks (typically 1)
 */
export function chunkVerse(verse: RawVerse, maxTokens = 400): ClassicalChunk[] {
  const content = buildVerseContent(verse);
  const sourceCid = `classical_texts/${verse.work}`;
  const baseChunkId = `classical_texts/${verse.verse_id}`;

  const contentParts = splitAtSentences(content, maxTokens);

  return contentParts.map((part, idx) => {
    const chunkId = idx === 0 ? baseChunkId : `${baseChunkId}_p${idx + 1}`;
    return {
      chunk_id: chunkId,
      source_canonical_id: sourceCid,
      content: part,
      token_count: estimateTokens(part),
      verse,
    };
  });
}

/**
 * Chunk an entire chapter's verses.
 *
 * @param verses - array of raw verse objects for the chapter
 * @param maxTokens - maximum tokens per chunk
 * @returns flat array of ClassicalChunk objects
 */
export function chunkChapter(verses: RawVerse[], maxTokens = 400): ClassicalChunk[] {
  return verses.flatMap(v => chunkVerse(v, maxTokens));
}

/**
 * Parse BPHS djvu.txt OCR output into structured verse records.
 *
 * The djvu.txt format has:
 *   - "Chapter N" headers (appearing multiple times as page headers)
 *   - Verse ranges like "5-8. text here..." or "20. text here..."
 *   - Sanskrit lines (mixed in, can be detected by high non-ASCII ratio)
 *
 * @param text - raw text content of a BPHS volume file
 * @param volumeLabel - "Vol. 1" or "Vol. 2" for attribution
 * @returns array of RawVerse objects
 */
export function parseBphsDjvuText(text: string, volumeLabel = 'Vol. 1'): RawVerse[] {
  // Find chapter boundaries using "Chapter N" at line start
  const chapterPattern = /(?:^|\n)(Chapter\s+(\d+))\s*(?:\n|$)/gm;
  const chapterPositions: Map<number, number> = new Map();

  let match: RegExpExecArray | null;
  while ((match = chapterPattern.exec(text)) !== null) {
    const chNum = parseInt(match[2], 10);
    chapterPositions.set(chNum, match.index); // last occurrence wins (avoids page headers)
  }

  // Sort chapters by position
  const sortedChapters = [...chapterPositions.entries()].sort((a, b) => a[1] - b[1]);

  const verses: RawVerse[] = [];

  for (let i = 0; i < sortedChapters.length; i++) {
    const [chNum, chStart] = sortedChapters[i];
    const chEnd = i + 1 < sortedChapters.length ? sortedChapters[i + 1][1] : text.length;
    const section = text.slice(chStart, chEnd);

    // Extract verse blocks: "N." or "N-M." at line start followed by text
    const versePattern = /^(\d+(?:-\d+)?)\.\s+(.+?)(?=^\d+(?:-\d+)?\.\s|\z)/gms;
    let vMatch: RegExpExecArray | null;

    while ((vMatch = versePattern.exec(section)) !== null) {
      const verseRef = vMatch[1];
      const rawText = vMatch[2].trim().replace(/\s+/g, ' ');

      if (rawText.length < 25) continue; // skip very short TOC artifacts

      const parts = verseRef.split('-');
      const verseStart = parseInt(parts[0], 10);
      const verseEnd = parts.length > 1 ? parseInt(parts[parts.length - 1], 10) : verseStart;

      const verseId = `BPHS.${String(chNum).padStart(2, '0')}.${String(verseStart).padStart(3, '0')}`;

      verses.push({
        work: 'BPHS',
        chapter: chNum,
        verse_start: verseStart,
        verse_end: verseEnd,
        verse_ref: `${chNum}.${verseRef}`,
        verse_id: verseId,
        translation_text: rawText,
        source_edition: `R. Santhanam / archive.org (BPHSEnglish ${volumeLabel})`,
      });
    }
  }

  return verses;
}

/**
 * Deduplicate verses by verse_id, keeping the last occurrence.
 * Used when merging Vol. 1 and Vol. 2 which may share chapter headers.
 */
export function deduplicateVerses(verses: RawVerse[]): RawVerse[] {
  const seen = new Map<string, RawVerse>();
  for (const v of verses) {
    seen.set(v.verse_id, v); // last occurrence wins
  }
  return [...seen.values()];
}
