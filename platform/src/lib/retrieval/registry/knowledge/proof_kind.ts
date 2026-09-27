import type { CapabilityProofKind, SemanticCapabilityBinding, SemanticCapabilityDeclaration } from './types'

/**
 * The single fallback chain for "what proof kind does this BINDING actually have" (R3
 * boundary, "genuine per-mode proof typing"). Every caller that needs a binding's proof kind
 * — the compiler's integrity checks, the overlay's availability resolution, the planner's
 * admission decision — MUST go through this function rather than reading `binding.proof_kind`
 * or `scu.proof_kind` directly, so a future fourth call site cannot silently pick a different
 * (wrong) precedence and reintroduce the exact "one capability, one proof_kind" defect this
 * type exists to close.
 */
export function bindingProofKind(
  scu: Pick<SemanticCapabilityDeclaration, 'proof_kind'>,
  binding: Pick<SemanticCapabilityBinding, 'proof_kind'>,
): CapabilityProofKind {
  return binding.proof_kind ?? scu.proof_kind ?? 'answer'
}

/** True when this specific binding's own proof kind is not 'answer' — i.e. it can never
 *  evidence a composite answer or be admitted as answer evidence, regardless of what other
 *  bindings on the same SCU report. */
export function isNonAnswerBinding(
  scu: Pick<SemanticCapabilityDeclaration, 'proof_kind'>,
  binding: Pick<SemanticCapabilityBinding, 'proof_kind'>,
): boolean {
  return bindingProofKind(scu, binding) !== 'answer'
}

/**
 * Does this request's intended arguments select `binding` over its SCU siblings? A binding
 * with no `mode_selector` is the SCU's default: it matches whenever no OTHER binding's
 * selector matches (so a plain, non-modal SCU's single primary binding is always selected,
 * exactly as before this type existed), or when `intendedArgs` is empty/undefined.
 */
export function bindingMatchesMode(
  binding: Pick<SemanticCapabilityBinding, 'mode_selector'>,
  intendedArgs: Readonly<Record<string, unknown>> | undefined,
): boolean {
  const selector = binding.mode_selector
  if (!selector || selector.length === 0) return true
  if (!intendedArgs) return false
  return selector.every((clause) => intendedArgs[clause.argument] === clause.equals)
}

/**
 * Select the one binding (from an SCU's channel-eligible bindings) matching the caller's
 * intended arguments, per the `mode_selector`/`fixed_args` contract above. Returns the
 * default binding — preferring `relation: 'primary'`, exactly today's pre-existing
 * `primary ?? candidates[0]` fallback — when no candidate's selector matches, or when no
 * mode-specific args were supplied. This is a strict generalization of that fallback: for
 * every SCU in the current estate (none declare `mode_selector`), the result is byte-identical
 * to the old `primary ?? candidates[0]` heuristic.
 */
export function selectBindingForMode<B extends Pick<SemanticCapabilityBinding, 'mode_selector' | 'relation'>>(
  candidates: readonly B[],
  intendedArgs: Readonly<Record<string, unknown>> | undefined,
): B | null {
  if (candidates.length === 0) return null
  const explicitMatch = candidates.find((candidate) =>
    (candidate.mode_selector?.length ?? 0) > 0 && bindingMatchesMode(candidate, intendedArgs))
  if (explicitMatch) return explicitMatch
  const selectorless = candidates.filter((candidate) => (candidate.mode_selector?.length ?? 0) === 0)
  return selectorless.find((candidate) => candidate.relation === 'primary') ?? selectorless[0] ?? candidates[0] ?? null
}
