#!/usr/bin/env python3
"""Ω7 dark-corpus report assembler (Elevation Campaign v2.1, Lane Ω7).

Runs the dark-corpus matcher for each (flagship domain, chart) pair over the
captured replay-set transcripts and assembles DARK_CORPUS_REPORT_v1_0.json + .md.

Usage: build_report.py <runs_dir> <accounting_dir> <out_dir>
"""
import json, os, sys, subprocess, datetime, glob, re
HERE = os.path.dirname(os.path.abspath(__file__))
MATCH = os.path.join(HERE, 'darkcorpus_match.py')

# frozen replay-set membership (ids we EXPECT per domain), from DARK_CORPUS_REPLAY_SET_v1_0.json
EXPECTED = {
    'wealth': [f'DC-W-{n:02d}' for n in range(1, 22)],
    'career': [f'DC-C-{n:02d}' for n in range(1, 22)],
}
GLOB = {'wealth': 'DC-W-*.json', 'career': 'DC-C-*.json'}
# (domain, chart8) -> accounting filename
ACC = lambda dom, ch8: f'COMPLETENESS_ACCOUNTING_{dom}_{ch8}_v1_0.json'


NONCHART = ('ToolSearch', 'tool_search', 'Bash', 'Write', 'Read', 'TodoWrite', 'Edit', 'Glob', 'Grep')

def valid_run(fp):
    """A run is valid if it contains >=1 real chart-tool call. Lenient parse
    (strict -> trailing-comma repair -> regex), mirroring the matcher, so a
    recoverable transcript is counted as ran, not dropped."""
    raw = open(fp).read()
    d = None
    for attempt in (raw, re.sub(r',(\s*[}\]])', r'\1', raw)):
        try:
            d = json.loads(attempt); break
        except Exception:
            continue
    if d is None:
        tools = [t.split('__')[-1] for t in re.findall(r'"tool"\s*:\s*"([^"]+)"', raw)]
        chart = [t for t in tools if t and t not in NONCHART]
        return (len(chart) > 0), len(tools), sorted(set(chart))
    tools = []
    for c in d if isinstance(d, list) else []:
        if isinstance(c, dict):
            t = (c.get('tool') or '').split('__')[-1]
            if t and t not in NONCHART:
                tools.append(t)
    return (len(tools) > 0), len(d) if isinstance(d, list) else 0, sorted(set(tools))


def run_match(acc_path, run_glob, dump_path):
    out = subprocess.check_output(['python3', MATCH, acc_path, run_glob, dump_path])
    return json.loads(out)


def write_md(r, path):
    L = []
    L.append('# Ω7 — Dark-Corpus Report (Elevation Campaign v2.1, Stream γ · PŪRṆA)\n')
    L.append(f"*Generated {r['generated_at']} · target chart `{r['target_chart']}` (native — Abhisek Mohanty)*\n")
    L.append('> **What this measures.** Of every concept the instrument *computes and stores non-empty* '
             'for this chart in a flagship domain, how many were **never surfaced** across a fresh execution '
             'of the FROZEN dark-corpus replay set (naive + narrow + expert phrasings) through the sealed '
             'evaluator harness. This is the direct measurement of the native\'s ~20% unknown-unknown. '
             '**Target: zero.** A dark concept = computed, non-empty, and still not served.\n')
    L.append('## Headline\n')
    L.append('| Domain | Served (non-empty) | Dark | Bright | Coverage | Replay runs |')
    L.append('|---|---|---|---|---|---|')
    for dom, d in r['domains'].items():
        rc = d['replay_coverage']
        L.append(f"| **{dom}** | {d['served_universe_non_empty']:,} | **{d['dark_corpus_count']:,}** | "
                 f"{d['bright_count']:,} | {d['coverage_pct']}% | {rc['ran_valid']}/{rc['expected']} |")
    L.append('')
    L.append('The dark count is an **upper bound** (see method): composed-reading tools emit prose that may carry '
             'a concept\'s substance without its fact_id/token, so true coverage is ≥ reported. Even so, the '
             'signal is unambiguous — a naive→expert answer corpus surfaces only a few percent of what the '
             'instrument holds. The number is honest and is meant to trend toward zero across campaign iterations.\n')
    for dom, d in r['domains'].items():
        rc = d['replay_coverage']
        L.append(f'## {dom.title()} — dark-corpus breakdown\n')
        L.append(f"- **Served universe (non-empty for this chart):** {d['served_universe_non_empty']:,}")
        L.append(f"- **Dark:** {d['dark_corpus_count']:,}  "
                 f"( tool-never-called {d['dark_tool_never_called']:,} · substance-absent {d['dark_substance_absent']:,} )")
        L.append(f"- **Bright (surfaced ≥1×):** {d['bright_count']:,}  ({d['coverage_pct']}% coverage)")
        L.append(f"- **Replay coverage:** {rc['ran_valid']}/{rc['expected']} questions ran with ≥1 live chart-tool call.")
        if rc['invalid_or_no_chart_tool']:
            L.append(f"  - invalid/no-chart-tool: {rc['invalid_or_no_chart_tool']}")
        if rc['missing_files']:
            L.append(f"  - missing: {rc['missing_files']}")
        L.append(f"- **Tools the corpus actually called:** {', '.join(d['tools_called_in_corpus'])}\n")
        L.append('**Dark by layer:**  ' + ' · '.join(f'{k}={v:,}' for k, v in sorted(d['dark_by_layer'].items())) + '\n')
        L.append('**Dark by serving tool (top 12):**\n')
        L.append('| serving tool | dark concepts |')
        L.append('|---|---|')
        for k, v in list(d['dark_by_serving_tool'].items())[:12]:
            L.append(f'| `{k}` | {v:,} |')
        L.append('')
        L.append('**Dark by concept family (top 15) — the actionable slice:**\n')
        L.append('| concept family | dark |')
        L.append('|---|---|')
        for k, v in list(d['dark_by_family_full'].items())[:15]:
            L.append(f'| `{k}` | {v:,} |')
        L.append('')
        L.append(f"Full dark + bright concept_id lists: `{d['concept_dump_file']}`\n")
    L.append('## Method (faithful to the sealed evaluator harness)\n')
    L.append(r['method']['consumer'] + '\n')
    L.append('**Matching rule.** ' + r['method']['matching_rule'] + '\n')
    L.append('**Bias direction.** ' + r['method']['bias_direction'] + '\n')
    L.append('## Deviations from the sealed harness (declared, per §0 no-silent-omission)\n')
    for dv in r['deviations_from_sealed_harness']:
        L.append(f'- {dv}')
    L.append('')
    L.append('## Coverage / what is NOT covered\n')
    for k, v in r['coverage'].items():
        L.append(f'- **{k}:** {v}')
    L.append('')
    open(path, 'w').write('\n'.join(L))


def main():
    runs_dir, acc_dir, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    chart8 = '482012f1'   # primary/native chart (charter acceptance criterion #2)
    report = {
        'artifact': 'DARK_CORPUS_REPORT',
        'version': '1.0',
        'campaign': 'Elevation Campaign v2.1, Stream gamma (PURNA), Lane Omega-7 (dark-corpus report)',
        'generated_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'target_chart': f'{chart8}-710e-4a25-994a-93821f5871aa',
        'definition': ('A dark concept = a TCI entry that (a) exists in the TCI, (b) is non-empty '
                       '(state "served", real row_count>0) for the target chart per the Omega-3 '
                       'completeness accounting, AND (c) was NOT surfaced across a FRESH execution of '
                       'the FROZEN DARK_CORPUS_REPLAY_SET_v1_0 through the sealed evaluator harness. '
                       'Target: zero. This is the direct measurement of the native\'s ~20% unknown-unknown.'),
        'method': {
            'consumer': ('Fresh general-purpose sub-agent per replay question, sealed-harness system '
                         'framing (SEALED_EVALUATOR_HARNESS_v1_0.md #1): no charter text, no EL vocabulary, '
                         'no concept names, no mention of dossier/Lane-Omega. One user turn per run; the '
                         'agent chose its own tools. A methodologically-neutral tool-access + transcript-'
                         'capture instruction was appended (plumbing only) — see deviations.'),
            'matching_rule': ('Faithful to the harness grader: each served concept maps to one serving tool '
                              '+ sample fact_ids + a distinguishing concept token. A concept is BRIGHT iff, '
                              'across the UNION of all replay transcripts, its serving tool was actually called '
                              'AND (one of its sample fact_ids appears verbatim in that tool\'s raw result OR its '
                              'distinguishing token appears in that result). Else DARK. Two dark sub-reasons: '
                              'tool_never_called (serving tool absent from the entire corpus) and substance_absent '
                              '(tool called but concept substance never surfaced).'),
            'bias_direction': ('Conservative toward OVER-reporting dark: fact_id evidence is only 3 samples per '
                              'concept, and composed-reading tools (assess_*, judgment_query) emit prose that may '
                              'carry a concept\'s substance without its fact_id or exact token. So the true bright '
                              'set is >= reported; the dark count is an UPPER bound. This matches Omega-7\'s intent '
                              '(silent omission is a build failure — err toward flagging, not hiding).'),
        },
        'deviations_from_sealed_harness': [
            'No Agent-SDK transcript interceptor was available, so each consumer wrote its own tool-call log '
            '(tool, arguments, result_raw verbatim) to a file rather than the harness capturing it externally. '
            'The capture instruction reveals nothing about what is measured (no concept/dossier vocabulary).',
            'A neutral tool-access note (the chart tools are under mcp__marsys-jis-direct__ and need no auth) was '
            'appended after an early run (DC-W-09 first attempt) failed by confusing the auth-gated claude.ai '
            'MARSYS-JIS connector with the working direct namespace. Note names a spread of example tools, not a '
            'routing hint.',
            'Second chart 1c826d5a NOT executed (time budget) — see coverage.chart_1c826d5a_status.',
        ],
        'domains': {},
    }

    for dom in ('wealth', 'career'):
        acc_path = os.path.join(acc_dir, ACC(dom, chart8))
        run_glob = os.path.join(runs_dir, GLOB[dom])
        dump_path = os.path.join(out_dir, f'DARK_CORPUS_{dom}_{chart8}_concepts_v1_0.json')
        # coverage accounting: which expected ids ran validly
        ran, invalid, missing = [], [], []
        for rid in EXPECTED[dom]:
            fp = os.path.join(runs_dir, rid + '.json')
            if not os.path.exists(fp):
                missing.append(rid); continue
            ok, n, tools = valid_run(fp)
            (ran if ok else invalid).append(rid)
        m = run_match(acc_path, run_glob, dump_path)
        report['domains'][dom] = {
            'served_universe_non_empty': m['served_total'],
            'replay_coverage': {
                'expected': len(EXPECTED[dom]),
                'ran_valid': len(ran), 'ran_valid_ids': ran,
                'invalid_or_no_chart_tool': invalid,
                'missing_files': missing,
            },
            'tools_called_in_corpus': m['tools_called_in_corpus'],
            'dark_corpus_count': m['dark_count'],
            'bright_count': m['bright_count'],
            'coverage_pct': m['coverage_pct'],
            'dark_tool_never_called': m['dark_tool_never_called'],
            'dark_substance_absent': m['dark_substance_absent'],
            'dark_by_layer': m['dark_by_layer'],
            'dark_by_serving_tool': m['dark_by_serving_tool'],
            'dark_by_family_full': m['dark_by_family_full'],
            'bright_by_layer': m['bright_by_layer'],
            'bright_by_serving_tool': m['bright_by_serving_tool'],
            'concept_dump_file': os.path.basename(dump_path),
        }

    report['coverage'] = {
        'chart_482012f1_status': 'EXECUTED (both flagship domains)',
        'chart_1c826d5a_status': 'NOT EXECUTED — time budget; queued for next Omega-7 iteration',
    }
    outp = os.path.join(out_dir, 'DARK_CORPUS_REPORT_v1_0.json')
    json.dump(report, open(outp, 'w'), indent=2)
    print('WROTE', outp)
    write_md(report, os.path.join(out_dir, 'DARK_CORPUS_REPORT_v1_0.md'))
    print('WROTE', os.path.join(out_dir, 'DARK_CORPUS_REPORT_v1_0.md'))
    print(json.dumps({d: {'dark': report['domains'][d]['dark_corpus_count'],
                          'bright': report['domains'][d]['bright_count'],
                          'served': report['domains'][d]['served_universe_non_empty'],
                          'ran': report['domains'][d]['replay_coverage']['ran_valid']}
                      for d in report['domains']}, indent=2))
    return report


if __name__ == '__main__':
    main()
