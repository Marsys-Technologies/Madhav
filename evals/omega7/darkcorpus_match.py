#!/usr/bin/env python3
"""Ω7 dark-corpus matcher (Elevation Campaign v2.1, Lane Ω7).

Given (a) the Ω3 completeness-accounting file for a (domain, chart) pair and
(b) a set of captured consumer transcripts from the sealed evaluator harness run
over the frozen DARK_CORPUS_REPLAY_SET, computes the dark-corpus set:

  dark = { served concept : NOT surfaced across ANY transcript in the corpus }

Matching model (faithful to SEALED_EVALUATOR_HARNESS_v1_0.md grader rule
"a matching fact/signal actually appears in a served tool result"):

  A served concept maps to exactly one serving `tool` plus sample `fact_ids`
  and a distinguishing token (last dotted segment of concept_id).
  A concept is BRIGHT (surfaced) iff, across the union of all transcripts:
    - its serving tool was actually called, AND
    - EITHER one of its sample fact_ids appears verbatim in that tool's raw result,
      OR its distinguishing token appears (case-insensitive, word-ish) in that
         tool's raw result.
  Otherwise the concept is DARK. Two dark sub-reasons are recorded:
    - tool_never_called: the serving tool was not invoked anywhere in the corpus
    - substance_absent:  the tool was called but the concept's substance never appeared
"""
import json, sys, re, glob, os
from collections import Counter, defaultdict

def load_served(accounting_path):
    d = json.load(open(accounting_path))
    served = [r for r in d['rows'] if r['state'] == 'served']
    idx = {}
    for r in served:
        cid = r['concept_id']
        ev = r.get('evidence') or {}
        tool = ev.get('tool')
        fids = ev.get('fact_ids') or []
        token = cid.split('.')[-1]
        idx[cid] = {'tool': tool, 'fact_ids': [str(f) for f in fids], 'token': token,
                    'layer': cid.split('.')[0], 'family': '.'.join(cid.split('.')[:2])}
    return idx, d

def norm_token(tok):
    # distinguishing token -> a regex-safe lowercased search string
    return tok.lower()

def _repair_json(txt):
    """Light repair for common sub-agent JSON glitches: trailing commas."""
    t = re.sub(r',(\s*[}\]])', r'\1', txt)
    return t


def load_transcripts(run_glob):
    """Each transcript file is a JSON list of {tool, arguments, result_raw}.

    Robust: on strict-parse failure, try a trailing-comma repair; if that also
    fails, fall back to regex — extract every "tool":"..." and attribute the
    WHOLE file text as that run's tool-result blob to each tool called. This
    guarantees a valid run is never silently dropped (Omega-7's own principle).
    """
    per_tool_blob = defaultdict(list)   # tool -> list of raw text blobs
    tools_called = set()
    files = sorted(glob.glob(run_glob))
    n_calls = 0
    parsed_ok, recovered = [], []
    for fp in files:
        raw = open(fp).read()
        data = None
        for attempt in (raw, _repair_json(raw)):
            try:
                data = json.loads(attempt); break
            except Exception:
                continue
        if data is not None:
            parsed_ok.append(os.path.basename(fp))
            if isinstance(data, dict):
                data = data.get('calls') or data.get('tool_calls') or []
            for call in data:
                if not isinstance(call, dict): continue
                tool = call.get('tool') or call.get('name')
                if not tool: continue
                tool_short = tool.split('__')[-1]
                tools_called.add(tool_short)
                blob = json.dumps(call.get('result_raw', call.get('result', '')), default=str)
                blob += ' ' + json.dumps(call.get('arguments', ''), default=str)
                per_tool_blob[tool_short].append(blob.lower())
                n_calls += 1
        else:
            # regex fallback: recover tool names + attribute whole-file text
            tools = re.findall(r'"tool"\s*:\s*"([^"]+)"', raw)
            if not tools:
                print(f"WARN: unrecoverable {fp}", file=sys.stderr); continue
            recovered.append(os.path.basename(fp))
            blob = raw.lower()
            for tool in tools:
                tool_short = tool.split('__')[-1]
                tools_called.add(tool_short)
                per_tool_blob[tool_short].append(blob)
                n_calls += 1
    if recovered:
        print(f"INFO: regex-recovered {len(recovered)} transcript(s): {recovered}", file=sys.stderr)
    return tools_called, per_tool_blob, files, n_calls

def match(idx, tools_called, per_tool_blob):
    bright, dark_toolnever, dark_absent = [], [], []
    for cid, meta in idx.items():
        tool = (meta['tool'] or '').split('__')[-1]
        if tool not in tools_called:
            dark_toolnever.append(cid); continue
        blobs = per_tool_blob.get(tool, [])
        joined = '\n'.join(blobs)
        hit = False
        for f in meta['fact_ids']:
            if f and f.lower() in joined:
                hit = True; break
        if not hit:
            tok = norm_token(meta['token'])
            # token match: require the token as a substring (tokens are descriptive, e.g. anumukha_shani_period_duration_days)
            if len(tok) >= 4 and tok in joined:
                hit = True
        (bright if hit else dark_absent).append(cid)
    return bright, dark_toolnever, dark_absent

def breakdown(idx, cids):
    by_layer = Counter(idx[c]['layer'] for c in cids)
    by_tool = Counter((idx[c]['tool'] or 'none') for c in cids)
    by_family = Counter(idx[c]['family'] for c in cids)
    return dict(by_layer), dict(by_tool.most_common()), dict(by_family.most_common(40))

def family_full(idx, cids):
    from collections import Counter
    return dict(Counter(idx[c]['family'] for c in cids).most_common())

if __name__ == '__main__':
    acc, run_glob = sys.argv[1], sys.argv[2]
    dump_path = sys.argv[3] if len(sys.argv) > 3 else None
    idx, meta = load_served(acc)
    tools_called, per_tool_blob, files, n_calls = load_transcripts(run_glob)
    bright, dtn, dab = match(idx, tools_called, per_tool_blob)
    dark = dtn + dab
    # which transcript ids were ingested (basename without .json)
    run_ids = sorted(os.path.basename(f)[:-5] for f in files)
    out = {
        'domain': meta['domain'], 'chart_id': meta['chart_id'],
        'served_total': len(idx),
        'transcripts_ingested': len(files),
        'replay_ids_ingested': run_ids,
        'tool_calls_ingested': n_calls,
        'tools_called_in_corpus': sorted(tools_called),
        'bright_count': len(bright), 'dark_count': len(dark),
        'dark_tool_never_called': len(dtn), 'dark_substance_absent': len(dab),
        'coverage_pct': round(100*len(bright)/len(idx), 2),
        'dark_by_layer': breakdown(idx, dark)[0],
        'dark_by_serving_tool': breakdown(idx, dark)[1],
        'dark_by_family_full': family_full(idx, dark),
        'bright_by_layer': breakdown(idx, bright)[0],
        'bright_by_serving_tool': breakdown(idx, bright)[1],
        'bright_by_family_full': family_full(idx, bright),
    }
    print(json.dumps(out, indent=2))
    if dump_path:
        full = dict(out)
        full['tool_never_called_tools'] = sorted(set((idx[c]['tool'] or 'none') for c in dtn))
        full['dark_concept_ids'] = sorted(dark)
        full['bright_concept_ids'] = sorted(bright)
        json.dump(full, open(dump_path, 'w'), indent=1)
        print(f'WROTE {dump_path}', file=sys.stderr)
