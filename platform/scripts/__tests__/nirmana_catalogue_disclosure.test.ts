import { describe, it, expect, beforeAll } from 'vitest'
import { spawnSync } from 'child_process'
import fs from 'fs'
import os from 'os'
import path from 'path'

// ═══════════════════════════════════════════════════════════════════════════════════════
// REGRESSION COVERAGE FOR THE PER-RULE DISCLOSURE MECHANISM — Nirmāṇa M0-T43 (SQ-04)
//
// WHAT DEFECT THIS PINS (F-T36-3). Sixteen `deferred_rule_disclosures` entries were written
// to satisfy ADHIKĀRIN D-30 part 4, and NOTHING READ THEM: severity was a constant typed
// into the RULES table. A disclosure could be written, look correct, and change no outcome —
// so the precondition for flipping the CI gate to blocking was satisfiable on paper and
// inert in fact. M0-T40 made severity computed FROM the disclosures, under three refusals.
// This file drives those three refusals from outside the module.
//
// THE THREE REFUSALS, each with the regression it stops:
//   1. NEVER GREEN     — a disclosure may demote a gate, never change a rule's `status` or
//                        hide a violation. The tempting "simplification" is to mark the rule
//                        pass; that is D-12 part 4's exact prohibition.
//   2. NEVER WHOLESALE — the demotion holds only while EVERY current violation is inside the
//                        itemised `covers`. One new violation and the gate is back. The
//                        regression is a backlog silently GROWING under an old disclosure.
//   3. AUTHORITY       — a demotion takes effect only when `authorised_by` names a decision
//                        that EXISTS in DECISIONS.jsonl and was authored by ADHIKĀRIN.
//                        Catalogue-gate disposition is a charter G-power; an entry any agent
//                        can type is not an authority record. Without this, a KĀRAKA demotes
//                        a gate by writing a file, which is charter H3.
//
// WHY NOT JUST `--self-test`. Those probes live inside the module and are exercised only by
// nirmana-m0-guards.yml, which is `continue-on-error: true` and does not fire on the campaign
// branch. A commit that deletes a probe case leaves `--self-test` green with the coverage
// gone. This file runs in the blocking unit-test job and asserts from outside.
//
// HOW IT DRIVES THE MODULE. A generated python driver imports the guard and calls its public
// functions with the module's declared test-injection points (`_RULE_DISCLOSURE_DOC`,
// `_DECISION_INDEX`). No database: `run_rules` takes an in-memory Snapshot. The shipped
// residuals file is never modified — the injection point exists precisely so a test need not
// write to a governance artefact to exercise the reader.
// ═══════════════════════════════════════════════════════════════════════════════════════

const REPO_ROOT = path.resolve(__dirname, '../../..')
const GUARD_DIR = path.join(REPO_ROOT, 'platform/scripts/governance')
const PY = process.env.PYTHON ?? 'python3'

const DRIVER = `
import json, sys, pathlib
sys.path.insert(0, ${JSON.stringify(GUARD_DIR)})
import check_asset_catalogue_contract as cc

spec = json.loads(sys.argv[1])

decisions = cc.decision_index(force=True)
adhikarin = sorted(k for k, v in decisions.items() if v.get("agent") == "ADHIKARIN")
if not adhikarin:
    print(json.dumps({"error": "no ADHIKARIN decision in the shipped ledger"})); sys.exit(0)
real = adhikarin[0]

if spec.get("inject_decision"):
    decisions = dict(decisions, **{spec["inject_decision"]["id"]:
                                   {"agent": spec["inject_decision"]["agent"]}})
    cc._DECISION_INDEX = decisions

assets = [
    {"asset_id": "zz_probe_one", "layer": "ganita", "asset_kind": "data",
     "asset_type": "data", "count_sql": None, "catalog_status": "CURRENT",
     "is_active": True, "scope": "global", "depends_on": []},
    {"asset_id": "ga_probe_two", "layer": "ganita", "asset_kind": "data",
     "asset_type": "data", "count_sql": None, "catalog_status": "CURRENT",
     "is_active": True, "scope": "global", "depends_on": []},
]
if spec.get("extra_violation"):
    assets.append({"asset_id": "qq_probe_three", "layer": "ganita", "asset_kind": "data",
                   "asset_type": "data", "count_sql": "SELECT 1",
                   "catalog_status": "CURRENT", "is_active": True, "scope": "global",
                   "depends_on": []})

ent = None
if spec.get("disclosure") is not None:
    ent = {"rule": "C-01", "owner": "m0t43 test", "deferred_to": "R5",
           "disclosed_via": "M0-T43 test", "reason": "regression fixture",
           "disclosed_at": "2026-08-23", "disclosed_by": "M0-T43",
           "gating_effect": "non_gating", "authorised_by": real,
           "covers": ["zz_probe_one"]}
    over = dict(spec["disclosure"])
    if over.get("authorised_by") == "__REAL__":
        over["authorised_by"] = real
    for k, v in over.items():
        if v is None and k in ("covers", "authorised_by"):
            ent.pop(k, None)
        else:
            ent[k] = v
doc = {"deferred_rule_disclosures": {"C-01": ent}} if ent is not None else {}
cc._RULE_DISCLOSURE_DOC = doc

out = {"real_decision": real}
if spec.get("expect_load_error"):
    try:
        cc.load_rule_disclosures()
        out["load"] = "ACCEPTED"
    except cc.GuardError as e:
        out["load"] = "GuardError"
        out["load_message"] = str(e)
    print(json.dumps(out)); sys.exit(0)

results = cc.run_rules(cc.Snapshot({"assets": assets}))
summary = cc.summarise(results)
c01 = results["C-01"]
out.update({
    "c01_status": c01["status"],
    "c01_violations": c01["violation_count"],
    "c01_violation_ids": [cc.violation_identity(v) for v in c01["violations"]],
    "c01_declared": c01.get("declared_severity"),
    "c01_effective": c01.get("effective_severity"),
    "c01_disclosure": c01.get("disclosure"),
    "c01_gates": "C-01" in summary["blocking_failures"],
    "c05_gates": "C-05" in summary["blocking_failures"],
    "disclosed_non_gating": summary["disclosed_non_gating_failures"],
})
print(json.dumps(out))
`

let driverPath: string
beforeAll(() => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'm0t43-disc-'))
  driverPath = path.join(dir, 'driver.py')
  fs.writeFileSync(driverPath, DRIVER, 'utf8')
})

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function drive(spec: Record<string, unknown>): any {
  const r = spawnSync(PY, [driverPath, JSON.stringify(spec)], {
    cwd: REPO_ROOT,
    encoding: 'utf8',
    timeout: 180_000,
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
  })
  if (r.error) {
    throw new Error(
      `could not run ${PY}: ${r.error.message}. This file deliberately does not skip on a ` +
        `missing interpreter — a skipped guard test is an unearned green (§N.8).`,
    )
  }
  if (r.status !== 0) throw new Error(`driver failed (${r.status}):\n${r.stderr}\n${r.stdout}`)
  const out = JSON.parse(r.stdout.trim().split('\n').pop() as string)
  if (out.error) throw new Error(out.error)
  return out
}

describe('a disclosure is NEVER a green (D-12 part 4)', () => {
  it('A — control: with no disclosure at all, C-01 and C-05 both gate', () => {
    // Without this the whole file could pass over a fixture that never violated anything.
    const o = drive({})
    expect(o.c01_status).toBe('fail')
    expect(o.c01_violations).toBe(1)
    expect(o.c01_effective).toBe('BLOCKING')
    expect(o.c01_gates).toBe(true)
    expect(o.c05_gates).toBe(true)
  }, 180_000)

  it('B — an authorised, itemised, fully-covering disclosure demotes the GATE and nothing else', () => {
    // The mechanism working. Note what is asserted alongside the demotion: status is still
    // `fail` and the violation is still counted and still named. A refactor that "simplifies"
    // this by marking the rule pass — the obvious way to make a dashboard look better — turns
    // this test red on three separate assertions, not one.
    const o = drive({ disclosure: {} })
    expect(o.c01_status).toBe('fail')
    expect(o.c01_violations).toBe(1)
    expect(o.c01_violation_ids).toEqual(['zz_probe_one'])
    expect(o.c01_declared).toBe('BLOCKING')
    expect(o.c01_effective).toBe('DISCLOSED_NON_GATING')
    expect(o.c01_gates).toBe(false)
    expect(o.disclosed_non_gating).toContain('C-01')
    // …and the demotion is confined to the rule it names. A disclosure for C-01 that
    // silenced C-05 would be a wholesale silencer wearing an itemised disguise.
    expect(o.c05_gates).toBe(true)
  }, 180_000)

  it('C — the severity is COMPUTED from the disclosure, not a constant (the F-T36-3 defect itself)', () => {
    // Before M0-T40, `effective_severity` did not exist and severity was a constant in the
    // RULES table: entries were written, read by nothing, and changed no outcome. The pair
    // A-vs-B above differs ONLY in the disclosure document, so a return to a constant makes
    // one of them fail whichever constant is chosen. Stated as its own case because this —
    // not the demotion — is the regression the mechanism was built for.
    expect(drive({}).c01_effective).toBe('BLOCKING')
    expect(drive({ disclosure: {} }).c01_effective).toBe('DISCLOSED_NON_GATING')
  }, 180_000)
})

describe('a disclosure covers what it NAMES — a backlog may be paid down, never silently grown', () => {
  it('D — one violation outside `covers` and the rule gates again at its declared severity', () => {
    const o = drive({ disclosure: {}, extra_violation: true })
    expect(o.c01_violations).toBe(2)
    expect(o.c01_effective).toBe('BLOCKING')
    expect(o.c01_gates).toBe(true)
    // and it says WHICH row escaped the disclosure, not merely that one did
    expect(o.c01_disclosure.uncovered_violations).toEqual(['qq_probe_three'])
  }, 180_000)

  it('E — a `covers` list that names nothing present buys nothing', () => {
    // The stale-disclosure case: the entry survives, the violation it named has been repaired
    // and a different one has appeared. Coverage is computed against the CURRENT violations,
    // so an out-of-date list cannot carry a new failure.
    const o = drive({ disclosure: { covers: ['some_asset_repaired_long_ago'] } })
    expect(o.c01_effective).toBe('BLOCKING')
    expect(o.c01_gates).toBe(true)
  }, 180_000)
})

describe('an entry cannot demote a rule without naming a decision that exists under ADHIKĀRIN', () => {
  it('F — `authorised_by` naming a decision id nobody ever recorded ⇒ no effect', () => {
    // "A KĀRAKA cannot demote a gate by writing a file." Without this detector the whole
    // mechanism is a free-text field, and charter H3 is one edit away.
    const o = drive({ disclosure: { authorised_by: 'D-NO-SUCH-RULING' } })
    expect(o.c01_effective).toBe('BLOCKING')
    expect(o.c01_gates).toBe(true)
    expect(JSON.stringify(o.c01_disclosure.notes)).toMatch(/not a decision id present/i)
  }, 180_000)

  it('G — a REAL decision id authored by someone other than ADHIKĀRIN ⇒ no effect', () => {
    // The second conjunct, and the one with no natural counter-example in the shipped ledger
    // (which is currently 100% ADHIKĀRIN). A conjunct with no counter-example is an untested
    // conjunct, so one is injected rather than skipped past. A mutation that checks only
    // "the id exists" survives F and dies here.
    const o = drive({
      disclosure: { authorised_by: 'D-M0T43-NOT-ADHIKARIN' },
      inject_decision: { id: 'D-M0T43-NOT-ADHIKARIN', agent: 'KARAKA' },
    })
    expect(o.c01_effective).toBe('BLOCKING')
    expect(o.c01_gates).toBe(true)
    expect(JSON.stringify(o.c01_disclosure.notes)).toMatch(/not ADHIK/)
  }, 180_000)

  it('H — the ADHIKĀRIN id the other cases cite is real, so F and G are not passing by accident', () => {
    // If the shipped ledger stopped parsing, every case above would report BLOCKING for the
    // wrong reason and the file would be green while testing nothing.
    const o = drive({ disclosure: { authorised_by: '__REAL__' } })
    expect(o.real_decision).toMatch(/^D-/)
    expect(o.c01_effective).toBe('DISCLOSED_NON_GATING')
  }, 180_000)
})

describe('an incomplete demotion is REFUSED loudly, never applied partially', () => {
  it('I — gating_effect="non_gating" with no `covers` ⇒ GuardError', () => {
    // Without both required fields the entry would silence the rule wholesale. The refusal
    // is an exception, not a downgrade to "recorded, no effect": a half-written demotion is
    // an authoring mistake that must be seen, not absorbed.
    const o = drive({ disclosure: { covers: null }, expect_load_error: true })
    expect(o.load).toBe('GuardError')
    expect(o.load_message).toMatch(/covers/)
  }, 180_000)

  it('J — gating_effect="non_gating" with no `authorised_by` ⇒ GuardError', () => {
    const o = drive({ disclosure: { authorised_by: null }, expect_load_error: true })
    expect(o.load).toBe('GuardError')
    expect(o.load_message).toMatch(/authorised_by/)
  }, 180_000)

  it('K — a disclosure that claims NO gating effect loads fine and changes nothing', () => {
    // The other boundary, and the state all sixteen shipped entries are actually in. A
    // validator that rejected these would make the honest, effect-free disclosure
    // unwritable — which is the form the campaign is currently using.
    const o = drive({ disclosure: { gating_effect: 'none' } })
    expect(o.c01_effective).toBe('BLOCKING')
    expect(o.c01_gates).toBe(true)
    expect(o.c01_disclosure.count).toBe(1)
    expect(o.c01_disclosure.effect).toBe('none')
  }, 180_000)
})

describe('the shipped governance artefacts still validate', () => {
  it('L — `--self-test` exits 0 (the module\'s own probes, from the blocking test job)', () => {
    const r = spawnSync(
      PY,
      [path.join(GUARD_DIR, 'check_asset_catalogue_contract.py'), '--self-test'],
      { cwd: REPO_ROOT, encoding: 'utf8', timeout: 180_000 },
    )
    expect((r.stdout ?? '') + (r.stderr ?? '')).toMatch(/self-test OK/)
    expect(r.status).toBe(0)
  }, 180_000)
})
