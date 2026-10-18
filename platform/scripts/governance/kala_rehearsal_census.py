#!/usr/bin/env python3
"""K9-5 offline rehearsal census preparation and comparison (SR-A4-01).

No database, orchestrator, certificate or activation calls. Without --census all
observations are null. With a supplied census file, preserve its measurements and
use asset_census's existing applicability/cap/rollup code. This is an inspection
report, never certification or proof that an imported file is authentic.

--expectations is a JSON object {asset_id: {gate: verdict_or_null}}. Predictions
are separate from observations; no expectation changes a measured cell.
Exit 0: report produced, NOT a gate PASS; 2: mismatch/refusal/stale artifact.
"""
from __future__ import annotations

import argparse
import ast
import copy
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import sys

import asset_census as ac

ROOT = Path(__file__).resolve().parents[3]
PLAN = "00_ARCHITECTURE/briefs/l3_families/KALA_LAYER_CODE_ARCHITECTURE_PLAN_v1_1.md"
REGISTRY = "platform/scripts/governance/asset_census.py"
DECLARATIONS = "platform/scripts/governance/asset_declarations.json"
DOCUMENT = "00_ARCHITECTURE/briefs/l3_families/measurements/K9_CENSUS_v1_0.md"
VERDICTS = (*ac.ROLLUP_ORDER, "N/A")


def _sha(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def _strict_object(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _finite_float(value):
    number = float(value)
    _require(math.isfinite(number), f"non-finite JSON number: {value}")
    return number


def _read_json(blob):
    return json.loads(blob, object_pairs_hook=_strict_object,
                      parse_float=_finite_float, parse_constant=_finite_float)


def _inventory(repo):
    text = (repo / PLAN).read_text()
    section = text.split("## §8 ·", 1)[1].split("## §9 ·", 1)[0]
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        if line not in section.splitlines():
            continue
        match = re.match(r"\| `(ka_[a-z0-9_]+)` \|", line)
        if match:
            rows.append(dict(asset=match[1], disposition=line.split("|")[3].strip(),
                             source=f"{PLAN}:{number}"))
    _require(rows and len({r['asset'] for r in rows}) == len(rows), "missing/duplicate PLAN §8 inventory")
    return rows


def _criteria(repo):
    tree = ast.parse((repo / REGISTRY).read_text())
    node = next(n.value for n in tree.body if isinstance(n, ast.AnnAssign)
                and getattr(n.target, "id", None) == "CRITERION_REGISTRY")
    locations = {ast.literal_eval(k): v.lineno for k, v in zip(node.keys, node.values)}
    return {c: dict(gate=e['gate'], revision=e['revision'], detector=e['detector'],
                    recordable_verdict="NO_DETECTOR" if e['detector'] == "NONE" else None,
                    source=f"{REGISTRY}:{locations[c]}")
            for c, e in ac.CRITERION_REGISTRY.items() if e['gate'] in ac.CELL_GATES and 'L3' in e['layers']}


def _load_census(path, inventory, declarations_blob):
    blob = Path(path).read_bytes()
    obj = _read_json(blob)
    _require(isinstance(obj, dict) and isinstance(obj.get('L3'), dict), "census needs an L3 object")
    head = obj['L3']
    _require(head.get('layer') == 'L3', "census layer is not L3")
    _require(type(head.get('registry_revision')) is int and head['registry_revision'] == ac.REGISTRY_REVISION
             and head.get('registry_fingerprint') == ac.registry_fingerprint(), "registry binding mismatch")
    _require(head.get('declarations_sha256') == _sha(declarations_blob)
             and head.get('declarations_version') == _read_json(declarations_blob)['version'],
             "declarations binding mismatch")
    target = head.get('census_target')
    _require(isinstance(target, dict) and target.get('declared') in ('disposable', 'evaluation_copy'),
             "only an explicitly declared off-production census may be inspected")
    generated = head.get('generated')
    _require(isinstance(generated, str), "missing census run timestamp")
    _require(datetime.fromisoformat(generated).utcoffset() is not None, "census timestamp needs timezone")
    _require(head.get('chart_scope') == '482012f1-710e-4a25-994a-93821f5871aa', "unexpected census chart scope")
    records = head.get('assets')
    _require(isinstance(records, list) and records, "census assets must be a nonempty list")
    indexed = {}
    for record in records:
        _require(isinstance(record, dict), "census asset must be an object")
        aid = record.get('asset_id')
        _require(isinstance(aid, str) and aid in inventory and aid not in indexed, "unknown/duplicate census asset")
        _require(record.get('layer') == 'L3', "wrong asset layer")
        measurements = record.get('measurements')
        _require(isinstance(measurements, dict), "missing census measurements")
        for criterion, measurement in measurements.items():
            entry = ac.CRITERION_REGISTRY.get(criterion)
            _require(entry is not None or criterion in ac.RETIRED_CRITERIA, f"unknown criterion: {criterion}")
            allowed = VERDICTS if entry and entry['gate'] in ac.CELL_GATES else (*VERDICTS, 'NOT_GENERIC')
            _require(isinstance(measurement, dict) and isinstance(measurement.get('v'), str)
                     and measurement['v'] in allowed, f"invalid measurement: {criterion}")
        indexed[aid] = record
    return indexed, dict(sha256=_sha(blob), generated=generated, census_target=copy.deepcopy(target),
                         declarations_sha256=head['declarations_sha256'], declarations_version=head['declarations_version'],
                         chart_scope=head['chart_scope'])


def build_report(repo: Path = ROOT, census_path=None, expectations=None) -> dict:
    """Prepare unknowns or inspect one file. Never fill observations from predictions."""
    repo = Path(repo)
    # The imported rollup must be the same source as the bindings named below.
    _require((repo / REGISTRY).read_bytes() == Path(ac.__file__).read_bytes(), "rollup source differs from report binding")
    inventory = _inventory(repo)
    ids = {r['asset'] for r in inventory}
    criteria = _criteria(repo)
    expected = {} if expectations is None else expectations
    _require(isinstance(expected, dict), "expectations must be an object")
    for aid, gates in expected.items():
        _require(aid in ids and isinstance(gates, dict), "unknown asset or invalid expectation")
        for gate, verdict in gates.items():
            _require(gate in ac.CELL_GATES and (verdict is None or isinstance(verdict, str) and verdict in VERDICTS),
                     "unknown gate or invalid expected verdict")
    declarations_blob = (repo / DECLARATIONS).read_bytes()
    records, source = _load_census(census_path, ids, declarations_blob) if census_path is not None else ({}, None)
    declarations = _read_json(declarations_blob)['assets']
    assets, mismatches, refusals = [], [], []
    for item in inventory:
        aid = item['asset']
        record = records.get(aid)
        measurements = record['measurements'] if record is not None else {}
        cells = ac.rollup_asset('L3', measurements, ac.facts_for_asset(record, declarations)) if record is not None else {}
        for criterion, measurement in measurements.items():
            if criterion in criteria and criteria[criterion]['detector'] == 'NONE' and measurement['v'] != 'NO_DETECTOR':
                refusals.append(dict(asset=aid, criterion=criterion, verdict=measurement['v'], reason='detector_none'))
        gates = {}
        for gate in ac.CELL_GATES:
            want = expected.get(aid, {}).get(gate)
            observed = cells[gate]['v'] if cells else None
            gates[gate] = dict(expected=want, observed=observed, checks=cells[gate]['checks'] if cells else [])
            if want is not None and want != observed:
                mismatches.append(dict(asset=aid, gate=gate, expected=want, observed=observed,
                                       reason='unmeasured' if observed is None else 'census_mismatch'))
        assets.append(dict(**item, gates=gates, measurements=copy.deepcopy(measurements),
                           information=ac.rollup_excluded('L3', measurements) if record is not None else {}))
    return dict(schema='kala.rehearsal_census/1', mode='rehearsal_file' if source else 'preparation',
                production_certification=None, source=source,
                bindings={p: _sha((repo / p).read_bytes()) for p in (PLAN, REGISTRY, DECLARATIONS)},
                registry_revision=ac.REGISTRY_REVISION, registry_fingerprint=ac.registry_fingerprint(),
                criteria=criteria, assets=assets, mismatches=mismatches, certifier_refusals=refusals,
                summary=dict(planned_assets=len(assets), observed_assets=len(records), missing_assets=len(assets)-len(records),
                             observed_gates=len(records)*len(ac.CELL_GATES)))


def render_markdown(report):
    """Deterministic human view; the JSON report retains raw cells and causes."""
    lines = ['---', 'artifact: K9_CENSUS_v1_0.md', 'version: "1.0"',
             f"status: {'PRE_BUILD_UNMEASURED' if report['mode'] == 'preparation' else 'IMPORTED_REHEARSAL_ONLY'}",
             'authority: "SR-A4-01; code/declaration only"', '---', '', '# K9-5 · Rehearsal census', '',
             'No production census, certification, rebuild, publication or retirement is asserted.',
             'An imported file is inspection evidence; this tool does not authenticate it or issue certificates.',
             'Every `null` is unmeasured. Expectations never overwrite observations.', '',
             '**(I) INTERPRETATION:** pre-build prepares the full PLAN §8 population, including',
             'historical/superseded assets. Missing future census records stay null; a smaller',
             'active population must be reconciled explicitly after K9-4b and KR-1/KR-2.',
             'Alternative: wait for those operations before preparing this report.', '',
             '**(I) INTERPRETATION:** detector-NONE raw readings are preserved for inspection.',
             'Every reading other than NO_DETECTOR is separately flagged `detector_none`,',
             'including a current engine rule-computed N/A; no certifier admission is inferred.',
             'Alternative: discard the entire census on the first such cell.', '',
             f"Registry revision: {report['registry_revision']}; fingerprint: `{report['registry_fingerprint']}`.", '',
             '## Bound inputs', '']
    for path, digest in report['bindings'].items():
        lines.append(f'- `{path}` · SHA-256 `{digest}`')
    lines += ['', 'PLAN §7 defines the nine gates; PLAN §9 K8 exit requires the measured expected',
              'reading, including honest NO_DETECTOR. Current engine rules supersede the old',
              'detector snapshot only for this inspection; no plan or engine contract is edited.', '',
              '## Per-asset gates', '', 'Cells are **expected / observed**. No expected PASS is pre-assigned.', '',
              '| Asset | ' + ' | '.join(ac.CELL_GATES) + ' |',
              '|---|' + '---|' * len(ac.CELL_GATES)]
    for asset in report['assets']:
        values = [f"{g['expected'] or 'null'} / {g['observed'] or 'null'}" for g in asset['gates'].values()]
        lines.append(f"| `{asset['asset']}` | " + ' | '.join(values) + ' |')
    lines += ['', '## Detector constraints', '', '| Criterion | Revision | Detector | Recordable constraint | Source |', '|---|---|---|---|---|']
    for criterion, entry in report['criteria'].items():
        lines.append(f"| `{criterion}` | {entry['revision']} | `{entry['detector']}` | {entry['recordable_verdict'] or 'null; must be measured'} | `{entry['source']}` |")
    lines += ['', '## Population and evidence', '']
    for asset in report['assets']:
        lines.append(f"- `{asset['asset']}`: {asset['disposition']}; `{asset['source']}`.")
    lines += ['', '```json', json.dumps({k: report[k] for k in ('source', 'summary', 'mismatches', 'certifier_refusals')}, indent=2, allow_nan=False), '```', '',
              '## Execution and activation gates', '',
              '- K9-4b rebuild/verification and KR-1/KR-2 dispositions must complete or be explicitly ruled not applicable.',
              '- Capture a real guarded off-production L3 census with registry revision/fingerprint, declarations SHA-256/version and explicit chart scope.',
              '- Supply independently reviewed per-gate expectations; inspect raw measurements, effective checks, missing assets and all mismatches.',
              '- Resolve detector_none conflicts through the campaign; a rule-computed N/A in the engine is not certifier admission.',
              '- Code merge alone does not complete the dependent operations or authorize activation.', '',
              '## Reproduce', '', '```sh',
              f'GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1 python3 platform/scripts/governance/kala_rehearsal_census.py --format markdown --out {DOCUMENT} --check',
              '# Later, inspect a supplied off-production census (no connection is opened):',
              'GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1 python3 platform/scripts/governance/kala_rehearsal_census.py --census /path/to/census_L3.json --expectations /path/to/expected.json',
              '```', '', 'Expectations JSON: `{ "ka_avadhi": { "Idem": "PASS", "Build": null } }`.',
              'A missing expectation remains null. Exit 0 means the report was produced, never that the layer passed.',
              'Tests are auto-discovered by mandatory Governance Tool Tests (pytest), via ci_shard.py.', '']
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--census', type=Path)
    parser.add_argument('--expectations', type=Path)
    parser.add_argument('--format', choices=('json', 'markdown'), default='json')
    parser.add_argument('--out', type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(argv)
    try:
        report = build_report(args.repo, args.census, _read_json(args.expectations.read_bytes()) if args.expectations else None)
        output = render_markdown(report) if args.format == 'markdown' else json.dumps(report, indent=2, allow_nan=False) + '\n'
        if args.check:
            _require(args.out is not None and args.out.is_file() and args.out.read_text() == output, 'stale/missing output')
        elif args.out:
            args.out.write_text(output)
        else:
            print(output, end='')
        return 2 if report['mismatches'] or report['certifier_refusals'] else 0
    except (OSError, ValueError, KeyError, TypeError, IndexError, StopIteration) as exc:
        print(f'REFUSED: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
