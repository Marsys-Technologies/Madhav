/**
 * route_auth_recogniser.ts — pure source analysis behind
 * `route_auth_guard.test.ts` (SS N-373 PR-S3 part B). No filesystem, no DB.
 *
 * Question it answers, per exported HTTP method handler of a Next route file:
 *   "does this handler (or a file-local helper it calls) make at least one
 *    RECOGNISED verification call?"
 *
 * What it deliberately is NOT: a proof that the reject branch is correct, or
 * that the guard covers the right principal/chart. It detects the ABSENCE of any
 * recognised verification, which is exactly the class of bug the audit found
 * (handlers that rely on `proxy.ts` alone, whose check is forgeable). Presence
 * of a recognised call is necessary, not sufficient; the handlers' own tests
 * (`route.authz.test.ts`, ...) own sufficiency.
 *
 * Earned-signal discipline (§N.8): the analysis only counts CODE. Comments,
 * string literals and regex literals are blanked first, so a guard name that
 * appears only in a comment or a string does not make a handler "guarded".
 * `route_auth_guard.test.ts` self-tests this on synthetic sources, including a
 * synthetic UNGUARDED handler that must read false.
 */

export const HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'] as const
export type HttpMethod = (typeof HTTP_METHODS)[number]

/**
 * RECOGNISED verification calls. Every name was located in the audit
 * (`SESSION_GATE_AUDIT.md` §1, §9c) or in the handlers themselves; each is a
 * call (`name(`), so `process.env.NAME` or an import alone never counts.
 *
 * session (firebase-admin verifySessionCookie / verifyIdToken underneath):
 *   getServerUser, getServerUserWithProfile, verifySessionCookie, verifyIdToken
 * role / ownership / chart permission (all start from getServerUser):
 *   requireSuperAdmin, accountOwner, usageOwner, withAiConsole,
 *   guardObservatoryRoute, requireChartPermission, authorizeChartAccess,
 *   resolveChartPageAccess
 * service-to-service:
 *   validateServiceToken (X-MCP-Internal-Token), validateMcpServiceRequest
 *   (token + Google OIDC), validateMcpKey (MCP API key), verifyOidcToken
 *   (Google OIDC), verifyFeedToken (HMAC feed token)
 */
export const RECOGNISED_VERIFICATION_CALLS: readonly string[] = [
  'getServerUser',
  'getServerUserWithProfile',
  'verifySessionCookie',
  'verifyIdToken',
  'requireSuperAdmin',
  'accountOwner',
  'usageOwner',
  'withAiConsole',
  'withAiConsoleMutation',
  'admitRequest',
  'guardObservatoryRoute',
  'requireChartPermission',
  'authorizeChartAccess',
  'resolveChartPageAccess',
  'validateServiceToken',
  'validateMcpServiceRequest',
  'validateMcpKey',
  'verifyOidcToken',
  'verifyFeedToken',
]

/**
 * Authorisation-only primitives: they decide WHAT a known principal may do but
 * take the uid as an argument, so on their own they authenticate nobody. They
 * are recognised (listed above) but do not make a handler "guarded" unless an
 * authenticating call is reachable too. (Today every handler that uses one also
 * calls getServerUser / a service-token check, so this costs nothing and closes
 * the "authz call on an attacker-supplied uid" hole.)
 */
export const AUTHZ_ONLY_CALLS: ReadonlySet<string> = new Set(['requireChartPermission', 'authorizeChartAccess'])

/** Cron-secret check: a read of `env.MARSYS_CRON_SECRET` (dot or bracket form) in code. */
const CRON_SECRET_RE = /\benv\s*(?:\.\s*MARSYS_CRON_SECRET\b|\[\s*MARSYS_CRON_SECRET\s*\])/

const CALL_RE = new RegExp(`\\b(?:${RECOGNISED_VERIFICATION_CALLS.join('|')})\\s*\\(`)

// ── 1. blank comments, strings and regex literals ─────────────────────────────

const REGEX_PRECEDERS = new Set(['(', ',', '=', ':', '[', '!', '&', '|', '?', '{', '}', ';', '+', '-', '*', '%', '<', '>', '~', '^'])

/**
 * Returns `src` with every comment, string literal (contents AND quotes) and
 * regex literal replaced by spaces; newlines are preserved. Template-literal
 * `${ ... }` expressions are code and are kept. A string used as a property key
 * of the form `x['IDENTIFIER']` keeps its identifier (so `process.env['X']` is
 * still recognisable).
 */
export function stripNonCode(src: string): string {
  const out: string[] = []
  const n = src.length
  let i = 0
  // Stack of template-expression brace depths; empty => plain code.
  const templateStack: number[] = []
  let braceDepth = 0
  let lastSignificant = '' // last non-space code char, for regex-vs-divide

  // Rolling tail of emitted output (cheap lookbehind without re-joining `out`).
  let tail = ''
  const emit = (ch: string) => {
    out.push(ch)
    tail = (tail + ch).slice(-16)
  }
  const push = (ch: string) => emit(ch)
  const blank = (ch: string) => emit(ch === '\n' ? '\n' : ' ')

  while (i < n) {
    const c = src[i]
    const d = src[i + 1]

    // line comment
    if (c === '/' && d === '/') {
      while (i < n && src[i] !== '\n') blank(src[i++])
      continue
    }
    // block comment
    if (c === '/' && d === '*') {
      blank(src[i++])
      blank(src[i++])
      while (i < n && !(src[i] === '*' && src[i + 1] === '/')) blank(src[i++])
      if (i < n) {
        blank(src[i++])
        blank(src[i++])
      }
      continue
    }
    // quoted string
    if (c === '"' || c === "'") {
      const quote = c
      const start = i
      let j = i + 1
      while (j < n && src[j] !== quote && src[j] !== '\n') {
        if (src[j] === '\\') j++
        j++
      }
      const content = src.slice(start + 1, Math.min(j, n))
      const closed = src[j] === quote
      const before = tail.trimEnd().slice(-1)
      const after = src.slice(j + 1).trimStart()[0]
      const keep = closed && before === '[' && after === ']' && /^[A-Za-z_][A-Za-z0-9_]*$/.test(content)
      for (let k = start; k <= Math.min(j, n - 1); k++) {
        if (keep && k > start && k < j) push(src[k])
        else blank(src[k])
      }
      i = Math.min(j, n - 1) + 1
      lastSignificant = ')' // a string ends an operand
      continue
    }
    // template literal
    if (c === '`') {
      blank(src[i++])
      while (i < n && src[i] !== '`') {
        if (src[i] === '\\') {
          blank(src[i++])
          if (i < n) blank(src[i++])
          continue
        }
        if (src[i] === '$' && src[i + 1] === '{') {
          // enter a code expression
          blank(src[i++])
          push('{')
          i++
          templateStack.push(braceDepth)
          braceDepth++
          lastSignificant = '{'
          break
        }
        blank(src[i++])
      }
      if (i < n && src[i] === '`') {
        blank(src[i++])
        lastSignificant = ')'
      }
      continue
    }
    // regex literal (heuristic: only where an operand cannot precede)
    if (c === '/' && (lastSignificant === '' || REGEX_PRECEDERS.has(lastSignificant) || /\b(return|typeof|case)$/.test(tail.trimEnd()))) {
      let j = i + 1
      let inClass = false
      while (j < n && src[j] !== '\n') {
        if (src[j] === '\\') {
          j += 2
          continue
        }
        if (src[j] === '[') inClass = true
        else if (src[j] === ']') inClass = false
        else if (src[j] === '/' && !inClass) break
        j++
      }
      if (src[j] === '/') {
        j++
        while (j < n && /[a-z]/i.test(src[j])) j++
        for (let k = i; k < j; k++) blank(src[k])
        i = j
        lastSignificant = ')'
        continue
      }
    }
    // braces (track template-expression exit)
    if (c === '{') {
      braceDepth++
    } else if (c === '}') {
      braceDepth--
      if (templateStack.length > 0 && braceDepth === templateStack[templateStack.length - 1]) {
        // closing a ${ ... } : resume the template literal body
        templateStack.pop()
        push('}')
        i++
        while (i < n && src[i] !== '`') {
          if (src[i] === '\\') {
            blank(src[i++])
            if (i < n) blank(src[i++])
            continue
          }
          if (src[i] === '$' && src[i + 1] === '{') {
            blank(src[i++])
            push('{')
            i++
            templateStack.push(braceDepth)
            braceDepth++
            break
          }
          blank(src[i++])
        }
        if (i < n && src[i] === '`') {
          blank(src[i++])
          lastSignificant = ')'
        }
        continue
      }
    }
    push(c)
    if (!/\s/.test(c)) lastSignificant = c
    i++
  }
  return out.join('')
}

// ── 2. split into top-level chunks ────────────────────────────────────────────

const DECL_START = /^(?:export|function|async\s+function|const|let|var|type|interface|class|enum|import|declare|abstract)\b/

interface Chunk {
  text: string
}

export function splitTopLevel(code: string): Chunk[] {
  const chunks: Chunk[] = []
  let depth = 0
  let start = 0
  let lastSig = ''
  const n = code.length
  for (let i = 0; i < n; i++) {
    const c = code[i]
    if (c === '{' || c === '(' || c === '[') depth++
    else if (c === '}' || c === ')' || c === ']') depth = Math.max(0, depth - 1)

    if (depth === 0 && i > start && !/\s/.test(c) && /\s/.test(code[i - 1] ?? '') && DECL_START.test(code.slice(i, i + 24))) {
      // only at a line start, or right after `;` / `}` at depth 0
      const lineStart = code.lastIndexOf('\n', i - 1) + 1
      const atLineStart = code.slice(lineStart, i).trim() === ''
      if (atLineStart || lastSig === ';' || lastSig === '}') {
        // `export` directly followed by a `function`/`const` is one statement; handled by DECL_START on `export`.
        const prev = code.slice(start, i)
        if (prev.trim() !== '') {
          chunks.push({ text: prev })
          start = i
        }
      }
    }
    if (!/\s/.test(c)) lastSig = c
  }
  const tail = code.slice(start)
  if (tail.trim() !== '') chunks.push({ text: tail })
  return chunks
}

// ── 3. per-method analysis ────────────────────────────────────────────────────

export interface HandlerVerdict {
  method: HttpMethod
  guarded: boolean
  /** Recognised calls reached (directly or through file-local helpers). */
  via: string[]
  /** True when the export form could not be resolved to a body (conservative: unguarded). */
  unresolved?: boolean
}

function directGuards(text: string): string[] {
  const found: string[] = []
  const callRe = new RegExp(`\\b(${RECOGNISED_VERIFICATION_CALLS.join('|')})\\s*\\(`, 'g')
  for (const m of text.matchAll(callRe)) found.push(m[1])
  if (CRON_SECRET_RE.test(text)) found.push('MARSYS_CRON_SECRET')
  return found
}

function localName(chunk: string): string | null {
  const m =
    /^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)/.exec(chunk) ??
    /^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*[=:]/.exec(chunk)
  return m ? m[1] : null
}

/**
 * Analyses one route source. Returns one verdict per EXPORTED HTTP method.
 * Export forms understood: `export [async] function M`, `export const M =`,
 * `export { local as M }` / `export { M }` (resolved to the local declaration).
 * `export { M } from '...'` and `export * from '...'` cannot be resolved and
 * are reported as unresolved (unguarded) so they must be allow-listed.
 */
export function buildReach(code: string): { chunks: Chunk[]; reach: Map<string, Set<string>> } {
  const chunks = splitTopLevel(code)

  // File-local declarations by name.
  const byName = new Map<string, string>()
  for (const ch of chunks) {
    const name = localName(ch.text)
    if (name) byName.set(name, ch.text)
  }

  // Guard reach through file-local helpers: fixpoint over "calls a guarded local".
  const reach = new Map<string, Set<string>>()
  for (const [name, text] of byName) reach.set(name, new Set(directGuards(text)))
  let changed = true
  while (changed) {
    changed = false
    for (const [name, text] of byName) {
      const mine = reach.get(name)!
      for (const [other, otherReach] of reach) {
        if (other === name || otherReach.size === 0) continue
        // an edge is a call `other(`, or a bare reference as the whole right-hand side (`= other`)
        const edge = new RegExp(`\\b${escapeRe(other)}\\s*\\(|=\\s*${escapeRe(other)}\\s*;?\\s*$`)
        if (edge.test(text)) {
          for (const g of otherReach) {
            if (!mine.has(g)) {
              mine.add(g)
              changed = true
            }
          }
        }
      }
    }
  }

  return { chunks, reach }
}

/**
 * Recognised calls reachable from the file-local function `name` in `src`
 * (directly or through file-local helpers). Used to verify that the shared
 * wrapper helpers still really call the verification they are trusted for.
 */
export function reachOfFunction(src: string, name: string): string[] | null {
  const { reach } = buildReach(stripNonCode(src))
  const r = reach.get(name)
  return r ? [...r] : null
}

export function analyseRouteSource(src: string): HandlerVerdict[] {
  const { chunks, reach } = buildReach(stripNonCode(src))

  const verdicts = new Map<HttpMethod, HandlerVerdict>()
  const setVerdict = (method: HttpMethod, via: Set<string> | string[], unresolved = false) => {
    const arr = [...via]
    const prev = verdicts.get(method)
    // If a method is somehow exported twice, the weaker verdict wins (conservative).
    if (prev && !prev.guarded) return
    const authenticates = arr.some((g) => !AUTHZ_ONLY_CALLS.has(g))
    verdicts.set(method, { method, guarded: authenticates && !unresolved, via: arr, unresolved: unresolved || undefined })
  }

  for (const ch of chunks) {
    const text = ch.text
    const fn = /^\s*export\s+(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)/.exec(text)
    const cn = /^\s*export\s+(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*[=:]/.exec(text)
    const exportedName = fn?.[1] ?? cn?.[1]
    if (exportedName && (HTTP_METHODS as readonly string[]).includes(exportedName)) {
      const own = new Set(directGuards(text))
      const viaLocal = reach.get(exportedName)
      if (viaLocal) for (const g of viaLocal) own.add(g)
      setVerdict(exportedName as HttpMethod, own)
      continue
    }

    // export { a as GET, b as POST, PATCH }   (local) — or with `from` (unresolvable)
    const list = /^\s*export\s*\{([^}]*)\}\s*(from\b)?/.exec(text)
    if (list) {
      const isFrom = Boolean(list[2])
      for (const part of list[1].split(',')) {
        const m = /^\s*([A-Za-z_$][\w$]*)(?:\s+as\s+([A-Za-z_$][\w$]*))?\s*$/.exec(part)
        if (!m) continue
        const local = m[1]
        const exported = (m[2] ?? m[1]) as string
        if (!(HTTP_METHODS as readonly string[]).includes(exported)) continue
        if (isFrom) {
          setVerdict(exported as HttpMethod, [], true)
        } else {
          setVerdict(exported as HttpMethod, reach.get(local) ?? [])
        }
      }
      continue
    }

    // export * from '...'  : cannot tell which methods it exports
    if (/^\s*export\s*\*\s*from\b/.test(text)) {
      for (const method of HTTP_METHODS) if (!verdicts.has(method)) setVerdict(method, [], true)
    }
  }

  return [...verdicts.values()].sort((a, b) => HTTP_METHODS.indexOf(a.method) - HTTP_METHODS.indexOf(b.method))
}

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

/** Exposed for the test's sanity check that the call regex is non-vacuous. */
export function mentionsRecognisedCall(code: string): boolean {
  return CALL_RE.test(code) || CRON_SECRET_RE.test(code)
}
