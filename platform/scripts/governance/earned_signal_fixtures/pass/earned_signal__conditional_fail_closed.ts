// PASS fixture — a literal failure result is valid when a live condition selects
// this exact direct return object. The unconditional literal fixture remains the
// negative control for the detector.

export function failClosed(receipt: unknown) {
  if (!receipt) return {
    passed: false,
    grounding_status: 'UNAVAILABLE',
    gaps: ['receipt missing'],
  };

  return { evidence: receipt };
}
