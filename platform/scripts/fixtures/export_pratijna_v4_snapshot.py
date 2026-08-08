#!/usr/bin/env python3
"""
export_pratijna_v4_snapshot.py — PRATIJÑĀ v4 Lane B3: real-data snapshot
fixture refresh procedure.

Regenerates `platform/python-sidecar/tests/fixtures/pratijna_v4_snapshot/`
— the CI-tier fixture that lets `chart_reader_v4.ChartReaderV4` and
`bo_pratijna_v4_engine.PratijnaV4Engine` run for real, against a real
(frozen, versioned) export of chart 482012f1's own facts, inside an
ephemeral CI Postgres with no network access to the production database.

── What this exports, and why exactly this set ────────────────────────────
`ChartReaderV4` (Lane B1) touches exactly five tables: `chart_divisionals`,
`chart_facts`, `chart_fact_identity`, `reference_planets` (global, no
chart_id), and — only via a FOREIGN KEY, never a query of its own —
`charts` (chart_divisionals.chart_id REFERENCES charts.id). Those five are
the fixture's schema. `bo_pratijna_v4_engine.PratijnaV4Engine` and
`bo_pratijna_karyatva.KARYATVA_REGISTRY` never issue their own SQL (R19 —
everything goes through the Reader), so nothing beyond those five tables is
needed to run the full v4 scoring engine (`score_all`) end to end.

Scoped to ONE ayanamsha (`lahiri_chitrapaksha` — the campaign's own
DEFAULT_AYANAMSHA and the only ayanamsha every existing live test in this
campaign scores against) rather than all 5 CANONICAL_AYAS the real writer
loops over: this cuts fixture size roughly 5x (the full 5-ayanamsha export
was ~120MB raw / ~9MB gzip; the 1-ayanamsha export used here is ~25MB raw /
~1.8MB gzip) with zero loss of engine-scoring coverage — every property
test in `test_pratijna_v4_snapshot_properties.py` only ever needs one
ayanamsha's worth of facts to score all 27 event classes. Not a fabrication
of any kind: this is a real subset of a real chart's real L1 facts, not
synthesized or altered data (R19/B.10).

`charts` gets ONE row (the chart_id/birth-metadata row your queries FK
against) with its `client_id -> profiles(id)` foreign key constraint
stripped from the schema dump (see `_strip_client_id_fk` below) — the
fixture never needs a `profiles` table, and keeping that FK would force
exporting an entire unrelated table for a column this fixture always
leaves NULL.

── How to regenerate this fixture (when chart 482012f1's underlying L1
   facts change — e.g. after a Ganita rebuild, a new ayanamsha convention,
   or a schema migration touching any of the 5 source tables) ─────────────

    1. Ensure a live DB connection is available (see
       `PRATIJNA_V4_STATE.md` "DB access" section for the gcloud-secret +
       cloud-sql-proxy resolution recipe — this script reads the same
       `DBURL` env var `chart_reader_v4.py` does).
    2. From the repo root:
           DBURL=... python3 platform/scripts/fixtures/export_pratijna_v4_snapshot.py
    3. This OVERWRITES every file under
       `platform/python-sidecar/tests/fixtures/pratijna_v4_snapshot/` in
       place. Diff before committing — a refresh that silently changes the
       property tests' expected numbers (marriage/separation/childbirth
       occurrence+condition) is itself worth a second look, not just a
       rubber-stamped commit.
    4. Run the CI-tier property test suite locally against the refreshed
       fixture (see that test file's own module docstring for the local
       ephemeral-Postgres recipe) before pushing — a fixture refresh that
       breaks its own test suite must not land silently.

R19: this script only ever SELECTs from the production connection (via
`pg_dump --schema-only` and read-only `COPY ... TO STDOUT`). It never
writes to it.
"""
from __future__ import annotations

import gzip
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURE_DIR = (
    REPO_ROOT
    / "platform"
    / "python-sidecar"
    / "tests"
    / "fixtures"
    / "pratijna_v4_snapshot"
)
DATA_DIR = FIXTURE_DIR / "data"

CHART_ID = "482012f1-710e-4a25-994a-93821f5871aa"
AYANAMSHA = "lahiri_chitrapaksha"

SCHEMA_TABLES = [
    "charts",
    "chart_divisionals",
    "chart_facts",
    "chart_fact_identity",
    "reference_planets",
]

# (output filename, SELECT statement). reference_planets is genuinely
# global (no chart_id column at all — see chart_reader_v4.py's
# `reference_planets()` docstring) so it is exported in full, not
# chart-scoped.
DATA_QUERIES: dict[str, str] = {
    "charts.csv": f"COPY (SELECT * FROM charts WHERE id='{CHART_ID}') TO STDOUT WITH CSV HEADER",
    "chart_divisionals.csv": (
        f"COPY (SELECT * FROM chart_divisionals "
        f"WHERE chart_id='{CHART_ID}' AND ayanamsha_id='{AYANAMSHA}') "
        f"TO STDOUT WITH CSV HEADER"
    ),
    "chart_facts.csv": (
        f"COPY (SELECT * FROM chart_facts "
        f"WHERE chart_id='{CHART_ID}' AND ayanamsha_id='{AYANAMSHA}') "
        f"TO STDOUT WITH CSV HEADER"
    ),
    "chart_fact_identity.csv": (
        # JOINed against the SAME ayanamsha-scoped chart_facts subset —
        # not independently ayanamsha-filtered, because chart_fact_identity
        # has no ayanamsha_id column of its own (identity is 1:1 with
        # fact_id, which IS ayanamsha-specific in chart_facts). Exporting
        # this table without the join would pull identity rows for OTHER
        # ayanamshas' fact_ids, which the restored chart_facts subset would
        # then reject via the fact_id FOREIGN KEY (chart_fact_identity.
        # fact_id REFERENCES chart_facts(fact_id)) — the join keeps the two
        # exports consistent by construction, not by coincidence.
        f"COPY (SELECT cfi.* FROM chart_fact_identity cfi "
        f"JOIN chart_facts cf ON cf.fact_id = cfi.fact_id "
        f"WHERE cfi.chart_id='{CHART_ID}' AND cf.ayanamsha_id='{AYANAMSHA}') "
        f"TO STDOUT WITH CSV HEADER"
    ),
    "reference_planets.csv": "COPY (SELECT * FROM reference_planets) TO STDOUT WITH CSV HEADER",
}


def get_dburl() -> str:
    url = os.environ.get("DBURL")
    if not url:
        raise SystemExit(
            "DBURL not set — see PRATIJNA_V4_STATE.md 'DB access' section for the "
            "gcloud-secret + cloud-sql-proxy resolution recipe."
        )
    return url


def _strip_client_id_fk(schema_sql: str) -> str:
    """Remove the `charts.client_id -> profiles(id)` FK constraint block.
    `profiles` is not part of this fixture's table set (this fixture never
    populates `client_id`), and pg_dump's --table filtering emits FK
    constraints referencing tables outside the requested set regardless of
    whether those tables are also being dumped."""
    marker = "-- Name: charts charts_client_id_fkey"
    if marker not in schema_sql:
        return schema_sql
    start = schema_sql.index(marker)
    block_start = schema_sql.rfind("--\n--", 0, start)
    if block_start == -1:
        block_start = start
    end = schema_sql.index("ON DELETE CASCADE;", start) + len("ON DELETE CASCADE;")
    end = schema_sql.index("\n", end) + 1
    return schema_sql[:block_start] + schema_sql[end:]


def _strip_rls_policies(schema_sql: str) -> str:
    """Remove every `CREATE POLICY` / `ENABLE ROW LEVEL SECURITY` block.
    Production's `charts` table carries a `chart_grant_policy` RLS policy
    referencing `public.chart_grants` — a table outside this fixture's
    scope, so the policy's own CREATE POLICY statement fails to restore
    (its USING clause queries a table that doesn't exist here). RLS
    policies are an access-control concern; every consumer of this
    fixture (ChartReaderV4, PratijnaV4Engine, and this suite's tests)
    connects as the ephemeral CI Postgres's superuser, which bypasses RLS
    entirely regardless of whether any policy is defined — so dropping
    these statements changes nothing about what the tests can observe,
    only removes restore-time noise for a subsystem (chart_grants-based
    access control) this fixture was never scoped to exercise."""
    lines = schema_sql.splitlines(keepends=True)
    out: list[str] = []
    skip_block = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if "Type: POLICY" in line or "Type: ROW SECURITY" in line:
            # Walk back over the preceding "--\n--\n" header pair already
            # appended to `out`, then skip forward to the statement's
            # terminating semicolon (policy/ALTER TABLE statements here are
            # always single-statement, semicolon-terminated). The header
            # comment line ITSELF often contains a literal ';' (e.g.
            # "Schema: public; Owner: -"), so the semicolon search must
            # skip past the "--"-prefixed comment lines (this header line
            # plus its closing "--" line) and any blank separator line
            # before it starts looking for the real statement's terminator
            # — otherwise it stops on the comment's own ';' immediately.
            while out and out[-1].strip() in ("", "--"):
                out.pop()
            j = i
            while j < len(lines) and (
                lines[j].startswith("--") or lines[j].strip() == "" or ";" not in lines[j]
            ):
                j += 1
            i = j + 1
            continue
        out.append(line)
        i += 1
    return "".join(out)


def _strip_restrict_directives(schema_sql: str) -> str:
    """Remove `\\restrict` / `\\unrestrict` meta-commands. These are a psql
    dump/restore-pairing safety feature that only exists in newer psql
    client versions; an older `psql` (e.g. the one CI's `ubuntu-latest`
    runner installs via apt, or the ephemeral Postgres image's bundled
    client) rejects an unrecognized backslash command outright under
    `-v ON_ERROR_STOP=1`. Dropping both lines changes nothing about the
    schema itself — they are a client-side guard against restoring a dump
    fragment out of order, not part of the DDL — and keeps the fixture
    restorable across psql versions rather than pinned to whatever
    version happened to produce the export."""
    lines = [
        ln for ln in schema_sql.splitlines(keepends=True)
        if not ln.startswith("\\restrict") and not ln.startswith("\\unrestrict")
    ]
    return "".join(lines)


def export_schema(dburl: str) -> None:
    args = ["pg_dump", dburl, "--schema-only", "--no-owner", "--no-privileges"]
    for t in SCHEMA_TABLES:
        args += [f"--table={t}"]
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f"pg_dump schema export failed:\n{result.stderr}")
    schema_sql = _strip_restrict_directives(result.stdout)
    schema_sql = _strip_client_id_fk(schema_sql)
    schema_sql = _strip_rls_policies(schema_sql)
    (FIXTURE_DIR / "schema.sql").write_text(schema_sql)
    print(f"wrote {FIXTURE_DIR / 'schema.sql'} ({len(schema_sql)} bytes)")


def export_data(dburl: str) -> None:
    """Exports each table straight to gzip (`<name>.csv.gz`) — the fixture
    is committed compressed (~1.8MB total vs. ~25MB raw) so the CI restore
    step (see .github/workflows/ci.yml's `pratijna-v4-fixture-property-
    tests` job) gunzips-then-COPYs, mirroring how `fresh_chart_smoke.yml`
    keeps its own snapshot dumps out of the working tree entirely (that
    workflow re-dumps at CI time instead of committing a fixture at all;
    this fixture is deliberately COMMITTED and versioned instead, per the
    Lane B3 brief's "real-data snapshot fixture, versioned" requirement)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for fname, query in DATA_QUERIES.items():
        out_path = DATA_DIR / (fname + ".gz")
        result = subprocess.run(
            ["psql", dburl, "-c", query], capture_output=True, text=True
        )
        if result.returncode != 0:
            raise SystemExit(f"psql COPY export failed for {fname}:\n{result.stderr}")
        with gzip.open(out_path, "wt") as f:
            f.write(result.stdout)
        n_lines = result.stdout.count("\n") - 1  # minus header
        print(f"wrote {out_path} ({n_lines} rows)")


def main() -> int:
    dburl = get_dburl()
    export_schema(dburl)
    export_data(dburl)
    print(f"\nFixture regenerated under {FIXTURE_DIR}")
    print("Diff before committing — see this script's module docstring, step 3.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
