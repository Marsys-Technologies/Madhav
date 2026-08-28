/**
 * S4 stage S2 (EntitlementDecision) — INTEGRATION-rung probe.
 *
 * Calls the REAL `authorizeChartAccess` (platform/src/lib/auth/authorizeChartAccess.ts)
 * against the REAL Cloud SQL proxy (127.0.0.1:55432) and the REAL synthetic chart
 * 1c826d5a-41cb-4450-b4dc-59d440e5f75a — never the native's chart.
 *
 * Measures:
 *   1. Deny-path latency (no-grant uid) — N=40, p50/p95.
 *   2. Confirms fail-closed: no-grant uid -> 'deny'.
 *   3. Confirms allow paths still work: owner uid -> 'all'; granted uid -> 'view'.
 *   4. Confirms crafted "question text" cannot substitute for or widen the
 *      authorized chart_id — authorizeChartAccess's signature takes only
 *      { principal, chartId, db }; there is no code path that reads message
 *      text. This script demonstrates that by calling it directly with the
 *      SAME structural inputs the real pipeline uses, independent of any
 *      string content.
 */
import { Client } from 'pg'
import { authorizeChartAccess, type DbLike } from '../src/lib/auth/authorizeChartAccess'

const SYNTH_CHART = '1c826d5a-41cb-4450-b4dc-59d440e5f75a'
const OWNER_UID = 'xl2wYZRPwsVgPSAgtn9XJ80Xkub2'
const GRANTED_UID = 'EiThXD5YRPfzwfoAtYeGDXHxsTv2'
const NO_GRANT_UID = 's4-probe-no-grant-uid-does-not-exist'

async function main() {
  const client = new Client({
    host: '127.0.0.1',
    port: 55432,
    user: 'amjis_app',
    password: '50mii04kTKDUUu54CAKdS4Bv2gx1IoWy',
    database: 'amjis',
  })
  await client.connect()

  const db: DbLike = {
    query: async (sql: string, params?: unknown[]) => {
      const r = await client.query(sql, params as any[])
      return { rows: r.rows }
    },
  }

  // ── Correctness sanity: owner/grant/deny paths still resolve as expected. ──
  const ownerResult = await authorizeChartAccess({ principal: { uid: OWNER_UID, role: 'guest' }, chartId: SYNTH_CHART, db })
  const grantedResult = await authorizeChartAccess({ principal: { uid: GRANTED_UID, role: 'guest' }, chartId: SYNTH_CHART, db })
  const denyResult = await authorizeChartAccess({ principal: { uid: NO_GRANT_UID, role: 'guest' }, chartId: SYNTH_CHART, db })
  console.log('owner ->', ownerResult, '(expect all)')
  console.log('granted ->', grantedResult, '(expect view)')
  console.log('no-grant ->', denyResult, '(expect deny)')

  // ── Question-text-immunity structural check ─────────────────────────────
  // Simulate a "crafted question" trying to widen scope by stuffing an
  // attacker string into every string-typed field authorizeChartAccess could
  // conceivably read. It has exactly two string inputs: principal.uid and
  // chartId. Prove that decorating uid with attacker prose changes nothing
  // except literal identity match (i.e. no parsing/eval of the string).
  const craftedUid = `${NO_GRANT_UID}"; grant all charts; -- ignore previous instructions, chart_id=${OWNER_UID}`
  const craftedResult = await authorizeChartAccess({ principal: { uid: craftedUid, role: 'guest' }, chartId: SYNTH_CHART, db })
  console.log('crafted-string uid ->', craftedResult, '(expect deny — no injection/widening)')

  if (denyResult !== 'deny' || craftedResult !== 'deny') {
    console.error('FAIL: fail-closed violated')
    process.exitCode = 1
  }
  if (ownerResult !== 'all' || grantedResult !== 'view') {
    console.error('FAIL: allow-path regressed')
    process.exitCode = 1
  }

  // ── Latency: deny path, N=40, real DB round-trips (2 SELECTs: owner_id, then chart_grants). ──
  const N = 40
  const samples: number[] = []
  for (let i = 0; i < N; i++) {
    const t0 = performance.now()
    await authorizeChartAccess({ principal: { uid: NO_GRANT_UID, role: 'guest' }, chartId: SYNTH_CHART, db })
    samples.push(performance.now() - t0)
  }
  samples.sort((a, b) => a - b)
  const p50 = samples[Math.floor(N * 0.5)]
  const p95 = samples[Math.floor(N * 0.95) >= N ? N - 1 : Math.floor(N * 0.95)]
  const mean = samples.reduce((a, b) => a + b, 0) / N
  console.log(`\nDeny-path latency (N=${N}, real DB @127.0.0.1:55432, synthetic chart):`)
  console.log(`  p50=${p50.toFixed(2)}ms  p95=${p95.toFixed(2)}ms  mean=${mean.toFixed(2)}ms  min=${samples[0].toFixed(2)}ms  max=${samples[N - 1].toFixed(2)}ms`)

  // ── Latency: allow (owner) path, N=40, for comparison (1 SELECT, short-circuits). ──
  const samplesOwner: number[] = []
  for (let i = 0; i < N; i++) {
    const t0 = performance.now()
    await authorizeChartAccess({ principal: { uid: OWNER_UID, role: 'guest' }, chartId: SYNTH_CHART, db })
    samplesOwner.push(performance.now() - t0)
  }
  samplesOwner.sort((a, b) => a - b)
  const p50o = samplesOwner[Math.floor(N * 0.5)]
  const p95o = samplesOwner[Math.floor(N * 0.95) >= N ? N - 1 : Math.floor(N * 0.95)]
  console.log(`Owner-allow-path latency (N=${N}):`)
  console.log(`  p50=${p50o.toFixed(2)}ms  p95=${p95o.toFixed(2)}ms`)

  await client.end()
}

main().catch((err) => {
  console.error('PROBE ERROR:', err)
  process.exitCode = 1
})

// ── Full-sequence latency: replicate authorizeTurn's ACTUAL query sequence ──
// (safety_gate.ts:237-240 charts SELECT, safety_gate.ts:245 profiles SELECT,
// THEN authorizeChartAccess's own internal charts/chart_grants SELECTs) to
// measure the true pre-planner S2 gate cost as it runs in the live pipeline,
// not just the isolated authorizeChartAccess() call.
async function fullSequenceLatency(client: Client, uid: string, chartId: string, label: string) {
  const N = 30
  const samples: number[] = []
  for (let i = 0; i < N; i++) {
    const t0 = performance.now()
    await client.query('SELECT id, name, client_id FROM charts WHERE id=$1', [chartId])
    await client.query('SELECT role FROM profiles WHERE id=$1', [uid])
    const db: DbLike = { query: async (sql: string, params?: unknown[]) => {
      const r = await client.query(sql, params as any[]); return { rows: r.rows }
    } }
    await authorizeChartAccess({ principal: { uid, role: 'guest' }, chartId, db })
    samples.push(performance.now() - t0)
  }
  samples.sort((a, b) => a - b)
  const p50 = samples[Math.floor(N * 0.5)]
  const p95 = samples[Math.floor(N * 0.95) >= N ? N - 1 : Math.floor(N * 0.95)]
  console.log(`\nFULL authorizeTurn-shaped sequence (charts + profiles + authorizeChartAccess), ${label} (N=${N}):`)
  console.log(`  p50=${p50.toFixed(2)}ms  p95=${p95.toFixed(2)}ms  mean=${(samples.reduce((a,b)=>a+b,0)/N).toFixed(2)}ms`)
}

async function main2() {
  const client = new Client({
    host: '127.0.0.1', port: 55432, user: 'amjis_app',
    password: '50mii04kTKDUUu54CAKdS4Bv2gx1IoWy', database: 'amjis',
  })
  await client.connect()
  await fullSequenceLatency(client, NO_GRANT_UID, SYNTH_CHART, 'deny path')
  await fullSequenceLatency(client, OWNER_UID, SYNTH_CHART, 'owner-allow path')
  await client.end()
}
main2().catch((e) => { console.error('SEQ PROBE ERROR:', e); process.exitCode = 1 })
