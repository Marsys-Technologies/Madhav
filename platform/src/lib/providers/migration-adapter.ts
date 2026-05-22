/**
 * migration-adapter.ts — Bridge utility (R11 dispatch wiring)
 *
 * Provides the bridge() pass-through helper used by any provider adapter
 * that delegates to an injected generator rather than calling a provider SDK
 * directly. All 5 production adapters (anthropic, google, openai, deepseek,
 * nvidia) now use real SDK calls, so bridge() is available for future use
 * but not actively called by any of them.
 */

import type { ChatRequest, ChatEvent } from './types';
import type { StackId } from './dispatcher';

// ---------------------------------------------------------------------------
// MigrationAdapter — translation bridge
// ---------------------------------------------------------------------------

export class MigrationAdapter {
  async *bridge(
    request: ChatRequest,
    stackId: StackId,
    providerChat: (req: ChatRequest) => AsyncIterable<ChatEvent>,
  ): AsyncIterable<ChatEvent> {
    if (!request.messages || request.messages.length === 0) {
      yield { type: 'error', error: `MigrationAdapter.bridge [${stackId}]: no messages provided` };
      return;
    }
    for await (const event of providerChat(request)) {
      yield event;
    }
  }
}

/**
 * Singleton migration adapter instance — shared across all provider adapters.
 * Each per-provider adapter holds a reference to this for its chat() delegation.
 */
export const migrationAdapter = new MigrationAdapter();
