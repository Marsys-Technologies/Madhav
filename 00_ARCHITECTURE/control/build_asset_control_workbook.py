#!/usr/bin/env python3
"""
NIRMĀṆA ASSET CONTROL WORKBOOK generator.

Self-contained: reads the live production registry, scans the writer code for
substep/resume facts, builds the asset -> serving-consumer index, evaluates each
asset against the Asset Catalogue Contract (NIRMANA_ELEVATION_PLAN §3), and emits
the control workbook.

Re-run after every phase so the workbook tracks movement instead of being hand-edited.

    python3 00_ARCHITECTURE/control/build_asset_control_workbook.py \
        00_ARCHITECTURE/control/NIRMANA_ASSET_CONTROL_WORKBOOK_v2_0.xlsx

Requires a reachable DATABASE_URL (platform/.env.local) — i.e. cloud-sql-proxy up.
"""
import collections
import pathlib
import re
import sys

import json
import psycopg
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from asset_plans import derive, derive_v41_columns
from writer_substep_census import (registered_asset_ids, resume_mechanism_by_asset,
                                   substep_truth_by_asset, writer_file_by_asset)
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

ROOT = pathlib.Path(__file__).resolve().parents[2]
MEAS_PATH = ROOT / '00_ARCHITECTURE/control/asset_measurements.json'
PLAN_PATH = ROOT / '00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v3_0.md'
MEAS = json.loads(MEAS_PATH.read_text()) if MEAS_PATH.exists() else {}
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else \
    ROOT / '00_ARCHITECTURE/control/NIRMANA_ASSET_CONTROL_WORKBOOK_v3_0.xlsx'

CHARTS = [
    ('482012f1-710e-4a25-994a-93821f5871aa', 'Abhisek (native)'),
    ('1c826d5a-41cb-4450-b4dc-59d440e5f75a', 'Abhinandan'),
    ('cb73cd3d-9eba-4220-9902-0de91566e980', 'Chart 3'),
]
LAYER = {
    'brahmagyan': ('L0', 'Brahmagyan'), 'ganita': ('L1', 'Gaṇita'),
    'bodha': ('L2', 'Bodha'), 'kala': ('L3', 'Kāla'),
    'phala': ('L4', 'Phala'), 'mimamsa': ('L5', 'Mīmāṃsā'),
}
LAYER_ROLE = {
    'L0': 'Global reference substrate — chart-independent, built once, reused by every chart',
    'L1': 'Computed chart facts — the authority every higher layer references, never restates',
    'L2': 'Derivation & synthesis — signals, mechanisms, contradictions, gestalt',
    'L3': 'Time — dashas, transits, windows, the field; the heaviest layer by compute',
    'L4': 'Deterministic outcome shaping — phala, remedies, rectification',
    'L5': 'Calibration & judgment — prediction/outcome loop, scoring, review',
}
THESIS = {
    'L0': 'Publish a substrate version + content digest per asset so every chart records what it consumed. '
          'Repair the service probes — this layer holds most of them, and one sat red for 66 days. Cost here '
          'is paid once and amortises across every chart, so it is the cheapest layer to make honest.',
    'L1': 'The authority layer: everything above references its fact ids. Content digests here have the highest '
          'leverage in the system — a no-op L1 rebuild currently invalidates the entire DAG above it. Several '
          'writers carry substep plans and none of them can resume.',
    'L2': 'Broad, shallow and cheap per asset, but deep in fan-out. The win is early cutoff: most L2 rebuilds '
          'produce identical rows and should stop propagating.',
    'L3': 'Where the wall-clock lives. Two assets have individually exceeded 33 hours. Partition receipts and '
          'shared resumability convert interruption from total loss into bounded rework, and the '
          'generation/authority model belongs here.',
    'L4': 'Deterministic and inexpensive, but structurally serial — it sits at DAG depths 16–20 and gates all of '
          'L5. The win is edge hygiene: removing declared-but-unread dependencies shortens the critical path.',
    'L5': 'The deepest and most cascade-prone layer: eight of its assets were recently blocked by a single '
          'upstream fault. Cascade-root collapse and honest partial states matter more here than raw speed.',
}


def layer_thesis(lx, sub):
    """The layer's durable narrative, plus any MEASURED clause, derived at render time.

    Nirmana M0-T30 / F-4. `THESIS` is hand-written prose living inside a generator whose
    whole premise (section 16) is "generated, never hand-edited" -- and a hardcoded claim
    cannot drift-detect itself. `THESIS['L2']` used to end "Three writers here have their
    completeness gate silently disabled." That was true when it was written; after the
    Phase 0.6a `has_substeps` repair (D-24) and M0-T28's `Substeps (code)` fix, the
    measured registry-vs-code divergence is 0 in EVERY layer, so the sentence had become a
    hardcoded claim contradicting the generated columns two sheets away.

    The sentence is NOT re-worded with a fresh hardcoded number -- that only resets the
    same clock (the reasoning DVA Ruling 16 applied to CLAUDE.md's row counts). It is
    DERIVED from the rows the Layer Map is already counting, and emitted ONLY when the
    count is non-zero, so a clean layer says nothing rather than carrying a permanent
    "0 defects" boast. The claim can no longer outlive its cause: if the divergence
    returns -- in L2 or in any other layer -- the thesis says so, with the measured count
    and the asset ids.

    A count of 0 here is a real detector's real verdict, not an unearned green (section
    N.8): `Substeps (registry)` and `Substeps (code)` are both populated per asset by
    detectors that CAN disagree, and M0-T28 proved by mutation that they do. Saying
    nothing is the honest rendering of "nothing to report", not a silent pass.
    """
    t = THESIS[lx]
    bad = [x['Asset ID'] for x in sub
           if x['Substeps (code)'] == 'yes' and x['Substeps (registry)'] == 'no']
    if bad:
        t += (f" Measured this run: {len(bad)} writer(s) here have their completeness "
              f"gate silently disabled -- asset_registry.has_substeps is false while the "
              f"writer class overrides both plan_substeps and run_substep "
              f"({', '.join(sorted(bad))}).")
    return t


# Known supersession pointers (Phase 0.3 seeds these into the registry itself).
SUPERSEDED_BY = {'ka_gochara_sweep': 'ka_gochara_v3_century_materialize (gen 3.0 authority)'}
DATA_DISPOSITION = {'ka_gochara_sweep': 'RETAINED_AS_CAPITAL — 38,287 v1 rows; no registered writer can rebuild them'}


def db_url() -> str:
    for line in (ROOT / 'platform/.env.local').read_text().splitlines():
        m = re.match(r'^\s*DATABASE_URL\s*=\s*(.+)$', line)
        if m:
            return m.group(1).strip().strip('"').strip("'")
    raise SystemExit('DATABASE_URL not found in platform/.env.local')


def fetch():
    d = {}
    with psycopg.connect(db_url(), row_factory=psycopg.rows.dict_row) as conn:
        c = conn.cursor()
        c.execute("""SELECT asset_id, layer, layer_index, layer_name, sanskrit_name, english_name,
            scope, asset_type, asset_kind, catalog_status, is_active, has_writer, has_substeps,
            storage_type, target_table, (count_sql IS NOT NULL) AS has_count_sql, target_floor,
            estimated_seconds, writer_timeout_seconds, COALESCE(depends_on,'{}') AS depends_on
            FROM asset_registry ORDER BY asset_id""")
        d['registry'] = c.fetchall()
        c.execute("""SELECT r.asset_id, count(*)::int AS n FROM asset_registry r
            JOIN asset_registry x ON r.asset_id = ANY(x.depends_on) GROUP BY r.asset_id""")
        d['fanout'] = {r['asset_id']: r['n'] for r in c.fetchall()}
        c.execute("""SELECT asset_id, count(*)::int AS runs,
            count(*) FILTER (WHERE state='complete')::int AS ok,
            percentile_cont(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (ended_at-started_at))) AS med,
            percentile_cont(0.9) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (ended_at-started_at))) AS p90,
            max(EXTRACT(EPOCH FROM (ended_at-started_at))) AS mx
            FROM build_run_assets GROUP BY asset_id""")
        d['timing'] = {r['asset_id']: r for r in c.fetchall()}
        c.execute("SELECT asset_id, chart_id::text AS chart_id, state FROM asset_throughput")
        d['tp'] = collections.defaultdict(dict)
        for r in c.fetchall():
            d['tp'][r['asset_id']][r['chart_id']] = r['state']
        c.execute("""WITH RECURSIVE dag AS (
            SELECT asset_id, 0 AS depth FROM asset_registry
             WHERE (depends_on IS NULL OR cardinality(depends_on)=0) AND is_active
            UNION ALL
            SELECT r.asset_id, g.depth+1 FROM asset_registry r JOIN dag g ON g.asset_id = ANY(r.depends_on)
             WHERE r.is_active AND g.depth < 40)
            SELECT asset_id, max(depth)::int AS depth FROM dag GROUP BY asset_id""")
        d['depth'] = {r['asset_id']: r['depth'] for r in c.fetchall()}
        c.execute("SELECT count(*)::int AS n FROM build_protected_assets")
        d['protection_rows'] = c.fetchone()['n']
        # V-2 / §15 'timeout source': the column's OWN default, read live rather than
        # hardcoded, so the classifier tracks the schema instead of a constant in this file.
        c.execute("""SELECT column_default FROM information_schema.columns
             WHERE table_name='asset_registry' AND column_name='writer_timeout_seconds'""")
        _cd = c.fetchone()
        m_cd = re.search(r'\d+', (_cd or {}).get('column_default') or '')
        d['timeout_column_default'] = int(m_cd.group()) if m_cd else None
        # §8.5 within-rung wave: intra-layer topological wave over depends_on, restricted to
        # the SAME layer_index (cross-layer deps are satisfied by rung sequencing, not this).
        # Mirrors the DAG-depth CTE above, style-for-style; NOT EXISTS handles both a NULL
        # depends_on and a depends_on with no same-layer member as wave 0 uniformly.
        c.execute("""WITH RECURSIVE wave AS (
            SELECT r.asset_id, r.layer_index, 0 AS w FROM asset_registry r
             WHERE r.is_active AND NOT EXISTS (
                 SELECT 1 FROM asset_registry dep
                  WHERE dep.asset_id = ANY(r.depends_on) AND dep.layer_index = r.layer_index
                    AND dep.is_active)
            UNION ALL
            SELECT r.asset_id, r.layer_index, g.w + 1 FROM asset_registry r
             JOIN wave g ON g.asset_id = ANY(r.depends_on) AND g.layer_index = r.layer_index
             WHERE r.is_active AND g.w < 40)
            SELECT asset_id, max(w)::int AS w FROM wave GROUP BY asset_id""")
        d['wave'] = {r['asset_id']: r['w'] for r in c.fetchall()}
    return d


def code_registered_asset_ids():
    """The code-derived `has_writer`, from the M0-T8 AST census (D-25 part 2a).

    NOT read from asset_registry.has_writer, and NOT re-parsed here. D-25 part 3's
    standing rule: any registry boolean that gates whether a check runs must be derived
    from code, never trusted as declared. `has_writer=false` gates the §19 efficiency
    pass — `_bound_class()` reads it as "nothing builds this asset" and returns
    `not-a-build`, which exempts the asset from §8.3 item 5 ALTOGETHER. A registry row
    that is wrong therefore walks a genuinely-built asset through a freeze gate
    unexamined. That is what V-6 caught on two R0 assets.

    Reuses `writer_substep_census.registered_asset_ids()` — the same AST parser that
    also produces the `Substeps (code)`, `Writer File` and `Resume` truths — rather than
    adding a parser. A regex is not the authority for any of them, because it counts
    docstring mentions of `@register(` and a naive AST pass drops `@register(ASSET_ID)`.
    (M0-T28 / F-1 removed `scan_code()`'s `code_has_plan_substeps` key for the first of
    those reasons — the docstring `@register('bg_reference')` at `writers/__init__.py:172`
    was being read as a real registration and picking up `WriterBase`'s own
    `plan_substeps`. M0-T30 / F-5 removed the regex ITSELF, the last text match in the
    generator's asset-level derivations; see `scan_code()`.)

    NO ASSET ID IS SPECIAL-CASED here or anywhere downstream (D-25 part 2c): the two
    known cases are secondary decorators stacked on a shared writer class, which is the
    general shape, and the census collects registrations per-decorator so that shape
    resolves without naming anything.
    """
    return registered_asset_ids()


def code_substep_truth():
    """The code-derived `has_substeps`, from the SAME M0-T8 AST census (M0-T28 / F-1).

    WHAT THIS REPLACED, AND WHY. The `Substeps (code)` column used to come from
    `scan_code()`'s regex: `has_plan = 'def plan_substeps' in txt` — a substring search
    over the WHOLE FILE (plus an appended `services/*` blob), attributed to EVERY
    `@register` found in that file. That is file granularity where the question is
    class granularity, and after the Phase 0.6a `has_substeps` repair it reported TWO
    divergences that do not exist, so the Phase 0 Queue's 0.6a cell read "2" where the
    true count is 0 — a stale-looking defect count generated by a defective scanner.

    Both false positives are instances of traps this campaign has already named:

      · `bo_laksana_rerank` — FILE GRANULARITY. `BoLaksanaRerankWriter` defines `run()`
        only and merely SHARES `writers/bo_laksana.py` with the heavy `BoLaksanaWriter`.
        This is the exact pair D-24 condition (b) made the discriminating detector for.
      · `bg_reference` — THE DOCSTRING TRAP AND THE MRO-CONSTANT TRAP AT ONCE. Its own
        writer file is 51 lines and defines `run()` alone; the regex matched
        `@register('bg_reference')` inside the USAGE DOCSTRING of `register()` at
        `pipeline/orchestrator/writers/__init__.py:172`, and that file is `WriterBase`'s
        own module, which of course contains `def plan_substeps` (line 116). So the
        column was reporting the FROZEN BASE'S method as the writer's — which is a
        constant, true of all 123 writers, not a detector.

    The census answers the right question: it resolves the class graph and asks whether
    the @register'd class (or a project-local ancestor) genuinely OVERRIDES both
    `plan_substeps` and `run_substep`, contributing none of `WriterBase`'s own methods.
    It is also the same derivation the Phase 0.6a registry repair was measured against,
    so the registry side and the code side of the pair are finally like-for-like and the
    divergence column means what it says.

    ONE PARSER, REUSED (D-25 part 2c): no fourth parser is written here, and no asset id
    is special-cased. D-25 part 3's standing rule — any registry boolean that gates
    whether a check runs must be DERIVED FROM CODE and surfaced as a registry-vs-code
    pair — is what this column is for; deriving its code side from a coarse proxy left
    the pair looking honest while reporting a divergence that was an artefact of the
    proxy.
    """
    return substep_truth_by_asset()


def scan_code():
    """asset_id -> {writer_file, resume_mechanism} — BOTH DERIVED FROM THE AST CENSUS.

    NO TEXT MATCH REMAINS IN THIS FUNCTION (Nirmāṇa M0-T30 / F-5). It is now a thin
    projection of `writer_substep_census`, kept under its original name and shape so
    `build_rows()` and its `cf.get(...)` callers are untouched.

    THE SWEEP M0-T28 STARTED, FINISHED. M0-T28 moved `Substeps (code)` off the regex
    and said plainly that `resume_mechanism` was the same defect in the same function,
    one column over. It is — and measurement showed it was not merely capable of going
    wrong, it WAS wrong, in both of its outputs:

      · `writer_file` was the LAST file `rglob` happened to visit whose text matched
        an `@register(...)` pattern — a test file for 3 assets, a shim's docstring for 11, and
        for `ka_gochara` the tombstone of a DIFFERENT retired asset. 14 of 123 wrong.
      · `resume_mechanism` was a substring search over the whole writer file PLUS every
        `.py` in the first `services/<pkg>` package it imports, attributed to every
        `@register` the regex found in that file. `ka_gochara` read
        `substep_fingerprint` from RETIRED `ka_gochara_sweep`'s service package;
        `bg_gochara_arcs` read `delta_fingerprint` from a module its writer never calls.

    Three traps, all previously paid for by this campaign, and this function had all
    three: the DOCSTRING trap (a retired shim naming `@register('ka_gochara')` in prose
    was read as a registration), FILE GRANULARITY (one answer per file, applied to every
    registration in it), and — one this function had beyond M0-T28's list — NO EXCLUDE
    LIST AT ALL, so `writers/tests/` was scanned and produced three phantom asset ids
    (`bad_infra_writer`, `test_infra_asset_1`, `test_infra_asset_dup`) alongside the real
    ones. The census has always excluded test trees.

    ONE PARSER, REUSED (D-25 part 2c): the derivations live in the census next to the
    `has_writer` and `has_substeps` ones, not here, so there is still exactly one AST
    parser for `@register` in the control plane.
    """
    files = writer_file_by_asset()
    resume = resume_mechanism_by_asset()
    return {aid: {'writer_file': files[aid],
                  'resume_mechanism': resume.get(aid, 'none')}
            for aid in files}


def consumer_map(registry):
    """asset_id -> sorted list of serving surfaces that reference its target_table."""
    tables = collections.defaultdict(list)
    for r in registry:
        if r['target_table']:
            tables[r['target_table']].append(r['asset_id'])
    bases = [('MCP', ROOT / 'platform-mcp/src/tools'),
             ('API', ROOT / 'platform/src/app/api'),
             ('retrieval', ROOT / 'platform/src/lib/retrieval')]
    hits = collections.defaultdict(set)
    pats = {t: re.compile(r'\b' + re.escape(t) + r'\b') for t in tables}
    for label, base in bases:
        if not base.exists():
            continue
        for p in base.rglob('*.ts'):
            s = str(p)
            if '__tests__' in s or p.name.endswith('.test.ts'):
                continue
            try:
                txt = p.read_text(errors='ignore')
            except Exception:
                continue
            for t, rx in pats.items():
                if rx.search(txt):
                    hits[t].add(f'{label}:{p.stem}')
    out = {}
    for t, assets in tables.items():
        c = sorted(hits.get(t, []))
        for a in assets:
            out[a] = c
    return out


def num(v):
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return int(f) if f == int(f) else round(f, 1)


def fmt_dur(s):
    if s is None:
        return ''
    s = float(s)
    return f'{s:.0f}s' if s < 90 else (f'{s/60:.0f}m' if s < 5400 else f'{s/3600:.1f}h')


# ------------------------------------------------------------------ build rows
def build_rows(d, code, consumers):
    # D-25 part 2(a): `has_writer` is DERIVED FROM THE WRITER CLASS, exactly as
    # `has_substeps` already is, and both readings are carried so the divergence is
    # visible instead of silently authoritative (D-25 part 3). Computed once per run.
    code_writers = code_registered_asset_ids()
    # M0-T28 / F-1: `Substeps (code)` is the AST OVERRIDE test, not a file-granular
    # regex. Same census, same run, computed once (see code_substep_truth).
    code_substeps = code_substep_truth()
    rows = []
    for r in d['registry']:
        aid = r['asset_id']
        lx, lname = LAYER.get(r['layer'], ('—', r['layer'] or 'UNCLASSIFIED'))
        cf, t = code.get(aid, {}), d['timing'].get(aid, {})
        max_s, med_s, p90_s = num(t.get('mx')), num(t.get('med')), num(t.get('p90'))
        polluted = bool(max_s) and max_s > 48 * 3600
        runs, ok = num(t.get('runs')) or 0, num(t.get('ok')) or 0
        succ = round(100.0 * ok / runs, 1) if runs else None
        is_service = 'service' in (r['asset_kind'], r['asset_type'], r['storage_type'])
        reg_sub, code_sub = bool(r['has_substeps']), bool(code_substeps.get(aid, False))
        sub_mismatch = code_sub and not reg_sub
        # has_writer, the registry-vs-code pair. `code_hw` is the one that gates:
        # everything downstream (_bound_class, the Rebuild-Time Plan narrative, the
        # Writer File placeholder) reads the CODE flag. `reg_hw` is carried for the
        # divergence column only — repairing the asset_registry rows is R0 stage 2's
        # (D-25 part 2b), not this generator's.
        reg_hw, code_hw = bool(r['has_writer']), aid in code_writers
        writer_mismatch = code_hw != reg_hw
        resume = cf.get('resume_mechanism', 'none') if code_sub else 'n/a'
        down = num(d['fanout'].get(aid, 0)) or 0
        gen_bearing = aid.startswith('ka_gochara')
        # Heavy = genuinely long-running. A substep plan alone does not make an asset heavy
        # (ga_prashna plans substeps and runs in 6 seconds).
        heavy = (p90_s or 0) >= 1800 or (med_s or 0) >= 600 or (code_sub and (p90_s or 0) >= 300) \
            or ((max_s or 0) >= 3600 and not polluted)
        cons = consumers.get(aid, [])

        # ---- lifecycle (Contract §3.2) ----
        if aid == 'lel_events':
            life = 'SOURCE'
        elif r['catalog_status'] == 'RETIRED' or not r['is_active']:
            life = 'SUPERSEDED_BY' if aid in SUPERSEDED_BY else 'RETIRED'
        elif r['catalog_status'] == 'DRAFT':
            life = 'DRAFT'
        else:
            life = 'CURRENT'

        # ---- contract conformance (Contract §3.4) ----
        v = []
        if life != 'SOURCE':
            if not r['layer_index']:
                v.append('no layer_index')
            elif not re.fullmatch(r'L[0-5]', str(r['layer_index'])):
                v.append(f"layer_index format '{r['layer_index']}'")
            if r['layer'] and lx != '—' and not aid.startswith(
                    {'L0': 'bg_', 'L1': 'ga_', 'L2': 'bo_', 'L3': 'ka_', 'L4': 'ph_', 'L5': 'mi_'}[lx]):
                v.append('prefix ≠ layer')
        if sub_mismatch:
            v.append('has_substeps false negative')
        kinds = {k for k in (r['asset_kind'], r['asset_type'], r['storage_type']) if k}
        if 'service' in kinds and len(kinds & {'data', 'artifact'}) > 0:
            v.append('kind/type/storage disagree')
        if not is_service and life in ('CURRENT', 'DRAFT'):
            if not r['target_table']:
                v.append('no target_table')
            if not r['has_count_sql']:
                v.append('no count_sql')
        if life == 'RETIRED' or life == 'SUPERSEDED_BY':
            if aid not in DATA_DISPOSITION:
                v.append('no data_disposition')
            if d['tp'].get(aid):
                v.append('retired but has throughput rows')
        if r['is_active'] and not d['tp'].get(aid) and life != 'SOURCE':
            v.append('never built on any chart')
        # DRAFT is defined as "registered, not yet authoritative". An asset that is
        # actively built AND read by a serving surface is authoritative in practice.
        if r['catalog_status'] == 'DRAFT' and d['tp'].get(aid) and cons:
            v.append('DRAFT but built and served')
        adv = []
        if not r['estimated_seconds']:
            adv.append('no estimated_seconds')
        if not cons and r['target_table'] and life == 'CURRENT':
            adv.append('no detected serving consumer')

        tier = ('S · Service probe' if is_service else
                'X · Generation-bearing' if gen_bearing else
                'G · Global substrate' if r['scope'] == 'global' else
                'H · Heavy partitioned' if heavy else 'M · Medium deterministic')

        # ---- actions + benefits ----
        acts, bens = [], []
        if sub_mismatch:
            acts.append('P0 · Derive has_substeps from the writer class; assert in CI')
            bens.append('Re-arms the §N.8 completeness gate — a partial build can no longer be promoted to lit. '
                        'Also unlocks the "partial" UI state.')
        if 'no layer_index' in v or any(x.startswith('layer_index format') for x in v):
            acts.append(f'P0 · Backfill/normalise layer_index → {lx}, layer_name → {lname}')
            bens.append('Asset sorts and groups correctly in the cockpit instead of falling into an ad-hoc bucket.')
        if 'kind/type/storage disagree' in v:
            acts.append('P0 · Collapse to asset_kind as the single authoritative classification')
            bens.append('Cockpit renders it in the correct lane; row-count expectations stop being applied to a service.')
        if 'prefix ≠ layer' in v:
            acts.append('P0 · Reclassify as SOURCE (outside L0–L5) or rename to the layer prefix')
            bens.append('Layer population counts and per-layer health arithmetic become honest.')
        if life in ('RETIRED', 'SUPERSEDED_BY'):
            acts.append('P0 · Lifecycle: record superseded_by + data_disposition; clear residual throughput rows')
            bens.append('Removes a permanent red from every chart that still holds a throughput row for it.')
        if 'DRAFT but built and served' in v:
            acts.append('P0 · Promote to CURRENT or record why it is still DRAFT')
            bens.append('catalog_status regains meaning — DRAFT stops covering assets that are already '
                        'authoritative in production, so the field can gate real decisions.')
        if is_service:
            acts.append('P1 · Real health probe with an SLO + alerting; dedicated cockpit service lane')
            bens.append('A degraded service surfaces in minutes, not months.')
        if r['scope'] == 'global':
            acts.append('P3 · Publish substrate_version + output content digest; consumers record the version read')
            bens.append(f'Cost amortises across all charts. {down} direct dependant(s) stop invalidating on a '
                        'no-op rebuild.')
        if tier.startswith('H'):
            if resume == 'none':
                acts.append('P4 · Adopt the shared ResumableWriter mixin (currently NO resume capability)')
                bens.append((f'Worst observed run {fmt_dur(max_s)}; today any interruption discards all of it. '
                             if max_s else '') + 'After: work resumes from the last committed substep.')
            elif resume == 'substep_fingerprint':
                acts.append('P4 · Migrate the private resume copy onto the shared mixin; add per-substep INPUT digests')
                bens.append('Removes a hand-maintained _RESUME_VERSION. Rebuild re-runs only the partitions whose '
                            'inputs changed, instead of replanning all of them on any fingerprint mismatch.')
            else:
                acts.append('P4 · Keep the delta fingerprint; migrate onto the shared mixin so the pattern is inherited')
                bens.append('Proven skip-on-unchanged behaviour becomes reusable by every other heavy writer.')
            acts.append('P2 · Persist the substep plan total at plan time')
            bens.append('Cockpit shows a real denominator and the watchdog gets a true progress signal.')
        if tier.startswith('M'):
            acts.append('P3 · Output content digest + early cutoff on read')
            bens.append(f'A rebuild producing identical content stops invalidating {down} direct dependant(s) — '
                        'this is the long tail that makes full rebuilds slow.')
        if gen_bearing:
            acts.append('P2 · Model generation + per-chart authority as first-class registry/UI concepts')
            bens.append('One asset, N generations, one authoritative pointer per chart — each with its own count '
                        'and freshness. Ends the hand-repointing of count_sql.')
        if not cons and r['target_table'] and life == 'CURRENT':
            acts.append('P1 · Confirm this asset has no serving consumer — candidate for retirement review')
            bens.append('Either a real consumer is found and recorded, or the DAG sheds an asset nothing reads.')
        if not acts:
            acts.append('P3 · Output content digest + early cutoff on read')
            bens.append('Participates in content-addressed freshness; no bespoke work required.')

        pr = ('P0 · Blocking defect' if v and any(x in v for x in (
                'has_substeps false negative', 'no layer_index', 'prefix ≠ layer',
                'kind/type/storage disagree', 'retired but has throughput rows',
                'DRAFT but built and served'))
              else 'P1 · High' if (max_s or 0) >= 3600 or is_service
              else 'P2 · Medium' if down >= 5 or (med_s or 0) >= 300
              else 'P3 · Standard')

        rec = {
            'Layer': lx, 'Layer Name': lname, 'Asset ID': aid,
            'Sanskrit': r['sanskrit_name'] or '', 'English': r['english_name'] or '',
            'Tier': tier, 'Priority': pr, 'Lifecycle': life,
            'Superseded By': SUPERSEDED_BY.get(aid, ''),
            'Data Disposition': DATA_DISPOSITION.get(aid, ''),
            'Contract Violations': '; '.join(v), 'Conformant': 'no' if v else 'YES',
            'Advisory': '; '.join(adv),
            'Scope': r['scope'] or '', 'Kind': r['asset_kind'] or '', 'Catalog': r['catalog_status'] or '',
            'DAG Depth': num(d['depth'].get(aid)), 'Deps': len(r['depends_on']), 'Downstream': down,
            'Consumers': str(len(cons)), 'Consumer Surfaces': ', '.join(cons[:8]) + ('…' if len(cons) > 8 else ''),
            'Target Table': r['target_table'] or '', 'count_sql': 'yes' if r['has_count_sql'] else 'NO',
            'Substeps (registry)': 'yes' if reg_sub else 'no', 'Substeps (code)': 'yes' if code_sub else 'no',
            'Resume': resume,
            'Median': fmt_dur(med_s), 'P90': fmt_dur(num(t.get('p90'))), 'Worst': fmt_dur(max_s),
            'Worst (h)': round(max_s / 3600, 2) if max_s else None,
            'Runs': runs, 'Success %': succ,
            'Writer File': cf.get('writer_file', '') or ('— no writer —' if not code_hw else ''),
            'has_writer (registry)': 'yes' if reg_hw else 'no',
            'has_writer (code)': 'yes' if code_hw else 'no',
            '_has_writer': code_hw,
            '_has_writer_registry': reg_hw,
            '_has_writer_divergent': writer_mismatch,
            'Elevation Actions': '\n'.join(f'• {a}' for a in acts),
            'Expected Benefit': '\n'.join(f'• {b}' for b in bens),
        }
        for cid, label in CHARTS:
            rec[label] = d['tp'].get(aid, {}).get(cid, '—') if r['scope'] != 'global' else 'n/a'
        rec['Global'] = d['tp'].get(aid, {}).get(None, '—') if r['scope'] == 'global' else 'n/a'
        rec['_med_s'], rec['_max_s'], rec['_p90_s'] = med_s, max_s, p90_s
        rec['Telemetry'] = 'POLLUTED (unclosed run)' if polluted else 'ok'
        mm = MEAS.get(aid, {})
        rec['Rows (native)'] = mm.get('actual_rows_native')
        rec['Rows (abhinandan)'] = mm.get('actual_rows_abhinandan')
        rec['Rows (chart 3)'] = mm.get('actual_rows_chart3')
        rec['Floor'] = mm.get('target_floor')
        fl, rn = mm.get('target_floor'), mm.get('actual_rows_native')
        rec['Completeness %'] = round(100.0 * rn / fl, 1) if fl and rn is not None else None
        rec['Integrity Check'] = 'yes' if mm.get('integrity_check_sql') else 'NO'
        plan = derive(rec, mm)
        rec['What'] = plan.what
        rec['Now'] = plan.now
        rec['Correctness & Completeness Plan'] = '\n'.join(f'• {x}' for x in plan.correctness) or '—'
        rec['Rebuild-Time Plan'] = '\n'.join(f'• {x}' for x in plan.rebuild_time) or '—'
        rec['Re-architecture & Alignment Plan'] = '\n'.join(f'• {x}' for x in plan.architecture) or '—'
        rec['Expected Benefit'] = '\n'.join(f'• {x}' for x in plan.benefit) or rec['Expected Benefit']
        # NIRMANA_ELEVATION_PLAN_v4_0.md §15 — the six v4.1 per-asset columns (single-chart).
        rec.update(derive_v41_columns(
            aid=aid, layer=lx, scope=r['scope'] or '', tier_letter=tier[0],
            reg_sub=reg_sub, code_sub=code_sub, writer_timeout_seconds=r['writer_timeout_seconds'],
            med_s=med_s, p90_s=p90_s, wave=d['wave'].get(aid),
            has_writer=code_hw,
            timeout_column_default=d.get('timeout_column_default'),
            polluted=polluted, max_s=max_s))
        rows.append(rec)
    rows.sort(key=lambda x: (x['Layer'], x['Tier'], x['Asset ID']))
    return rows


# ------------------------------------------------------------------ styling
ACCENT, INK = '14655F', '1B2A2C'
HDR = PatternFill('solid', fgColor='0E4B47')
TIER_FILL = {'G': PatternFill('solid', fgColor='E3EFEE'), 'H': PatternFill('solid', fgColor='F7EADB'),
             'S': PatternFill('solid', fgColor='F6E3E3'), 'X': PatternFill('solid', fgColor='EDE7F4')}
STATE_FONT = {'lit': Font(name='Menlo', size=9, color='2E7A57', bold=True),
              'stale': Font(name='Menlo', size=9, color='8E6210', bold=True),
              'error': Font(name='Menlo', size=9, color='9E3438', bold=True),
              'incomplete': Font(name='Menlo', size=9, color='9E3438', bold=True),
              'dormant': Font(name='Menlo', size=9, color='647577')}
PR_FONT = {'P0': Font(size=9, color='9E3438', bold=True), 'P1': Font(size=9, color='8E6210', bold=True),
           'P2': Font(size=9, color=INK), 'P3': Font(size=9, color='647577')}
SEV_FONT = {'CRITICAL': Font(size=10, bold=True, color='9E3438'), 'HIGH': Font(size=10, bold=True, color='B4552B'),
            'MEDIUM': Font(size=10, bold=True, color='8E6210'), 'LOW': Font(size=10, color='647577')}
BORDER = Border(bottom=Side(style='thin', color='D3DCDC'))


def head(ws, n, h=30):
    for c in range(1, n + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = Font(bold=True, color='FFFFFF', size=10)
        cell.fill = HDR
        cell.alignment = Alignment(vertical='center', wrap_text=True)
    ws.row_dimensions[1].height = h


def widths(ws, ws_widths):
    for i, w in enumerate(ws_widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w


def wrap_sheet(ws, rowheight=None, bolds=(0,)):
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
            c.font = Font(size=9)
            c.border = BORDER
        for b in bolds:
            row[b].font = Font(size=10, bold=True)
        if rowheight:
            ws.row_dimensions[row[0].row].height = rowheight


# ------------------------------------------------------------------ main
def main():
    d = fetch()
    code = scan_code()
    cons = consumer_map(d['registry'])
    rows = build_rows(d, code, cons)
    wb = Workbook()

    n_p0 = sum(1 for x in rows if x['Priority'].startswith('P0'))
    n_bad = sum(1 for x in rows if x['Conformant'] == 'no')
    n_nocons = sum(1 for x in rows if x['Consumers'] == '0' and x['Target Table'])

    # ---- Control ----
    ws = wb.active
    ws.title = 'Control'
    ws.sheet_view.showGridLines = False
    blocks = [
        ('NIRMĀṆA ASSET CONTROL WORKBOOK', 'title'),
        ('v3.0 — a plan of action for every asset in every layer, generated from live production measurements', 'sub'),
        ('', ''),
        ('PROVENANCE', 'h'),
        ('Generated', 'Live production read at generation time — re-run this script, never hand-edit'),
        ('Generator', '00_ARCHITECTURE/control/build_asset_control_workbook.py'),
        ('Companion plan', '00_ARCHITECTURE/NIRMANA_ELEVATION_PLAN_v3_0.md'),
        ('Status', 'PROPOSED — nothing in this workbook has been executed'),
        ('', ''),
        ('ASSET PROTECTION', 'h'),
        ('Removed', '2026-08-23, on native instruction — the campaign rebuilds all assets, so per-asset '
                    'DELETE/UPDATE/TRUNCATE guards are no longer wanted.'),
        ('Replaced by', 'A full logical snapshot taken immediately before removal: '
                        '00_ARCHITECTURE/control/snapshots/20260823_pre_protection_removal/'),
        ('Standing caution', 'ka_gochara_sweep\'s 38,287 v1 rows have NO registered writer — the @register was '
                             'removed at retirement. They cannot be rebuilt by the build system; the snapshot is '
                             'their only recovery path.'),
        ('', ''),
        ('SHEETS', 'h'),
        ('Layer Map', 'L0–L5 roll-up: population, conformance, health, cost, elevation thesis per layer.'),
        ('Asset Register', 'The master sheet. One row per asset — grounded fact, measured rows vs floor, conformance, plan, benefit.'),
        ('Asset Plans', 'THE plan of action for every asset: correctness & completeness · rebuild time · re-architecture & alignment · benefit. Identical to plan §13.'),
        ('Phase 0 Queue', 'The pre-flight work queue: every catalogue defect class with its recommendation.'),
        ('Elevation Plan', 'Per-asset actions and expected benefit, ordered by priority.'),
        ('Defect Register', 'Cross-cutting defects that no single asset owns.'),
        ('Infrastructure', 'Cloud Run, database and platform recommendations, ranked by measured value.'),
        ('Roadmap', 'Phases 0–6 with gates and live-verified acceptance criteria.'),
        ('', ''),
        ('HOW TO USE IT', 'h'),
        ('1', 'Phase 0 Queue is the current working surface. Nothing else starts until it is drained.'),
        ('2', 'Filter Asset Register by Conformant = no to get the per-asset reconciliation list.'),
        ('3', 'Filter by Priority for the working queue; by Tier to plan a wave.'),
        ('4', 'Sort by Worst (h) to see where wall-clock and interruption risk actually live.'),
        ('5', 'Re-run the generator after each phase; the workbook then shows movement, not a stale snapshot.'),
        ('', ''),
        ('CURRENT COUNTS', 'h'),
        ('Assets', f'{len(rows)} registered'),
        ('Contract violations', f'{n_bad} assets non-conformant'),
        ('P0 blocking', f'{n_p0} assets'),
        ('No serving consumer', f'{n_nocons} table-backed assets read by no MCP tool, API route or retrieval layer'),
        ('Protection rows remaining', f"{d['protection_rows']}"),
        ('', ''),
        ('LEGEND — LIFECYCLE (Contract §3.2)', 'h'),
        ('CURRENT', 'Live, buildable, authoritative for its output. Full contract conformance required.'),
        ('DRAFT', 'Registered, not yet authoritative. Must not be depended on by a CURRENT asset.'),
        ('RETIRED / SUPERSEDED_BY', 'No longer built; record retained. Requires a data disposition. Never deleted.'),
        ('SOURCE', 'Ingested data the DAG reads but never builds. Sits outside L0–L5.'),
        ('', ''),
        ('LEGEND — TIER', 'h'),
        ('G · Global substrate', 'Chart-independent, built once, reused by every chart. Cost amortises.'),
        ('H · Heavy partitioned', 'Substep plans, hours to days. Where wall-clock and interruption loss live.'),
        ('M · Medium deterministic', 'Seconds to minutes. The long tail that makes full rebuilds slow.'),
        ('S · Service probe', 'Health surfaces, not data writers.'),
        ('X · Generation-bearing', 'Carries multiple generations with a per-chart authority seam.'),
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
    cols = ['Layer', 'Name', 'Role in the instrument', 'Assets', 'Conformant', 'Violations', 'Global',
            'Services', 'Heavy', 'No resume', 'No consumer', 'Worst (h)', 'Native lit/stale/err',
            'Elevation thesis for this layer']
    ws.append(cols)
    head(ws, len(cols))
    for lx in ['L0', 'L1', 'L2', 'L3', 'L4', 'L5']:
        sub = [x for x in rows if x['Layer'] == lx]
        if not sub:
            continue
        heavy = [x for x in sub if x['Tier'].startswith('H')]
        nat = collections.Counter(x[CHARTS[0][1]] for x in sub)
        ws.append([lx, sub[0]['Layer Name'], LAYER_ROLE[lx], len(sub),
                   sum(1 for x in sub if x['Conformant'] == 'YES'),
                   sum(1 for x in sub if x['Conformant'] == 'no'),
                   sum(1 for x in sub if x['Scope'] == 'global'),
                   sum(1 for x in sub if x['Tier'].startswith('S')), len(heavy),
                   sum(1 for x in heavy if x['Resume'] == 'none'),
                   sum(1 for x in sub if x['Consumers'] == '0' and x['Target Table']),
                   round(max([x['Worst (h)'] or 0 for x in sub] or [0]), 1) or '',
                   f"{nat.get('lit',0)} / {nat.get('stale',0)} / {nat.get('error',0)+nat.get('incomplete',0)}",
                   layer_thesis(lx, sub)])
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

    # ---- Asset Register ----
    ws = wb.create_sheet('Asset Register')
    cols = ['Layer', 'Layer Name', 'Asset ID', 'Sanskrit', 'English', 'Tier', 'Priority', 'Lifecycle',
            'Superseded By', 'Data Disposition', 'Conformant', 'Contract Violations', 'Advisory',
            'Scope', 'Kind', 'Catalog', 'DAG Depth', 'Deps', 'Downstream', 'Consumers', 'Consumer Surfaces',
            'Target Table', 'count_sql', 'has_writer (registry)', 'has_writer (code)',
            'Substeps (registry)', 'Substeps (code)', 'Resume',
            'Median', 'P90', 'Worst', 'Worst (h)', 'Telemetry', 'Runs', 'Success %',
            'Rows (native)', 'Rows (abhinandan)', 'Rows (chart 3)', 'Floor', 'Completeness %', 'Integrity Check',
            CHARTS[0][1], CHARTS[1][1], CHARTS[2][1], 'Global',
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
        for k in ('Target Table', 'Writer File', 'Consumer Surfaces'):
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
        for cn in [CHARTS[0][1], CHARTS[1][1], CHARTS[2][1], 'Global']:
            cell = row[idx[cn]]
            cell.font = STATE_FONT.get(str(cell.value), Font(name='Menlo', size=9, color='9AA7A8'))
            cell.alignment = Alignment(horizontal='center', vertical='top')
        for cn in ('Elevation Actions', 'Expected Benefit', 'Data Disposition'):
            row[idx[cn]].alignment = Alignment(wrap_text=True, vertical='top')
        for cn in ('DAG Depth', 'Deps', 'Downstream', 'Consumers', 'Worst (h)', 'Runs', 'Success %',
                   'Rows (native)', 'Rows (abhinandan)', 'Rows (chart 3)', 'Floor', 'Completeness %'):
            row[idx[cn]].alignment = Alignment(horizontal='right', vertical='top')
            row[idx[cn]].number_format = '#,##0' if cn != 'Completeness %' else '0.0'
        ic = row[idx['Integrity Check']]
        ic.font = Font(size=9, bold=True, color='2E7A57' if ic.value == 'yes' else '9E3438')
        cp = row[idx['Completeness %']]
        if isinstance(cp.value, (int, float)) and cp.value < 95:
            cp.font = Font(size=9, bold=True, color='8E6210')
    widths(ws, [6, 11, 34, 20, 28, 22, 18, 15, 30, 42, 11, 40, 30, 10, 9, 9, 7, 6, 11, 10, 40, 30,
                9, 17, 15, 10, 10, 20, 9, 9, 9, 9, 20, 7, 9, 12, 12, 12, 11, 11, 10, 15, 13, 11, 8, 46, 78, 88])
    ws.freeze_panes = 'C2'
    ws.auto_filter.ref = f'A1:{get_column_letter(len(cols))}{ws.max_row}'

    # ---- Phase 0 Queue ----
    _append_phase0_queue(wb, rows)

    # ---- Asset Plans (plan of action for every asset, by layer) ----
    ws = wb.create_sheet('Asset Plans')
    cols = ['Layer', 'Asset ID', 'What it is', 'Where it stands now', 'Tier', 'Priority',
            '1 · Correctness & completeness', '2 · Rebuild time', '3 · Re-architecture & alignment', 'Expected benefit']
    ws.append(cols)
    head(ws, len(cols), h=34)
    for rec in rows:
        ws.append([rec['Layer'], rec['Asset ID'], rec['What'], rec['Now'], rec['Tier'], rec['Priority'],
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
    widths(ws, [6, 32, 40, 40, 20, 16, 70, 62, 62, 48])
    ws.freeze_panes = 'C2'
    ws.auto_filter.ref = f'A1:J{ws.max_row}'
    emit_plan_markdown(rows)

    # ---- Elevation Plan ----
    _append_elevation_plan(wb, rows)

    # ---- Defect Register ----
    ws = wb.create_sheet('Defect Register')
    cols = ['ID', 'Defect', 'Severity', 'Evidence', 'Consequence', 'Fix', 'Phase']
    ws.append(cols)
    head(ws, len(cols))
    for x in DEFECTS:
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

    # ---- Roadmap ----
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
    print('assets:', len(rows), '| non-conformant:', n_bad, '| P0:', n_p0,
          '| zero-consumer:', n_nocons, '| protection rows:', d['protection_rows'])
    print('tiers:', dict(collections.Counter(x['Tier'] for x in rows)))
    print('layers:', dict(collections.Counter(x['Layer'] for x in rows)))
    print('lifecycle:', dict(collections.Counter(x['Lifecycle'] for x in rows)))


def _append_phase0_queue(wb, rows):
    """The Phase 0 Queue sheet. Extracted so the v4.1 driver (build_control_workbook_v4_1.py)
    can reuse it verbatim — the six-source-census work items are unaffected by the scope ruling."""
    ws = wb.create_sheet('Phase 0 Queue')
    cols = ['Step', 'Defect class / work item', 'Severity', 'n', 'Assets affected', 'Why it matters', 'Recommendation']
    ws.append(cols)
    head(ws, len(cols))
    def ids(pred):
        a = [x['Asset ID'] for x in rows if pred(x)]
        return len(a), ', '.join(a)
    n_sub, s_sub = ids(lambda x: 'has_substeps false negative' in x['Contract Violations'])
    n_idx, s_idx = ids(lambda x: 'layer_index' in x['Contract Violations'])
    n_pre, s_pre = ids(lambda x: 'prefix ≠ layer' in x['Contract Violations'])
    n_kind, s_kind = ids(lambda x: 'kind/type/storage disagree' in x['Contract Violations'])
    n_ret, s_ret = ids(lambda x: x['Lifecycle'] in ('RETIRED', 'SUPERSEDED_BY'))
    n_nb, s_nb = ids(lambda x: 'never built on any chart' in x['Contract Violations'])
    n_nc, s_nc = ids(lambda x: x['Consumers'] == '0' and x['Target Table'])
    n_est, s_est = ids(lambda x: 'no estimated_seconds' in x['Advisory'])
    n_draft, s_draft = ids(lambda x: 'DRAFT but built and served' in x['Contract Violations'])
    q = [
        ('0.1', 'Six-source census', 'PROCESS', '6', 'registry · @register code · seed.ts · migrations · asset_throughput · CAPABILITY_MANIFEST',
         'Orphans live in the gaps between sources. A registry-only census would have missed the throughput row that made migration 563 fail silently.',
         'Reconcile all six into one authoritative list before any field-level work begins.'),
        ('0.2', 'Author the Asset Catalogue Contract', 'CRITICAL', '1', 'all assets',
         'The instruction "register the asset as per the system" cannot be followed because that system is not written down as an enforceable spec. This is the root cause of every row below.',
         'Write the per-kind required-field contract (plan §3.4) and make it the schema every later check reads.'),
        ('0.3', 'Lifecycle states + tombstone discipline', 'HIGH', str(n_ret), s_ret,
         'Retired rows carry FK dependants, audit history and (until today) protection references. Migration 563 already failed once on exactly this FK.',
         'Add lifecycle_state, superseded_by and data_disposition. Never DELETE a registry row (invariant I6).'),
        ('0.4', 'Semantic de-duplication', 'HIGH', '4', 'bodha_msr_signals (7 writers), chart_facts (5), brahma_class_priors (2), classical_text_chunks (2)',
         'All four multi-writer tables are legitimate co-writers partitioned by natural key. A naive dedup by target_table would destroy 14 valid assets.',
         'Enforce one authoritative producer per (table × generation × natural-key partition) — not one per table. Correct the ka_gochara generation attribution.'),
        ('0.5a', 'layer_index missing or mis-formatted', 'HIGH', str(n_idx), s_idx,
         'The cockpit orders and groups by layer_index. Nulls drop the asset into an ad-hoc bucket; two encodings coexist so string matches on "L3" silently miss assets stored as "3".',
         'Backfill and normalise to the Lx form; derive layer_name from layer in the locked lexicon; add NOT NULL + a CI pattern assert.'),
        ('0.5b', 'Asset id prefix does not match its layer', 'MEDIUM', str(n_pre), s_pre,
         'Ingested source data forced into a build layer corrupts that layer population count and its health arithmetic.',
         'Introduce the SOURCE classification outside L0–L5 and move it there.'),
        ('0.6a', 'has_substeps false negative', 'CRITICAL', str(n_sub), s_sub,
         'The orchestrator reads this flag to decide whether to run the substep-plan completeness check. When false, the no-op rescue promotes the asset to lit unconditionally — so a partial build is reported green. This silently disables the §N.8 gate.',
         'Derive has_substeps from the writer class at registration and assert code-vs-registry equality in CI. Backfill in a migration until then.'),
        ('0.6b', 'asset_type / asset_kind / storage_type disagree', 'MEDIUM', str(n_kind), s_kind,
         'Three columns disagree about which assets are services. The cockpit branches on type/kind, so a service marked data is rendered in the data ledger and expected to produce row counts.',
         'Collapse to asset_kind as authoritative; derive or drop the others; CI guard asserting they never disagree.'),
        ('0.7', 'Consumer map absent', 'HIGH', str(n_nc), s_nc,
         'The catalogue records downstream assets but not which MCP tools, API routes or retrieval layers read an asset table. Without it, "is it safe to retire this?" is unanswerable — and the count in this row is how many table-backed assets currently have no detected consumer.',
         'Build the asset → serving-surface index, make it a required field, and review every zero-consumer asset for retirement.'),
        ('0.8a', 'Registered but never built', 'MEDIUM', str(n_nb), s_nb,
         'An asset marked CURRENT that nothing can build and that has never existed on any chart is dead weight the catalogue reports as real.',
         'Flag dead assets explicitly; either provision a writer, demote to DRAFT, or retire with a disposition.'),
        ('0.8b', 'catalog_status has drifted from its meaning', 'HIGH', str(n_draft), s_draft,
         'DRAFT is defined as "registered, not yet authoritative", but these assets are actively built AND read by a serving surface — they are authoritative in practice. A status that covers half the catalogue cannot gate any decision.',
         'Promote to CURRENT, or record explicitly why each remains DRAFT. Then make catalog_status meaningful enough that a CURRENT asset may not depend on a DRAFT one.'),
        ('0.8c', 'Zero-consumer review', 'HIGH', str(n_nc), s_nc,
         'Each table-backed asset with no detected serving consumer is either a real asset whose consumer was never recorded, or dead weight the DAG still builds. Both readings need the consumer map to resolve.',
         'Resolve every one: record the missing consumer, or retire the asset with a data disposition.'),
        ('0.9', 'Telemetry repair / no estimated_seconds', 'MEDIUM', str(n_est), 'nearly all assets',
         'Advisory, not a registration defect — but every ETA is inferred from historical medians computed over run rows that are never closed on failure (observed maxima include 16.9 days).',
         'Close orphaned build_run_assets rows, recompute medians, backfill estimated_seconds, refresh on a schedule.'),
        ('0.10', 'CI enforcement', 'CRITICAL', '1', 'all assets',
         'A one-time cleanup decays within weeks — the seed was 17 rows behind before W0.1, and CURRENT_STATE §2 is still behind for three campaigns.',
         'Three-way guard (code ↔ seed ↔ live DB) plus contract conformance, prefix-matches-layer, CURRENT-may-not-depend-on-DRAFT, and the edge invariant — merged and BLOCKING.'),
        ('0.11', 'Freeze the baseline', 'PROCESS', '1', 'all assets',
         'Without a frozen baseline, later phases cannot tell whether a change is progress or regression.',
         'Tag the reconciled catalogue as the control-workbook baseline; every later phase measures drift against it rather than re-deriving truth.'),
    ]
    for x in q:
        ws.append(list(x))
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
            c.font = Font(size=9)
            c.border = BORDER
        row[0].font = Font(name='Menlo', size=11, bold=True, color=ACCENT)
        row[1].font = Font(size=10, bold=True)
        row[2].font = SEV_FONT.get(str(row[2].value), Font(size=9, color='647577'))
        row[4].font = Font(name='Menlo', size=8)
        ws.row_dimensions[row[0].row].height = 84
    widths(ws, [8, 34, 11, 6, 46, 66, 70])
    ws.freeze_panes = 'A2'


def _append_elevation_plan(wb, rows):
    """The Elevation Plan sheet. Extracted so the v4.1 driver can reuse it verbatim."""
    ws = wb.create_sheet('Elevation Plan')
    cols = ['Priority', 'Layer', 'Asset ID', 'Tier', 'Lifecycle', 'Worst run', 'Elevation Actions',
            'Expected Benefit After Implementation']
    ws.append(cols)
    head(ws, len(cols))
    rank = {'P0': 0, 'P1': 1, 'P2': 2, 'P3': 3}
    for rec in sorted(rows, key=lambda x: (rank[x['Priority'][:2]], x['Layer'], x['Asset ID'])):
        ws.append([rec['Priority'], rec['Layer'], rec['Asset ID'], rec['Tier'], rec['Lifecycle'],
                   rec['Worst'], rec['Elevation Actions'], rec['Expected Benefit']])
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical='top')
            c.font = Font(size=9)
            c.border = BORDER
        row[2].font = Font(name='Menlo', size=9, bold=True)
        row[0].font = PR_FONT.get(str(row[0].value)[:2], Font(size=9))
    widths(ws, [18, 7, 34, 22, 15, 10, 80, 90])
    ws.freeze_panes = 'A2'
    ws.auto_filter.ref = f'A1:H{ws.max_row}'


def emit_plan_markdown(rows, plan_path=None, extra_cols=False, generator_note=None):
    """Write the per-asset plan-of-action section into the plan file between markers,
    so the plan and the workbook are generated from the same derivation and cannot drift.

    plan_path   — defaults to v3.0's PLAN_PATH (legacy behaviour); the v4.1 driver passes
                  NIRMANA_ELEVATION_PLAN_v4_0.md's own path per §15's regeneration spec.
    extra_cols  — when True, appends the six §15 v4.1 columns (domain/rung/wave/continuation
                  class/rehearsal partition/timeout source) to each asset's table.
    """
    plan_path = plan_path or PLAN_PATH
    if not plan_path.exists():
        print('plan file not found; skipping markdown emit:', plan_path)
        return
    BEGIN, END = '<!-- ASSET_PLANS:BEGIN -->', '<!-- ASSET_PLANS:END -->'
    doc = plan_path.read_text()
    if BEGIN not in doc or END not in doc:
        print('markers missing in plan; skipping'); return
    names = {'L0': 'Brahmagyan', 'L1': 'Gaṇita', 'L2': 'Bodha', 'L3': 'Kāla', 'L4': 'Phala', 'L5': 'Mīmāṃsā'}
    note = generator_note or (
        "Generated by `build_asset_control_workbook.py` from live production measurements; "
        "identical to the workbook's **Asset Plans** sheet. Do not hand-edit between the markers.")
    out = [f'\n*{note}*\n']
    def cell(s):
        return (s or '—').replace('\n', '<br>').replace('|', '\\|')
    for lx in ['L0', 'L1', 'L2', 'L3', 'L4', 'L5']:
        sub = [x for x in rows if x['Layer'] == lx]
        if not sub:
            continue
        n_bad = sum(1 for x in sub if x['Conformant'] == 'no')
        n_p0 = sum(1 for x in sub if x['Priority'].startswith('P0'))
        heavy = [x for x in sub if x['Tier'].startswith('H')]
        out.append(f'\n### {lx} · {names[lx]} — {len(sub)} assets · {n_bad} non-conformant · {n_p0} P0 · {len(heavy)} heavy\n')
        out.append(f'*{LAYER_ROLE[lx]}.* {layer_thesis(lx, sub)}\n')
        for x in sorted(sub, key=lambda r: ({'P0':0,'P1':1,'P2':2,'P3':3}[r['Priority'][:2]], r['Asset ID'])):
            out.append(f"\n#### `{x['Asset ID']}` — {x['Tier']} · {x['Priority']} · {x['Lifecycle']}\n")
            out.append(f"**What:** {x['What'] or '—'}  \n**Now:** {x['Now']}\n")
            if extra_cols:
                out.append(f"**domain:** {x['Domain']} · **rung:** {x['Rung']} · **within-rung wave:** "
                            f"{x['Within-Rung Wave'] if x['Within-Rung Wave'] is not None else '—'} · "
                            f"**continuation class:** {x['Continuation Class']} · **rehearsal partition:** "
                            f"`{x['Rehearsal Partition']}` · **timeout source:** {x['Timeout Source']} "
                            f"*({x['Timeout Source Basis']})*\n")
                # §19 ledger, per asset — identical to the workbook's Efficiency sheet.
                out.append(f"\n**§19 efficiency ledger** · **p50:** {x['p50']} · **p90:** {x['p90']} · "
                            f"**worst:** {x['p_worst']} · **rows/sec:** {x['Rows/sec']} · "
                            f"**bound class:** {x['Bound Class']} · **hotspot:** {x['Hotspot']} · "
                            f"**technique:** {x['Technique']} · **target:** {x['Target']} · "
                            f"**speedup achieved:** {x['Speedup Achieved']} · "
                            f"**identity proof:** {x['Identity Proof']} · **profiled:** {x['Profiled']}  \n"
                            f"*Basis: {x['Efficiency Basis']}*\n")
            out.append('| Dimension | Plan of action |\n|---|---|')
            out.append(f"| Correctness & completeness | {cell(x['Correctness & Completeness Plan'])} |")
            out.append(f"| Rebuild time | {cell(x['Rebuild-Time Plan'])} |")
            out.append(f"| Re-architecture & alignment | {cell(x['Re-architecture & Alignment Plan'])} |")
            out.append(f"| Expected benefit | {cell(x['Expected Benefit'])} |")
    body = '\n'.join(out) + '\n'
    pre, rest = doc.split(BEGIN, 1)
    _, post = rest.split(END, 1)
    plan_path.write_text(pre + BEGIN + body + END + post)
    print('plan markdown emitted:', plan_path, f'({len(rows)} assets)')


DEFECTS = [
    ('D-01', 'has_substeps false negative', 'CRITICAL',
     '28 registered writers implement plan_substeps in code; 14 carry has_substeps=false. ka_sangam has 61 substep rows per chart recorded while the registry says it has none.',
     'The §N.8 completeness gate is skipped — partial builds are promoted to lit. The "partial" UI state is unreachable for these assets.',
     'Derive the flag from the writer class at registration; assert in CI; backfill.', 'P0'),
    ('D-02', 'Gochara protection keyed to the wrong asset id', 'RESOLVED',
     'build_protected_assets held ka_gochara/gen-3.0 while the gen-3.0 writer is ka_gochara_v3_century_materialize — which sat in error BUILD-PROTECTED.',
     'The guard blocked the authoritative writer.',
     'Superseded: all protection removed 2026-08-23 on native instruction, after a full logical snapshot. If protection is ever reinstated, key it on table+generation, not asset_id.', 'done'),
    ('D-03', 'Retired asset leaves permanent error rows', 'HIGH',
     'ka_gochara_sweep is inactive and RETIRED yet holds asset_throughput rows on two charts producing "no writer registered".',
     'Permanent reds no operator action can clear; erodes trust in every other red.',
     'Supported retire/rename/supersede lifecycle operation that repoints dependants and clears throughput.', 'P0'),
    ('D-04', 'Watchdog reads transaction-start time as liveness', 'HIGH',
     'The watchdog uses NOW() in 16 places; clock_timestamp() appears nowhere in the repo. ka_kshetra was reaped at 301 of 308 committed substeps.',
     'Long-running substeps look dead; the most expensive asset loses ~6h of committed work.',
     'Switch heartbeat and watchdog windows to clock_timestamp(); read build_substep_progress as primary liveness.', 'P2'),
    ('D-05', 'Two divergent staleness cascades run per completion', 'HIGH',
     "staleness.py matches (lit, service_ok) and measures the prior state; the inline copy matches (lit, mature) and hardcodes from_state='lit'.",
     'Propagation is non-deterministic between paths and one emits an unearned event field.',
     'Delete the inline cascade; staleness.py becomes sole owner.', 'P2'),
    ('D-06', 'Freshness decided by timestamps, not content', 'CRITICAL',
     'The upstream hash hashes last_built_at values; the writer hash is a git SHA. Neither is ever read — isStale() has no production caller.',
     'Any upstream rebuild invalidates its whole downstream cone even when output is byte-identical. Root cause of "a small L1 change stales the whole DAG".',
     'Re-point to content digests and a source-content writer hash; read at plan time; grade staleness.', 'P3'),
    ('D-07', 'Substep plan totals never persisted', 'MEDIUM',
     'build_substep_progress has no planned-total column; the stats route hardcodes total=null.',
     'The cockpit shows a committed count with no denominator; the watchdog has no progress signal.',
     'Persist the plan total at plan time and surface it.', 'P2'),
    ('D-08', 'No retry logic anywhere in the orchestrator', 'HIGH',
     'runner.py contains no retry/backoff/attempt logic. 45.6% of asset attempts reach complete (3,255 of 7,144).',
     'Every transient failure becomes a manual re-dispatch; operators built /tmp restart loops to compensate.',
     'Error taxonomy plus retry with backoff at savepoint granularity; multi-dispatch continuation.', 'P4'),
    ('D-09', 'Resume protocol forked into three private copies', 'MEDIUM',
     'ka_kshetra, ka_gochara_sweep and ka_sangam each carry a private resume protocol; two independently reached _RESUME_VERSION = 7. The orchestrator primitive completed_keys is passed by no caller.',
     '20 heavy assets have no resume at all; the three that do must be maintained by hand.',
     'One shared ResumableWriter mixin; wire completed_keys; per-substep input digests.', 'P4'),
    ('D-10', 'Cockpit state contradicts the planner', 'HIGH',
     "deriveState returns lit whenever rows > 0, so 'stale' is unreachable with data; the planner gates on raw throughput state.",
     'An asset renders green and then blocks the build with UPSTREAM_BLOCKED.',
     "Render stale-with-data as amber using the planner's own predicate.", 'P2'),
    ('D-11', 'Refresh action mutates nothing', 'MEDIUM',
     'The refresh route only bumps updated_at — a column nothing reads — and inserts dormant rows.',
     'The one control an operator reaches for when state looks wrong cannot repair state.',
     'Make it a real reconciler (recount, re-probe, recompute freshness) or remove it.', 'P2'),
    ('D-12', 'State vocabulary disagrees across three layers', 'MEDIUM',
     'The CHECK constraint allows six states; service_ok and mature appear in Python and TypeScript but cannot be stored. mature appears exactly once, in the dead inline cascade.',
     'Any attempt to write those states raises; the type union promises states the database refuses.',
     'One enum across DB, Python and TypeScript, asserted in CI.', 'P2'),
    ('D-13', 'Build telemetry polluted by unclosed rows', 'MEDIUM',
     'Observed maxima include ga_positions at 16.9 days and ga_sade_sati at 4.4 days. estimated_seconds is populated on 2 of 128 assets.',
     'Every ETA and cost-of-action number is computed from corrupted data.',
     'Close orphaned rows, recompute medians, backfill estimates, refresh on a schedule.', 'P0'),
    ('D-14', 'Service probes can sit red indefinitely', 'HIGH',
     'bg_ephemeris_engine was in error from 2026-06-18 — 66 days — with a missing ephemeris file.',
     'A core global capability degraded with nothing surfacing it.',
     'Real probes with SLOs, alerting, and a dedicated cockpit service lane.', 'P2'),
    ('D-15', 'The state-audit spine exists and is unused', 'LOW',
     'asset_throughput_state_audit (migration 586) holds a handful of rows and is read by nothing.',
     'No build history surface, even though the substrate for one now exists.',
     'Adopt it as the event spine for run history, provenance and the timeline view.', 'P6'),
    ('D-29', 'has_writer false negative — a registry boolean that exempts an asset from the efficiency gate', 'CRITICAL',
     'The AST @register census finds 123 asset_ids bound to a writer class in production source; asset_registry carries has_writer=true on 121. Measured 2026-08-23 against live production: exactly 2 false negatives (bg_nakshatra_medical, @register at brahmagyan/writers/bg_medical_mappings.py:26; bg_transit_engine, @register at brahmagyan/writers/bg_transit_rules.py:12) and 0 false positives. Both are SECONDARY decorators stacked on a shared writer class — the general shape, not two special cases.',
     "D-01's sibling, one column over: a registry boolean that DISAGREES WITH THE CODE and, when false, silently disables a check. _bound_class() reads has_writer=false as \"no registered writer -> nothing builds this asset\" and returns bound class `not-a-build`, which exempts the asset from the §8.3 item 5 efficiency pass ALTOGETHER — not \"optimized with an identity proof\", not \"examined, already efficient\", but unexamined. Two genuinely-built R0 assets would have walked through the campaign's first freeze gate on that exemption.",
     'Generator side, done (M0-T22 / D-25 part 2a): the workbook DERIVES has_writer from the writer class via the M0-T8 AST census and carries `has_writer (registry)` + `has_writer (code)` as a visible pair, so the two assets now read bound class = null and are back inside the efficiency gate. Registry side, NOT done and deliberately deferred (D-25 part 2b): correcting the two asset_registry.has_writer ROWS belongs to R0 stage 2 (Conform), which owns R0 registry metadata, and opens there with this measurement in hand. STANDING RULE (D-25 part 3): any registry boolean that gates whether a check runs must be derived from code, never trusted as declared, and surfaced as a registry-vs-code pair.', 'R0'),
    ('D-16', 'Hash spill directory is RAM-backed on Cloud Run', 'HIGH',
     'KA_KSHETRA_HASH_SPILL_DIR is pinned to /tmp, which on Cloud Run is a tmpfs. A 3–4.2 GB spill counts against the 8Gi limit, inverting the bounded-memory guarantee the spill was built to provide.',
     'OOM risk on the single largest asset; the compensating fix was doubling job memory rather than fixing the substrate.',
     'Mount a real volume (Cloud Storage FUSE or a disk) and point the spill dir at it. The repo currently has zero Cloud Run volume mounts.', 'P1'),
]

INFRA = [
    ('1', 'Cloud Run', 'Real volume for the hash spill directory', 'DO IT',
     'KA_KSHETRA_HASH_SPILL_DIR=/tmp on Cloud Run is RAM-backed tmpfs; a 3–4.2 GB spill counts against the 8Gi job limit. The repo has zero Cloud Run volume mounts anywhere.',
     'Mount a disk or Cloud Storage FUSE volume and point the spill directory at it. This is the only infrastructure item that fixes a live correctness/OOM risk rather than buying headroom.', 'P1'),
    ('2', 'Database', 'Connection pooler (PgBouncer / Cloud SQL connector pooling)', 'HIGH VALUE',
     'Parallelism is capped by a connection budget, not CPU: the orchestrator enforces MAX_CONCURRENT_RUNS × (1 + WORKER_LIMIT) ≤ ~33. WORKER_LIMIT is 4.',
     'A pooler decouples worker count from backend connections, letting width rise where the DAG is actually wide (L0+L1 hold 60 of 128 assets). Without it, raising WORKER_LIMIT just exhausts connections.', 'P5'),
    ('3', 'Database', 'Partition the largest tables by chart_id', 'HIGH VALUE',
     'ka_kshetra writes 10.5M rows per chart. §N.3 idempotency is delete-then-insert, so every rebuild deletes and reinserts millions of rows, generating heavy bloat.',
     'Partition by chart_id so a per-chart rebuild becomes DROP PARTITION — instant, no bloat, and structurally incapable of touching another chart. This is also the natural stepping stone to the per-chart database plan, and it makes DELETE-protection triggers unnecessary.', 'P4'),
    ('4', 'Database', 'Autovacuum tuning on high-churn build tables', 'WORTH DOING',
     'Delete-then-insert at 10.5M-row scale on every rebuild is the heaviest churn pattern in the system; default autovacuum thresholds are tuned for far gentler workloads.',
     'Per-table autovacuum settings on the largest build targets, sized to the rebuild pattern rather than the defaults.', 'P4'),
    ('5', 'Cloud Run', 'Multi-dispatch continuation instead of a bigger machine', 'DO IT (as code)',
     'Cloud Run Jobs have a task wall-clock ceiling; ka_gochara_sweep historically needed roughly five dispatches, and operators wrote /tmp watch-loops to chain them.',
     'Solve in the orchestrator (Phase 4), not the infrastructure: a run that hits the ceiling re-dispatches itself until its plan is complete.', 'P4'),
    ('6', 'Observability', 'Per-substep tracing and build metrics', 'WORTH DOING',
     'Diagnosing a slow or failed build today means reading logs. There is no span-level timing, and asset_throughput_state_audit — the natural event spine — holds a handful of rows and is read by nothing.',
     'OpenTelemetry spans per asset and per substep, exported alongside the audit spine, so the cockpit timeline and the cost model read measured data rather than inference.', 'P6'),
    ('7', 'Cloud Run', 'CPU / memory sizing', 'NOT THE BOTTLENECK',
     'The job was already raised to 8Gi / 4 CPU. But 18 of 21 DAG levels are narrower than the existing worker pool of 4 — the build is serial from L3 down, so added cores idle.',
     'Do not spend here until Phases 3–5 land. Content addressing, resume and edge pruning change wall-clock; a bigger machine does not. Re-measure afterwards and size from data.', 'defer'),
    ('8', 'Database', 'Per-chart databases', 'LATER — hybrid shape',
     'Native intent, correctly deferred. Note the constraint: 44 of 128 assets are global scope (chart-independent substrate) and amortise across charts; L5 calibration and cohort priors are inherently cross-chart.',
     'When the time comes, the shape that works is hybrid: one shared reference database for the global substrate, one database per chart for L1–L5. Partitioning by chart_id (item 3) is the migration path — it gets most of the isolation benefit now and makes the eventual split mechanical.', 'later'),
    ('9', 'Process', 'Formalise a rehearsal chart', 'WORTH DOING',
     'Chart 3 (cb73cd3d) is already in poor health (31 lit / 14 stale / 14 error) and is not a serving target, while both canonical charts are.',
     'Designate it the standing rehearsal subject for destructive and first-run operations, so no elevation step is ever first executed against a canonical chart.', 'P1'),
    ('10', 'Process', 'Determinism harness', 'WORTH DOING',
     'There is no test that builds an asset twice and compares output. Content addressing (Phase 3) assumes determinism it never verifies.',
     'Build-twice-and-compare-digests for a representative asset per tier. This doubles as the acceptance test for Phase 3 and would have caught the frozen-score defect that the scoring-signature fix later had to repair.', 'P3'),
]


def roadmap(total, n_p0, n_bad, heavy_n, svc_n):
    return [
        ('0', 'Pre-flight · asset catalogue reconciliation', 'own phase', 'No',
         'Six-source census; author the contract; lifecycle and tombstone discipline; semantic de-duplication; layer organisation and the SOURCE class; the catalogue-truth defects; consumer map; build-coverage audit; CI enforcement; freeze the baseline.',
         'Every exit check returns zero, verified live — three-way diff, contract violations, prefix mismatches, dangling edges, duplicate producers, orphan throughput rows, retired assets without a disposition — AND the CI guard for all of it is merged and blocking.',
         f'{n_bad} non-conformant of {total}'),
        ('1', 'Runtime truth debris', 'days', 'No',
         'Runtime truth debris AND parity: lifecycle retirement of the zombie asset; the 66-day ephemeris red; register hand-applied migrations 588/589 with the tracked runner; real volume for the spill directory; chart 3 brought to parity (29 empty assets rebuilt) and designated the rehearsal subject, with a gochara authority row; the 5 Abhinandan-empty assets rebuilt; ga_prashna (zero rows) and ga_sade_sati (57% of floor) investigated and rebuilt; the F-52 rematerialization decision recorded.',
         'Error counts drop on all three charts; chart 3 matches the canonical charts\' asset population; every remaining red has a named owner.',
         f'{n_p0} P0 assets + {svc_n} services'),
        ('2', 'Truth and safety', 'days', 'One deletion',
         'Amber stale-with-data; delete the duplicate cascade; persist substep totals; clock_timestamp() heartbeat; real-or-removed Refresh; state vocabulary reconciled; generation/authority in the UI; cascade-root collapse; service-health lane; INTEGRITY GATE live for every data asset (lit is earned, §4.1); honest floors on every chart (§4.2); completeness % in the cockpit.',
         'A heavy build survives a full substep without a reap. An asset whose integrity check fails cannot reach lit. No asset lacks a floor.',
         'cockpit + orchestrator'),
        ('3', 'Content-addressed freshness', '1–2 weeks', 'Yes',
         'Output digests on every asset; upstream-digest freshness with early cutoff; source-content writer hash read at plan time; graded staleness; dead staleness spec wired or deleted; determinism harness; L1 verification-tier programme begins (80.7% single today).',
         'Identical-content upstream rebuild leaves downstream fresh, live. Editing a writer marks exactly that asset stale:code. Harness passes for one asset per tier. single share at L1 measured and falling.',
         f'all {total}'),
        ('4', 'Receipts and robust execution', '~2 weeks', 'Yes',
         'Shared ResumableWriter mixin replacing three private copies; per-substep input digests; error taxonomy and retry; multi-dispatch continuation; chart_id partitioning; resume-run and rebuild-failed-only.',
         'A deliberately interrupted heavy build resumes without losing committed substeps. A transient failure recovers with no human dispatch. Completion rate measured against the 45.6% baseline.',
         f'{heavy_n} heavy assets'),
        ('5', 'DAG management', '~1 week', 'Yes',
         'Edge provenance; declared-vs-read dependency audit; published critical path; blast radius on pull request; connection pooler so width can rise where the DAG is wide. Shape guards already landed in Phase 0.',
         'The critical path is published per chart, and at least one over-declared edge is removed with a measured wall-clock reduction.',
         'DAG-wide (21 levels)'),
        ('6', 'Operator experience', '1–2 weeks', 'No (UI only)',
         'Blast-radius preview, provenance panel, run timeline from the audit spine, failure triage, generation display, multi-chart view, per-substep tracing, and the polish sweep.',
         'An operator can answer without leaving the cockpit: what is stale and why, what this action costs, which fault is behind the red, and what happened on the last run.',
         'cockpit (23 components)'),
    ]


if __name__ == '__main__':
    main()
