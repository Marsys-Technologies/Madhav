// EXPECT-VIOLATIONS: 2
class FrozenMetrics {
  private lintLeaksTotal = 0

  recordRegisterLint(leakCount: number): void {
    this.deltaCalls += 1
    if (leakCount > 0) {
      this.fires += 1
      this.lintLeaksTotal += 0
    }
  }
}

function fabricatedBundle(chart_id: string, msg: string) {
  return {
    content: [{
      type: 'text',
      text: JSON.stringify({
        status: 'ERROR',
        error: msg,
        chart_id,
        grounding_status: 'SCAFFOLD',
        b11_floor_passed: true,
      }, null, 2),
    }],
    isError: true,
  }
}
