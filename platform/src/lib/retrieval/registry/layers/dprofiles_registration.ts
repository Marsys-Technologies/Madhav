/**
 * D-PROFILES — MARO Capability Registration (per-wave file)
 * ===========================================================
 * GATE A compliance: this is the per-wave registration file for D-PROFILES.
 * It does NOT edit registry/index.ts or registry/types.ts.
 *
 * Registers the MARO meta-capabilities:
 *   - marsys://tool/maro/orchestrate      — the primary MARO orchestration tool
 *   - marsys://tool/maro/mcp_surface      — MCP channel surface resolver
 *   - marsys://resource/maro/profiles     — read-only profile dossier resource
 *
 * These capabilities are:
 *   - NOT LLM-facing for end-user queries
 *   - Consumed by both the chat channel and the MCP adapter
 *   - Introspectable by the D8 eval harness and the integration smoke test
 *
 * Scope=global: MARO is chart-agnostic at the meta level.
 * chart_id is injected per call from the RetrievalRequest — not stored here.
 */

import { registerCapability } from '../index'
import type { CapabilityDescriptor } from '../types'
import { orchestrate, getMcpSurface, getProfile, PROFILE_VERSION, ANTHROPIC_PROFILE, GEMINI_PROFILE, OPENAI_PROFILE, DEEPSEEK_PROFILE, UNIVERSAL_PROFILE } from '../../maro'
import type { ModelFamily } from '../../maro'

// ── marsys://tool/maro/orchestrate ─────────────────────────────────────────────

const maroOrchestrateTool: CapabilityDescriptor = {
  uri: 'marsys://tool/maro/orchestrate',
  type: 'tool',
  layer: 'L0',
  name: 'maro_orchestrate',
  scope: 'global',

  description: [
    'MARO core: resolves the per-family normalization parameters for a retrieval request.',
    'Takes a chart_id (required, never defaulted), query, model_family, and capability URI.',
    'Returns the full normalization spec: tool_arg_format, cache_strategy, validate_and_repair,',
    'prompt_structure, context_budget_tokens, and reasoning_round_trip mode for the resolved family.',
    'Consumed by both the chat channel (MARO owns loop) and the MCP adapter (surface shaping).',
    'Families: anthropic / gemini / openai / deepseek / universal (undeclared fallback).',
    'NVIDIA NIM: use openai family + is_nvidia_model=true to apply cache_strategy:none override.',
    'Not LLM-facing for end-user queries — internal orchestration layer only.',
  ].join(' '),

  input_schema: {
    chart_id: {
      type: 'string',
      description: 'Chart UUID (required; never defaulted by MARO)',
      required: true,
    },
    query: {
      type: 'string',
      description: 'The retrieval query',
      required: true,
    },
    model_family: {
      type: 'string',
      description: "Declared LLM family: 'anthropic' | 'gemini' | 'openai' | 'deepseek' | 'universal'. Undeclared → 'universal'.",
      required: false,
    },
    capability_uri: {
      type: 'string',
      description: 'URI of the capability to invoke (for behavioral_overrides lookup)',
      required: false,
    },
    model_tier: {
      type: 'string',
      description: "Model tier for context budget: 'worker' | 'mid' | 'premium'. Default: 'premium'.",
      required: false,
    },
    lel_enabled: {
      type: 'boolean',
      description: 'Whether LEL signals are enabled (default: false)',
      required: false,
    },
    is_nvidia_model: {
      type: 'boolean',
      description: 'True if model is on NVIDIA NIM: applies openai profile + cache_strategy:none override',
      required: false,
    },
  },

  required_inputs: ['chart_id', 'query'],

  // D1 topology fields
  archetype: 'orientation_digest',
  traversal_level: 'L-ORIENT',
  tool_role: 'umbrella',
  emits_references: true,
  lel_capable: false,
  grounds_to: undefined,

  // R4: behavioral_overrides — per-family shaping for MARO orchestration meta-tool.
  // These override MARO family defaults when this capability is the active cap descriptor.
  // Most capabilities leave this unset. The orchestrate meta-tool sets it to demonstrate
  // the populate-or-amend contract: any key here merges into capability_overrides in the
  // FamilyNormalization result (see normalizer.ts applyBehavioralOverrides).
  behavioral_overrides: {
    deepseek: {
      // DeepSeek: reduce max_tokens_hint for the meta-tool response (json_object output is small)
      max_tokens_hint: 512,
      note: 'MARO orchestrate result is a small JSON object; no extended reasoning needed on DeepSeek',
    },
    gemini: {
      // Gemini: hint that this tool output is always a flat object (no nested schema issues)
      validate_schema_depth: 'flat',
      note: 'MARO orchestrate result has no nested lists; validate_and_repair can be lightweight',
    },
  },

  mcp_annotations: {
    readOnly: true,
    destructive: false,
  },

  async handler(args: Record<string, unknown>) {
    const chart_id = args['chart_id']
    if (!chart_id || typeof chart_id !== 'string') {
      return {
        content: { error: 'chart_id is required and must be a non-empty string. MARO never defaults chart_id.' },
        is_error: true,
      }
    }

    const query = String(args['query'] ?? '')
    const model_family = args['model_family'] as ModelFamily | undefined
    const capability_uri = args['capability_uri'] as string | undefined
    const model_tier = args['model_tier'] as 'worker' | 'mid' | 'premium' | undefined
    const lel_enabled = Boolean(args['lel_enabled'] ?? false)
    const is_nvidia_model = Boolean(args['is_nvidia_model'] ?? false)

    try {
      const result = orchestrate(
        {
          chart_id,
          query,
          model_family,
          capability_uri: capability_uri ?? '',
          model_tier,
          lel_enabled,
        },
        undefined,  // capability descriptor not available at this meta level
        is_nvidia_model,
      )

      return {
        content: {
          resolved_family: result.resolved_family,
          tool_arg_format: result.normalization.tool_arg_format,
          requires_json_parse: result.normalization.requires_json_parse,
          tool_result_wire: result.normalization.tool_result_wire,
          cache_strategy: result.normalization.cache_strategy,
          structured_output_format: result.normalization.structured_output_format,
          validate_and_repair: result.validate_and_repair,
          context_budget_tokens: result.context_budget_tokens,
          reasoning_round_trip: result.normalization.reasoning_round_trip,
          mcp_transport: result.normalization.mcp_transport,
          strip_mcp_constructs: result.strip_mcp_constructs,
          prompt_structure: result.prompt_structure,
          max_active_tools: result.normalization.max_active_tools,
          profile_version: PROFILE_VERSION,
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err) },
        is_error: true,
      }
    }
  },
}

// ── marsys://tool/maro/mcp_surface ─────────────────────────────────────────────

const maroMcpSurfaceTool: CapabilityDescriptor = {
  uri: 'marsys://tool/maro/mcp_surface',
  type: 'tool',
  layer: 'L0',
  name: 'maro_mcp_surface',
  scope: 'global',

  description: [
    'MARO MCP channel surface resolver. Returns the surface spec for the BYO-MCP channel',
    'given a declared (or undeclared) model family.',
    'Declared family → serve that family\'s profiled surface (max_tools, tool_name_pattern, transport).',
    'Undeclared → serve the universal-best surface (10–15 consolidated tools, cross-family valid names,',
    'dual structuredContent+text output).',
    'DeepSeek on MCP: strip_mcp_constructs=true; serve as plain tool-calling backend only.',
    'All tool names are cross-family valid: snake_case, no hyphens, ≤64 chars, [A-Za-z0-9_.].',
  ].join(' '),

  input_schema: {
    model_family: {
      type: 'string',
      description: "Declared LLM family: 'anthropic' | 'gemini' | 'openai' | 'deepseek' | 'universal'",
      required: false,
    },
  },

  required_inputs: [],

  archetype: 'orientation_digest',
  traversal_level: 'L-ORIENT',
  tool_role: 'umbrella',
  emits_references: false,
  lel_capable: false,
  grounds_to: undefined,

  mcp_annotations: {
    readOnly: true,
    destructive: false,
  },

  async handler(args: Record<string, unknown>) {
    const family = (args['model_family'] as ModelFamily | undefined) ?? 'universal'

    try {
      const surface = getMcpSurface(family)
      return {
        content: {
          family: surface.family,
          max_tools: surface.max_tools,
          tool_name_pattern: surface.tool_name_pattern,
          requires_dual_output: surface.requires_dual_output,
          strip_mcp_constructs: surface.strip_mcp_constructs,
          transport: surface.transport,
          note: family === 'deepseek'
            ? 'DeepSeek has no MCP support — serve as plain tool-calling backend only'
            : family === 'universal'
            ? 'Universal surface: cross-family safe tool names; consolidated 10-15 tools'
            : `Profiled surface for ${family} family`,
        },
        is_error: false,
      }
    } catch (err) {
      return {
        content: { error: String(err) },
        is_error: true,
      }
    }
  },
}

// ── marsys://resource/maro/profiles ───────────────────────────────────────────

const maroProfilesResource: CapabilityDescriptor = {
  uri: 'marsys://resource/maro/profiles',
  type: 'resource',
  layer: 'L0',
  name: 'maro_profiles',
  scope: 'global',

  description: [
    'MARO behavioral profiles — read-only dossier for all four LLM families.',
    'Returns the v1 profile for each family (anthropic / gemini / openai / deepseek)',
    'plus the universal fallback profile. Values tagged UNMEASURED are v1 hypotheses',
    'from RETRIEVAL_GROUNDTRUTH_LLM_PROVIDER_SPEC_v1_0.md awaiting D8 eval-harness',
    'measurement against the MARSYS corpus. Used by the D8 eval harness for profile',
    'validation and by the integration smoke test for roster-completeness checks.',
  ].join(' '),

  archetype: 'calibration',
  traversal_level: 'L-OVERVIEW',
  tool_role: 'quality',
  emits_references: false,
  lel_capable: false,
  grounds_to: undefined,

  mcp_annotations: {
    readOnly: true,
    destructive: false,
  },

  // handler satisfies CapabilityDescriptor contract (resources use loader, but handler is required by the type)
  async handler(_args: Record<string, unknown>) {
    return {
      content: {
        profile_version: PROFILE_VERSION,
        status: 'UNMEASURED',
        status_note: 'v1 hypothesis values from provider spec; awaiting D8 eval-harness measurement on MARSYS corpus',
        profiles: {
          anthropic: ANTHROPIC_PROFILE,
          gemini: GEMINI_PROFILE,
          openai: OPENAI_PROFILE,
          deepseek: DEEPSEEK_PROFILE,
          universal: UNIVERSAL_PROFILE,
        },
        nvidia_note: 'NVIDIA NIM inherits openai profile with cache_strategy:none and streaming_required:true — no fifth profile',
        deprecation_note: 'DeepSeek legacy aliases deepseek-chat + deepseek-reasoner retire 2026-07-24',
      },
      is_error: false,
    }
  },
}

// ── Registration export ────────────────────────────────────────────────────────

/**
 * Register D-PROFILES MARO capabilities.
 * Call at application startup (after registry is initialized).
 * GATE A: only registers NEW files for this wave — does not edit registry/index.ts.
 */
export function registerMaroCapabilities(): void {
  registerCapability(maroOrchestrateTool)
  registerCapability(maroMcpSurfaceTool)
  registerCapability(maroProfilesResource)
}
