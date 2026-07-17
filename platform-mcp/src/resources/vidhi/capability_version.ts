/**
 * capability_version.ts — D-2 Lane V-2, BIND_D-2.md §F1.7 ledger row 18.
 *
 * "Serve a `capability_version`; a bump triggers a `tools/list_changed` notification
 * (staleness kill)." (BRIEF_D2.md §F1 Lane V-2.)
 *
 * The vidhi delivery surface (registry resource + plan prompt + plan_retrieval tool) is
 * versioned by a SINGLE deterministic string derived from the compiler version and a
 * content hash of the registry rows it serves. Any change to the registry data or the
 * compiler shifts the hash → the version string changes → a consuming client holding the
 * old version is stale. Because this MCP server is stateless-per-request (a fresh McpServer
 * per POST /mcp — see server.ts), the "staleness kill" is realized by:
 *   (a) SERVING `capability_version` on every vidhi surface (resource + plan output), and
 *   (b) when a client presents a `client_capability_version` that no longer matches the
 *       live one, replying with `capability_stale: true` AND emitting a
 *       `notifications/tools/list_changed` on that request's server (so a compliant host
 *       re-fetches tools/resources/prompts) — see `notifyIfCapabilityStale`.
 *
 * Deterministic by construction: identical registry + compiler → identical version, so a
 * unit test can assert the version is stable across process runs and only moves when the
 * data moves.
 */
import { createHash } from 'node:crypto';
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { COMPILER_VERSION } from './compiler.js';
import { VIDHI_PRIMITIVES, VIDHI_INTENT_FLOORS } from './registry_data.js';

/** Short, stable content hash of the served registry rows. */
function registryContentHash(): string {
  const canonical = JSON.stringify({
    primitives: VIDHI_PRIMITIVES,
    floors: VIDHI_INTENT_FLOORS,
  });
  return createHash('sha256').update(canonical).digest('hex').slice(0, 12);
}

/**
 * The live vidhi capability version, e.g. `vidhi-1.0.0+r3f9a1c8e2b04`.
 * Format: `vidhi-<compiler_version>+r<registry_hash12>`.
 * Deterministic — a pure function of the vendored registry + compiler version.
 */
export const VIDHI_CAPABILITY_VERSION = `vidhi-${COMPILER_VERSION}+r${registryContentHash()}`;

/**
 * Compare a client-presented capability version against the live one. Returns whether the
 * client is stale and, when a server is supplied AND the client is stale, emits a
 * `tools/list_changed` notification on that server (the staleness kill).
 *
 * Never throws: a notification-send failure (e.g. transport not yet connected in a unit
 * test) is swallowed and reported via `notified: false` rather than crashing a tool call.
 *
 * @param clientVersion  The `client_capability_version` the caller sent, or undefined.
 * @param server         The request-scoped McpServer, or undefined (pure-check mode).
 * @returns `{ live, stale, notified }`.
 */
export function notifyIfCapabilityStale(
  clientVersion: string | undefined,
  server?: McpServer,
): { live: string; stale: boolean; notified: boolean } {
  const live = VIDHI_CAPABILITY_VERSION;
  // A client that presents no version is not "stale" — it simply has not cached one yet.
  const stale = typeof clientVersion === 'string' && clientVersion.length > 0 && clientVersion !== live;
  let notified = false;
  if (stale && server) {
    try {
      server.sendToolListChanged();
      notified = true;
    } catch {
      notified = false;
    }
  }
  return { live, stale, notified };
}
