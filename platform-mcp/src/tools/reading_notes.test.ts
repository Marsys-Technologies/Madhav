/**
 * reading_notes.test.ts — D-2 Lane V-3, CR-38/71/80 (ledger row 25).
 */
import { describe, it, expect } from 'vitest'
import { readingNotesFor, READING_NOTES_482012F1 } from './reading_notes.js'

describe('reading_notes — CR-38/71/80', () => {
  it('serves verified notes for 482012f1 matching the register content', () => {
    const n = readingNotesFor('482012f1-710e-4a25-994a-93821f5871aa')
    expect(n).toBe(READING_NOTES_482012F1)
    // load-bearing register facts present
    expect(n).toContain('Dhana Yoga')
    expect(n).toContain('Ketu MD')
    expect(n).toContain('Karakāṁśa = Gemini')
    expect(n).toContain('Wealth-loss mechanism')
  })
  it('returns null (honest empty) for a chart with no logged notes', () => {
    expect(readingNotesFor('00000000-0000-0000-0000-000000000000')).toBeNull()
  })
})
