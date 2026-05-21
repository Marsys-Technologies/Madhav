/**
 * TypeScript types for the sade_sati_cycles table.
 * Mirrors migration 071_sade_sati_cycles.sql.
 */

export type SadeSatiPhase = 'rising' | 'peak' | 'setting'

export interface SadeSatiCycle {
  id: string
  native_id: string
  start_date: string
  end_date: string
  phase: SadeSatiPhase
  moon_sign: string
  saturn_sign: string
  severity_weight: number
  computation_source: string
  created_at: string
}

/** Input shape for the population script — one row per detected Saturn sign run */
export interface SadeSatiCycleInsert {
  native_id: string
  start_date: string
  end_date: string
  phase: SadeSatiPhase
  moon_sign: string
  saturn_sign: string
  severity_weight: number
  computation_source: string
}

/**
 * Sade Sati phase classification for Aquarius natal Moon.
 * Rising = Capricorn (severity 0.7), Peak = Aquarius (1.0), Setting = Pisces (0.7).
 */
export const SADE_SATI_PHASE_MAP: Record<string, { phase: SadeSatiPhase; severity_weight: number } | undefined> = {
  Capricorn: { phase: 'rising', severity_weight: 0.7 },
  Aquarius:  { phase: 'peak',   severity_weight: 1.0 },
  Pisces:    { phase: 'setting', severity_weight: 0.7 },
}
