/**
 * PROBE_anthropic_tools_forwarding.test.ts — diagnostic probe artifact.
 *
 * Probe authored 2026-05-23 by an investigation agent to verify that
 * AnthropicAdapter.chat() does NOT forward `request.tools` or
 * `request.toolsConfig.tools` to the underlying streamText() call.
 *
 * Result on 2026-05-23 (main HEAD): streamText invoked with keys
 *   "model,messages,maxOutputTokens" — args.tools === undefined for both
 *   request.tools and request.toolsConfig.tools.
 *
 * This file is parked as a skipped describe block. Re-enable / replace
 * after AnthropicAdapter.chat() is amended to translate request.tools and
 * toolsConfig into provider arguments.
 */
import { describe, it } from 'vitest';

describe.skip('PROBE — AnthropicAdapter.chat tools forwarding (re-enable post-fix)', () => {
  it('placeholder — see file header', () => {});
});
