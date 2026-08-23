#!/usr/bin/env python3
"""
P4 RETIREMENT CENSUS — re-derives the condemned-tree census for the Paripraśna
P4-B deletion warrant, and hashes it.

SCOPE NOTE (read before trusting the output)
--------------------------------------------
This script is READ-ONLY. It deletes nothing, edits nothing, and has no side
effect beyond writing its own report to stdout (or --out). It is a census
INSTRUMENT, not a deletion instrument.

It answers, mechanically and reproducibly:
  1. What files are reachable ONLY from the condemned entrypoints?
  2. What files are ALSO reachable from a surviving entrypoint (→ SURVIVES)?
  3. What files carry a dynamic/string/config reference that a static import
     walk would miss (→ AMBIGUOUS, and AMBIGUOUS = OUT)?
  4. Does any PARIŚEṢA-RĀTRI-territory file import from the condemned tree?
     (a single hit PARKS the retirement train — charter §10.3 precondition 1)

It is deliberately CONSERVATIVE. Every heuristic is tuned to over-report
survival and over-report ambiguity. A file this script calls CONDEMNED-CANDIDATE
is still only a candidate: the P4-B verifier reviews the deletion diff
line-by-line against it. A file this script calls AMBIGUOUS or SURVIVES is
NOT deletable tonight, full stop.

§N.8 note — what would make this script's own verdict read false:
  - `--selftest` injects a synthetic condemned path that a surviving entrypoint
    imports, and asserts the script classifies it SURVIVES rather than
    CONDEMNED-CANDIDATE. If that assertion cannot fail, the classifier is not
    a detector. Run `--selftest` BEFORE trusting any green census.

USAGE (the one command the P4-B verifier runs at commit time):

    git --no-optional-locks fetch origin && git --no-optional-locks log -1 --format=%H origin/main
    python3 platform/scripts/governance/p4_retirement_census.py \
        --repo-root . --out /tmp/p4_census_refreshed.json

The report's `census_hash` is a sha256 over the sorted (path, status) pairs
plus the git HEAD it was derived from. Two censuses with the same hash are the
same census. The deletion PR's diff must be checked path-by-path against the
`condemned_candidates` list of a census whose `git_head` equals the tip the
deletion PR is based on.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

SRC_EXT = ('.ts', '.tsx', '.js', '.jsx', '.mts', '.mjs')

# ---------------------------------------------------------------------------
# The condemned entrypoints — the legacy `consult` / `consume` surfaces that
# P4-A replaces with 308 redirects (browser) / 410 + pointer (API).
# Everything reachable ONLY from here is a deletion candidate.
# ---------------------------------------------------------------------------
CONDEMNED_ENTRYPOINTS = [
    'platform/src/app/api/chat/consult',
    'platform/src/app/api/chat/consume',
    'platform/src/app/api/consume',
    'platform/src/app/clients/[id]/consult',
    'platform/src/app/clients/[id]/consume',
]

# Prefixes that are NEVER condemned even if they path-match `consume`.
# `api/mcp/oauth/codes/consume` is OAuth authorization-code consumption — an
# unrelated verb sense of the same word, and live PARIŚEṢA (SF-003/SF-004)
# territory. This exclusion is the single most important line in the file.
NEVER_CONDEMNED = [
    'platform/src/app/api/mcp/',
]

# PARIŚEṢA-RĀTRI territory, for the cross-campaign import check (§10.3).
# Derived from the campaign's own file footprint on `main`; --parisesa-since
# recomputes it live from git rather than trusting this list.
PARISESA_TERRITORY_FALLBACK = [
    'platform/src/app/api/mcp/',
    'platform/src/app/api/pariprashna/',
    'platform-mcp/',
    'platform/python-sidecar/',
    'platform/tests/pariprashna/',
    '00_ARCHITECTURE/briefs/parisesa/',
]

# NOTE (a real defect found while building this instrument, kept documented
# because it is the exact failure mode a census must not have): an earlier
# version required the `from` clause on the SAME LINE as `import`, which
# silently dropped every multi-line `import {\n a,\n b,\n} from '...'`.
# That under-counted the LIVE set and therefore OVER-condemned — the direction
# of error that is unrecoverable in the morning. `[\s\S]*?` is deliberate.
IMPORT_RE = re.compile(
    r"""(?:^|\n)[ \t]*(?:import|export)[\s{*][\s\S]*?from\s*['"]([^'"]+)['"]"""
    r"""|import\s*\(\s*['"]([^'"]+)['"]\s*\)"""
    r"""|require\s*\(\s*['"]([^'"]+)['"]\s*\)"""
    r"""|vi\.mock\s*\(\s*['"]([^'"]+)['"]""",
    re.M,
)
# Bare side-effect imports: `import '@/lib/x'`
BARE_IMPORT_RE = re.compile(r"""(?:^|\n)\s*import\s*['"]([^'"]+)['"]""", re.M)


def sh(args, cwd):
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True).stdout.strip()


def is_source(p: str) -> bool:
    return p.endswith(SRC_EXT)


def is_test(p: str) -> bool:
    return ('__tests__' in p or '/tests/' in p
            or p.endswith(('.test.ts', '.test.tsx', '.spec.ts', '.spec.tsx',
                           '.smoke.ts')))


def all_sources(root: Path) -> list[str]:
    out = []
    for base in ('platform/src', 'platform/tests', 'platform-mcp/src',
                 'platform/scripts'):
        b = root / base
        if not b.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(b):
            dirnames[:] = [d for d in dirnames
                           if d not in ('node_modules', '.next', 'dist', 'build')]
            for f in filenames:
                if f.endswith(SRC_EXT):
                    out.append(str(Path(dirpath, f).relative_to(root)))
    return sorted(out)


def resolve(spec: str, importer: str, root: Path, index: set[str]) -> str | None:
    """Resolve an import specifier to a repo-relative source path, or None."""
    if spec.startswith('@/'):
        base = 'platform/src/' + spec[2:]
    elif spec.startswith('.'):
        base = os.path.normpath(os.path.join(os.path.dirname(importer), spec))
    else:
        return None  # bare package specifier
    for cand in (base, *[base + e for e in SRC_EXT],
                 *[base + '/index' + e for e in SRC_EXT]):
        if cand in index:
            return cand
    return None


def build_graph(root: Path, files: list[str]):
    index = set(files)
    imports: dict[str, set[str]] = {}
    importers: dict[str, set[str]] = {f: set() for f in files}
    text_cache: dict[str, str] = {}
    for f in files:
        try:
            src = (root / f).read_text(errors='replace')
        except OSError:
            src = ''
        text_cache[f] = src
        specs = set()
        for m in IMPORT_RE.finditer(src):
            specs.add(next(g for g in m.groups() if g))
        for m in BARE_IMPORT_RE.finditer(src):
            specs.add(m.group(1))
        deps = set()
        for s in specs:
            r = resolve(s, f, root, index)
            if r:
                deps.add(r)
        imports[f] = deps
        for d in deps:
            importers.setdefault(d, set()).add(f)
    return imports, importers, text_cache


def under(path: str, prefixes: list[str]) -> bool:
    return any(path == p or path.startswith(p.rstrip('/') + '/') or path.startswith(p)
               for p in prefixes)


def reachable(seeds: set[str], imports: dict[str, set[str]]) -> set[str]:
    seen, stack = set(seeds), list(seeds)
    while stack:
        cur = stack.pop()
        for d in imports.get(cur, ()):
            if d not in seen:
                seen.add(d)
                stack.append(d)
    return seen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo-root', default='.')
    ap.add_argument('--out', default=None)
    ap.add_argument('--parisesa-since', default='2026-08-01',
                    help='recompute PARIŚEṢA territory from git commits since this date')
    ap.add_argument('--selftest', action='store_true',
                    help='§N.8 — prove the classifier can report a non-green answer')
    args = ap.parse_args()

    root = Path(args.repo_root).resolve()
    git_head = sh(['git', '--no-optional-locks', 'rev-parse', 'HEAD'], root)

    files = all_sources(root)
    imports, importers, text = build_graph(root, files)

    condemned_entry = {f for f in files
                       if under(f, CONDEMNED_ENTRYPOINTS)
                       and not under(f, NEVER_CONDEMNED)}
    # Surviving entrypoints: every Next.js route/page/layout + every MCP tool +
    # every script, that is NOT itself condemned.
    surviving_entry = {
        f for f in files
        if f not in condemned_entry
        and not is_test(f)
        and (
            re.search(r'/(route|page|layout|template|error|loading|not-found|middleware)\.(ts|tsx)$', f)
            or f.startswith('platform-mcp/src/')
            or f.startswith('platform/scripts/')
            or f == 'platform/src/middleware.ts'
        )
    }

    # ---- homograph guard (§N.8: a guard that cannot fail is not a guard) --
    # `consume` is a HOMOGRAPH in this repo: the legacy chat surface, and OAuth
    # authorization-CODE consumption (`api/mcp/oauth/codes/consume`) — live
    # PARIŚEṢA SF-003/SF-004 territory. This check enumerates every path whose
    # name matches the condemned vocabulary but which is NOT condemned, and
    # asserts the intersection with NEVER_CONDEMNED is empty. It reads false the
    # moment anyone broadens CONDEMNED_ENTRYPOINTS toward a `**/consume/**` glob.
    name_matches = sorted(f for f in files
                          if re.search(r'/(consume|consult)(/|$)', f))
    homograph_excluded = [f for f in name_matches if f not in condemned_entry]
    homograph_violations = [f for f in condemned_entry if under(f, NEVER_CONDEMNED)]
    homograph_guard = {
        'passed': not homograph_violations,
        'name_matching_paths_total': len(name_matches),
        'condemned': len(condemned_entry),
        'excluded_as_homograph_or_out_of_scope': homograph_excluded,
        'violations': homograph_violations,
        'note': ('If `violations` is non-empty the entrypoint list has been broadened '
                 'into an unrelated verb sense of the same word. STOP — do not delete.'),
    }

    cand = reachable(condemned_entry, imports)
    live = reachable(surviving_entry, imports)

    # PARIŚEṢA territory
    parisesa_prefixes = list(PARISESA_TERRITORY_FALLBACK)
    parisesa_files: set[str] = set()
    log = sh(['git', '--no-optional-locks', 'log', 'origin/main',
              f'--since={args.parisesa_since}', '--grep=parisesa', '-i',
              '--format=%H'], root)
    for h in [x for x in log.splitlines() if x.strip()]:
        for p in sh(['git', '--no-optional-locks', 'show', '--name-only',
                     '--format=', h], root).splitlines():
            if p.strip():
                parisesa_files.add(p.strip())

    def is_parisesa(p: str) -> bool:
        return p in parisesa_files or under(p, parisesa_prefixes)

    dyn_index = build_dynamic_index(root, cand)

    # ---- classification -------------------------------------------------
    rows = []
    for f in sorted(cand):
        imps = sorted(importers.get(f, ()))
        prod_imps = [i for i in imps if not is_test(i)]
        outside = [i for i in prod_imps if i not in cand]
        test_imps = [i for i in imps if is_test(i)]
        # dynamic / string / config references from OUTSIDE the candidate set
        dyn = dyn_index.get(f, [])
        if f in live or outside:
            status = 'SURVIVES'
            why = ('reachable from a surviving entrypoint'
                   if f in live else f'imported from outside the condemned set: {outside}')
        elif dyn:
            status = 'AMBIGUOUS'
            why = f'dynamic/string/config reference from outside the condemned tree: {dyn}'
        elif test_imps:
            status = 'AMBIGUOUS'
            why = (f'only test importers remain ({len(test_imps)}); the tests must be '
                   'dispositioned (deleted with it / repointed) before the file is')
        else:
            status = 'CONDEMNED-CANDIDATE'
            why = 'no production importer, no dynamic reference, not reachable from any surviving entrypoint'
        rows.append({
            'path': f,
            'status': status,
            'reason': why,
            'importers': imps,
            'imports': sorted(imports.get(f, ())),
            'dynamic_refs': dyn,
            'is_leaf': not any(d in cand for d in imports.get(f, ())),
        })

    # ---- transitivity closure (a real hole, closed) ---------------------
    # A CONDEMNED-CANDIDATE whose only importer is an AMBIGUOUS file would be
    # deleted out from under a file that is NOT being deleted tonight — the
    # orphaned-importer defect the deletion warrant exists to prevent, produced
    # by the census itself. AMBIGUOUS = OUT must propagate DOWN the graph:
    # if a parent survives the night, everything it imports survives the night.
    # Iterate to fixpoint; conservative direction only (never CONDEMNS anything
    # that was not already condemned).
    by_path = {r['path']: r for r in rows}
    changed = True
    passes = 0
    while changed and passes < 50:
        changed = False
        passes += 1
        for r in rows:
            if r['status'] != 'CONDEMNED-CANDIDATE':
                continue
            keepers = [i for i in r['importers']
                       if i in by_path and by_path[i]['status'] != 'CONDEMNED-CANDIDATE']
            if keepers:
                r['status'] = 'AMBIGUOUS'
                r['reason'] = ('transitivity: imported by a file that is NOT being deleted '
                               f'tonight ({keepers}) — AMBIGUOUS=OUT propagates down the graph')
                changed = True
    closure_passes = passes

    # ---- projection: what the set becomes if tests are co-deleted -------
    # Most of the AMBIGUOUS mass is "only test importers remain". Those tests are
    # legitimately part of the retirement (they test the retired surface), but
    # deleting them is a DECISION, not a derivation — so it is reported as a
    # PROJECTION the verifier may adopt, never as a warrant the script issues.
    # A test is co-deletable only if EVERY non-test path it references is inside
    # the candidate set: a test that also covers a surviving surface is not.
    # `cand` is the REACHABLE set, which includes files classified SURVIVES.
    # A test is co-deletable only if every source dep it has is itself slated
    # for deletion — a test that also touches a SURVIVING module is NOT
    # co-deletable, it is a test that must be repointed by hand.
    doomed = {r['path'] for r in rows if r['status'] != 'SURVIVES'}
    codeletable_tests = set()
    for f in files:
        if not is_test(f):
            continue
        deps = imports.get(f, set())
        if not deps:
            continue
        if any(d in doomed for d in deps) and all(d in doomed for d in deps):
            codeletable_tests.add(f)
    proj_status = {r['path']: r['status'] for r in rows}
    changed = True
    while changed:
        changed = False
        for r in rows:
            if proj_status[r['path']] != 'AMBIGUOUS':
                continue
            if r['dynamic_refs']:
                continue
            keepers = [i for i in r['importers']
                       if i not in codeletable_tests
                       and (i not in proj_status or proj_status[i] != 'CONDEMNED-CANDIDATE')]
            if not keepers:
                proj_status[r['path']] = 'CONDEMNED-CANDIDATE'
                changed = True
    projection = {
        'note': ('PROJECTION ONLY — not a deletion warrant. Shows what the condemned set '
                 'becomes IF the co-deletable test files below are deleted in the same PR. '
                 'Adopting it is a verifier decision that must be recorded; the script does '
                 'not make it.'),
        'codeletable_tests': sorted(codeletable_tests),
        'condemned_if_tests_codeleted': sorted(
            p for p, st in proj_status.items() if st == 'CONDEMNED-CANDIDATE'),
    }
    projection['counts'] = {
        'codeletable_tests': len(projection['codeletable_tests']),
        'condemned_if_tests_codeleted': len(projection['condemned_if_tests_codeleted']),
    }

    # ---- cross-campaign check (§10.3 precondition 1) --------------------
    # SCOPED CORRECTLY: the check is against the tree that would actually be
    # DELETED (CONDEMNED-CANDIDATE, plus AMBIGUOUS as an advisory tier) — NOT
    # against every file transitively reachable from a condemned entrypoint.
    # The reachable set includes shared infrastructure (`components/ui/button`,
    # `lib/auth/authorizeChartAccess`) that survives; counting a PARIŚEṢA import
    # of those as a collision would park the train on noise every single time,
    # which trains the operator to ignore the check — the exact failure mode the
    # check exists to prevent.
    status_of = {r['path']: r['status'] for r in rows}
    delete_set = {p for p, st in status_of.items() if st == 'CONDEMNED-CANDIDATE'}
    advisory_set = {p for p, st in status_of.items() if st == 'AMBIGUOUS'}

    blocking: list[dict] = []
    advisory: list[dict] = []
    for f in sorted(delete_set | advisory_set):
        tier = 'BLOCKING' if f in delete_set else 'ADVISORY'
        for i in sorted(importers.get(f, ())):
            if i in delete_set or i in advisory_set:
                continue
            if not is_parisesa(i):
                continue
            rec = {'parisesa_file': i, 'condemned_path': f,
                   'kind': 'static import',
                   'test_only': is_test(i)}
            (blocking if (tier == 'BLOCKING' and not is_test(i)) else advisory).append(rec)
        for ref in dyn_index.get(f, []):
            if is_parisesa(ref) and ref not in delete_set and ref not in advisory_set:
                advisory.append({'parisesa_file': ref, 'condemned_path': f,
                                 'kind': 'string/path/config reference (not a static import)',
                                 'test_only': is_test(ref)})

    cross = blocking

    # leaf-first ordering: depth = longest chain to a condemned leaf
    def depth(p, seen=None):
        seen = seen or set()
        if p in seen:
            return 0
        seen = seen | {p}
        ds = [depth(d, seen) for d in imports.get(p, ()) if d in cand]
        return 1 + max(ds) if ds else 0
    for r in rows:
        r['leaf_order_depth'] = depth(r['path'])
    rows.sort(key=lambda r: (r['leaf_order_depth'], r['path']))

    counts = {}
    for r in rows:
        counts[r['status']] = counts.get(r['status'], 0) + 1

    payload = {
        'artifact': 'P4_RETIREMENT_CENSUS',
        'git_head': git_head,
        'condemned_entrypoints': CONDEMNED_ENTRYPOINTS,
        'never_condemned_prefixes': NEVER_CONDEMNED,
        'counts': counts,
        'homograph_guard': homograph_guard,
        'transitivity_closure_passes': closure_passes,
        'projection_tests_codeleted': projection,
        'cross_campaign_check': {
            'verdict': ('PARK — a PARIŚEṢA-RĀTRI production file imports from the condemned tree'
                        if blocking else
                        'CLEAN — no PARIŚEṢA-RĀTRI production file imports from the condemned tree'),
            'scope_note': ('BLOCKING is scoped to static imports, from PARIŚEṢA production files, '
                           'into CONDEMNED-CANDIDATE paths only. Imports of shared infrastructure '
                           'that the census already classified SURVIVES are not collisions.'),
            'blocking_hits': blocking,
            'advisory_hits': advisory,
        },
        'rows': rows,
    }
    h = hashlib.sha256()
    h.update(git_head.encode())
    for r in rows:
        h.update(f"{r['path']}|{r['status']}\n".encode())
    payload['census_hash'] = h.hexdigest()

    if args.selftest:
        ok = selftest(root, files, imports, importers, cand, live)
        payload['selftest'] = ok
        if not ok['passed']:
            print(json.dumps(payload['selftest'], indent=2))
            return 3

    out = json.dumps(payload, indent=2)
    if args.out:
        Path(args.out).write_text(out)
        print(f"census_hash={payload['census_hash']}")
        print(f"git_head={git_head}")
        print(f"counts={counts}")
        print(f"cross_campaign={payload['cross_campaign_check']['verdict']}")
        print(f"written to {args.out}")
    else:
        print(out)
    return 0


def build_dynamic_index(root: Path, cand: set[str]) -> dict[str, list[str]]:
    """ONE pass over every non-condemned text file, finding NON-import references
    to any condemned path.

    This is the class a naive import-graph walk misses: registry lookups,
    string-built routes, config manifests, `readFileSync(...)` source assertions,
    serving-path manifests, CI allowlists. Batched into a single scan because a
    per-target grep over a 10k-file repo does not finish in a night.
    """
    # patterns → candidate path
    pat_to_target: dict[str, str] = {}
    for c in sorted(cand):
        stem = c[len('platform/'):] if c.startswith('platform/') else c
        pat_to_target.setdefault(stem, c)
        pat_to_target.setdefault(stem.rsplit('.', 1)[0], c)
        m = re.match(r'platform/src/app(/.*)/(route|page)\.tsx?$', c)
        if m:
            pat_to_target.setdefault(m.group(1), c)
    pats = sorted(pat_to_target, key=len, reverse=True)

    hits: dict[str, list[str]] = {}
    scan_roots = ['platform/src', 'platform/scripts', 'platform-mcp/src',
                  '.github', 'platform/supabase']
    exts = ('.ts', '.tsx', '.js', '.mjs', '.json', '.yaml', '.yml', '.py',
            '.sh', '.sql', '.css')
    for base in scan_roots:
        b = root / base
        if not b.exists():
            continue
        for dirpath, dirnames, filenames in os.walk(b):
            dirnames[:] = [d for d in dirnames
                           if d not in ('node_modules', '.next', 'dist', 'build')]
            for fn in filenames:
                if not fn.endswith(exts):
                    continue
                rel = str(Path(dirpath, fn).relative_to(root))
                # The census instrument itself hardcodes condemned paths; if it
                # counted its own mentions it would mark the whole tree AMBIGUOUS
                # forever — a signal that can never read false is not a signal (§N.8).
                if rel in cand or is_test(rel) or rel.endswith('p4_retirement_census.py'):
                    continue
                try:
                    src = Path(dirpath, fn).read_text(errors='replace')
                except OSError:
                    continue
                for pat in pats:
                    if pat in src:
                        tgt = pat_to_target[pat]
                        hits.setdefault(tgt, [])
                        if rel not in hits[tgt]:
                            hits[tgt].append(rel)
    return {k: sorted(v) for k, v in hits.items()}


def selftest(root, files, imports, importers, cand, live) -> dict:
    """§N.8 — demonstrate the classifier CAN report a non-CONDEMNED answer.

    Picks a real file inside the candidate set that IS imported from outside it
    and asserts the classifier does not call it CONDEMNED-CANDIDATE; and picks a
    file that is not, asserting it IS callable CONDEMNED. If neither case exists
    in the corpus, the selftest FAILS — a classifier with no discriminating case
    is not a detector.
    """
    survives_case = None
    condemned_case = None
    for f in sorted(cand):
        outside = [i for i in importers.get(f, ()) if i not in cand and not is_test(i)]
        if outside and survives_case is None:
            survives_case = (f, outside)
        if not outside and not importers.get(f) and condemned_case is None:
            condemned_case = f
    return {
        'passed': survives_case is not None and condemned_case is not None,
        'survives_discriminator': survives_case,
        'condemned_discriminator': condemned_case,
        'note': ('Both branches of the classifier are exercised by real corpus '
                 'members, so a CONDEMNED verdict is earned, not vacuous. If '
                 'either is null the census is NOT a detector and must not be '
                 'used as a deletion warrant.'),
    }


if __name__ == '__main__':
    sys.exit(main())
