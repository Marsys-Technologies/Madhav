"""K-AVADHI-C preparation, NOT a canonical failure capture or registry port.

The synthetic M4-shaped defect below must never be presented as native readback.
Run the full installed 1341 SQL as well as the independently retained legacy SQL.
"""
from copy import deepcopy

import pytest
from psycopg.types.json import Jsonb

from pipeline.orchestrator.writers.ka_avadhi import KaAvdhiWriter
from tests.l3.kala_db.ka_avadhi.test_writer import AYA, BUILD, CHART, GEN, NATAL, PLATFORM, ctx, db  # noqa: F401


def inspect(db, chart=CHART, build=BUILD):
    from services.ka_avadhi.integrity import inspect_candidate
    return inspect_candidate(db, chart, build)


def installed_check(db):
    sql = db.execute("SELECT integrity_check_sql FROM asset_registry WHERE asset_id='ka_avadhi'").fetchone()[0]
    return db.execute(sql).fetchone()[0]


def legacy_check(db):
    # Same whole 1023 SQL retained by 1341, scoped exactly as 1341 scopes it.
    original = (PLATFORM / 'migrations/1023_nirmana_l3_ka_avadhi_integrity_conjunct_d_graha_code_fix.sql').read_text().split('$ck$')[1]
    sql = "WITH retained_legacy AS (SELECT * FROM kala_avadhi WHERE generation='legacy') "
    sql += original.replace('kala_avadhi', 'retained_legacy')
    return db.execute(sql).fetchone()[0]


def snapshot(db):
    return db.execute('SELECT row_to_json(a)::text FROM kala_avadhi a ORDER BY avadhi_id').fetchall()


def change_dossier(db, fn):
    dossier = deepcopy(db.execute("SELECT dossier FROM kala_avadhi WHERE generation=%s AND lord_graha='Mars'", (GEN,)).fetchone()[0])
    fn(dossier)
    db.execute("UPDATE kala_avadhi SET dossier=%s WHERE generation=%s AND lord_graha='Mars'", (Jsonb(dossier), GEN))


def test_candidate_pass_does_not_turn_synthetic_legacy_failure_green(db):
    db.execute("UPDATE kala_avadhi SET dossier=jsonb_set(dossier,'{lord_condition_fact_refs}','[]') WHERE generation='legacy'")
    before = snapshot(db)
    assert legacy_check(db) is False and installed_check(db) is False
    KaAvdhiWriter().run(ctx(db))
    report = inspect(db)
    assert report.passed is True
    assert report.generation == GEN and report.rows_checked == 2
    assert report.certification_hold is True
    assert report.warning == 'Candidate validation does not repair legacy rows; retain the legacy detector, certification HOLD and served warning.'
    assert legacy_check(db) is False and installed_check(db) is False
    assert all(row in snapshot(db) for row in before)


@pytest.mark.parametrize('mutation', [
    "DELETE FROM kala_layer_candidate",
    "UPDATE kala_layer_candidate SET build_id='00000000-0000-0000-0000-000000000999'",
    "UPDATE kala_layer_candidate SET chart_id='00000000-0000-0000-0000-000000000999'",
    "UPDATE kala_layer_candidate SET state='published'",
    "INSERT INTO kala_layer_head SELECT chart_id,generation FROM kala_layer_candidate",
    "DELETE FROM kala_avadhi WHERE generation<>'legacy'",
    "DELETE FROM kala_avadhi WHERE generation<>'legacy' AND level_n=2",
    "UPDATE kala_avadhi SET source_dasha_build_id=NULL WHERE generation<>'legacy'",
    "UPDATE kala_avadhi SET source_natal_build_id=NULL WHERE generation<>'legacy'",
    "UPDATE kala_avadhi SET ayanamsha_id='wrong' WHERE generation<>'legacy'",
    "UPDATE kala_avadhi SET lord_graha='Venus' WHERE generation<>'legacy' AND lord_graha='Mars'",
    "UPDATE kala_avadhi SET period_start_iso=period_start_iso+interval '1 second' WHERE generation<>'legacy'",
    "UPDATE kala_layer_candidate SET conventions=jsonb_set(conventions,'{natal,tier}','\"single\"')",
    "UPDATE kala_layer_candidate SET conventions=jsonb_set(conventions,'{f2,systems}','[\"vimshottari\",\"ashtottari\"]')",
    "UPDATE kala_avadhi SET source_dasha_row_id='00000000-0000-0000-0000-000000000999' WHERE generation<>'legacy' AND level_n=1",
    "UPDATE kala_avadhi SET generation='unrelated-build' WHERE generation<>'legacy'",
    "INSERT INTO kala_layer_candidate SELECT chart_id,'other-candidate',build_id,state,conventions FROM kala_layer_candidate",
])
def test_dispatch_binding_coverage_and_pins_fail_closed(db, mutation):
    KaAvdhiWriter().run(ctx(db))
    db.execute(mutation)
    assert inspect(db).passed is False


@pytest.mark.parametrize('mutation', [
    "DELETE FROM chart_facts WHERE fact_id='CODEX-Mars-house'",
    "UPDATE chart_facts SET chart_id='00000000-0000-0000-0000-000000000999' WHERE fact_id='CODEX-Mars-house'",
    "UPDATE chart_facts SET build_id='00000000-0000-0000-0000-000000000999' WHERE fact_id='CODEX-Mars-house'",
    "UPDATE chart_facts SET ayanamsha_id='wrong' WHERE fact_id='CODEX-Mars-house'",
    "UPDATE chart_facts SET fact_subject='VEN' WHERE fact_id='CODEX-Mars-house'",
    "UPDATE chart_facts SET fact_key='sign' WHERE fact_id='CODEX-Mars-house'",
    "UPDATE chart_facts SET fact_value_num=8 WHERE fact_id='CODEX-Mars-house'",
    "UPDATE chart_facts SET verification_pass_status='single' WHERE fact_id='CODEX-Mars-house'",
])
def test_real_fact_identity_and_inherited_value_mutants(db, mutation):
    KaAvdhiWriter().run(ctx(db))
    db.execute(mutation)
    assert inspect(db).passed is False


@pytest.mark.parametrize('mutant', ['absent', 'dangling', 'wrong_lord', 'value', 'ref_value', 'ref_subject', 'ref_key', 'ref_role', 'missing_refs', 'unsupported_null', 'conceal_available', 'untyped', 'promotion'])
def test_payload_mutants_cannot_hide_behind_typed_null_or_existing_fact_id(db, mutant):
    KaAvdhiWriter().run(ctx(db))
    def mutate(d):
        if mutant == 'absent': d.pop('lord_condition_fact_refs')
        elif mutant == 'dangling': d['lord_condition_fact_refs'][0]['fact_id'] = 'does-not-exist'
        elif mutant == 'wrong_lord': d['lord_condition_fact_refs'][0]['fact_id'] = 'CODEX-Venus-house'
        elif mutant == 'value': d['lord_condition']['value']['house_d1']['value'] = 99
        elif mutant.startswith('ref_'): d['lord_condition_fact_refs'][0][mutant[4:].replace('subject', 'fact_subject').replace('key', 'fact_key')] = 'wrong'
        elif mutant == 'missing_refs': d['lord_condition_fact_refs'] = []
        elif mutant in ('unsupported_null', 'conceal_available', 'untyped'):
            d['lord_condition'] = {'value': None, 'null_reason': {'unsupported_null': 'unknown', 'conceal_available': 'missing_fact', 'untyped': None}[mutant], 'fact_ids': []}
            d['lord_condition_fact_refs'] = []
        elif mutant == 'promotion': d['attached_mechanisms'][0]['effective_state'] = 'in_force'
    change_dossier(db, mutate)
    assert inspect(db).passed is False


def test_json_boolean_does_not_impersonate_numeric_l1_value(db):
    db.execute("UPDATE chart_facts SET fact_value_num=1 WHERE fact_id='CODEX-Mars-house'")
    KaAvdhiWriter().run(ctx(db))
    change_dossier(db, lambda d: d['lord_condition']['value']['house_d1'].update(value=True))
    assert inspect(db).passed is False


def test_full_current_sql_does_not_measure_inherited_candidate_values(db):
    KaAvdhiWriter().run(ctx(db))
    assert installed_check(db) is True and legacy_check(db) is True
    change_dossier(db, lambda d: d['lord_condition']['value']['house_d1'].update(value=99))
    assert installed_check(db) is True  # Synthetic proof of the current gate's gap.
    assert inspect(db).passed is False


@pytest.mark.parametrize('method,lords,reason', [
    ('chara_karaka', ['Aries', 'Taurus'], 'method_inapplicable'),
    ('yogini', ['Mangala', 'Siddha'], 'missing_fact'),
])
def test_method_specific_lords_and_null_reasons(db, method, lords, reason):
    db.execute("UPDATE kala_layer_candidate SET conventions=jsonb_set(conventions,'{f2,systems}',%s)", (Jsonb([method]),))
    for level, lord in enumerate(lords, 1):
        db.execute('UPDATE chart_dashas SET system_id=%s,lord_graha=%s WHERE level_n=%s', (method, lord, level))
    KaAvdhiWriter().run(ctx(db))
    assert inspect(db).passed is True
    dossier = db.execute('SELECT dossier FROM kala_avadhi WHERE generation=%s AND level_n=1', (GEN,)).fetchone()[0]
    assert dossier['lord_condition']['null_reason'] == reason
    change_dossier_for_lord = deepcopy(dossier)
    change_dossier_for_lord['lord_condition']['null_reason'] = 'information_unavailable'
    db.execute('UPDATE kala_avadhi SET dossier=%s WHERE generation=%s AND level_n=1', (Jsonb(change_dossier_for_lord), GEN))
    assert inspect(db).passed is False


def test_missing_fact_null_requires_actual_pinned_input_absence(db):
    db.execute("DELETE FROM chart_facts WHERE fact_subject IN ('MAR','D1_MAR')")
    KaAvdhiWriter().run(ctx(db))
    assert inspect(db).passed is True
    db.execute("INSERT INTO chart_facts VALUES ('new-Mars-sign',%s,%s,%s,'two_pass_verified','graha_position','MAR','sign','Aries',NULL,NULL,'synthetic')", (CHART, NATAL, AYA))
    assert inspect(db).passed is False


def test_partial_null_l1_value_is_inherited_and_cannot_be_invented(db):
    db.execute("UPDATE chart_facts SET fact_value_num=NULL WHERE fact_id='CODEX-Mars-house'")
    KaAvdhiWriter().run(ctx(db))
    assert inspect(db).passed is True
    change_dossier(db, lambda d: d['lord_condition']['value']['house_d1'].update(value=3, null_reason=None))
    assert inspect(db).passed is False


def test_repeat_inspection_and_other_chart_corruption_are_read_only_and_isolated(db):
    KaAvdhiWriter().run(ctx(db))
    db.execute("INSERT INTO kala_avadhi(chart_id,system_id,level_n,lord_graha,period_start,period_end,dossier) VALUES ('00000000-0000-0000-0000-000000000999','vimshottari',1,'Mars','2000-01-01','2001-01-01','{}')")
    before = snapshot(db)
    first = inspect(db)
    assert first.passed is True and inspect(db) == first
    assert inspect(db, chart='00000000-0000-0000-0000-000000000999').passed is False
    assert snapshot(db) == before
    assert installed_check(db) is False


def test_published_rows_and_registry_bytes_stay_unchanged(db):
    KaAvdhiWriter().run(ctx(db))
    db.execute("UPDATE kala_layer_candidate SET state='published'")
    before, registry = snapshot(db), db.execute('SELECT row_to_json(r)::text FROM asset_registry r').fetchall()
    assert inspect(db).passed is False
    assert snapshot(db) == before
    assert db.execute('SELECT row_to_json(r)::text FROM asset_registry r').fetchall() == registry


def test_existing_mandatory_db_job_collects_preparation_suite():
    import yaml
    ci = yaml.safe_load((PLATFORM.parent / '.github/workflows/ci.yml').read_text())
    job = ci['jobs']['kala-db-tests']
    step = next(s for s in job['steps'] if 'pytest tests/l3/kala_db ' in s.get('run', ''))
    assert str(step['env']['KALA_REQUIRE_DB']) == '1'
    assert step['env']['KALA_ADMIN_DSN']
    assert not job.get('continue-on-error') and not step.get('continue-on-error')
    assert 'changes' in job['needs'] and "docs_only != 'true'" in job['if']
    assert not any(flag in step['run'] for flag in ('--ignore', '--deselect', ' -k ', '||'))
