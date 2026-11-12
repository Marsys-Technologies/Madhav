// EXPECT-VIOLATIONS: 2
// A constant object's name and primitive value types cannot prove its role.
export const CANNED_RESULT = {
  verification_pass_status: 'PASS',
  label: 'result',
} as const

export const CANNED_COUNTS: Record<string, number> = {
  leak_count: 0,
  ordinary_count: 1,
}
