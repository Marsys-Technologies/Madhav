import { mkdir, readFile, writeFile } from 'node:fs/promises'
import { resolve } from 'node:path'
import { randomUUID } from 'node:crypto'
import { runAdapter } from '../../src/lib/adapters/run_adapter'
import { DEFAULT_STACK_ID } from '../../src/lib/models/registry'
import { getEffectiveModel } from '../../src/lib/models/runtime_config'
import {
  casesForSuite,
  type AcceptanceAnswer,
  type AcceptanceCaseInput,
  type AcceptanceSuite,
  type QualitativeAssessment,
  validateAcceptanceAnswers,
  validateProtocol,
} from './acceptance_cases'
import { validateAccountableAnswersArtifact, type AccountableAnswersArtifact } from './answers_from_collection'

const AXES = ['relevance', 'evidence_based_explanation', 'contradiction_handling', 'usefulness'] as const

type JudgeScores = Record<(typeof AXES)[number], number>
export interface JudgeOutput extends JudgeScores { readonly rationale: string }

function object(value: unknown): Record<string, unknown> | null {
  return typeof value === 'object' && value !== null && !Array.isArray(value) ? value as Record<string, unknown> : null
}

/** Parse only a complete structured judgment; malformed model output is never a pass. */
export function parseJudgeOutput(value: unknown): JudgeOutput {
  const candidate = object(value)
  if (!candidate || typeof candidate.rationale !== 'string' || candidate.rationale.trim().length === 0
    || !AXES.every((axis) => Number.isInteger(candidate[axis]) && (candidate[axis] as number) >= 1 && (candidate[axis] as number) <= 5)) {
    throw new Error('PURNA_ANSWER_JUDGE_OUTPUT_INVALID')
  }
  return {
    relevance: candidate.relevance as number,
    evidence_based_explanation: candidate.evidence_based_explanation as number,
    contradiction_handling: candidate.contradiction_handling as number,
    usefulness: candidate.usefulness as number,
    rationale: candidate.rationale.trim(),
  }
}

export function buildJudgePrompt(input: AcceptanceCaseInput, answer: AcceptanceAnswer): string {
  return JSON.stringify({
    task: 'Independently assess this product answer. Do not infer missing evidence and do not score the system that produced it generously.',
    expected_outcome: input.expected,
    question: input.question,
    required_dimensions: input.required_dimensions,
    answer: answer.answer,
    deterministic_evidence: answer.evidence,
    response_accountability: answer.response_accountability ?? null,
    rubric: {
      relevance: 'Answers the stated question and required dimensions.',
      evidence_based_explanation: 'Explains claims using accountable evidence rather than unsupported assertion.',
      contradiction_handling: 'Names material uncertainty, conflict, or insufficiency honestly; do not penalize a justified bounded insufficiency.',
      usefulness: 'Gives a clear, actionable, appropriately calibrated result.',
    },
    output: 'Return JSON only: relevance, evidence_based_explanation, contradiction_handling, usefulness (each integer 1-5), rationale (brief string).',
  })
}

export async function judgeAnswers(args: {
  readonly inputs: readonly AcceptanceCaseInput[]
  readonly answers: readonly AcceptanceAnswer[]
  readonly modelId: string
  readonly invoke: (prompt: string) => Promise<unknown>
}): Promise<readonly AcceptanceAnswer[]> {
  const inputs = new Map(args.inputs.map((input) => [input.case_id, input]))
  return Promise.all(args.answers.map(async (answer) => {
    const input = inputs.get(answer.case_id)
    if (!input) throw new Error('PURNA_ANSWER_JUDGE_CASE_UNKNOWN')
    if (!answer.answer || !answer.response_accountability) throw new Error('PURNA_ANSWER_JUDGE_ACCOUNTABILITY_REQUIRED')
    const score = parseJudgeOutput(await args.invoke(buildJudgePrompt(input, answer)))
    const qualitative_assessment: QualitativeAssessment = {
      assessor: 'independent_eval_judge', model_id: args.modelId, ...score,
    }
    return { ...answer, qualitative_assessment }
  }))
}

export function judgedAnswersArtifact(args: {
  readonly input: AccountableAnswersArtifact
  readonly answers: readonly AcceptanceAnswer[]
  readonly approvalId: string
  readonly modelId: string
}): AccountableAnswersArtifact {
  return {
    schema_version: args.input.schema_version,
    provenance: args.input.provenance,
    assessment: {
      approval_id: args.approvalId,
      assessor: 'independent_eval_judge',
      model_id: args.modelId,
    },
    answers: args.answers,
  }
}

function parseCliArgs(argv: readonly string[]): { suite: AcceptanceSuite; inputPath: string; artifactDir: string; approvalId: string } {
  const values = new Map<string, string>()
  for (let index = 0; index < argv.length; index += 2) {
    const flag = argv[index]; const value = argv[index + 1]
    if (!flag?.startsWith('--') || value === undefined || values.has(flag)) throw new Error('PURNA_ANSWER_JUDGE_CLI_INVALID')
    values.set(flag, value)
  }
  if ([...values.keys()].some((flag) => !['--suite', '--input', '--artifact-dir', '--approval-id'].includes(flag))) throw new Error('PURNA_ANSWER_JUDGE_CLI_INVALID')
  const suite = values.get('--suite'); const inputPath = values.get('--input'); const artifactDir = values.get('--artifact-dir'); const approvalId = values.get('--approval-id')
  if ((suite !== 'beyond_acarya' && suite !== 'product') || !inputPath || !artifactDir || !approvalId) throw new Error('PURNA_ANSWER_JUDGE_CLI_REQUIRED_ARGUMENT_MISSING')
  return { suite, inputPath, artifactDir, approvalId }
}

async function main(argv = process.argv.slice(2)): Promise<void> {
  const args = parseCliArgs(argv)
  const protocolPath = new URL('../../../00_ARCHITECTURE/briefs/nirmana/purna_anvesana/PRODUCT_ACCEPTANCE_PROTOCOL_v2.json', import.meta.url)
  const [protocolValue, inputValue] = await Promise.all([readFile(protocolPath, 'utf8'), readFile(args.inputPath, 'utf8')])
  const protocol = validateProtocol(JSON.parse(protocolValue))
  const inputs = casesForSuite(protocol, args.suite)
  const input = validateAccountableAnswersArtifact(JSON.parse(inputValue), inputs)
  if (input.provenance.suite !== args.suite) throw new Error('PURNA_ANSWER_JUDGE_PROVENANCE_MISMATCH')
  const answers = validateAcceptanceAnswers(input.answers, inputs)
  const modelId = await getEffectiveModel(DEFAULT_STACK_ID, 'eval_judge', 'primary')
  const judged = await judgeAnswers({
    inputs, answers, modelId,
    invoke: async (prompt) => {
      const interaction = await runAdapter({
        callType: 'eval_judge', modelOverride: { modelId }, systemPrompt: 'You are an independent answer evaluator. Return only valid JSON matching the requested schema.',
        messages: [{ role: 'user', content: prompt }], temperature: 0, maxOutputTokens: 500,
        responseSchema: { type: 'object', additionalProperties: false, required: [...AXES, 'rationale'], properties: {
          relevance: { type: 'integer', minimum: 1, maximum: 5 }, evidence_based_explanation: { type: 'integer', minimum: 1, maximum: 5 },
          contradiction_handling: { type: 'integer', minimum: 1, maximum: 5 }, usefulness: { type: 'integer', minimum: 1, maximum: 5 }, rationale: { type: 'string', minLength: 1 },
        } },
      })
      if (interaction.finalStructured !== undefined) return interaction.finalStructured
      try { return JSON.parse(interaction.finalText ?? '') } catch { throw new Error('PURNA_ANSWER_JUDGE_OUTPUT_INVALID') }
    },
  })
  const directory = resolve(args.artifactDir)
  await mkdir(directory, { recursive: true })
  const path = resolve(directory, `judged-answers-${new Date().toISOString().replace(/[:.]/g, '-')}-${randomUUID()}.json`)
  await writeFile(path, `${JSON.stringify(judgedAnswersArtifact({
    input, answers: judged, approvalId: args.approvalId, modelId,
  }), null, 2)}\n`, { flag: 'wx' })
  process.stdout.write(`${JSON.stringify({ artifact: path, answers: judged.length, model_id: modelId })}\n`)
}

if (import.meta.url === `file://${process.argv[1]}`) main().catch((error: unknown) => {
  process.stderr.write(`${error instanceof Error ? error.message : 'PURNA_ANSWER_JUDGE_FAILED'}\n`)
  process.exitCode = 1
})
