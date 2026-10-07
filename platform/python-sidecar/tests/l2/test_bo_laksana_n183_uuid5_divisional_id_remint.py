"""N-183 (Strategic Suvarna ruling): the one-time bo_laksana signal-id re-mint that
follows from deterministic uuid5 `chart_divisionals.id` is ACCEPTED, and documented here.

Why the re-mint is accepted
---------------------------
S-L1 TI-l1-deterministic-row-ids-001 (PR #3213) makes `chart_divisionals.id` a UUID5 over
the table's natural key. ga_structural copies that id into the L1 fact value as
`constituent_fact_id` (vargottama_per_varga / graha_vargottama_amplification_factor).

bo_laksana's B1 strip (`_strip_random_row_ids`, `_UUID_V4_RE`) removes ONLY uuid-v4
values. A uuid5 divisional id is therefore NOT stripped: it stays in the signal
configuration_jsonb, and `signal_id = bodha_signal_identity(chart, ayanamsha,
signal_type_id, varga_id, configuration_jsonb)` hashes that config. So the first
bo_laksana run after the L1 pass (ga_vargas + ga_structural rebuilt with uuid5 ids)
mints new signal ids for the affected signals ONCE -- v4 id in the old config, v5 id in
the new one -- inside the pass's own L2 run. From then on the id is a pure function of the
natural key, so every later L1 rebuild yields the same uuid5, the same config, and the
same signal_id. The churn that DIVID-001 / B1 existed to stop (a fresh random id per L1
rebuild => fresh signal ids per rebuild) is gone for good; what remains is a single
transition, which the ruling accepts rather than widening the strip (the strip is NOT
changed, and bo_laksana stays frozen).

What these tests pin (so the ruling cannot silently drift):
  1. a uuid5 divisional id inside `constituent_fact_id` IS kept in the signal config
     (and is not stripped by `_strip_random_row_ids`);
  2. the resulting signal_id is STABLE across two builds with identical inputs (here: the
     uuid5 is derived from the same natural key twice, as two successive L1 rebuilds do);
  3. a uuid4 `constituent_fact_id` is still stripped (existing B1 behaviour, unchanged),
     so the pre-pass (v4) and post-pass (v5) configs differ -- that difference IS the
     one-time re-mint.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest

from ga_writers._deterministic_ids import divisional_row_id
from pipeline.orchestrator.writers import bo_laksana as bo
from tests.pg_disposable import HAVE_PG, PG_SKIP_REASON, new_db, pg, psql  # noqa: F401

_NOW = "2026-10-05T00:00:00+00:00"
_CHART = "482012f1-710e-4a25-994a-93821f5871aa"
_AYA = "lahiri_chitrapaksha"
_GRAHAS = ("SUN", "MOON", "MAR", "MER", "JUP", "VEN", "SAT")
_VARGAS = ("D9", "D10", "D12", "D108")


def _natural_key_id(varga: str, graha: str) -> str:
    """The L1 deterministic divisional id for one (varga, graha), derived from its key."""
    return divisional_row_id(_CHART, graha, _AYA, varga, "varga_vargottama_flag",
                             "vargottama", f"{varga}_{graha}")


def _vargottama_fact(varga: str, graha: str, rowid: str) -> dict:
    return {
        "fact_id": f"fid-{varga}-{graha}",
        "fact_category": "vargottama_per_varga",
        "fact_key": "is_vargottama",
        "fact_subject": f"{varga}_{graha}",
        "fact_value_text": "not_vargottama",
        "fact_value_num": 0.0,
        "ayanamsha_id": _AYA,
        "source_calculation": "chart_divisionals.varga_vargottama_flag/pyjhora/1.0.0",
        "fact_value_jsonb": {"varga": varga, "varga_sign": "Pisces", "ayanamsha_id": _AYA,
                             "uncatalogued": False, "constituent_fact_id": rowid},
    }


def _build(fact: dict) -> dict:
    return bo._build_signal_row(fact, _CHART, "b1", {}, {}, {}, _NOW,
                                valid_fact_ids={fact["fact_id"]})


def _population(rowid_for) -> list[dict]:
    return [_vargottama_fact(v, g, rowid_for(v, g)) for v in _VARGAS for g in _GRAHAS]


def test_n183_uuid5_divisional_id_is_kept_in_signal_config_not_stripped():
    rid = _natural_key_id("D9", "MAR")
    assert uuid.UUID(rid).version == 5
    # the strip itself is a no-op for a uuid5 (it only removes uuid4)
    assert bo._strip_random_row_ids({"constituent_fact_id": rid}) == {"constituent_fact_id": rid}
    cfg = json.loads(_build(_vargottama_fact("D9", "MAR", rid))["configuration_jsonb"])
    assert cfg["constituent_fact_id"] == rid          # kept: this is what causes the re-mint
    assert cfg["fact_subject"] == "D9_MAR"            # natural key still carried (LAKSANA-COLLISION)


def test_n183_uuid4_divisional_id_is_still_stripped_existing_b1_behaviour():
    rid4 = str(uuid.uuid4())
    cfg = json.loads(_build(_vargottama_fact("D9", "MAR", rid4))["configuration_jsonb"])
    assert "constituent_fact_id" not in cfg
    assert rid4 not in json.dumps(cfg)


def test_n183_one_time_remint_pre_pass_v4_config_differs_from_post_pass_v5_config():
    """The accepted transition: same logical fact, v4 id (pre-pass) vs v5 id (post-pass)
    => different configuration_jsonb => different signal_id, exactly once."""
    pre = _build(_vargottama_fact("D9", "MAR", str(uuid.uuid4())))
    post = _build(_vargottama_fact("D9", "MAR", _natural_key_id("D9", "MAR")))
    assert pre["configuration_jsonb"] != post["configuration_jsonb"]


def test_n183_post_pass_configs_identical_across_two_l1_rebuilds_and_all_distinct():
    run1 = [_build(f) for f in _population(_natural_key_id)]
    run2 = [_build(f) for f in _population(_natural_key_id)]   # a second L1 rebuild
    assert [r["configuration_jsonb"] for r in run1] == [r["configuration_jsonb"] for r in run2]
    keys = {(r["signal_type_id"], r["varga_id"], r["configuration_jsonb"]) for r in run1}
    assert len(keys) == len(run1)                              # no collapse onto one signal


# ── signal_id stability through the REAL identity function (disposable PostgreSQL) ──
_MIG_661 = Path(__file__).resolve().parents[3] / "migrations" / "661_l2_bodha_signal_identity.sql"


def _identity_function_sql() -> str:
    text = _MIG_661.read_text()
    start = text.index("CREATE OR REPLACE FUNCTION bodha_signal_identity_namespace()")
    end = text.index("COMMENT ON FUNCTION bodha_signal_identity(")
    return text[start:end]


def test_n183_signal_id_stable_across_two_builds_with_uuid5_divisional_ids(pg):  # noqa: F811
    if not HAVE_PG:
        pytest.skip(PG_SKIP_REASON)
    import psycopg
    from psycopg.rows import dict_row

    db = new_db(pg)
    r = psql(pg, db, 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    if r.returncode != 0:
        pytest.skip("uuid-ossp extension is not available in this PostgreSQL install")
    assert psql(pg, db, _identity_function_sql()).returncode == 0

    def _run(rowid_for) -> list[str]:
        rows = [_build(f) for f in _population(rowid_for)]
        with psycopg.connect(host="127.0.0.1", port=pg, user="postgres", dbname=db,
                             row_factory=dict_row) as conn:
            assert bo.assign_deterministic_signal_ids(conn, rows) == 0   # no collapse
        return [r["signal_id"] for r in rows]

    v5_a, v5_b = _run(_natural_key_id), _run(_natural_key_id)
    assert v5_a == v5_b                       # stable after the one-time re-mint
    assert len(set(v5_a)) == len(v5_a)        # all distinct

    # uuid4 fixtures: stripped, so still stable across builds with fresh random ids ...
    v4_a, v4_b = _run(lambda v, g: str(uuid.uuid4())), _run(lambda v, g: str(uuid.uuid4()))
    assert v4_a == v4_b
    # ... and different from the v5 generation: that difference IS the accepted one-time re-mint.
    assert set(v4_a).isdisjoint(v5_a)
