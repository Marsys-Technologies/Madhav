// EXPECT-VIOLATIONS: 3
export function frozen() {
  return {
    grounding_status: 'GROUNDED',
    passed: false,
    validator_verdict: 'PASS',
  }
}
