"""Static checks of the DRAFT migration 1219 (SS N-61): ownership row + ga_structural digest-spec revision.

No DB. Proves (a) the embedded spec is migration 914's active spec plus exactly one category, (b) the stored
sha is the real `canonical_digest` of the embedded spec (the same function reproduces 914's sha), (c) the
ownership row and the retire-then-insert guard are present, and (d) the new category is exactly what the
writer emits.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from pipeline.orchestrator.provenance import canonical_digest  # noqa: E402

MIGRATIONS = pathlib.Path(__file__).resolve().parents[2] / "migrations"
M914 = (MIGRATIONS / "914_nirmana_l1_ga_structural_output_digest_spec.sql").read_text(encoding="utf-8")
M1219 = (MIGRATIONS / "1219_nirmana_l1_ga_structural_argala_graha_natal_ownership_and_digest.sql").read_text(encoding="utf-8")

OLD_SHA = "b24906468e53894de0f223c70c9222eb8fbad3933f79ef7dbee7422b8dd709a6"
NEW_SHA = "d480c829b61dcb2a94cc6f47b10d02fe63ae4830a3505f7c5a30c72d6224e620"


def _spec(text: str) -> dict:
    m = re.search(r"'(\{\"version\":\"nirmana-output-digest-spec-v1\".*?\})'::jsonb", text, re.S)
    assert m
    return json.loads(m.group(1))


def test_914_sha_is_reproduced_by_the_real_digest_function():
    assert canonical_digest(_spec(M914)) == OLD_SHA


def test_new_spec_is_the_old_spec_plus_exactly_the_new_category_and_its_sha_is_real():
    old, new = _spec(M914), _spec(M1219)
    old_cats = old["components"][0]["where_in"]["fact_category"]
    new_cats = new["components"][0]["where_in"]["fact_category"]
    assert len(old_cats) == 81 and len(new_cats) == 82
    assert set(new_cats) - set(old_cats) == {"argala_graha_natal"} and set(old_cats) <= set(new_cats)
    assert new_cats == sorted(new_cats)
    old["components"][0]["where_in"]["fact_category"] = new_cats
    assert old == new                                    # nothing else in the spec moved
    assert canonical_digest(new) == NEW_SHA
    assert M1219.count(NEW_SHA) >= 3 and OLD_SHA in M1219


def test_ownership_row_and_guards():
    assert "('argala_graha_natal', 'ga_structural')" in M1219
    assert "ON CONFLICT (fact_category, owning_asset_id) DO NOTHING" in M1219
    assert not re.search(r"UPDATE\s+asset_registry", M1219, re.I)        # count_sql joins the ownership table (410)
    assert "retired_at = now()" in M1219 and "unrecognised active row" in M1219
    assert not re.search(r"^\s*(BEGIN|COMMIT)\s*;", M1219, re.M)         # the runner owns the transaction


def test_the_category_in_the_spec_is_the_one_the_writer_emits():
    import ga_writers.ga_structural_writer as sut
    rows = sut._build_argala_graha_rows(
        {"Mars": {"sign_num": 1}, "Sun": {"sign_num": 2}}, "D1", "c", "b", "a", "t", "e")
    assert {r["fact_category"] for r in rows} == {"argala_graha_natal"}
