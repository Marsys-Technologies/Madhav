import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { randomUUID } from 'node:crypto'
import {
  PRODUCT_ACCEPTANCE_RUN_VERSION,
  casesForSuite,
  type AcceptanceAnswer,
  type AcceptanceEnvironment,
  type AcceptanceSuite,
  type ApprovedEnvironmentConfig,
  validateAcceptanceAnswers,
  validateEnvironmentConfig,
  validateProtocol,
} from './acceptance_cases'
import { scoreAnswers, type AcceptanceFailure, type CaseScore } from './score_answers'
import {
  accountableAnswersHash,
  answersFromCollection,
  validateAccountableAnswersArtifact,
  type AccountableAnswersArtifact,
} from './answers_from_collection'
import { validateCollectionArtifact, type AcceptanceDoor } from './collection_types'

export type AcceptanceInputFile = AccountableAnswersArtifact

export interface AcceptanceRunRecord {
  readonly schema_version: typeof PRODUCT_ACCEPTANCE_RUN_VERSION
  readonly run_id: string
  readonly created_at: string
  readonly protocol_version: string
  readonly suite: AcceptanceSuite
  readonly environment: AcceptanceEnvironment
  readonly revision: string
  readonly door: AcceptanceDoor
  readonly collection_artifact: string
  readonly collection_hash: string
  readonly collection_manifest_hash: string
  readonly accountable_answers_hash: string
  readonly judge_approval_id: string
  readonly judge_assessor: 'independent_eval_judge'
  readonly judge_model_id: string
  readonly judged_artifact_hash: string
  readonly environment_config: Pick<ApprovedEnvironmentConfig, 'schema_version' | 'environment' | 'chart_id' | 'portal_url' | 'mcp_url' | 'revision' | 'authorization' | 'judge_authority' | 'evidence_mode'>
  readonly case_inputs: readonly unknown[]
  readonly evidence: readonly unknown[]
  readonly answers: readonly AcceptanceAnswer[]
  readonly case_verdicts: readonly CaseScore[]
  readonly failures: readonly AcceptanceFailure[]
  readonly verdict: string
  readonly evidence_kind: 'candidate_or_live' | 'fixture'
  /** Network calls evidenced by the collection rows judged for this door. */
  readonly network_calls_made: number
}

function object(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

function assertNoSecrets(value: unknown): void {
  if (Array.isArray(value)) return value.forEach(assertNoSecrets)
  if (!object(value)) return
  for (const [key, child] of Object.entries(value)) {
    if (/(token|secret|password|api[_-]?key|authorization_value|credential)/i.test(key)) {
      throw new Error('PRODUCT_ACCEPTANCE_SECRET_CONFIG_FORBIDDEN')
    }
    if (typeof child === 'string' && /^bearer\s+/i.test(child)) {
      throw new Error('PRODUCT_ACCEPTANCE_SECRET_CONFIG_FORBIDDEN')
    }
    assertNoSecrets(child)
  }
}

export function parseCliArgs(argv: readonly string[]): {
  suite: AcceptanceSuite
  environment: AcceptanceEnvironment
  configPath: string
  inputPath: string
  artifactDir: string
} {
  const values = new Map<string, string>()
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index]
    const value = argv[index + 1]
    if (!flag?.startsWith('--') || value === undefined || values.has(flag)) throw new Error('PRODUCT_ACCEPTANCE_CLI_INVALID')
    values.set(flag, value)
  }
  const allowed = new Set(['--suite', '--environment', '--config', '--input', '--artifact-dir'])
  if ([...values.keys()].some((flag) => !allowed.has(flag))) throw new Error('PRODUCT_ACCEPTANCE_CLI_INVALID')
  const suite = values.get('--suite')
  const environment = values.get('--environment')
  const configPath = values.get('--config')
  const inputPath = values.get('--input')
  const artifactDir = values.get('--artifact-dir')
  if ((suite !== 'beyond_acarya' && suite !== 'product')
    || (environment !== 'candidate' && environment !== 'live')
    || !configPath || !inputPath || !artifactDir) throw new Error('PRODUCT_ACCEPTANCE_CLI_REQUIRED_ARGUMENT_MISSING')
  return { suite, environment, configPath, inputPath, artifactDir }
}

async function readJson(path: string): Promise<unknown> {
  try { return JSON.parse(await readFile(path, 'utf8')) } catch { throw new Error('PRODUCT_ACCEPTANCE_JSON_INVALID') }
}

function assertSafeArtifactDirectory(path: string): string {
  const directory = resolve(path)
  if (directory === '/' || /(^|\/)\.env(?:\.|$)/.test(directory)) throw new Error('PRODUCT_ACCEPTANCE_ARTIFACT_DIR_INVALID')
  return directory
}

export async function writeAcceptanceRun(args: {
  protocol: unknown
  suite: AcceptanceSuite
  environment: AcceptanceEnvironment
  environmentConfig: unknown
  input: unknown
  artifactDir: string
  now?: Date
  runId?: string
}): Promise<{ record: AcceptanceRunRecord; path: string }> {
  assertNoSecrets(args.environmentConfig)
  assertNoSecrets(args.input)
  const protocol = validateProtocol(args.protocol)
  const config = validateEnvironmentConfig(args.environmentConfig, args.environment)
  const inputs = casesForSuite(protocol, args.suite)
  const input = validateAccountableAnswersArtifact(args.input, inputs)
  if (!input.assessment) throw new Error('PRODUCT_ACCEPTANCE_JUDGED_ARTIFACT_REQUIRED')
  if (input.assessment.approval_id !== config.judge_authority.approval_id
    || input.assessment.model_id !== config.judge_authority.model_id
    || input.assessment.judged_artifact_hash !== config.judge_authority.judged_artifact_hash) {
    throw new Error('PRODUCT_ACCEPTANCE_JUDGE_AUTHORITY_MISMATCH')
  }
  if (input.provenance.suite !== args.suite
    || input.provenance.environment !== args.environment
    || input.provenance.expected_revision !== config.revision
    || input.provenance.authorization_approval_id !== config.authorization.approval_id
    || resolve(input.provenance.collection_artifact) !== input.provenance.collection_artifact) {
    throw new Error('PRODUCT_ACCEPTANCE_COLLECTION_PROVENANCE_MISMATCH')
  }
  let collectionValue: unknown
  try { collectionValue = JSON.parse(await readFile(input.provenance.collection_artifact, 'utf8')) } catch {
    throw new Error('PRODUCT_ACCEPTANCE_COLLECTION_ARTIFACT_INVALID')
  }
  const collection = validateCollectionArtifact(collectionValue)
  if (collection.collection_hash !== input.provenance.collection_hash
    || collection.manifest_hash !== input.provenance.collection_manifest_hash
    || collection.manifest.suite !== args.suite
    || collection.manifest.environment !== args.environment
    || collection.manifest.expected_revision !== config.revision
    || collection.manifest.authorization_approval_id !== config.authorization.approval_id) {
    throw new Error('PRODUCT_ACCEPTANCE_COLLECTION_PROVENANCE_MISMATCH')
  }
  if (collection.manifest.target.chart_id !== config.chart_id
    || collection.manifest.target.portal_url !== config.portal_url
    || collection.manifest.target.mcp_url !== config.mcp_url) {
    throw new Error('PRODUCT_ACCEPTANCE_COLLECTION_TARGET_MISMATCH')
  }
  const canonicalInputsById = new Map(inputs.map((caseInput) => [caseInput.case_id, caseInput]))
  const collectedInputs = collection.manifest.case_inputs.map((caseInput) => canonicalInputsById.get(caseInput.case_id))
  if (collectedInputs.some((caseInput) => caseInput === undefined)) {
    throw new Error('PRODUCT_ACCEPTANCE_COLLECTION_PROVENANCE_MISMATCH')
  }
  const derivedAnswers = answersFromCollection({
    inputs: collectedInputs as typeof inputs,
    door: input.provenance.door,
    collection,
  })
  if (accountableAnswersHash(
    derivedAnswers, collection.collection_hash, input.provenance.door,
  ) !== input.provenance.accountable_answers_hash) {
    throw new Error('PRODUCT_ACCEPTANCE_COLLECTION_ANSWER_MISMATCH')
  }
  const answers = validateAcceptanceAnswers(input.answers, inputs)
  if (accountableAnswersHash(answers, collection.collection_hash, input.provenance.door)
    !== accountableAnswersHash(derivedAnswers, collection.collection_hash, input.provenance.door)) {
    throw new Error('PRODUCT_ACCEPTANCE_COLLECTION_ANSWER_MISMATCH')
  }
  const score = scoreAnswers(inputs, answers)
  const fixture = config.evidence_mode === 'fixture'
  // The acceptance runner is offline, but its verdict is bound to one door's
  // live collection. Preserve that door's observed network-work total instead
  // of writing a false zero into the durable acceptance record.
  const networkCallsMade = collection.rows
    .filter((row) => row.door === input.provenance.door)
    .reduce((total, row) => total + row.networkCallCount, 0)
  const createdAt = (args.now ?? new Date()).toISOString()
  const record: AcceptanceRunRecord = {
    schema_version: PRODUCT_ACCEPTANCE_RUN_VERSION,
    run_id: args.runId ?? randomUUID(),
    created_at: createdAt,
    protocol_version: protocol.protocol_version,
    suite: args.suite,
    environment: args.environment,
    revision: config.revision,
    door: input.provenance.door,
    collection_artifact: input.provenance.collection_artifact,
    collection_hash: input.provenance.collection_hash,
    collection_manifest_hash: input.provenance.collection_manifest_hash,
    accountable_answers_hash: input.provenance.accountable_answers_hash,
    judge_approval_id: input.assessment.approval_id,
    judge_assessor: input.assessment.assessor,
    judge_model_id: input.assessment.model_id,
    judged_artifact_hash: input.assessment.judged_artifact_hash,
    environment_config: config,
    case_inputs: inputs,
    evidence: answers.flatMap((answer) => answer.evidence.map((evidence) => ({ case_id: answer.case_id, ...evidence }))),
    answers,
    case_verdicts: score.cases,
    failures: score.failures,
    // Fixture evidence may exercise the runner but is never accepted as a
    // candidate/live product result, regardless of qualitative score.
    verdict: fixture ? 'NOT_LIVE_EVIDENCE' : score.verdict,
    evidence_kind: fixture ? 'fixture' : 'candidate_or_live',
    network_calls_made: networkCallsMade,
  }
  const directory = assertSafeArtifactDirectory(args.artifactDir)
  await mkdir(directory, { recursive: true })
  const path = resolve(directory, `purna-product-acceptance-${record.created_at.replace(/[:.]/g, '-')}-${record.run_id}.json`)
  await writeFile(path, `${JSON.stringify(record, null, 2)}\n`, { encoding: 'utf8', flag: 'wx' })
  return { record, path }
}

export async function main(argv = process.argv.slice(2)): Promise<void> {
  const args = parseCliArgs(argv)
  const protocolPath = new URL('../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PRODUCT_ACCEPTANCE_PROTOCOL_v2.json', import.meta.url)
  const [protocol, config, input] = await Promise.all([
    readJson(protocolPath.pathname), readJson(args.configPath), readJson(args.inputPath),
  ])
  const written = await writeAcceptanceRun({
    protocol, suite: args.suite, environment: args.environment,
    environmentConfig: config, input, artifactDir: args.artifactDir,
  })
  process.stdout.write(`${JSON.stringify({ run_id: written.record.run_id, verdict: written.record.verdict, artifact: written.path })}\n`)
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((error: unknown) => {
    process.stderr.write(`${error instanceof Error ? error.message : 'PRODUCT_ACCEPTANCE_FAILED'}\n`)
    process.exitCode = 1
  })
}
