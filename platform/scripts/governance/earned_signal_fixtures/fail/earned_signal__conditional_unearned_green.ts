// FAIL fixture — control flow alone is not enough. The direct conditional
// return must be a fail-closed `passed: false` outcome, never a hidden green.
// EXPECT-VIOLATIONS: 1
export function incorrectlyPasses(receipt: unknown) {
  if (!receipt) return {
    passed: true,
    gaps: ['receipt missing'],
  };

  return { evidence: receipt };
}
