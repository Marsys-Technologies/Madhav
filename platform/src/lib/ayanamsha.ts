export const VALID_AYANAMSHAS = [
  'lahiri',
  'true_chitra',
  'kp',
  'raman',
  'surya_siddhanta',
] as const

export type Ayanamsha = (typeof VALID_AYANAMSHAS)[number]
export const DEFAULT_AYANAMSHAS: Ayanamsha[] = [...VALID_AYANAMSHAS]

/**
 * Stored/legacy spellings of the five supported frames, folded to the short
 * ids the chart forms and the PATCH schema use. Spellings mirror the MCP
 * resolver (`platform-mcp/src/lib/ayanamsha.ts`), which keeps `true_chitra`
 * distinct from Lahiri. Deliberately not named `*ayanamsha*` map: it is a
 * spelling fold for chart-edit comparison, never a computation alias.
 */
const SPELLING_TO_SHORT_ID: Readonly<Record<string, Ayanamsha>> = {
  lahiri: 'lahiri',
  lahiri_chitra: 'lahiri',
  lahiri_chitrapaksha: 'lahiri',
  true_chitra: 'true_chitra',
  true_citra: 'true_chitra',
  chitra: 'true_chitra',
  kp: 'kp',
  krishnamurti: 'kp',
  raman: 'raman',
  surya_siddhanta: 'surya_siddhanta',
  surya_siddhanta_classical: 'surya_siddhanta',
}

/**
 * One id in its short form when it is a known spelling of a supported frame;
 * any other id is returned trimmed and unchanged (never silently dropped).
 */
export function toShortAyanamshaId(raw: string): string {
  const trimmed = raw.trim()
  return SPELLING_TO_SHORT_ID[trimmed.toLowerCase()] ?? trimmed
}

/** True for one of the five ids the edit schema and the forms accept. */
export function isSupportedAyanamsha(id: string): id is Ayanamsha {
  return (VALID_AYANAMSHAS as readonly string[]).includes(id)
}
