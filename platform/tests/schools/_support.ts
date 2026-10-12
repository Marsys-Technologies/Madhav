import type { Domain, SchoolName, SignalScore } from '@/lib/schools/types'

export const ALL_DOMAINS: Domain[] = ['CAREER', 'HEALTH', 'RELATIONSHIP', 'SPIRITUAL', 'PSYCHOLOGICAL']
export const ALL_SCHOOLS: SchoolName[] = ['parashari', 'jaimini', 'tajika', 'kp', 'nadi', 'bnn', 'yogini']

/** Synthetic live signals (test-only, fictional ids; no chart data). */
export function liveSignals(score: number, n = 3): SignalScore[] {
  return Array.from({ length: n }, (_, i) => ({
    signalId: `SIG.TEST.${String(i + 1).padStart(3, '0')}`,
    signalName: `Test live signal ${i + 1}`,
    score,
    weight: 0.9 - i * 0.1,
  }))
}

export function liveSignalsForAll(score: number): Record<SchoolName, SignalScore[]> {
  return Object.fromEntries(ALL_SCHOOLS.map(s => [s, liveSignals(score)])) as Record<SchoolName, SignalScore[]>
}
