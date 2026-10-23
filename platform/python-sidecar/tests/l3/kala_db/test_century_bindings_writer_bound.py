"""F-CHANNEL claims 3, 4, 5 (SR-W34-PREP-RULINGS 1) that need the REAL ka_gochara_v5 writer: the century manifest component, the launcher's staged/expected manifest and the
dispatch's CLI-vs-request check all validate through the writer's own `validate_century_config` (v5_small_test_shared.writer(); the single implementation of what the
writer accepts). The governance tool-test shards install only pyyaml + pytest, where that import honestly refuses; these four therefore run here, in the sidecar
environment (Kāla DB Tests job), with the writer importable. Claims 1-2 (the exact argument contract) need no writer and stay in
platform/scripts/governance/__tests__/test_century_bindings.py. Moved verbatim, not weakened."""
import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
FLEET = ROOT / '00_ARCHITECTURE/briefs/kalayantra/fleet'
SCRIPTS = ROOT / 'platform/scripts'
for path in (str(SCRIPTS), str(SCRIPTS / '__tests__'), str(FLEET)):
    if path not in sys.path:
        sys.path.insert(0, path)
import v5_small_test_shared as shared
import smalltest_safety_support as S

# SYNTHETIC bounds only — the real D-G9 horizon is life-event derived and appears in no code, test or commit text.
HORIZON = '2001-01-01T00:00:00+00:00,2051-01-01T00:00:00+00:00'
ARGS = {'classes': 'all', 'final_rules': 'true', 'defer_in_build_verify': 'false', 'horizon': HORIZON, 'result_policy': 'window_qualification/1'}


def load(name):
    path = FLEET / (name + '.py')
    spec = importlib.util.spec_from_file_location('century_' + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CANDIDATE = dict(asset_id=shared.ASSET_ID, scope='per_chart', depends_on=[], natural_key_partition=None, has_cowriters=False)


def century_dispatch_module(monkeypatch):
    import dispatch_v5_century_job as dry
    monkeypatch.setattr(dry.staging, '_load_writer_digest', lambda asset_id: 'd' * 64)        # the generated digest file is CI-owned; the manifest shape is what is under test
    return dry


def test_century_staging_carries_the_three_values_inside_the_manifest_digest(monkeypatch):
    """Claim 3: what the request says is what the manifest (and so plan_manifest_digest) holds, in the writer's canonical form (UTC), and any change of any of the
    three changes the digest — the writer reads them from there because the orchestrator hands it chart_id and birth_params only."""
    dry = century_dispatch_module(monkeypatch)
    writer = shared.writer()
    assert shared.CENTURY_CONFIG_KEY == writer.CENTURY_CONFIG_KEY            # the staged key IS the key the writer reads
    shape = dry.century_shape(classes='all', final_rules='true', defer_in_build_verify='false', horizon='2001-01-01T05:30:00+05:30,2051-01-01T00:00:00+00:00',
                              result_policy='window_qualification/1')
    manifest, digest = dry.build_century_manifest(candidate=CANDIDATE, slice_marker=shape)
    assert manifest[shared.CENTURY_CONFIG_KEY] == dict(schema='gochara_v5_century_config/2', final_rules=True, defer_in_build_verify=False,
                                                        horizon=['2001-01-01T00:00:00+00:00', '2051-01-01T00:00:00+00:00'], result_policy='window_qualification/1')
    assert digest == shared.evidence_digest(manifest) == writer._manifest_digest(manifest)         # the digest the writer verifies on every read
    assert writer.validate_century_config(manifest[shared.CENTURY_CONFIG_KEY]) == manifest[shared.CENTURY_CONFIG_KEY]
    seen = {digest}
    for changed in (dict(final_rules='false'), dict(defer_in_build_verify='true'), dict(horizon='2002-01-01T00:00:00+00:00,2051-01-01T00:00:00+00:00'),
                    dict(result_policy='all_null_candidate/1')):
        other = dry.century_shape(classes='all', **{**dict(final_rules='true', defer_in_build_verify='false', horizon=HORIZON, result_policy='window_qualification/1'), **changed})
        seen.add(dry.build_century_manifest(candidate=CANDIDATE, slice_marker=other)[1])
    assert len(seen) == 5                                                    # OD-1: the policy is covered by the manifest digest like the other three
    plain, plain_digest = dry.build_century_manifest(candidate=CANDIDATE)                 # no shape: the manifest is build_manifest's own, as before
    assert shared.CENTURY_CONFIG_KEY not in plain and plain_digest == shared.evidence_digest(plain)


def test_century_shape_takes_the_four_values_together_or_not_at_all(monkeypatch):
    dry = century_dispatch_module(monkeypatch)
    with pytest.raises(shared.Refused, match='together'):
        dry.century_shape(classes='all', final_rules='true')
    with pytest.raises(shared.Refused, match='together'):                   # OD-1: a century config without its result_policy is not staged
        dry.century_shape(classes='all', final_rules='true', defer_in_build_verify='false', horizon=HORIZON)
    with pytest.raises(shared.Refused):
        dry.century_shape(classes='all', final_rules='true', defer_in_build_verify='false', horizon='2051-01-01T00:00:00+00:00,2001-01-01T00:00:00+00:00',
                          result_policy='window_qualification/1')
    with pytest.raises(shared.Refused):                                     # inside the form but outside the writer's substrate domain: the WRITER's validator refuses
        dry.century_shape(classes='all', final_rules='true', defer_in_build_verify='false', horizon='1900-01-01T00:00:00+00:00,2051-01-01T00:00:00+00:00',
                          result_policy='window_qualification/1')
    with pytest.raises(shared.Refused):                                     # a policy the writer does not know is refused by the WRITER's validator
        dry.century_shape(classes='all', final_rules='true', defer_in_build_verify='false', horizon=HORIZON, result_policy='all_null')


def test_century_launch_stages_and_expects_the_requests_three_values(monkeypatch, tmp_path):
    """Claim 4: the launcher hands the staging binding the three values and expects, from the staged run, the manifest that carries them."""
    dry = century_dispatch_module(monkeypatch)
    century_launch = load('century_launch')
    staging_argv, expected = [], []

    class Dispatcher:
        century_shape = staticmethod(dry.century_shape)
        build_century_manifest = staticmethod(dry.build_century_manifest)
        _load_inactive_candidate = staticmethod(lambda cur: CANDIDATE)

        @staticmethod
        def main(argv):
            staging_argv.extend(argv)
            print(S.RUN)

    class Conn:
        def execute(self, *a): return None
        def cursor(self): return None
        def rollback(self): return None
        def close(self): return None

    monkeypatch.setattr(century_launch.bridge, 'launch_staged', lambda **kw: expected.append(kw['expected_manifest']) or {'status': 'LAUNCHED'})
    century_launch.run(['--classes', 'all', '--final_rules', 'true', '--defer_in_build_verify', 'true', '--horizon', HORIZON, '--result_policy', 'window_qualification/1'],
                       dispatcher=Dispatcher, connect=Conn, claim_dir=tmp_path)
    assert staging_argv[-8:] == ['--final_rules', 'true', '--defer_in_build_verify', 'true', '--horizon', HORIZON, '--result_policy', 'window_qualification/1']
    assert expected[0][shared.CENTURY_CONFIG_KEY]['defer_in_build_verify'] is True and expected[0][shared.CENTURY_CONFIG_KEY]['final_rules'] is True
    assert expected[0][shared.CENTURY_CONFIG_KEY]['result_policy'] == 'window_qualification/1'
    for missing in ('--final_rules', '--defer_in_build_verify', '--horizon', '--result_policy'):        # all four are required: a launch without one would stage a run the writer refuses
        argv = ['--classes', 'all', '--final_rules', 'true', '--defer_in_build_verify', 'false', '--horizon', HORIZON, '--result_policy', 'window_qualification/1']
        at = argv.index(missing)
        with pytest.raises(SystemExit):
            century_launch.run(argv[:at] + argv[at + 2:], dispatcher=Dispatcher, connect=Conn)


def test_century_dispatch_refuses_cli_values_that_differ_from_the_accepted_request(monkeypatch):
    """Claim 5: --final_rules/--defer_in_build_verify/--horizon must equal the bound request's args, exactly as --classes always had to."""
    dry = century_dispatch_module(monkeypatch)
    monkeypatch.setattr(shared, 'operation_request', lambda: dict(kind='century_dispatch_dryrun', args=dict(ARGS)))
    monkeypatch.setattr(shared, 'century_request_problem', lambda req, root, measure=None: None)
    monkeypatch.setattr(shared, 'evidence_root', lambda: Path('.'))
    base = ['--i-am-steward', '--after-settled-1', '--dry-run', '--classes', 'all']
    other = ARGS['horizon'].replace('2001', '2002')
    qual = ['--result_policy', 'window_qualification/1']
    for changed in (['--final_rules', 'false', '--defer_in_build_verify', 'false', '--horizon', HORIZON, *qual],
                    ['--final_rules', 'true', '--defer_in_build_verify', 'true', '--horizon', HORIZON, *qual],
                    ['--final_rules', 'true', '--defer_in_build_verify', 'false', '--horizon', other, *qual],
                    ['--final_rules', 'true', '--defer_in_build_verify', 'false', '--horizon', HORIZON, '--result_policy', 'all_null_candidate/1']):        # OD-1
        with pytest.raises(shared.Refused, match='differ from the accepted request'):
            dry.main(base + changed)
