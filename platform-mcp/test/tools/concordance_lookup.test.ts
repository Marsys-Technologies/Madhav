/**
 * concordance_lookup.test.ts
 * Brahmagyan Concordance (BG-0-7) — unit tests for concordance.lookup tool.
 *
 * Tests cover:
 *   1. Input schema validation
 *   2. Stance derivation logic (agree / qualify / conflict / absent)
 *   3. Topic coverage (all 4 schools represented per topic)
 *   4. Conflict-surfacing (conflicts not flattened)
 *   5. Tool smoke: concordance.lookup returns correct envelope shape
 *   6. FORENSIC: "Sun in 2nd house" returns stances from BPHS + Jaimini + KP + Tajaka
 *
 * DB calls are mocked — these tests are offline-safe.
 *
 * [BRAHMA-BG-0-7]
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  ConcordanceLookupInputSchema,
  buildEnvelope,
} from '../../src/tools/concordance_lookup.js'

// ── Mock pg pool ──────────────────────────────────────────────────────────────

const mockQuery = vi.fn()
const mockPool = { query: mockQuery }

vi.mock('pg', () => ({
  default: {
    Pool: vi.fn(() => mockPool),
  },
}))

process.env['DATABASE_URL'] = 'postgresql://test:test@localhost:5432/test'

import { lookupConcordance } from '../../src/tools/concordance_lookup.js'

// ── Fixtures ──────────────────────────────────────────────────────────────────

interface RawRow {
  topic: string
  topic_slug: string
  topic_category: string
  grahas: string[]
  rasis: string[]
  bhavas: number[]
  school: string
  stance: string
  assertion_summary: string
  stance_note: string
  rules_cited: string[]
  rule_count: number
  primary_rule_id: string | null
  source_works: string[]
  verse_refs: string[]
  stance_confidence: string
  conflict_severity: string | null
}

function makeStanceRow(overrides: Partial<RawRow> = {}): RawRow {
  return {
    topic: 'Sun in 2nd house',
    topic_slug: 'sun_2nd_house',
    topic_category: 'placement',
    grahas: ['SUN'],
    rasis: [],
    bhavas: [2],
    school: 'parashari',
    stance: 'agree',
    assertion_summary:
      'Sun in the 2nd bhava indicates strong speech and wealth potential; may cause harshness.',
    stance_note: 'This school has 2 rule(s) on this topic. Avg confidence: 0.720.',
    rules_cited: ['BPHS.25.003.R001', 'BPHS.25.004.R002'],
    rule_count: 2,
    primary_rule_id: 'BPHS.25.003.R001',
    source_works: ['BPHS'],
    verse_refs: ['25.3-4'],
    stance_confidence: '0.720',
    conflict_severity: null,
    ...overrides,
  }
}

function makeAbsentRow(school: string): RawRow {
  return makeStanceRow({
    school,
    stance: 'absent',
    assertion_summary: '[no rule in pilot scope]',
    stance_note: 'No rule yet extracted for this school on this topic.',
    rules_cited: [],
    rule_count: 0,
    primary_rule_id: null,
    source_works: [],
    verse_refs: [],
    stance_confidence: '0.000',
    conflict_severity: null,
  })
}

// ── §1 — Input schema validation ──────────────────────────────────────────────

describe('ConcordanceLookupInputSchema', () => {
  it('rejects empty topic', () => {
    const result = ConcordanceLookupInputSchema.safeParse({ topic: '' })
    expect(result.success).toBe(false)
  })

  it('accepts minimal topic', () => {
    const result = ConcordanceLookupInputSchema.safeParse({ topic: 'Sun in 2nd house' })
    expect(result.success).toBe(true)
  })

  it('accepts full input with all fields', () => {
    const result = ConcordanceLookupInputSchema.safeParse({
      topic: 'Saturn in Scorpio',
      school: 'parashari',
      stance_filter: 'conflict',
      include_absent: false,
      limit: 3,
    })
    expect(result.success).toBe(true)
  })

  it('rejects unknown school', () => {
    const result = ConcordanceLookupInputSchema.safeParse({
      topic: 'Sun in 2nd house',
      school: 'unknown_school',
    })
    expect(result.success).toBe(false)
  })

  it('rejects unknown stance_filter', () => {
    const result = ConcordanceLookupInputSchema.safeParse({
      topic: 'Sun in 2nd house',
      stance_filter: 'maybe',
    })
    expect(result.success).toBe(false)
  })

  it('rejects limit=0', () => {
    const result = ConcordanceLookupInputSchema.safeParse({
      topic: 'Sun in 2nd house',
      limit: 0,
    })
    expect(result.success).toBe(false)
  })

  it('rejects limit=21 (over max)', () => {
    const result = ConcordanceLookupInputSchema.safeParse({
      topic: 'Sun in 2nd house',
      limit: 21,
    })
    expect(result.success).toBe(false)
  })

  it('valid stances: agree, qualify, conflict, absent', () => {
    for (const stance of ['agree', 'qualify', 'conflict', 'absent']) {
      const result = ConcordanceLookupInputSchema.safeParse({
        topic: 'Sun in 2nd house',
        stance_filter: stance,
      })
      expect(result.success).toBe(true)
    }
  })

  it('valid schools: parashari, jaimini, kp, tajaka', () => {
    for (const school of ['parashari', 'jaimini', 'kp', 'tajaka']) {
      const result = ConcordanceLookupInputSchema.safeParse({
        topic: 'Sun in 2nd house',
        school,
      })
      expect(result.success).toBe(true)
    }
  })
})

// ── §2 — Envelope shape ───────────────────────────────────────────────────────

describe('buildEnvelope', () => {
  it('returns correct top-level shape', () => {
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = buildEnvelope(input, [])

    expect(envelope).toHaveProperty('query')
    expect(envelope).toHaveProperty('topics')
    expect(envelope).toHaveProperty('total_topics_found')
    expect(envelope).toHaveProperty('total_stances_returned')
    expect(envelope).toHaveProperty('conflict_topics')
    expect(envelope).toHaveProperty('provenance')
    expect(envelope).toHaveProperty('pilot_note')
  })

  it('provenance.asset_id is brahmagyan.concordance', () => {
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = buildEnvelope(input, [])
    expect(envelope.provenance.asset_id).toBe('brahmagyan.concordance')
  })

  it('provenance.asset_version is BG-0-7', () => {
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = buildEnvelope(input, [])
    expect(envelope.provenance.asset_version).toBe('BG-0-7')
  })

  it('provenance.schools contains all 4 schools', () => {
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = buildEnvelope(input, [])
    expect(envelope.provenance.schools).toEqual(['parashari', 'jaimini', 'kp', 'tajaka'])
  })

  it('empty result returns total_topics_found=0 with pilot_note', () => {
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = buildEnvelope(input, [])
    expect(envelope.total_topics_found).toBe(0)
    expect(envelope.pilot_note).toContain('No concordance entries found')
  })
})

// ── §3 — Topic coverage ────────────────────────────────────────────────────────

describe('topic coverage', () => {
  it('groups stances by topic_slug correctly', () => {
    const rows = [
      makeStanceRow({ school: 'parashari', stance: 'agree' }),
      makeAbsentRow('jaimini'),
      makeAbsentRow('kp'),
      makeAbsentRow('tajaka'),
    ]
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = buildEnvelope(input, rows)

    expect(envelope.total_topics_found).toBe(1)
    expect(envelope.topics[0]!.school_stances).toHaveLength(4)
  })

  it('each school_stance has required fields', () => {
    const rows = [
      makeStanceRow({ school: 'parashari', stance: 'agree' }),
    ]
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = buildEnvelope(input, rows)
    const stance = envelope.topics[0]!.school_stances[0]!

    expect(stance).toHaveProperty('school')
    expect(stance).toHaveProperty('stance')
    expect(stance).toHaveProperty('assertion_summary')
    expect(stance).toHaveProperty('stance_note')
    expect(stance).toHaveProperty('rules_cited')
    expect(stance).toHaveProperty('rule_count')
    expect(stance).toHaveProperty('source_works')
    expect(stance).toHaveProperty('verse_refs')
    expect(stance).toHaveProperty('stance_confidence')
    expect(stance).toHaveProperty('conflict_severity')
  })

  it('counts schools_present and schools_absent correctly', () => {
    const rows = [
      makeStanceRow({ school: 'parashari', stance: 'agree' }),
      makeAbsentRow('jaimini'),
      makeAbsentRow('kp'),
      makeAbsentRow('tajaka'),
    ]
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = buildEnvelope(input, rows)
    const topic = envelope.topics[0]!

    expect(topic.schools_present).toBe(1)
    expect(topic.schools_absent).toBe(3)
  })

  it('handles multiple topics correctly', () => {
    const rows = [
      makeStanceRow({ topic: 'Sun in 2nd house', topic_slug: 'sun_2nd_house', school: 'parashari' }),
      makeStanceRow({ topic: 'Moon in Cancer', topic_slug: 'moon_in_cancer', school: 'parashari', grahas: ['MOON'], rasis: ['CANCER'], bhavas: [] }),
    ]
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun' })
    const envelope = buildEnvelope(input, rows)

    expect(envelope.total_topics_found).toBe(2)
  })
})

// ── §4 — Conflict surfacing ────────────────────────────────────────────────────

describe('conflict surfacing', () => {
  it('detects has_conflict when any school has conflict stance', () => {
    const rows = [
      makeStanceRow({ school: 'parashari', stance: 'agree' }),
      makeStanceRow({
        school: 'kp',
        stance: 'conflict',
        conflict_severity: 'significant',
        assertion_summary: 'KP disagrees: Sun in 2nd causes financial loss.',
        stance_note: 'KP: opposing view based on sublord theory.',
      }),
      makeAbsentRow('jaimini'),
      makeAbsentRow('tajaka'),
    ]
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = buildEnvelope(input, rows)
    const topic = envelope.topics[0]!

    expect(topic.has_conflict).toBe(true)
    expect(topic.conflict_schools).toContain('kp')
  })

  it('does NOT flatten conflicts — both stances appear in school_stances', () => {
    const rows = [
      makeStanceRow({ school: 'parashari', stance: 'agree' }),
      makeStanceRow({
        school: 'kp',
        stance: 'conflict',
        assertion_summary: 'Opposing view.',
        conflict_severity: 'significant',
      }),
      makeAbsentRow('jaimini'),
      makeAbsentRow('tajaka'),
    ]
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = buildEnvelope(input, rows)
    const topic = envelope.topics[0]!

    const agreeStance = topic.school_stances.find(s => s.school === 'parashari')
    const conflictStance = topic.school_stances.find(s => s.school === 'kp')

    expect(agreeStance?.stance).toBe('agree')
    expect(conflictStance?.stance).toBe('conflict')
    expect(conflictStance?.conflict_severity).toBe('significant')
  })

  it('conflict_topics count is accurate', () => {
    const rows = [
      makeStanceRow({ topic: 'Sun in 2nd house', topic_slug: 'sun_2nd_house', school: 'parashari', stance: 'agree' }),
      makeStanceRow({ topic: 'Sun in 2nd house', topic_slug: 'sun_2nd_house', school: 'kp', stance: 'conflict', conflict_severity: 'significant' }),
      makeStanceRow({ topic: 'Moon in Cancer', topic_slug: 'moon_in_cancer', school: 'parashari', stance: 'agree', grahas: ['MOON'], rasis: ['CANCER'], bhavas: [] }),
    ]
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun' })
    const envelope = buildEnvelope(input, rows)

    expect(envelope.conflict_topics).toBe(1)
  })

  it('has_conflict is false when no school has conflict stance', () => {
    const rows = [
      makeStanceRow({ school: 'parashari', stance: 'agree' }),
      makeStanceRow({ school: 'kp', stance: 'qualify' }),
      makeAbsentRow('jaimini'),
      makeAbsentRow('tajaka'),
    ]
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = buildEnvelope(input, rows)
    const topic = envelope.topics[0]!

    expect(topic.has_conflict).toBe(false)
    expect(topic.conflict_schools).toHaveLength(0)
  })

  it('conflict_severity is preserved from input row', () => {
    const rows = [
      makeStanceRow({
        school: 'jaimini',
        stance: 'conflict',
        conflict_severity: 'fundamental',
        assertion_summary: 'Jaimini reverses the expected result entirely.',
      }),
    ]
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = buildEnvelope(input, rows)
    const conflictStance = envelope.topics[0]!.school_stances.find(s => s.school === 'jaimini')

    expect(conflictStance?.conflict_severity).toBe('fundamental')
  })
})

// ── §5 — Absent stances ───────────────────────────────────────────────────────

describe('absent stances', () => {
  it('absent stances are included by default (include_absent=true)', () => {
    const rows = [
      makeAbsentRow('parashari'),
      makeAbsentRow('jaimini'),
      makeAbsentRow('kp'),
      makeAbsentRow('tajaka'),
    ]
    const input = ConcordanceLookupInputSchema.parse({
      topic: 'Sun in 2nd house',
      include_absent: true,
    })
    const envelope = buildEnvelope(input, rows)
    expect(envelope.topics[0]!.schools_absent).toBe(4)
    expect(envelope.topics[0]!.school_stances).toHaveLength(4)
  })

  it('stance_confidence is 0.000 for absent stances', () => {
    const rows = [makeAbsentRow('jaimini')]
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = buildEnvelope(input, rows)
    const absent = envelope.topics[0]!.school_stances.find(s => s.school === 'jaimini')

    expect(absent?.stance_confidence).toBe(0.0)
    expect(absent?.rules_cited).toHaveLength(0)
    expect(absent?.rule_count).toBe(0)
  })
})

// ── §6 — Tool smoke: DB mock ──────────────────────────────────────────────────

describe('tool smoke (mocked DB)', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('returns empty topics when no slug matches', async () => {
    // Slug match query returns 0 rows
    mockQuery.mockResolvedValueOnce({ rows: [] })

    const input = ConcordanceLookupInputSchema.parse({ topic: 'Nonexistent topic xyz' })
    const envelope = await lookupConcordance(input)

    expect(envelope.total_topics_found).toBe(0)
    expect(envelope.pilot_note).toContain('No concordance entries found')
  })

  it('returns stances when topic matches', async () => {
    const slugRows = [{ topic_slug: 'sun_2nd_house', rank: 100 }]
    const stanceRows = [
      makeStanceRow({ school: 'parashari', stance: 'agree' }),
      makeAbsentRow('jaimini'),
      makeAbsentRow('kp'),
      makeAbsentRow('tajaka'),
    ]

    // First call: slug search; second call: stance fetch
    mockQuery
      .mockResolvedValueOnce({ rows: slugRows })
      .mockResolvedValueOnce({ rows: stanceRows })

    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = await lookupConcordance(input)

    expect(envelope.total_topics_found).toBe(1)
    expect(envelope.total_stances_returned).toBe(4)
    expect(envelope.topics[0]!.topic_slug).toBe('sun_2nd_house')
  })

  it('envelope query field reflects input accurately', async () => {
    mockQuery.mockResolvedValueOnce({ rows: [] })

    const input = ConcordanceLookupInputSchema.parse({
      topic: 'Saturn in Scorpio',
      school: 'kp',
      stance_filter: 'conflict',
      include_absent: false,
    })
    const envelope = await lookupConcordance(input)

    expect(envelope.query.topic).toBe('Saturn in Scorpio')
    expect(envelope.query.school).toBe('kp')
    expect(envelope.query.stance_filter).toBe('conflict')
    expect(envelope.query.include_absent).toBe(false)
  })

  it('does not throw on DB error — propagates error', async () => {
    mockQuery.mockRejectedValueOnce(new Error('DB connection refused'))

    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    await expect(lookupConcordance(input)).rejects.toThrow('DB connection refused')
  })
})

// ── §7 — FORENSIC: "Sun in 2nd house" returns all 4 schools ──────────────────

describe('FORENSIC: concordance.lookup("Sun in 2nd house")', () => {
  beforeEach(() => {
    mockQuery.mockReset()
  })

  it('returns stances from all 4 schools (BPHS=parashari, Jaimini, KP, Tajaka)', async () => {
    const slugRows = [{ topic_slug: 'sun_2nd_house', rank: 100 }]
    const stanceRows = [
      makeStanceRow({ school: 'parashari', stance: 'agree' }),
      makeAbsentRow('jaimini'),
      makeAbsentRow('kp'),
      makeAbsentRow('tajaka'),
    ]

    mockQuery
      .mockResolvedValueOnce({ rows: slugRows })
      .mockResolvedValueOnce({ rows: stanceRows })

    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = await lookupConcordance(input)

    expect(envelope.total_topics_found).toBe(1)

    const topic = envelope.topics[0]!
    const schools = topic.school_stances.map(s => s.school)

    expect(schools).toContain('parashari')   // BPHS
    expect(schools).toContain('jaimini')     // Jaimini Sutram
    expect(schools).toContain('kp')          // KP
    expect(schools).toContain('tajaka')      // Tajaka
  })

  it('parashari stance is "agree" with rules_cited for Sun in 2nd house', async () => {
    const slugRows = [{ topic_slug: 'sun_2nd_house', rank: 100 }]
    const stanceRows = [
      makeStanceRow({
        school: 'parashari',
        stance: 'agree',
        rules_cited: ['BPHS.25.003.R001', 'BPHS.25.004.R002'],
        rule_count: 2,
      }),
      makeAbsentRow('jaimini'),
      makeAbsentRow('kp'),
      makeAbsentRow('tajaka'),
    ]

    mockQuery
      .mockResolvedValueOnce({ rows: slugRows })
      .mockResolvedValueOnce({ rows: stanceRows })

    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = await lookupConcordance(input)

    const parashari = envelope.topics[0]!.school_stances.find(s => s.school === 'parashari')
    expect(parashari?.stance).toBe('agree')
    expect(parashari?.rules_cited.length).toBeGreaterThan(0)
  })

  it('absent schools carry rules_cited=[] and rule_count=0', async () => {
    const slugRows = [{ topic_slug: 'sun_2nd_house', rank: 100 }]
    const stanceRows = [
      makeStanceRow({ school: 'parashari', stance: 'agree' }),
      makeAbsentRow('jaimini'),
      makeAbsentRow('kp'),
      makeAbsentRow('tajaka'),
    ]

    mockQuery
      .mockResolvedValueOnce({ rows: slugRows })
      .mockResolvedValueOnce({ rows: stanceRows })

    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = await lookupConcordance(input)
    const topic = envelope.topics[0]!

    for (const school of ['jaimini', 'kp', 'tajaka']) {
      const stance = topic.school_stances.find(s => s.school === school)
      expect(stance?.stance).toBe('absent')
      expect(stance?.rules_cited).toHaveLength(0)
      expect(stance?.rule_count).toBe(0)
      expect(stance?.stance_confidence).toBe(0.0)
    }
  })

  it('lineage_summary notes schools that have rules', async () => {
    const slugRows = [{ topic_slug: 'sun_2nd_house', rank: 100 }]
    const stanceRows = [
      makeStanceRow({ school: 'parashari', stance: 'agree', rule_count: 2 }),
      makeAbsentRow('jaimini'),
      makeAbsentRow('kp'),
      makeAbsentRow('tajaka'),
    ]

    mockQuery
      .mockResolvedValueOnce({ rows: slugRows })
      .mockResolvedValueOnce({ rows: stanceRows })

    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = await lookupConcordance(input)
    const topic = envelope.topics[0]!

    expect(topic.lineage_summary).toContain('school(s) have rules')
  })

  it('has_conflict is false for Sun in 2nd house (pilot scope — no cross-school conflict yet)', async () => {
    const slugRows = [{ topic_slug: 'sun_2nd_house', rank: 100 }]
    const stanceRows = [
      makeStanceRow({ school: 'parashari', stance: 'agree' }),
      makeAbsentRow('jaimini'),
      makeAbsentRow('kp'),
      makeAbsentRow('tajaka'),
    ]

    mockQuery
      .mockResolvedValueOnce({ rows: slugRows })
      .mockResolvedValueOnce({ rows: stanceRows })

    const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
    const envelope = await lookupConcordance(input)

    expect(envelope.conflict_topics).toBe(0)
    expect(envelope.topics[0]!.has_conflict).toBe(false)
  })
})

// ── §8 — Stance type coverage ─────────────────────────────────────────────────

describe('stance types', () => {
  const STANCES = ['agree', 'qualify', 'conflict', 'absent'] as const

  for (const stance of STANCES) {
    it(`stance type "${stance}" is valid and preserved in envelope`, () => {
      const row = makeStanceRow({
        school: 'parashari',
        stance,
        conflict_severity: stance === 'conflict' ? 'significant' : null,
      })
      const input = ConcordanceLookupInputSchema.parse({ topic: 'Sun in 2nd house' })
      const envelope = buildEnvelope(input, [row])
      const result = envelope.topics[0]!.school_stances[0]!
      expect(result.stance).toBe(stance)
    })
  }
})

// ── §9 — Query field echo ──────────────────────────────────────────────────────

describe('query field echo', () => {
  it('query.topic matches input topic', () => {
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Jupiter in Sagittarius' })
    const envelope = buildEnvelope(input, [])
    expect(envelope.query.topic).toBe('Jupiter in Sagittarius')
  })

  it('query.school is null when not specified', () => {
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Jupiter in Sagittarius' })
    const envelope = buildEnvelope(input, [])
    expect(envelope.query.school).toBeNull()
  })

  it('query.stance_filter is null when not specified', () => {
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Jupiter in Sagittarius' })
    const envelope = buildEnvelope(input, [])
    expect(envelope.query.stance_filter).toBeNull()
  })

  it('query.include_absent defaults to true', () => {
    const input = ConcordanceLookupInputSchema.parse({ topic: 'Jupiter in Sagittarius' })
    const envelope = buildEnvelope(input, [])
    expect(envelope.query.include_absent).toBe(true)
  })
})
