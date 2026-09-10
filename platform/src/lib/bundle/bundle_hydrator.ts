/**
 * bundle_hydrator.ts — resolves PipelinePlan.asset_bundle[] to canonical
 * document content for the synthesis context window.
 *
 * Replaces rule_composer.ts + composition_rules.ts (deleted Phase 4).
 * Floor asset CGM is enforced even when absent from the planner-produced
 * asset_bundle. A non-floor asset that fails to load is skipped with a
 * warning. A floor asset that fails to load throws (fatal).
 *
 * FORENSIC was removed from FLOOR_ASSET_IDS 2026-07-21 (W4 precondition
 * fix): FORENSIC was deleted from CAPABILITY_MANIFEST.json in PR #187
 * (Legacy Teardown) but never removed from this list, so every hydrateBundle
 * call unconditionally threw before any planning or streaming began —
 * PG-2 Lane X-2 root-caused this live against the deployed consult path
 * (REPORT_PG-2.md). No test exercised the real post-teardown manifest state,
 * which is why this survived undetected; see the regression test guarding
 * against it.
 *
 * Returns a HydratedBundle that satisfies the Bundle interface consumed by
 * synthesize() — its mandatory_context is BundleEntry[], so downstream
 * single_model_strategy.ts and validators continue to work unchanged.
 */

import crypto from 'crypto'
import { getStorageClient } from '@/lib/storage'
import type {
  AssetEntry,
  Bundle,
  BundleEntry,
  ManifestData,
} from './types'
import type { PipelinePlan } from '@/lib/pipeline/types'
import { decideAssetScope } from './native_corpus_scope'

const FLOOR_ASSET_IDS: readonly string[] = ['CGM']

export interface HydratedAsset {
  asset_id: string
  content: string
  priority: 1 | 2 | 3
  byte_count: number
}

export interface HydratedBundle extends Bundle {
  /** Per-asset hydrated content + metadata, in load order. */
  assets: HydratedAsset[]
  /** Bytes summed across assets (≠ total_tokens, which is the rough estimate). */
  total_bytes: number
  /** True when at least one floor asset was injected by the hydrator. */
  floor_enforced: boolean
  /**
   * V3-E-016. Assets withheld because they are bound to a DIFFERENT native's
   * chart than the one this turn is about — an honest, inspectable record that
   * something was deliberately not injected, rather than a silent drop.
   * Empty on the bound native's own turns.
   */
  excluded_native_scoped: ExcludedNativeScopedAsset[]
}

export interface ExcludedNativeScopedAsset {
  asset_id: string
  reason: 'native_binding_mismatch' | 'native_binding_unknown'
  was_floor: boolean
}

interface AssetSpec {
  asset_id: string
  priority: 1 | 2 | 3
  reason: string
  is_floor: boolean
}

export interface HydrateBundleOptions {
  /**
   * The chart THIS turn is about. REQUIRED — there is deliberately no
   * unscoped/default path, because the default is what leaked (V3-E-016):
   * every caller already has the chart id in hand, and a call that cannot name
   * its chart has no business receiving a native-bound corpus document.
   */
  chartId: string
}

export async function hydrateBundle(
  plan: PipelinePlan,
  manifest: ManifestData,
  options: HydrateBundleOptions,
): Promise<HydratedBundle> {
  const storage = getStorageClient()
  const { chartId } = options

  // 1. Build effective asset list and enforce floor assets.
  const declared = plan.asset_bundle ?? []
  const declaredIds = new Set(declared.map(a => a.asset_id))

  let floor_enforced = false
  const floorPrepend: AssetSpec[] = []
  for (const id of FLOOR_ASSET_IDS) {
    if (!declaredIds.has(id)) {
      floor_enforced = true
      floorPrepend.push({
        asset_id: id,
        priority: 1,
        reason: 'floor asset enforced by hydrator',
        is_floor: true,
      })
    }
  }

  const effective: AssetSpec[] = [
    ...floorPrepend,
    ...declared.map(a => ({
      asset_id: a.asset_id,
      priority: a.priority,
      reason: a.reason,
      is_floor: FLOOR_ASSET_IDS.includes(a.asset_id),
    })),
  ]

  // 2. Sort by priority ascending (1 = required first).
  effective.sort((a, b) => a.priority - b.priority)

  // 3. Fetch each asset's content. Floor failures throw; non-floor failures warn+skip.
  const assets: HydratedAsset[] = []
  const mandatoryContext: BundleEntry[] = []
  const excluded_native_scoped: ExcludedNativeScopedAsset[] = []
  let totalBytes = 0

  for (const spec of effective) {
    const entry: AssetEntry | undefined = manifest.byId.get(spec.asset_id)

    // ── V3-E-016 — chart scoping, BEFORE any read. ───────────────────────────
    // A native-bound corpus asset (CGM/MSR/CDLM/RM/UCN/LEL — the manifest's own
    // `native_id` field) describes one specific person's chart. It may only
    // enter a synthesis prompt for THAT person's chart. This runs ahead of the
    // storage read so a withheld asset is never even loaded into memory for the
    // wrong turn.
    //
    // Note the floor interaction: a floor asset that is inadmissible here is
    // WITHHELD, not fatal. The existing floor `throw`s below are unchanged and
    // still fire for what they were always about — a floor asset that is
    // missing, path-less, or unreadable, i.e. a broken deployment. "Correctly
    // refused for this chart" is a different condition from "broken", and
    // crashing every non-native chart's turn would be a worse outcome than the
    // honest, recorded absence. Nothing here widens any existing admission.
    if (entry) {
      const scope = decideAssetScope(entry, chartId)
      if (!scope.admissible) {
        excluded_native_scoped.push({
          asset_id: spec.asset_id,
          reason: scope.reason,
          was_floor: spec.is_floor,
        })
        console.warn(
          `[bundle_hydrator] asset '${spec.asset_id}' withheld from chart ${chartId}: ${scope.reason} ` +
            `(asset is bound to native '${entry.native_id}')`,
        )
        continue
      }
    }

    if (!entry) {
      if (spec.is_floor) {
        throw new Error(`bundle_hydrator: floor asset '${spec.asset_id}' not found in manifest`)
      }
      console.warn(`[bundle_hydrator] unknown asset_id '${spec.asset_id}' — skipped`)
      continue
    }
    if (!entry.path) {
      if (spec.is_floor) {
        throw new Error(`bundle_hydrator: floor asset '${spec.asset_id}' has no path in manifest`)
      }
      console.warn(`[bundle_hydrator] asset '${spec.asset_id}' has no path — skipped`)
      continue
    }

    let content: string
    try {
      content = await storage.readFile(entry.path)
    } catch (err) {
      if (spec.is_floor) {
        throw new Error(
          `bundle_hydrator: failed to load floor asset '${spec.asset_id}' from ${entry.path}: ${err instanceof Error ? err.message : String(err)}`,
        )
      }
      console.warn(
        `[bundle_hydrator] failed to load asset '${spec.asset_id}' from ${entry.path}: ${err instanceof Error ? err.message : String(err)} — skipped`,
      )
      continue
    }

    const byte_count = Buffer.byteLength(content, 'utf-8')
    totalBytes += byte_count

    assets.push({
      asset_id: spec.asset_id,
      content,
      priority: spec.priority,
      byte_count,
    })

    mandatoryContext.push({
      canonical_id: entry.canonical_id,
      version: entry.version ?? '1.0',
      content_hash:
        'sha256:' + crypto.createHash('sha256').update(content).digest('hex'),
      token_count: entry.token_count ?? Math.ceil(byte_count / 4),
      role: spec.is_floor ? 'floor' : 'interpretive',
      source: spec.is_floor ? 'rule_composer' : 'planner',
    })
  }

  // 4. Bundle hash = sha256 of sorted canonical_ids (parity with rule_composer).
  const sortedIds = [...mandatoryContext.map(e => e.canonical_id)].sort()
  const bundleHash =
    'sha256:' + crypto.createHash('sha256').update(sortedIds.join('\n')).digest('hex')

  const totalTokens = mandatoryContext.reduce((s, e) => s + e.token_count, 0)

  return {
    bundle_id: crypto.randomUUID(),
    query_plan_reference: plan.query_plan_id ?? '',
    manifest_fingerprint: manifest.fingerprint,
    mandatory_context: mandatoryContext,
    total_tokens: totalTokens,
    bundle_hash: bundleHash,
    schema_version: '1.0',
    assets,
    total_bytes: totalBytes,
    // A floor asset that was prepended and then withheld for scope was never
    // actually injected — reporting `floor_enforced: true` for it would be a
    // signal with no injection behind it (§N.8).
    floor_enforced: floor_enforced && assets.some(a => FLOOR_ASSET_IDS.includes(a.asset_id)),
    excluded_native_scoped,
  }
}
