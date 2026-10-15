"""Load PR #2949's verifier/sealer grant migration, landed as 1378.

The archived 1241 v7 fixture keeps its original pin. The landing changes only migration-number
metadata and diagnostics; its own pin and an exact comparison with the archived bytes guard
against a semantic change. Either file is refused on hash drift.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

M1241_NAME = "1378_gochara_verifier_sealer_inventory_grants.sql"
M1378_SHA256 = "04540a995e849517d03d80835a4dfaae0ee588c081485337d976814e44a70108"
M1241_SHA256 = "a3480710c7498065892965f23d9bee43dc700d4d8f16eb46ac8fb0ee601efefa"
M1241_FIXTURE = (Path(__file__).resolve().parent / "fixtures"
                 / "1241_v7_verifier_sealer_grants.fixture.sql")


def migration_1241_sql(migrations_dir: Path) -> str:
    real = Path(migrations_dir) / M1241_NAME
    path = real if real.exists() else M1241_FIXTURE
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    expected = M1378_SHA256 if real.exists() else M1241_SHA256
    assert digest == expected, (
        f"{path}: sha256 {digest} != pinned grant migration {expected} — the faithful mirror applies "
        "only the reviewed 1241 v7 bytes (PR #2949)")
    if real.exists():
        archived = M1241_FIXTURE.read_bytes()
        assert hashlib.sha256(archived).hexdigest() == M1241_SHA256
        assert raw == archived.replace(b"1241", b"1378"), (
            "1378 must preserve every archived 1241 v7 byte except the migration number")
    return raw.decode()
