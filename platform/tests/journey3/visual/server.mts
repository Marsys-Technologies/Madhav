// Actual components and polling hooks; in-memory fictional responses only.
// All execution endpoints are blocked. Plan and clear endpoints return previews.
import { createServer } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'node:path'
import fixtures from '../fixtures'
const { DATA_ASSET, statOf } = fixtures
const root = process.cwd(), here = path.join(root, 'tests/journey3/visual')
const layers = ['brahmagyan', 'ganita', 'bodha', 'kala', 'phala', 'mimamsa']
const names = ['Ephemeris Engine', 'Planet positions', 'House themes', 'Timing windows', 'Synthesised indications', 'Prediction review']
const sanskrit = ['Graha Gaṇanā', 'Graha-sphuṭa', 'Bhāva', 'Daśā-kāla', 'Phala', 'Mīmāṃsā']
const assets = layers.map((layer, i) => ({ ...DATA_ASSET, layer, asset_id: `${layer}_fixture`, english_name: names[i], sanskrit_name: sanskrit[i],
  english_description: `Fictional ${names[i].toLowerCase()} for preparation verification.`, depends_on: i ? [`${layers[i-1]}_fixture`] : [] }))
assets.push({ ...assets[3], asset_id: 'candidate_fixture', english_name: 'Candidate timing model', sanskrit_name: 'candidate_fixture', is_active: false })
const requests: { method: string; pathname: string }[] = []
const server = await createServer({ configFile: false, root, plugins: [react(), {
  name: 'fictional-preparation-only', configureServer(server) {
    server.middlewares.use(async (req, res, next) => {
      const url = new URL(req.url ?? '/', 'http://fixture.local')
      if (!url.pathname.startsWith('/api/')) return next()
      const method = req.method ?? 'GET'; requests.push({ method, pathname: url.pathname })
      res.setHeader('Content-Type', 'application/json')
      let body: unknown
      if (method === 'GET' && url.pathname === '/api/fixture/requests') body = requests
      else if (method === 'GET' && url.pathname === '/api/cockpit/registry') body = { data: { assets } }
      else if (method === 'GET' && url.pathname === '/api/cockpit/stats') {
        const referer = req.headers.referer ?? ''
        if (referer.includes('status=error')) { res.statusCode = 503; res.end(JSON.stringify({ error: 'Fictional outage' })); return }
        body = { data: { assets: assets.filter(a => a.is_active && (!referer.includes('status=missing') || a.layer !== 'ganita')).map((a, i) => statOf({ asset_id: a.asset_id, state: i < 3 ? 'lit' : 'incomplete', actual_rows: i < 3 ? 9 : 2 })) } }
      }
      else if (method === 'GET' && url.pathname === '/api/cockpit/runs/active') body = { data: { run: (req.headers.referer ?? '').includes('run=active')
        ? { id: 'fictional-run', scope: 'asset', scope_target: 'ganita_fixture', action: 'build', state: 'running', plan: ['ganita_fixture'],
          current_asset_id: 'ganita_fixture', created_at: new Date().toISOString(), started_at: null, pause_requested_at: null, stop_requested_at: null }
        : null, assets: [] } }
      else if (method === 'GET' && url.pathname === '/api/charts/fictional-chart') body = { subject_name: 'Fictional Native', birth_date: '1990-01-01', birth_place: 'Fictional birthplace' }
      else if (method === 'GET' && url.pathname === '/api/cockpit/sse') {
        res.setHeader('Content-Type', 'text/event-stream'); res.write('event: hello\ndata: {}\n\n'); req.on('close', () => res.end()); return
      }
      else if (method === 'POST' && ['/api/cockpit/plan', '/api/cockpit/clear'].includes(url.pathname)) {
        const chunks: Buffer[] = []; for await (const chunk of req) chunks.push(Buffer.from(chunk))
        const request = JSON.parse(Buffer.concat(chunks).toString())
        const selected = request.scope === 'asset' ? assets.filter(a => a.asset_id === request.scope_target) : assets.filter(a => a.is_active && (request.scope === 'global' || a.layer === request.scope_target))
        body = url.pathname.endsWith('/plan') ? { data: { status: 'ok', plan_waves: [selected.map(a => a.asset_id)], blockers: [], estimated_seconds: 12 } } : { preview: { tables: [{ table: 'fictional_data', rows: 9 }], total_rows: 9, affected_assets: selected.map(a => a.asset_id), downstream_stale_assets: [], assets_clearable: selected.map(a => ({ id: a.asset_id, label: a.english_name, rows: 9 })), preview_hash: 'fixture-only', scope_label: selected[0]?.english_name, requires_typed_confirmation: 'CLEAR' } }
      } else { res.statusCode = 403; body = { error: 'Component verification cannot execute actions' } }
      res.end(JSON.stringify(body))
    })
  }
}], resolve: { alias: [
  { find: '@/hooks/useUserRole', replacement: path.join(here, 'role.ts') },
  { find: '@', replacement: path.join(root, 'src') },
  { find: 'next/link', replacement: path.join(here, 'navigation.tsx') },
  { find: 'next/navigation', replacement: path.join(here, 'navigation.tsx') },
] }, define: { 'process.env': {} }, server: { host: '127.0.0.1', port: 3193, strictPort: true } })
await server.listen()
console.log('Journey 3 verification: http://127.0.0.1:3193/tests/journey3/visual/index.html')
