"""Optional local cross-runtime rehearsal; uses real registered TS handler.

Run with KALA_REQUIRE_DB=1 and the disposable KALA_ADMIN_DSN from the sidecar
directory: python -m tests.l3.kala_db.e2e.registry_rehearsal. The Python/SQL
oracles remain in CI's DB suite; this bridge also needs platform node_modules.
"""
import json
from pathlib import Path
import shutil
import subprocess
import uuid
from urllib.parse import urlsplit

import psycopg

from pipeline.orchestrator.writers.ka_kala_darshana import KaKalaDarshanaWriter
from tests.l3.kala_db.conftest import _assert_kala_disposable_connection
from tests.l3.kala_db.e2e.conftest import REPO
from tests.l3.kala_db.e2e.test_slice import seed, candidate, ctx
from tests.l3.kala_db.idempotency.conftest import _disposable_test_dsn


def run():
    node = shutil.which("node")
    if node is None:
        raise RuntimeError("Node is required for the registry rehearsal")
    admin_dsn = _disposable_test_dsn()
    parsed = urlsplit(admin_dsn)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise RuntimeError("The cross-runtime rehearsal requires a disposable URI DSN")
    name = "kala_ci_" + uuid.uuid4().hex
    with psycopg.connect(admin_dsn, autocommit=True) as admin:
        dbname = admin.execute("SELECT current_database()").fetchone()[0]
        _assert_kala_disposable_connection(admin, dbname, admin_dsn)
        admin.execute(f'CREATE DATABASE "{name}"')
        try:
            dsn = psycopg.conninfo.make_conninfo(admin_dsn, dbname=name)
            with psycopg.connect(dsn) as conn:
                _assert_kala_disposable_connection(conn, name, dsn)
                conn.execute(Path(__file__).with_name("legacy_schema.sql").read_text()
                             .replace("CREATE TEMP TABLE", "CREATE TABLE"))
                conn.execute((REPO / "platform/migrations/1330_kala_layer_manifest_candidates.sql")
                             .read_text().split("-- A separately dispatched verifier")[0])
                conn.execute((REPO / "platform/migrations/1338_kala_assertion_vertical_slice.sql").read_text())
                seed(conn)
                candidate(conn)
                assert KaKalaDarshanaWriter().run(ctx(conn)).rows_inserted == 1
                conn.commit()
            code = """
import './src/lib/retrieval/registry/layers/L3_kala/index';
import {getCapability} from './src/lib/retrieval/registry/index';
import {getPool} from './src/lib/db/client';
(async()=>{try {
  const cap=getCapability('marsys://tool/L3/query_kala_assertion_fixture');
  if(!cap?.handler) throw new Error('fixture capability not registered');
  const result=await cap.handler({chart_id:'00000000-0000-0000-0000-000000000001',generation:'candidate-a'},{} as never);
  console.log(JSON.stringify(result));
} finally {await (await getPool()).end();}})();
"""
            result = subprocess.run([node, str(REPO / "platform/node_modules/tsx/dist/cli.mjs"),
                                     "--conditions=react-server", "-e", code], cwd=REPO / "platform",
                                    env={"PATH": str(Path(node).parent) + ":/usr/bin:/bin",
                                         "DATABASE_URL": parsed._replace(path="/" + name).geturl(),
                                         "KALA_ASSERTION_FIXTURE_ENABLED": "1"},
                                    capture_output=True, text=True, check=True, timeout=30)
            response = json.loads(result.stdout)
            assert response["is_error"] is False
            rows = response["content"]["assertions"]
            assert len(rows) == 1 and rows[0]["candidate_effective_state"] == "obstruction_cancelled"
            assert rows[0]["record_ids"] == ["11"]
            return response
        finally:
            admin.execute(f'DROP DATABASE "{name}"')


if __name__ == "__main__":
    print(json.dumps(run()))
