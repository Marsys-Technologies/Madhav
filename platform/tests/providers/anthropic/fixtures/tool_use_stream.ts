/**
 * Mock stream parts simulating Anthropic streamText responses.
 * Iteration 1: emits a tool_call for 'query_ephemeris'
 * Iteration 2: emits text
 */
export const anthropicToolUseFixture = {
  iteration1: [
    { type: 'tool-call-streaming-start', toolCallId: 'tc_001', toolName: 'query_ephemeris' },
    { type: 'tool-call-delta', toolCallId: 'tc_001', argsTextDelta: '{"date":' },
    { type: 'tool-call-delta', toolCallId: 'tc_001', argsTextDelta: '"1984-02-05"}' },
    { type: 'tool-call', toolCallId: 'tc_001', toolName: 'query_ephemeris', args: { date: '1984-02-05' } },
    { type: 'finish', finishReason: 'tool-calls', totalUsage: { inputTokens: 100, outputTokens: 30 } },
  ],
  iteration2: [
    { type: 'text-delta', text: "Saturn is in Scorpio at 5° 18'" },
    { type: 'finish', finishReason: 'stop', totalUsage: { inputTokens: 200, outputTokens: 40 } },
  ],
}
