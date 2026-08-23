#!/usr/bin/env python3
"""Render CONSUMER_MAP.md from CONSUMER_MAP.json. No new facts are introduced here."""
import json, pathlib, collections

ROOT = pathlib.Path(__file__).resolve().parents[2]
D = json.loads((ROOT / '00_ARCHITECTURE/control/CONSUMER_MAP.json').read_text())
M, A = D['_meta'], D['assets']

CLASS_LABEL = {
    'serving_consumer_detected': 'serving consumer detected',
    'serving_consumer_detected_via_code_module': 'serving consumer detected (code-module interface)',
    'writer_consumer_only': 'writer consumers only',
    'writer_consumer_only_via_code_module': 'writer consumers only (code-module interface)',
    'statements_only_in_non_serving_buckets': 'no consumer — statements only in its own writer / seed / ops scripts',
    'UNKNOWN_no_table_declared': 'UNKNOWN — asset declares no table and no reachable code interface',
    'UNKNOWN_reads_exist_but_unattributed': 'UNKNOWN — reads exist that this method could not attribute',
    'no_sql_statement_found_anywhere': 'no SQL statement found anywhere in the scanned corpus',
}

def top_consumers(v, n=6):
    ks = sorted(v['serving_consumers'])
    out = []
    for k in ks[:n]:
        x = v['serving_consumers'][k]
        s = k
        if x['tier'] == 'capability' and x.get('mcp_tools'):
            s += ' → ' + ','.join(x['mcp_tools'][:2])
        out.append(f'`{s}`')
    if len(ks) > n:
        out.append(f'…+{len(ks) - n}')
    return '<br>'.join(out) if out else '—'

L = []
w = L.append
w('# NIRMĀṆA M0-T6 — Asset → Serving-Surface Consumer Map')
w('')
w(f"**Generated:** {M['generated_at']}  ")
w(f"**Generator:** `{M['generator']}` (machine-readable output: `00_ARCHITECTURE/control/CONSUMER_MAP.json`)  ")
w(f"**Task:** {M['task']}  ")
w(f"**Database access:** {M['db_access']}  ")
w(f"**Status:** observations only. This document issues no verdict, proposes no disposition and "
  f"certifies nothing (I16 / charter H7). Promote / retire / reclassify is ADHIKĀRIN's G1 power.")
w('')
w('---')
w('')
w('## 0 — What was scanned')
w('')
w('| quantity | value |')
w('|---|--:|')
w(f"| registered assets | {M['assets']} |")
w(f"| source files scanned (non-test) | {M['files_scanned']} |")
w(f"| distinct tables/views indexed | {M['tables_indexed']} |")
w(f"| API routes detected (`app/**/route.ts`) | {M['surfaces_detected']['api_route']} |")
w(f"| UI pages detected (`app/**/page.tsx`) | {M['surfaces_detected']['ui_page']} |")
w(f"| MCP tool names detected (`server.tool(`/`registerTool(`) | {M['surfaces_detected']['mcp_tool']} |")
w(f"| MCP resource names detected (`server.resource(`) | {M['surfaces_detected'].get('mcp_resource', 0)} |")
w(f"| FastAPI sidecar endpoints detected | {M['surfaces_detected']['sidecar_endpoint']} |")
w(f"| retrieval capability URIs detected (`marsys://…`) | {M['surfaces_detected']['retrieval_capability_uris']} |")
w(f"| python writers detected (`@register(...)`) | {M['surfaces_detected']['python_writers']} |")
w(f"| resolved import edges | {M['import_edges']} |")
w(f"| import-walk depth cap | {M['import_depth']} |")
w(f"| hub modules excluded from traversal (fan-in ≥ {M['hub_fanin_threshold']}) | {M['hub_modules']} |")
w('')
w('## 1 — Method')
w('')
w('The map is built from code, not from what the registry claims about itself. In outline:')
w('')
w("1. Each asset contributes its `target_table` (**primary**) plus any table names parsed out of "
  "its `count_sql` and `clear_tables` (**derived**). Every view, materialized view and SQL "
  "function whose definition names one of those tables is resolved from `pg_views` / "
  "`pg_matviews` / `pg_proc`, and the view name is scanned too (**via_db_view**).")
w("2. Every non-test file in the four corpora (`platform-mcp/src`, `platform/src`, "
  "`platform/scripts`, the python sidecar) is scanned for whole-word occurrences of those names. "
  "Each hit is graded `sql_read` (immediately preceded by `FROM`/`JOIN`/`USING`), `sql_write` "
  "(`INTO`/`UPDATE`/`DELETE FROM`/`TRUNCATE`/`TABLE`) or `weak` (anything else — a comment, a "
  "description string, an identifier). **`weak` hits are never treated as evidence of a consumer.**")
w("3. A statement is attributed to a consumer by one of four relations, never by an unbounded "
  "transitive import walk:")
w('')
w('   | tier | relation |')
w('   |---|---|')
w('   | `direct` | the statement is inside the surface file itself (a `route.ts`, a `page.tsx`, a file calling `server.tool()`, a FastAPI router) |')
w("   | `capability` | the statement is inside a retrieval `CapabilityDescriptor` module. The capability's own `marsys://` URI **is** the served surface — `POST /api/retrieval/capability` dispatches it — and the MCP tool bound to that URI is named from platform-mcp's generated surface profile (an exact binding, not an import walk) |")
w(f"   | `traced` | the statement is in a library module forward-reachable from a route/page/router within {M['import_depth']} import hops, not crossing a hub module |")
w('   | `writer` | the statement is in a python module reachable from a `@register()`-ed writer — this is an **input** consumer, reported separately from serving consumers and never merged with them |')
w('')
w("4. Anything else the scan found is kept, per asset, in a non-serving bucket "
  "(`own_writer` / `registry_declaration` / `ops_script` / `prompt_text`) or as an "
  "`unattributed_read`, rather than being dropped.")
w("5. For an asset whose interface is code rather than rows (`asset_kind = service`, or a "
  "registry row with `provides_apis` and no `target_table`), a second, separate detector runs: "
  "who imports the module(s) that own the asset, and whether the symbols named in "
  "`provides_apis` appear anywhere in the corpus.")
w('')
w('## 2 — What this method cannot show')
w('')
w('This is the part M0-T1 flagged as still open. It is not closed by this document; it is *scoped*.')
w('')
for lim in M['method_limits']:
    w(f'- {lim}')
w('')
w('## 3 — Headline counts')
w('')
cnt = collections.Counter(v['evidence_class'] for v in A.values())
w('| evidence class | assets |')
w('|---|--:|')
for k, n in sorted(cnt.items(), key=lambda kv: -kv[1]):
    w(f'| {CLASS_LABEL.get(k, k)} | {n} |')
w(f'| **total** | **{len(A)}** |')
w('')
serving = [a for a, v in A.items() if v['evidence_class'].startswith('serving_consumer_detected')]
writer_only = [a for a, v in A.items() if v['evidence_class'].startswith('writer_consumer_only')]
unknown = [a for a, v in A.items() if v['evidence_class'].startswith('UNKNOWN')]
none_ = [a for a, v in A.items() if v['evidence_class'] in
         ('statements_only_in_non_serving_buckets', 'no_sql_statement_found_anywhere')]
w(f'- **≥1 serving consumer detected: {len(serving)}**')
w(f'- **only writer (input) consumers: {len(writer_only)}**')
w(f'- **no consumer of any kind detected: {len(none_)}** — {", ".join("`%s`" % x for x in sorted(none_))}')
w(f'- **UNKNOWN-only evidence: {len(unknown)}** — {", ".join("`%s`" % x for x in sorted(unknown))}')
w('')
w(f'The zero-serving set is therefore **{len(writer_only) + len(none_) + len(unknown)} assets**, '
  f'not the 13 the plan states (§1 / v3.0 §0.8c). See '
  '`ZERO_CONSUMER_EVIDENCE_v1_0.md` for the per-asset packets and for the reconciliation of the '
  'two figures.')
w('')
w('## 4 — Full map')
w('')
w('`serve` = distinct serving surfaces detected · `wr` = distinct writer (input) consumers · '
  '`rd`/`wt` = SQL-context read/write statements found · `?` = unattributed reads present.')
w('')
w('| asset_id | layer | status | kind | target_table | serve | wr | rd | wt | ? | evidence class | detected serving consumers (first 6) |')
w('|---|---|---|---|---|--:|--:|--:|--:|:--:|---|---|')
for a in sorted(A):
    v = A[a]
    w('| `{aid}` | {lay} | {st} | {kd} | {tt} | {sv} | {wr} | {rd} | {wt} | {q} | {ec} | {tc} |'.format(
        aid=a, lay=v['layer'] or '—', st=v['catalog_status'], kd=v['asset_kind'] or '—',
        tt=('`%s`' % v['target_table']) if v['target_table'] else '—',
        sv=v['serving_consumer_count'], wr=v['writer_consumer_count'],
        rd=v['sql_context_reads'], wt=v['sql_context_writes'],
        q='Y' if v.get('has_unattributed_reads') else '·',
        ec=CLASS_LABEL.get(v['evidence_class'], v['evidence_class']),
        tc=top_consumers(v)))
w('')
w('## 5 — Co-written tables: attribution is table-level, not partition-level')
w('')
w('Where two or more assets declare the same `target_table` (census §5), a consumer of the table '
  'is not necessarily a consumer of *this* asset\'s rows. The affected assets are listed so the '
  'over-attribution is visible rather than silently absorbed:')
w('')
byt = collections.defaultdict(list)
for a, v in A.items():
    if v['target_table']:
        byt[v['target_table']].append(a)
w('| target_table | assets sharing it |')
w('|---|---|')
for t, aa in sorted(byt.items()):
    if len(aa) > 1:
        w(f'| `{t}` | {", ".join("`%s`" % x for x in sorted(aa))} |')
w('')
w('## 6 — What this document does NOT establish')
w('')
w('- It does not prove any surface is reachable by a real caller at runtime, nor that a detected '
  'read executes on any code path a user can trigger.')
w('- It does not prove an asset with no detected consumer is unused — only that this method, with '
  'the limits in §2, found none.')
w('- It does not evaluate whether any asset\'s rows are correct, complete or current.')
w('- It proposes no disposition and takes none. Promote / retire / reclassify is ADHIKĀRIN\'s G1 '
  'power, on this evidence (charter §1).')
w('- It certifies nothing. Verification belongs to PARĪKṢAKA (I16).')
w('')

(ROOT / '00_ARCHITECTURE/control/CONSUMER_MAP.md').write_text('\n'.join(L) + '\n')
print('wrote CONSUMER_MAP.md', len(L), 'lines')
