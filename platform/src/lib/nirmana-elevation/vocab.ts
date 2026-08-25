export const NIRMANA_STAGE_IDS = [
  'BOOTSTRAP', 'T0_CENSUS', 'PLAN_FROZEN', 'DENOMINATOR_FROZEN', 'F0_FOUNDATION',
  'L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'CLOSING', 'COMPLETE',
] as const

export const NIRMANA_LAYER_NAMES = {
  L0: 'Brahmagyan', L1: 'Ganita', L2: 'Bodha',
  L3: 'Kala', L4: 'Phala', L5: 'Mimamsa',
} as const

export const NIRMANA_MILESTONE_IDS = [
  'analysed', 'decision_accepted', 'built_or_dispositioned',
  'deployed_and_executed', 'verified', 'frozen',
] as const
