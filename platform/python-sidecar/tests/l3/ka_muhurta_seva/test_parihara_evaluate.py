"""Route contract and the actual main.py guarded mount, without loading .env."""
import ast
from pathlib import Path

from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.testclient import TestClient
import pytest
import psycopg

from routers import parihara_evaluate as route


@pytest.fixture
def client(monkeypatch):
    # Execute main.py's actual verify function + this router's include line.
    # Importing the entire legacy main loads dotenv and unrelated retired routes.
    main = Path(__file__).resolve().parents[3] / "main.py"
    tree = ast.parse(main.read_text())
    verify = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name=="verify_api_key")
    mounts = [n for n in tree.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)
              and ast.unparse(n.value.func)=="app.include_router" and n.value.args
              and ast.unparse(n.value.args[0])=="parihara_evaluate_router.router"]
    assert len(mounts)==1, "main must mount the real route exactly once"
    app=FastAPI()
    namespace=dict(app=app,API_KEY="synthetic-test-key",Header=Header,HTTPException=HTTPException,
                   Depends=Depends,parihara_evaluate_router=route)
    exec(compile(ast.Module(body=[verify,*mounts],type_ignores=[]),str(main),"exec"),namespace)
    class Connection:
        def __enter__(self): return self
        def __exit__(self,*args): pass
    monkeypatch.setattr(route,"_connect",lambda:Connection())
    monkeypatch.setattr(route,"load_rules",lambda conn,undertaking,dosas:[])
    return TestClient(app)


@pytest.mark.parametrize("headers", [{},{"X-API-Key":"wrong"}])
def test_main_mount_refuses_missing_or_wrong_key_before_db(client,monkeypatch,request_data,headers):
    monkeypatch.setattr(route,"_connect",lambda:pytest.fail("unauthenticated DB access"))
    assert client.post("/api/compute/parihara_evaluate",json=request_data,headers=headers).status_code==401


def test_valid_request_roundtrips_caller_and_reference_origin(client,request_data,sky):
    sky()
    for basis in ("caller","lattice_reference_location"):
        request_data["location_basis"]=basis
        response=client.post("/api/compute/parihara_evaluate",json=request_data,headers={"X-API-Key":"synthetic-test-key"})
        assert response.status_code==200,response.text
        out=response.json()
        assert out["location"]==request_data["location"] and out["location_basis"]==basis
        assert out["dosas"][0]["reason"]=="no_sourced_rule_in_scope"
        sky()


@pytest.mark.parametrize("patch", [
    {"location":None}, {"location":{"lat":91,"lon":0,"tz_offset_minutes":0}},
    {"location":{"lat":20.27,"lon":85.84}},
    {"location":{"lat":20.27,"lon":85.84,"tz_offset_minutes":330.5}},
    {"candidate":{"start_utc":"2026-10-15T06:00:00","end_utc":"2026-10-15T07:00:00Z"}},
    {"candidate":{"start_utc":"2026-10-15T06:00:00Z","end_utc":"2026-10-15T06:00:00Z"}},
    {"candidate":{"start_utc":"2026-10-15T08:00:00+02:00","end_utc":"2026-10-15T09:00:00+02:00"}},
    {"location_basis":"lattice_reference_location","location":{"lat":0,"lon":0,"tz_offset_minutes":0}},
    {"dosas_present":["*"]}, {"undertaking":""},
])
def test_invalid_inputs_refused_before_db(client,monkeypatch,request_data,patch):
    request_data.update(patch)
    monkeypatch.setattr(route,"_connect",lambda:pytest.fail("invalid request reached DB"))
    response=client.post("/api/compute/parihara_evaluate",json=request_data,headers={"X-API-Key":"synthetic-test-key"})
    assert response.status_code==422,response.text
    if patch.get("location","present") is None:
        assert response.json()["detail"]["reason"]=="location_missing"


def test_schema_or_db_error_refuses_instead_of_empty_residual(client,monkeypatch,request_data):
    def fail(*args): raise psycopg.errors.UndefinedColumn("private details must not be served")
    monkeypatch.setattr(route,"load_rules",fail)
    response=client.post("/api/compute/parihara_evaluate",json=request_data,headers={"X-API-Key":"synthetic-test-key"})
    assert response.status_code==503
    assert response.json()["detail"]=={"reason":"parihara_source_unavailable"}


def test_ci_runs_the_entire_evaluator_directory_in_required_db_job():
    import yaml
    repo=Path(__file__).resolve().parents[5]
    job=yaml.safe_load((repo/".github/workflows/ci.yml").read_text())["jobs"]["kala-db-tests"]
    steps=[s for s in job["steps"] if "pytest" in str(s.get("run","")) and "tests/l3/ka_muhurta_seva" in s["run"]]
    assert len(steps)==1
    assert str(steps[0]["env"]["KALA_REQUIRE_DB"])=="1"
    run=steps[0]["run"]
    assert not any(token in run.split()[run.split().index("pytest")+1:] for token in ("-k","-m","--deselect","--ignore","||",";","|"))
    assert "postgres" in job["services"]
    assert job["needs"]=="changes" and "!cancelled()" in str(job["if"])
    assert "needs.changes.outputs.docs_only != 'true'" in str(job["if"])
    assert steps[0]["env"]["KALA_ADMIN_DSN"]
    assert not steps[0].get("continue-on-error") and not job.get("continue-on-error")
