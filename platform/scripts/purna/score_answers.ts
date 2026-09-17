import type { AcceptanceAnswer, AcceptanceCaseInput, DeterministicEvidence, QualitativeAssessment } from './acceptance_cases'

export interface CaseScore {
  readonly case_id: string
  readonly qualitative_assessment: QualitativeAssessment | null
  readonly deterministic_failures: readonly DeterministicEvidence[]
  readonly verdict: 'PASS' | 'FAIL_DETERMINISTIC_EVIDENCE' | 'FAIL_QUALITATIVE' | 'INCOMPLETE'
}

export interface AcceptanceFailure {
  readonly case_id: string
  readonly kind: 'deterministic' | 'qualitative' | 'incomplete'
  readonly gate_id: string | null
  readonly detail: string
  readonly qualitative_assessment: QualitativeAssessment | null
}

export interface AcceptanceScore {
  readonly verdict: 'PASS' | 'FAIL_DETERMINISTIC_EVIDENCE' | 'FAIL_QUALITATIVE' | 'INCOMPLETE'
  readonly cases: readonly CaseScore[]
  readonly failures: readonly AcceptanceFailure[]
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

function assessmentPasses(assessment: QualitativeAssessment): boolean {
  const scores = [assessment.relevance, assessment.evidence_based_explanation, assessment.contradiction_handling, assessment.usefulness]
  return scores.every((score) => score >= 3) && scores.reduce((total, score) => total + score, 0) / scores.length >= 4
}

/** Deterministic evidence always overrides an independent assessment. */
export function scoreAnswers(
  inputs: readonly AcceptanceCaseInput[],
  answers: readonly AcceptanceAnswer[],
): AcceptanceScore {
  const answersByCase = new Map(answers.map((answer) => [answer.case_id, answer]))
  const cases = inputs.map((input): CaseScore => {
    const answer = answersByCase.get(input.case_id)
    const failures = deterministicFailures(input, answer)
    const qualitative = answer?.qualitative_assessment ?? null
    if (failures.length > 0) return {
      case_id: input.case_id, qualitative_assessment: qualitative, deterministic_failures: failures,
      verdict: 'FAIL_DETERMINISTIC_EVIDENCE',
    }
    if (qualitative === null) return {
      case_id: input.case_id, qualitative_assessment: null, deterministic_failures: [], verdict: 'INCOMPLETE',
    }
    return {
      case_id: input.case_id, qualitative_assessment: qualitative, deterministic_failures: [],
      verdict: assessmentPasses(qualitative) ? 'PASS' : 'FAIL_QUALITATIVE',
    }
  })
  const deterministicFailureCount = cases.reduce((total, item) => total + item.deterministic_failures.length, 0)
  const failures = cases.flatMap((item): AcceptanceFailure[] => {
    if (item.verdict === 'FAIL_DETERMINISTIC_EVIDENCE') return item.deterministic_failures.map((failure) => ({
      case_id: item.case_id,
      kind: 'deterministic',
      gate_id: failure.gate_id,
      detail: failure.detail ?? 'evidence_failed_or_unreceipted',
      qualitative_assessment: item.qualitative_assessment,
    }))
    if (item.verdict === 'FAIL_QUALITATIVE') return [{
      case_id: item.case_id,
      kind: 'qualitative',
      gate_id: null,
      detail: 'independent_assessment_below_threshold',
      qualitative_assessment: item.qualitative_assessment,
    }]
    if (item.verdict === 'INCOMPLETE') return [{
      case_id: item.case_id,
      kind: 'incomplete',
      gate_id: null,
      detail: 'independent_assessment_missing',
      qualitative_assessment: null,
    }]
    return []
  })
  const verdict = deterministicFailureCount > 0 ? 'FAIL_DETERMINISTIC_EVIDENCE'
    : cases.some((item) => item.verdict === 'INCOMPLETE') ? 'INCOMPLETE'
      : cases.some((item) => item.verdict === 'FAIL_QUALITATIVE') ? 'FAIL_QUALITATIVE'
        : 'PASS'
  return { verdict, cases, failures, deterministic_failure_count: deterministicFailureCount }
}
