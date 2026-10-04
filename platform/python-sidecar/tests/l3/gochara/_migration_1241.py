"""Shared loader for Stream B's migration 1241 (verifier/sealer grants).

1241 is Stream B's, carried by PR #2949 (pravaha/b6-1241-verifier-sealer-grants). Until it lands
on main it must NOT live in platform/migrations on branches that do not own it (protected-window
rule), so the faithful mirror resolves it two ways, always pinned to the same reviewed bytes:

1. if platform/migrations/1241_gochara_verifier_sealer_inventory_grants.sql EXISTS (i.e. the tree
   already carries the real migration), apply it — asserting its sha256 equals the pinned v7 digest;
2. otherwise apply the byte-exact TEST FIXTURE
   tests/l3/gochara/fixtures/1241_v7_verifier_sealer_grants.fixture.sql (same pin).

Either way the applied bytes are exactly migration 1241 v7; anything else is a hard failure.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

M1241_NAME = "1241_gochara_verifier_sealer_inventory_grants.sql"
M1241_SHA256 = "a3480710c7498065892965f23d9bee43dc700d4d8f16eb46ac8fb0ee601efefa"
M1241_FIXTURE = (Path(__file__).resolve().parent / "fixtures"
                 / "1241_v7_verifier_sealer_grants.fixture.sql")


def migration_1241_sql(migrations_dir: Path) -> str:
    real = Path(migrations_dir) / M1241_NAME
    path = real if real.exists() else M1241_FIXTURE
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == M1241_SHA256, (
        f"{path}: sha256 {digest} != pinned 1241 v7 {M1241_SHA256} — the faithful mirror applies "
        "only the reviewed 1241 v7 bytes (PR #2949)")
    return raw.decode()
