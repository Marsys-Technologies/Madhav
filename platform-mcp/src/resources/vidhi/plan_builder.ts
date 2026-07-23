/**
 * plan_builder.ts — D-2 Lane V-2. Shared plan assembly for the `vidhi_plan` prompt and the
 * `plan_retrieval` tool (BIND_D-2.md §F1.7 ledger rows 15, 16, 17).
 *
 * Assembles, deterministically, from a question and/or a DR-8 scope tuple:
 *   - the resolved + ECHOED scope_tuple (row 16 — for correction before execution),
 *   - the compiled contract (floor + machine band) via V-1's deterministic compiler,
 *   - a completeness receipt (served/empty/dark per floor item; dark cites its CR — row 17),
 *   - the served capability_version (row 18).
 */
import { compileMultiDomainContract, defaultRegistry } from './compiler.js';
import { resolveScopeTuple, type ScopeTupleInput, type ResolvedScope } from './scope_resolver.js';
import { VIDHI_CAPABILITY_VERSION } from './capability_version.js';
import {
  emitCompletenessReceipt,
  type FloorItemObservation,
  type CompletenessReceipt,
} from '../../lib/completeness_receipt.js';
import type { AdaptiveExpansion, CompiledFloorItem } from './types.js';

export interface BuildPlanArgs {
  readonly chart_id: string;
  readonly question?: string;
  /** DR-8 (intent_classify) scope tuple, if the caller already classified. */
  readonly scope_tuple?: ScopeTupleInput;
  /** Post-execution results from a synthesis, to produce a truthful served/empty receipt. */
  readonly observations?: readonly FloorItemObservation[];
}

export interface VidhiPlan {
  readonly capability_version: string;
  readonly compiler_version: string;
  readonly chart_id: string;
  readonly scope_tuple: ResolvedScope['scope_tuple'];
  readonly scope_resolution: {
    readonly method: ResolvedScope['method'];
    readonly matched_rules: readonly string[];
    readonly fallback_recommended: boolean;
    readonly note: string;
  };
  readonly floor: readonly CompiledFloorItem[];
  readonly machine_band: readonly CompiledFloorItem[];
  /**
   * E-3 Anusaraṇa (VIDHI-PŪRṆATĀ P-3b): the deterministic, one-hop, executor-side follow-rules
   * the compiler pre-authorized from the resolved floor (bhāveśa→occupied-house, kāraka→dispositor,
   * response-flag drills). Chart-agnostic directives — the executor materializes each against live
   * chart facts (never the compiler; that would need chart data). Empty when nothing triggers.
   */
  readonly adaptive_expansions: readonly AdaptiveExpansion[];
  readonly completeness_receipt: CompletenessReceipt;
  readonly llm_extension_note: string;
  readonly correction_hint: string;
}

/**
 * Build a full vidhi plan. Pure/deterministic given identical args (the compiler is pure and
 * capability_version is content-derived) — so identical inputs yield an identical plan, which
 * the tool test asserts.
 */
export function buildVidhiPlan(args: BuildPlanArgs): VidhiPlan {
  const resolved = resolveScopeTuple(args.question, args.scope_tuple);
  const registry = defaultRegistry();
  // E-4 (VIDHI-PŪRṆATĀ P-3b): compile via the multi-domain-aware entry. It delegates to the plain
  // single-intent compileContract when the tuple resolves to one deepdive (the common case → the
  // output is byte-identical), and UNIONS the matched deepdive floors when scope_tuple.domains[]
  // names more than one (dedup on primitive_id+args, primary-first stable order).
  const contract = compileMultiDomainContract(resolved.scope_tuple, registry, args.chart_id);
  const receipt = emitCompletenessReceipt(contract, args.observations ?? []);

  return {
    capability_version: VIDHI_CAPABILITY_VERSION,
    compiler_version: contract.compiler_version,
    chart_id: args.chart_id,
    scope_tuple: contract.scope_tuple,
    scope_resolution: {
      method: resolved.method,
      matched_rules: resolved.matched_rules,
      fallback_recommended: resolved.fallback_recommended,
      note: resolved.note,
    },
    floor: contract.floor,
    machine_band: contract.machine_band,
    adaptive_expansions: contract.adaptive_expansions,
    completeness_receipt: receipt,
    llm_extension_note: contract.llm_extension_note,
    correction_hint:
      'scope_tuple is echoed above. If any field is wrong (e.g. the intent should be ' +
      'career_deepdive not wealth_deepdive, or depth should be structure not deepdive), re-call ' +
      'plan_retrieval with an explicit scope_tuple to override it BEFORE executing the floor. ' +
      'After executing the plan, re-call with `observations` (one {floor_item_id, status: ' +
      "served|empty, source?/empty_reason?} per floor item) to record the post-synthesis " +
      'completeness receipt.',
  };
}
