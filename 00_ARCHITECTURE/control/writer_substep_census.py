#!/usr/bin/env python3
"""writer_substep_census.py — AST (not regex) census of registered writer classes.

Authored for Nirmāṇa task M0-T8 (Phase 0.6a). Durable and re-runnable: it is the
truth source behind DERIVED_FIELD_REPAIR_PROPOSAL_v1_0.md §4 and behind that
document's detector D-3 ("re-run the census and diff").

READ-ONLY. It touches no database and imports no project module — it only calls
ast.parse over source text, which is also how it satisfies D-9 (nothing under the
migrations tree is ever imported or executed).

REUSED, NOT RE-IMPLEMENTED (Nirmāṇa M0-T22 / D-25 part 2a): this module is now
importable. `census()` returns the full record and `registered_asset_ids()` returns
just the set of asset_ids that carry a @register decorator in production source —
which is the code-derived truth behind the workbook's `has_writer (code)` column.
D-25 part 3's standing rule ("any registry boolean that gates whether a check runs
must be derived from code") is served by that one function, so there is exactly ONE
AST parser for @register in the control plane, not a second one per consumer.

Two traps this parser exists to avoid, both found the hard way in M0-T8:
  · a regex over source text counts docstring mentions of `@register(` as writers;
  · a naive AST pass drops the `@register(ASSET_ID)` module-constant form (4 writers
    missed, 2 of them HEAVY). Both forms — and the class-attribute form — resolve here,
    and anything that does NOT resolve lands in `unresolved_registrations` rather than
    being silently dropped. `registered_asset_ids()` ASSERTS that list is empty.

Writers live in TWO trees under platform/python-sidecar — `writers/` and
`services/*/writer.py`. This scan is a full rglob over the sidecar, so both are covered
(measured 2026-08-23: 112 registrations under writers/, 11 under services/).

M0-T8 0.6a — AST (not regex) census of registered writer classes.

For every class decorated with @register('<asset_id>') anywhere under
platform/python-sidecar (excluding test trees), record which of the FROZEN
contract methods it defines, resolving inheritance through the collected
class graph. NO imports are executed (D-9: never import the migrations tree
or run module-level code); this is pure ast.parse over source text.
"""
import ast, json, os, pathlib, sys


def repo_root() -> pathlib.Path:
    """The repository root, DERIVED FROM THIS FILE'S OWN LOCATION.

    Nirmāṇa M0-T28 / F-2. This module used to pin
    `ROOT = pathlib.Path('/Users/Dev/Vibe-Coding/Apps/Madhav')` — one developer's
    absolute path, baked in when it was a run-once script. On any other machine (CI,
    a second checkout, a container) that directory does not exist, so `BASE.rglob`
    yielded nothing and `census()` returned `files_scanned=0, n_registrations=0`
    while `registered_asset_ids()` handed back an EMPTY SET WITHOUT RAISING. Every
    consumer tests membership (`aid in code_writers`), so an empty set reads as
    "no asset has a registered writer" — which makes `_bound_class()` return
    `not-a-build` for all 128 assets and EXEMPTS THE ENTIRE CATALOGUE from the
    §8.3 item 5 efficiency gate, silently and looking entirely normal.

    This is the same defect shape the campaign already fixed once in D-1
    (`heartbeat.sh` hard-required `NIRMANA_REPO`, which the launcher never provided,
    so every heartbeat aborted and the fleet's liveness detector was disarmed), and
    it takes the same remedy D-1 prescribed: derive the root from the script's own
    location, and keep the environment variable as an OVERRIDE ONLY, never a
    requirement. `__file__` is `<root>/00_ARCHITECTURE/control/writer_substep_census.py`,
    so the root is `parents[2]`.

    `NIRMANA_REPO` is honoured when set, for the one legitimate case of pointing the
    census at a checkout other than the one this file lives in. It cannot reintroduce
    the silent failure: a root that does not contain the writer tree produces an empty
    scan, and an empty scan is now LOUD (see `_assert_trustworthy`).
    """
    env = os.environ.get('NIRMANA_REPO')
    if env:
        return pathlib.Path(env).expanduser().resolve()
    return pathlib.Path(__file__).resolve().parents[2]


ROOT = repo_root()
BASE = ROOT/'platform/python-sidecar'

EXCLUDE_PARTS = {'__pycache__', 'node_modules', '.clone', 'tests', '__tests__', 'venv', '.venv', 'site-packages', 'build', 'dist'}

def dotted(node):
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.Attribute):
        p = dotted(node.value)
        return f'{p}.{node.attr}' if p else node.attr
    return None


# ── resume-mechanism vocabulary ──────────────────────────────────────────────
# Nirmāṇa M0-T30 / F-5. These token sets are CARRIED OVER UNCHANGED from
# `build_asset_control_workbook.scan_code()`, deliberately: M0-T30's task was the
# ATTRIBUTION mechanism (which code the tokens are looked for in), not the
# vocabulary (which tokens count as a resume protocol). Changing both at once would
# make any value change unattributable, which is the same discipline §19 imposes on
# optimizations. Widening the vocabulary is a content decision and is NOT taken here
# — see the M0-T30 report on `bg_gochara_arcs`, whose class calls `arc_fingerprint`,
# a delta mechanism no token names.
RESUME_SUBSTEP_TOKENS = ('_RESUME_VERSION', 'build_fingerprint')
RESUME_DELTA_TOKENS = ('compute_substep_fingerprint', 'class_fingerprint', 'scoring_signature')


def class_identifiers(node: ast.ClassDef) -> set:
    """Every IDENTIFIER appearing anywhere in a class's own subtree.

    Deliberately NOT a text scan of the class's source lines, and deliberately NOT
    including string constants — those two exclusions are the whole point:

      · **comments and docstrings are invisible to `ast.walk`.** This is the docstring
        trap that produced M0-T28's `bg_reference` false positive one column over, and
        it is live in this very column: `writers/ka_gochara_sweep.py` is a RETIRED
        tombstone (`__all__ = []`, no executable `@register` at all) whose docstring
        names `@register('ka_gochara')` and `@register('ka_gochara_sweep')`. A regex
        read both of those as registrations.
      · **string constants are excluded** because `build_fingerprint` occurs mostly
        inside SQL text. A writer that merely SELECTs a column named
        `build_fingerprint` from someone else's table has not thereby implemented a
        resume protocol; a writer that *maintains* one names it as an identifier
        (`_RESUME_VERSION`, `_compute_build_fingerprint`, `class_fingerprint(...)`).

    Method names are included, so `_compute_build_fingerprint` matches the
    `build_fingerprint` token by substring exactly as it did before.
    """
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Name): out.add(n.id)
        elif isinstance(n, ast.Attribute): out.add(n.attr)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)): out.add(n.name)
        elif isinstance(n, ast.ClassDef): out.add(n.name)
        elif isinstance(n, ast.arg): out.add(n.arg)
        elif isinstance(n, ast.keyword) and n.arg: out.add(n.arg)
        elif isinstance(n, ast.alias): out.add((n.asname or n.name).split('.')[-1])
    return out


def resume_from_identifiers(idents) -> str:
    """`none` | `substep_fingerprint` | `delta_fingerprint`, from a class's identifiers.

    Same precedence the file-granular version used: a delta token outranks a substep
    token when both are present.
    """
    joined = '\n'.join(sorted(idents))
    out = 'none'
    if any(tok in joined for tok in RESUME_SUBSTEP_TOKENS): out = 'substep_fingerprint'
    if any(tok in joined for tok in RESUME_DELTA_TOKENS): out = 'delta_fingerprint'
    return out


_CACHE = None


def census(force: bool = False) -> dict:
    """Run the AST census and return its record. Cached — repeated callers in one
    process re-use the single parse. Pure function of source text on disk."""
    global _CACHE
    if _CACHE is not None and not force:
        return _CACHE

    classes = {}      # (module, classname) -> record
    class_idents = {}  # (module, classname) -> set of identifiers in the class subtree
    unresolved_registrations = []
    registrations = []  # {asset_id, module, classname, lineno}
    by_name = {}      # classname -> [ (module, classname) ]
    parse_errors = []
    files_scanned = 0

    for p in sorted(BASE.rglob('*.py')):
        rel = p.relative_to(ROOT)
        if any(part in EXCLUDE_PARTS for part in rel.parts): continue
        files_scanned += 1
        try:
            tree = ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
        except (SyntaxError, UnicodeDecodeError) as e:
            parse_errors.append(f'{rel}: {e}'); continue
        mod = str(rel)
        # module-level string constants, so @register(ASSET_ID) resolves
        modconsts = {}
        for b in tree.body:
            if isinstance(b, ast.Assign):
                for t in b.targets:
                    if isinstance(t, ast.Name) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                        modconsts[t.id] = b.value.value
            elif isinstance(b, ast.AnnAssign) and isinstance(b.target, ast.Name) \
                    and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                modconsts[b.target.id] = b.value.value
        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef): continue
            methods = set()
            has_substeps_attr = None
            asset_id_attr = None
            for b in node.body:
                if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.add(b.name)
                elif isinstance(b, ast.Assign):
                    for t in b.targets:
                        if isinstance(t, ast.Name) and t.id == 'has_substeps':
                            if isinstance(b.value, ast.Constant): has_substeps_attr = b.value.value
                        if isinstance(t, ast.Name) and t.id == 'asset_id':
                            if isinstance(b.value, ast.Constant): asset_id_attr = b.value.value
                elif isinstance(b, ast.AnnAssign) and isinstance(b.target, ast.Name):
                    if b.target.id == 'has_substeps' and isinstance(b.value, ast.Constant):
                        has_substeps_attr = b.value.value
                    if b.target.id == 'asset_id' and isinstance(b.value, ast.Constant):
                        asset_id_attr = b.value.value
            bases = [dotted(b) for b in node.bases]
            key = (mod, node.name)
            classes[key] = {'module': mod, 'classname': node.name, 'bases': bases,
                            'methods': sorted(methods), 'has_substeps_attr': has_substeps_attr,
                            'asset_id_attr': asset_id_attr, 'lineno': node.lineno}
            # Kept OUT of `classes[key]` on purpose: identifier sets are large, they are
            # an internal intermediate, and `classes` is what __main__ serialises.
            class_idents[key] = class_identifiers(node)
            by_name.setdefault(node.name, []).append(key)
            for dec in node.decorator_list:
                fn = dec.func if isinstance(dec, ast.Call) else dec
                name = dotted(fn)
                if name and name.split('.')[-1] == 'register' and isinstance(dec, ast.Call):
                    aid = None; how = None
                    if dec.args and isinstance(dec.args[0], ast.Constant):
                        aid, how = dec.args[0].value, 'literal'
                    elif dec.args and isinstance(dec.args[0], ast.Name) and dec.args[0].id in modconsts:
                        aid, how = modconsts[dec.args[0].id], f'module_const:{dec.args[0].id}'
                    elif dec.args and isinstance(dec.args[0], ast.Attribute) and asset_id_attr:
                        aid, how = asset_id_attr, 'class_attr'
                    if aid is None:
                        unresolved_registrations.append({'module': mod, 'classname': node.name,
                                                         'lineno': node.lineno,
                                                         'arg': ast.dump(dec.args[0]) if dec.args else '<no args>'})
                    else:
                        registrations.append({'asset_id': aid, 'module': mod, 'how': how,
                                              'classname': node.name, 'lineno': node.lineno})

    def resolve(key, seen=None):
        """Walk the class's own methods then its bases (by simple name) within the
        collected graph. Returns (defines_map, chain, identifiers).

        `identifiers` (M0-T30 / F-5) is the union of the class's own identifiers and
        those of its PROJECT-LOCAL ancestors, resolved by the same base-picking rule
        the method map uses — one traversal, one set of tie-breaks, so the resume
        signal and the substep signal can never be attributed differently.
        `WriterBase` contributes nothing here for the same reason it contributes no
        methods: it is the FROZEN base every writer has, so anything it defined would
        be a CONSTANT across all 123 registrations, not a discriminator.
        """
        seen = seen or set()
        if key in seen: return {}, [], set()
        seen.add(key)
        rec = classes[key]
        out = {m: key for m in rec['methods']}
        chain = [f"{rec['module']}::{rec['classname']}"]
        idents = set(class_idents.get(key, ()))
        attr = rec['has_substeps_attr']
        for b in rec['bases']:
            if not b: continue
            simple = b.split('.')[-1]
            if simple == 'WriterBase':
                chain.append('WriterBase(frozen base)'); continue
            cands = by_name.get(simple, [])
            # prefer a candidate in the same module, else unique match
            pick = None
            for c in cands:
                if c[0] == rec['module']: pick = c; break
            if pick is None and len(cands) == 1: pick = cands[0]
            if pick is None:
                chain.append(f'UNRESOLVED_BASE:{b}'); continue
            sub, subchain, subids = resolve(pick, seen)
            for m, k in sub.items(): out.setdefault(m, k)
            chain.extend(subchain)
            idents |= subids
            if attr is None and classes[pick]['has_substeps_attr'] is not None:
                attr = classes[pick]['has_substeps_attr']
        rec['_inherited_has_substeps'] = attr
        return out, chain, idents

    results = {}
    dupes = {}
    for r in registrations:
        key = (r['module'], r['classname'])
        defines, chain, idents = resolve(key)
        rec = classes[key]
        plan = 'plan_substeps' in defines
        runsub = 'run_substep' in defines
        runm = 'run' in defines
        # FROZEN contract (writers/__init__.py WriterBase docstring):
        #  HEAVY = overrides BOTH plan_substeps and run_substep
        #  LIGHT = implements run()
        truth = plan and runsub
        results.setdefault(r['asset_id'], []).append({
            'module': r['module'], 'classname': r['classname'], 'lineno': r['lineno'], 'register_arg': r['how'],
            'defines_plan_substeps': plan, 'plan_substeps_from': defines.get('plan_substeps', [None])[1] if plan else None,
            'defines_run_substep': runsub, 'run_substep_from': defines.get('run_substep', [None])[1] if runsub else None,
            'defines_run': runm,
            'class_attr_has_substeps': rec['has_substeps_attr'],
            'inherited_has_substeps': rec.get('_inherited_has_substeps'),
            'mro_chain': chain,
            'writer_truth_has_substeps': truth,
            # M0-T30 / F-5: attributed to the CLASS, not to the file it happens to
            # share with other registrations, and not to a neighbouring service package.
            'resume_mechanism': resume_from_identifiers(idents),
            'shape': 'HEAVY' if truth else ('LIGHT' if runm else ('PARTIAL_plan_only' if plan else ('PARTIAL_runsubstep_only' if runsub else 'NEITHER'))),
        })
    for a, v in results.items():
        if len(v) > 1: dupes[a] = v

    _CACHE = {'unresolved_registrations': unresolved_registrations, 'files_scanned': files_scanned,
              'parse_errors': parse_errors,
              'n_registrations': len(registrations), 'n_distinct_asset_ids': len(results),
              'duplicate_asset_ids': dupes, 'writers': results,
              # M0-T28 / F-2: WHAT WAS SCANNED, recorded alongside what was found. An
              # empty census is indistinguishable from a healthy one unless the record
              # says where it looked. `census()` itself does NOT raise — it is the raw
              # measurement, and "I scanned 0 files under <path>" is a true and useful
              # thing for it to report (the C-23 guard writes exactly these fields into
              # its `not_checkable` provenance). The refusal to emit a value from an
              # empty census lives in the DERIVED accessors below, which have no channel
              # for "I don't know" and must therefore raise.
              'scan_root': str(ROOT), 'scan_base': str(BASE), 'base_exists': BASE.exists()}
    return _CACHE


def _assert_trustworthy(c: dict, what: str) -> dict:
    """Refuse to hand back a DERIVED value from a census that does not know the answer.

    H4/§N.8, and D-25 part 3 in its sharpest form: a value that can turn a detector off
    must never arrive by accident. Every condition below means the parser did not see the
    writer tree, or saw it incompletely — and in each case the natural return value
    (a short set, a short map) is silently indistinguishable from a true measurement of a
    codebase that has no writers. There is no in-band way to say "I don't know" in a
    `set` or a `dict[str, bool]` whose consumers test membership, so this raises.

    THE EMPTY CASE IS THE ONE M0-T28 ADDED, and it is the reason F-2 was dangerous rather
    than merely wrong: the two pre-existing guards (unresolved args, parse errors) both
    require something to have been parsed, and neither can fire when there is nothing to
    parse at all. An absent writer tree therefore sailed through both.

    `census()` itself deliberately does NOT raise — see the note on its record. Callers
    that want the diagnostic detail rather than an exception (the C-23 guard) call
    `census()` and inspect `files_scanned` / `n_registrations` / `base_exists` themselves.
    """
    if not c.get('base_exists'):
        raise SystemExit(
            f'writer_substep_census: the writer tree does not exist at {c.get("scan_base")!r} '
            f'(scan root {c.get("scan_root")!r}) — {what} CANNOT be derived and no value may '
            f'be emitted from an empty scan. Set NIRMANA_REPO to a checkout that contains '
            f'platform/python-sidecar, or run this module from inside one.')
    if c['unresolved_registrations']:
        raise SystemExit(
            f'writer_substep_census: UNRESOLVED @register argument(s) — {what} is NOT '
            'trustworthy and no value may be emitted from it: '
            + repr(c['unresolved_registrations']))
    if c['parse_errors']:
        raise SystemExit(
            f'writer_substep_census: source files failed to parse — {what} is incomplete: '
            + repr(c['parse_errors']))
    if not c['files_scanned'] or not c['n_registrations']:
        raise SystemExit(
            f'writer_substep_census: scanned {c["files_scanned"]} file(s) under '
            f'{c.get("scan_base")!r} and found {c["n_registrations"]} @register decorator(s). '
            f'{what} would be EMPTY, and an empty writer set does not read as "unknown" '
            f'downstream — it reads as "nothing builds any asset", which exempts every asset '
            f'from the §8.3 item 5 efficiency gate (§19 / D-25 part 3). Refusing to emit it.')
    return c


def registered_asset_ids(force: bool = False) -> set:
    """The code-derived truth for `has_writer`: every asset_id that a production
    @register decorator binds to a writer class.

    D-25 part 2(a)/2(c): the caller must NOT special-case any asset id. The two
    R0 assets the defect was found on (bg_nakshatra_medical, bg_transit_engine) are
    SECONDARY decorators stacked on a shared writer class — a general shape, and it
    falls out of this function because registrations are collected per-decorator,
    not per-class.

    H4/§N.8: this signal is only earned if the parser actually resolved everything it
    saw — and, since M0-T28/F-2, if it saw anything at all. See `_assert_trustworthy`.
    """
    return set(_assert_trustworthy(census(force=force), 'the code-derived has_writer set')['writers'])


def substep_truth_by_asset(force: bool = False) -> dict:
    """The code-derived truth for `has_substeps`: `{asset_id: bool}`, one entry per
    registered asset, `True` iff the @register'd class **OVERRIDES BOTH** `plan_substeps`
    AND `run_substep` (the FROZEN contract's HEAVY shape, CLAUDE.md §N.2).

    Nirmāṇa M0-T28 / F-1. Added so the workbook's `Substeps (code)` column can stop being
    a file-granular regex (`'def plan_substeps' in txt` over the whole file, attributed to
    every `@register` in it) and read the same AST override test the registry repair was
    measured against. THREE traps this exists to avoid, all of which have caught agents in
    this campaign:

      · a regex counts docstring mentions of `@register(` / `def plan_substeps` and misses
        real writers;
      · a naive AST pass silently drops the `@register(ASSET_ID)` module-constant form
        (4 of 123 registrations use it);
      · **"has plan_substeps in the MRO" is a CONSTANT, not a detector** — `WriterBase`
        defines both methods itself, so that test is true for all 123. The census resolves
        the class graph WITHOUT WriterBase (`resolve()` appends `WriterBase(frozen base)`
        to the chain and contributes none of its methods), so what is measured is a genuine
        OVERRIDE by the writer or one of its project-local ancestors.

    D-24 condition (b)'s discriminating pair is the check that this is file-granular no
    longer: `bo_laksana` True and `bo_laksana_rerank` False, from the SAME source file.

    Same §N.8 refusal as `registered_asset_ids()`: an empty or incomplete census raises
    rather than returning a map in which every asset reads False.
    """
    c = _assert_trustworthy(census(force=force), 'the code-derived has_substeps map')
    return {aid: bool(recs[0]['writer_truth_has_substeps'])
            for aid, recs in c['writers'].items() if recs}


def writer_file_by_asset(force: bool = False) -> dict:
    """`{asset_id: path}` — the file that contains the @register'd WRITER CLASS.

    Nirmāṇa M0-T30 / F-5. `scan_code()` used to derive this by regex over whole files
    and attribute it to whichever matching file `rglob` happened to visit LAST, which
    produced three distinct wrong answers, all measured on 2026-08-23 against this tree:

      · **a test file** — `bg_cohort`, `bg_sky_calendar` and `mi_sankalpa` were
        attributed to `writers/tests/test_*.py`, because `scan_code()` had no exclude
        list at all and scanned the test tree this module has always skipped;
      · **a registration shim's DOCSTRING** — eleven `ka_*` assets were attributed to
        `writers/ka_*.py`, files which in several cases contain no executable
        `@register` whatsoever and merely NAME it in prose;
      · **an unrelated retired writer** — `ka_gochara` was attributed to
        `writers/ka_gochara_sweep.py`, a tombstone for a DIFFERENT, retired asset.

    Fourteen of 123 wrong is not a rounding error, and none of the three shapes is
    detectable from the column itself, which is why this is derived and not scanned.
    """
    c = _assert_trustworthy(census(force=force), 'the code-derived writer_file map')
    return {aid: recs[0]['module'] for aid, recs in c['writers'].items() if recs}


def resume_mechanism_by_asset(force: bool = False) -> dict:
    """`{asset_id: 'none'|'substep_fingerprint'|'delta_fingerprint'}`, per WRITER CLASS.

    Nirmāṇa M0-T30 / F-5, the sweep M0-T28 started. `Substeps (code)` stopped being a
    whole-file text match in M0-T28; `resume_mechanism` was the same defect in the same
    function one column over, and unlike the substep column it was ALREADY WRONG on live
    data rather than merely capable of going wrong:

      · `scan_code()` searched a blob of the WHOLE FILE **plus every `.py` in the first
        `services/<pkg>` package the file imports**, then attributed the single answer to
        EVERY `@register` the regex found in that file — docstring mentions included.
      · `ka_gochara` therefore read `substep_fingerprint`, sourced from the service
        package of `ka_gochara_sweep` — a RETIRED asset it is merely the successor to —
        reached through a docstring mention in a tombstone shim. Its own writer class
        uses `class_fingerprint`, i.e. `delta_fingerprint`.
      · `bg_gochara_arcs` read `delta_fingerprint` because `services/w2g/fingerprint.py`
        — a module its writer class never calls — sits in the package it imports
        `arc_fingerprint` from. Its own docstring says it "never writes
        `build_substep_progress`".

    The class-scoped derivation asks the narrower and answerable question: does THIS
    writer class (or a project-local ancestor) NAME resume machinery? See
    `class_identifiers` for why that is an AST identifier scan rather than a text search,
    and `RESUME_SUBSTEP_TOKENS` for why the vocabulary was deliberately left alone.

    HONEST LIMIT, stated because it is the weak half of this signal: unlike
    `has_substeps` there is no `asset_registry` column for `resume_mechanism`, so this
    map has NOTHING TO BE PAIRED AGAINST and no registry-vs-code divergence detector can
    exist for it (F-5 named this, and it is unchanged). What can be falsified is the
    ATTRIBUTION — that two registrations in one file get different answers when their
    classes differ — and that is what M0-T30's constructed fixture exercises.
    """
    c = _assert_trustworthy(census(force=force), 'the code-derived resume_mechanism map')
    return {aid: recs[0]['resume_mechanism'] for aid, recs in c['writers'].items() if recs}


if __name__ == '__main__':
    out = census()
    results = out['writers']
    unresolved_registrations = out['unresolved_registrations']
    files_scanned, parse_errors = out['files_scanned'], out['parse_errors']
    registrations_n, dupes = out['n_registrations'], out['duplicate_asset_ids']
    (pathlib.Path(__file__).resolve().parent/'writer_substep_census.json').write_text(json.dumps(out, indent=1, default=str))
    print('UNRESOLVED @register args:', unresolved_registrations)
    print(f'files_scanned={files_scanned} parse_errors={len(parse_errors)} registrations={registrations_n} distinct_asset_ids={len(results)} dupes={list(dupes)}')
    heavy = sorted(a for a,v in results.items() if v[0]['writer_truth_has_substeps'])
    print(f'HEAVY (plan_substeps+run_substep) n={len(heavy)}:'); [print('  ',h) for h in heavy]
    odd = {a: v[0]['shape'] for a,v in results.items() if v[0]['shape'] not in ('HEAVY','LIGHT')}
    print('non-standard shapes:', odd)
    unres = {a: [c for c in v[0]['mro_chain'] if c.startswith('UNRESOLVED')] for a,v in results.items() if any(c.startswith('UNRESOLVED') for c in v[0]['mro_chain'])}
    print('unresolved bases:', unres)
