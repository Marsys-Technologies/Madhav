#!/usr/bin/env python3
"""
NIRMĀṆA ASSET CONTROL WORKBOOK v4.1 generator — Track M0, §16.

Single-chart scope (native chart 482012f1-…, plus the chart-independent shared substrate).
Cross-chart columns for Abhinandan / "Chart 3" are RETIRED from this programme (scope
ruling, NIRMANA_ELEVATION_PLAN_v4_0.md) and dropped here.

This script does not duplicate the measurement/derivation pipeline — it imports fetch(),
scan_code(), consumer_map(), build_rows(), the styling helpers, DEFECTS, INFRA and roadmap()
from build_asset_control_workbook.py (the v3.0 generator), which build_rows() now also
enriches with the §15 six v4.1 columns (domain/rung/within-rung wave/continuation class/
rehearsal partition/timeout source — see asset_plans.derive_v41_columns). This keeps the two
workbooks, and the regenerated plan-file §15 markdown, single-sourced (no re-derivation, no
disagreement possible).

Read-only against the database: every query in the imported fetch()/build_rows() pipeline is
a SELECT. This script performs no DB writes, no migration, no asset_registry mutation.

    python3 00_ARCHITECTURE/control/build_control_workbook_v4_1.py
"""
import collections
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font
from openpyxl.utils import get_column_letter

import build_asset_control_workbook as v3
from build_asset_control_workbook import (
    ACCENT, INK, HDR, TIER_FILL, STATE_FONT, PR_FONT, SEV_FONT, BORDER,
    CHARTS, LAYER_ROLE, THESIS, DEFECTS, INFRA, roadmap,
    head, widths, emit_plan_markdown,
)

ROOT = v3.ROOT
V4_PLAN_PATH = ROOT / '00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v4_0.md'
V3_PLAN_PATH = ROOT / '00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v3_0.md'
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
    ROOT / '00_ARCHITECTURE/control/NIRMANA_ASSET_CONTROL_WORKBOOK_v4_1.xlsx'

NATIVE_LABEL = CHARTS[0][1]  # 'Abhisek (native)'

RUNG_LAYER = [('R0', 'L0'), ('R1', 'L1'), ('R2', 'L2'), ('R3', 'L3'), ('R4', 'L4'), ('R5', 'L5')]

# §1.9 loophole register (v4.0 plan) folded into the Defect Register as D-17…D-28. Evidence
# strings are verbatim from the plan's L-01…L-12 table, code-citation preserved as-is.
LOOPHOLE_DEFECTS = [
    ('D-17', "The word \"global\" means three different things", 'MEDIUM',
     "`build_runs.scope='global'` means \"everything for this chart, L1–L5\" (`plan.ts:8,138`; "
     "the L0 GATE then strips brahmagyan, `runs/route.ts:166–170`). `asset_registry.scope="
     "'global'` means \"chart-independent singleton\" (`runner.py:465–467`). `/api/cockpit/"
     "refresh` treats `scope='global'` as \"every asset in the registry, L0 included\" "
     "(`refresh/route.ts:29–33`). Three semantics, one word, one product. [L-01]",
     'An operator or contributor cannot reason about "global" without knowing which of three '
     'call sites they are reading; the ambiguity is load-bearing in D-18/D-20/D-23.',
     'The rename to domain: shared|chart (I9) behind a compat window (§6).', 'M1'),
    ('D-18', 'A single shared asset cannot be rebuilt at all', 'HIGH',
     "`scope='asset'` on a shared asset → 403 \"Global assets must be built at scope=global\" "
     "(`runs/route.ts:81–93`) — but `scope='global'` excludes brahmagyan by the L0 GATE "
     "(`:166–170`), and `scope='layer'`+`brahmagyan` rebuilds all 40. Corollary: `mi_kula`/"
     "`mi_vistara` are rejected with the misleading code `FORBIDDEN_L0`. [L-02]",
     "The path the error message itself recommends is a dead end — the measured cause of the "
     "66-day bg_ephemeris_engine red being awkward to clear.",
     'Single-shared-asset rebuild path (§6.5), closing L-02.', 'M1'),
    ('D-19', 'Two runners, two contracts', 'HIGH',
     "Chart runs get build_runs row, DAG gating, substeps, watchdog timeouts, SSE events, F-01 "
     "verdicts. `--global-build` runs `global_runner.py`: no build_runs row, no dependency "
     "gating (`ORDER BY layer, sort_order`, `:84–91`), no substep support, no per-writer "
     "timeout, no cockpit visibility; unimplemented writers skipped as `deferred` with only a "
     "log line (`:155–158`). [L-03]",
     'The foundation substrate — the layer this programme must finish first — is built by the '
     'primitive runner.',
     "Single runner for both domains, global_runner.py retired (§6.4).", 'M1'),
    ('D-20', 'Shared writes are unguarded', 'HIGH',
     "A chart run holds only the chart advisory lock (`locks.py`) yet builds shared assets in "
     "its plan with `chart_id=None` (`runner.py:465–467`); a concurrent `--global-build` takes "
     "the `hashtext('global')` lock the chart run never takes. Global builds have no build_runs "
     "row, so the 409 RUN_ACTIVE gate (`runs/route.ts:95–120`) and `_MAX_CONCURRENT_RUNS` "
     "(`runner.py:813–822`) cannot see them. [L-04]",
     'Two runs can write the same shared table at the same time.',
     'Shared advisory-lock discipline with the shared_barrier (§6.4), closing L-04 by '
     'construction.', 'M1'),
    ('D-21', 'Substrate rebuilds leave the chart falsely green', 'CRITICAL',
     "`global_runner.py` never calls `propagate_downstream_staleness` — a shared asset rebuilt "
     "through it relights without marking a single downstream asset on the chart stale. The "
     "propagator itself updates only `WHERE chart_id = <run's chart>` (`staleness.py:90–99`), "
     "so `chart_id IS NULL` shared-domain downstream is never staled by anything. [L-05]",
     "Both halves bite a single-chart programme directly — the chart can read fully green while "
     "its substrate has silently drifted underneath it.",
     "The invalidation sweep's chart_id IS NULL branch; staleness propagation for shared runs "
     "(§6.7), closing both halves of L-05.", 'M1'),
    ('D-22', 'A zombie control plane is still wired to buttons', 'MEDIUM',
     "`/api/build/rebuild`, `/rebuild-all`, `/continue` insert rows into `build_events`/"
     "`builds` — vocabulary the orchestrator never reads (it polls `build_runs.stop/"
     "pause_requested_at`, `runner.py:213–225`). `pipeline/dispatcher.py` walks the legacy "
     "`build_dependencies` table (the A1..A22 scheme). `/api/build/pyramid-layers` reads a "
     "fourth status source, `pyramid_layers`. [L-06]",
     'An operator can click Rebuild and produce an event nothing will ever consume.',
     'Decommission register executed (§7.6), closing L-06.', 'M1'),
    ('D-23', '"Refresh" mutates state', 'HIGH',
     "`/api/cockpit/refresh` INSERTs `state='dormant'` throughput rows keyed (chart_id, "
     "asset_id) for every asset in scope — including chart-scoped shadow rows for shared "
     "assets, the exact spurious rows runner.py's own comment (`:834–837`) warns shadow the "
     "correct shared row in the stats query (`refresh/route.ts:44–52`). [L-07]",
     'The v3.0 "fake Refresh" finding is worse than fake: it is corrupting.',
     'Real reconciler or removal; the dormant-INSERT deleted (§7.6), closing L-07.', 'M1'),
    ('D-24', 'Pre-flight treats unknown as ready', 'MEDIUM',
     '`preflight()` skips any dependency with no throughput row — "absent entries are not our '
     'concern" (`plan.ts:248–250`). [L-08]',
     'A never-built upstream passes the plan-time gate and is caught only mid-run, converting a '
     'plannable refusal into a mid-run BLOCKED cascade.',
     "Pre-flight unknown-is-not-ready, the one-line inversion at plan.ts:249 (§10), closing "
     "L-08.", 'M1'),
    ('D-25', 'Asset-scope operations bypass the machinery', 'MEDIUM',
     "`computeWaves` returns `[[candidate]]` for scope='asset' (`plan.ts:283`); `preflight` "
     "checks only direct deps, no recursion (`:239`); `action='rebuild'` expands no downstream "
     "(`:396–399`). [L-09]",
     'A single-asset rebuild neither re-derives its consumers nor prices them.',
     'Run groups + the resolution preview closure (§6.5/§6.6).', 'M1'),
    ('D-26', 'action=\'cascade\' does not mean what an operator thinks', 'MEDIUM',
     "It plans the downstream of everything currently *stale* in scope (`plan.ts:364–376`) — "
     "not the downstream of the thing just rebuilt. Combined with L-09 there is no single "
     "operation meaning \"rebuild X and everything X feeds.\" [L-10]",
     'Operator intent and system behaviour diverge silently on the most consequential rebuild '
     'action.',
     "action='cascade' renamed and redefined per §6.6.", 'M1'),
    ('D-27', 'A chart-scoped action can destroy shared capital', 'CRITICAL',
     "clear-before-build on a scope that includes shared assets executes unscoped `DELETE FROM "
     "<table>` (`runs/route.ts:301–304`) inside an operation the operator initiated *for the "
     "chart*. Guarded only by force_l0 + super_admin — a courage check, not a semantic one. "
     "[L-11]",
     "A chart-scoped operator action can delete every chart's shared substrate in one "
     "keystroke.",
     'Structurally impossible under I11 (§6).', 'M1'),
    ('D-28', 'Nothing guarantees a run finishes', 'CRITICAL',
     "One-shot dispatch (`invokeRunJob`; no continuation on execution-ceiling death); default "
     "writer timeout 600s against measured 30h heavy builds unless writer_timeout_seconds is "
     "set (`runner.py:89`; set on ~2 of 128); substep resume machinery's completed_keys passed "
     "by NO caller (`asset_runner.py:397`); no transient-vs-deterministic error classification "
     "(proxy drops/`/tmp` restarts fail assets permanently); SIGTERM drain window 10s. [L-12]",
     'The 45.6% completion rate is the sum of these — the root-cause chain behind §1.10 (why a '
     'full chart build has never run end to end).',
     'The Run-to-Completion Contract (§7): deadline-aware continuation, completed_keys wired, '
     'error taxonomy + retry.', 'M2'),
]


def rung_board_rows(rows):
    """§16 Rung Board — honest current-state measurement, no rung opened, all Frozen=No."""
    out = []
    for rung, lx in RUNG_LAYER:
        sub = [x for x in rows if x['Layer'] == lx]
        n = len(sub)
        if n == 0:
            continue

        def state_of(x):
            return x['Global'] if x['Domain'] == 'shared' else x[NATIVE_LABEL]

        conformant_pct = round(100.0 * sum(1 for x in sub if x['Conformant'] == 'YES') / n, 1)
        lit_pct = round(100.0 * sum(1 for x in sub if state_of(x) in ('lit', 'service_ok')) / n, 1)
        integrity_pct = round(100.0 * sum(1 for x in sub if x['Integrity Check'] == 'yes') / n, 1)
        shared_n = sum(1 for x in sub if x['Domain'] == 'shared')
        out.append({
            'Rung': rung, 'Layer': lx, 'Assets': n, 'Shared assets': shared_n,
            'Conformant %': conformant_pct, 'Lit %': lit_pct, 'Integrity-passed %': integrity_pct,
            'Frozen': 'No', 'Current wave': 'not opened — Track M0 in progress',
            'Freeze record / notes': 'no freeze record — rung not yet opened (§8.3)',
        })
    return out


def main():
    d = v3.fetch()
    code = v3.scan_code()
    cons = v3.consumer_map(d['registry'])
    rows = v3.build_rows(d, code, cons)
    wb = Workbook()

    n_p0 = sum(1 for x in rows if x['Priority'].startswith('P0'))
    n_bad = sum(1 for x in rows if x['Conformant'] == 'no')
    n_nocons = sum(1 for x in rows if x['Consumers'] == '0' and x['Target Table'])
    shared_rows = [x for x in rows if x['Domain'] == 'shared']
    chart_rows = [x for x in rows if x['Domain'] == 'chart']

    # ---- Control ----
    ws = wb.active
    ws.title = 'Control'
    ws.sheet_view.showGridLines = False
    blocks = [
        ('NIRMĀṆA ASSET CONTROL WORKBOOK', 'title'),
        ('v4.1 — single-chart scope (native + shared substrate); Track M0 catalogue '
         'reconciliation, §15/§16', 'sub'),
        ('', ''),
        ('PROVENANCE', 'h'),
        ('Generated', 'Live production read at generation time — re-run this script, never hand-edit'),
        ('Generator', '00_ARCHITECTURE/control/build_control_workbook_v4_1.py'),
        ('Companion plan', '00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v4_0.md §15/§16'),
        ('Predecessor', 'NIRMANA_ASSET_CONTROL_WORKBOOK_v3_0.xlsx (three-chart; not overwritten)'),
        ('Status', 'PROPOSED — nothing in this workbook has been executed; Track M0 measurement/'
                   'reporting only, data-neutral by invariant I14'),
        ('', ''),
        ('SCOPE RULING', 'h'),
        ('Single-chart', 'The only chart in scope is 482012f1-710e-4a25-994a-93821f5871aa '
                          '(Abhisek Mohanty, "the native chart") plus the chart-independent '
                          'shared substrate.'),
        ('Retired', 'Cross-chart columns for Abhinandan (1c826d5a) and "Chart 3" / Kiran Shenoy '
                     '(cb73cd3d) are dropped from this and all future v4.1 output.'),
        ('', ''),
        ('SHEETS', 'h'),
        ('Layer Map', 'L0–L5 roll-up: population, conformance, health, cost, elevation thesis per layer.'),
        ('Asset Register', 'The master sheet — one row per asset, native + substrate only, plus the six '
                            '§15 v4.1 columns (domain, rung, within-rung wave, continuation class, '
                            'rehearsal partition, timeout source).'),
        ('Rung Board', 'NEW — one row per rung R0–R5: conformant % / lit % / integrity-passed % / '
                        'frozen / current wave / freeze-record notes. Honest current-state measurement; '
                        'no rung has been worked, so Frozen = No throughout.'),
        ('Asset Plans', 'The plan of action for every asset, native + substrate only, with the six §15 '
                         'columns. Identical to plan §15.'),
        ('Efficiency', 'NEW — the §19 ledger (§16): per asset p50 / p90 / worst / rows-per-sec / bound '
                        'class / hotspot / technique / target / achieved / identity proof, each with the '
                        'basis it rests on. Nothing has been profiled (the harness is M3, §14.1), so every '
                        'profiling-derived field reads an honest null — never a reassuring sentence '
                        '(§15\u2019s named correction; ADHIKARIN ruling D-8).'),
        ('Phase 0 Queue', 'The pre-flight work queue: every catalogue defect class with its recommendation.'),
        ('Elevation Plan', 'Per-asset actions and expected benefit, ordered by priority.'),
        ('Defect Register', 'Cross-cutting defects, including D-17…D-28 — the §1.9 loophole register '
                             '(L-01…L-12) folded in with code-citation evidence preserved.'),
        ('Infrastructure', 'Cloud Run, database and platform recommendations, ranked by measured value.'),
        ('Roadmap', 'Phases 0–6 (v3.0 vocabulary, carried) with gates and live-verified acceptance criteria.'),
        ('', ''),
        ('CURRENT COUNTS', 'h'),
        ('Assets', f'{len(rows)} registered — {len(chart_rows)} chart-domain, {len(shared_rows)} shared-domain'),
        ('Contract violations', f'{n_bad} assets non-conformant'),
        ('P0 blocking', f'{n_p0} assets'),
        ('No serving consumer', f'{n_nocons} table-backed assets read by no MCP tool, API route or retrieval layer'),
        ('', ''),
        ('LEGEND — §15 v4.1 columns', 'h'),
        ('domain', 'shared | chart, derived 1:1 from asset_registry.scope.'),
        ('rung', 'R0–R5, derived from layer_index per §8.4. Follows LAYER, not domain — mi_kula/'
                 'mi_vistara are domain=shared but rung=R5.'),
        ('within-rung wave', 'Intra-layer topological wave over depends_on restricted to the same '
                              'layer_index (§8.5); computed live from a recursive CTE, never hardcoded.'),
        ('continuation class', 'probe-only (tier S) | resumable-substep (has_substeps true, registry or '
                                'code) | restartable-light (single-shot, no substep plan).'),
        ('rehearsal partition', 'PARTITION_KEY entry if declared; else an explicit n/a reason '
                                 '(service probe, or single-shot whole-asset).'),
        ('timeout source', 'registered — writer_timeout_seconds DIFFERS from the column default; '
                            'default — it is NULL or EQUALS the column default (600), which is also the '
                            'runner fallback _WRITER_TIMEOUT_SECONDS, so the two are indistinguishable; '
                            'telemetry-derived — the profile ledger records derivation from measured '
                            'runtime. Corrected per PARĪKṢAKA V-2: the previous rule tested non-null '
                            'only, and the column is NOT NULL DEFAULT 600, so the field was a constant.'),
        ('', ''),
        ('LEGEND — §19 efficiency ledger (Efficiency sheet)', 'h'),
        ('bound class', 'round-trip | I/O | CPU | algorithmic | not-a-build (§19.4 step 3). A profiling '
                         'result, EXCEPT not-a-build, which is derivable structurally (service probe, or '
                         'no registered writer) and is emitted on that evidence. "No registered writer" '
                         'is read from the CODE (the AST @register census), never from '
                         'asset_registry.has_writer — see has_writer (registry) / has_writer (code) on the '
                         'Asset Register, and D-29. not-a-build EXEMPTS an asset from the §8.3 item 5 '
                         'efficiency pass, so a wrong input here walks a real build through a freeze gate '
                         'unexamined (D-25).'),
        ('has_writer (registry) / (code)',
         'The registry-vs-code PAIR for has_writer, carried exactly as Substeps (registry)/(code) is. '
         'D-25 part 3 standing rule: any registry boolean that gates whether a check runs must be derived '
         'from code, never trusted as declared, and must be surfaced as a pair so the divergence is '
         'visible rather than silently authoritative. A red registry cell means the two disagree; the CODE '
         'column is what every derived field reads.'),
        ('hotspot', 'The measured dominant cost, named. NULL UNTIL PROFILED (§15, verbatim). No asset has '
                     'been profiled, so it is null on all of them — that is the correct M0 answer, not a gap.'),
        ('technique / target / achieved / identity proof',
         'From §19.5\u2019s catalogue, §19.6\u2019s target discipline and I18\u2019s identity proof. All null '
         'until an optimization exists to describe; a value here without a profile behind it would be the '
         'same unearned signal this sheet was created to remove.'),
        ('rows/sec', 'Null: build_run_assets carries no row count and no chart_id, so the only available '
                      'quotient mixes this chart\u2019s current table rows with a median across every chart '
                      'that ever built the asset. That is an inference, not a measurement.'),
        ('p50 / p90 / worst', 'Measured from build_run_assets. Rows flagged POLLUTED (D-13, unclosed run '
                               'rows) say so in the Basis column.'),
        ('Basis', 'The §N.8 receipt: for every value, the detector that produced it; for every null, why '
                   'it is null. A ledger of unexplained nulls is the same defect one layer along.'),
    ]
    r = 1
    for a, b in blocks:
        if b == 'title':
            ws.cell(r, 1, a).font = Font(size=20, bold=True, color=ACCENT)
            ws.row_dimensions[r].height = 30
        elif b == 'sub':
            ws.cell(r, 1, a).font = Font(size=11, italic=True, color='647577')
        elif b == 'h':
            ws.cell(r, 1, a).font = Font(size=10, bold=True, color='FFFFFF')
            ws.cell(r, 1).fill = HDR
            ws.cell(r, 2).fill = HDR
        else:
            ws.cell(r, 1, a).font = Font(size=10, bold=True, color=INK)
            c = ws.cell(r, 2, b)
            c.font = Font(size=10, color=INK)
            c.alignment = Alignment(wrap_text=True, vertical='top')
            if len(str(b)) > 100:
                ws.row_dimensions[r].height = 42
        r += 1
    widths(ws, [30, 108])

    # ---- Layer Map ----
    ws = wb.create_sheet('Layer Map')
    ws.sheet_view.showGridLines = False
    cols = ['Layer', 'Name', 'Role in the instrument', 'Assets', 'Conformant', 'Violations', 'Shared',
            'Services', 'Heavy', 'No resume', 'No consumer', 'Worst (h)', 'Native lit/stale/err',
            'Elevation thesis for this layer']
    ws.append(cols)
    head(ws, len(cols))
    for lx in ['L0', 'L1', 'L2', 'L3', 'L4', 'L5']:
        sub = [x for x in rows if x['Layer'] == lx]
        if not sub:
            continue
        heavy = [x for x in sub if x['Tier'].startswith('H')]
        nat = collections.Counter(x[NATIVE_LABEL] for x in sub)
        ws.append([lx, sub[0]['Layer Name'], LAYER_ROLE[lx], len(sub),
                   sum(1 for x in sub if x['Conformant'] == 'YES'),
                   sum(1 for x in sub if x['Conformant'] == 'no'),
                   sum(1 for x in sub if x['Domain'] == 'shared'),
                   sum(1 for x in sub if x['Tier'].startswith('S')), len(heavy),
                   sum(1 for x in heavy if x['Resume'] == 'none'),
                   sum(1 for x in sub if x['Consumers'] == '0' and x['Target Table']),
                   round(max([x['Worst (h)'] or 0 for x in sub] or [0]), 1) or '',
                   f"{nat.get('lit',0)} / {nat.get('stale',0)} / {nat.get('error',0)+nat.get('incomplete',0)}",
                   THESIS[lx]])
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
            c.font = Font(size=10)
            c.border = BORDER
        row[0].font = Font(size=12, bold=True, color=ACCENT)
        row[1].font = Font(size=10, bold=True)
        ws.row_dimensions[row[0].row].height = 94
    widths(ws, [7, 13, 42, 8, 11, 10, 8, 9, 8, 10, 11, 10, 16, 66])
    ws.freeze_panes = 'A2'

    # ---- Rung Board (NEW, §16 / §12) ----
    ws = wb.create_sheet('Rung Board')
    ws.sheet_view.showGridLines = False
    rb_cols = ['Rung', 'Layer', 'Assets', 'Shared assets', 'Conformant %', 'Lit %',
               'Integrity-passed %', 'Frozen', 'Current wave', 'Freeze record / notes']
    ws.append(rb_cols)
    head(ws, len(rb_cols))
    rb_rows = rung_board_rows(rows)
    for rb in rb_rows:
        ws.append([rb[c] for c in rb_cols])
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
            c.font = Font(size=10)
            c.border = BORDER
        row[0].font = Font(size=14, bold=True, color=ACCENT)
        row[7].font = Font(size=10, bold=True, color='9E3438')
        for i in (4, 5, 6):
            row[i].number_format = '0.0'
        ws.row_dimensions[row[0].row].height = 40
    widths(ws, [7, 8, 8, 13, 14, 10, 18, 9, 30, 46])
    ws.freeze_panes = 'A2'

    # ---- Asset Register (single-chart + six v4.1 columns) ----
    ws = wb.create_sheet('Asset Register')
    cols = ['Layer', 'Layer Name', 'Asset ID', 'Sanskrit', 'English', 'Tier', 'Priority', 'Lifecycle',
            'Domain', 'Rung', 'Within-Rung Wave', 'Continuation Class', 'Rehearsal Partition', 'Timeout Source',
            'Superseded By', 'Data Disposition', 'Conformant', 'Contract Violations', 'Advisory',
            'Scope', 'Kind', 'Catalog', 'DAG Depth', 'Deps', 'Downstream', 'Consumers', 'Consumer Surfaces',
            'Target Table', 'count_sql', 'has_writer (registry)', 'has_writer (code)',
            'Substeps (registry)', 'Substeps (code)', 'Resume',
            'Median', 'P90', 'Worst', 'Worst (h)', 'Telemetry', 'Runs', 'Success %',
            'Rows (native)', 'Floor', 'Completeness %', 'Integrity Check',
            NATIVE_LABEL, 'Global',
            'Writer File', 'Elevation Actions', 'Expected Benefit']
    ws.append(cols)
    head(ws, len(cols))
    for rec in rows:
        ws.append([rec.get(c, '') for c in cols])
    idx = {c: i for i, c in enumerate(cols)}
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        tk = row[idx['Tier']].value[0]
        for c in row:
            c.font = Font(size=9)
            c.alignment = Alignment(vertical='top')
            c.border = BORDER
            if tk in TIER_FILL:
                c.fill = TIER_FILL[tk]
        row[idx['Asset ID']].font = Font(name='Menlo', size=9, bold=True)
        row[idx['Layer']].font = Font(size=10, bold=True, color=ACCENT)
        row[idx['Rung']].font = Font(name='Menlo', size=9, bold=True, color=ACCENT)
        row[idx['Domain']].font = Font(size=9, bold=True,
                                        color='647577' if row[idx['Domain']].value == 'shared' else INK)
        for k in ('Target Table', 'Writer File', 'Consumer Surfaces', 'Rehearsal Partition'):
            row[idx[k]].font = Font(name='Menlo', size=8, color='647577')
        row[idx['Priority']].font = PR_FONT.get(str(row[idx['Priority']].value)[:2], Font(size=9))
        cf = row[idx['Conformant']]
        cf.font = Font(size=9, bold=True, color='2E7A57' if cf.value == 'YES' else '9E3438')
        row[idx['Contract Violations']].font = Font(size=8, color='9E3438')
        row[idx['Contract Violations']].alignment = Alignment(wrap_text=True, vertical='top')
        # D-25 part 3 — the registry-vs-code pair must be VISIBLE, not silently
        # authoritative. Red on the registry cell wherever it disagrees with the code.
        if row[idx['has_writer (registry)']].value != row[idx['has_writer (code)']].value:
            row[idx['has_writer (registry)']].font = Font(size=9, bold=True, color='9E3438')
            row[idx['has_writer (code)']].font = Font(size=9, bold=True, color='2E7A57')
        row[idx['Advisory']].font = Font(size=8, color='8E6210')
        row[idx['Advisory']].alignment = Alignment(wrap_text=True, vertical='top')
        for cn in [NATIVE_LABEL, 'Global']:
            cell = row[idx[cn]]
            cell.font = STATE_FONT.get(str(cell.value), Font(name='Menlo', size=9, color='9AA7A8'))
            cell.alignment = Alignment(horizontal='center', vertical='top')
        for cn in ('Elevation Actions', 'Expected Benefit', 'Data Disposition'):
            row[idx[cn]].alignment = Alignment(wrap_text=True, vertical='top')
        for cn in ('DAG Depth', 'Deps', 'Downstream', 'Consumers', 'Worst (h)', 'Runs', 'Success %',
                   'Rows (native)', 'Floor', 'Completeness %', 'Within-Rung Wave'):
            row[idx[cn]].alignment = Alignment(horizontal='right', vertical='top')
            row[idx[cn]].number_format = '#,##0' if cn != 'Completeness %' else '0.0'
        ic = row[idx['Integrity Check']]
        ic.font = Font(size=9, bold=True, color='2E7A57' if ic.value == 'yes' else '9E3438')
        cp = row[idx['Completeness %']]
        if isinstance(cp.value, (int, float)) and cp.value < 95:
            cp.font = Font(size=9, bold=True, color='8E6210')
    widths(ws, [6, 11, 34, 20, 28, 22, 18, 15, 8, 6, 8, 20, 34, 16, 30, 42, 11, 40, 30, 10, 9, 9,
                7, 6, 11, 10, 40, 30, 9, 17, 15, 10, 10, 20, 9, 9, 9, 9, 20, 7, 9, 12, 11, 11, 10, 15, 13, 11, 46, 78, 88])
    ws.freeze_panes = 'D2'
    ws.auto_filter.ref = f'A1:{get_column_letter(len(cols))}{ws.max_row}'

    # ---- Phase 0 Queue (carried, unchanged content — single-chart facts don't change these totals) ----
    v3._append_phase0_queue(wb, rows)

    # ---- Asset Plans (single-chart + six v4.1 columns) ----
    ws = wb.create_sheet('Asset Plans')
    cols = ['Layer', 'Asset ID', 'What it is', 'Where it stands now', 'Tier', 'Priority',
            'Domain', 'Rung', 'Within-Rung Wave', 'Continuation Class', 'Rehearsal Partition', 'Timeout Source',
            '1 · Correctness & completeness', '2 · Rebuild time', '3 · Re-architecture & alignment', 'Expected benefit']
    ws.append(cols)
    head(ws, len(cols), h=34)
    for rec in rows:
        ws.append([rec['Layer'], rec['Asset ID'], rec['What'], rec['Now'], rec['Tier'], rec['Priority'],
                   rec['Domain'], rec['Rung'], rec['Within-Rung Wave'], rec['Continuation Class'],
                   rec['Rehearsal Partition'], rec['Timeout Source'],
                   rec['Correctness & Completeness Plan'], rec['Rebuild-Time Plan'],
                   rec['Re-architecture & Alignment Plan'], rec['Expected Benefit']])
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
            c.font = Font(size=9)
            c.border = BORDER
            tk = row[4].value[0]
            if tk in TIER_FILL:
                c.fill = TIER_FILL[tk]
        row[0].font = Font(size=10, bold=True, color=ACCENT)
        row[1].font = Font(name='Menlo', size=9, bold=True)
        row[3].font = Font(name='Menlo', size=8, color='647577')
        row[5].font = PR_FONT.get(str(row[5].value)[:2], Font(size=9))
        row[7].font = Font(name='Menlo', size=9, bold=True, color=ACCENT)
    widths(ws, [6, 32, 40, 40, 20, 16, 8, 6, 8, 20, 34, 16, 70, 62, 62, 48])
    ws.freeze_panes = 'C2'
    ws.auto_filter.ref = f'A1:{get_column_letter(len(cols))}{ws.max_row}'
    emit_plan_markdown(
        rows, plan_path=V4_PLAN_PATH, extra_cols=True,
        generator_note="Generated by build_control_workbook_v4_1.py (Track M0, §15) from live "
                        "production measurements, single-chart scope; identical to the "
                        "workbook's Asset Plans sheet. Do not hand-edit between the markers.")

    # ---- Efficiency (NEW, §16 — the §19 ledger) ----
    # §16: "a new Efficiency sheet (per asset: p50/p90 baseline, rows/sec, bound class, hotspot,
    # technique, target, achieved, identity proof — the §19 ledger)". PARĪKṢAKA V-1 found it
    # absent and no emitter for its fields; ADHIKĀRIN D-8 upheld and refused a deferral.
    # Every profiling-derived cell here is a null produced by a detector (asset_plans.PROFILES
    # is empty because M3 has not run), never a reassuring sentence. §15's correction, exactly.
    ws = wb.create_sheet('Efficiency')
    ws.sheet_view.showGridLines = False
    eff_cols = ['Layer', 'Asset ID', 'Rung', 'Tier', 'Domain', 'Profiled',
                'p50', 'p90', 'Worst', 'rows/sec', 'Bound class', 'Hotspot',
                'Technique (proposed / applied)', 'Target', 'Achieved', 'Identity proof',
                'Timeout source', 'Basis']
    ws.append(eff_cols)
    head(ws, len(eff_cols), h=34)
    for rec in rows:
        ws.append([rec['Layer'], rec['Asset ID'], rec['Rung'], rec['Tier'], rec['Domain'],
                   rec['Profiled'], rec['p50'], rec['p90'], rec['p_worst'], rec['Rows/sec'],
                   rec['Bound Class'], rec['Hotspot'], rec['Technique'], rec['Target'],
                   rec['Speedup Achieved'], rec['Identity Proof'], rec['Timeout Source'],
                   rec['Efficiency Basis']])
    ei = {c: i for i, c in enumerate(eff_cols)}
    NULL_FONT = Font(name='Menlo', size=9, italic=True, color='9AA7A8')
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        tk = row[ei['Tier']].value[0]
        for c in row:
            c.font = Font(size=9)
            c.alignment = Alignment(wrap_text=True, vertical='top')
            c.border = BORDER
            if tk in TIER_FILL:
                c.fill = TIER_FILL[tk]
        row[ei['Layer']].font = Font(size=10, bold=True, color=ACCENT)
        row[ei['Asset ID']].font = Font(name='Menlo', size=9, bold=True)
        row[ei['Rung']].font = Font(name='Menlo', size=9, bold=True, color=ACCENT)
        pf = row[ei['Profiled']]
        pf.font = Font(size=9, bold=True, color='2E7A57' if pf.value == 'yes' else '8E6210')
        # A null is rendered as the word `null`, greyed — never as an empty cell, which reads
        # as "nobody filled this in" rather than "the detector returned nothing".
        for cn in ('p50', 'p90', 'Worst', 'rows/sec', 'Bound class', 'Hotspot',
                   'Technique (proposed / applied)', 'Target', 'Achieved', 'Identity proof'):
            cell = row[ei[cn]]
            if str(cell.value) == 'null':
                cell.font = NULL_FONT
            else:
                cell.font = Font(name='Menlo', size=9, color=INK)
        row[ei['Basis']].font = Font(size=8, color='647577')
        ws.row_dimensions[row[0].row].height = 58
    widths(ws, [6, 32, 6, 22, 8, 9, 9, 9, 9, 10, 14, 26, 30, 22, 24, 20, 16, 96])
    ws.freeze_panes = 'C2'
    ws.auto_filter.ref = f'A1:{get_column_letter(len(eff_cols))}{ws.max_row}'

    # ---- Elevation Plan ----
    v3._append_elevation_plan(wb, rows)

    # ---- Defect Register (+ D-17…D-28) ----
    ws = wb.create_sheet('Defect Register')
    cols = ['ID', 'Defect', 'Severity', 'Evidence', 'Consequence', 'Fix', 'Phase']
    ws.append(cols)
    head(ws, len(cols))
    # sorted by ID so D-29 (M0-T22, appended to the v3 DEFECTS list) lands after D-28
    # rather than in the middle of the loophole block.
    for x in sorted(list(DEFECTS) + LOOPHOLE_DEFECTS, key=lambda t: t[0]):
        ws.append(list(x))
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
            c.font = Font(size=9)
            c.border = BORDER
        row[0].font = Font(name='Menlo', size=10, bold=True, color=ACCENT)
        row[1].font = Font(size=10, bold=True)
        row[2].font = SEV_FONT.get(str(row[2].value), Font(size=9))
        ws.row_dimensions[row[0].row].height = 72
    widths(ws, [8, 40, 11, 62, 56, 60, 8])
    ws.freeze_panes = 'A2'

    # ---- Infrastructure ----
    ws = wb.create_sheet('Infrastructure')
    cols = ['Rank', 'Area', 'Item', 'Verdict', 'Evidence', 'Recommendation', 'Phase']
    ws.append(cols)
    head(ws, len(cols))
    for x in INFRA:
        ws.append(list(x))
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
            c.font = Font(size=9)
            c.border = BORDER
        row[0].font = Font(name='Menlo', size=12, bold=True, color=ACCENT)
        row[2].font = Font(size=10, bold=True)
        row[3].font = SEV_FONT.get(str(row[3].value), Font(size=9, bold=True, color='647577'))
        ws.row_dimensions[row[0].row].height = 84
    widths(ws, [7, 15, 34, 16, 62, 70, 9])
    ws.freeze_panes = 'A2'

    # ---- Roadmap (v3.0 vocabulary, carried per §14.4) ----
    ws = wb.create_sheet('Roadmap')
    cols = ['Phase', 'Name', 'Effort', 'Freeze exception', 'Scope', 'Acceptance (live-verified)', 'Assets touched']
    ws.append(cols)
    head(ws, len(cols))
    heavy_n = sum(1 for x in rows if x['Tier'].startswith('H'))
    svc_n = sum(1 for x in rows if x['Tier'].startswith('S'))
    for x in roadmap(len(rows), n_p0, n_bad, heavy_n, svc_n):
        ws.append(list(x))
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
            c.font = Font(size=9)
            c.border = BORDER
        row[0].font = Font(size=16, bold=True, color=ACCENT)
        row[1].font = Font(size=11, bold=True)
        ws.row_dimensions[row[0].row].height = 100
    widths(ws, [7, 32, 13, 16, 70, 62, 26])
    ws.freeze_panes = 'A2'

    OUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUT)
    print('WROTE', OUT)
    print('assets:', len(rows), '| chart-domain:', len(chart_rows), '| shared-domain:', len(shared_rows),
          '| non-conformant:', n_bad, '| P0:', n_p0, '| zero-consumer:', n_nocons)
    print('rung board:', rb_rows)
    prof_n = sum(1 for x in rows if x['Profiled'] == 'yes')
    print('efficiency ledger: profiled', prof_n, '/', len(rows),
          '| null hotspot:', sum(1 for x in rows if x['Hotspot'] == 'null'),
          '| bound class not-a-build:', sum(1 for x in rows if x['Bound Class'] == 'not-a-build'),
          '| bound class null:', sum(1 for x in rows if x['Bound Class'] == 'null'))
    print('timeout source:', dict(collections.Counter(x['Timeout Source'] for x in rows)))

    # §15's last line: annotate v3.0's own copy as superseded.
    annotate_v3_superseded()


def annotate_v3_superseded():
    if not V3_PLAN_PATH.exists():
        print('v3.0 plan not found; skipping supersession note:', V3_PLAN_PATH)
        return
    doc = V3_PLAN_PATH.read_text()
    marker = 'NIRMĀṆA ELEVATION PLAN — v3.0'
    note = ('\n> **Superseded by v4.1 §15** — `00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v4_0.md` §15 '
            'now carries the live-regenerated, single-chart per-asset plans (Track M0). This §13 '
            'copy is retained as three-chart measurement history only.\n')
    if 'Superseded by v4.1 §15' in doc:
        print('v3.0 already annotated; skipping'); return
    idx = doc.find('## §13')
    if idx == -1:
        print('§13 header not found in v3.0 plan; skipping annotation'); return
    nl = doc.find('\n', idx)
    doc = doc[:nl + 1] + note + doc[nl + 1:]
    V3_PLAN_PATH.write_text(doc)
    print('v3.0 §13 annotated superseded-by-v4.1-§15:', V3_PLAN_PATH)


if __name__ == '__main__':
    main()
