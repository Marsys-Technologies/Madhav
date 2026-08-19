/**
 * PB-3.1 G1 — the MOUNT GUARD. The regression detector PB-3 did not have.
 *
 * `REPORT_PB-3.md` closed the whole wave SHIP-DEGRADED for exactly one reason: every lane's own
 * tests passed while the loop's entry point was **imported by nothing**. Six real detections
 * ran in production and `brahma_mimamsa_prediction_ledger` stayed at zero rows, because no test
 * anywhere asserted that the capture is actually WIRED into a live route. Unit-testing a writer
 * proves the writer works; it says nothing about whether anything calls it.
 *
 * This file is the missing assertion, and it is deliberately the cheapest possible kind: a
 * source-level read of the live route with NO database and NO network, so it runs on every PR in
 * CI unconditionally — unlike the DB-integration tests, which are env-gated (PB-3.1 G3) and
 * were therefore skipped for the entire PB-3 wave. Precedent for the shape:
 * `tests/integration/chat-v2/regenerate_truncation.test.ts`.
 *
 * ## Honest bounds of this check (per §N.8 — a lint must state its own limits)
 *
 * It proves the call site EXISTS in the shipped route source and that the capture module is
 * imported there. It does NOT prove the route executes (the flag could be off), that the write
 * succeeds against production, or that the row renders. Those are A1/A2's live proofs and
 * cannot be made from a source read. What it *does* catch is precisely the failure mode that
 * cost PB-3 the wave: a refactor that silently orphans the entry point again.
 */

import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import path from 'node:path'

import { readRouteSurface } from '../route_surface'

const ROOT = path.resolve(__dirname, '../../..')
const readSrc = (rel: string) => readFileSync(path.join(ROOT, rel), 'utf8')

describe('PB-3.1 G1 — the prediction loop has a live entry point', () => {
  // P0-C / RF-1: the reading pipeline moved out of the 1,179-line route.ts into
  // typed stage modules the shell composes. The guard's question is unchanged
  // ("is the capture wired into the LIVE reading route?"); the surface it reads
  // is now the shell plus every stage module the shell actually imports — see
  // tests/pariprashna/route_surface.ts for why that keeps the detector honest
  // rather than making it pass vacuously.
  const routeSrc = readRouteSurface()

  it('the live Paripraśna reading route imports the SAMĪKṢĀ capture', () => {
    expect(routeSrc).toMatch(
      /import\s*\{[^}]*captureDetectedCandidates[^}]*\}\s*from\s*'@\/lib\/pariprashna\/samiksha\/capture'/,
    )
  })

  it('the route CALLS it — an import alone is what PB-3 mistook for a mount', () => {
    // Strip the import line, then require a real call expression to survive.
    const body = routeSrc.replace(/^import[\s\S]*?from\s*'[^']*'\s*$/gm, '')
    expect(body).toMatch(/captureDetectedCandidates\s*\(/)
  })

  it('the call is inside the turn-commit persistence path, not a dead branch', () => {
    const callIdx = routeSrc.indexOf('captureDetectedCandidates({')
    const writeTurnIdx = routeSrc.indexOf('await writeTurn(canonicalMessage, canonicalParts)')
    expect(writeTurnIdx).toBeGreaterThan(-1)
    expect(callIdx).toBeGreaterThan(writeTurnIdx) // capture happens AFTER the parts are committed
  })

  it('the capture is passed the persisted turn id and the detected candidates', () => {
    const call = routeSrc.slice(
      routeSrc.indexOf('captureDetectedCandidates({'),
      routeSrc.indexOf('captureDetectedCandidates({') + 600,
    )
    expect(call).toContain('messageId: assistantMessageId')
    expect(call).toContain('candidates: predictionCandidatesFound')
    expect(call).toContain('chartId')
    // The D-16 now-date, not a fresh wall-clock read — relative horizons must anchor to the turn.
    expect(call).toContain('nowDate: provenanceStamp.now_context_date')
  })

  it('a capture failure cannot cost the reader their turn (it is caught, not propagated)', () => {
    const idx = routeSrc.indexOf('captureDetectedCandidates({')
    // Look backwards for the nearest `try {` and forwards for the matching catch.
    const before = routeSrc.slice(Math.max(0, idx - 400), idx)
    const after = routeSrc.slice(idx, idx + 1200)
    expect(before).toMatch(/try\s*\{\s*$/m)
    expect(after).toMatch(/catch\s*\(/)
  })

  it('writes `detected`, never `confirmed` — W-1 forbids auto-promotion', () => {
    const captureSrc = readSrc('src/lib/pariprashna/samiksha/capture.ts')
    expect(captureSrc).toContain("initial_status: 'detected'")
    expect(captureSrc).not.toContain("initial_status: 'confirmed'")
    // No stamp is copied at detection — the stamp is a confirmation-time artefact (D-16(d)).
    expect(captureSrc).not.toMatch(/\bstamp:\s/)
  })
})
