// EXPECT-VIOLATIONS: 4
export const BOOLEAN_RESULTS = {
  passed: true,
  label: 'result',
}

export const SPREAD_RESULTS = {
  verified: 'PASS',
  ...upstream,
}

export const NESTED_RESULTS = {
  verdict: 'PASS',
  metadata: {},
}

export const COMPUTED_RESULTS = {
  passed: true,
  [name]: 'result',
}
