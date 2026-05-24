/**
 * types.ts — Typed request/response shapes for the CapabilityAdapter interface.
 *
 * Each capability method on CapabilityAdapter accepts one of the request types
 * defined here and returns one of the response types. Provider implementations
 * that don't support a capability should throw CapabilityUnsupportedError.
 *
 * Source of truth: CAPABILITY_MATRIX.md §9 + A-S1 brief.
 */

import type { ProviderCapabilities } from './capabilities';

// ---------------------------------------------------------------------------
// Error types
// ---------------------------------------------------------------------------

/**
 * Thrown by adapter methods for capabilities the provider does not support.
 * Catch this in the dispatcher to surface a "switch stack" hint to the UI.
 */
export class CapabilityUnsupportedError extends Error {
  public readonly capability: string;
  public readonly providerId: string;

  constructor(capability: string, providerId: string) {
    super(
      `[capability-adapter] Provider "${providerId}" does not support capability "${capability}". ` +
        `Check ProviderCapabilities manifest or switch to a provider that supports this capability.`,
    );
    this.name = 'CapabilityUnsupportedError';
    this.capability = capability;
    this.providerId = providerId;
  }
}

// ---------------------------------------------------------------------------
// Chat (primary streaming call)
// ---------------------------------------------------------------------------

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string | ChatContentBlock[];
}

export type ChatContentBlock =
  | { type: 'text'; text: string }
  | { type: 'image'; source: ImageSource }
  | { type: 'tool_result'; toolUseId: string; name?: string; content: string }
  | { type: 'tool_use'; id: string; name: string; input: Record<string, unknown> };

export interface ImageSource {
  type: 'base64' | 'url';
  mediaType?: string;
  data?: string;
  url?: string;
}

export interface ChatTool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
}

export interface ChatRequest {
  messages: ChatMessage[];
  system?: string;
  tools?: ChatTool[];
  model: string;
  maxTokens?: number;
  temperature?: number;
  /** Thinking configuration, if pre-configured by the thinking() method. */
  thinkingConfig?: ResolvedThinkingConfig;
  /** Cache markers, if pre-configured by the cache() method. */
  cacheConfig?: ResolvedCacheConfig;
  /** Tool loop topology, if pre-configured by the tools() method. */
  toolsConfig?: ResolvedToolsConfig;
}

export type ChatEvent =
  | { type: 'text_delta'; text: string }
  | { type: 'thinking_delta'; thinking: string }
  | { type: 'tool_use_start'; id: string; name: string }
  | { type: 'tool_use_input_delta'; id: string; partialJson: string }
  | { type: 'tool_use_complete'; id: string; name: string; input: Record<string, unknown> }
  | { type: 'message_stop'; stopReason: string }
  | { type: 'usage'; inputTokens: number; outputTokens: number; cacheReadTokens?: number; cacheCreationTokens?: number }
  | { type: 'error'; error: string };

// ---------------------------------------------------------------------------
// Thinking (configures extended thinking — called BEFORE chat)
// ---------------------------------------------------------------------------

export interface ThinkingRequest {
  /** Provider's manifest declaration for extended thinking. */
  extendedThinkingMode: ProviderCapabilities['extendedThinking'];
  /**
   * Desired effort level: 'low' | 'medium' | 'high'.
   * The adapter translates this into provider-specific budget values.
   */
  effort?: 'low' | 'medium' | 'high';
  /**
   * Explicit token budget (overrides effort mapping).
   * Only meaningful for 'native_budget' (Gemini) and 'inline_blocks' (DeepSeek).
   */
  budgetTokens?: number;
}

/** Pre-resolved thinking configuration, injected into ChatRequest. */
export interface ResolvedThinkingConfig {
  mode: ProviderCapabilities['extendedThinking'];
  effort?: 'low' | 'medium' | 'high';
  budgetTokens?: number;
  /** Provider-specific payload (e.g., `{ type: 'enabled', budget_tokens: N }` for Claude). */
  providerPayload?: Record<string, unknown>;
}

export type ThinkingResponse = ResolvedThinkingConfig;

// ---------------------------------------------------------------------------
// Cache (configures prompt caching — called BEFORE chat)
// ---------------------------------------------------------------------------

export interface CacheRequest {
  cacheMode: ProviderCapabilities['promptCaching'];
  /** Positions in the prompt that should receive cache breakpoints (0-indexed message index). */
  breakpointPositions?: number[];
}

/** Pre-resolved cache configuration, injected into ChatRequest. */
export interface ResolvedCacheConfig {
  mode: ProviderCapabilities['promptCaching'];
  breakpointPositions?: number[];
  /** Provider-specific payload. */
  providerPayload?: Record<string, unknown>;
}

export type CacheResponse = ResolvedCacheConfig;

// ---------------------------------------------------------------------------
// Tools (configures tool loop topology — called BEFORE chat)
// ---------------------------------------------------------------------------

export interface ToolsRequest {
  toolLoopMode: ProviderCapabilities['adaptiveToolLoop'];
  maxIterations?: number;
  tools: ChatTool[];
}

/** Pre-resolved tool loop configuration, injected into ChatRequest. */
export interface ResolvedToolsConfig {
  mode: ProviderCapabilities['adaptiveToolLoop'];
  maxIterations: number;
  tools: ChatTool[];
  /** Tool choice behaviour forwarded to the AI SDK ('auto' | 'required' | 'none'). */
  toolChoice?: 'auto' | 'required' | 'none';
  /** Provider-specific payload (e.g., Responses API for OpenAI). */
  providerPayload?: Record<string, unknown>;
}

export type ToolsResponse = ResolvedToolsConfig;

// ---------------------------------------------------------------------------
// Web Search (server-side tool — async)
// ---------------------------------------------------------------------------

export interface WebSearchRequest {
  query: string;
  /** Conversation messages to provide context for multi-hop search. */
  contextMessages?: ChatMessage[];
}

export interface WebSearchResult {
  results: Array<{
    title: string;
    url: string;
    snippet: string;
    citedText?: string;
  }>;
  /** Provider-specific raw response for debugging. */
  rawResponse?: unknown;
}

// ---------------------------------------------------------------------------
// Web Fetch (server-side tool — async)
// ---------------------------------------------------------------------------

export interface WebFetchRequest {
  url: string;
  /** Optional selector hint (e.g., CSS selector for the content area). */
  selector?: string;
}

export interface WebFetchResult {
  url: string;
  title?: string;
  content: string;
  contentType?: string;
}

// ---------------------------------------------------------------------------
// Code Execution (server-side tool — async)
// ---------------------------------------------------------------------------

export interface CodeExecutionRequest {
  code: string;
  language?: 'python' | 'javascript';
  /** Files to provide as input. */
  inputFiles?: Array<{ name: string; content: string | Uint8Array }>;
}

export interface CodeExecutionResult {
  stdout: string;
  stderr?: string;
  returnCode: number;
  outputFiles?: Array<{ name: string; content: string | Uint8Array; mimeType?: string }>;
}

// ---------------------------------------------------------------------------
// Memory (cross-conversation — async)
// ---------------------------------------------------------------------------

export type MemoryOperation = 'read' | 'write' | 'delete' | 'list';

export interface MemoryRequest {
  operation: MemoryOperation;
  /** Key for write/delete operations. */
  key?: string;
  /** Value for write operations. */
  value?: string;
  /** Query for fuzzy-match read operations. */
  query?: string;
}

export interface MemoryResponse {
  operation: MemoryOperation;
  /** Retrieved memories for read/list operations. */
  memories?: Array<{ key: string; value: string; timestamp?: number }>;
  /** Confirmation for write/delete operations. */
  success?: boolean;
}

// ---------------------------------------------------------------------------
// Multi-modal (modality routing — synchronous configuration)
// ---------------------------------------------------------------------------

export interface MultimodalRequest {
  /** Requested input modalities. */
  inputModalities: Array<'image' | 'audio' | 'video' | 'pdf'>;
  /** Requested output modalities. */
  outputModalities?: Array<'voice' | 'image'>;
}

export interface MultimodalResponse {
  /** Supported input modalities on this provider. */
  supportedInputModalities: Array<'image' | 'audio' | 'video' | 'pdf'>;
  /** Unsupported input modalities (should trigger "switch stack" hint). */
  unsupportedInputModalities: Array<'image' | 'audio' | 'video' | 'pdf'>;
  /** Supported output modalities. */
  supportedOutputModalities: Array<'voice' | 'image'>;
  /** Provider-specific configuration payload. */
  providerPayload?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Image Generation (async)
// ---------------------------------------------------------------------------

export interface ImageGenRequest {
  prompt: string;
  size?: '256x256' | '512x512' | '1024x1024' | '1792x1024' | '1024x1792';
  quality?: 'standard' | 'hd';
  style?: 'vivid' | 'natural';
  n?: number;
}

export interface ImageGenResult {
  images: Array<{
    url?: string;
    base64?: string;
    revisedPrompt?: string;
  }>;
  model?: string;
}

// ---------------------------------------------------------------------------
// Computer Use (async streaming)
// ---------------------------------------------------------------------------

export interface ComputerUseRequest {
  task: string;
  /** Initial screenshot (base64 PNG) if available. */
  initialScreenshot?: string;
  maxActions?: number;
}

export type ComputerUseEvent =
  | { type: 'screenshot'; imageBase64: string }
  | { type: 'action'; action: string; coordinates?: { x: number; y: number } }
  | { type: 'text'; text: string }
  | { type: 'complete'; success: boolean; summary: string }
  | { type: 'error'; error: string };

// ---------------------------------------------------------------------------
// Structured Outputs (synchronous configuration)
// ---------------------------------------------------------------------------

export interface StructuredOutputsRequest {
  /** JSON Schema defining the expected output shape. */
  schema: Record<string, unknown>;
  /** Whether to enforce strict schema compliance. */
  strict?: boolean;
}

export interface StructuredOutputsResponse {
  mode: ProviderCapabilities['structuredOutputs'];
  /** Provider-specific configuration payload. */
  providerPayload?: Record<string, unknown>;
}
