"""bo_karanajala arudha nodes: Title-case graha subjects, and a per-chart REPLACE on rebuild.

Defect (SS ruling N-240): graha-keyed arudha_pada facts (ARUDHA_SU..ARUDHA_SA) were written to
bodha_cgm_nodes.node_subject as the raw two-letter L1 code ('SU'), while every other graha-keyed node
(bo_bimba) uses the Title-case vocabulary ('Sun'). And the arudha/special_lagna nodes were inserted
ON CONFLICT DO NOTHING with no delete, so no rebuild could ever clear an old row.

Fake-connection tests always run. The SQL test runs the REAL delete helper on a disposable local
PostgreSQL (tests/pg_disposable.py; skips loudly when no server binaries are present).
"""
from __future__ import annotations

import pathlib
import re
import sys

import pytest

SIDECAR = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SIDECAR))

from pipeline.orchestrator.writers import bo_karanajala as k  # noqa: E402
from tests.pg_disposable import HAVE_PG, PG_SKIP_REASON, new_db, psql, q, pg, requires_pg  # noqa: E402,F401

CHART = "482012f1-710e-4a25-994a-93821f5871aa"
OTHER = "00000000-0000-4000-8000-000000000002"
AYA = "lahiri_chitrapaksha"
GRAHAS = {"SU": "Sun", "MO": "Moon", "MA": "Mars", "ME": "Mercury", "JU": "Jupiter",
          "VE": "Venus", "SA": "Saturn", "RA": "Rahu", "KE": "Ketu"}


class _Rows:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return list(self._rows)


class _FakeFacts:
    """chart_facts read: (fact_id, category, subject, key, text, num)."""

    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, params=None):
        return _Rows(self.rows)


def _facts():
    rows = []
    for i, sub in enumerate([f"ARUDHA_A{n}" for n in range(1, 13)] + [f"ARUDHA_{c}" for c in GRAHAS]):
        rows.append((f"h{i}", "arudha_pada", sub, "house_d1", None, float(i % 12 + 1)))
        rows.append((f"s{i}", "arudha_pada", sub, "sign", "leo", None))
    rows.append(("g1", "special_lagna", "GHATI_LAGNA", "house_d1", None, 3.0))
    return rows


@pytest.mark.parametrize("code,title", sorted(GRAHAS.items()))
def test_graha_keyed_arudha_subject_is_title_case(code, title):
    assert k._arudha_node_subject(f"ARUDHA_{code}") == title


@pytest.mark.parametrize("n", range(1, 13))
def test_house_keyed_arudha_subject_unchanged(n):
    assert k._arudha_node_subject(f"ARUDHA_A{n}") == f"A{n}"


def test_no_arudha_node_subject_is_a_two_letter_code():
    out = k._fetch_arudha_special_lagna_facts(_FakeFacts(_facts()), CHART, AYA)
    arudha = sorted(s for (t, s) in out if t == "arudha")
    assert not [s for s in arudha if len(s) == 2 and not re.fullmatch(r"A\d", s)]
    assert not [s for s in arudha if s in GRAHAS]
    assert {"Sun", "Moon", "Saturn", "Ketu"} <= set(arudha)
    # special_lagna subjects are untouched, and the citation still names the raw L1 fact subject
    assert ("special_lagna", "GHATI_LAGNA") in out
    assert k._arudha_fact_subject("arudha", "Sun") == "SU"
    assert k._arudha_fact_subject("arudha", "A5") == "A5"
    assert k._arudha_fact_subject("special_lagna", "GHATI_LAGNA") == "GHATI_LAGNA"


def test_second_run_yields_identical_subject_set():
    a = k._fetch_arudha_special_lagna_facts(_FakeFacts(_facts()), CHART, AYA)
    b = k._fetch_arudha_special_lagna_facts(_FakeFacts(_facts()), CHART, AYA)
    assert sorted(a) == sorted(b)


def test_delete_runs_before_node_map_read_and_not_in_dry_run():
    src = (SIDECAR / "pipeline/orchestrator/writers/bo_karanajala.py").read_text()
    body = src[src.index("def run(self, ctx: ContextSpec)"):]
    d = body.index("_replace_prior_arudha_special_lagna_nodes(conn, chart_id, aya, SNAPSHOT_TYPE)")
    assert body.rindex("if not ctx.dry_run:", 0, d) > body.index("for aya in CANONICAL_AYAS")
    assert d < body.index("_fetch_node_map(conn, chart_id, aya)")
    assert d < body.index("_build_arudha_special_lagna_nodes_and_edges(")


NODES_DDL = """
CREATE TABLE public.bodha_cgm_nodes (node_id text PRIMARY KEY, chart_id text, ayanamsha_id text,
  snapshot_type text, node_type text, node_subject text);
CREATE TABLE public.bodha_cgm_edges (edge_id text PRIMARY KEY, chart_id text, ayanamsha_id text,
  snapshot_type text, from_node_id text, to_node_id text);
"""


@requires_pg
def test_replace_clears_old_codes_and_their_edges_only_for_this_chart(pg):
    rep = k._replace_prior_arudha_special_lagna_nodes
    import psycopg
    db = new_db(pg)
    assert psql(pg, db, NODES_DDL).returncode == 0
    vals = []
    for chart in (CHART, OTHER):
        for aya in (AYA, "krishnamurti"):
            for typ, sub in [("arudha", "SU"), ("arudha", "A1"), ("special_lagna", "GHATI_LAGNA"),
                             ("graha", "Sun"), ("bhava", "1")]:
                nid = f"{chart[:4]}-{aya[:3]}-{typ}-{sub}"
                vals.append(f"('{nid}','{chart}','{aya}','static_natal','{typ}','{sub}')")
    assert psql(pg, db, "INSERT INTO bodha_cgm_nodes VALUES " + ",".join(vals)).returncode == 0
    ed = []
    for chart in (CHART, OTHER):
        for aya in (AYA, "krishnamurti"):
            p = f"{chart[:4]}-{aya[:3]}"
            ed.append(f"('{p}-e1','{chart}','{aya}','static_natal','{p}-arudha-SU','{p}-bhava-1')")
            ed.append(f"('{p}-e2','{chart}','{aya}','static_natal','{p}-graha-Sun','{p}-bhava-1')")
    assert psql(pg, db, "INSERT INTO bodha_cgm_edges VALUES " + ",".join(ed)).returncode == 0

    with psycopg.connect(host="127.0.0.1", port=pg, user="postgres", dbname=db) as conn:
        n1 = rep(conn, CHART, AYA, "static_natal")
        n2 = rep(conn, CHART, AYA, "static_natal")      # idempotent
    assert (n1, n2) == (3, 0)
    mine = q(pg, db, f"select count(*) from bodha_cgm_nodes where chart_id='{CHART}' and ayanamsha_id='{AYA}'"
                     " and node_type in ('arudha','special_lagna')")
    assert mine == "0"
    # nothing else touched: bimba nodes of this chart/aya, and every row of the other aya / other chart
    assert q(pg, db, f"select count(*) from bodha_cgm_nodes where chart_id='{CHART}' and ayanamsha_id='{AYA}'") == "2"
    assert q(pg, db, "select count(*) from bodha_cgm_nodes") == "17"
    # the edge that pointed at a deleted node is gone (no orphan); the graha edge and other scopes survive
    assert q(pg, db, f"select count(*) from bodha_cgm_edges where chart_id='{CHART}' and ayanamsha_id='{AYA}'") == "1"
    assert q(pg, db, "select count(*) from bodha_cgm_edges") == "7"
    assert q(pg, db, "select count(*) from bodha_cgm_edges e where not exists "
                     "(select 1 from bodha_cgm_nodes n where n.node_id = e.from_node_id)") == "0"
