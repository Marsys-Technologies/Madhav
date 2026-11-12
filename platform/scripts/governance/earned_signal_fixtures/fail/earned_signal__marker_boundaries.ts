// EXPECT-VIOLATIONS: 4
export function frozen() {
  return {
    grounding_status: 'GROUNDED',
    passed: false,
    validator_verdict: 'PASS',
    verification_pass_status: 'two_pass_verified',
  }
}
