/**
 * _structural_checks.ts — shared structural-invariant walkers used by Task 3
 * (receipt_gate.ts) and Task 5 (claim_checker_gate.ts). Both checks are purely
 * structural (per task-5 spec: "bounded to structural checks (array length vs
 * claimed count, presence/absence consistency), not semantic/timing claim
 * verification") — they walk an already-parsed JSON response object, never inspect
 * chart semantics.
 */

export type StructuralViolation = { path: string; reason: string }

const COMPLETE_STATUS_VALUES = new Set(['complete', 'confirmed', 'served', 'done', 'pass', 'passed', 'full', '✓', 'ok'])
const ARRAY_KEY_HINT = /^(rows|items|results|signals|entries|records|categories|data|list|matches|hits|values)$/i
const STATUS_KEY_HINT = /^(status|state|receipt_state|completeness|verification_status)$/i
const COUNT_KEY_HINT = /(_count|^count$|^total)/i

function isPlainObject(v: unknown): v is Record<string, unknown> {
  return typeof v === 'object' && v !== null && !Array.isArray(v)
}

/**
 * Task 3 / C2's core structural invariant: "✓ over an empty array" must be
 * impossible. Walks every plain object in the response tree; whenever a key matching
 * STATUS_KEY_HINT holds a "complete"-class value (string in COMPLETE_STATUS_VALUES,
 * or boolean `true` under a key literally named `complete`/`served`/`confirmed`) AND
 * a SIBLING key matching ARRAY_KEY_HINT (or literally named the same domain word,
 * e.g. `rows`) is an array of length 0, that is a violation — a section claiming full
 * service while serving nothing.
 */
export function findEmptyOverConfirmedViolations(obj: unknown, path = '$'): StructuralViolation[] {
  const violations: StructuralViolation[] = []
  function walk(node: unknown, p: string): void {
    if (Array.isArray(node)) {
      node.forEach((item, i) => walk(item, `${p}[${i}]`))
      return
    }
    if (!isPlainObject(node)) return
    const keys = Object.keys(node)
    const statusKeys = keys.filter((k) => STATUS_KEY_HINT.test(k) || /^(complete|served|confirmed)$/i.test(k))
    const emptyArrayKeys = keys.filter((k) => Array.isArray(node[k]) && (node[k] as unknown[]).length === 0)
    if (statusKeys.length > 0 && emptyArrayKeys.length > 0) {
      for (const sk of statusKeys) {
        const v = node[sk]
        const isCompleteClaim =
          (typeof v === 'string' && COMPLETE_STATUS_VALUES.has(v.toLowerCase())) || (typeof v === 'boolean' && v === true && /^(complete|served|confirmed)$/i.test(sk))
        if (isCompleteClaim) {
          for (const ak of emptyArrayKeys) {
            violations.push({
              path: `${p}.${ak}`,
              reason: `Status field '${sk}'='${String(v)}' claims completeness while sibling array '${ak}' is empty (length 0) — a "✓ over an empty array" structural violation.`,
            })
          }
        }
      }
    }
    for (const k of keys) walk(node[k], `${p}.${k}`)
  }
  walk(obj, path)
  return violations
}

/**
 * Task 5b: receipt-vs-payload consistency (array length vs claimed count). Walks the
 * response tree; whenever a plain object has BOTH a key matching COUNT_KEY_HINT
 * (numeric) AND a sibling array-typed key whose base name plausibly matches the count
 * key (e.g. `confirmed_count` + `confirmed`/`confirmed_rows`, or a lone `count` next
 * to a lone array field), asserts the count equals the array's length. Deliberately
 * conservative — only fires when the naming correspondence is unambiguous, to avoid
 * false positives on unrelated counts/arrays that happen to be siblings.
 */
export function findCountArrayMismatches(obj: unknown, path = '$'): StructuralViolation[] {
  const violations: StructuralViolation[] = []
  function baseName(k: string): string {
    return k.replace(/_count$/i, '').replace(/^total_/i, '').toLowerCase()
  }
  function walk(node: unknown, p: string): void {
    if (Array.isArray(node)) {
      node.forEach((item, i) => walk(item, `${p}[${i}]`))
      return
    }
    if (!isPlainObject(node)) return
    const keys = Object.keys(node)
    const countKeys = keys.filter((k) => COUNT_KEY_HINT.test(k) && typeof node[k] === 'number')
    const arrayKeys = keys.filter((k) => Array.isArray(node[k]))
    // Case A: exactly one count field and one array field on the same object — a very
    // common shape (`{ count, items }` / `{ total, results }`) — always comparable.
    if (countKeys.length === 1 && arrayKeys.length === 1) {
      const ck = countKeys[0]!
      const ak = arrayKeys[0]!
      const claimed = node[ck] as number
      const actual = (node[ak] as unknown[]).length
      if (claimed !== actual) {
        violations.push({
          path: `${p}.${ck}`,
          reason: `Claimed count '${ck}'=${claimed} does not match actual array length '${ak}'.length=${actual}.`,
        })
      }
    }
    // Case B: name-correspondence match (e.g. confirmed_count <-> confirmed / confirmed_rows).
    for (const ck of countKeys) {
      const base = baseName(ck)
      if (!base) continue
      const matchingArrayKey = arrayKeys.find((ak) => {
        const akl = ak.toLowerCase()
        return akl === base || akl === `${base}_rows` || akl === `${base}s` || akl.startsWith(base)
      })
      if (matchingArrayKey && countKeys.length > 1) {
        const claimed = node[ck] as number
        const actual = (node[matchingArrayKey] as unknown[]).length
        if (claimed !== actual) {
          violations.push({
            path: `${p}.${ck}`,
            reason: `Claimed count '${ck}'=${claimed} does not match name-corresponding array '${matchingArrayKey}'.length=${actual}.`,
          })
        }
      }
    }
    for (const k of keys) walk(node[k], `${p}.${k}`)
  }
  walk(obj, path)
  return violations
}
