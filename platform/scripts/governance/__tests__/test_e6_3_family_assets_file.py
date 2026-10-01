"""E6.3: pins 00_ARCHITECTURE/control/FAMILY_ASSETS.json (the file the E5.3 level-wave dispatcher reads from origin/main).

Schema (Track E brief 8): version, frozen_at, registry_revision, the six lists, family_set = their union. Keys prefixed
`_` are notes (`_open_questions` carries the strategist's three membership questions; `_provenance` the sourcing)."""
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[4]
FILE = REPO / "00_ARCHITECTURE/control/FAMILY_ASSETS.json"
SEED = REPO / "platform/scripts/seed/asset_registry_seed.ts"
LISTS = ("family_gochara", "family_sangam", "family_kshetra", "family_readers_L3", "family_readers_L4", "family_readers_L5")
DOC = json.loads(FILE.read_text(encoding="utf-8"))


def test_keys_are_exactly_the_pinned_schema_plus_underscore_notes():
    pinned = ["version", "frozen_at", "registry_revision", *LISTS, "family_set"]
    assert [k for k in DOC if not k.startswith("_")] == pinned
    assert isinstance(DOC["version"], str) and DOC["version"]
    assert isinstance(DOC["registry_revision"], int) and not isinstance(DOC["registry_revision"], bool)
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT[\d:]+(\+00:00|Z|[+-]\d\d:\d\d)", DOC["frozen_at"])


def test_each_list_is_sorted_unique_asset_ids_and_family_set_is_their_union():
    union = set()
    for k in LISTS:
        v = DOC[k]
        assert v == sorted(set(v)) and all(re.fullmatch(r"[a-z][a-z0-9_]*", a) for a in v), k
        union |= set(v)
    assert DOC["family_set"] == sorted(union) and len(DOC["family_set"]) == 18


def test_the_lists_are_exactly_what_the_focus_families_doc_names():
    assert DOC["family_gochara"] == ["ka_gochara", "ka_gochara_resonance", "ka_vedha_gochara"]
    assert DOC["family_sangam"] == ["ka_sangam"] and DOC["family_kshetra"] == ["ka_kshetra"]
    assert DOC["family_readers_L3"] == ["ka_bhavishya_lekha", "ka_jivana_parva", "ka_kala_darshana", "ka_kalasutra",
                                        "ka_taranga", "ka_tulana", "ka_vighnakara"]
    assert DOC["family_readers_L4"] == ["ph_muhurta", "ph_nimitta", "ph_pratikara"]
    assert DOC["family_readers_L5"] == ["mi_adhilepa", "mi_bhara", "mi_sankalpa"]


def test_every_member_is_an_asset_of_the_registry_seed_in_its_layer():
    seed = SEED.read_text(encoding="utf-8")
    for a in DOC["family_set"]:
        m = re.search(r"asset_id:\s*'%s',\s*layer:\s*'(\w+)'" % a, seed)
        assert m, a
    layer = {"L3": "kala", "L4": "phala", "L5": "mimamsa"}
    for k in ("family_readers_L3", "family_readers_L4", "family_readers_L5"):
        for a in DOC[k]:
            assert re.search(r"asset_id:\s*'%s',\s*layer:\s*'%s'" % (a, layer[k[-2:]]), seed), (k, a)


def test_the_open_membership_questions_are_recorded_in_the_file():
    qs = DOC["_open_questions"]
    assert len(qs) == 3 and all(isinstance(q, str) and q.startswith(f"Q{i + 1}:") for i, q in enumerate(qs))
