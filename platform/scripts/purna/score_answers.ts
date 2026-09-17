import type { AcceptanceAnswer, AcceptanceCaseInput, DeterministicEvidence } from './acceptance_cases'

export interface CaseScore {
  readonly case_id: string
  readonly qualitative_score: number | null
  readonly deterministic_failures: readonly DeterministicEvidence[]
  readonly verdict: 'PASS' | 'FAIL_DETERMINISTIC_EVIDENCE' | 'FAIL_QUALITATIVE' | 'INCOMPLETE'
}

export interface AcceptanceScore {
  readonly verdict: 'PASS' | 'FAIL_DETERMINISTIC_EVIDENCE' | 'FAIL_QUALITATIVE' | 'INCOMPLETE'
  readonly cases: readonly CaseScore[]
  readonly deterministic_failure_count: number
}

function deterministicFailures(
  input: AcceptanceCaseInput,
  answer: AcceptanceAnswer | undefined,
): DeterministicEvidence[] {
  if (!answer) return input.deterministic_gates.map((gate_id) => ({
    gate_id, passed: false, receipt_ref: null, detail: 'answer_missing',
  }))
  const byGate = new Map(answer.evidence.map((evidence) => [evidence.gate_id, evidence]))
  return input.deterministic_gates.flatMap((gateId) => {
    const evidence = byGate.get(gateId)
    if (!evidence) return [{ gate_id: gateId, passed: false, receipt_ref: null, detail: 'evidence_missing' }]
    return evidence.passed && evidence.receipt_ref ? [] : [{ ...evidence, detail: evidence.detail ?? 'evidence_failed_or_unreceipted' }]
  })
}

/** Deterministic evidence always overrides a qualitative score, including 1.0. */
export function scoreAnswers(
  inputs: readonly AcceptanceCaseInput[],
  answers: readonly AcceptanceAnswer[],
  minimumQualitativeScore = 0.7,
): AcceptanceScore {
  const answersByCase = new Map(answers.map((answer) => [answer.case_id, answer]))
  const cases = inputs.map((input): CaseScore => {
    const answer = answersByCase.get(input.case_id)
    const failures = deterministicFailures(input, answer)
    const qualitative = answer?.qualitative_score ?? null
    if (failures.length > 0) return {
      case_id: input.case_id, qualitative_score: qualitative, deterministic_failures: failures,
      verdict: 'FAIL_DETERMINISTIC_EVIDENCE',
    }
    if (qualitative === null) return {
      case_id: input.case_id, qualitative_score: null, deterministic_failures: [], verdict: 'INCOMPLETE',
    }
    return {
      case_id: input.case_id, qualitative_score: qualitative, deterministic_failures: [],
      verdict: qualitative >= minimumQualitativeScore ? 'PASS' : 'FAIL_QUALITATIVE',
    }
  })
  const deterministicFailureCount = cases.reduce((total, item) => total + item.deterministic_failures.length, 0)
  const verdict = deterministicFailureCount > 0 ? 'FAIL_DETERMINISTIC_EVIDENCE'
    : cases.some((item) => item.verdict === 'INCOMPLETE') ? 'INCOMPLETE'
      : cases.some((item) => item.verdict === 'FAIL_QUALITATIVE') ? 'FAIL_QUALITATIVE'
        : 'PASS'
  return { verdict, cases, deterministic_failure_count: deterministicFailureCount }
}
