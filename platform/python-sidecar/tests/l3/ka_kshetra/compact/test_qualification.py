from services.ka_kshetra.compact.qualification import qualify, aggregate
from .fixtures import evaluator, curved_evaluator


def test_trial_distinguishes_test_success_from_numerical_contract_failure():
    result = qualify(curved_evaluator(), fixture_id='curved', expected_knots=(0, 16, 32))
    assert result['clauses']['per_segment_bound']['passed']
    assert result['clauses']['one_sided_discontinuities']['passed']
    assert not result['clauses']['null_statistics']['passed']
    assert result['status'] == 'failed_with_failing_clause'
    assert 'null_statistics' in result['failed_clauses']


def test_no_vacuous_pass_for_empty_trial_or_omitted_fixture():
    assert aggregate([], required_fixtures={'clock'})['status'] == 'failed_with_failing_clause'
    clock = qualify(evaluator(), fixture_id='clock', expected_knots=(0, 16, 32))
    assert clock['status'] == 'implemented_and_proven'
    report = aggregate([clock], required_fixtures={'clock', 'curved'})
    assert report['status'] == 'failed_with_failing_clause'
    assert report['production_activation'] is False


def test_failed_root_detector_cannot_claim_adversarial_fixture_passed():
    result = qualify(evaluator(), fixture_id='missing-root', expected_knots=(13,))
    assert not result['clauses']['adversarial_switching_peaks']['passed']


def test_source_hashes_and_tolerances_are_carried_in_result():
    result = qualify(evaluator(), fixture_id='clock', expected_knots=(0, 16, 32))
    assert result['reference']['dhara_null.py']['sha256']
    assert result['reference']['hazard.py']['sha256']
    assert len(result['candidate']['compiler.py']['sha256']) == 64
    assert len(result['candidate']['null.py']['sha256']) == 64
    assert result['tolerances']['null_rtol'] == 1e-12
    assert result['tolerances']['tau_nats'] == .02


def test_aggregate_recomputes_status_from_clauses_not_supplied_green_label():
    result = qualify(evaluator(), fixture_id='clock', expected_knots=(0, 16, 32))
    result['clauses']['null_statistics']['passed'] = False
    result['failed_clauses'] = []
    result['status'] = 'implemented_and_proven'
    assert aggregate([result], required_fixtures={'clock'})['status'] == 'failed_with_failing_clause'


def test_committed_trial_runs_all_adversaries_and_reports_actual_failing_clause():
    from .run_contract_trial import build_report
    result = build_report()
    assert {fixture['fixture_id'] for fixture in result['fixtures']} == {
        'corrected_clock', 'max_switch_and_peak', 'min_crossing',
        'steps_and_support_edges', 'curved_suppression', 'shift_seam',
        'long_horizon',
    }
    assert result['status'] == 'failed_with_failing_clause'
    assert result['failed_clauses'] == {'curved_suppression': ['null_statistics']}
    assert result['dense_path_disposition'] == 'retain'
    for fixture in result['fixtures']:
        for clause, data in fixture['clauses'].items():
            if clause != 'null_statistics':
                assert data['passed'], (fixture['fixture_id'], clause, data)
