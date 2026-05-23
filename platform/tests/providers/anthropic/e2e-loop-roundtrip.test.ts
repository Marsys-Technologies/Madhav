/**
 * R11F-A-S4: e2e-loop-roundtrip.test.ts
 *
 * End-to-end integration test for the Anthropic adapter → agentic loop round-trip.
 *
 * Covers:
 *   1. adapter.chat() emitting tool_use events → runAgenticLoop() → mock executor
 *      → second iteration → text output (full happy path).
 *   2. Loop halts at maxIterations if the model keeps calling tools (AgenticLoopCapExceeded).
 *   3. B.11 floor context marker is present in the first streamText call's messages.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { PipelinePlanSchema } from '../../../src/lib/pipeline/types';

// ------------------------------------------------------------------
// Mock 'ai' before importing the adapter (same pattern as F-S2 tests)
// ------------------------------------------------------------------
vi.mock('ai', () => ({
  streamText: vi.fn(),
  jsonSchema: vi.fn((schema: unknown) => schema),
}));

// Mock @ai-sdk/anthropic so adapter.ts can import without real credentials
vi.mock('@ai-sdk/anthropic', () => ({
  anthropic: vi.fn((modelId: string) => ({ modelId })),
}));

// Mock retrieve/index to avoid DB calls (matches pattern in agentic-loop-engine.test.ts)
vi.mock('../../../src/lib/retrieve/index', () => ({
  getTool: vi.fn(),
  RETRIEVAL_TOOLS: [],
}));

import { streamText } from 'ai';
import { AnthropicAdapter } from '../../../src/lib/providers/anthropic/adapter';
import {
  runAgenticLoop,
  AgenticLoopCapExceeded,
  ANTHROPIC_LOOP_CONFIG,
} from '../../../src/lib/synthesis/agentic_loop';
import type { ChatRequest, ChatEvent } from '../../../src/lib/providers/types';
import { anthropicToolUseFixture } from './fixtures/tool_use_stream';

// ------------------------------------------------------------------
// Helpers
// ------------------------------------------------------------------

/** Build an async iterable from a flat array of stream parts. */
async function* makeStream(parts: unknown[]) {
  for (const p of parts) {
    yield p;
  }
}

/** Collect all ChatEvents from an AsyncIterable into an array. */
async function collectEvents(iterable: AsyncIterable<ChatEvent>): Promise<ChatEvent[]> {
  const result: ChatEvent[] = [];
  for await (const event of iterable) {
    result.push(event);
  }
  return result;
}

/** Minimal ChatRequest. */
function makeRequest(overrides?: Partial<ChatRequest>): ChatRequest {
  return {
    messages: [{ role: 'user', content: 'What is Saturn doing?' }],
    model: 'claude-sonnet-4-6',
    tools: [
      {
        name: 'query_ephemeris',
        description: 'Query ephemeris data for a given date',
        inputSchema: {
          type: 'object',
          properties: { date: { type: 'string' } },
          required: ['date'],
        },
      },
    ],
    ...overrides,
  };
}

// ------------------------------------------------------------------
// Test 1: Full happy-path round-trip
// ------------------------------------------------------------------

describe('R11F E2E: Anthropic adapter → agentic loop round-trip (happy path)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('executes tool_use block, injects result, and produces text on second iteration', async () => {
    // streamText call 1: returns tool-call stream
    // streamText call 2: returns text stream
    let callCount = 0;
    vi.mocked(streamText).mockImplementation(() => {
      callCount++;
      const parts =
        callCount === 1
          ? anthropicToolUseFixture.iteration1
          : anthropicToolUseFixture.iteration2;
      return {
        fullStream: makeStream(parts),
      } as unknown as ReturnType<typeof streamText>;
    });

    const adapter = new AnthropicAdapter();

    // Mock executor: returns ephemeris JSON when called
    const mockExecutor = vi.fn().mockResolvedValue(
      JSON.stringify({ planet: 'Saturn', sign: 'Scorpio', degrees: '5° 18\'' }),
    );

    const events = await collectEvents(
      runAgenticLoop(adapter, makeRequest(), mockExecutor, ANTHROPIC_LOOP_CONFIG),
    );

    // Executor called exactly once for query_ephemeris with correct input
    expect(mockExecutor).toHaveBeenCalledTimes(1);
    expect(mockExecutor).toHaveBeenCalledWith(
      expect.objectContaining({
        name: 'query_ephemeris',
        input: { date: '1984-02-05' },
      }),
    );

    // Text events from iteration 2 must be present in output
    const textEvents = events.filter((e) => e.type === 'text_delta');
    expect(textEvents.length).toBeGreaterThan(0);

    // streamText must have been called exactly twice (iter 1 + iter 2)
    expect(streamText).toHaveBeenCalledTimes(2);

    // Both calls must include the tools array (forwarded from request)
    const firstCall = vi.mocked(streamText).mock.calls[0][0];
    const secondCall = vi.mocked(streamText).mock.calls[1][0];
    expect(firstCall).toHaveProperty('tools');
    expect(secondCall).toHaveProperty('tools');

    // AI SDK v6 requires 'inputSchema' field on CoreTool — NOT 'parameters'.
    // If the adapter still uses 'parameters', tool2.inputSchema is undefined and
    // asSchema(undefined) produces { properties: {} } (no type), causing Anthropic 400.
    const tools = firstCall.tools as Record<string, { inputSchema?: unknown; parameters?: unknown }>;
    for (const toolDef of Object.values(tools)) {
      expect(toolDef).toHaveProperty('inputSchema');
      expect(toolDef).not.toHaveProperty('parameters');
      // With jsonSchema() mocked as identity, inputSchema is the raw normalized schema
      const schema = toolDef.inputSchema as { type?: string };
      expect(schema.type).toBe('object');
    }
  });
});

// ------------------------------------------------------------------
// Test 1b: Tool schemas without 'type' are normalised to type:object
//
// Tightened fixture: request includes tools with bare {} and properties-only
// schemas. The adapter must normalise these before forwarding to streamText
// so Anthropic never sees input_schema without type:object.
// ------------------------------------------------------------------

describe('R11F A-S6 regression: bare tool inputSchemas are normalised to type:object', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('normalises {} and properties-only schemas before passing to streamText', async () => {
    vi.mocked(streamText).mockImplementation(() => ({
      fullStream: makeStream([...anthropicToolUseFixture.iteration2]),
    } as unknown as ReturnType<typeof streamText>));

    const adapter = new AnthropicAdapter();
    const mockExecutor = vi.fn().mockResolvedValue('{}');

    // Request with deliberately under-specified schemas
    const requestWithBareSchemas = makeRequest({
      tools: [
        {
          name: 'query_bare',
          description: 'Parameterless tool — no schema at all',
          inputSchema: {},  // should become { type: 'object', properties: {} }
        },
        {
          name: 'query_props_only',
          description: 'Properties present but no root type',
          inputSchema: {
            properties: { date: { type: 'string' } },  // should become { type: 'object', properties: {...} }
          },
        },
      ],
    });

    await collectEvents(
      runAgenticLoop(adapter, requestWithBareSchemas, mockExecutor, ANTHROPIC_LOOP_CONFIG),
    );

    const firstCall = vi.mocked(streamText).mock.calls[0][0];
    const tools = firstCall.tools as Record<string, { inputSchema?: unknown; parameters?: unknown }>;

    // Both tools must arrive at streamText with type:object
    for (const toolDef of Object.values(tools)) {
      expect(toolDef).toHaveProperty('inputSchema');
      expect(toolDef).not.toHaveProperty('parameters');
      const schema = toolDef.inputSchema as { type?: string };
      expect(schema.type).toBe('object');
    }

    // Specifically: bare {} becomes { type: 'object', properties: {} }
    const bareTool = tools['query_bare'] as { inputSchema: { type: string; properties: unknown } };
    expect(bareTool.inputSchema.type).toBe('object');
    expect(bareTool.inputSchema.properties).toEqual({});

    // Specifically: properties-only becomes { type: 'object', properties: { date: ... } }
    const propsTool = tools['query_props_only'] as { inputSchema: { type: string; properties: unknown } };
    expect(propsTool.inputSchema.type).toBe('object');
    expect(propsTool.inputSchema.properties).toEqual({ date: { type: 'string' } });
  });
});

// ------------------------------------------------------------------
// Test 2: Cap exceeded — model keeps requesting tools
// ------------------------------------------------------------------

describe('R11F E2E: Anthropic adapter → agentic loop cap enforcement', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('throws AgenticLoopCapExceeded when model always returns tool-calls (maxIterations: 3)', async () => {
    // streamText always returns iteration1 — tool calls forever
    vi.mocked(streamText).mockImplementation(() => ({
      fullStream: makeStream([...anthropicToolUseFixture.iteration1]),
    } as unknown as ReturnType<typeof streamText>));

    const adapter = new AnthropicAdapter();
    const mockExecutor = vi.fn().mockResolvedValue('{"result":"ephemeris data"}');

    const customConfig = { ...ANTHROPIC_LOOP_CONFIG, maxIterations: 3 };

    await expect(async () => {
      await collectEvents(
        runAgenticLoop(adapter, makeRequest(), mockExecutor, customConfig),
      );
    }).rejects.toThrow(AgenticLoopCapExceeded);

    // Executor called exactly maxIterations times (3 tool-call iterations before cap)
    expect(mockExecutor).toHaveBeenCalledTimes(3);
  });
});

// ------------------------------------------------------------------
// Test 3: B.11 floor context marker in first iteration
// ------------------------------------------------------------------

describe('R11F E2E: Anthropic adapter → B.11 floor context threading', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('passes B.11 floor context through to first iteration system message', async () => {
    // Capture streamText arguments to inspect message content
    const capturedCalls: Array<Parameters<typeof streamText>[0]> = [];
    vi.mocked(streamText).mockImplementation((params) => {
      capturedCalls.push(params as Parameters<typeof streamText>[0]);
      return {
        fullStream: makeStream([...anthropicToolUseFixture.iteration2]),
      } as unknown as ReturnType<typeof streamText>;
    });

    const B11_FLOOR_MARKER = '[B.11-FLOOR-CONTEXT: MSR+UCN+CDLM+CGM+RM synthesised]';

    const adapter = new AnthropicAdapter();
    const mockExecutor = vi.fn().mockResolvedValue('{}');

    // Include the B.11 marker in the system field of the request
    const requestWithFloor = makeRequest({
      system: `You are a Jyotish instrument. ${B11_FLOOR_MARKER}`,
    });

    await collectEvents(
      runAgenticLoop(adapter, requestWithFloor, mockExecutor, ANTHROPIC_LOOP_CONFIG),
    );

    // First streamText call must have been made
    expect(capturedCalls.length).toBeGreaterThan(0);

    // The first call's system parameter must include the B.11 marker
    const firstCallParams = capturedCalls[0] as Record<string, unknown>;
    const systemContent = firstCallParams['system'] as string | undefined;
    expect(systemContent).toBeDefined();
    expect(systemContent).toContain(B11_FLOOR_MARKER);
  });
});

// ------------------------------------------------------------------
// Test 4: Planner null synthesis_guidance — the A-S5 production bug
//
// This test would NOT have caught the original bug because the A-S4
// fixtures only mocked the adapter/loop layer, not the planner schema.
// It now covers the exact production wire format that Anthropic returns:
// a valid PipelinePlan except synthesis_guidance is null rather than
// a string or absent. The schema fix (z.preprocess null→undefined) must
// accept this without throwing.
// ------------------------------------------------------------------

describe('R11F A-S5 regression: planner synthesis_guidance: null does not cause 422', () => {
  it('PipelinePlanSchema accepts synthesis_guidance: null and coerces to undefined', () => {
    // This is the exact shape that caused the A-S5 422 in production.
    // Anthropic returned synthesis_guidance: null; the old z.string().optional()
    // rejected it; PipelinePlannerError was thrown; route.ts returned 422.
    const productionWireFormat = {
      query_class: 'predictive',
      query_intent_summary: 'When does the native\'s next Saturn mahadasha start?',
      asset_bundle: [
        { asset_id: 'FORENSIC', priority: 1, reason: 'Floor: birth chart facts.' },
        { asset_id: 'LEL', priority: 2, reason: 'Life event log for dasha correlation.' },
      ],
      tool_calls: [
        {
          tool_name: 'query_dasha_periods',
          params: { dasha_lord: 'Saturn', limit: 5 },
          token_budget: 800,
          priority: 1,
          reason: 'Saturn dasha sequence from current position.',
        },
      ],
      synthesis_guidance: null,      // ← The bug: Anthropic returned null here
      planning_rationale: null,      // ← Both soft-optional fields null (worst case)
      forward_looking: true,
      dasha_context_required: true,
    };

    const result = PipelinePlanSchema.safeParse(productionWireFormat);

    // Must succeed — the schema fix coerces null → undefined for soft-optional fields
    expect(result.success).toBe(true);

    if (result.success) {
      // synthesis_guidance null → undefined: treated as absent, synthesis uses default prompt
      expect(result.data.synthesis_guidance).toBeUndefined();
      expect(result.data.planning_rationale).toBeUndefined();
      // Hard-required fields must be preserved exactly
      expect(result.data.query_class).toBe('predictive');
      expect(result.data.tool_calls).toHaveLength(1);
      expect(result.data.tool_calls[0].tool_name).toBe('query_dasha_periods');
    }
  });
});
