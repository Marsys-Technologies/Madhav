"""K8 crosswalk derived from real writer SQL, not a second asserted edge list."""
import ast
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'platform/scripts/governance'))
import asset_census as ac


def sources():
    spec=importlib.util.spec_from_file_location('k8_level_map',ROOT/'00_ARCHITECTURE/control/generate_level_map.py')
    mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
    seed=(ROOT/'platform/scripts/seed/asset_registry_seed.ts').read_text()
    graph={r['asset_id']:r['depends_on'] for r in mod.parse_seed_text(seed)}
    correction=json.loads((ROOT/'platform/migrations/1392_k8_registry_truth.sql').read_text().split('$k8_rows$')[1])
    for row in correction:
        assert graph[row['asset_id']]==row['depends_on']
    return seed,graph,correction


def test_k8_whole_registry_graph_resolves_and_is_acyclic():
    _,graph,rows=sources()
    assert len(rows)==25 and len({r['asset_id'] for r in rows})==25
    def visit(aid,path):
        assert aid not in path, ' -> '.join((*path,aid))
        assert aid in graph, aid
        for dep in graph[aid]:visit(dep,(*path,aid))
    for row in rows:visit(row['asset_id'],())


def test_k8_reads_match_the_actual_known_active_producers_with_one_disclosed_back_read():
    seed,graph,rows=sources()
    ownership=[]
    for block in re.findall(r'^  \{\n(.*?)^  \},',seed,re.M|re.S):
        aid=re.search(r"(?m)^    asset_id: '([^']+)'",block)
        if not aid or 'is_active: false' in block or aid[1]=='bg_sarvatobhadra_grid':continue
        def literal(field):
            found=re.search(r'\b'+field+r''': (null|'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")''',block)
            return None if not found or found[1]=='null' else ast.literal_eval(found[1])
        ownership.append((aid[1],literal('target_table'),literal('count_sql')))
    owners=ac.build_table_owners(ownership)
    # These are lifecycle/selector inputs, not products of Avadhi or K6.
    # The current census count_sql owner inference over-attributes nested FROMs;
    # that detector gap is disclosed, never repaired with fictitious writer edges.
    for workflow_table in ('kala_layer_head','kala_layer_candidate','build_runs'):
        owners.pop(workflow_table,None)
    back_reads=set(); matched=0
    for row in rows:
        aid=row['asset_id'];files=[aid+'.py'];path=ac.WRITERS/files[0]
        if ac._writer_class(path,aid) is None:
            for imported in ac._first_party_imports(ast.parse(path.read_text()),path):
                if ac._writer_class(imported,aid):
                    files=[str(imported.relative_to(ac.SIDECAR))];break
        scan=ac.reads_scan(aid,files)
        for table,sites in scan['reads'].items():
            producers=set(owners.get(table,[]))
            if not producers or aid in producers:continue
            if producers & set(row['depends_on']):matched+=1;continue
            # Never repair a downstream calibration read by creating a cycle.
            cyclic={p for p in producers if aid in ac._ancestors(graph,p)}
            if cyclic==producers:
                back_reads.add((aid,table,tuple(sorted(producers))));continue
            raise AssertionError((aid,table,sorted(producers),sites))
    assert matched>=50, 'read coverage must exercise the real writer portfolio'
    assert back_reads=={('ka_kshetra','kala_field_weight_versions',('mi_bhara',))}


def test_k8_counter_sql_is_nonconstant_chart_scoped_and_services_have_no_fake_counts():
    seed,_,_=sources()
    for block in re.findall(r'^  \{\n(.*?)^  \},',seed,re.M|re.S):
        aid=re.search(r"(?m)^    asset_id: '(ka_[^']+)'",block)
        if not aid:continue
        if "storage_type: 'service'" in block:
            assert 'count_sql: null' in block
        else:
            assert re.search(r'count_sql: .*\$1',block)
            assert re.search(r'count_sql: .*\bFROM\b',block,re.I)


def test_k8_writer_flags_match_the_real_registered_classes():
    seed,_,rows=sources()
    for row in rows:
        aid=row['asset_id'];path=ac.WRITERS/(aid+'.py')
        cls=ac._writer_class(path,aid)
        if cls is None:
            for imported in ac._first_party_imports(ast.parse(path.read_text()),path):
                cls=ac._writer_class(imported,aid)
                if cls is not None:
                    path=imported;break
        assert row['has_writer'] is (cls is not None),aid
        start=seed.index("    asset_id: '"+aid+"'")
        block=seed[start:seed.index('\n  },',start)]
        seed_flag=re.search(r'has_writer: (true|false)',block)
        assert seed_flag and (seed_flag[1]=='true') is row['has_writer'],aid
        if cls is not None:
            classes={n.name:n for n in ast.parse(path.read_text()).body if isinstance(n,ast.ClassDef)}
            def substeps(klass):
                for node in klass.body:
                    if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='has_substeps' for t in node.targets):
                        return ast.literal_eval(node.value)
                return any(substeps(classes[b.id]) for b in klass.bases if isinstance(b,ast.Name) and b.id in classes)
            assert row['has_substeps'] is substeps(cls),aid


def test_k8_counter_bootstrap_matches_the_existing_generation_aware_migrations():
    seed,_,rows=sources()
    source=(ROOT/'platform/migrations/1356_k6_read_model_build_scoped_detectors.sql').read_text()
    expected={aid:q.strip() for q,aid in re.findall(r"count_sql=\$count\$(.*?)\$count\$ WHERE asset_id='([^']+)'",source,re.S)}
    avadhi=(ROOT/'platform/migrations/1341_k1_2_avadhi_candidate_dossiers.sql').read_text()
    expected['ka_avadhi']=re.search(r"count_sql='((?:''|[^'])*)'",avadhi)[1].replace("''", "'")
    assert {r['asset_id'] for r in rows if 'count_sql' in r}==set(expected)
    for aid,query in expected.items():
        start=seed.index("    asset_id: '"+aid+"'")
        block=seed[start:seed.index('\n  },',start)]
        literal=re.search(r'''\bcount_sql: ('(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*")''',block)[1]
        assert ast.literal_eval(literal)==query,aid
        assert next(r for r in rows if r['asset_id']==aid)['count_sql']==query
