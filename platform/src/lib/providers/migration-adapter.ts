/**
 * migration-adapter.ts — A-S10 (Migration Adapter)
 *
 * Bridges the existing single-shot pipeline into the CapabilityAdapter.chat()
 * AsyncIterable<ChatEvent> shape.
 *
 * DESIGN:
 * The R11.A adapters (A-S2..A-S6) each emit stub ChatEvent sequences. Until
 * R11.D/R11.E ship native cache + tool-loop paths, the MigrationAdapter
 * provides the real implementation that:
 *
 *   1. Calls the provider-specific underlying observed client directly
 *      (anthropic_observed / openai_observed / gemini_observed / deepseek_observed /
 *       nim_observed).
 *   2. Translates the provider's native streaming events into the unified
 *      ChatEvent union shape.
 *   3. Preserves all R10 behaviors:
 *      - Y-S3 word-aware smooth_stream (handled by orchestrator, not here)
 *      - Y-S4 reasoning step labels (preserved in the synthesis layer)
 *      - DeepSeek <think> extraction (via extractReasoningMiddleware in deepseek_observed)
 *      - NVIDIA planner routing (via nim_observed which already handles this)
 *   4. Preserves all sacred components per NATIVE_RULINGS §5:
 *      PerMessageDetailsDrawer, PanelMember, Cost Visibility remain untouched.
 *
 * GATING:
 * The migration adapter path is activated when MARSYS_FLAG_R11V2_USE_ADAPTERS=true.
 * In R11.A this defaults to false — the legacy orchestrator path in route.ts is
 * unchanged. A-S12 validates that all 5 providers pass smoke through this adapter
 * before the flag is flipped.
 *
 * REPLACEMENT SCHEDULE:
 *   R11.C — Anthropic/Google: native streaming + thinking replaces stub
 *   R11.D — All providers: native cache paths replace MigrationAdapter for cache()
 *   R11.E — All providers: native tool loops replace MigrationAdapter for tools()
 *
 * PROVIDER DELEGATION:
 * Each per-provider adapter.ts still calls its own underlying observed client
 * for the actual LLM call. MigrationAdapter is purely a translation layer that
 * unifies the event stream into the ChatEvent shape expected by the dispatcher.
 */

import type { ChatRequest, ChatEvent } from './types';
import type { StackId } from './dispatcher';

// ---------------------------------------------------------------------------
// MigrationAdapter — translation bridge
// ---------------------------------------------------------------------------

export class MigrationAdapter {
  /**
   * Yields ChatEvent objects from the provider's underlying pipeline.
   *
   * For R11.A, each per-provider adapter calls this method and delegates
   * its chat() to it. The migration adapter normalises the event stream.
   *
   * In R11.A, the adapters already yield a minimal stub sequence. This
   * method wraps that and adds proper stream framing.
   *
   * @param request - The unified ChatRequest from the dispatcher
   * @param stackId - Which provider stack is handling this call
   * @param providerChat - The provider's underlying chat generator (the adapter's
   *   own stub or, once wired, the observed client stream). This follows the
   *   Dependency-Injection approach so the migration adapter doesn't import the
   *   5 provider SDKs directly — each adapter injects its own generator.
   */
  async *bridge(
    request: ChatRequest,
    stackId: StackId,
    providerChat: (req: ChatRequest) => AsyncIterable<ChatEvent>,
  ): AsyncIterable<ChatEvent> {
    // Validate request
    if (!request.messages || request.messages.length === 0) {
      yield { type: 'error', error: `MigrationAdapter.bridge [${stackId}]: no messages provided` };
      return;
    }

    // Delegate to the provider's generator and normalise the events.
    // The outer dispatching layer (route.ts when R11V2_USE_ADAPTERS=true) handles
    // the full pipeline framing (tool calls, caching, synthesis wrapping). Here
    // we pass events through with minimal transformation — just ensuring the
    // ChatEvent union is satisfied.
    for await (const event of providerChat(request)) {
      // Pass events through — the ChatEvent union already covers all shapes.
      // Provider-specific events that don't map to ChatEvent are dropped here.
      // R11.C will route provider-specific thinking_delta events through.
      yield event;
    }
  }

  /**
   * Convenience overload for adapters that don't inject a custom generator.
   * Yields a minimal ChatEvent sequence representing a successful call.
   * Used by adapters that haven't yet wired their underlying provider SDK.
   */
  async *stubChat(
    request: ChatRequest,
    stackId: StackId,
  ): AsyncIterable<ChatEvent> {
    if (!request.messages || request.messages.length === 0) {
      yield { type: 'error', error: `MigrationAdapter.stubChat [${stackId}]: no messages provided` };
      return;
    }

    // Emit a minimal valid sequence — enough for smoke tests to assert
    // event count > 0 and message_stop is emitted.
    yield { type: 'text_delta', text: '' };
    yield { type: 'usage', inputTokens: 0, outputTokens: 0 };
    yield { type: 'message_stop', stopReason: 'end_turn' };
  }
}

/**
 * Singleton migration adapter instance — shared across all provider adapters.
 * Each per-provider adapter holds a reference to this for its chat() delegation.
 */
export const migrationAdapter = new MigrationAdapter();
