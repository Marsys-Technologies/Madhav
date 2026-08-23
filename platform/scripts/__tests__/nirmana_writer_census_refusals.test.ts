import { describe, it, expect } from 'vitest'
import { spawnSync } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'

// ═══════════════════════════════════════════════════════════════════════════════════════
// REGRESSION COVERAGE FOR writer_substep_census.py — Nirmāṇa M0-T43 (SQ-04)
//
// WHAT DEFECT THIS PINS (M0-T28 / F-2). The module used to pin
// `ROOT = pathlib.Path('/Users/Dev/Vibe-Coding/Apps/Madhav')` — one developer's absolute
// path, baked in when this was a run-once script. On any other machine (CI, a second
// checkout, a container) that directory does not exist, so `BASE.rglob` yielded nothing,
// `census()` reported `files_scanned=0, n_registrations=0`, and `registered_asset_ids()`
// HANDED BACK AN EMPTY SET WITHOUT RAISING.
//
// Every consumer tests membership (`aid in code_writers`), so an empty set does not read as
// "unknown" downstream — it reads as "no asset has a registered writer", which makes
// `_bound_class()` return `not-a-build` for all 128 assets and EXEMPTS THE ENTIRE CATALOGUE
// from the §8.3 item 5 efficiency gate, silently and looking entirely normal. A green from a
// detector that never ran: CLAUDE.md §N.8's defect class exactly, and the same shape as D-1's
// disarmed heartbeat.
//
// The two pre-existing guards (unresolved @register args, parse errors) could not catch it:
// both require something to have been PARSED, and neither can fire when there is nothing to
// parse at all. So the fix has two halves, and this file tests both:
//   (a) the root is derived from `__file__`, with NIRMANA_REPO as an OVERRIDE ONLY;
//   (b) an empty scan is LOUD — the derived accessors raise rather than emit a value.
//
// WOULD THESE HAVE CAUGHT THE ORIGINAL BUG? Case A is the bug verbatim: point the module at
// a checkout with no writer tree and demand that it refuse. Under the pre-M0-T28 code it
// returned `set()` and exited 0. Case E pins the other half — that the default root really is
// self-derived, which is what stops the failure from needing NIRMANA_REPO to be discovered.
//
// NO DATABASE, NO IMPORTS EXECUTED: the module is pure `ast.parse` over source text (D-9).
// ═══════════════════════════════════════════════════════════════════════════════════════

const REPO_ROOT = path.resolve(__dirname, '../../..')
const CONTROL = path.join(REPO_ROOT, '00_ARCHITECTURE/control')
const PY = process.env.PYTHON ?? 'python3'

/** Import the census under a chosen NIRMANA_REPO and call one accessor. */
function callAccessor(fn: string, nirmanaRepo?: string) {
  const prog = `
import json, sys
sys.path.insert(0, ${JSON.stringify(CONTROL)})
import writer_substep_census as c
try:
    v = getattr(c, ${JSON.stringify(fn)})()
    out = {"raised": False, "n": len(v),
           "sample": sorted(v)[:3] if isinstance(v, set) else sorted(v.keys())[:3],
           "root": str(c.ROOT), "base": str(c.BASE)}
except SystemExit as e:
    out = {"raised": True, "message": str(e), "root": str(c.ROOT), "base": str(c.BASE)}
print(json.dumps(out))
`
  const env = { ...process.env, PYTHONDONTWRITEBYTECODE: '1' } as Record<string, string>
  if (nirmanaRepo === undefined) delete env.NIRMANA_REPO
  else env.NIRMANA_REPO = nirmanaRepo
  const r = spawnSync(PY, ['-c', prog], {
    cwd: REPO_ROOT,
    encoding: 'utf8',
    timeout: 180_000,
    env,
  })
  if (r.error) {
    throw new Error(
      `could not run ${PY}: ${r.error.message}. This file deliberately does not skip on a ` +
        `missing interpreter — a skipped guard test is an unearned green (§N.8).`,
    )
  }
  if (r.status !== 0) throw new Error(`driver failed (${r.status}):\n${r.stderr}`)
  return JSON.parse(r.stdout.trim().split('\n').pop() as string)
}

/** A throwaway checkout root. `withTree` decides whether platform/python-sidecar exists. */
function fakeRoot(opts: { withTree?: boolean; writer?: string } = {}): string {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'm0t43-census-'))
  if (opts.withTree) {
    const base = path.join(dir, 'platform/python-sidecar')
    fs.mkdirSync(base, { recursive: true })
    if (opts.writer) fs.writeFileSync(path.join(base, 'w.py'), opts.writer, 'utf8')
  }
  return dir
}

const ACCESSORS = [
  'registered_asset_ids',
  'substep_truth_by_asset',
  'writer_file_by_asset',
  'resume_mechanism_by_asset',
]

describe('an empty census RAISES rather than emitting a value', () => {
  it('A — a root with NO writer tree at all: every derived accessor refuses', () => {
    // F-2 verbatim. Pre-M0-T28 this returned an empty set and a caller read it as
    // "nothing builds any asset". The `base_exists` branch also has to name WHERE it
    // looked — an accessor that raises without saying which path it searched sends the
    // next reader hunting for a defect in the parser rather than in the root.
    const root = fakeRoot()
    for (const fn of ACCESSORS) {
      const o = callAccessor(fn, root)
      expect(o.raised, `${fn} must refuse over a rootless checkout`).toBe(true)
      expect(o.message).toMatch(/writer tree does not exist/)
      expect(o.message).toContain('platform/python-sidecar')
      expect(o.root).toBe(fs.realpathSync(root))
    }
  }, 180_000)

  it('B — a writer tree that EXISTS but is empty: still refuses, by the other branch', () => {
    // A distinct code path, and the one the `base_exists` check cannot reach: the directory
    // is there and `files_scanned` is 0. Testing only case A would let this branch be
    // deleted — and it is the branch that fires on a checkout that is merely INCOMPLETE
    // (a sparse clone, a partially-restored worktree) rather than obviously wrong.
    const root = fakeRoot({ withTree: true })
    for (const fn of ACCESSORS) {
      const o = callAccessor(fn, root)
      expect(o.raised, `${fn} must refuse over an empty writer tree`).toBe(true)
      expect(o.message).toMatch(/scanned 0 file/)
      // and it says WHY an empty answer is not a safe answer, in the message itself
      expect(o.message).toMatch(/nothing builds any asset|would be EMPTY/)
    }
  }, 180_000)

  it('C — a tree with files but NO @register decorator: still refuses', () => {
    // `files_scanned` is non-zero here and `n_registrations` is zero, which is the third
    // conjunct of the same branch. A mutation that checks only `files_scanned` passes A and
    // B and dies here.
    const root = fakeRoot({ withTree: true, writer: 'class NotAWriter:\n    pass\n' })
    const o = callAccessor('registered_asset_ids', root)
    expect(o.raised).toBe(true)
    expect(o.message).toMatch(/found 0 @register decorator/)
  }, 180_000)

  it('D — the refusal is not universal: one real writer and the accessor returns it', () => {
    // The other boundary. Without this, `_assert_trustworthy` could be `raise` unconditionally
    // and A, B and C would all still pass while the census became unusable.
    const root = fakeRoot({
      withTree: true,
      writer:
        "from x import register\n\n@register('bg_probe_writer')\nclass W(WriterBase):\n" +
        '    def plan_substeps(self, ctx): ...\n    def run_substep(self, ctx, s): ...\n',
    })
    const ids = callAccessor('registered_asset_ids', root)
    expect(ids.raised).toBe(false)
    expect(ids.sample).toEqual(['bg_probe_writer'])
    // and the HEAVY shape is read as an override, not as WriterBase's own definition
    const substeps = callAccessor('substep_truth_by_asset', root)
    expect(substeps.raised).toBe(false)
    expect(substeps.n).toBe(1)
  }, 180_000)
})

describe('the repo root is derived from the file\'s own location', () => {
  it('E — with NIRMANA_REPO unset the census finds this checkout and is non-empty', () => {
    // The half of the F-2 fix that stops the failure from requiring an env var to avoid.
    // A regression to a hardcoded absolute path passes on the machine that authored it and
    // fails here on every other one — which is exactly what happened, and why the test has
    // to assert the RESOLVED root rather than merely that something was found.
    const o = callAccessor('registered_asset_ids')
    expect(o.raised).toBe(false)
    expect(o.root).toBe(fs.realpathSync(REPO_ROOT))
    expect(o.base).toBe(path.join(fs.realpathSync(REPO_ROOT), 'platform/python-sidecar'))
    expect(o.n).toBeGreaterThan(50)   // ~123 registrations live in this tree
  }, 180_000)

  it('F — NIRMANA_REPO remains an OVERRIDE, and cannot reintroduce a silent empty', () => {
    // The override is legitimate (pointing the census at another checkout) and must keep
    // working; what it must never do is buy back the silent failure. Both halves in one case.
    const root = fakeRoot({
      withTree: true,
      writer: "from x import register\n\n@register('ga_elsewhere')\nclass W: ...\n",
    })
    const ok = callAccessor('registered_asset_ids', root)
    expect(ok.raised).toBe(false)
    expect(ok.sample).toEqual(['ga_elsewhere'])
    expect(callAccessor('registered_asset_ids', fakeRoot()).raised).toBe(true)
  }, 180_000)
})

describe('census() itself does NOT raise — the diagnostic channel stays open', () => {
  it('G — over a rootless checkout census() returns a record saying where it looked', () => {
    // Deliberate asymmetry, and it is load-bearing: the C-23 guard calls `census()` and
    // inspects `files_scanned` / `n_registrations` / `base_exists` to write its
    // `not_checkable` provenance. If a well-meaning change made `census()` raise too, that
    // guard would CRASH where it is supposed to report "not checkable" — trading a silent
    // green for a loud unavailability, which is a different defect, not a fix.
    const prog = `
import json, sys
sys.path.insert(0, ${JSON.stringify(CONTROL)})
import writer_substep_census as c
r = c.census()
print(json.dumps({k: r[k] for k in
    ("files_scanned", "n_registrations", "scan_root", "scan_base", "base_exists")}))
`
    const r = spawnSync(PY, ['-c', prog], {
      cwd: REPO_ROOT,
      encoding: 'utf8',
      timeout: 180_000,
      env: { ...process.env, NIRMANA_REPO: fakeRoot(), PYTHONDONTWRITEBYTECODE: '1' },
    })
    expect(r.status).toBe(0)
    const rec = JSON.parse((r.stdout ?? '').trim().split('\n').pop() as string)
    expect(rec.files_scanned).toBe(0)
    expect(rec.n_registrations).toBe(0)
    expect(rec.base_exists).toBe(false)
    // "I scanned 0 files under <path>" is a true and useful thing for the raw measurement to
    // report; the refusal belongs in the derived accessors, which have no channel for
    // "I don't know".
    expect(rec.scan_base).toContain('platform/python-sidecar')
  }, 180_000)
})
