/**
 * ProviderCapabilities — TypeScript interface codified from CAPABILITY_MATRIX.md §9
 *
 * Each provider adapter declares a manifest implementing this interface at module load.
 * The dispatcher (A-S7) consults this manifest to decide:
 *   - Which UI affordances to expose
 *   - Which polyfills to engage
 *   - Which "switch stack" hints to surface
 *
 * Maintained by: R11 v2 Multi-Provider Parity arc (Chat V2 R11 v2 — Claude Takeover)
 * Source of truth: 00_ARCHITECTURE/CAPABILITY_MATRIX.md §9
 */

export interface ProviderCapabilities {
  // ---------------------------------------------------------------------------
  // Cluster A — Foundation: Thinking + Streaming + Caching + Tool Loops
  // ---------------------------------------------------------------------------

  /**
   * Extended thinking support level.
   * - 'native_effort'  — Claude 4.x: effort-based thinking (Anthropic)
   * - 'native_budget'  — Gemini 2.5: integer thinkingBudget parameter
   * - 'inline_blocks'  — DeepSeek: inline <think>...</think> blocks extracted via middleware
   * - 'polyfill_cot'   — GPT/OpenAI: "think step by step" system-prompt nudge (no native support)
   * - null             — provider does not support extended thinking
   */
  extendedThinking: 'native_effort' | 'native_budget' | 'inline_blocks' | 'polyfill_cot' | null;

  /**
   * Prompt caching strategy.
   * - 'explicit_4bp'         — Anthropic: explicit cache_control breakpoints (up to 4)
   * - 'cached_content_api'   — Google: separate cachedContent API call (TTL configurable)
   * - 'automatic'            — OpenAI: automatic (default on, 25% hit cost)
   * - 'implicit'             — DeepSeek: implicit, prompt_cache_hit_tokens in usage
   * - null                   — not supported / depends on hosted model
   */
  promptCaching: 'explicit_4bp' | 'cached_content_api' | 'automatic' | 'implicit' | null;

  /**
   * Adaptive multi-step tool loop stop signal.
   * - 'stop_reason'                    — Anthropic: stop_reason === 'tool_use'
   * - 'finish_reason_function_calls'   — Google: finish_reason === 'function_calls'
   * - 'finish_reason_tool_calls'       — OpenAI/DeepSeek: finish_reason === 'tool_calls'
   * - null                             — no structured tool loop signal (depends on model)
   */
  adaptiveToolLoop:
    | 'stop_reason'
    | 'finish_reason_function_calls'
    | 'finish_reason_tool_calls'
    | null;

  /**
   * Whether the provider supports interleaved thinking + tool use in the same turn.
   * True for Claude 4.x and Gemini 2.5; false for others.
   */
  interleavedThinkingTool: boolean;

  /**
   * Whether smooth streaming is supported.
   * Always true via Marsys server adapter (applied at the stream-flush layer,
   * not provider-native). Kept as an explicit field for future per-provider overrides.
   */
  smoothStreaming: boolean;

  // ---------------------------------------------------------------------------
  // Cluster B — Server-side tools
  // ---------------------------------------------------------------------------

  /**
   * Built-in web search support.
   * - 'first_party'  — Anthropic: web_search tool (web_search_tool_result content block)
   * - 'grounding'    — Google: Google Search grounding via tools: [{ google_search: {} }]
   * - 'preview_api'  — OpenAI: web_search_preview tool (Responses API)
   * - null           — not supported (DeepSeek, NVIDIA NIM)
   */
  webSearch: 'first_party' | 'grounding' | 'preview_api' | null;

  /**
   * Built-in URL fetch tool.
   * - 'first_party'  — Anthropic: web_fetch tool (native)
   * - null           — must be polyfilled via function calling + Marsys fetcher
   */
  webFetch: 'first_party' | null;

  /**
   * Sandboxed code execution built-in tool.
   * - 'first_party'  — Anthropic (code_execution), Google (Code Execution), OpenAI (Code Interpreter)
   * - null           — not supported or depends on hosted model
   */
  codeExecution: 'first_party' | null;

  // ---------------------------------------------------------------------------
  // Cluster C — Memory + Projects + Learning Layer
  // ---------------------------------------------------------------------------

  /**
   * Native (provider-managed) cross-conversation memory.
   * - 'memory_tool'    — Anthropic: Memory tool (Claude 4.5+), API-accessible
   * - 'workspace'      — Google: Workspace context binding
   * - 'product_only'   — OpenAI: Memory feature (ChatGPT product-only; not API-native)
   * - null             — provider does not support native memory
   */
  nativeMemory: 'memory_tool' | 'workspace' | 'product_only' | null;

  // ---------------------------------------------------------------------------
  // Cluster D — Multi-modal input
  // ---------------------------------------------------------------------------

  /** Image input supported (vision). */
  inputImage: boolean;

  /** Audio input supported. */
  inputAudio: boolean;

  /** Video input supported. */
  inputVideo: boolean;

  /**
   * PDF input mode.
   * - 'files_api'  — PDF uploaded via Files API (Anthropic, Google, OpenAI)
   * - 'inline'     — PDF inlined in message content (Anthropic also supports this)
   * - null         — not supported
   */
  inputPdf: 'files_api' | 'inline' | 'files_api_inline' | null;

  // ---------------------------------------------------------------------------
  // Cluster D — Multi-modal output
  // ---------------------------------------------------------------------------

  /**
   * Voice / TTS output mode.
   * - 'live_api'       — Google: Gemini Live real-time TTS
   * - 'tts_streaming'  — OpenAI: Audio Preview / TTS streaming
   * - null             — not supported
   */
  outputVoice: 'live_api' | 'tts_streaming' | null;

  /**
   * Image generation output.
   * - 'imagen'     — Google: Imagen via API
   * - 'dalle'      — OpenAI: DALL-E
   * - 'gpt_image'  — OpenAI: gpt-image-1
   * - null         — not supported
   */
  outputImage: 'imagen' | 'dalle' | 'gpt_image' | null;

  /**
   * Computer use / agentic browsing.
   * - 'computer_use_api'  — Anthropic: Computer Use API (screenshot + click + type)
   * - 'cua_responses'     — OpenAI: Computer Use Agent via Responses API
   * - null                — not supported
   */
  computerUse: 'computer_use_api' | 'cua_responses' | null;

  // ---------------------------------------------------------------------------
  // Cross-cutting capabilities
  // ---------------------------------------------------------------------------

  /**
   * Structured JSON output enforcement.
   * - 'json_schema_strict'  — OpenAI: response_format: { type: 'json_schema', strict: true }
   * - 'response_schema'     — Google: responseSchema in generation config
   * - 'tool_force'          — Anthropic: tool_use forcing (no native JSON schema output)
   * - null                  — not supported
   */
  structuredOutputs: 'json_schema_strict' | 'response_schema' | 'tool_force' | null;

  /**
   * Maximum context window in tokens.
   * Used to display per-provider limits in the UI and to enforce compaction thresholds.
   */
  maxContextTokens: number;
}

/**
 * A type-safe constant of all required ProviderCapabilities keys.
 * Used by the runtime validator to enumerate required fields without
 * re-declaring them manually.
 */
export const PROVIDER_CAPABILITY_KEYS: ReadonlyArray<keyof ProviderCapabilities> = [
  'extendedThinking',
  'promptCaching',
  'adaptiveToolLoop',
  'interleavedThinkingTool',
  'smoothStreaming',
  'webSearch',
  'webFetch',
  'codeExecution',
  'nativeMemory',
  'inputImage',
  'inputAudio',
  'inputVideo',
  'inputPdf',
  'outputVoice',
  'outputImage',
  'computerUse',
  'structuredOutputs',
  'maxContextTokens',
] as const;
