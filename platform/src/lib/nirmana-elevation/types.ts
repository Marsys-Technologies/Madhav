import { z } from 'zod'
import { NirmanaLegacyAliasSchema } from './label-contract'
import { NIRMANA_LAYER_NAMES, NIRMANA_MILESTONE_IDS, NIRMANA_STAGE_IDS } from './vocab'

export { NIRMANA_LAYER_NAMES, NIRMANA_MILESTONE_IDS, NIRMANA_STAGE_IDS } from './vocab'

const nullableIso = z.string().datetime().nullable()

/** Version 1 remains the on-wire contract emitted by the existing projection. */
export const NirmanaElevationSnapshotV1Schema = z.object({
  schema_version: z.literal('1.0'),
  generation: z.string().regex(/^[a-f0-9]{64}$/),
  generated_at: z.string().datetime(),
  campaign: z.object({
    campaign_id: z.string(),
    definition_revision: z.string().nullable(),
    definition_status: z.enum(['reconciling', 'frozen', 'superseded']),
    campaign_status: z.enum(['takeover', 'foundation', 'running', 'blocked', 'paused', 'completed', 'unknown']),
    current_layer: z.string().nullable(),
    current_wave: z.number().int().nullable(),
  }),
  progress: z.object({
    denominator_status: z.enum(['reconciling', 'frozen']),
    assets_total: z.number().int().nonnegative().nullable(),
    assets_frozen: z.number().int().nonnegative(),
    layers_total: z.literal(6),
    layers_frozen: z.number().int().nonnegative(),
    buildable_assets_total: z.number().int().nonnegative().nullable(),
    accepted_rebuilds: z.number().int().nonnegative(),
  }),
  layers: z.array(z.object({
    layer_id: z.enum(['L0', 'L1', 'L2', 'L3', 'L4', 'L5']),
    order: z.number().int().min(0).max(5),
    state: z.enum(['locked', 'open', 'blocked', 'verifying', 'frozen', 'unknown']),
    assets_total: z.number().int().nonnegative().nullable(),
    optimization_reviewed: z.number().int().nonnegative(),
    rebuilt_or_dispositioned: z.number().int().nonnegative(),
    verified: z.number().int().nonnegative(),
    frozen: z.number().int().nonnegative(),
    waves: z.array(z.object({
      wave_index: z.number().int().nonnegative(),
      state: z.string(),
      asset_ids: z.array(z.string()),
      active_asset_ids: z.array(z.string()),
      blocked_asset_ids: z.array(z.string()),
    })),
  })),
  assets: z.array(z.object({
    asset_id: z.string(),
    display_name: z.string(),
    layer: z.string(),
    wave_index: z.number().int().nullable(),
    producer_id: z.string().nullable(),
    covered_asset_ids: z.array(z.string()),
    execution_obligation: z.enum(['build', 'probe', 'producer_covered', 'static_acceptance', 'source_acceptance', 'empty_acceptance', 'retired_with_disposition', 'unresolved']),
    lifecycle_state: z.string(),
    readiness_state: z.string(),
    current_run_state: z.string().nullable(),
    progress_mode: z.enum(['determinate', 'indeterminate', 'not_applicable']),
    work_committed: z.number().int().nonnegative().nullable(),
    work_total: z.number().int().nonnegative().nullable(),
    current_unit_label: z.string().nullable(),
    baseline_duration_seconds: z.number().nonnegative().nullable(),
    final_duration_seconds: z.number().nonnegative().nullable(),
    improvement_percent: z.number().nullable(),
    blocker: z.string().nullable(),
    evidence_refs: z.array(z.string()),
  })),
  active_runs: z.array(z.object({
    run_id: z.string(),
    layer: z.string().nullable(),
    wave_index: z.number().int().nullable(),
    state: z.string(),
    active_asset_ids: z.array(z.string()),
    completed_assets: z.number().int().nonnegative(),
    planned_assets: z.number().int().nonnegative(),
    started_at: nullableIso,
    last_progress_at: nullableIso,
  })),
  release: z.object({
    main_sha: z.string().nullable(),
    deployed_sha: z.string().nullable(),
    deployed_revision: z.string().nullable(),
    production_in_sync: z.boolean().nullable(),
    observed_at: nullableIso,
  }),
  sources: z.array(z.object({
    source_id: z.string(),
    provenance: z.string(),
    state: z.enum(['fresh', 'stale', 'unavailable', 'unknown']),
    observed_at: nullableIso,
    age_seconds: z.number().int().nonnegative().nullable(),
    error: z.string().nullable(),
  })),
  data_quality: z.object({
    verdict: z.enum(['reliable', 'degraded', 'unknown']),
    gaps: z.array(z.string()),
    contradictions: z.array(z.string()),
  }),
})

const LayerIdSchema = z.enum(['L0', 'L1', 'L2', 'L3', 'L4', 'L5'])
const LayerNameSchema = z.enum(['Brahmagyan', 'Ganita', 'Bodha', 'Kala', 'Phala', 'Mimamsa'])
const OperationalStateSchema = z.enum(['completed', 'active', 'blocked', 'locked', 'unknown'])

const FoundationLaneSchema = z.object({
  lane_id: z.enum(['A', 'B', 'C', 'D', 'E']),
  name: z.enum(['Asset and DAG census', 'Run and progress truth', 'Hash and invalidation', 'Tracker and release', 'Evidence control']),
  state: z.enum(['completed', 'active', 'locked', 'blocked', 'unknown']),
  completed_at: nullableIso,
  blocked_reason: z.string().nullable(),
})

export const NirmanaCampaignStageSchema = z.object({
  stage_id: z.enum(NIRMANA_STAGE_IDS),
  order: z.number().int().min(0).max(12),
  kind: z.enum(['bootstrap', 'census', 'plan', 'denominator', 'foundation', 'layer', 'closing', 'complete']),
  state: z.enum(['completed', 'active', 'locked', 'blocked', 'paused', 'unknown']),
  required_gate: z.string(),
  completed_at: nullableIso,
  blocked_reason: z.string().nullable(),
  earned: z.number().int().nonnegative().nullable(),
  required: z.number().int().nonnegative().nullable(),
  foundation_lanes: z.array(FoundationLaneSchema).nullable(),
})

export const NirmanaMilestoneSchema = z.object({
  milestone_id: z.enum(NIRMANA_MILESTONE_IDS),
  state: z.enum(['earned', 'current', 'pending', 'not_applicable']),
  event_type: z.string().nullable(),
  accepted_at: nullableIso,
})

const OrderedStagesSchema = z.array(NirmanaCampaignStageSchema)
  .length(NIRMANA_STAGE_IDS.length)
  .superRefine((stages, context) => {
    for (const [index, expectedStageId] of NIRMANA_STAGE_IDS.entries()) {
      const stage = stages[index]
      if (stage?.stage_id !== expectedStageId) {
        context.addIssue({ code: 'custom', path: [index, 'stage_id'], message: `Stage ${index} must be ${expectedStageId}.` })
      }
      if (stage?.order !== index) {
        context.addIssue({ code: 'custom', path: [index, 'order'], message: `Stage ${expectedStageId} must have order ${index}.` })
      }
    }
  })

const V2WaveSchema = z.object({
  wave_index: z.number().int().nonnegative(),
  state: OperationalStateSchema,
  asset_ids: z.array(z.string()),
  completed_asset_ids: z.array(z.string()),
  active_asset_ids: z.array(z.string()),
  blocked_asset_ids: z.array(z.string()),
  locked_asset_ids: z.array(z.string()),
  unknown_asset_ids: z.array(z.string()),
  eligible_next_asset_ids: z.array(z.string()),
}).superRefine((wave, context) => {
  const partitions = [
    ...wave.completed_asset_ids,
    ...wave.active_asset_ids,
    ...wave.blocked_asset_ids,
    ...wave.locked_asset_ids,
    ...wave.unknown_asset_ids,
  ]
  if (new Set(partitions).size !== partitions.length
    || partitions.length !== wave.asset_ids.length
    || wave.asset_ids.some((assetId) => !partitions.includes(assetId))) {
    context.addIssue({ code: 'custom', path: ['asset_ids'], message: 'Every wave asset must appear in exactly one normalized state partition.' })
  }
  if (wave.eligible_next_asset_ids.some((assetId) => !wave.asset_ids.includes(assetId))) {
    context.addIssue({ code: 'custom', path: ['eligible_next_asset_ids'], message: 'Eligible assets must belong to their wave.' })
  }
})

const V2LayerSchema = NirmanaElevationSnapshotV1Schema.shape.layers.element.extend({
  layer_id: LayerIdSchema,
  layer_name: LayerNameSchema,
  required_gate: z.string(),
  eligible_next_asset_ids: z.array(z.string()),
  waves: z.array(V2WaveSchema),
}).superRefine((layer, context) => {
  if (layer.layer_name !== NIRMANA_LAYER_NAMES[layer.layer_id]) {
    context.addIssue({ code: 'custom', path: ['layer_name'], message: `${layer.layer_id} must use its governed layer name.` })
  }
})

const V2AssetSchema = NirmanaElevationSnapshotV1Schema.shape.assets.element.extend({
  sanskrit_name: z.string().nullable(),
  english_name: z.string().min(1),
  description: z.string().nullable(),
  legacy_aliases: z.array(NirmanaLegacyAliasSchema),
  identity_quality: z.enum(['complete', 'incomplete', 'unversioned_fallback']),
  layer: LayerIdSchema,
  campaign_state: OperationalStateSchema,
  milestones: z.array(NirmanaMilestoneSchema)
    .length(NIRMANA_MILESTONE_IDS.length)
    .superRefine((milestones, context) => {
      for (const [index, expectedMilestoneId] of NIRMANA_MILESTONE_IDS.entries()) {
        if (milestones[index]?.milestone_id !== expectedMilestoneId) {
          context.addIssue({ code: 'custom', path: [index, 'milestone_id'], message: `Milestone ${index} must be ${expectedMilestoneId}.` })
        }
      }
    }),
  milestones_earned: z.number().int().nonnegative().max(NIRMANA_MILESTONE_IDS.length).nullable(),
  milestones_required: z.number().int().nonnegative().max(NIRMANA_MILESTONE_IDS.length).nullable(),
  current_action: z.string().nullable(),
  next_action: z.string().nullable(),
  depends_on: z.array(z.string()),
  unlocks: z.array(z.string()),
}).superRefine((asset, context) => {
  if (asset.execution_obligation === 'unresolved') {
    if (asset.milestones_earned !== null || asset.milestones_required !== null) {
      context.addIssue({ code: 'custom', path: ['milestones_earned'], message: 'Unresolved obligations must withhold milestone counters.' })
    }
    return
  }

  const expectedRequired = asset.milestones.filter((milestone) => milestone.state !== 'not_applicable').length
  const expectedEarned = asset.milestones.filter((milestone) => milestone.state === 'earned').length
  if (asset.milestones_required === null) {
    context.addIssue({ code: 'custom', path: ['milestones_required'], message: 'Determinate obligations must declare milestone requirements.' })
  } else if (asset.milestones_required !== expectedRequired) {
    context.addIssue({ code: 'custom', path: ['milestones_required'], message: `Milestone requirements must equal ${expectedRequired} after not-applicable milestones.` })
  }
  if (asset.milestones_earned === null) {
    context.addIssue({ code: 'custom', path: ['milestones_earned'], message: 'Determinate obligations must declare earned milestones.' })
  } else if (asset.milestones_earned !== expectedEarned) {
    context.addIssue({ code: 'custom', path: ['milestones_earned'], message: `Earned milestones must equal ${expectedEarned}.` })
  }
})

const V2SourceSchema = z.object({
  source_id: z.string(),
  provenance: z.string(),
  state: z.enum(['fresh', 'stale', 'unavailable', 'unknown']),
  observed_at: nullableIso,
  age_seconds: z.number().int().nonnegative().nullable(),
  error_code: z.enum([
    'NIRMANA_SOURCE_UNAVAILABLE',
    'NIRMANA_RELEASE_SOURCE_UNAVAILABLE',
    'NIRMANA_RELEASE_PROVENANCE_UNAVAILABLE',
  ]).nullable(),
  error_message: z.string().max(240).nullable(),
})

const AuditReceiptSchema = z.object({
  ledger_ref: z.string().min(1).max(256),
  event_type: z.enum([
    'asset_analysis_accepted',
    'optimization_verdict_accepted',
    'implementation_accepted',
    'accepted_rebuild_observed',
    'integrity_verified',
    'asset_frozen',
    'probe_accepted',
    'static_accepted',
    'source_accepted',
    'empty_accepted',
    'retired_with_disposition',
    'producer_covered',
    'stage_transition_accepted',
    'foundation_lane_accepted',
    'asset_label_catalogue_accepted',
    'build_run_authorized',
  ]),
  entity_type: z.enum(['asset', 'campaign_stage', 'foundation_lane', 'label_catalogue', 'build_run']),
  entity_id: z.string().min(1).max(256),
  related_asset_ids: z.array(z.string()),
  layer: LayerIdSchema.nullable(),
  source_kind: z.string().min(1).max(128),
  source_ref: z.string().min(1).max(512),
  observed_at: z.string().datetime(),
  recorded_at: z.string().datetime(),
  payload_sha256: z.string().regex(/^[a-f0-9]{64}$/),
})

const AuditLedgerRefSchema = z.object({
  ledger_kind: z.enum(['campaign_event', 'build_run']),
  ledger_ref: z.string().min(1).max(256),
})

const ProgramSyncSchema = z.object({
  status: z.enum([
    'unknown',
    'in_sync',
    'baseline_missing',
    'plan_adaptation_required',
    'evidence_refresh_required',
    'label_refresh_required',
    'release_attention',
    'source_unavailable',
  ]),
  observed_at: nullableIso,
  age_seconds: z.number().int().nonnegative().nullable(),
  affected_asset_ids: z.array(z.string()),
  current_definition_sha256: z.string().regex(/^[a-f0-9]{64}$/).nullable(),
  candidate_definition_sha256: z.string().regex(/^[a-f0-9]{64}$/).nullable(),
  candidate_catalogue_sha256: z.string().regex(/^[a-f0-9]{64}$/).nullable(),
})

/** Version 2 adds governed campaign stages and display identities without changing v1. */
export const NirmanaElevationSnapshotV2Schema = NirmanaElevationSnapshotV1Schema.extend({
  schema_version: z.literal('2.0'),
  campaign: NirmanaElevationSnapshotV1Schema.shape.campaign.extend({
    current_stage: z.enum(NIRMANA_STAGE_IDS).nullable(),
  }),
  stages: OrderedStagesSchema,
  layers: z.array(V2LayerSchema),
  assets: z.array(V2AssetSchema),
  sources: z.array(V2SourceSchema),
  program_sync: ProgramSyncSchema,
  audit: z.object({
    receipts: z.array(AuditReceiptSchema),
    raw_ledger_refs: z.array(AuditLedgerRefSchema),
  }),
})

export const NirmanaElevationSnapshotSchema = z.discriminatedUnion('schema_version', [
  NirmanaElevationSnapshotV1Schema,
  NirmanaElevationSnapshotV2Schema,
])

export type NirmanaCampaignStage = z.infer<typeof NirmanaCampaignStageSchema>
export type NirmanaMilestone = z.infer<typeof NirmanaMilestoneSchema>
export type NirmanaElevationSnapshotV1 = z.infer<typeof NirmanaElevationSnapshotV1Schema>
export type NirmanaElevationSnapshotV2 = z.infer<typeof NirmanaElevationSnapshotV2Schema>
export type NirmanaElevationSnapshot = z.infer<typeof NirmanaElevationSnapshotSchema>
