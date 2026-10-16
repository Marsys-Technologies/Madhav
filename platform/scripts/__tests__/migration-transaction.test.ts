import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { transactionalMigrationSql } from '../migration-transaction'

const prepare = (sql: string) => transactionalMigrationSql(sql, '001_test.sql')

describe('runner-owned migration transactions', () => {
  it.each([
    ['BEGIN;', 'COMMIT;'],
    ['begin work;', 'end work;'],
    ['START TRANSACTION;', 'COMMIT TRANSACTION'],
  ])('absorbs the single outer %s / %s without rewriting its body', (begin, commit) => {
    const body = "\nCREATE TABLE t (v text);\nINSERT INTO t VALUES ('COMMIT;');\n"
    expect(prepare(`-- header\n${begin}${body}${commit} -- tail`))
      .toBe(`-- header\n${body}${commit.endsWith(';') ? ' -- tail' : ''}`)
  })

  it('absorbs the unchanged real 1376 wrapper', () => {
    const sql = readFileSync(new URL('../../supabase/migrations/1376_k7_stage_verification_status.sql', import.meta.url), 'utf8')
    expect(prepare(sql)).toBe(sql.replace('BEGIN;', '').replace('COMMIT;', ''))
  })

  it('keeps a transaction-safe prelude in the runner transaction (historical 353 shape)', () => {
    const sql = 'CREATE EXTENSION IF NOT EXISTS vector;\nBEGIN;\nSELECT 1;\nCOMMIT;'
    expect(prepare(sql)).toBe('CREATE EXTENSION IF NOT EXISTS vector;\n\nSELECT 1;\n')
  })

  it('leaves transaction words in literals, identifiers, comments and PL/pgSQL bodies intact', () => {
    const sql = `-- COMMIT;\n/* BEGIN; /* ROLLBACK; */ COMMIT; */
      SELECT 'BEGIN; COMMIT; it''s safe', E'escaped\\\'; COMMIT;', "COMMIT";
      DO $outer$ BEGIN PERFORM '; COMMIT;'; END $outer$;
      DO $\u03bb$ BEGIN PERFORM 'COMMIT;'; END $\u03bb$;
      CREATE FUNCTION f() RETURNS text LANGUAGE sql AS $$ SELECT 'ROLLBACK;' $$;`
    expect(prepare(sql)).toBe(sql)
  })

  it.each([
    'CREATE TABLE t (id int); COMMIT; SELECT 1;',
    'BEGIN; SELECT 1; COMMIT; SELECT 2;',
    'BEGIN; SELECT 1; COMMIT; BEGIN; SELECT 2; COMMIT;',
    'BEGIN; SELECT 1; COMMIT AND CHAIN;',
    'START TRANSACTION READ ONLY; SELECT 1; COMMIT;',
    'SELECT 1; END;', 'ROLLBACK;', 'ABORT;', 'SAVEPOINT x;',
    'RELEASE SAVEPOINT x;', "PREPARE TRANSACTION 'x';",
    'BEGIN; COMMIT; COMMIT;', 'BEGIN;', 'COMMIT;',
    'BEGIN /* comment */; SELECT 1; COMMIT /* comment */; ROLLBACK;',
  ])('refuses transaction escape: %s', sql => {
    expect(() => prepare(sql)).toThrow(/transaction/i)
  })

  it.each([
    'CREATE INDEX CONCURRENTLY i ON t (v);',
    'CREATE UNIQUE INDEX /* nested /* comment */ */ CONCURRENTLY i ON t (v);',
    'DROP INDEX CONCURRENTLY IF EXISTS i;', 'REINDEX INDEX CONCURRENTLY i;',
    'VACUUM t;', 'CREATE DATABASE x;', 'DROP DATABASE x;',
    "CREATE TABLESPACE x LOCATION '/scratch';", 'DROP TABLESPACE x;',
    'ALTER DATABASE x SET TABLESPACE y;', "ALTER SYSTEM SET x = 'y';", 'DISCARD ALL;',
  ])('refuses nontransactional commands: %s', sql => {
    expect(() => prepare(sql)).toThrow(/nontransactional command.*reviewed handler/)
  })

  it('does not mistake a quoted index name or literal for a CONCURRENTLY keyword', () => {
    const sql = `CREATE INDEX "concurrently" ON t (v); SELECT 'CREATE INDEX CONCURRENTLY';`
    expect(prepare(sql)).toBe(sql)
  })

  it.each(["SELECT 'unterminated", 'DO $body$ BEGIN;', 'SELECT 1; /* unclosed', 'SELECT "broken'])
    ('refuses unterminated lexical input: %s', sql => expect(() => prepare(sql)).toThrow(/unterminated/))

  it.each(["SET standard_conforming_strings = off;", 'RESET standard_conforming_strings;'])
    ('refuses changing the string grammar: %s', sql => expect(() => prepare(sql)).toThrow(/string grammar/))
})
