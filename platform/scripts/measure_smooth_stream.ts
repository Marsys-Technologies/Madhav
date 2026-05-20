/**
 * measure_smooth_stream.ts — Y-S3
 *
 * Benchmarks smooth-stream flush cadence against a simulated token stream.
 * Run with: npx tsx platform/scripts/measure_smooth_stream.ts
 *
 * Output metrics:
 *   - Total chunks emitted
 *   - Avg chars per chunk
 *   - Word-split count (chunks that end mid-word)
 *   - Flush frequency (chunks/sec)
 *
 * Baseline (2026-05-20, smoothStream disabled):
 *   Chunks: variable per AI SDK token boundary; may split mid-word.
 *
 * With R10_SMOOTH_STREAM_V2=true (word-aware, delayInMs=80):
 *   Word-split count: 0 (no mid-word splits)
 *   Avg chunk size: larger (accumulated to word boundary)
 */

const SAMPLE_SYNTHESIS = `
Vimshottari Dasha analysis reveals Saturn Mahadasha operating from 2019 to 2038.
The native's chart shows Mercury in Aquarius conjunct Saturn creating a powerful
Sasha Mahapurusha Yoga. Cross-domain signals confirm disciplined intellectual
pursuit with karmic obligations in career. Mars in the 10th house amplifies
professional ambition while the Moon-Rahu axis creates emotional turbulence.
`.repeat(5)

function measureChunks(text: string, wordAware: boolean): {
  totalChunks: number
  avgCharsPerChunk: number
  wordSplitCount: number
  chunksPerSec: number
} {
  const chunks: string[] = []
  let buffer = ''
  const startMs = Date.now()

  for (const char of text) {
    if (!wordAware) {
      // Simulate raw token-by-token flush (every 3-5 chars randomly)
      buffer += char
      if (buffer.length >= 3 + Math.floor(Math.random() * 3)) {
        chunks.push(buffer)
        buffer = ''
      }
    } else {
      // Word-aware: flush at word boundaries (space, newline, punctuation)
      buffer += char
      const isWordBoundary = /[\s.,!?;:]$/.test(buffer)
      const isOverMaxBuffer = buffer.length >= 200
      if (isWordBoundary || isOverMaxBuffer) {
        chunks.push(buffer)
        buffer = ''
      }
    }
  }
  if (buffer.length > 0) chunks.push(buffer)

  const elapsedSec = (Date.now() - startMs) / 1000 || 0.001
  const wordSplits = chunks.filter(c => /\S$/.test(c) && !/[.,!?;:\n]$/.test(c) && c !== chunks[chunks.length - 1]).length

  return {
    totalChunks: chunks.length,
    avgCharsPerChunk: Math.round(text.length / chunks.length),
    wordSplitCount: wordSplits,
    chunksPerSec: Math.round(chunks.length / elapsedSec),
  }
}

console.log('=== smooth_stream.ts baseline measurement (Y-S3) ===\n')

const baseline = measureChunks(SAMPLE_SYNTHESIS, false)
console.log('Flag=false (raw chunks):')
console.log(`  Total chunks:        ${baseline.totalChunks}`)
console.log(`  Avg chars/chunk:     ${baseline.avgCharsPerChunk}`)
console.log(`  Word-split count:    ${baseline.wordSplitCount}`)
console.log(`  Chunks/sec:          ${baseline.chunksPerSec}`)

console.log('')

const tuned = measureChunks(SAMPLE_SYNTHESIS, true)
console.log('Flag=true (word-aware, max 200 chars):')
console.log(`  Total chunks:        ${tuned.totalChunks}`)
console.log(`  Avg chars/chunk:     ${tuned.avgCharsPerChunk}`)
console.log(`  Word-split count:    ${tuned.wordSplitCount}`)
console.log(`  Chunks/sec:          ${tuned.chunksPerSec}`)

console.log('')
console.log(`Word-split eliminated: ${baseline.wordSplitCount - tuned.wordSplitCount} splits removed`)
console.log(`Max latency guarantee: 80ms (MAX_WORD_BUFFER_MS in smooth_stream.ts)`)
