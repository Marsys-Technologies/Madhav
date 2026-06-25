export const VALID_AYANAMSHAS = [
  'lahiri',
  'true_chitra',
  'kp',
  'raman',
  'surya_siddhanta',
] as const

export type Ayanamsha = (typeof VALID_AYANAMSHAS)[number]
export const DEFAULT_AYANAMSHAS: Ayanamsha[] = [...VALID_AYANAMSHAS]
