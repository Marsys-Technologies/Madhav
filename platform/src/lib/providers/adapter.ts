/**
 * adapter.ts — CapabilityAdapter interface: unified contract for all 5 provider adapters.
 *
 * Every provider adapter (Anthropic, Google, OpenAI, DeepSeek, NVIDIA) implements this
 * interface. The dispatcher (A-S7) routes incoming chat requests through these methods.
 * The migration adapter (A-S10) wraps the legacy pipeline as one adapter implementation.
 *
 * Architecture:
 * - getManifest()     — returns the provider's ProviderCapabilities manifest (A-S0 schema)
 * - chat()            — primary streaming method; returns AsyncIterable<ChatEvent>
 * - thinking()        — pre-configures extended thinking (synchronous; BEFORE chat)
 * - cache()           — pre-configures prompt caching (synchronous; BEFORE chat)
 * - tools()           — pre-configures tool loop topology (synchronous; BEFORE chat)
 * - webSearch()       — server-side web search (async)
 * - webFetch()        — server-side URL fetch (async)
 * - codeExecution()   — sandboxed code execution (async)
 * - memory()          — cross-conversation memory read/write (async)
 * - multimodal()      — modality routing configuration (synchronous)
 * - imageGeneration() — image generation (async)
 * - computerUse()     — computer use / agentic browsing (streaming async)
 * - structuredOutputs() — structured JSON output configuration (synchronous)
 *
 * Providers that don't support a capability MUST throw CapabilityUnsupportedError
 * in the method body. The interface itself is contract-complete; no optional methods.
 *
 * Source: A-S1 brief, CAPABILITY_MATRIX.md §9.
 */

import type { ProviderCapabilities } from './capabilities';
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
} from './types';

// Re-export the error type so consumers only need to import from 'adapter'.
export { CapabilityUnsupportedError } from './types';

/**
 * CapabilityAdapter — the unified interface all provider adapters implement.
 *
 * Usage pattern in the dispatcher:
 *
 *   const adapter = resolveAdapter(stack);  // returns CapabilityAdapter
 *   const thinkingCfg = adapter.thinking({ extendedThinkingMode: manifest.extendedThinking, effort: 'high' });
 *   const cacheCfg = adapter.cache({ cacheMode: manifest.promptCaching, breakpointPositions: [0] });
 *   const toolsCfg = adapter.tools({ toolLoopMode: manifest.adaptiveToolLoop, tools: [...] });
 *   const stream = adapter.chat({ messages, system, thinkingConfig: thinkingCfg, cacheConfig: cacheCfg, toolsConfig: toolsCfg });
 *   for await (const event of stream) { ... }
 */
export interface CapabilityAdapter {
  /**
   * Provider identifier — must match the stack-picker registry key
   * (e.g., 'anthropic', 'google', 'openai', 'deepseek', 'nvidia', 'legacy').
   */
  readonly providerId: string;

  /**
   * Returns the provider's capability manifest.
   * Called by the dispatcher to determine which capabilities are available
   * and which UI affordances to expose.
   */
  getManifest(): ProviderCapabilities;

  /**
   * Primary streaming chat method.
   * Returns an AsyncIterable<ChatEvent> that yields token deltas, thinking blocks,
   * tool use events, and final stop/usage events.
   *
   * Pre-conditions: call thinking(), cache(), and tools() first if those capabilities
   * are needed; pass the resulting configs in request.thinkingConfig / .cacheConfig / .toolsConfig.
   *
   * @throws CapabilityUnsupportedError — should not happen for chat (all providers support it)
   */
  chat(request: ChatRequest): AsyncIterable<ChatEvent>;

  /**
   * Configures extended thinking for the next chat call.
   * Returns a ResolvedThinkingConfig to inject into ChatRequest.thinkingConfig.
   *
   * Must be called synchronously before chat().
   * Providers without extended thinking support MUST throw CapabilityUnsupportedError.
   */
  thinking(request: ThinkingRequest): ThinkingResponse;

  /**
   * Configures prompt caching for the next chat call.
   * Returns a ResolvedCacheConfig to inject into ChatRequest.cacheConfig.
   *
   * Must be called synchronously before chat().
   * Providers without caching support MUST throw CapabilityUnsupportedError.
   */
  cache(request: CacheRequest): CacheResponse;

  /**
   * Configures tool loop topology for the next chat call.
   * Returns a ResolvedToolsConfig to inject into ChatRequest.toolsConfig.
   *
   * Must be called synchronously before chat().
   * Providers without tool loops MUST throw CapabilityUnsupportedError.
   */
  tools(request: ToolsRequest): ToolsResponse;

  /**
   * Executes server-side web search.
   * Returns structured search results with citations.
   *
   * @throws CapabilityUnsupportedError — providers without native web search
   */
  webSearch(request: WebSearchRequest): Promise<WebSearchResult>;

  /**
   * Fetches a URL server-side and returns extracted content.
   *
   * @throws CapabilityUnsupportedError — providers without web_fetch support
   */
  webFetch(request: WebFetchRequest): Promise<WebFetchResult>;

  /**
   * Executes code in a sandboxed environment server-side.
   * Returns stdout, stderr, return code, and any output files.
   *
   * @throws CapabilityUnsupportedError — providers without code execution support
   */
  codeExecution(request: CodeExecutionRequest): Promise<CodeExecutionResult>;

  /**
   * Reads or writes cross-conversation memory.
   *
   * @throws CapabilityUnsupportedError — providers without native memory support
   */
  memory(request: MemoryRequest): Promise<MemoryResponse>;

  /**
   * Configures multi-modal input/output routing.
   * Returns which modalities are supported vs. unsupported on this provider.
   * Unsupported modalities trigger a "switch stack" hint in the UI.
   *
   * Must be called synchronously before chat() when multi-modal content is present.
   */
  multimodal(request: MultimodalRequest): MultimodalResponse;

  /**
   * Generates images via the provider's image generation API.
   *
   * @throws CapabilityUnsupportedError — providers without image generation
   */
  imageGeneration(request: ImageGenRequest): Promise<ImageGenResult>;

  /**
   * Executes a computer use / agentic browsing task.
   * Returns an AsyncIterable<ComputerUseEvent> yielding screenshots, actions, and completion.
   *
   * @throws CapabilityUnsupportedError — providers without computer use support
   */
  computerUse(request: ComputerUseRequest): AsyncIterable<ComputerUseEvent>;

  /**
   * Configures structured JSON output enforcement.
   * Returns a StructuredOutputsResponse with provider-specific configuration.
   *
   * Must be called synchronously before chat() when structured output is required.
   * Providers without structured outputs support MUST throw CapabilityUnsupportedError.
   */
  structuredOutputs(request: StructuredOutputsRequest): StructuredOutputsResponse;
}
