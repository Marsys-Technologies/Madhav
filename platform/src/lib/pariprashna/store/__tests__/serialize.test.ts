import { describe, it, expect } from 'vitest'
import {
  serializeCanonical,
  serializeCanonicalObject,
  canonicalizeValue,
} from '../serialize'
import type { CanonicalMessage, MessagePartInput } from '../schema'

// A fixed logical message used across the determinism tests.
const MESSAGE: CanonicalMessage = {
  id: '11111111-1111-1111-1111-111111111111',
  conversation_id: '22222222-2222-2222-2222-222222222222',
  role: 'assistant',
  schema_version: 1,
  model_id: 'claude-opus-4-8[1m]',
  provider: 'anthropic',
}

// The same three logical parts, authored in seq order 0,1,2.
const PARTS_IN_ORDER: MessagePartInput[] = [
  { seq: 0, kind: 'text', body: { text: 'Your Moon is in Purva Bhadrapada.' }, model_visible: true },
  {
    seq: 1,
    kind: 'tool_call',
    body: { call_id: 'c1', tool_name: 'ganita_nakshatra_get', args: { chart_id: 'x', planet: 'Moon' } },
    model_visible: false,
  },
  {
    seq: 2,
    kind: 'citation',
    body: { index: 1, signal_id: 'SIG.MSR.042', layer: 'L2', snippet: 'Moon–PBhadra' },
    model_visible: true,
  },
]

/** Deterministic shuffle (Fisher–Yates with a seeded LCG) — no randomness escapes the test. */
function seededShuffle<T>(arr: readonly T[], seed: number): T[] {
  const out = [...arr]
  let s = seed
  const next = () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff
    return s / 0x7fffffff
  }
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(next() * (i + 1))
    ;[out[i], out[j]] = [out[j], out[i]]
  }
  return out
}

/** Rebuild an object with keys inserted in a rotated order — same logical content. */
function reorderKeys<T extends Record<string, unknown>>(obj: T, rotate: number): T {
  const keys = Object.keys(obj)
  const rotated = [...keys.slice(rotate), ...keys.slice(0, rotate)]
  const out: Record<string, unknown> = {}
  for (const k of rotated) out[k] = obj[k]
  return out as T
}

describe('canonicalizeValue', () => {
  it('sorts object keys recursively', () => {
    const a = canonicalizeValue({ b: 1, a: { d: 4, c: 3 } })
    expect(JSON.stringify(a)).toBe('{"a":{"c":3,"d":4},"b":1}')
  })

  it('preserves array order (arrays are ordered data)', () => {
    const a = canonicalizeValue([{ b: 2, a: 1 }, { z: 26 }])
    expect(JSON.stringify(a)).toBe('[{"a":1,"b":2},{"z":26}]')
  })

  it('drops undefined properties (absent === explicitly-undefined)', () => {
    expect(JSON.stringify(canonicalizeValue({ a: 1, b: undefined }))).toBe('{"a":1}')
  })
})

describe('serializeCanonical — determinism', () => {
  it('is stable across repeated calls with identical input', () => {
    const a = serializeCanonical(MESSAGE, PARTS_IN_ORDER)
    const b = serializeCanonical(MESSAGE, PARTS_IN_ORDER)
    expect(a).toBe(b)
  })

  it('PROPERTY: byte-identical regardless of part ARRAY order (10 shuffles)', () => {
    const golden = serializeCanonical(MESSAGE, PARTS_IN_ORDER)
    for (let seed = 1; seed <= 10; seed++) {
      const shuffled = seededShuffle(PARTS_IN_ORDER, seed)
      expect(serializeCanonical(MESSAGE, shuffled)).toBe(golden)
    }
  })

  it('PROPERTY: byte-identical regardless of object KEY insertion order', () => {
    const golden = serializeCanonical(MESSAGE, PARTS_IN_ORDER)

    // Reorder the message keys and every part's top-level + body keys.
    for (let rot = 1; rot <= 5; rot++) {
      const msgReordered = reorderKeys(MESSAGE as Record<string, unknown>, rot) as unknown as CanonicalMessage
      const partsReordered: MessagePartInput[] = PARTS_IN_ORDER.map((p) => {
        const bodyReordered = reorderKeys(p.body as Record<string, unknown>, rot)
        return reorderKeys(
          { ...p, body: bodyReordered } as unknown as Record<string, unknown>,
          rot,
        ) as unknown as MessagePartInput
      })
      expect(serializeCanonical(msgReordered, partsReordered)).toBe(golden)
    }
  })

  it('PROPERTY: array order AND key order jointly do not matter', () => {
    const golden = serializeCanonical(MESSAGE, PARTS_IN_ORDER)
    for (let seed = 1; seed <= 8; seed++) {
      const shuffled = seededShuffle(PARTS_IN_ORDER, seed).map((p, i) => {
        const bodyReordered = reorderKeys(p.body as Record<string, unknown>, (seed + i) % 3)
        return { ...p, body: bodyReordered } as MessagePartInput
      })
      expect(serializeCanonical(MESSAGE, shuffled)).toBe(golden)
    }
  })

  it('EXCLUDES non-shared fields (part id, created_at, message metadata)', () => {
    // A "persisted" view carries DB-assigned id/created_at + row metadata; the
    // "replay" view does not. Both must serialize identically.
    const persistedParts = PARTS_IN_ORDER.map((p, i) => ({
      ...p,
      id: `aaaaaaaa-0000-0000-0000-00000000000${i}`,
      message_id: MESSAGE.id,
      created_at: '2026-07-28T00:00:00.000Z',
    }))
    const replayString = serializeCanonical(MESSAGE, PARTS_IN_ORDER)
    // A CanonicalMessage may carry metadata; the serializer's input type omits it,
    // so the exclusion is enforced at the type level AND (here) proven at runtime.
    const withMetadata: CanonicalMessage = { ...MESSAGE, metadata: { cost_usd: 0.42, tokens: 1234 } }
    const persistedString = serializeCanonical(withMetadata, persistedParts)
    expect(persistedString).toBe(replayString)
  })

  it('DISTINGUISHES genuinely different content (not a constant)', () => {
    const golden = serializeCanonical(MESSAGE, PARTS_IN_ORDER)
    const changed = serializeCanonical(MESSAGE, [
      ...PARTS_IN_ORDER.slice(0, 2),
      { seq: 2, kind: 'citation', body: { index: 1, signal_id: 'SIG.MSR.999', layer: 'L2', snippet: 'x' }, model_visible: true },
    ])
    expect(changed).not.toBe(golden)
  })

  it('serializeCanonicalObject orders parts by seq even when input is reversed', () => {
    const reversed = [...PARTS_IN_ORDER].reverse()
    const obj = serializeCanonicalObject(MESSAGE, reversed)
    expect(obj.parts.map((p) => p.seq)).toEqual([0, 1, 2])
  })
})
