#!/usr/bin/env python3
"""Build harness/SANDBOX_MANIFEST.json from .sandbox/copy_report.tsv + schema.sql."""
import json, hashlib, datetime, pathlib

SB = pathlib.Path(__file__).resolve().parents[1] / ".sandbox"
OUT = pathlib.Path(__file__).resolve().parents[1] / "harness" / "SANDBOX_MANIFEST.json"

ddl_sha = hashlib.sha256((SB / "schema.sql").read_bytes()).hexdigest()
tables = []
for line in (SB / "copy_report.tsv").read_text().splitlines():
    t, rule, pc, sc = line.split("\t")
    tables.append({
        "table": t, "rule": rule,
        "rows_production": None if pc in ("view", "COPY_FAIL") or pc == "view" else int(pc) if pc.isdigit() else pc,
        "rows_sandbox": sc if sc == "COPY_FAIL" else int(sc),
        "sampled_5pct": rule == "sample5pct_ctidhash",
    })
manifest = {
    "generated": datetime.datetime.now(datetime.UTC).isoformat(),
    "ddl_sha256": ddl_sha,
    "sampling_rule": "abs(hashtext(ctid::text)) % 20 = 0  (deterministic 5%)",
    "fk_enforcement": "disabled in sandbox via ALTER DATABASE … SET session_replication_role=replica (constraints remain defined for pg_constraint reads)",
    "source": "production via read-only proxy (PGPORT 5433, default_transaction_read_only=on)",
    "sandbox": {"host": "unix socket .sandbox", "port": 54329, "db": "nikasha_sandbox", "user": "sandbox"},
    "tables": tables,
}
OUT.write_text(json.dumps(manifest, indent=1))
fails = [t["table"] for t in tables if t["rows_sandbox"] == "COPY_FAIL"]
print(f"manifest: {len(tables)} tables, {len(fails)} COPY_FAIL", fails or "")
