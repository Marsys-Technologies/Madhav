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
  validateEnvironmentConfig,
  validateProtocol,
} from './acceptance_cases'
import { scoreAnswers } from './score_answers'

export interface AcceptanceInputFile {
  readonly answers: readonly AcceptanceAnswer[]
}

export interface AcceptanceRunRecord {
  readonly schema_version: typeof PRODUCT_ACCEPTANCE_RUN_VERSION
  readonly run_id: string
  readonly created_at: string
  readonly protocol_version: string
  readonly suite: AcceptanceSuite
  readonly environment: AcceptanceEnvironment
  readonly revision: string
  readonly environment_config: Pick<ApprovedEnvironmentConfig, 'schema_version' | 'environment' | 'base_url' | 'revision' | 'authorization' | 'evidence_mode'>
  readonly case_inputs: readonly unknown[]
  readonly evidence: readonly unknown[]
  readonly answers: readonly AcceptanceAnswer[]
  readonly failures: readonly unknown[]
  readonly verdict: string
  readonly evidence_kind: 'candidate_or_live' | 'fixture'
  readonly network_calls_made: 0
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
  if (!object(args.input) || !Array.isArray(args.input.answers)) throw new Error('PRODUCT_ACCEPTANCE_INPUT_INVALID')
  const inputs = casesForSuite(protocol, args.suite)
  const answers = args.input.answers as AcceptanceAnswer[]
  const score = scoreAnswers(inputs, answers)
  const fixture = config.evidence_mode === 'fixture'
  const deterministicFailures = score.cases.flatMap((item) => item.deterministic_failures.map((failure) => ({
    case_id: item.case_id, ...failure,
  })))
  const createdAt = (args.now ?? new Date()).toISOString()
  const record: AcceptanceRunRecord = {
    schema_version: PRODUCT_ACCEPTANCE_RUN_VERSION,
    run_id: args.runId ?? randomUUID(),
    created_at: createdAt,
    protocol_version: protocol.protocol_version,
    suite: args.suite,
    environment: args.environment,
    revision: config.revision,
    environment_config: config,
    case_inputs: inputs,
    evidence: answers.flatMap((answer) => answer.evidence.map((evidence) => ({ case_id: answer.case_id, ...evidence }))),
    answers,
    failures: deterministicFailures,
    // Fixture evidence may exercise the runner but is never accepted as a
    // candidate/live product result, regardless of qualitative score.
    verdict: fixture ? 'NOT_LIVE_EVIDENCE' : score.verdict,
    evidence_kind: fixture ? 'fixture' : 'candidate_or_live',
    network_calls_made: 0,
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
