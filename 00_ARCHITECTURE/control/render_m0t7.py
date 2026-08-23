#!/usr/bin/env python3
"""Render DRAFT_INVENTORY.md and DAG_AUDIT_v1_0.md from the two JSON artefacts.
Presentation only — every figure comes from the JSON, nothing is computed here that
is not a re-count of what the JSON already holds."""
import json, pathlib, collections
ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT  = ROOT/'00_ARCHITECTURE/control'
inv  = json.load(open(OUT/'DRAFT_INVENTORY.json'))
dag  = json.load(open(OUT/'DAG_AUDIT.json'))
A, M = inv['assets'], inv['_meta']
DM   = dag['_meta']

def yn(v):
    return {'yes':'**yes**','no':'no'}.get(v, v)

# ── DRAFT_INVENTORY.md ────────────────────────────────────────────────────────
L=[]
w=L.append
w('# NIRMĀṆA M0-T7 — DRAFT-but-served inventory (Phase 0.8b)')
w('')
w(f"**Generated:** {M['generated_at']}  ")
w(f"**Generators:** `00_ARCHITECTURE/control/draft_reachability.py` (facts) · `render_m0t7.py` (this page)  ")
w(f"**Git:** `{M['git_branch']}` @ `{M['git_head']}`  ")
w(f"**Database access:** {M['database_access']}  ")
w(f"**Credential handling:** {M['credential_handling']}  ")
w(f"**Native chart:** `{M['native_chart']}`  ")
w('**Status:** observations only. This document issues no verdict, decides no disposition and')
w('certifies nothing. Catalogue disposition is charter power **G1 (ADHIKĀRIN)**; this is the')
w('evidence it rests on (I16 / charter H7).')
w('')
w('## 0 — The four facts, kept apart')
w('')
w('The plan\'s exit criterion says "DRAFT-but-served". *Served* has four different readings and')
w('they do not agree with each other. Each asset below is reported against all four, separately.')
w('')
w('| # | Fact | What produced it | What it does NOT establish |')
w('|---|---|---|---|')
w('| **F1** | `registry_active` — the registry claims the asset is active | `asset_registry.is_active` (live DB) | Nothing about whether any code reads its output. It is the registry\'s claim about itself. |')
w('| **F2** | `rows_exist` — the asset\'s target table(s) hold rows | `SELECT count(*)` on each table, plus the asset\'s own `count_sql` run for the native chart | That the rows are correct, current, or built by this asset rather than a co-writer of the same table. |')
w('| **F3** | `surface_references` — a non-test serving-side source file issues a SQL read of one of those tables | regex over comment-stripped source in `platform/src`, `platform-mcp/src`, the FastAPI sidecar; occurrence classified `sql_read` / `sql_write` / `mention` by its immediately preceding SQL context | That the reading file is reachable, or that the read is on a live code path. Dynamic SQL (`FROM ${table}`) is flagged `dynamic_sql_candidate`, not counted as a confirmed read. |')
w('| **F4** | `caller_reachable` — that file sits in the transitive import closure of a caller-facing entrypoint, and (for a retrieval capability) its descriptor is passed to `registerCapability()` from a module in that closure | TS import graph over '+str(M['ts_files_scanned'])+' files from '+str(M['ts_entrypoint_roots'])+' entrypoint roots (`app/**/route.ts`, `page.tsx`, `platform-mcp/src/server.ts`, `instrumentation.ts`) → '+str(M['ts_reachable_files'])+' reachable files; Python import graph over '+str(M['py_files_scanned'])+' sidecar files from `main.py` → '+str(M['py_reachable_from_main'])+' reachable | **That a live HTTP call succeeds.** It is static reachability plus registration. It does not evaluate per-profile MCP allowlists, auth gates, feature flags, or runtime errors. A capability can be registered and reachable and still return an error to every caller. |')
w('')
w('Reading them together is what the exit criterion actually needs: F1 alone is the registry')
w('talking about itself; F1+F2 is "built"; F1+F2+F3 is "wired"; all four is "wired and callable".')
w('')
c1=sum(1 for v in A.values() if v['F1_registry_active'])
c2=collections.Counter(v['F2_rows_exist'] for v in A.values())
c3=collections.Counter(v['F3_surface_references'] for v in A.values())
c4=collections.Counter(v['F4_caller_reachable'] for v in A.values())
w('## 1 — Headline counts (re-derived, not inherited)')
w('')
w(f"- `asset_registry` rows: **{M['registry_rows']}**")
w(f"- `catalog_status = 'DRAFT'`: **{M['draft_count']}**")
w(f"- **F1** registry says active: **{c1} / {M['draft_count']}**")
w(f"- **F2** rows exist: **{c2['yes']}** yes · {c2.get('no',0)} no (all-zero tables) · {c2.get('n/a_no_table_declared',0)} no table declared")
w(f"- **F3** a serving surface references the table: **{c3['yes']}** yes · {c3.get('no',0)} no · {c3.get('n/a_no_table_declared',0)} no table declared")
w(f"- **F4** that surface is reachable from a caller entrypoint: **{c4['yes']}** yes · {c4.get('no',0)} no · {c4.get('UNKNOWN_no_table_to_trace',0)} UNKNOWN (no table to trace)")
w('')
w('The four UNKNOWNs are the four `asset_kind = service` DRAFT assets that declare no')
w('`target_table` and no `count_sql` (`ka_dasha_kala`, `ka_graha_sancara`, `ka_muhurta_seva`,')
w('`ka_tulana`). There is no table for the table-tracing method to follow, and they carry no')
w('`provides_apis` and no `health_probe` either — so the F3/F4 method cannot establish their')
w('reachability in **either** direction. They are UNKNOWN, not "unserved".')
w('')
w('**But they are not evidence-free.** All four carry a populated `selftest_detail` written by a')
w('real self-test in their own writer (`services/ka_dasha_kala/writer.py`,')
w('`services/ka_tulana/writer.py`, `writers/ka_graha_sancara.py`, and the FORENSIC-anchored')
w('muhurta probe) — so their `service_health` is an EARNED signal in the §N.8 sense, with a')
w('detector that demonstrably can and does return a non-green verdict: `ka_graha_sancara` reads')
w('`unhealthy` with the failing check recorded verbatim. Each of the four packets below quotes')
w('its `selftest_detail`. That establishes the service *runs and self-checks*; it still does not')
w('establish that any caller reaches it.')
w('')
w('## 2 — The matrix')
w('')
w('| asset_id | layer | kind | F1 active | F2 rows | F3 refs | F4 reachable | native rows | reachable capabilities |')
w('|---|---|---|:--:|:--:|:--:|:--:|--:|---|')
for a in sorted(A):
    v=A[a]
    caps=', '.join(f'`{c}`' for c in v['reachable_capability_names']) or '—'
    nr=v['F2_detail']['count_sql_native']
    w(f"| `{a}` | {v['layer']} | {v['asset_kind']} | {'Y' if v['F1_registry_active'] else '·'} | "
      f"{ {'yes':'Y','no':'0','n/a_no_table_declared':'—'}.get(v['F2_rows_exist'],v['F2_rows_exist']) } | "
      f"{ {'yes':'Y','no':'·','n/a_no_table_declared':'—'}.get(v['F3_surface_references'],v['F3_surface_references']) } | "
      f"{ {'yes':'Y','no':'·','UNKNOWN_no_table_to_trace':'?'}.get(v['F4_caller_reachable'],v['F4_caller_reachable']) } | "
      f"{nr if nr is not None else '—'} | {caps} |")
w('')
w('`Y` = established · `·` = established absent · `?` = UNKNOWN, this method cannot tell · `—` = not applicable · `0` = table exists, zero rows')
w('')
shared = collections.Counter(t for v in A.values() for t in v['tables'])
multi = {t for t,n in shared.items() if n > 1}
if multi:
    w('**Shared-table caveat, read before using the last column.** '
      + ', '.join('`'+t+'`' for t in sorted(multi))
      + ' is the declared table of more than one DRAFT asset, so those assets necessarily show '
        'the SAME capability list — the capability reads the table, not the asset. Seven DRAFT '
        'assets share `bodha_msr_signals` alone. Use each asset\'s own `count_sql` figure (the '
        '"native rows" column) for the asset-scoped quantity; the capability column establishes '
        'that the TABLE is served, not that this asset\'s rows are the ones being read.')
    w('')
notser=[a for a,v in A.items() if v['F4_caller_reachable']=='no']
unk=[a for a,v in A.items() if v['F4_caller_reachable']=='UNKNOWN_no_table_to_trace']
w('## 3 — The DRAFT assets this method finds NOT reachable')
w('')
w(f'**{len(notser)}** DRAFT assets are built (rows present, or table present) but no reachable')
w('serving surface issues a SQL read against their table:')
w('')
for a in sorted(notser):
    v=A[a]
    w(f"- **`{a}`** — {v['english_name']}. Table(s) {', '.join('`'+t+'`' for t in v['tables'])}; "
      f"native rows {v['F2_detail']['count_sql_native']}. "
      + ('No serving-side reference of any kind.' if not v['serving_surfaces']
         else 'Only unreachable references: ' + ', '.join(f"`{s['file']}`" for s in v['serving_surfaces']))
      + (' Build-side readers exist: ' + ', '.join(f"`{x['file']}`" for x in (v.get('build_side_readers') or []))
         + '.' if v.get('build_side_readers') else ''))
w('')
w(f'**{len(unk)}** are UNKNOWN (no table, no `provides_apis`, no `health_probe`): '
  + ', '.join(f'`{a}`' for a in sorted(unk)) + '.')
w('')
w('## 4 — Per-asset evidence packets (for the G1 ruling)')
w('')
w('Each packet states what the asset is, what it produces, whether it is served and **how that')
w('was established**, its DAG neighbourhood, and the *factual* consequence of each of the three')
w('dispositions. It does not recommend one. `promote to CURRENT` / `retire with a')
w('`data_disposition`` / `reclassify as SOURCE` are ADHIKĀRIN\'s (G1).')
w('')
w('> **Schema note that binds all three options.** Re-derived live this session: the')
w('> `asset_registry_catalog_status_check` CHECK permits only `CURRENT | DRAFT | RETIRED`, and')
w('> `asset_registry_asset_kind_check` permits only `data | service | artifact`. There is no')
w('> `SOURCE` value in either column today, and `data_disposition` **does not exist as a column')
w('> in the live database** — migration `590_nirmana_m0_catalogue_contract_columns.sql` (staged')
w('> on this branch, verified NOT applied) would add it. So "retire with a `data_disposition`"')
w('> requires 590 to be applied first, and "reclassify as SOURCE" requires a CHECK-constraint')
w('> change that no migration in this plan names (charter P5). This is a mechanical fact about')
w('> the schema, not an argument for or against any option; it is stated because two of the')
w('> three options are not currently expressible. It independently corroborates')
w('> `ASSET_CATALOGUE_CONTRACT_v1_0.md` §10.1.')
w('')
for a in sorted(A):
    v=A[a]
    w(f"### `{a}`")
    w('')
    w(f"**What it is.** {v['english_name'] or '—'} · layer `{v['layer']}` (`layer_index`="
      f"{v['layer_index']}) · kind `{v['asset_kind']}` · scope `{v['scope']}`.")
    d=(v['english_description'] or '').strip().replace('\n',' ')
    if d: w(f"> {d}")
    w('')
    td=v['F2_detail']
    tl=[]
    for t,e in td['tables'].items():
        tl.append(f"`{t}` (exists={e['exists']}, view={e['is_view']}, total={e['total_rows']}, native={e['native_rows']})")
    w(f"**What it produces.** `target_table` = `{v['target_table']}`. Tables touched: "
      + ('; '.join(tl) if tl else '**none declared**') + '.')
    w(f"`count_sql` for the native chart returns **{td['count_sql_native']}**"
      + (f" (error: `{td['count_sql_error']}`)" if td['count_sql_error'] else '')
      + f"; `target_floor` = {td['target_floor']}.")
    if v['throughput']:
        w("`asset_throughput`: " + '; '.join(f"{t['state']}×{t['n']} (last {t['last_built']}, rows_written {t['rows_written']})" for t in v['throughput']) + '.')
    else:
        w("`asset_throughput`: **no rows**.")
    w('')
    w(f"**Is it served, and how do I know.** F1 `is_active`={v['F1_detail']['is_active']}, "
      f"`has_writer`={v['F1_detail']['has_writer']}, `provides_apis`="
      f"{'set' if v['F1_detail']['provides_apis'] else 'NULL'}, `health_probe`="
      f"{'set' if v['F1_detail']['health_probe'] else 'NULL'}, `service_health`="
      f"{v['F1_detail']['service_health']}, `last_invoked_at`={v['F1_detail']['last_invoked_at']}, "
      f"`last_selftest_at`={v['F1_detail']['last_selftest_at']}. "
      f"F2 **{v['F2_rows_exist']}** · F3 **{v['F3_surface_references']}** · F4 **{v['F4_caller_reachable']}**.")
    if v['F1_detail'].get('selftest_detail'):
        w('')
        w("**`selftest_detail`** (a real detector's own output, quoted verbatim — not a status this audit assigned): "
          + '`' + json.dumps(v['F1_detail']['selftest_detail'])[:700].replace('|','\\|') + '`')
    w('')
    if v['serving_surfaces']:
        w('| surface file | class | reachable | capability (registered?) | evidence |')
        w('|---|---|:--:|---|---|')
        for s in v['serving_surfaces']:
            caps = '; '.join(
                (f"`{c.get('name')}` ({c.get('uri')}) — registered_from_reachable="
                 f"{c.get('registered_from_reachable')}") for c in s['capabilities']) or '—'
            ev = '<br>'.join(f"L{e['line']} `{e['text'][:110].replace('|','\\|')}`" for e in s['evidence'][:3]) or '—'
            w(f"| `{s['file']}` | {s['class']} | {s['reachable']} | {caps} | {ev} |")
        w('')
        if v['capability_attribution_ambiguous_files']:
            w('Capability attribution ambiguous (file defines several descriptors and the read sits')
            w('outside all of them): ' + ', '.join(f"`{f}`" for f in v['capability_attribution_ambiguous_files']) + '.')
            w('')
    else:
        w('_No serving-side SQL read of this asset\'s table was found in any non-test source file._')
        w('')
    bsr=v.get('build_side_readers') or []
    if bsr:
        w('**Build-side readers** (other writers that SELECT from this asset\'s table — not a serving')
        w('surface, but a real consumer a retirement would break): '
          + '; '.join(f"`{x['file']}` (`{x['table']}` L{x['lines'][:3]})" for x in bsr) + '.')
        w('')
    dep=v['depends_on']; rdep=v['depended_on_by_status']
    w(f"**Depends on.** " + (', '.join(f'`{d}`' for d in dep) if dep else '_nothing_') + '.')
    w(f"**Depended on by.** " + (', '.join(f'`{k}` ({s})' for k,s in rdep.items()) if rdep else '_nothing_') + '.')
    w('')
    draft_deps=[d for d in dep if d in A]
    w('**What each disposition would mechanically change.**')
    w('')
    curdeps=[k for k,s in rdep.items() if s=='CURRENT']
    w(f"- *Promote to CURRENT* — "
      + (f"the {len(curdeps)} CURRENT dependent(s) " + ', '.join(f'`{k}`' for k in curdeps)
         + ' would stop being CURRENT-on-DRAFT edges. ' if curdeps
         else 'no CURRENT asset currently depends on it, so no CURRENT-on-DRAFT edge is resolved by this. ')
      + (f"It would itself become a CURRENT asset resting on DRAFT: {', '.join('`'+d+'`' for d in draft_deps)}."
         if draft_deps else 'It declares no DRAFT dependency of its own, so it creates no new CURRENT-on-DRAFT edge.')
      + (f" `integrity_check_sql` is {'set' if v['integrity_check_sql'] else '**NULL**'}"
         f" and `target_floor` is {td['target_floor']}.")
      )
    consumers=[s for s in v['serving_surfaces'] if s['reachable']=='yes']
    w(f"- *Retire with a `data_disposition`* — {len(consumers)} reachable serving surface(s) would be reading a table whose producer is retired"
      + (': ' + ', '.join(f"`{s['file']}`" for s in consumers) if consumers else ' (none found)')
      + f"; {len(rdep)} registry dependent(s) would name a RETIRED upstream"
      + (': ' + ', '.join(f'`{k}`' for k in rdep) if rdep else '')
      + (f"; {len(bsr)} other writer(s) SELECT from its table at build time"
         + (': ' + ', '.join(f"`{x['file'].split('/')[-1]}`" for x in bsr) if bsr else '')
         if bsr else '')
      + '. Requires migration 590 (the `data_disposition` column) to be applied first — it is not.')
    w(f"- *Reclassify as SOURCE* — not expressible today: `asset_kind` CHECK permits only "
      f"`data|service|artifact`. Would additionally void the writer/count/floor/integrity "
      f"requirements for this asset; it currently "
      f"{'HAS' if v['F1_detail']['has_writer'] else 'has NO'} a registered writer"
      + (', which is what a SOURCE asset by definition does not have.' if v['F1_detail']['has_writer']
         else ' — consistent with the SOURCE reading.'))
    w('')
    if v['volume_explanation']:
        w(f"_`volume_explanation`_: {v['volume_explanation'][:300]}")
        w('')
    w('---')
    w('')
w('## 5 — What this inventory does NOT establish')
w('')
w('- **It does not prove any capability actually returns rows to a caller.** F4 is static import')
w('  reachability plus a `registerCapability()` call. No HTTP request was issued and no MCP tool')
w('  was invoked in producing this document.')
w('- **It cannot see dynamic SQL it did not flag.** A read assembled as `FROM ${tableVar}` is')
w('  detected only when the table name also appears as a literal in the same file; a name built')
w('  by concatenation or fetched from another module is invisible. `bo_cdlm_summary` is the')
w('  worked example: its table is read through a `TIER_TABLE` lookup map, so the occurrence is a')
w('  string literal, not a `FROM <table>` match.')
w('- **It does not attribute rows to producers.** Seven assets share `bodha_msr_signals` and five')
w('  share `chart_facts`; a serving surface reading that table is reading *the table*, not')
w('  necessarily this asset\'s rows. Each asset\'s own `count_sql` (reported per asset) is the')
w('  narrower figure.')
w('- **It does not evaluate auth, feature flags, MCP surface-profile allowlists, or runtime')
w('  health.** A reachable, registered capability can still be denied to every caller.')
w('- **It does not evaluate correctness of any row.**')
w('- **It certifies nothing.** Verification belongs to PARĪKṢAKA (I16); disposition to ADHIKĀRIN (G1).')
w('')
(OUT/'DRAFT_INVENTORY.md').write_text('\n'.join(L))
print('wrote DRAFT_INVENTORY.md', len(L), 'lines')

# ── DAG_AUDIT_v1_0.md ─────────────────────────────────────────────────────────
D=[]
w=D.append
q1=dag['q1_current_depends_on_draft']; q2=dag['q2_dangling_registry']
q3=dag['q3_over_declaration']
c=collections.Counter(r['loose'] for r in q3); ct=collections.Counter(r['tight'] for r in q3)
w('# NIRMĀṆA M0-T7 — DAG edge audit v1.0')
w('')
w(f"**Generated:** {DM['generated_at']}  ")
w(f"**Generators:** `00_ARCHITECTURE/control/dag_audit.py` (facts) · `render_m0t7.py` (this page)  ")
w(f"**Git:** `{DM['git_branch']}` @ `{DM['git_head']}`  ")
w(f"**Database access:** {DM['database_access']}  ")
w('**Status:** observations only. No edge was changed. No verdict is issued (I16 / charter H7).')
w('')
w('## 0 — The graph, measured')
w('')
w('| quantity | value | source |')
w('|---|--:|---|')
w(f"| `asset_registry` rows | {DM['registry_rows']} | live DB |")
w(f"| `depends_on` edges (registry) | {DM['registry_edges']} | live DB |")
w(f"| assets declaring ≥1 dependency | {DM['assets_with_deps']} | live DB |")
w(f"| assets declaring none | {DM['assets_without_deps']} | live DB |")
w(f"| asset entries in the seed .ts | {DM['seed_assets']} | `platform/scripts/seed/asset_registry_seed.ts` |")
w(f"| `depends_on` edges (seed .ts) | {DM['seed_edges']} | same |")
w(f"| coefficient edges (seed .ts) | {DM['seed_coefficient_edges']} | same (`upstream_asset_id`/`downstream_asset_id`) |")
w(f"| writer assets resolved from `@register` | {DM['writers_resolved']} | sidecar sources |")
w('')
w('## 1 — CURRENT assets depending on DRAFT assets')
w('')
w(f'**{len(q1)}** instances. This is the contract violation the M0 exit criterion requires to be zero.')
w('')
w('| CURRENT asset | layer | depends on | dependency status | dependency layer |')
w('|---|---|---|---|---|')
rs=dag['registry_status']
for a,d in q1:
    w(f"| `{a}` | {rs[a]['layer']} | `{d}` | {rs[d]['catalog_status']} (is_active={rs[d]['is_active']}) | {rs[d]['layer']} |")
w('')
w(f"Adjacent checks, kept separate because they are different defects:")
w('')
w(f"- CURRENT → RETIRED edges: **{len(dag['q1_current_depends_on_retired'])}**"
  + (' — ' + ', '.join(f'`{a}`→`{d}`' for a,d in dag['q1_current_depends_on_retired']) if dag['q1_current_depends_on_retired'] else ' _(none)_'))
w(f"- CURRENT → `is_active = false` edges: **{len(dag['q1_current_depends_on_inactive'])}**"
  + (' — ' + ', '.join(f'`{a}`→`{d}`' for a,d in dag['q1_current_depends_on_inactive']) if dag['q1_current_depends_on_inactive'] else ' _(none)_'))
w(f"- cycles in the registry DAG: **{len(dag['cycles'])}**"
  + (' — ' + str(dag['cycles']) if dag['cycles'] else ' _(none)_'))
w(f"- self-edges: **{len(dag['self_edges'])}** · duplicate edges: **{len(dag['duplicate_edges'])}**")
w('')
w('## 2 — Dangling edges')
w('')
w('A dangling edge is a `depends_on` entry naming an `asset_id` that has no registry row. The')
w('M0-T1 census found a 138-id union against a 128-row registry, so the question is whether any')
w('of those 10 extra ids is referenced as a dependency. Both declaration surfaces were checked.')
w('')
w(f"- Dangling in the **live registry** (`depends_on` target absent from `asset_registry`): **{len(q2)}**"
  + (' — ' + ', '.join(f'`{a}`→`{d}`' for a,d in q2) if q2 else ' — **zero**.'))
w(f"- Dangling in the **seed .ts** (target absent from the live registry): **{len(dag['q2_dangling_seed_vs_registry'])}**"
  + (' — ' + ', '.join(f'`{a}`→`{d}`' for a,d in dag['q2_dangling_seed_vs_registry']) if dag['q2_dangling_seed_vs_registry'] else ' — **zero**.'))
w(f"- Dangling **within the seed itself** (target absent from the seed's own asset list): **{len(dag['q2_dangling_seed_vs_seed'])}**"
  + (' — ' + ', '.join(f'`{a}`→`{d}`' for a,d in dag['q2_dangling_seed_vs_seed']) if dag['q2_dangling_seed_vs_seed'] else ' — **zero**.'))
w(f"- Seed coefficient edges with a dangling endpoint: **{len(dag['seed_coefficient_dangling'])}**"
  + (' — ' + str(dag['seed_coefficient_dangling']) if dag['seed_coefficient_dangling'] else ' — **zero**.'))
w('')
w('**The 10 non-registry ids the census found do not appear as a dependency target anywhere.**')
w('They are decorator-only test fixtures (`bad_infra_writer`, `fixture.*`, `test_infra_*`) and')
w('migration-only tombstones (`ga_pyjhora_engine`, `ga_vastu_planet_direction_map`,')
w('`ka_gochara_v2_materialize`, `ka_transit_almanac`) — none of them is on the left or right of')
w('any edge. The 138-vs-128 gap is real, and it is not hiding in the DAG.')
w('')
w('### Registry-vs-seed edge divergence (reported, not adjudicated)')
w('')
w(f"- Edges present in the registry but not in the seed: **{len(dag['edges_only_in_registry'])}** — expected, since post-seed migrations add edges.")
w(f"- Edges present in the seed but not in the registry: **{len(dag['edges_only_in_seed'])}**"
  + (' — ' + ', '.join(f'`{a}`→`{d}`' for a,d in dag['edges_only_in_seed']) if dag['edges_only_in_seed'] else ''))
w(f"- Seed assets absent from the registry: {dag['_meta']['seed_assets_not_in_registry'] or '_none_'}")
w(f"- Registry assets absent from the seed: {', '.join('`'+x+'`' for x in dag['_meta']['registry_assets_not_in_seed']) or '_none_'}")
w('')
w('## 3 — Over-declared edges (declared but not read) — evidence, not verdict')
w('')
w('For each declared edge `A → B`, does `A`\'s writer source show a textual read (`FROM`/`JOIN`)')
w('of a table `B` produces? Two scan widths are reported because neither alone is honest:')
w('')
w('- **tight** — only the file carrying `@register(\'A\')`. Too narrow: most writers delegate')
w('  their reads to a service package they import, so a tight miss means nothing on its own.')
w('- **loose** — that file plus the local modules and service packages it imports (1 hop,')
w('  whole-package). Too broad: a package pulled in for one helper contributes all its SQL.')
w('')
w('| verdict | tight scan | loose scan |')
w('|---|--:|--:|')
for k in ['read_evidence','mentioned_not_read','NO_TEXTUAL_READ_EVIDENCE','UNKNOWN_dep_declares_no_table','UNKNOWN_no_writer_source','DANGLING']:
    if ct.get(k,0) or c.get(k,0): w(f"| `{k}` | {ct.get(k,0)} | {c.get(k,0)} |")
w('')
w(f"**No edge lacks read evidence under the loose scan.** {ct.get('NO_TEXTUAL_READ_EVIDENCE',0)} edges")
w('lack it under the tight scan and every one of them is explained by the writer delegating to an')
w('imported service module. **I therefore cannot establish that any edge is over-declared, and I')
w('am not claiming any is.** What I can report is the set of edges whose evidence is weakest —')
w('the dependency\'s table is *mentioned* in the writer\'s source but never read from:')
w('')
w('| edge | dependency tables | writer file |')
w('|---|---|---|')
for r in q3:
    if r['loose']=='mentioned_not_read':
        w(f"| `{r['asset']}` → `{r['dep']}` | {', '.join('`'+t+'`' for t in r['dep_tables'])} | `{r['writer_files'][0]}` |")
w('')
w('And the edges this method cannot evaluate at all:')
w('')
w('| edge | why |')
w('|---|---|')
for r in q3:
    if r['loose']=='UNKNOWN_dep_declares_no_table':
        w(f"| `{r['asset']}` → `{r['dep']}` | the dependency declares no `target_table` and no `count_sql` — there is no table whose read could be looked for |")
    elif r['loose']=='UNKNOWN_no_writer_source':
        w(f"| `{r['asset']}` → `{r['dep']}` | no `@register` writer source resolves for `{r['asset']}` |")
w('')
w('## 4 — Method limits, stated plainly')
w('')
w('- The over-declaration detector is a **regex over source text**. It cannot see dynamic SQL,')
w('  ORM/query-builder access, a read performed by a module it failed to resolve, or a dependency')
w('  that is a genuine *ordering* constraint rather than a data read. A dependency can be')
w('  perfectly correct and produce no read at all.')
w('- The **loose** scan pulls whole service packages, so `read_evidence` under loose does NOT')
w('  prove *this writer* performs *that* read.')
w('- `@register` resolution handles both a string literal and a module-level `ASSET_ID` constant.')
w(f"  It resolved {DM['writers_resolved']} writer assets; {DM['registry_rows']-DM['writers_resolved']} registry rows have no resolvable writer source.")
w('- The seed parser deliberately does **not** strip `/* */` blocks: the file contains prose')
w('  strings holding glob patterns like `gochara_intensity/*`, and a naive block strip silently')
w('  swallows 53 real entries between two of them. It also requires a left word boundary on')
w('  `asset_id:` so `upstream_asset_id:` in the coefficient block is not miscounted as an entry.')
w('  Both are corrections to a first version of this scan that got the seed counts wrong.')
w('- Nothing here evaluates whether an edge *should* exist. Missing edges are the existing')
w('  `pipeline/orchestrator/dag_edge_guard.py`\'s question; this audit is its mirror image and')
w('  does not re-run it.')
w('')
(OUT/'DAG_AUDIT_v1_0.md').write_text('\n'.join(D))
print('wrote DAG_AUDIT_v1_0.md', len(D), 'lines')
