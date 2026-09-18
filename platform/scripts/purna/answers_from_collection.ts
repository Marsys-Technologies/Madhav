import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import {
  casesForSuite,
  validateAcceptanceAnswers,
  validateProtocol,
  type AcceptanceAnswer,
  type AcceptanceCaseInput,
  type AcceptanceSuite,
  type DeterministicEvidence,
} from './acceptance_cases'
import {
  assertLiveEvidence,
  PURNA_ACCOUNTABLE_ANSWERS_VERSION,
  validateCollectionArtifact,
  type AcceptanceDoor,
  type CollectedCase,
  type CollectionArtifact,
  type CollectionProvenance,
} from './collection_types'
import { stableFingerprint } from '../../src/lib/retrieval/registry/knowledge/stable'

function evidence(gate_id: string, passed: boolean, receipt_ref: string | null, detail?: string): DeterministicEvidence {
  return { gate_id, passed, receipt_ref, ...(detail ? { detail } : {}) }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function accountabilityEvidence(row: CollectedCase): DeterministicEvidence {
  if (!isObject(row.responseAccountability)) {
    return evidence('response_accountability', false, null, 'RESPONSE_ACCOUNTABILITY_ENVELOPE_MISSING')
  }
  return evidence('response_accountability', true, `response_accountability:${stableFingerprint(row.responseAccountability)}`)
}

function gateEvidence(
  input: AcceptanceCaseInput,
  row: CollectedCase,
  collection: CollectionArtifact,
): readonly DeterministicEvidence[] {
  const delivered = new Set(row.deliveredFactIds)
  const allMaterialDelivered = row.materialFactIds.every((factId) => delivered.has(factId))
  const collectionReceipt = {
    collection_hash: collection.collection_hash,
    collection_manifest_hash: collection.manifest_hash,
    door: row.door,
    row_hash: stableFingerprint(row),
  }
  return input.deterministic_gates.map((gate): DeterministicEvidence => {
    if (gate === 'immutable_case_input') {
      return evidence(gate, true, stableFingerprint({
        gate_id: gate,
        ...collectionReceipt,
        case_input: input,
      }))
    }
    if (gate === 'source_acceptance_denominator') {
      return evidence(gate, true, stableFingerprint({
        gate_id: gate,
        ...collectionReceipt,
        case_id: input.case_id,
        required_dimensions: input.required_dimensions,
        expected: input.expected,
      }))
    }
    if (gate === 'inquiry_closure_receipt') {
      const receipt = row.receiptRefs[0] ?? null
      return evidence(gate, row.terminal === 'complete' && row.observedRevision === row.expectedRevision && receipt !== null, receipt,
        row.terminal === 'complete' && row.observedRevision === row.expectedRevision && receipt !== null ? undefined : 'COMPLETE_REVISION_BOUND_CLOSURE_RECEIPT_REQUIRED')
    }
    if (gate === 'response_accountability') return accountabilityEvidence(row)
    if (gate === 'citation_resolution') {
      return evidence(gate, row.materialFactIds.length > 0 && allMaterialDelivered, row.receiptRefs[0] ?? null,
        row.materialFactIds.length > 0 && allMaterialDelivered ? undefined : 'MATERIAL_FACT_DELIVERY_RECEIPT_INCOMPLETE')
    }
    // Collection intentionally has no heuristic substitute for these semantic
    // receipts. A door must expose typed proof before this bridge can pass it.
    return evidence(gate, false, null, `CHANNEL_${gate.toUpperCase()}_RECEIPT_UNAVAILABLE`)
  })
}

/**
 * Convert exactly one actual channel arm into the answer-input shape consumed
 * by the independent judge and acceptance runner. Duplicate/missing rows are
 * rejected; unsupported evidence remains an explicit failed deterministic gate.
 */
export function answersFromCollection(args: {
  readonly inputs: readonly AcceptanceCaseInput[]
  readonly door: AcceptanceDoor
  readonly collection: CollectionArtifact
}): readonly AcceptanceAnswer[] {
  const collection = validateCollectionArtifact(args.collection)
  if (stableFingerprint(collection.manifest.case_inputs) !== stableFingerprint(args.inputs)) {
    throw new Error('PURNA_COLLECTION_CASE_INPUT_MISMATCH')
  }
  const byCase = new Map<string, CollectedCase>()
  for (const row of collection.rows.filter((candidate) => candidate.door === args.door)) {
    if (byCase.has(row.caseId)) throw new Error('PURNA_COLLECTION_DUPLICATE_DOOR_CASE')
    byCase.set(row.caseId, row)
  }
  return args.inputs.map((input): AcceptanceAnswer => {
    const row = byCase.get(input.case_id)
    if (!row) throw new Error('PURNA_COLLECTION_DOOR_CASE_MISSING')
    assertLiveEvidence(row)
    return {
      case_id: input.case_id,
      answer: row.answer || null,
      evidence: gateEvidence(input, row, collection),
      response_accountability: row.responseAccountability as AcceptanceAnswer['response_accountability'],
    }
  })
}

export interface AccountableAnswersArtifact {
  readonly schema_version: typeof PURNA_ACCOUNTABLE_ANSWERS_VERSION
  readonly provenance: CollectionProvenance
  readonly assessment?: {
    readonly approval_id: string
    readonly assessor: 'independent_eval_judge'
    readonly model_id: string
  }
  readonly answers: readonly AcceptanceAnswer[]
}

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export function accountableAnswersHash(
  answers: readonly AcceptanceAnswer[],
  collectionHash: string,
  door: AcceptanceDoor,
): string {
  return stableFingerprint({
    collection_hash: collectionHash,
    door,
    answers: answers.map((answer) => ({
      case_id: answer.case_id,
      answer: answer.answer,
      evidence: answer.evidence,
      response_accountability: answer.response_accountability ?? null,
    })),
  })
}

export function createAccountableAnswersArtifact(args: {
  readonly inputs: readonly AcceptanceCaseInput[]
  readonly door: AcceptanceDoor
  readonly collection: CollectionArtifact
  readonly collectionArtifact: string
}): AccountableAnswersArtifact {
  const collection = validateCollectionArtifact(args.collection)
  const answers = answersFromCollection({ inputs: args.inputs, door: args.door, collection })
  return {
    schema_version: PURNA_ACCOUNTABLE_ANSWERS_VERSION,
    provenance: {
      collection_artifact: resolve(args.collectionArtifact),
      collection_hash: collection.collection_hash,
      collection_manifest_hash: collection.manifest_hash,
      suite: collection.manifest.suite,
      door: args.door,
      environment: collection.manifest.environment,
      expected_revision: collection.manifest.expected_revision,
      authorization_approval_id: collection.manifest.authorization_approval_id,
      accountable_answers_hash: accountableAnswersHash(answers, collection.collection_hash, args.door),
    },
    answers,
  }
}

export function validateAccountableAnswersArtifact(
  value: unknown,
  inputs: readonly AcceptanceCaseInput[],
): AccountableAnswersArtifact {
  if (!object(value) || value.schema_version !== PURNA_ACCOUNTABLE_ANSWERS_VERSION
    || !object(value.provenance) || !Array.isArray(value.answers)) {
    throw new Error('PURNA_ACCOUNTABLE_ANSWERS_INVALID')
  }
  const provenance = value.provenance
  const exactProvenanceKeys = [
    'collection_artifact', 'collection_hash', 'collection_manifest_hash', 'suite', 'door', 'environment',
    'expected_revision', 'authorization_approval_id', 'accountable_answers_hash',
  ]
  const allowedTopLevelKeys = value.assessment === undefined
    ? ['schema_version', 'provenance', 'answers']
    : ['schema_version', 'provenance', 'assessment', 'answers']
  const validAssessment = value.assessment === undefined || (object(value.assessment)
    && Object.keys(value.assessment).length === 3
    && Object.keys(value.assessment).every((key) => ['approval_id', 'assessor', 'model_id'].includes(key))
    && typeof value.assessment.approval_id === 'string' && value.assessment.approval_id.length > 0
    && value.assessment.assessor === 'independent_eval_judge'
    && typeof value.assessment.model_id === 'string' && value.assessment.model_id.length > 0)
  if (Object.keys(value).length !== allowedTopLevelKeys.length
    || Object.keys(value).some((key) => !allowedTopLevelKeys.includes(key))
    || !validAssessment
    || Object.keys(provenance).length !== exactProvenanceKeys.length
    || Object.keys(provenance).some((key) => !exactProvenanceKeys.includes(key))
    || typeof provenance.collection_artifact !== 'string' || provenance.collection_artifact.length === 0
    || typeof provenance.collection_hash !== 'string' || !/^sha256:[a-f0-9]{64}$/.test(provenance.collection_hash)
    || typeof provenance.collection_manifest_hash !== 'string' || !/^sha256:[a-f0-9]{64}$/.test(provenance.collection_manifest_hash)
    || (provenance.suite !== 'beyond_acarya' && provenance.suite !== 'product')
    || (provenance.door !== 'portal' && provenance.door !== 'managed_mcp' && provenance.door !== 'raw_mcp')
    || (provenance.environment !== 'candidate' && provenance.environment !== 'live')
    || typeof provenance.expected_revision !== 'string' || provenance.expected_revision.length === 0
    || typeof provenance.authorization_approval_id !== 'string' || provenance.authorization_approval_id.length === 0
    || typeof provenance.accountable_answers_hash !== 'string' || !/^sha256:[a-f0-9]{64}$/.test(provenance.accountable_answers_hash)) {
    throw new Error('PURNA_ACCOUNTABLE_ANSWERS_INVALID')
  }
  const answers = validateAcceptanceAnswers(value.answers, inputs)
  if (accountableAnswersHash(
    answers,
    provenance.collection_hash as string,
    provenance.door as AcceptanceDoor,
  ) !== provenance.accountable_answers_hash) {
    throw new Error('PURNA_ACCOUNTABLE_ANSWERS_HASH_MISMATCH')
  }
  return {
    schema_version: PURNA_ACCOUNTABLE_ANSWERS_VERSION,
    provenance: provenance as unknown as CollectionProvenance,
    ...(value.assessment === undefined ? {} : { assessment: value.assessment as AccountableAnswersArtifact['assessment'] }),
    answers,
  }
}

function parseCliArgs(argv: readonly string[]): {
  suite: AcceptanceSuite
  door: AcceptanceDoor
  collectionPath: string
  artifactDir: string
} {
  const values = new Map<string, string>()
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index]; const value = argv[index + 1]
    if (!flag?.startsWith('--') || value === undefined || values.has(flag)) throw new Error('PURNA_ANSWERS_CLI_INVALID')
    values.set(flag, value)
  }
  if ([...values.keys()].some((flag) => !['--suite', '--door', '--collection', '--artifact-dir'].includes(flag))) {
    throw new Error('PURNA_ANSWERS_CLI_INVALID')
  }
  const suite = values.get('--suite'); const door = values.get('--door')
  const collectionPath = values.get('--collection'); const artifactDir = values.get('--artifact-dir')
  if ((suite !== 'beyond_acarya' && suite !== 'product')
    || (door !== 'portal' && door !== 'managed_mcp' && door !== 'raw_mcp')
    || !collectionPath || !artifactDir) throw new Error('PURNA_ANSWERS_CLI_REQUIRED_ARGUMENT_MISSING')
  return { suite, door, collectionPath, artifactDir }
}

export async function main(argv = process.argv.slice(2)): Promise<void> {
  const args = parseCliArgs(argv)
  const protocolPath = new URL('../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PRODUCT_ACCEPTANCE_PROTOCOL_v2.json', import.meta.url)
  const [protocolValue, collectionValue] = await Promise.all([
    readFile(protocolPath, 'utf8'), readFile(args.collectionPath, 'utf8'),
  ])
  const protocol = validateProtocol(JSON.parse(protocolValue))
  const collection = validateCollectionArtifact(JSON.parse(collectionValue))
  if (collection.manifest.suite !== args.suite) throw new Error('PURNA_COLLECTION_SUITE_MISMATCH')
  const canonicalById = new Map(casesForSuite(protocol, args.suite).map((input) => [input.case_id, input]))
  const inputs = collection.manifest.case_inputs.map((input) => canonicalById.get(input.case_id))
  if (inputs.some((input) => input === undefined)) throw new Error('PURNA_COLLECTION_CASE_INPUT_MISMATCH')
  const artifact = createAccountableAnswersArtifact({
    inputs: inputs as readonly AcceptanceCaseInput[],
    door: args.door,
    collection,
    collectionArtifact: args.collectionPath,
  })
  const directory = resolve(args.artifactDir)
  await mkdir(directory, { recursive: true })
  const suffix = collection.collection_hash.replace(/^sha256:/, '').slice(0, 16)
  const path = resolve(directory, `accountable-answers-${args.door}-${suffix}.json`)
  await writeFile(path, `${JSON.stringify(artifact, null, 2)}\n`, { flag: 'wx' })
  process.stdout.write(`${JSON.stringify({ artifact: path, door: args.door, answers: artifact.answers.length, accountable_answers_hash: artifact.provenance.accountable_answers_hash })}\n`)
}

if (import.meta.url === `file://${process.argv[1]}`) main().catch((error: unknown) => {
  process.stderr.write(`${error instanceof Error ? error.message : 'PURNA_ANSWERS_FAILED'}\n`)
  process.exitCode = 1
})
