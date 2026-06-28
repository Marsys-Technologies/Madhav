/**
 * anthropic/adapter.ts — Anthropic CapabilityAdapter skeleton (A-S2).
 *
 * Implements CapabilityAdapter for the Anthropic stack.
 * chat() wraps the existing Anthropic-shaped pipeline.
 * All other capability methods throw CapabilityUnsupportedError with a
 * phase pointer indicating when they will ship.
 *
 * Phase roadmap for unsupported methods:
 *   thinking()         → R11.C (Streaming + Thinking)
 *   cache()            → R11.D (Caching)
 *   tools()            → R11.E (Adaptive Tool Sequencing)
 *   webSearch()        → R11.F (Server-Side Tools)
 *   webFetch()         → R11.F
 *   codeExecution()    → R11.F
 *   memory()           → R11.G (Memory + Projects)
 *   imageGeneration()  → R11.K (Image Generation — not supported by Anthropic API)
 *   computerUse()      → R11.K
 *   structuredOutputs() → R11.D (via tool_force)
 */

import type { CapabilityAdapter } from '../adapter';
import { CapabilityUnsupportedError } from '../adapter';
import type { ProviderCapabilities } from '../capabilities';
import type {
  ChatRequest,
  ChatEvent,
  ThinkingRequest,
  ThinkingResponse,
  CacheRequest,
  CacheResponse,
  ToolsRequest,
  ToolsResponse,
  WebSearchRequest,
  WebSearchResult,
  WebFetchRequest,
  WebFetchResult,
  CodeExecutionRequest,
  CodeExecutionResult,
  MemoryRequest,
  MemoryResponse,
  MultimodalRequest,
  MultimodalResponse,
  ImageGenRequest,
  ImageGenResult,
  ComputerUseRequest,
  ComputerUseEvent,
  StructuredOutputsRequest,
  StructuredOutputsResponse,
} from '../types';
import { streamText, jsonSchema } from 'ai';
// D7 migration: normalizeInputSchema moved to @/lib/retrieval/registry/schema_utils
// (pure utility, no retrieval dispatch dependency). DO NOT restore lib/retrieve import.
import { normalizeInputSchema } from '@/lib/retrieval/registry/schema_utils';
import { anthropic as anthropicProvider } from '@ai-sdk/anthropic';
import { ANTHROPIC_MANIFEST } from './manifest';

export class AnthropicAdapter implements CapabilityAdapter {
  readonly providerId = 'anthropic';

  getManifest(): ProviderCapabilities {
    return ANTHROPIC_MANIFEST;
  }

  /**
   * Primary streaming chat — real Anthropic implementation via Vercel AI SDK.
   *
   * Uses streamText() + @ai-sdk/anthropic and translates the fullStream
   * parts into the unified ChatEvent shape. Supports extended thinking when
   * request.thinkingConfig is set (providerOptions.anthropic.thinking).
   */
  async *chat(request: ChatRequest): AsyncIterable<ChatEvent> {
    // Separate system messages from the conversation messages
    const systemContent =
      request.system ??
      (request.messages.find((m) => m.role === 'system')?.content as string | undefined);

    const conversationMessages = request.messages
      .filter((m) => m.role !== 'system')
      .map((m) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content as string,
      }));

    // Build provider options — include thinking config if set
    const thinkingProviderOption =
      request.thinkingConfig?.providerPayload?.['thinking'] as Record<string, unknown> | undefined;
    const providerOptions = thinkingProviderOption
      ? { anthropic: { thinking: thinkingProviderOption } }
      : undefined;

    try {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const streamParams: any = {
        model: anthropicProvider(request.model),
        messages: conversationMessages as Parameters<typeof streamText>[0]['messages'],
        maxOutputTokens: request.maxTokens ?? 8192,
      };
      if (systemContent) streamParams.system = systemContent;
      if (request.temperature !== undefined) streamParams.temperature = request.temperature;
      if (providerOptions) streamParams.providerOptions = providerOptions;

      // Forward tool definitions to streamText so the model can call them.
      // AI SDK v6: CoreTool uses 'inputSchema' (not 'parameters'). Using 'parameters'
      // leaves tool2.inputSchema undefined; asSchema(undefined) produces
      // { properties: {}, additionalProperties: false } — no 'type' field — causing
      // Anthropic API 400: tools.0.custom.input_schema.type: Field required.
      // normalizeInputSchema guarantees type:'object' regardless of what the
      // caller supplies.
      if (request.tools && request.tools.length > 0) {
        const toolsMap: Record<string, { description?: string; inputSchema: ReturnType<typeof jsonSchema> }> = {};
        for (const tool of request.tools) {
          toolsMap[tool.name] = {
            description: tool.description,
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            inputSchema: jsonSchema(normalizeInputSchema(tool.inputSchema as any) as any),
          };
        }
        streamParams.tools = toolsMap;
      }

      // Forward toolChoice ('auto' | 'required' | 'none') when present
      if (request.toolsConfig?.toolChoice) {
        streamParams.toolChoice = request.toolsConfig.toolChoice;
      }

      const result = streamText(streamParams);

      for await (const part of result.fullStream) {
        if (part.type === 'text-delta') {
          yield { type: 'text_delta', text: part.text };
        } else if (part.type === 'reasoning-delta') {
          // Extended thinking — Vercel AI SDK surfaces as 'reasoning-delta' parts with .text
          yield { type: 'thinking_delta', thinking: (part as unknown as { text: string }).text };
        } else if ((part as unknown as { type: string }).type === 'tool-call-streaming-start') {
          // Tool call begins — emit start event with id + name
          const p = part as unknown as { toolCallId: string; toolName: string };
          yield { type: 'tool_use_start', id: p.toolCallId, name: p.toolName };
        } else if ((part as unknown as { type: string }).type === 'tool-call-delta') {
          // Incremental tool input JSON
          const p = part as unknown as { toolCallId: string; argsTextDelta: string };
          yield { type: 'tool_use_input_delta', id: p.toolCallId, partialJson: p.argsTextDelta };
        } else if (part.type === 'tool-call') {
          // Full tool call available — emit complete event with parsed args
          const p = part as unknown as { toolCallId: string; toolName: string; args: Record<string, unknown> };
          yield { type: 'tool_use_complete', id: p.toolCallId, name: p.toolName, input: p.args };
        } else if (part.type === 'finish') {
          const usage = part.totalUsage;
          yield {
            type: 'usage',
            inputTokens: usage.inputTokens ?? 0,
            outputTokens: usage.outputTokens ?? 0,
            cacheReadTokens:
              (usage as unknown as { inputTokenDetails?: { cacheReadTokens?: number } })
                .inputTokenDetails?.cacheReadTokens ?? 0,
            cacheCreationTokens:
              (usage as unknown as { inputTokenDetails?: { cacheWriteTokens?: number } })
                .inputTokenDetails?.cacheWriteTokens ?? 0,
          };
          // Map tool-calls finish reason to canonical 'tool_use' stop reason
          const stopReason = part.finishReason === 'tool-calls' ? 'tool_use' : (part.finishReason ?? 'end_turn');
          yield {
            type: 'message_stop',
            stopReason,
          };
        } else if (part.type === 'error') {
          const raw = (part as unknown as { error?: unknown }).error;
          const errMsg = raw instanceof Error ? raw.message : String(raw ?? 'unknown error');
          yield { type: 'error', error: errMsg };
        }
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      yield { type: 'error', error: message };
    }
  }

  thinking(request: ThinkingRequest): ThinkingResponse {
    // R11.C — Adaptive Thinking Budget (Anthropic)
    // Anthropic API shape: { type: 'enabled', effort: 'low'|'medium'|'high' }
    // for Opus 4.6+ / Sonnet 4.6+ (effort-based API).
    // For older models: { type: 'enabled', budget_tokens: N }
    // Effort → budget_tokens fallback mapping (used if effort API unsupported):
    //   low → 1024, medium → 8192, high → 32768
    const effort = request.effort ?? 'medium';
    const effortToBudget: Record<string, number> = {
      low: 1024,
      medium: 8192,
      high: 32768,
    };
    return {
      mode: 'native_effort',
      effort,
      budgetTokens: request.budgetTokens ?? effortToBudget[effort],
      providerPayload: {
        // effort-based API (Opus 4.6+, Sonnet 4.6+)
        thinking: { type: 'enabled', effort },
        // budget_tokens fallback (legacy models)
        thinking_budget_fallback: { type: 'enabled', budget_tokens: request.budgetTokens ?? effortToBudget[effort] },
      },
    };
  }

  cache(request: CacheRequest): CacheResponse {
    // R11.D — Anthropic 4-breakpoint cache_control (NATIVE_RULINGS §4).
    //
    // Canonical breakpoint positions (0-indexed, relative to assembled message array):
    //   BP0: end-of-tools     — after the tool definitions block
    //   BP1: end-of-system    — at the end of the system prompt
    //   BP2: end-of-RAG       — after the last retrieval/bundle message
    //   BP3: last-turn        — at the last assistant turn in history
    //
    // The prompt_assembler.ts (D-S1) injects `cache_control: { type: 'ephemeral' }`
    // at these positions when this config is returned.
    //
    // 5-minute TTL (ephemeral). Cache hits reduce input tokens by ~90%.
    // Cost model: cache write = 1.25x base; cache read = 0.1x base.
    const defaultBreakpoints = [
      0,  // BP0: end-of-tools
      1,  // BP1: end-of-system
      2,  // BP2: end-of-RAG-bundle
      3,  // BP3: last-assistant-turn
    ];
    return {
      mode: 'explicit_4bp',
      breakpointPositions: request.breakpointPositions ?? defaultBreakpoints,
      providerPayload: {
        // Anthropic API shape injected by prompt_assembler at each breakpoint position
        cacheControl: { type: 'ephemeral' },
        ttlMinutes: 5,
        maxBreakpoints: 4,
      },
    };
  }

  tools(request: ToolsRequest): ToolsResponse {
    // R11.E — Anthropic stop_reason agentic loop (E-S1).
    //
    // Loop terminates when stop_reason === 'tool_use'.
    // 8-iteration cap enforced by agentic_loop.ts checkIterationCap().
    // Default false (MARSYS_FLAG_R11E_ANTHROPIC_LOOP) — HIGH risk.
    // When flag=false, route.ts uses single-shot pipeline.
    const maxIterations = request.maxIterations ?? 8;
    return {
      mode: 'stop_reason',
      maxIterations,
      tools: request.tools,
      providerPayload: {
        // Anthropic stop_reason signal that triggers next iteration
        terminationSignal: 'stop_reason',
        terminationValue: 'tool_use',
        // Per-iteration usage accumulation for Observatory (E-S9)
        trackPerIterationUsage: true,
        // Interleaved text+tool ordering supported by Claude 4.x (E-S6)
        supportsInterleavedTextTool: true,
      },
    };
  }

  webSearch(_request: WebSearchRequest): Promise<WebSearchResult> {
    // R11.F — Server-Side Tools (Anthropic: first-party web_search)
    throw new CapabilityUnsupportedError('webSearch', 'anthropic');
  }

  webFetch(_request: WebFetchRequest): Promise<WebFetchResult> {
    // R11.F — Server-Side Tools (Anthropic: first-party web_fetch)
    throw new CapabilityUnsupportedError('webFetch', 'anthropic');
  }

  codeExecution(_request: CodeExecutionRequest): Promise<CodeExecutionResult> {
    // R11.F — Server-Side Tools (Anthropic: code_execution first-party)
    throw new CapabilityUnsupportedError('codeExecution', 'anthropic');
  }

  memory(_request: MemoryRequest): Promise<MemoryResponse> {
    // R11.G — Memory + Projects (Anthropic: Memory tool, Claude 4.5+)
    throw new CapabilityUnsupportedError('memory', 'anthropic');
  }

  multimodal(request: MultimodalRequest): MultimodalResponse {
    // Always-on: determines which modalities are supported vs. not.
    const supportedInput: MultimodalResponse['supportedInputModalities'] = [];
    const unsupportedInput: MultimodalResponse['unsupportedInputModalities'] = [];

    for (const modality of request.inputModalities) {
      if (modality === 'image' || modality === 'pdf') {
        supportedInput.push(modality);
      } else {
        unsupportedInput.push(modality);
      }
    }

    return {
      supportedInputModalities: supportedInput,
      unsupportedInputModalities: unsupportedInput,
      supportedOutputModalities: [], // Anthropic API: no voice/image generation output
    };
  }

  imageGeneration(_request: ImageGenRequest): Promise<ImageGenResult> {
    // Anthropic API does not support image generation — this will never ship.
    throw new CapabilityUnsupportedError('imageGeneration', 'anthropic');
  }

  async *computerUse(_request: ComputerUseRequest): AsyncIterable<ComputerUseEvent> {
    // R11.K — Computer Use (Anthropic: Computer Use API)
    throw new CapabilityUnsupportedError('computerUse', 'anthropic');
  }

  structuredOutputs(_request: StructuredOutputsRequest): StructuredOutputsResponse {
    // R11.D — Structured Outputs (Anthropic: tool_force)
    throw new CapabilityUnsupportedError('structuredOutputs', 'anthropic');
  }
}
