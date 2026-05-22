/**
 * dispatcher.ts — Central capability dispatcher for R11 v2 Multi-Provider Parity.
 *
 * The dispatcher is the single import point for the chat surface. It:
 *   1. Maintains a registry of all 5 provider adapters
 *   2. Routes capability calls to the correct adapter based on the active stack ID
 *   3. Re-raises CapabilityUnsupportedError with stack context for "switch stack" UI hints
 *
 * Gated by MARSYS_FLAG_R11V2_USE_ADAPTERS (server-side, default false at A-S0 registration).
 * When false, the caller falls back to the legacy single-shot pipeline.
 * When true, all chat calls route through this dispatcher to the appropriate adapter.
 *
 * Usage in route.ts:
 *   if (configService.getFlag('R11V2_USE_ADAPTERS')) {
 *     const stream = getAdapter(stackId).chat(chatRequest);
 *     // ...
 *   } else {
 *     // legacy path
 *   }
 *
 * Telemetry: when MARSYS_FLAG_R11V2_CAPABILITY_TELEMETRY=true, the dispatcher
 * calls logCapabilityPath() after every successful dispatch. (A-S9 wires this.)
 */

import type { CapabilityAdapter } from './adapter';
import { CapabilityUnsupportedError } from './adapter';
import type { ProviderCapabilities } from './capabilities';
import { AnthropicAdapter } from './anthropic/adapter';
import { ANTHROPIC_MANIFEST } from './anthropic/manifest';
import { GoogleAdapter } from './google/adapter';
import { GOOGLE_MANIFEST } from './google/manifest';
import { OpenAIAdapter } from './openai/adapter';
import { OPENAI_MANIFEST } from './openai/manifest';
import { DeepSeekAdapter } from './deepseek/adapter';
import { DEEPSEEK_MANIFEST } from './deepseek/manifest';
import { NVIDIAAdapter } from './nvidia/adapter';
import { NVIDIA_MANIFEST } from './nvidia/manifest';

// ---------------------------------------------------------------------------
// Stack ID type — matches the runtime_config.ts ModelStack values
// ---------------------------------------------------------------------------

/**
 * The 5 active provider stack IDs.
 * Must stay in sync with the `VALID_STACKS` / `ModelStack` type in runtime_config.ts.
 */
export type StackId = 'anthropic' | 'google' | 'openai' | 'deepseek' | 'nvidia';

export const VALID_STACK_IDS: ReadonlyArray<StackId> = [
  'anthropic',
  'google',
  'openai',
  'deepseek',
  'nvidia',
] as const;

// ---------------------------------------------------------------------------
// Adapter registry (instantiated at module load — all manifests validated)
// ---------------------------------------------------------------------------

interface AdapterEntry {
  adapter: CapabilityAdapter;
  manifest: ProviderCapabilities;
}

const ADAPTER_REGISTRY: Readonly<Record<StackId, AdapterEntry>> = {
  anthropic: { adapter: new AnthropicAdapter(), manifest: ANTHROPIC_MANIFEST },
  google: { adapter: new GoogleAdapter(), manifest: GOOGLE_MANIFEST },
  openai: { adapter: new OpenAIAdapter(), manifest: OPENAI_MANIFEST },
  deepseek: { adapter: new DeepSeekAdapter(), manifest: DEEPSEEK_MANIFEST },
  nvidia: { adapter: new NVIDIAAdapter(), manifest: NVIDIA_MANIFEST },
} as const;

// ---------------------------------------------------------------------------
// CapabilityUnsupportedOnStackError — re-raised with dispatcher context
// ---------------------------------------------------------------------------

/**
 * Thrown by the dispatcher when a capability method throws CapabilityUnsupportedError.
 * Contains the original error plus the stack ID context for UI hint generation.
 */
export class CapabilityUnsupportedOnStackError extends Error {
  public readonly capability: string;
  public readonly stackId: StackId;
  public readonly originalError: CapabilityUnsupportedError;

  constructor(capability: string, stackId: StackId, originalError: CapabilityUnsupportedError) {
    super(
      `[dispatcher] Capability "${capability}" is not supported on stack "${stackId}". ` +
        `Switch to a provider that supports this capability. ` +
        `Original: ${originalError.message}`,
    );
    this.name = 'CapabilityUnsupportedOnStackError';
    this.capability = capability;
    this.stackId = stackId;
    this.originalError = originalError;
  }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Looks up the adapter for the given stack ID.
 * Throws RangeError for unknown stack IDs.
 */
export function getAdapter(stackId: StackId): CapabilityAdapter {
  const entry = ADAPTER_REGISTRY[stackId];
  if (!entry) {
    throw new RangeError(
      `[dispatcher] Unknown stack ID "${stackId}". Valid IDs: ${VALID_STACK_IDS.join(', ')}`,
    );
  }
  return entry.adapter;
}

/**
 * Returns the ProviderCapabilities manifest for the given stack.
 * The UI reads this to determine which affordances to show/hide.
 */
export function getManifest(stackId: StackId): ProviderCapabilities {
  const entry = ADAPTER_REGISTRY[stackId];
  if (!entry) {
    throw new RangeError(
      `[dispatcher] Unknown stack ID "${stackId}". Valid IDs: ${VALID_STACK_IDS.join(', ')}`,
    );
  }
  return entry.manifest;
}

/**
 * Returns the manifests for all registered stacks.
 * Used by the capability availability surface (A-S8) to compute cross-stack availability.
 */
export function getAllManifests(): Readonly<Record<StackId, ProviderCapabilities>> {
  return Object.fromEntries(
    VALID_STACK_IDS.map(id => [id, ADAPTER_REGISTRY[id].manifest]),
  ) as Record<StackId, ProviderCapabilities>;
}

/**
 * Routes a capability method call to the adapter for `stackId`.
 * Re-raises CapabilityUnsupportedError as CapabilityUnsupportedOnStackError.
 *
 * NOTE: Streaming methods (chat, computerUse) should use getAdapter() directly
 * since they return AsyncIterable<T>, not Promise<T>. This dispatch() helper
 * is for Promise-based capability methods (webSearch, webFetch, etc.).
 *
 * A-S9 (telemetry) will add logCapabilityPath() call here.
 */
export async function dispatch<K extends keyof CapabilityAdapter>(
  capability: K,
  request: Parameters<Extract<CapabilityAdapter[K], (...args: unknown[]) => unknown>>[0],
  stackId: StackId,
): Promise<Awaited<ReturnType<Extract<CapabilityAdapter[K], (...args: unknown[]) => unknown>>>> {
  const adapter = getAdapter(stackId);
  const method = adapter[capability];

  if (typeof method !== 'function') {
    throw new TypeError(`[dispatcher] "${capability}" is not a method on CapabilityAdapter`);
  }

  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const result = (method as (req: typeof request) => unknown).call(adapter, request);
    // Await if the result is a Promise
    if (result instanceof Promise) {
      return (await result) as Awaited<
        ReturnType<Extract<CapabilityAdapter[K], (...args: unknown[]) => unknown>>
      >;
    }
    return result as Awaited<
      ReturnType<Extract<CapabilityAdapter[K], (...args: unknown[]) => unknown>>
    >;
  } catch (e) {
    if (e instanceof CapabilityUnsupportedError) {
      throw new CapabilityUnsupportedOnStackError(String(capability), stackId, e);
    }
    throw e;
  }
}

/**
 * Checks whether a given capability is available on `stackId`.
 * Returns true if the manifest declares a non-null value for the capability field.
 *
 * Usage: `if (isCapabilityAvailable('webSearch', 'anthropic')) { ... }`
 */
export function isCapabilityAvailable(
  capability: keyof ProviderCapabilities,
  stackId: StackId,
): boolean {
  const manifest = getManifest(stackId);
  const value = manifest[capability];
  return value !== null && value !== false && value !== undefined;
}

/**
 * Returns a "switch stack" hint for a capability that's not available on `currentStack`.
 * Returns null if the capability is available on `currentStack`.
 * Returns a suggested provider stack ID if any other stack supports it.
 */
export function getSwitchStackHint(
  capability: keyof ProviderCapabilities,
  currentStack: StackId,
): { suggestedStack: StackId } | null {
  if (isCapabilityAvailable(capability, currentStack)) {
    return null; // No hint needed
  }

  // Find the first stack that supports this capability
  for (const stackId of VALID_STACK_IDS) {
    if (stackId !== currentStack && isCapabilityAvailable(capability, stackId)) {
      return { suggestedStack: stackId };
    }
  }

  return null; // No known stack supports this capability
}

// ---------------------------------------------------------------------------
// Telemetry hook (wired in A-S9)
// ---------------------------------------------------------------------------

/**
 * Stub for A-S9 telemetry. Called after every successful dispatch.
 * A-S9 replaces this stub with an actual Observatory log call.
 *
 * @param capability — the capability method that was dispatched
 * @param stackId — the stack the call was routed to
 * @param durationMs — call duration for latency tracking
 */
export function logCapabilityPath(
  _capability: string,
  _stackId: StackId,
  _durationMs: number,
): void {
  // A-S9 implements this: calls capability_telemetry.ts logCapabilityEvent()
  // when MARSYS_FLAG_R11V2_CAPABILITY_TELEMETRY=true
}
