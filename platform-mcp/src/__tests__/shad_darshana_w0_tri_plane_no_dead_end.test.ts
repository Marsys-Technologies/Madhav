/**
 * shad_darshana_w0_tri_plane_no_dead_end.test.ts — ṢAḌ-DARŚANA W0.6 CI skeleton, item 3
 * (SHAD_DARSHANA_BRIEF_v2_0.md §0.6.3 / §3 W0.6: "tri-plane no-dead-end battery (asserting
 * honest no_lever allowed)").
 *
 * DESIGN AUTHORITY: KALA_SUPREME_ELEVATION_v1_0.md §11 (item 43) — "every served temporal
 * object carries live pointers into the other two planes... or an honest
 * `no_lever (reason)`... CI battery: no view ships a row that dead-ends."
 *
 * This is the UNIT-level half of the battery: it exercises `kala_envelope.ts`'s own
 * `TriPlanePointers` / `pointerTo` / `noLeverPointer` / `isNoLever` shape directly — the
 * ONE implementation every one of the eight kala_* tool facades is contracted to build its
 * envelope from. It needs no live MCP server and is green from the moment this PR lands
 * (unlike the LIVE half, `platform/scripts/census/shad_darshana_gates/
 * tri_plane_no_dead_end_gate.ts`, which calls the real deployed facades once the sibling
 * lanes building them have merged).
 *
 * The invariant under test: for every one of the three tri-plane slots
 * (interpretation_ref / prediction_ref / intervention_ref), a non-null value produced by
 * this library is ALWAYS either (a) a resolvable pointer — `{instrument, hint}`, both
 * non-empty — or (b) an honest `no_lever` — `{no_lever:true, reason}`, reason non-empty.
 * There is no third shape the library can produce; a row that "dead-ends" (a pointer-
 * shaped object missing `hint`, or a `no_lever` missing `reason`) is a build error, not a
 * degraded-but-acceptable state.
 */
import { describe, it, expect } from 'vitest'
import {
  pointerTo,
  noLeverPointer,
  isNoLever,
  type TriPlanePointers,
  type TriPlanePointer,
  type DrillPointerLike,
} from '../lib/kala_envelope.js'

function isWellFormedPointer(p: TriPlanePointer): p is DrillPointerLike {
  return !isNoLever(p) && typeof p.instrument === 'string' && p.instrument.trim().length > 0 && typeof p.hint === 'string' && p.hint.trim().length > 0
}

function isWellFormedNoLever(p: TriPlanePointer): boolean {
  return isNoLever(p) && typeof p.reason === 'string' && p.reason.trim().length > 0
}

/** The no-dead-end assertion this whole battery exists to make: every non-null slot is
 *  EITHER a well-formed pointer OR a well-formed honest no_lever — never anything else. */
function assertNoDeadEnd(pointer: TriPlanePointer | null): void {
  if (pointer === null) return // null is a legal "this object IS that plane already" state
  const ok = isWellFormedPointer(pointer) || isWellFormedNoLever(pointer)
  expect(ok, `dead-end tri-plane pointer: ${JSON.stringify(pointer)}`).toBe(true)
}

describe('ṢAḌ-DARŚANA W0.6 item 3 — tri-plane no-dead-end battery (unit level)', () => {
  it('pointerTo() produces a well-formed resolvable pointer, never a no_lever', () => {
    const p = pointerTo('kala_ahead_get', 'the predictive continuation of this window')
    expect(isNoLever(p)).toBe(false)
    assertNoDeadEnd(p)
  })

  it('noLeverPointer() produces a well-formed honest no_lever, never a bare null smuggled through as a pointer', () => {
    const p = noLeverPointer('this configuration has no intervention lever in the current corpus')
    expect(isNoLever(p)).toBe(true)
    assertNoDeadEnd(p)
  })

  it('a pointer missing `hint` is correctly detected as a dead end (the check has real teeth — it is not vacuously true)', () => {
    const malformed = { instrument: 'kala_elect_get', hint: '' } as DrillPointerLike
    expect(isWellFormedPointer(malformed)).toBe(false)
  })

  it('a no_lever missing `reason` is correctly detected as a dead end (real teeth, not vacuous)', () => {
    const malformed = { no_lever: true, reason: '' } as ReturnType<typeof noLeverPointer>
    expect(isWellFormedNoLever(malformed)).toBe(false)
  })

  it('a fully-populated TriPlanePointers object (a served temporal object with a lever on every plane) has no dead ends', () => {
    const triPlane: TriPlanePointers = {
      interpretation_ref: pointerTo('kala_explain_get', 'why this window is graded this way'),
      prediction_ref: pointerTo('kala_ahead_get', 'the forward continuation of this window'),
      intervention_ref: pointerTo('kala_elect_get', 'the best act-time inside this window'),
    }
    for (const plane of ['interpretation_ref', 'prediction_ref', 'intervention_ref'] as const) {
      assertNoDeadEnd(triPlane[plane])
    }
  })

  it('a TriPlanePointers object with an HONEST no_lever on the intervention plane is a legal, non-dead-end state (brief: "asserting honest no_lever allowed")', () => {
    const triPlane: TriPlanePointers = {
      interpretation_ref: pointerTo('kala_explain_get', 'why this window is graded this way'),
      prediction_ref: pointerTo('kala_ahead_get', 'the forward continuation of this window'),
      intervention_ref: noLeverPointer('no ratified intervention exists for this configuration in the current corpus (not_in_corpus)'),
    }
    for (const plane of ['interpretation_ref', 'prediction_ref', 'intervention_ref'] as const) {
      assertNoDeadEnd(triPlane[plane])
    }
    expect(isNoLever(triPlane.intervention_ref)).toBe(true)
  })

  it('null is legal on a plane that IS the object\'s own plane (e.g. an interpretation-plane object omitting interpretation_ref) — never treated as a dead end by this checker', () => {
    const triPlane: TriPlanePointers = {
      interpretation_ref: null, // this object IS the interpretation plane already
      prediction_ref: pointerTo('kala_ahead_get', 'forward continuation'),
      intervention_ref: noLeverPointer('no lever yet — structural prior only'),
    }
    expect(() => {
      for (const plane of ['interpretation_ref', 'prediction_ref', 'intervention_ref'] as const) {
        assertNoDeadEnd(triPlane[plane])
      }
    }).not.toThrow()
  })
})
