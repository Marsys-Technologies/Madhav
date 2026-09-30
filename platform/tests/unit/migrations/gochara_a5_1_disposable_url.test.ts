// @vitest-environment node
/**
 * Pravāha A5.1 round 3 — the disposable-database boundary of the live-DB
 * migration suite (ASTRA_REVIEW_A5_1_MIGRATIONS v1_1 F10), tested WITHOUT
 * connecting anywhere: every misleading shape the review named (query-string
 * token, user name, host name) must be refused; only a loopback database named
 * exactly `gochara_a51_test` passes.
 */
import { describe, expect, it } from 'vitest'
import {
  DisposableDbUrlError,
  assertDisposableA51DatabaseUrl,
} from '../../integration/gochara_a5_1_disposable_url'

describe('assertDisposableA51DatabaseUrl (F10)', () => {
  it.each([
    'postgresql://postgres@127.0.0.1:59531/gochara_a51_test',
    'postgres://postgres:postgres@localhost:5432/gochara_a51_test',
    'postgresql://postgres@[::1]:5432/gochara_a51_test',
    'postgresql://postgres@localhost/gochara_a51_test?sslmode=disable',
    'postgresql:///gochara_a51_test',
  ])('accepts a loopback disposable target: %s', url => {
    expect(() => assertDisposableA51DatabaseUrl(url)).not.toThrow()
  })

  it.each([
    // the review's own counterexample: the token only in the query string
    ['postgresql://db.example/production?application_name=gochara_a51_test', /database in the path is "production"/],
    // token in the user name
    ['postgresql://gochara_a51_test@127.0.0.1/production', /database in the path is "production"/],
    // token in the host name
    ['postgresql://postgres@gochara_a51_test/production', /database in the path is "production"/],
    // token in the fragment
    ['postgresql://postgres@127.0.0.1/production#gochara_a51_test', /database in the path is "production"/],
    // token as a prefix / suffix of the real database name
    ['postgresql://postgres@127.0.0.1/gochara_a51_test_prod', /not "gochara_a51_test"/],
    ['postgresql://postgres@127.0.0.1/prod_gochara_a51_test', /not "gochara_a51_test"/],
    // right database name, remote host
    ['postgresql://postgres@db.example.com:5432/gochara_a51_test', /host "db.example.com" is not a loopback/],
    ['postgresql://postgres@10.0.0.5:5432/gochara_a51_test', /host "10.0.0.5" is not a loopback/],
    // wrong scheme
    ['mysql://root@127.0.0.1/gochara_a51_test', /scheme "mysql:"/],
    // no database at all
    ['postgresql://postgres@127.0.0.1:5432/', /"\(none\)"/],
    // garbage
    ['not a url', /not a parseable URL/],
  ])('refuses %s', (url, reason) => {
    expect(() => assertDisposableA51DatabaseUrl(url)).toThrow(DisposableDbUrlError)
    expect(() => assertDisposableA51DatabaseUrl(url)).toThrow(reason)
  })

  it('refuses an unset value', () => {
    expect(() => assertDisposableA51DatabaseUrl(undefined)).toThrow(/no URL supplied/)
    expect(() => assertDisposableA51DatabaseUrl('')).toThrow(/no URL supplied/)
  })
})
