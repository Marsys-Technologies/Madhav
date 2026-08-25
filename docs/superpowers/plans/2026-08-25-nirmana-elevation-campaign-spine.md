# Nirmāṇa Elevation Campaign Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the horizontal, evidence-heavy Nirmāṇa elevation tracker with an authenticated vertical campaign spine that truthfully projects governed stages, sequential waves, parallel assets, bilingual identities, obligation-aware progress, and secondary audit detail.

**Architecture:** Add an append-only, definition-scoped asset-label catalogue and a typed snapshot v2 projection. Keep DAG, stage, milestone, eligibility, freshness, and identity-quality derivation on the server; split the client into focused presentational components that consume the validated v2 snapshot while retaining a temporary v1 fallback during rollout.

**Tech Stack:** PostgreSQL migrations, Next.js 16 App Router, React 19, TypeScript, Zod 4, Vitest 4, Testing Library, axe-core, Tailwind/Marsys theme tokens, GitHub Actions, Cloud Run.

**Spec:** `docs/superpowers/specs/2026-08-25-nirmana-elevation-campaign-spine-design.md`

## Global Constraints

- Before execution, create a fresh isolated worktree from current `origin/main` with `superpowers:using-git-worktrees`; do not implement in a shared or dirty checkout.
- Read the approved spec and `00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v6_0.md` before editing.
- Preserve the exact state machine: `BOOTSTRAP → T0_CENSUS → PLAN_FROZEN → DENOMINATOR_FROZEN → F0_FOUNDATION → L0 → L1 → L2 → L3 → L4 → L5 → CLOSING → COMPLETE`.
- Preserve strict L0→L5 and wave ordering; horizontal layout means DAG-permitted parallelism only.
- No manually entered percentage, tracker-owned evidence, inferred green state, historical prose promotion, or A1–A22 execution identity.
- `Frozen` remains the canonical asset completion value; `Elevation complete` is explanatory copy only.
- Keep `/admin/nirmana-elevation` and both admin APIs super-admin protected and `Cache-Control: no-store`.
- Do not edit an applied migration. At plan time the next migration number is 595; immediately before Task 1, run `npm run guard:migration-numbers` and `npm run migration:next`. If the next number is no longer 595, rebase onto `origin/main`, rename the planned migration to the newly reported number, and update only the migration-path references in this plan before writing SQL.
- Use the `create-migration` skill for Task 1.
- Use Marsys theme tokens already present in the application; no purple, decorative gradients, large flat gold fills, or continuous motion.
- Scoped lint/tests come before the full repository gates. Do not broaden the change into unrelated lint cleanup; if a pre-existing full-gate failure appears, prove it against `origin/main` and report it separately.
- Never use or expose user credentials. Final authenticated super-admin smoke testing is performed by an authorized human in their own browser session.

---

### Task 1: Append-only asset-label catalogue migration

**Files:**
- Create: `platform/migrations/598_nirmana_elevation_asset_labels.sql`
- Create: `platform/tests/unit/migrations/nirmana_elevation_asset_labels.test.ts`

**Interfaces:**
- Consumes: existing `nirmana_elevation_campaign_definitions(campaign_id, definition_revision)` from migration 592.
- Produces: append-only table `nirmana_elevation_asset_labels` keyed by campaign, definition, catalogue revision, and canonical asset ID.

- [ ] **Step 1: Install the platform dependencies in the isolated worktree**

Run:

```bash
cd platform
npm ci
```

Expected: exit 0 and `platform/node_modules/.bin/vitest` exists.

- [ ] **Step 2: Verify and reserve migration 598**

Run:

```bash
cd platform
npm run guard:migration-numbers
npm run migration:next
```

Expected: the guard passes and the second command prints `598`. If it does not, follow the migration-number constraint above before continuing.

- [ ] **Step 3: Write the failing migration-contract test**

Create `platform/tests/unit/migrations/nirmana_elevation_asset_labels.test.ts`:

```ts
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const sql = readFileSync(join(process.cwd(), 'migrations/598_nirmana_elevation_asset_labels.sql'), 'utf8')

describe('migration 598: Nirmana elevation asset labels', () => {
  it('creates a definition-scoped append-only label catalogue', () => {
    expect(sql).toContain('CREATE TABLE IF NOT EXISTS nirmana_elevation_asset_labels')
    expect(sql).toContain('PRIMARY KEY (campaign_id, definition_revision, catalogue_revision, asset_id)')
    expect(sql).toContain('REFERENCES nirmana_elevation_campaign_definitions')
    expect(sql).toContain('CHECK (label_digest ~')
    expect(sql).toContain('jsonb_typeof(legacy_aliases) = \'array\'')
    expect(sql).toContain('BEFORE UPDATE OR DELETE ON nirmana_elevation_asset_labels')
    expect(sql).toContain('nirmana_elevation_asset_labels is append-only')
  })
})
```

- [ ] **Step 4: Run the test to verify it fails**

Run:

```bash
cd platform
npx vitest run tests/unit/migrations/nirmana_elevation_asset_labels.test.ts
```

Expected: FAIL because migration 598 does not exist.

- [ ] **Step 5: Create the migration**

Create `platform/migrations/598_nirmana_elevation_asset_labels.sql` with this structure:

```sql
-- Migration 598: immutable bilingual labels for the Nirmana elevation tracker
-- Created: 2026-08-25

BEGIN;

CREATE TABLE IF NOT EXISTS nirmana_elevation_asset_labels (
  campaign_id text NOT NULL,
  definition_revision text NOT NULL,
  catalogue_revision text NOT NULL CHECK (catalogue_revision ~ '^[A-Za-z0-9._-]{1,128}$'),
  asset_id text NOT NULL,
  sanskrit_name text,
  english_name text,
  description text,
  legacy_aliases jsonb NOT NULL DEFAULT '[]'::jsonb
    CHECK (jsonb_typeof(legacy_aliases) = 'array'),
  source_ref text NOT NULL,
  label_digest text NOT NULL CHECK (label_digest ~ '^[a-f0-9]{64}$'),
  recorded_at timestamptz NOT NULL DEFAULT now(),
  recorded_by text NOT NULL,
  PRIMARY KEY (campaign_id, definition_revision, catalogue_revision, asset_id),
  CONSTRAINT nirmana_elevation_label_definition_fk
    FOREIGN KEY (campaign_id, definition_revision)
    REFERENCES nirmana_elevation_campaign_definitions (campaign_id, definition_revision),
  CONSTRAINT nirmana_elevation_label_has_human_text CHECK (
    sanskrit_name IS NOT NULL OR english_name IS NOT NULL OR description IS NOT NULL
  )
);

CREATE INDEX IF NOT EXISTS nirmana_elevation_asset_labels_revision_idx
  ON nirmana_elevation_asset_labels (campaign_id, definition_revision, catalogue_revision);

CREATE OR REPLACE FUNCTION nirmana_elevation_prevent_label_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  RAISE EXCEPTION 'nirmana_elevation_asset_labels is append-only';
END;
$$;

DROP TRIGGER IF EXISTS nirmana_elevation_asset_labels_append_only
  ON nirmana_elevation_asset_labels;
CREATE TRIGGER nirmana_elevation_asset_labels_append_only
  BEFORE UPDATE OR DELETE ON nirmana_elevation_asset_labels
  FOR EACH ROW EXECUTE FUNCTION nirmana_elevation_prevent_label_mutation();

COMMENT ON TABLE nirmana_elevation_asset_labels IS
  'Append-only, definition-scoped canonical Sanskrit, English, description, and verified legacy labels for the Nirmana elevation projection.';

COMMIT;
```

- [ ] **Step 6: Run the focused test and migration guard**

Run:

```bash
cd platform
npx vitest run tests/unit/migrations/nirmana_elevation_asset_labels.test.ts
npm run guard:migration-numbers
```

Expected: both commands pass.

- [ ] **Step 7: Commit Task 1**

```bash
git add platform/migrations/598_nirmana_elevation_asset_labels.sql platform/tests/unit/migrations/nirmana_elevation_asset_labels.test.ts
git commit -m "feat(nirmana): add immutable asset label catalogue"
```

---

### Task 2: Catalogue digest, transactional recording, and audited ingress

**Files:**
- Create: `platform/src/lib/nirmana-elevation/labels.ts`
- Create: `platform/src/lib/nirmana-elevation/__tests__/labels.test.ts`
- Modify: `platform/src/app/api/admin/nirmana-elevation/evidence/route.ts`
- Modify: `platform/src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts`

**Interfaces:**
- Consumes: `getPool()` from `@/lib/db/client` and the table created in Task 1.
- Produces: `NirmanaAssetLabelSchema`, `NirmanaLabelCatalogueInputSchema`, `canonicalLabelCatalogueDigest(input)`, and `recordNirmanaElevationLabelCatalogue(input): Promise<'created' | 'idempotent'>`.

- [ ] **Step 1: Write failing digest and append-only recording tests**

Create `platform/src/lib/nirmana-elevation/__tests__/labels.test.ts` around these cases:

```ts
// @vitest-environment node
import { beforeEach, describe, expect, it, vi } from 'vitest'

vi.mock('server-only', () => ({}))
const clientQuery = vi.fn()
const release = vi.fn()
vi.mock('@/lib/db/client', () => ({
  getPool: async () => ({ connect: async () => ({ query: clientQuery, release }) }),
}))

import {
  canonicalLabelCatalogueDigest,
  recordNirmanaElevationLabelCatalogue,
} from '../labels'

const input = {
  campaign_id: 'nirmana-elevation' as const,
  definition_revision: 'r1',
  catalogue_revision: 'labels-v1',
  labels: [{
    asset_id: 'ka_smriti',
    sanskrit_name: 'Kala Smriti',
    english_name: 'Per-varsha digest',
    description: 'Produces a year-by-year digest of annual chart features.',
    legacy_aliases: [{ asset_id: 'A22', sanskrit_name: 'Varsha-Darshan', english_name: 'Yearly Vision' }],
    source_ref: 'PARIKSHA/ASSET_REGISTRY.md#kala-smriti',
  }],
  catalogue_sha256: '',
  recorded_by: 'admin-1',
}

describe('Nirmana label catalogue', () => {
  beforeEach(() => { clientQuery.mockReset(); release.mockReset() })

  it('has an order-independent canonical digest', () => {
    const second = { ...input.labels[0], asset_id: 'sphurana', legacy_aliases: [] }
    expect(canonicalLabelCatalogueDigest([input.labels[0], second]))
      .toBe(canonicalLabelCatalogueDigest([second, input.labels[0]]))
  })

  it('records labels and the acceptance receipt in one transaction', async () => {
    const digest = canonicalLabelCatalogueDigest(input.labels)
    clientQuery
      .mockResolvedValueOnce(undefined) // BEGIN
      .mockResolvedValueOnce({ rowCount: 1 }) // definition lock/check
      .mockResolvedValueOnce({ rowCount: 1 }) // label insert
      .mockResolvedValueOnce({ rowCount: 1 }) // acceptance event
      .mockResolvedValueOnce(undefined) // COMMIT

    await expect(recordNirmanaElevationLabelCatalogue({ ...input, catalogue_sha256: digest }))
      .resolves.toBe('created')
    expect(clientQuery).toHaveBeenNthCalledWith(1, 'BEGIN')
    expect(clientQuery).toHaveBeenLastCalledWith('COMMIT')
    expect(release).toHaveBeenCalledOnce()
  })
})
```

- [ ] **Step 2: Run the label test to verify it fails**

Run:

```bash
cd platform
npx vitest run src/lib/nirmana-elevation/__tests__/labels.test.ts
```

Expected: FAIL because `../labels` does not exist.

- [ ] **Step 3: Implement the typed catalogue and canonical digest**

Create `platform/src/lib/nirmana-elevation/labels.ts` with these public types and canonicalization rules:

```ts
import 'server-only'
import { createHash } from 'node:crypto'
import { z } from 'zod'
import { getPool } from '@/lib/db/client'

export const NirmanaLegacyAliasSchema = z.object({
  asset_id: z.string().min(1),
  sanskrit_name: z.string().min(1).nullable(),
  english_name: z.string().min(1).nullable(),
}).strict()

export const NirmanaAssetLabelSchema = z.object({
  asset_id: z.string().min(1),
  sanskrit_name: z.string().min(1).nullable(),
  english_name: z.string().min(1).nullable(),
  description: z.string().min(1).nullable(),
  legacy_aliases: z.array(NirmanaLegacyAliasSchema),
  source_ref: z.string().min(1).max(512),
}).strict().refine(
  (value) => value.sanskrit_name !== null || value.english_name !== null || value.description !== null,
  'At least one governed human-readable label is required.',
)

export const NirmanaLabelCatalogueInputSchema = z.object({
  campaign_id: z.literal('nirmana-elevation'),
  definition_revision: z.string().regex(/^[A-Za-z0-9._-]{1,128}$/),
  catalogue_revision: z.string().regex(/^[A-Za-z0-9._-]{1,128}$/),
  labels: z.array(NirmanaAssetLabelSchema).min(1),
  catalogue_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  recorded_by: z.string().min(1),
}).strict()

function stableJson(value: unknown): string {
  if (value === null || typeof value !== 'object') return JSON.stringify(value)
  if (Array.isArray(value)) return `[${value.map(stableJson).join(',')}]`
  const object = value as Record<string, unknown>
  return `{${Object.keys(object).sort().map((key) => `${JSON.stringify(key)}:${stableJson(object[key])}`).join(',')}}`
}

export function canonicalLabelCatalogueDigest(labels: z.infer<typeof NirmanaAssetLabelSchema>[]): string {
  const parsed = z.array(NirmanaAssetLabelSchema).min(1).parse(labels)
  const assetIds = new Set(parsed.map((label) => label.asset_id))
  if (assetIds.size !== parsed.length) throw new Error('Label catalogue asset IDs must be unique.')
  return createHash('sha256').update(stableJson([...parsed].sort((a, b) => a.asset_id.localeCompare(b.asset_id)))).digest('hex')
}
```

Implement `recordNirmanaElevationLabelCatalogue` with a single checked transaction:

```ts
export async function recordNirmanaElevationLabelCatalogue(
  raw: z.input<typeof NirmanaLabelCatalogueInputSchema>,
): Promise<'created' | 'idempotent'> {
  const input = NirmanaLabelCatalogueInputSchema.parse(raw)
  const digest = canonicalLabelCatalogueDigest(input.labels)
  if (digest !== input.catalogue_sha256) throw new Error('Label catalogue digest mismatch.')

  const client = await (await getPool()).connect()
  try {
    await client.query('BEGIN')
    const definition = await client.query(
      `SELECT definition_status FROM nirmana_elevation_campaign_definitions
       WHERE campaign_id = $1 AND definition_revision = $2 FOR SHARE`,
      [input.campaign_id, input.definition_revision],
    )
    if (definition.rows[0]?.definition_status !== 'frozen') throw new Error('Labels require a frozen campaign definition.')

    const inserted = await client.query(
      `INSERT INTO nirmana_elevation_asset_labels
       (campaign_id, definition_revision, catalogue_revision, asset_id, sanskrit_name,
        english_name, description, legacy_aliases, source_ref, label_digest, recorded_by)
       SELECT $1, $2, $3, label.asset_id, label.sanskrit_name, label.english_name,
              label.description, label.legacy_aliases, label.source_ref, $5, $6
       FROM jsonb_to_recordset($4::jsonb) AS label(
         asset_id text, sanskrit_name text, english_name text, description text,
         legacy_aliases jsonb, source_ref text
       )
       ON CONFLICT DO NOTHING`,
      [input.campaign_id, input.definition_revision, input.catalogue_revision,
       JSON.stringify(input.labels), digest, input.recorded_by],
    )

    const receipt = await client.query(
      `INSERT INTO nirmana_elevation_campaign_events
       (campaign_id, definition_revision, idempotency_key, event_type, entity_type, entity_id,
        evidence_payload, source_kind, source_ref, observed_at, recorded_by)
       VALUES ($1, $2, $3, 'asset_label_catalogue_accepted', 'label_catalogue', $4,
               $5::jsonb, 'governed_catalogue', $6, now(), $7)
       ON CONFLICT (campaign_id, definition_revision, idempotency_key) DO NOTHING
       RETURNING event_id`,
      [input.campaign_id, input.definition_revision,
       `asset-label-catalogue:${input.catalogue_revision}:${digest}`,
       input.catalogue_revision, JSON.stringify({ catalogue_sha256: digest, asset_count: input.labels.length }),
       `label_catalogue:${input.catalogue_revision}`, input.recorded_by],
    )
    if (inserted.rowCount === input.labels.length && receipt.rowCount === 1) {
      await client.query('COMMIT')
      return 'created'
    }

    const existingLabels = await client.query(
      `SELECT count(*)::int AS label_count,
              COALESCE(bool_and(label_digest = $4), false) AS digest_matches
         FROM nirmana_elevation_asset_labels
        WHERE campaign_id = $1 AND definition_revision = $2 AND catalogue_revision = $3`,
      [input.campaign_id, input.definition_revision, input.catalogue_revision, digest],
    )
    const existingReceipt = await client.query(
      `SELECT evidence_payload
         FROM nirmana_elevation_campaign_events
        WHERE campaign_id = $1 AND definition_revision = $2
          AND idempotency_key = $3`,
      [input.campaign_id, input.definition_revision,
       `asset-label-catalogue:${input.catalogue_revision}:${digest}`],
    )
    const payload = existingReceipt.rows[0]?.evidence_payload as Record<string, unknown> | undefined
    if (existingLabels.rows[0]?.label_count !== input.labels.length
      || existingLabels.rows[0]?.digest_matches !== true
      || payload?.catalogue_sha256 !== digest
      || payload?.asset_count !== input.labels.length) {
      throw new Error('Label catalogue revision conflicts with an existing receipt.')
    }
    await client.query('COMMIT')
    return 'idempotent'
  } catch (error) {
    await client.query('ROLLBACK')
    throw error
  } finally {
    client.release()
  }
}
```

Add one test with an existing mismatched digest/count and assert the function rolls back and throws `Label catalogue revision conflicts with an existing receipt.`

- [ ] **Step 4: Add the failing audited-ingress route test**

In `platform/src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts`, mock `recordNirmanaElevationLabelCatalogue`, post:

```ts
{
  command: 'record_label_catalogue',
  campaign_id: 'nirmana-elevation',
  definition_revision: 'r1',
  catalogue_revision: 'labels-v1',
  labels: [{
    asset_id: 'ka_smriti',
    sanskrit_name: 'Kala Smriti',
    english_name: 'Per-varsha digest',
    description: 'Produces a year-by-year digest of annual chart features.',
    legacy_aliases: [],
    source_ref: 'PARIKSHA/ASSET_REGISTRY.md#kala-smriti',
  }],
  catalogue_sha256: canonicalLabelCatalogueDigest(labels),
}
```

Assert 201, `Cache-Control: no-store`, recorder called with `recorded_by: 'admin-1'`, and audit action `nirmana_label_catalogue_recorded`. Also assert a non-super-admin request performs no write.

- [ ] **Step 5: Extend the evidence route**

Import the catalogue schema/recorder, add `record_label_catalogue` to the command union, handle it before generic evidence, and write only this audit metadata:

```ts
{
  campaign_id,
  definition_revision,
  catalogue_revision,
  catalogue_sha256,
  asset_count: labels.length,
  outcome,
}
```

Do not place the full label payload in the audit log.

- [ ] **Step 6: Run focused tests**

Run:

```bash
cd platform
npx vitest run src/lib/nirmana-elevation/__tests__/labels.test.ts src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts
```

Expected: PASS.

- [ ] **Step 7: Commit Task 2**

```bash
git add platform/src/lib/nirmana-elevation/labels.ts platform/src/lib/nirmana-elevation/__tests__/labels.test.ts platform/src/app/api/admin/nirmana-elevation/evidence/route.ts platform/src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts
git commit -m "feat(nirmana): add governed bilingual label ingress"
```

---

### Task 3: Snapshot v2 contract and shared vocabularies

**Files:**
- Modify: `platform/src/lib/nirmana-elevation/types.ts`
- Create: `platform/src/lib/nirmana-elevation/vocab.ts`
- Create: `platform/src/lib/nirmana-elevation/__tests__/types-v2.test.ts`
- Create: `platform/src/lib/nirmana-elevation/__tests__/fixture-v2.ts`

**Interfaces:**
- Produces: `NirmanaElevationSnapshotV1Schema`, `NirmanaElevationSnapshotV2Schema`, their inferred types, `NirmanaElevationSnapshotSchema` as a discriminated union, `NIRMANA_STAGE_IDS`, `NIRMANA_LAYER_NAMES`, `NirmanaMilestone`, and `NirmanaCampaignStage`.

- [ ] **Step 1: Write failing v2 schema tests**

Test that the fixture:

- parses only as schema version 2.0;
- contains all 13 stage IDs in exact order;
- rejects a bare layer without `layer_name`;
- rejects an asset without separate identity fields and milestones;
- accepts nullable Sanskrit/description with `identity_quality: 'incomplete'`;
- accepts a v1 fixture through the union during compatibility.

Use this exact stage array in the test:

```ts
[
  'BOOTSTRAP', 'T0_CENSUS', 'PLAN_FROZEN', 'DENOMINATOR_FROZEN', 'F0_FOUNDATION',
  'L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'CLOSING', 'COMPLETE',
]
```

The array contains 13 entries; assert 13 so the test catches accidental reintroduction of P0/P1/P2.

- [ ] **Step 2: Run the type test to verify it fails**

```bash
cd platform
npx vitest run src/lib/nirmana-elevation/__tests__/types-v2.test.ts
```

Expected: FAIL because the v2 exports do not exist.

- [ ] **Step 3: Create shared vocabulary constants**

Create `platform/src/lib/nirmana-elevation/vocab.ts`:

```ts
export const NIRMANA_STAGE_IDS = [
  'BOOTSTRAP', 'T0_CENSUS', 'PLAN_FROZEN', 'DENOMINATOR_FROZEN', 'F0_FOUNDATION',
  'L0', 'L1', 'L2', 'L3', 'L4', 'L5', 'CLOSING', 'COMPLETE',
] as const

export const NIRMANA_LAYER_NAMES = {
  L0: 'Brahmagyan', L1: 'Ganita', L2: 'Bodha',
  L3: 'Kala', L4: 'Phala', L5: 'Mimamsa',
} as const

export const NIRMANA_MILESTONE_IDS = [
  'analysed', 'decision_accepted', 'built_or_dispositioned',
  'deployed_and_executed', 'verified', 'frozen',
] as const
```

- [ ] **Step 4: Implement v1/v2 schemas**

Rename the current schema export to `NirmanaElevationSnapshotV1Schema` without changing its shape. Add v2 schemas with these required structures:

```ts
const CampaignStageSchema = z.object({
  stage_id: z.enum(NIRMANA_STAGE_IDS),
  order: z.number().int().min(0).max(12),
  kind: z.enum(['bootstrap', 'census', 'plan', 'denominator', 'foundation', 'layer', 'closing', 'complete']),
  state: z.enum(['completed', 'active', 'locked', 'blocked', 'paused', 'unknown']),
  required_gate: z.string(),
  completed_at: nullableIso,
  blocked_reason: z.string().nullable(),
  earned: z.number().int().nonnegative().nullable(),
  required: z.number().int().nonnegative().nullable(),
  foundation_lanes: z.array(z.object({
    lane_id: z.enum(['A', 'B', 'C', 'D', 'E']),
    name: z.enum(['Asset and DAG census', 'Run and progress truth', 'Hash and invalidation', 'Tracker and release', 'Evidence control']),
    state: z.enum(['completed', 'active', 'locked', 'blocked', 'unknown']),
    completed_at: nullableIso,
    blocked_reason: z.string().nullable(),
  })).nullable(),
})

const AssetMilestoneSchema = z.object({
  milestone_id: z.enum(NIRMANA_MILESTONE_IDS),
  state: z.enum(['earned', 'current', 'pending', 'not_applicable']),
  event_type: z.string().nullable(),
  accepted_at: nullableIso,
})
```

V2 assets must include `sanskrit_name`, `english_name`, `description`, `legacy_aliases`, `identity_quality`, `milestones`, `milestones_earned`, `milestones_required`, `current_action`, `next_action`, `depends_on`, and `unlocks`. V2 layers must include `layer_name`, `required_gate`, and `eligible_next_asset_ids`. V2 campaign must include `current_stage` and ordered `stages`.

Export:

```ts
export const NirmanaElevationSnapshotSchema = z.discriminatedUnion('schema_version', [
  NirmanaElevationSnapshotV1Schema,
  NirmanaElevationSnapshotV2Schema,
])
```

- [ ] **Step 5: Add a complete reusable v2 fixture**

Create `fixture-v2.ts` with a frozen 128-asset denominator, current stage `L0`, current wave 2, all 13 stages, one active build asset, one blocked probe asset, one frozen producer-covered asset, and all six layers. Use `ka_smriti / Kala Smriti / Per-varsha digest` as the bilingual example.

- [ ] **Step 6: Run the focused type tests**

```bash
cd platform
npx vitest run src/lib/nirmana-elevation/__tests__/types-v2.test.ts
```

Expected: PASS.

- [ ] **Step 7: Commit Task 3**

```bash
git add platform/src/lib/nirmana-elevation/types.ts platform/src/lib/nirmana-elevation/vocab.ts platform/src/lib/nirmana-elevation/__tests__/types-v2.test.ts platform/src/lib/nirmana-elevation/__tests__/fixture-v2.ts
git commit -m "feat(nirmana): define snapshot v2 campaign contract"
```

---

### Task 4: Pure stage, milestone, and DAG eligibility projection

**Files:**
- Create: `platform/src/lib/nirmana-elevation/projection.ts`
- Create: `platform/src/lib/nirmana-elevation/__tests__/projection.test.ts`

**Interfaces:**
- Consumes: v2 types and vocab from Task 3 plus manifest assets and campaign events.
- Produces: `projectCampaignStages(input)`, `projectAssetMilestones(input)`, and `deriveEligibleNextAssetIds(input)`.

- [ ] **Step 1: Write failing stage-projection tests**

Cover these exact rules:

```ts
it('uses the latest accepted stage transition instead of guessing from incomplete stages')
it('leaves current_stage unknown when no valid stage-transition evidence exists')
it('does not mark F0 complete from a frozen denominator alone')
it('projects all five F0 lanes from foundation-lane receipts and leaves missing lanes unknown')
it('marks a layer complete only when every in-layer asset is frozen and prior layers are complete')
it('turns contradictory transitions into a blocked stage and a contradiction')
```

Use `stage_transition_accepted` campaign events with `entity_type: 'campaign_stage'`, canonical stage IDs, and evidence payload `{ from_stage, to_stage, prerequisites_sha256 }`.
Use `foundation_lane_accepted` events with `entity_type: 'foundation_lane'`, entity IDs `A` through `E`, and evidence payload `{ acceptance_sha256 }`.

- [ ] **Step 2: Write failing milestone tests**

Cover:

- build with accepted change: all six required;
- build with `change_required: false`: milestone 3 N/A;
- probe: milestone 3 N/A unless a change receipt exists;
- source/static/empty/retired disposition: milestone 3 earned, milestone 4 N/A;
- producer-covered: inherited execution points to producer and never claims an independent build;
- unresolved: no determinate progress;
- a present event from another definition revision earns nothing.

Expected build event mapping:

```ts
{
  analysed: 'asset_analysis_accepted',
  decision_accepted: 'optimization_verdict_accepted',
  built_or_dispositioned: 'implementation_accepted',
  deployed_and_executed: 'accepted_rebuild_observed',
  verified: 'integrity_verified',
  frozen: 'asset_frozen',
}
```

- [ ] **Step 3: Write failing DAG eligibility tests**

Assert that only assets in the next unfinished wave are eligible, every same/lower-layer dependency is frozen or validly inherited, no blocked/unresolved asset is eligible, and L1 remains locked until all L0 assets are frozen.

- [ ] **Step 4: Run the projection test to verify it fails**

```bash
cd platform
npx vitest run src/lib/nirmana-elevation/__tests__/projection.test.ts
```

Expected: FAIL because `projection.ts` does not exist.

- [ ] **Step 5: Implement pure projections**

Use explicit, side-effect-free signatures:

```ts
export function projectCampaignStages(input: {
  definitionStatus: 'reconciling' | 'frozen' | 'superseded'
  events: CampaignEvent[]
  layers: Array<{ layer_id: NirmanaLayerId; state: string; assets_total: number | null; frozen: number }>
}): { current_stage: NirmanaStageId | null; stages: NirmanaCampaignStage[]; contradictions: string[] }

export interface CampaignEvent {
  campaign_id: string
  definition_revision: string
  event_type: string
  entity_type: string
  entity_id: string
  layer: string | null
  evidence_payload: unknown
  observed_at: string
  recorded_at: string
}

type ManifestAsset = NirmanaElevationManifest['assets'][number]

export interface AssetMilestoneProjection {
  milestones: NirmanaElevationSnapshotV2['assets'][number]['milestones']
  milestones_earned: number | null
  milestones_required: number | null
  current_action: string | null
  next_action: string | null
  inherited_from_asset_id: string | null
}

export function projectAssetMilestones(input: {
  asset: ManifestAsset
  events: CampaignEvent[]
  activeRunState: string | null
  producerAsset: ManifestAsset | null
}): AssetMilestoneProjection

export function deriveEligibleNextAssetIds(input: {
  manifestAssets: ManifestAsset[]
  frozenAssetIds: Set<string>
  blockedAssetIds: Set<string>
  currentLayer: NirmanaLayerId | null
  currentWave: number | null
}): string[]
```

Validate transition order against `NIRMANA_STAGE_IDS`; never use lexical comparison. Return sorted asset IDs for deterministic generation hashes.

- [ ] **Step 6: Run projection tests**

```bash
cd platform
npx vitest run src/lib/nirmana-elevation/__tests__/projection.test.ts
```

Expected: PASS.

- [ ] **Step 7: Commit Task 4**

```bash
git add platform/src/lib/nirmana-elevation/projection.ts platform/src/lib/nirmana-elevation/__tests__/projection.test.ts
git commit -m "feat(nirmana): derive governed campaign progress"
```

---

### Task 5: Load labels and emit a self-consistent snapshot v2

**Files:**
- Modify: `platform/src/lib/nirmana-elevation/snapshot.ts`
- Modify: `platform/src/lib/nirmana-elevation/__tests__/snapshot.test.ts`
- Modify: `platform/src/app/api/admin/nirmana-elevation/snapshot/__tests__/route.test.ts`

**Interfaces:**
- Consumes: Task 2 label table/acceptance receipt and Task 4 pure projections.
- Produces: schema-valid v2 snapshots from `buildNirmanaElevationSnapshot()` and typed v2 unavailable snapshots.

- [ ] **Step 1: Add failing raw-label selection tests**

Add snapshot fixtures with:

- two catalogue revisions where only the second has `asset_label_catalogue_accepted`;
- an accepted digest mismatch;
- no accepted catalogue but an `asset_registry.english_name` fallback;
- a missing Sanskrit name and description.

Assert the accepted revision wins, mismatch creates a contradiction, and fallback yields `identity_quality: 'unversioned_fallback'` with explicit missing fields.

- [ ] **Step 2: Add failing v2 snapshot-behavior tests**

Assert:

- `schema_version === '2.0'`;
- all 13 stages are present in order;
- no stage transition receipt means `current_stage === null`;
- layer names match `NIRMANA_LAYER_NAMES`;
- waves remain sorted and contain `eligible_next_asset_ids` derived by Task 4;
- milestone progress matches obligation-specific tests;
- raw evidence still exists but is not required to compute UI layout;
- unavailable evidence returns a typed v2 503 snapshot, not v1.

- [ ] **Step 3: Run focused tests to verify they fail**

```bash
cd platform
npx vitest run src/lib/nirmana-elevation/__tests__/snapshot.test.ts src/app/api/admin/nirmana-elevation/snapshot/__tests__/route.test.ts
```

Expected: FAIL on schema 1.0 and absent label/stage fields.

- [ ] **Step 4: Extend raw evidence loading**

Add `asset_labels` to the raw evidence type and load:

```sql
SELECT campaign_id, definition_revision, catalogue_revision, asset_id,
       sanskrit_name, english_name, description, legacy_aliases,
       source_ref, label_digest, recorded_at
  FROM nirmana_elevation_asset_labels
 WHERE campaign_id = 'nirmana-elevation'
 ORDER BY catalogue_revision, asset_id
```

Add `asset_label_catalogue` to the source list. A missing table before migration application must produce the same explicit unavailable-source behavior as other authoritative sources.

- [ ] **Step 5: Replace coarse snapshot inference with v2 projection**

In `snapshot.ts`:

- select the label catalogue only from the latest valid `asset_label_catalogue_accepted` event;
- call the Task 4 pure functions;
- map every asset to separate identity and milestones;
- use `NIRMANA_LAYER_NAMES` for layer names;
- derive `current_action` and `next_action` from the first current/pending required milestone;
- include stage/layer/asset/audit semantics in the generation digest;
- return `NirmanaElevationSnapshotV2Schema.parse(...)`;
- return a typed v2 unavailable snapshot on `NirmanaElevationSourceError`.

Do not delete the v1 schema; it remains client-readable during rollout.

- [ ] **Step 6: Extend accepted evidence vocabularies safely**

In the evidence route’s asset receipt enum, add `implementation_accepted`. Add a separate campaign-stage receipt schema:

```ts
z.object({
  command: z.literal('record_evidence'),
  campaign_id: campaignId,
  definition_revision: revision,
  idempotency_key: z.string().min(1).max(256),
  event_type: z.literal('stage_transition_accepted'),
  entity_type: z.literal('campaign_stage'),
  entity_id: z.enum(NIRMANA_STAGE_IDS),
  layer: z.enum(['L0', 'L1', 'L2', 'L3', 'L4', 'L5']).nullable(),
  evidence_payload: z.object({
    from_stage: z.enum(NIRMANA_STAGE_IDS).nullable(),
    to_stage: z.enum(NIRMANA_STAGE_IDS),
    prerequisites_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  }).strict(),
  source_kind: z.string().min(1).max(128),
  source_ref: z.string().min(1).max(512),
  observed_at: z.string().datetime(),
})
```

Add route tests proving an invalid transition payload is rejected before the DB write.

Add a separate foundation-lane receipt schema:

```ts
z.object({
  command: z.literal('record_evidence'),
  campaign_id: campaignId,
  definition_revision: revision,
  idempotency_key: z.string().min(1).max(256),
  event_type: z.literal('foundation_lane_accepted'),
  entity_type: z.literal('foundation_lane'),
  entity_id: z.enum(['A', 'B', 'C', 'D', 'E']),
  layer: z.null(),
  evidence_payload: z.object({
    acceptance_sha256: z.string().regex(/^[a-f0-9]{64}$/),
  }).strict(),
  source_kind: z.string().min(1).max(128),
  source_ref: z.string().min(1).max(512),
  observed_at: z.string().datetime(),
})
```

The F0 stage is completed only when lanes A–E each have a valid accepted receipt and the next accepted stage transition leaves F0.

Because all three receipt shapes use `command: 'record_evidence'`, replace the route’s outer
`z.discriminatedUnion('command', ...)` with an ordinary union and keep event-specific validation in
the receipt union:

```ts
const receipt = z.union([assetReceipt, campaignStageReceipt, foundationLaneReceipt])
const command = z.union([definition, freeze, labelCatalogue, receipt])
```

This prevents duplicate discriminator values from making stage or lane receipts unreachable.

- [ ] **Step 7: Run snapshot, route, and evidence tests**

```bash
cd platform
npx vitest run src/lib/nirmana-elevation/__tests__/snapshot.test.ts src/app/api/admin/nirmana-elevation/snapshot/__tests__/route.test.ts src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts
```

Expected: PASS.

- [ ] **Step 8: Commit Task 5**

```bash
git add platform/src/lib/nirmana-elevation/snapshot.ts platform/src/lib/nirmana-elevation/__tests__/snapshot.test.ts platform/src/app/api/admin/nirmana-elevation/snapshot/__tests__/route.test.ts platform/src/app/api/admin/nirmana-elevation/evidence/route.ts platform/src/app/api/admin/nirmana-elevation/evidence/__tests__/route.test.ts
git commit -m "feat(nirmana): project snapshot v2 campaign truth"
```

---

### Task 6: Executive snapshot, vertical campaign spine, and foundation stages

**Files:**
- Create: `platform/src/components/nirmana-elevation/CampaignSnapshotStrip.tsx`
- Create: `platform/src/components/nirmana-elevation/CampaignSpine.tsx`
- Create: `platform/src/components/nirmana-elevation/FoundationStage.tsx`
- Create: `platform/src/components/nirmana-elevation/NowNextRail.tsx`
- Create: `platform/src/components/nirmana-elevation/CampaignSpine.test.tsx`

**Interfaces:**
- Consumes: `NirmanaElevationSnapshotV2`, `NirmanaCampaignStage`, and v2 progress/quality fields.
- Produces: accessible, presentational campaign-summary components with no server derivation logic.

- [ ] **Step 1: Write failing component tests**

Render the Task 3 v2 fixture and assert:

```ts
expect(screen.getByText('L0 · Brahmagyan · Wave 2')).toBeVisible()
expect(screen.getByText('18 / 128')).toBeVisible()
expect(screen.getByText(/3 assets active/i)).toBeVisible()
expect(screen.getByRole('button', { name: /L0 · Brahmagyan/i })).toHaveAttribute('aria-expanded', 'true')
expect(screen.getByRole('button', { name: /L1 · Ganita/i })).toHaveAttribute('aria-expanded', 'false')
expect(screen.getAllByRole('button', { name: /BOOTSTRAP|T0_CENSUS|PLAN_FROZEN|DENOMINATOR_FROZEN|F0_FOUNDATION|L[0-5]|CLOSING|COMPLETE/ })).toHaveLength(13)
```

Also test reconciling denominator copy, unknown current position, keyboard toggle, and F0 lanes with unknown rather than invented percentages.

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd platform
npx vitest run src/components/nirmana-elevation/CampaignSpine.test.tsx
```

Expected: FAIL because the components do not exist.

- [ ] **Step 3: Implement the four focused components**

Use these signatures:

```tsx
export function CampaignSnapshotStrip({ snapshot }: { snapshot: NirmanaElevationSnapshotV2 })
export function CampaignSpine({ snapshot }: { snapshot: NirmanaElevationSnapshotV2 })
export function FoundationStage({ stage, snapshot }: { stage: NirmanaCampaignStage; snapshot: NirmanaElevationSnapshotV2 })
export function NowNextRail({ snapshot }: { snapshot: NirmanaElevationSnapshotV2 })
```

`CampaignSpine` owns only page-session expansion state:

```tsx
const [expanded, setExpanded] = useState<Set<NirmanaStageId>>(
  () => new Set(snapshot.campaign.current_stage ? [snapshot.campaign.current_stage] : []),
)
```

Render each header as a `<button>` with `aria-expanded`, `aria-controls`, exact governed stage name, textual status, and prerequisite when locked. Use existing `brand-*` Tailwind tokens and Lucide line icons already present in the tracker.

- [ ] **Step 4: Run the component test**

```bash
cd platform
npx vitest run src/components/nirmana-elevation/CampaignSpine.test.tsx
```

Expected: PASS.

- [ ] **Step 5: Commit Task 6**

```bash
git add platform/src/components/nirmana-elevation/CampaignSnapshotStrip.tsx platform/src/components/nirmana-elevation/CampaignSpine.tsx platform/src/components/nirmana-elevation/FoundationStage.tsx platform/src/components/nirmana-elevation/NowNextRail.tsx platform/src/components/nirmana-elevation/CampaignSpine.test.tsx
git commit -m "feat(nirmana): add vertical campaign spine"
```

---

### Task 7: Sequential waves, bilingual asset cards, and milestone disclosure

**Files:**
- Create: `platform/src/components/nirmana-elevation/LayerStage.tsx`
- Create: `platform/src/components/nirmana-elevation/WaveLane.tsx`
- Create: `platform/src/components/nirmana-elevation/AssetCard.tsx`
- Create: `platform/src/components/nirmana-elevation/AssetDisclosure.tsx`
- Create: `platform/src/components/nirmana-elevation/MilestoneBar.tsx`
- Create: `platform/src/components/nirmana-elevation/LayerStage.test.tsx`
- Modify: `platform/src/components/nirmana-elevation/CampaignSpine.tsx`

**Interfaces:**
- Consumes: v2 layer/asset/milestone projections only.
- Produces: vertical wave stack, responsive parallel-card layout, bilingual identity, progress, and expanded operational detail.

- [ ] **Step 1: Write failing layer/wave tests**

Assert waves render in numeric order, Wave 2 asset cards are siblings within one labelled group, Wave 3 says which gate locks it, and no asset from a later wave appears under the active-wave heading.

- [ ] **Step 2: Write failing bilingual identity tests**

For `ka_smriti`, assert all of these are independently visible:

```ts
expect(screen.getByText('ka_smriti')).toBeVisible()
expect(screen.getByText('Kala Smriti')).toBeVisible()
expect(screen.getByText('Per-varsha digest')).toBeVisible()
expect(screen.getByText(/year-by-year digest/i)).toBeVisible()
```

For an incomplete identity, assert `Not yet catalogued` appears and no invented Sanskrit name is rendered. For a legacy mapping, assert `Legacy alias` precedes `A22` and the link/action still uses `ka_smriti`.

- [ ] **Step 3: Write failing milestone and disclosure tests**

Assert six visible positions, textual `5 of 6 required milestones`, N/A exclusion from the denominator, current action, next action, dependencies, unlocks, blocker, and producer inheritance. Assert no bare `%` is the only accessible progress text.

- [ ] **Step 4: Run the tests to verify they fail**

```bash
cd platform
npx vitest run src/components/nirmana-elevation/LayerStage.test.tsx
```

Expected: FAIL because the components do not exist.

- [ ] **Step 5: Implement the layer and wave layout**

Use:

```tsx
export function LayerStage({ layer, assets, onOpenAudit }: {
  layer: NirmanaElevationSnapshotV2['layers'][number]
  assets: NirmanaElevationSnapshotV2['assets']
  onOpenAudit: (assetId: string) => void
})

export function WaveLane({ wave, assets, onOpenAudit }: {
  wave: NirmanaElevationSnapshotV2['layers'][number]['waves'][number]
  assets: NirmanaElevationSnapshotV2['assets']
  onOpenAudit: (assetId: string) => void
})
```

`LayerStage` renders `waves.sort((a, b) => a.wave_index - b.wave_index)` as a vertical `space-y-*` stack. `WaveLane` uses `grid gap-3 lg:grid-cols-2 xl:grid-cols-3`; mobile remains one column.

Update `CampaignSpine` to accept `onOpenAudit: (assetId: string) => void` and render `LayerStage`
for stage kinds `layer`; keep T0/F0 routed to `FoundationStage`.

- [ ] **Step 6: Implement bilingual asset cards and disclosure**

Use:

```tsx
export function AssetCard({ asset, onOpenAudit }: { asset: NirmanaElevationSnapshotV2['assets'][number]; onOpenAudit: (assetId: string) => void })
export function AssetDisclosure({ asset, onOpenAudit }: { asset: NirmanaElevationSnapshotV2['assets'][number]; onOpenAudit: (assetId: string) => void })
export function MilestoneBar({ asset }: { asset: NirmanaElevationSnapshotV2['assets'][number] })
```

Identity order is canonical ID → Sanskrit name or missing state → English name or missing state → description or missing state. Render six milestone segments with `aria-label` containing each label and state, followed by textual earned/required progress. Render N/A with a muted hatched class and `not applicable` text, not as an earned segment. The asset-level `Audit details` button calls `onOpenAudit(asset.asset_id)`.

- [ ] **Step 7: Run the focused tests**

```bash
cd platform
npx vitest run src/components/nirmana-elevation/LayerStage.test.tsx
```

Expected: PASS.

- [ ] **Step 8: Commit Task 7**

```bash
git add platform/src/components/nirmana-elevation/LayerStage.tsx platform/src/components/nirmana-elevation/WaveLane.tsx platform/src/components/nirmana-elevation/AssetCard.tsx platform/src/components/nirmana-elevation/AssetDisclosure.tsx platform/src/components/nirmana-elevation/MilestoneBar.tsx platform/src/components/nirmana-elevation/LayerStage.test.tsx platform/src/components/nirmana-elevation/CampaignSpine.tsx
git commit -m "feat(nirmana): add wave and asset progress explorer"
```

---

### Task 8: Assemble tracker v2, audit drawer, v1 fallback, and stale-state retention

**Files:**
- Create: `platform/src/components/nirmana-elevation/AuditDrawer.tsx`
- Create: `platform/src/components/nirmana-elevation/NirmanaElevationTrackerV1.tsx`
- Modify: `platform/src/components/nirmana-elevation/NirmanaElevationTracker.tsx`
- Modify: `platform/src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx`

**Interfaces:**
- Consumes: all Tasks 3, 6, and 7 components/types.
- Produces: `NirmanaElevationTrackerView`, the complete route UI with v1 compatibility, and last-valid-v2 failure behavior.

- [ ] **Step 1: Preserve the current v1 view behind an explicit component**

Move the existing v1 rendering sections—not fetch/poll logic—into:

```tsx
export function NirmanaElevationTrackerV1({ snapshot, fetchedAt }: {
  snapshot: NirmanaElevationSnapshotV1
  fetchedAt: Date
})
```

Add a visible banner: `Tracker upgrade pending — showing schema v1 evidence view.` This component is temporary compatibility code and receives no new features.

- [ ] **Step 2: Rewrite tracker tests around v2 first**

Replace the primary fixture with Task 3’s v2 fixture. Assert:

- executive snapshot, campaign spine, Now/Next rail, expanded current layer, bilingual asset, and closed Audit drawer render;
- horizontal `Sequential layer rail` and default `Asset evidence ledger` headings do not render in v2;
- v1 payload selects the temporary v1 component;
- malformed v2 is unavailable;
- after one valid v2 response, a 503 or malformed response retains the last v2 DOM and shows `Current state unknown` with the error;
- focus/reconnect and newest-request-wins behavior remain.

- [ ] **Step 3: Run tracker tests to verify they fail**

```bash
cd platform
npx vitest run src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx
```

Expected: FAIL against the current monolithic v1 renderer.

- [ ] **Step 4: Implement the audit drawer**

Use:

```tsx
export function AuditDrawer({ snapshot, assetId, open, onOpenChange }: {
  snapshot: NirmanaElevationSnapshotV2
  assetId: string | null
  open: boolean
  onOpenChange: (open: boolean) => void
})
```

The closed trigger names evidence count and data-quality verdict. The expanded drawer contains source provenance, observation times, release main/deployed/revision values, contradictions, and evidence refs filtered to `assetId` when supplied. It is read-only and uses a labelled `<dialog>` or accessible disclosure pattern already supported by the app.

- [ ] **Step 5: Assemble v2 in the top-level tracker**

Create a pure view boundary:

```tsx
export function NirmanaElevationTrackerView({ snapshot, fetchedAt }: {
  snapshot: NirmanaElevationSnapshot
  fetchedAt: Date
}) {
  if (snapshot.schema_version === '1.0') {
    return <NirmanaElevationTrackerV1 snapshot={snapshot} fetchedAt={fetchedAt} />
  }
  return <NirmanaElevationTrackerV2View snapshot={snapshot} />
}

function NirmanaElevationTrackerV2View({ snapshot }: { snapshot: NirmanaElevationSnapshotV2 }) {
  const [auditAssetId, setAuditAssetId] = useState<string | null>(null)
  const [auditOpen, setAuditOpen] = useState(false)
  const openAudit = (assetId: string) => {
    setAuditAssetId(assetId)
    setAuditOpen(true)
  }
  return (
    <main className="space-y-4">
      <CampaignSnapshotStrip snapshot={snapshot} />
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_18rem]">
        <CampaignSpine snapshot={snapshot} onOpenAudit={openAudit} />
        <NowNextRail snapshot={snapshot} />
      </div>
      <AuditDrawer snapshot={snapshot} assetId={auditAssetId} open={auditOpen} onOpenChange={setAuditOpen} />
    </main>
  )
}
```

Keep the existing polling constants, abort controller, visibility behavior, reconnect/focus refresh, backoff, and last-valid snapshot state. After union parsing, pass the last valid snapshot to `NirmanaElevationTrackerView`.

The failure overlay must sit above the retained last-valid view and state its failure time. It must never clear the snapshot merely because one poll failed.

- [ ] **Step 6: Run tracker and component tests**

```bash
cd platform
npx vitest run src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx src/components/nirmana-elevation/CampaignSpine.test.tsx src/components/nirmana-elevation/LayerStage.test.tsx
```

Expected: PASS.

- [ ] **Step 7: Commit Task 8**

```bash
git add platform/src/components/nirmana-elevation/AuditDrawer.tsx platform/src/components/nirmana-elevation/NirmanaElevationTrackerV1.tsx platform/src/components/nirmana-elevation/NirmanaElevationTracker.tsx platform/src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx
git commit -m "feat(nirmana): assemble campaign spine tracker"
```

---

### Task 9: Accessibility, responsive contracts, and complete local verification

**Files:**
- Create: `platform/src/components/nirmana-elevation/NirmanaElevationTracker.a11y.test.tsx`
- Modify only if a failing check proves necessary: files created or modified in Tasks 2–8.

**Interfaces:**
- Consumes: real v2 tracker and fixture.
- Produces: executable WCAG and responsive structural gates plus a clean repository verification record.

- [ ] **Step 1: Write the real axe test and demonstrate-can-fail control**

Create a jsdom test using `axe-core`:

```ts
import axe from 'axe-core'
import { render } from '@testing-library/react'

it('is axe-clean with the current layer and asset expanded', async () => {
  const { container } = render(
    <NirmanaElevationTrackerView snapshot={fixtureV2} fetchedAt={new Date('2026-08-25T09:00:00Z')} />,
  )
  const results = await axe.run(container, {
    runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
  })
  expect(results.violations.map(({ id }) => id)).toEqual([])
})

it('demonstrates that axe detects an unnamed control', async () => {
  const { container } = render(<button />)
  const results = await axe.run(container)
  expect(results.violations.map(({ id }) => id)).toContain('button-name')
})
```

- [ ] **Step 2: Add structural responsive assertions**

Assert WaveLane’s container has one-column base layout and desktop multi-column classes, the Now/Next rail has no fixed mobile width, names use wrapping rather than truncation, and no tracker component introduces `overflow-x-auto` for the operational canvas. The Audit drawer may scroll internally for raw evidence.

- [ ] **Step 3: Run the accessibility and focused suites**

```bash
cd platform
npx vitest run src/components/nirmana-elevation/NirmanaElevationTracker.a11y.test.tsx src/components/nirmana-elevation/NirmanaElevationTracker.test.tsx src/components/nirmana-elevation/CampaignSpine.test.tsx src/components/nirmana-elevation/LayerStage.test.tsx src/lib/nirmana-elevation/__tests__ src/app/api/admin/nirmana-elevation
```

Expected: PASS.

- [ ] **Step 4: Run scoped lint and type checking**

```bash
cd platform
npx eslint src/components/nirmana-elevation src/lib/nirmana-elevation src/app/api/admin/nirmana-elevation tests/unit/migrations/nirmana_elevation_asset_labels.test.ts
npx tsc --noEmit
```

Expected: PASS.

- [ ] **Step 5: Run full release-proportional local gates**

```bash
cd platform
npm run guard:migration-numbers
npm test
npm run lint
npm run build
```

Expected: PASS. If a full gate fails, first run the same command on current `origin/main` in a separate clean worktree. Fix only regressions introduced by this feature; record unrelated baseline failures without broad cleanup.

- [ ] **Step 6: Review the final diff against the approved spec**

Run:

```bash
git diff --check origin/main...HEAD
git diff --stat origin/main...HEAD
git status --short
```

Expected: no whitespace errors, only planned files changed, and a clean worktree after the next commit.

- [ ] **Step 7: Commit Task 9**

```bash
git add platform/src/components/nirmana-elevation/NirmanaElevationTracker.a11y.test.tsx
git commit -m "test(nirmana): gate tracker accessibility and layout"
```

---

### Task 10: Independent review, protected PR, deployment, and live verification

**Files:**
- Modify only if review finds a feature regression: files already in this plan.
- Do not create production evidence, backfill campaign stages, or start Nirmāṇa execution as part of this task.

**Interfaces:**
- Consumes: completed branch, CI, migration workflow, Cloud Run deployment, and public route.
- Produces: merged protected change, applied migration, deployed `amjis-web` revision, public route proof, and a clearly bounded authenticated-smoke handoff.

- [ ] **Step 1: Rebase and rerun changed-area gates**

```bash
git fetch origin --prune
git rebase origin/main
cd platform
npm run guard:migration-numbers
npx vitest run src/components/nirmana-elevation src/lib/nirmana-elevation/__tests__ src/app/api/admin/nirmana-elevation tests/unit/migrations/nirmana_elevation_asset_labels.test.ts
npx eslint src/components/nirmana-elevation src/lib/nirmana-elevation src/app/api/admin/nirmana-elevation tests/unit/migrations/nirmana_elevation_asset_labels.test.ts
npx tsc --noEmit
```

Expected: PASS after rebase.

- [ ] **Step 2: Obtain independent code, migration, and security review**

Review must explicitly check:

- migration idempotency, append-only trigger, FK, number uniqueness, and rollback implications;
- label transaction conflict/idempotency behavior;
- no campaign-state inference or historical A1–A22 execution revival;
- stage and milestone detectors measure the claimed state;
- authorization and audit payloads;
- no secret-bearing errors;
- keyboard, text-equivalent, and mobile behavior.

Resolve findings with failing tests first and separate commits.

- [ ] **Step 3: Push and open the protected PR**

Use the repository `pr-description` skill, then:

```bash
git push -u origin HEAD
gh pr create --base main --title "feat(nirmana): redesign elevation tracker as campaign spine" --body "Summary: vertical governed campaign spine, snapshot v2, bilingual asset identities, obligation-aware progress, and secondary audit detail. Includes append-only migration 598. No campaign execution or evidence backfill. Verification evidence is listed in the commits and PR checks."
```

- [ ] **Step 4: Monitor required checks and stop on an exact failure**

```bash
gh pr checks --watch --fail-fast
```

Expected: all required checks pass. If any required check fails, report the exact workflow/job and do not merge until the feature-caused failure is repaired and rerun.

- [ ] **Step 5: Enter the protected merge queue**

```bash
gh pr merge --auto --squash
```

Expected: PR enters the configured merge queue; no direct-main write or branch-protection bypass.

- [ ] **Step 6: Monitor post-merge CI and Deploy to Cloud Run**

```bash
gh run list --branch main --limit 10
```

Identify the runs triggered by the merge commit, then use `gh run watch` from the run list. Confirm both:

- CI completes successfully;
- Deploy to Cloud Run completes the `migrate` job before `deploy-web`, and `amjis-web` receives a Ready serving revision.

If any required job fails, report the exact job and stop. A green workflow alone is not deployment proof.

- [ ] **Step 7: Verify public reachability without credentials**

Run:

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://amjis-web-938361928218.asia-south1.run.app/admin/nirmana-elevation
curl -sS -o /dev/null -w '%{http_code}\n' https://amjis-web-938361928218.asia-south1.run.app/api/admin/nirmana-elevation/snapshot
```

Expected: the page route responds with the application’s normal auth redirect or page response; the snapshot API rejects unauthenticated access rather than returning tracker data.

- [ ] **Step 8: Perform the authorized human super-admin smoke test**

An authorized super-admin, using their existing browser session, verifies:

- snapshot v2 loads;
- exact 13-stage vertical spine;
- current stage expands by default;
- `L0 · Brahmagyan` through `L5 · Mimamsa` labels;
- waves vertical, parallel assets grouped within one wave;
- canonical ID + Sanskrit + English/description or honest missing state;
- milestone N/A handling and textual progress;
- Now/Next/Then and blocker information;
- Audit drawer closed by default and opens on demand;
- stale/error overlay retains last valid data;
- phone-width layout remains usable.

No credential is copied into logs, terminal output, screenshots, or chat.

- [ ] **Step 9: Report the release boundary honestly**

Report merge commit, CI run, deploy run, migration job result, serving revision, public route result, and human authenticated smoke outcome. Do not claim the tracker release complete until all are verified. Do not backfill stage receipts or resume Nirmāṇa as part of tracker release closure.

---

## Plan completion checklist

- [ ] All ten tasks landed in order with focused tests and reviewable commits.
- [ ] Migration number remains unique after final rebase.
- [ ] Snapshot v2 is evidence-derived and backward-compatible during rollout.
- [ ] Operational UI matches the approved campaign-spine hierarchy.
- [ ] Raw evidence is secondary but reachable.
- [ ] Scoped and full gates pass or unrelated baseline failures are independently proven.
- [ ] Protected merge, migration, Cloud Run serving revision, public reachability, and authorized authenticated smoke are all evidenced.
- [ ] No campaign execution, evidence backfill, credential exposure, or direct production mutation occurred outside the approved release workflow.
