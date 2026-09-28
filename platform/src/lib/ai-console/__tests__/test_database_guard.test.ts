import { describe, expect, it } from 'vitest'
import { assertDisposableAiConsoleDatabaseUrl } from '../../../../scripts/ai-console/test_database_guard'

describe('AI Console disposable database guard', () => {
  it.each([
    'postgresql://tester@localhost:5432/ai_console_test_acceptance?host=prod.example.com',
    'postgresql://tester@localhost:5432/ai_console_test_acceptance?hostaddr=203.0.113.9',
    'postgresql://tester@localhost:5432/ai_console_test_acceptance?service=production',
    'postgresql://tester@localhost:5432/ai_console_test_acceptance?%68ost=prod.example.com',
    'postgresql://tester@localhost:5432/ai_console_test_acceptance%3Fhost%3Dprod.example.com',
    'postgresql://tester@localhost:5432/ai_console_test_acceptance?host=%2Fvar%2Frun%2Fpostgresql',
  ])('rejects ambiguous or redirecting PostgreSQL target %s without connecting', value => {
    expect(() => assertDisposableAiConsoleDatabaseUrl(value)).toThrow('AIC_ACCEPTANCE_DB_NOT_DISPOSABLE_LOCAL')
  })

  it.each([
    'postgresql://tester@localhost:5432/ai_console_test_acceptance',
    'postgres://tester@127.22.3.4:5432/ai_console_test_guard',
    'postgresql://tester@[::1]:5432/ai_console_test_ipv6',
  ])('accepts an unambiguous loopback disposable target %s', value => {
    expect(assertDisposableAiConsoleDatabaseUrl(value)).toBe(value)
  })

  it.each([
    'postgresql://tester@db.example.com:5432/ai_console_test_acceptance',
    'postgresql://tester@localhost:5432/production',
    'postgresql:///ai_console_test_socket',
    'https://localhost/ai_console_test_wrong_protocol',
  ])('rejects a non-local or non-disposable target %s', value => {
    expect(() => assertDisposableAiConsoleDatabaseUrl(value)).toThrow('AIC_ACCEPTANCE_DB_NOT_DISPOSABLE_LOCAL')
  })
})
