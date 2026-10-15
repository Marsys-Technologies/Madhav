"""P09 positive integration oracle: actual approval-bound seal flow and HTTP read."""
from services.gochara_kernel import seal_flow
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


