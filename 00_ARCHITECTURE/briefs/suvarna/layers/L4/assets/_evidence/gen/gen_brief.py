#!/usr/bin/env python3
"""Renders one A.L4 asset brief from authored content + receipts."""
import subprocess, re, json
from gen_common import *

TEMPLATE_REV = 'ASSET_ELEVATION_TEMPLATE_v2_0.md at 2289778be (campaign/nikasha-test; DRAFT_PENDING_REVIEW)'
LAYER_INSTANCE = '00_ARCHITECTURE/briefs/suvarna/layers/L4/L4_LAYER_INSTANCE_v1_0.md (1.1, PROVISIONAL)'
CENSUS_USED = ("fresh census `/Users/Dev/suvarna-evidence/census_fresh/1e5781a/census_L4.json` (generated 2026-10-02T10:12:59+05:30, chart 482012f1, "
               "inspector 1e5781a at REGISTRY_REVISION 10; outside the repo) compared with the repo's saved census "
               "`00_ARCHITECTURE/briefs/suvarna/layers/census/census_L4.json` (2026-09-30T20:23:50+05:30, inspector 2a78ec64d). "
               "Main's inspector is now at REGISTRY_REVISION 15: the offline rollup below applies its rules to the fresh census; no live re-measure was run.")


def seed_line(a):
    r = subprocess.run(['grep', '-n', f"asset_id: '{a}'", WT + '/platform/scripts/seed/asset_registry_seed.ts'], capture_output=True, text=True)
    m = re.match(r'(\d+):', r.stdout.strip().split('\n')[0]) if r.stdout.strip() else None
    return m.group(1) if m else None


def reg_line(a):
    p = WT + '/' + WRITER[a]
    r = subprocess.run(['grep', '-n', '-E', '^@register', p], capture_output=True, text=True)
    m = re.match(r'(\d+):', r.stdout.strip().split('\n')[0]) if r.stdout.strip() else None
    return m.group(1) if m else None


def render(c):
    c = fixall(c)
    a = c['id']
    d = asset_data(a)
    reg = d['registry']
    thr = d['throughput']
    f = fresh()[a]
    live = d['live_count'].split('\n')[1] if isinstance(d.get('live_count'), str) and '\n' in d['live_count'] else d.get('live_count')
    tabs = d['tables']
    rbc = {}
    for t, td in tabs.items():
        rbc[t] = '; '.join(f"{r['chart_id'][:8]}={r['n']}" for r in td['rows_by_chart'])
    rd_md, rd_n = readers_md(a)
    seed = seed_line(a)
    L = []
    w = L.append
    gaps = c['gaps']
    ledger_ids = c.get('ledger_ids', [])
    w('---')
    w(f'asset_id: {a}')
    w('layer: L4 Phala (ph_*)')
    w('artifact: ASSET_ELEVATION_BRIEF')
    w('version: "1.0-provisional"')
    w('status: "PROVISIONAL - until J1; may register gaps, may not certify"')
    w('produced_by: track-a-l4 (worker under Exec Suvarna)')
    w(f'produced_on: {PRODUCED}')
    w('plan_item: A.L4 (briefs, dispositions, designs)')
    w(f'census_revision_used: "{CENSUS_USED}"')
    w(f'template_revision: "{TEMPLATE_REV}"')
    w(f'layer_instance: "{LAYER_INSTANCE}"')
    w(f'base_commit: "main {BASE}"')
    w(f'disposition: "{c["disp_code"]}"')
    w('disposition_proposal_approver: "Steward (G16); any output change to SS (R5)"')
    w(f'disposition_value: {c["disp_value"]}')
    w(f'risk_class: "{c["risk"]}"')
    w('decisions_applied: "none - SS has not answered the A.L4 questions (INDEX section 7); all dispositions and fix designs are proposals"')
    w('ss_questions: [' + ', '.join(c['qs']) + ']')
    w('track_i_items: [' + ', '.join(c['tis']) + ']')
    w('ledger_gap_ids: [' + ', '.join(ledger_ids) + ']')
    w('---')
    w(f'# {a} - {c["title"]}')
    w('')
    w('> **PROVISIONAL - until J1; may register gaps, may not certify.** Every figure below comes from a stated read-only query (suvarna_reader SELECTs on 2026-10-03, receipts under `/Users/Dev/suvarna-evidence/A_L4/data/`), from the census, from the repository at main `' + BASE + '` (file:line), or from running the asset\'s pure engine functions locally with no database. Where something could not be determined it says so. Nothing here certifies a gate, approves a disposition or changes an asset.')
    w('')
    w('## 0 - Identity: what the asset is')
    w('')
    w(c['identity'])
    w('')
    w('| field | value | source |')
    w('|---|---|---|')
    w(f"| kind | registry `asset_kind={reg['asset_kind']}`, `asset_type={reg['asset_type']}`, `scope={reg['scope']}`, `domain={reg['domain']}`, `rung={reg['rung']}`; role per L4 layer instance TG-L4-024: not assigned by any tier | `asset_registry` row, read 2026-10-03 |")
    w(f"| registry seed row | `platform/scripts/seed/asset_registry_seed.ts:{seed}` (live may differ by migration) | seed |")
    w(f"| writer / `@register` | `{WRITER[a]}:{reg_line(a)}`; engine `{ENGINE[a]}`; registry `has_writer={reg['has_writer']}` | code |")
    w(f"| target table(s) | {', '.join('`' + t + '`' for t in TABLES[a])} | registry `target_table` / `count_sql` |")
    w(f"| live rows (canonical chart) / floor / build record | {live} / {reg['target_floor'] if reg['target_floor'] is not None else 'none'} / `rows_written={thr['rows_written']}`; rows per chart in the table(s): {'; '.join(k + ': ' + v for k, v in rbc.items())} | `count_sql` run read-only; `asset_throughput`; table group-by |")
    w(f"| state / last built | `{thr['state']}` / {thr['last_built_at'][:19]} UTC (run `cbd6ea44`); `built_against_writer_hash={thr['built_against_writer_hash']}` | `asset_throughput` |")
    w(f"| catalog_status | {reg['catalog_status']} | registry |")
    w(f"| depends_on (declared, live) | {', '.join('`' + x + '`' for x in reg['depends_on'])} | `asset_registry.depends_on` |")
    w(f"| depends_on vs what the code reads | {c['edges']} | code (file:line) + fresh census `Build.dag` |")
    br = f['blocking_radius']
    w(f"| blast radius | declared dependents direct {br['direct']} / transitive {br['transitive']} (active assets, every layer) | fresh census `blocking_radius` |")
    w(f"| code readers outside the asset (non-test py/ts/tsx, {rd_n} files) | {rd_md} | `grep -rlw` over platform/python-sidecar, platform/src, platform-mcp/src at `{BASE}` (tests, generated and migrations excluded) |")
    w(f"| served surface | {c['served']} | code |")
    w(f"| role / scoring mode | manifestation-family asset of L4 Phala (T2 section 6.5); census `scoring: contribution`; {c['role_note']} | tiers + census |")
    w(f"| invalidation / FK | {c['fk']} | `pg_constraint` read 2026-10-03 |")
    w('')
    w('## 1 - Measured state and the nine gates')
    w('')
    w('### 1.1 - Live state on the canonical chart (read-only, 2026-10-03)')
    w('')
    for b in c['live_bullets']:
        w('- ' + b)
    w('')
    w(f"Build history for this asset (all charts, `build_run_assets`): {runs_line(d)}; the last complete canonical-chart run is `cbd6ea44` (2026-08-13), and the 26+ `error/blocked_dependency` rows are cascade skips, not writer errors. The only non-cascade errors on record: " + c['hist_errors'])
    w('')
    w('### 1.2 - Stored rows versus current code')
    w('')
    w('Commits touching this asset\'s writer or engine AFTER its last build (2026-08-13 01:16 UTC): ' + stored_vs_code(a) + '.')
    w('')
    w(c['stored_vs_code'])
    w('')
    w('### 1.3 - Census cells (fresh run, compared with the saved run)')
    w('')
    w('Census used: ' + CENSUS_USED)
    w('')
    w(census_section(a))
    w('')
    w('### 1.4 - Earned-signal (N.8), narration-fidelity (N.7) and honest-null audit of this asset\'s flags and verdicts')
    w('')
    w(md_table(['field / claim', 'what it claims', 'what code path could make it read false', 'finding'], c['audit']))
    w('')
    w('### 1.5 - UUID chart_id check (the bo_*/ph_* adapter defect)')
    w('')
    w(c['uuid'])
    w('')
    w('## 2 - Gaps: which are real, which are detector or definition gaps')
    w('')
    w('Class vocabulary: **real** = a shortfall in code, rows, registry row or served surface; **real-stored** = the CURRENT code already fixes it but the stored rows predate the fix (cured by a rebuild, not by an edit); **design** = needs an SS or acharya decision; **detector** = the instrument is absent or its definition is the open point; **history** = a recorded past outcome no edit can change; **information** = Count/Cost/Complete/Reach, never a blocker; **opportunity** = beyond the requirement.')
    w('')
    w(md_table(['gap id', 'gate', 'class', 'note (evidence)'], [[g[0], g[1], g[2], g[3]] for g in gaps]))
    w('')
    w('## 3 - Disposition')
    w('')
    w(f"DISPOSITION: {c['disp_value']}")
    w('')
    w(f"EVIDENCE_POINTER: 00_ARCHITECTURE/briefs/suvarna/layers/L4/assets/{a}_ELEVATION_BRIEF_v1_0.md (sections 1-4); receipts `_evidence/` (data/, upstream_receipts.json, rollup_L4.json, offline_checks.txt, rect_diag.txt); census `layers/census/census_L4.json` + fresh census `census_fresh/1e5781a/census_L4.json`")
    w('')
    w(f"**{c['disp_code']}.** " + c['disp_text'])
    w('')
    w('Approver under Track A brief section 10: **Steward (G16)** for keep/qualify/enrich; **SS** for any output change (R5). No disposition is applied by this brief.')
    w('')
    w('## 4 - Fix designs (one per real gap; anything marked `needs production rebuild` or `needs migration` is a REVIEW item for Strategic Suvarna)')
    w('')
    for i, fd in enumerate(c['fds'], 1):
        w(f'### FD-{i} - {fd["title"]}')
        w('')
        w(f"- **Answers:** {fd['answers']}")
        w(f"- **Change:** {fd['change']}")
        w(f"- **Files / declaration / migration:** {fd['files']}")
        w(f"- **Failing-first test and mutation:** {fd['test']}")
        w(f"- **Output change:** {fd['output']}")
        w(f"- **Blast radius:** {fd['blast']}")
        w(f"- **Rebuild:** {fd['rebuild']}")
        w(f"- **Gate it moves:** {fd['gate']}")
        w(f"- **Fix class:** {fd['cls']}; **risk class:** {fd['risk']}; **buildable before J1:** {fd['j1']}")
        w(f"- **Decision:** {fd['decision']}")
        w('')
    w('### Shared fixes that apply to this asset (full design in `INDEX.md`)')
    w('')
    for cf, why in c['cfs']:
        w(f'- **{cf}** - *this asset:* {why}')
    w('')
    w('## 5 - Semantic fingerprint contract (for the rebuild plan)')
    w('')
    w(c['fingerprint'])
    w('')
    w('## 6 - Preserved kernel, carriage check, opportunities')
    w('')
    w('- **Preserved kernel:** ' + c['kernel'])
    w('- **Carriage check (T4 4.1; one only):** ' + c['carriage'])
    w('- **By design, stated and not flagged:** ' + c['by_design'])
    w('- **Opportunities (never blocking):** ' + c['opps'])
    w('')
    w('## 7 - Decisions applied, questions for SS, Track I items arising')
    w('')
    w('No decision has been applied: SS has not yet answered the A.L4 questions. This brief raises:')
    w('')
    for q in c['questions']:
        w(f'- **{q[0]}** - {q[1]}')
    w('')
    w('**Track I items arising (see INDEX section 8):** ' + ', '.join(c['tis']) + '.')
    w('')
    return '\n'.join(L)
