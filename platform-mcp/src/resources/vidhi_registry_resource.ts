/**
 * vidhi_registry_resource.ts — D-2 Lane V-2, BIND_D-2.md §F1.7 ledger row 14.
 *
 * "Vidhi registry as an MCP resource (resources/list + readable). Rows must match V-1's
 * registry." (BRIEF_D2.md §F1 Lane V-2.)
 *
 * Exposes V-1's vidhi registry (the vendored 1:1 mirror in `./vidhi/` — drift-guarded by
 * `vidhi_registry_parity.test.ts` against `platform/src/lib/vidhi/`) as two MCP resources:
 *
 *   - marsys://vidhi/registry            — the FULL registry: all primitives + all intent
 *                                          floors + the served capability_version. Static,
 *                                          listed, readable. (JSON.)
 *   - marsys://vidhi/floor/{intent}      — one intent-class floor (acharya floor + machine
 *                                          band) as data. A resource TEMPLATE whose list
 *                                          callback enumerates all 8 intent classes so they
 *                                          are individually discoverable in resources/list.
 *
 * The registry is served as data (not prose): a consuming LLM reads the primitives (each
 * with its live-tool mapping + args template + fallback face + known_gap) and floors, then
 * asks the server to compile a scope tuple into a plan (the `vidhi_plan` prompt /
 * `plan_retrieval` tool). This is the "capabilities become contractually consumed"
 * surface (BRIEF_D2 §B0.4).
 */
import type { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { ResourceTemplate } from '@modelcontextprotocol/sdk/server/mcp.js';
import {
  VIDHI_PRIMITIVES,
  VIDHI_INTENT_FLOORS,
  type IntentFloor,
} from './vidhi/index.js';
import { VIDHI_CAPABILITY_VERSION } from './vidhi/capability_version.js';

const REGISTRY_URI = 'marsys://vidhi/registry';

/** The full registry payload — deterministic, capability-versioned. */
export function buildRegistryPayload(): Record<string, unknown> {
  return {
    capability_version: VIDHI_CAPABILITY_VERSION,
    generated_by: 'D-2 Lane V-2 (vidhi delivery); rows mirror V-1 platform/src/lib/vidhi',
    primitive_count: VIDHI_PRIMITIVES.length,
    intent_floor_count: VIDHI_INTENT_FLOORS.length,
    primitives: VIDHI_PRIMITIVES,
    intent_floors: VIDHI_INTENT_FLOORS,
    usage:
      'Read a primitive to see its live_tool + tool_args template. Read a floor (or the ' +
      'marsys://vidhi/floor/{intent} resource) to see the non-skippable acharya floor + machine ' +
      'band for an intent class. To get an executable, chart-filled plan for a question, invoke ' +
      "the 'vidhi_plan' prompt or the 'plan_retrieval' tool with a scope_tuple (or let the tool " +
      'resolve one). Every synthesis carries a completeness receipt (served/empty/dark per floor item).',
  };
}

function floorPayload(floor: IntentFloor): Record<string, unknown> {
  return {
    capability_version: VIDHI_CAPABILITY_VERSION,
    intent: floor.intent,
    version: floor.version,
    floor_items: floor.floor_items,
    cr27_coverage: floor.cr27_coverage,
    notes: floor.notes ?? null,
  };
}

export function registerVidhiRegistryResource(server: McpServer): void {
  // 1. Full registry — static, listed, readable.
  server.resource(
    'vidhi-registry',
    REGISTRY_URI,
    {
      description:
        'The Vidhi Engine registry (D-2): ~37 versioned retrieval primitives (each mapped to a ' +
        'live tool + args + fallback + known_gap) and 8 per-intent-class acharya floors. Rows ' +
        "mirror V-1's canonical registry. Carries capability_version.",
      mimeType: 'application/json',
    },
    async (uri) => ({
      contents: [
        {
          uri: uri.href,
          mimeType: 'application/json',
          text: JSON.stringify(buildRegistryPayload(), null, 2),
        },
      ],
    }),
  );

  // 2. Per-intent floor — template with an enumerating list callback (all 8 intents).
  const floorTemplate = new ResourceTemplate('marsys://vidhi/floor/{intent}', {
    list: async () => ({
      resources: VIDHI_INTENT_FLOORS.map((f) => ({
        uri: `marsys://vidhi/floor/${f.intent}`,
        name: `vidhi-floor-${f.intent}`,
        description: `Vidhi acharya floor + machine band for intent class "${f.intent}" (${f.floor_items.length} items).`,
        mimeType: 'application/json',
      })),
    }),
  });

  server.resource(
    'vidhi-floor',
    floorTemplate,
    async (uri, { intent }) => {
      const key = Array.isArray(intent) ? intent[0] : intent;
      const floor = VIDHI_INTENT_FLOORS.find((f) => f.intent === key);
      const text = floor
        ? JSON.stringify(floorPayload(floor), null, 2)
        : JSON.stringify(
            {
              error: 'unknown_intent',
              requested: key ?? null,
              known_intents: VIDHI_INTENT_FLOORS.map((f) => f.intent),
            },
            null,
            2,
          );
      return {
        contents: [{ uri: uri.href, mimeType: 'application/json', text }],
      };
    },
  );
}

/** Exported for the registration test (retrievability without a live transport). */
export const VIDHI_REGISTRY_URI = REGISTRY_URI;
