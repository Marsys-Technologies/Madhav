"""bo_laksana composes graha names in ONE spelling family (certification blocker
Vocab.alias for bo_laksana / bo_laksana_rerank).

The writer composes a subject graha on three paths (position-class sign-lord /
subject parse, aspect_parashari fact_subject, yoga/dosha inference) from canonical
3-letter codes (`_SIGN_LORD`, `_DOSHA_GROUP_GRAHA`, `_GRAHA_NAME_MAP`).  Those composed
copies in `configuration_jsonb.graha` and `epistemic_jsonb.subject_resolution.resolved_graha`
now carry the Title long form ('Mars'), the family the rest of the row and the Title-only
consumers (bo_karanajala, bo_bimba, bo_upaya, ...) already use.

Pinned here (every positive assertion FAILS on the pre-fix writer):
  * all five composition call sites emit Title names, for all nine grahas;
  * the working `tags['graha']` stays a code (salience/valence lookups key on it), so the
    salience stays stratified;
  * fields forwarded from an L1 jsonb leaf are NOT re-spelled (CLAUDE.md section N.5);
  * an unrecognised token / non-string passes through unchanged (never title-cased);
  * round trip through `to_title` / `norm_graha`, and the census family classifier reads the
    composed leaves as a single `name` family;
  * bo_karanajala's `_graha_from_cfg` resolves all nine grahas from the composed config
    (the pre-fix codes dropped seven of them), and the bo_bimba / bo_laksana_rerank
    extractors accept what the writer produces.

No DB.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from brahmagyan.graha_vocabulary import norm_graha, to_title
from pipeline.orchestrator.writers import bo_laksana as bo
from pipeline.orchestrator.writers import bo_bimba, bo_karanajala

_GOV = Path(__file__).resolve().parents[3] / "scripts" / "governance"
if str(_GOV) not in sys.path:
    sys.path.insert(0, str(_GOV))
import asset_census as census  # noqa: E402

_NOW = "2026-10-10T00:00:00+00:00"
_AYA = "lahiri_chitrapaksha"

# canonical subject code -> Title long form, the nine grahas bo_karanajala knows
_NINE = {
    "SUN": "Sun", "MOON": "Moon", "MAR": "Mars", "MER": "Mercury", "JUP": "Jupiter",
    "VEN": "Venus", "SAT": "Saturn", "RAH_MEAN": "Rahu", "KET_MEAN": "Ketu",
}


def _fact(fid, cat, key, subject, *, text=None, fvj=None, num=None):
    return {
        "fact_id": fid, "fact_category": cat, "fact_key": key, "fact_subject": subject,
        "fact_value_text": text, "fact_value_num": num, "ayanamsha_id": _AYA,
        "source_calculation": "x", "formula_id": None,
        "fact_value_jsonb": json.dumps(fvj) if fvj is not None else None,
    }


def _build(fact):
    row = bo._build_signal_row(
        fact, "chart-1", "b1", {}, {}, {}, _NOW, valid_fact_ids={fact["fact_id"]},
    )
    cfg = json.loads(row["configuration_jsonb"])
    epi = row["epistemic_jsonb"]
    epi = json.loads(epi) if isinstance(epi, str) else epi
    return row, cfg, epi


# ── the three composition paths, one parametrized case per call site and graha ──

_SIGN_OF = {  # sign whose classical lord is the graha (position-class sign_lord rule)
    "SUN": "Leo", "MOON": "Cancer", "MAR": "Aries", "MER": "Gemini",
    "JUP": "Sagittarius", "VEN": "Taurus", "SAT": "Capricorn",
}
_NODE_TEXT = {"RAH_MEAN": "Rahu", "KET_MEAN": "Ketu"}


def _position_sign_lord(code):
    return _fact(f"p-{code}", "special_lagna", "bhava_lagna", "SPECIAL_LAGNA",
                 fvj={"sign": _SIGN_OF[code]})


def _position_karaka_text(code):
    return _fact(f"k-{code}", "karaka_chara_position", "amk", "AMK", text=_NODE_TEXT[code])


def _aspect_given(code):
    return _fact(f"a-{code}", "aspect_parashari_given", "house_7", code)


def _aspect_per_varga(code):
    return _fact(f"v-{code}", "aspect_parashari_per_varga", "house_5", f"D9_{code}",
                 fvj={"varga_id": "D9", "target_house": 5})


def _yoga_fire_reason(code):
    return _fact(f"y-{code}", "yoga_fires", "yoga_name", "SOME_YOGA", text="SOME_YOGA",
                 fvj={"fire_reason": f"{_NINE[code]} in kendra (9) from the lagna"})


def _dosha_group(code):
    group = {"MAR": "mangal", "RAH_MEAN": "kala_sarpa"}[code]
    return _fact(f"d-{code}", "dosha_fires", "dosha_name", "SOME_DOSHA", text="SOME_DOSHA",
                 fvj={"dosha_group": group})


_CASES = (
    [("position_sign_lord", _position_sign_lord, c) for c in _SIGN_OF]
    + [("position_karaka_text", _position_karaka_text, c) for c in _NODE_TEXT]
    + [("aspect_given", _aspect_given, c) for c in _NINE]
    + [("aspect_per_varga", _aspect_per_varga, c) for c in _NINE]
    + [("yoga_fire_reason", _yoga_fire_reason, c) for c in _NINE]
    + [("dosha_group", _dosha_group, c) for c in ("MAR", "RAH_MEAN")]
)


@pytest.mark.parametrize("path,make,code", _CASES, ids=[f"{p}:{c}" for p, _, c in _CASES])
def test_composed_graha_is_title_in_config(path, make, code):
    _, cfg, _ = _build(make(code))
    assert cfg["graha"] == _NINE[code], (path, code, cfg.get("graha"))


@pytest.mark.parametrize("code", list(_SIGN_OF) + list(_NODE_TEXT))
def test_position_class_resolved_graha_is_title_in_epistemic(code):
    make = _position_sign_lord if code in _SIGN_OF else _position_karaka_text
    _, cfg, epi = _build(make(code))
    sr = epi["subject_resolution"]
    assert sr["resolved_graha"] == _NINE[code]
    assert cfg["graha"] == sr["resolved_graha"]


def test_working_tag_stays_a_code_so_salience_lookups_still_key_by_code():
    """tags['graha'] is the lookup key of the strength/dignity maps (keyed by code):
    the composed Title copy must not reach it.  Keyed by code, the lookups are hit and
    the shadbala input is the looked-up value (not the 1.0 miss default)."""
    fact = _position_sign_lord("MAR")
    row = bo._build_signal_row(
        fact, "chart-1", "b1", {"MAR": 3.0}, {"MAR": "own"}, {}, _NOW,
        valid_fact_ids={fact["fact_id"]},
    )
    miss = bo._build_signal_row(
        fact, "chart-1", "b1", {"Mars": 3.0}, {"Mars": "own"}, {}, _NOW,
        valid_fact_ids={fact["fact_id"]},
    )
    # same fact, lookups keyed by code vs by Title: only the code-keyed run is stratified
    assert row["computed_salience"] != miss["computed_salience"]
    # headline keeps the working code (left as is by design)
    assert row["signal_headline_text"].startswith("MAR"), row["signal_headline_text"]


# ── forwarded L1 leaves are never re-spelled (section N.5) ─────────────────────

def test_forwarded_jsonb_leaves_are_not_respelled():
    f = _fact("f1", "yoga_fires", "yoga_name", "SOME_YOGA", text="SOME_YOGA",
              fvj={"graha": "MAR", "primary_graha": "JUP", "lord": "SAT"})
    _, cfg, _ = _build(f)
    assert cfg["graha"] == "MAR"          # the fact's own jsonb leaf, forwarded as is
    assert cfg["primary_graha"] == "JUP"
    assert cfg["lord"] == "SAT"


def test_forwarded_lord_and_primary_graha_on_position_fact_stay_as_l1_spells_them():
    f = _fact("f2", "special_lagna", "x", "SPECIAL_LAGNA",
              fvj={"lord": "MAR", "primary_graha": "VEN"})
    _, cfg, _ = _build(f)
    assert cfg["lord"] == "MAR"
    assert cfg["primary_graha"] == "VEN"


def test_unknown_token_is_left_as_is_never_title_cased():
    _, cfg, _ = _build(_fact("u1", "aspect_parashari_given", "house_3", "XYZ_UNKNOWN"))
    assert cfg["graha"] == "XYZ_UNKNOWN"
    assert bo._compose_graha_name("zzz") == "zzz"
    assert bo._compose_graha_name("") == ""
    assert bo._compose_graha_name(None) is None
    assert bo._compose_graha_name(7) == 7
    assert bo._compose_graha_name(["MAR"]) == ["MAR"]


# ── round trip + census family ─────────────────────────────────────────────────

@pytest.mark.parametrize("code,title", list(_NINE.items()))
def test_round_trip_through_to_title_and_norm_graha(code, title):
    assert bo._compose_graha_name(code) == title
    assert to_title(title) == title
    assert norm_graha(title) == code
    assert bo._compose_graha_name(title) == title      # idempotent
    assert bo._compose_graha_name(title.upper()) == title


def test_composed_leaves_form_a_single_name_family_in_the_census():
    leaves = set()
    for path, make, code in _CASES:
        _, cfg, epi = _build(make(code))
        leaves.add(cfg["graha"])
        sr = (epi or {}).get("subject_resolution") or {}
        if sr.get("resolved_graha"):
            leaves.add(sr["resolved_graha"])
    fams = census.vocab_families(leaves)
    assert fams == frozenset({"name"}), (fams, sorted(leaves))
    # control: a code beside a name is the mixed state the certification flags
    assert census.vocab_families(leaves | {"MAR"}) == frozenset()


# ── consumers: the produced JSON is read by the Title-only and tolerant extractors ──

@pytest.mark.parametrize("code,title", list(_NINE.items()))
def test_karanajala_resolves_every_graha_from_composed_config(code, title):
    _, cfg, _ = _build(_aspect_given(code))
    assert bo_karanajala._graha_from_cfg(cfg) == title


def test_karanajala_old_code_spelling_dropped_seven_of_nine():
    """Documents the defect this fix closes: the old codes resolved for SUN/MOON only."""
    resolved = {c for c in _NINE if bo_karanajala._graha_from_cfg({"graha": c}) is not None}
    assert resolved == {"SUN", "MOON"}


@pytest.mark.parametrize("code,title", list(_NINE.items()))
def test_bimba_and_rerank_extractors_accept_the_produced_json(code, title):
    _, cfg, _ = _build(_aspect_given(code))
    assert bo_bimba._parse_graha_from_signal(cfg) == title
    # rerank folds any spelling to the canonical short code
    assert bo._extract_primary_graha_for_rerank(cfg) == code
