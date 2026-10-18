/**
 * The runner owns the file transaction, including its ledger INSERT. Absorb a
 * single historical BEGIN/COMMIT pair without changing migration bytes.
 * Refuse other transaction boundaries and known nontransactional commands.
 * There is deliberately no nontransactional bypass: such a file needs an
 * explicitly reviewed execution/ledger protocol before this runner can apply it.
 */
interface Statement {
  start: number
  end: number
  code: string
}

/** Split only at SQL statement boundaries, never inside comments or literals.
 * Dollar-quoted DO/function bodies are opaque: their PL/pgSQL BEGIN/END and
 * semicolons do not control the surrounding PostgreSQL transaction.
 */
function statements(sql: string, filename: string): Statement[] {
  const result: Statement[] = []
  let start = 0
  let tokenStart: number | undefined
  let code = ''
  let i = 0
  const invalid = (): never => { throw new Error(`Migration "${filename}": unterminated SQL literal/comment`) }
  const finish = (end: number) => {
    if (code.trim()) result.push({ start: tokenStart ?? start, end, code: code.trim().toUpperCase() })
    start = end
    tokenStart = undefined
    code = ''
  }
  while (i < sql.length) {
    const c = sql[i]
    if (tokenStart === undefined && !/\s/.test(c) && c !== ';'
      && !sql.startsWith('--', i) && !sql.startsWith('/*', i)) tokenStart = i
    if (sql.startsWith('--', i)) {
      i += 2
      while (i < sql.length && sql[i] !== '\n' && sql[i] !== '\r') i++
      code += ' '
    } else if (sql.startsWith('/*', i)) {
      let depth = 1
      i += 2
      while (i < sql.length && depth) {
        if (sql.startsWith('/*', i)) { depth++; i += 2 }
        else if (sql.startsWith('*/', i)) { depth--; i += 2 }
        else i++
      }
      if (depth) invalid()
      code += ' '
    } else if (c === "'" || c === '"') {
      const escaped = c === "'" && /[eE]/.test(sql[i - 1] ?? '')
        && !/[A-Za-z0-9_$\u0080-\uFFFF]/.test(sql[i - 2] ?? '')
      i++
      let closed = false
      while (i < sql.length) {
        if (escaped && sql[i] === '\\') { i += 2; continue }
        if (sql[i] === c) {
          if (sql[i + 1] === c) { i += 2; continue }
          i++
          closed = true
          break
        }
        i++
      }
      if (!closed) invalid()
      code += ' ? '
    } else if (c === '$' && !/[A-Za-z0-9_$\u0080-\uFFFF]/.test(sql[i - 1] ?? '')) {
      const tag = sql.slice(i).match(/^\$(?:[A-Za-z_\u0080-\uFFFF][A-Za-z0-9_\u0080-\uFFFF]*)?\$/)?.[0]
      if (tag) {
        const end = sql.indexOf(tag, i + tag.length)
        if (end === -1) invalid()
        i = end + tag.length
        code += ' ? '
      } else { code += c; i++ }
    } else if (c === ';') {
      i++
      finish(i)
    } else {
      code += c
      i++
    }
  }
  finish(sql.length)
  return result
}

export function transactionalMigrationSql(sql: string, filename: string): string {
  const parts = statements(sql, filename)
  const plain = (part: Statement) => part.code.replace(/\s+/g, ' ')
  const isBegin = (part: Statement) => /^(BEGIN(?: WORK| TRANSACTION)?|START TRANSACTION)$/.test(plain(part))
  const isCommit = (part: Statement) => /^(COMMIT|END)(?: WORK| TRANSACTION)?$/.test(plain(part))
  // Some historical files put CREATE EXTENSION before BEGIN (e.g. 353).
  // It already runs inside the runner's BEGIN. Absorb that one plain pair
  // too, keeping the prelude in the same transaction as the rest of the file.
  const beginIndex = parts.findIndex(isBegin)
  const last = parts.length - 1
  const wrapped = beginIndex >= 0 && beginIndex < last && isCommit(parts[last])
  const body = parts.filter((_, index) => !wrapped || (index !== beginIndex && index !== last))
  for (const part of body) {
    const text = plain(part)
    if (/^(?:BEGIN|COMMIT|END|ROLLBACK|ABORT|SAVEPOINT|RELEASE)\b/.test(text)
      || /^(?:START|PREPARE) TRANSACTION\b/.test(text)) {
      throw new Error(`Migration "${filename}": transaction control "${text}" is not allowed; the runner owns DDL and ledger atomicity`)
    }
    if (/^(?:VACUUM|ALTER SYSTEM|DISCARD ALL)\b/.test(text)
      || /^(?:CREATE|DROP) (?:DATABASE|TABLESPACE)\b/.test(text)
      || /^ALTER DATABASE\b.*\bSET TABLESPACE\b/.test(text)
      || /^(?:CREATE (?:UNIQUE )?INDEX|DROP INDEX) CONCURRENTLY\b/.test(text)
      || /^REINDEX(?: \([^)]*\))? (?:INDEX|TABLE|SCHEMA|DATABASE|SYSTEM) CONCURRENTLY\b/.test(text)) {
      throw new Error(`Migration "${filename}": nontransactional command requires an explicitly reviewed handler; this runner only applies atomic files`)
    }
    // Our lexer uses PostgreSQL's default standard strings. Do not let a file
    // change that grammar and conceal a later transaction-ending statement.
    if (/^(?:SET|RESET)\b.*\bSTANDARD_CONFORMING_STRINGS\b/.test(text)
      && !/^SET (?:LOCAL |SESSION )?STANDARD_CONFORMING_STRINGS (?:=|TO) ON$/.test(text)) {
      throw new Error(`Migration "${filename}": changing the SQL string grammar is not supported`)
    }
  }
  return wrapped
    ? sql.slice(0, parts[beginIndex].start) + sql.slice(parts[beginIndex].end, parts[last].start) + sql.slice(parts[last].end)
    : sql
}
