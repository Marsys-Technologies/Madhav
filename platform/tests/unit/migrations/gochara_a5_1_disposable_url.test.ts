// @vitest-environment node
/**
 * Pravāha A5.1 round 4 — the disposable-database boundary of the live-DB
 * migration suite (ASTRA_REVIEW_A5_1_MIGRATIONS v1_1 F10, v1_2 N11), tested
 * WITHOUT connecting anywhere. The guard validates the DRIVER's parse of the
 * connection string (pg-connection-string) and returns the resolved config the
 * suite connects with; the two bypasses the reviewer demonstrated (`?host=`
 * override, doubled path slash) and every other target-changing or
 * default-dependent shape must be refused.
 */
import { describe, expect, it } from 'vitest'
import {
  DisposableDbUrlError,
  assertDisposableA51DatabaseUrl,
  resolveDisposableA51Config,
} from '../../integration/gochara_a5_1_disposable_url'

describe('resolveDisposableA51Config (F10/N11)', () => {
  it.each([
    ['postgresql://postgres@127.0.0.1:59531/gochara_a51_test', { host: '127.0.0.1', port: 59531, database: 'gochara_a51_test', user: 'postgres' }],
    ['postgres://postgres:postgres@localhost:5432/gochara_a51_test', { host: 'localhost', port: 5432, database: 'gochara_a51_test', user: 'postgres', password: 'postgres' }],
    ['postgresql://postgres@[::1]:5432/gochara_a51_test', { host: '::1', port: 5432, database: 'gochara_a51_test', user: 'postgres' }],
    ['postgresql://postgres@localhost:5432/gochara_a51_test?sslmode=disable', { host: 'localhost', port: 5432, database: 'gochara_a51_test', user: 'postgres', ssl: false }],
    ['postgresql://postgres@127.0.0.1:5432/gochara_a51_test?application_name=a51', { host: '127.0.0.1', port: 5432, database: 'gochara_a51_test', user: 'postgres', application_name: 'a51' }],
  ])('accepts an explicit loopback disposable target and returns the resolved config: %s', (url, expected) => {
    expect(resolveDisposableA51Config(url)).toEqual(expected)
    expect(() => assertDisposableA51DatabaseUrl(url)).not.toThrow()
  })

  it.each([
    // N11: the driver honours a query-string host override
    ['postgresql://127.0.0.1:5432/gochara_a51_test?host=db.example.com', /query option "host" is not allowed/],
    // N11: the driver reads a doubled slash as database "/gochara_a51_test"
    ['postgresql://127.0.0.1:5432//gochara_a51_test', /database "\/gochara_a51_test", not "gochara_a51_test"/],
    // N11: default-dependent targets — no host, no port
    ['postgresql:///gochara_a51_test', /default host/],
    ['postgresql://postgres@127.0.0.1/gochara_a51_test', /explicit numeric port is required/],
    // other target-changing options
    ['postgresql://127.0.0.1:5432/gochara_a51_test?hostaddr=10.0.0.1', /query option "hostaddr" is not allowed/],
    ['postgresql://127.0.0.1:5432/gochara_a51_test?dbname=production', /query option "dbname" is not allowed/],
    ['postgresql://127.0.0.1:5432/gochara_a51_test?options=-csearch_path%3Dx', /query option "options" is not allowed/],
    ['postgresql://127.0.0.1:5432/gochara_a51_test?service=prod', /query option "service" is not allowed/],
    ['postgresql://127.0.0.1:5432/gochara_a51_test?port=5433', /query option "port" is not allowed/],
    ['postgresql://127.0.0.1:5432/gochara_a51_test?sslmode=require', /only sslmode=disable/],
    // F10: the token anywhere but the database path
    ['postgresql://db.example.com:5432/production?application_name=gochara_a51_test', /database "production"/],
    ['postgresql://gochara_a51_test@127.0.0.1:5432/production', /database "production"/],
    ['postgresql://postgres@gochara_a51_test:5432/production', /database "production"/],
    ['postgresql://postgres@127.0.0.1:5432/production#gochara_a51_test', /fragment is not allowed/],
    ['postgresql://postgres@127.0.0.1:5432/gochara_a51_test_prod', /not "gochara_a51_test"/],
    ['postgresql://postgres@127.0.0.1:5432/prod_gochara_a51_test', /not "gochara_a51_test"/],
    // right database name, remote host
    ['postgresql://postgres@db.example.com:5432/gochara_a51_test', /host "db.example.com", which is not a loopback/],
    ['postgresql://postgres@10.0.0.5:5432/gochara_a51_test', /host "10.0.0.5", which is not a loopback/],
    // wrong scheme / no database / garbage
    ['mysql://root@127.0.0.1:3306/gochara_a51_test', /scheme "mysql:"/],
    ['postgresql://postgres@127.0.0.1:5432/', /"\(none\)"/],
    ['not a url', /not a parseable URL/],
  ])('refuses %s', (url, reason) => {
    expect(() => resolveDisposableA51Config(url)).toThrow(DisposableDbUrlError)
    expect(() => resolveDisposableA51Config(url)).toThrow(reason)
  })

  it('refuses an unset value', () => {
    expect(() => resolveDisposableA51Config(undefined)).toThrow(/no URL supplied/)
    expect(() => resolveDisposableA51Config('')).toThrow(/no URL supplied/)
  })
})
