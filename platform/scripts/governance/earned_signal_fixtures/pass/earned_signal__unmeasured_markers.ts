export function unavailable() {
  return {
    grounding_status: 'UNGROUNDED',
    validator_verdict: 'UNKNOWN',
    verification_pass_status: 'floored',
  }
}
