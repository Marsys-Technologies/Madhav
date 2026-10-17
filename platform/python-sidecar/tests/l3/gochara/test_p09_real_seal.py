"""P09 positive integration oracle: actual approval-bound seal flow and HTTP read."""
import pytest

G8_CENSUS_OPT_OUT_REASON = "exercises approval-bound seal and HTTP readback on the deliberate one-class marriage world, independently of the class census"
pytestmark = pytest.mark.usefixtures("g8_census_opt_out")

from services.gochara_kernel import seal_flow
from services.gochara_kernel import scope_response as sr
from routers import gochara_v5 as route
from .test_a53_inventory import CHART_ID
from .test_a53_p1_support import GEN
from .test_a53_r11_seal_brief import _verified, _brief_as_verifier, _appr, _sealer_stand_ins
from .test_a53_verification_job import built, login, rworld  # noqa: F401
from .test_a53_window_verification_roles import _consistent_sky  # noqa: F401
from .test_a53_window_verification_gate import CLS
from .test_w1_serving_reader import _read

def test_real_approved_seal_is_read_through_reader_and_http_without_request_time_replay(built, monkeypatch):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    w = built
    _verified(w)
    commit = 'p09-reviewed-sealer'
    digest = _brief_as_verifier(w, sealing_commit=commit)['sha256']
    _sealer_stand_ins(w)
    with login(w, 'gochara_sealer') as conn:
        with conn.transaction():
            outcome = seal_flow.seal_with_approval(conn, chart_id=CHART_ID, generation=GEN,
                        approved_digest=digest, **_appr(digest, sealing_commit=commit))
    answer = _read(w, event_classes=[CLS], limit=route.DEFAULT_LIMIT)
    assert answer['seal']['brief_digest'] == digest and answer['seal']['manifest_id'] == outcome['manifest_id']
    assert all(c['coverage']['completeness_basis']['verification_source'] ==
               'seal_bound_immutable_attestation' for c in answer['classes'])
    assert answer['refusal'] is None
    monkeypatch.setattr(route, '_db_url', lambda: w.dsn)
    monkeypatch.setenv('PYTHON_SIDECAR_API_KEY', 'test-key')
    app = FastAPI()
    app.include_router(route.router, prefix='/api/compute')
    response = TestClient(app).post('/api/compute/gochara/v5/windows',
                  json={'chart_id': CHART_ID, 'generation': GEN, 'event_classes': [CLS]}, headers={'x-api-key': 'test-key'})
    assert response.status_code == 200 and response.json() == answer


def test_real_sealed_attestation_rejects_expected_count_drift_without_a_source_pin_proxy(built):
    """v23: a VERIFIED label cannot hide incompatible expected/stored counts."""
    w = built
    _verified(w)
    commit = 'p09-reviewed-sealer'
    digest = _brief_as_verifier(w, sealing_commit=commit)['sha256']
    _sealer_stand_ins(w)
    with login(w, 'gochara_sealer') as conn:
        with conn.transaction():
            seal_flow.seal_with_approval(conn, chart_id=CHART_ID, generation=GEN,
                        approved_digest=digest, **_appr(digest, sealing_commit=commit))
    assert sr._sealed_window_attestation(w.conn, CHART_ID, GEN, CLS) is True
    with w.conn.transaction():
        # Corrupt only this isolated fixture after the real approval/seal path.
        # The production reader must defend against drift even if write guards
        # have been bypassed; no applied migration file is changed.
        w.conn.execute('ALTER TABLE public.ka_gochara_eval_window_verification DISABLE TRIGGER USER')
        w.conn.execute('ALTER TABLE public.ka_gochara_eval_window_verification DROP CONSTRAINT kgewv_verified_total_ck')
        changed = w.conn.execute(
            'UPDATE public.ka_gochara_eval_window_verification SET windows_expected = windows_stored + 1 '
            'WHERE chart_id = %s AND generation = %s AND event_class = %s RETURNING path_id',
            (CHART_ID, GEN, CLS)).fetchall()
        assert changed
        w.conn.execute('ALTER TABLE public.ka_gochara_eval_window_verification ENABLE TRIGGER USER')
    assert sr._sealed_window_attestation(w.conn, CHART_ID, GEN, CLS) is False
    answer = _read(w, event_classes=[CLS])
    assert answer['classes'][0]['completeness'] == 'unverified'
    assert 'sealed_window_attestation_incompatible' in str(answer['classes'][0]['coverage'])


