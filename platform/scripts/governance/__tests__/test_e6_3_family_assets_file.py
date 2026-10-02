"""E6.3: pins 00_ARCHITECTURE/control/FAMILY_ASSETS.json (the file the E5.3 level-wave dispatcher reads from origin/main).

Schema (Track E brief 8): version, frozen_at, registry_revision, the six lists, family_set = their union. Keys prefixed
`_` are notes (`_open_questions` carries the strategist's three membership questions; `_provenance` the sourcing)."""
import json
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[4]
FILE = REPO / "00_ARCHITECTURE/control/FAMILY_ASSETS.json"
SEED = REPO / "platform/scripts/seed/asset_registry_seed.ts"
DIGESTS = REPO / "platform/src/generated/nirmana-writer-digests.json"
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
    assert DOC["family_set"] == sorted(union) and len(DOC["family_set"]) == 25


def test_the_lists_are_exactly_what_the_focus_families_doc_names():
    # the doc's lists plus the strategist's rulings (Q2: ka_yojaka, ka_gochara_v3_century_materialize; ka_moorti_nirnaya)
    assert DOC["family_gochara"] == ["bg_gochara_arcs", "bg_gochara_citation_resolution", "ka_gochara",
                                     "ka_gochara_resonance", "ka_gochara_sweep", "ka_gochara_v3_century_materialize",
                                     "ka_gochara_v4_41_candidate",
                                     "ka_moorti_nirnaya", "ka_vedha_gochara"]
    assert DOC["family_sangam"] == ["ka_sangam", "ka_yojaka"] and DOC["family_kshetra"] == ["ka_kshetra"]
    assert DOC["family_readers_L3"] == ["ka_bhavishya_lekha", "ka_jivana_parva", "ka_kala_darshana", "ka_kalasutra",
                                        "ka_taranga", "ka_tulana", "ka_vighnakara"]
    assert DOC["family_readers_L4"] == ["ph_muhurta", "ph_nimitta", "ph_pratikara"]
    assert DOC["family_readers_L5"] == ["mi_adhilepa", "mi_bhara", "mi_sankalpa"]


def _seed_entries():
    """{asset_id: (layer, is_active)} read from the seed text, entry by entry."""
    out = {}
    text = SEED.read_text(encoding="utf-8")
    region = text[text.index("export const ASSETS"):text.index("export const COEFFICIENTS")]
    for chunk in region.split("asset_id: '")[1:]:
        aid = chunk.split("'", 1)[0]
        layer = re.search(r"layer:\s*'(\w+)'", chunk)
        active = re.search(r"is_active:\s*(true|false)", chunk)
        out[aid] = (layer.group(1), active.group(1) == "true")
    return out


def test_every_member_is_in_the_seed_active_or_carries_a_recorded_inactive_reason():
    seed = _seed_entries()
    inactive = DOC["_notes"]["inactive"]
    for a in DOC["family_set"]:
        assert a in seed, a
        if not seed[a][1]:
            assert any(x.get("asset") == a and x.get("reason") for x in inactive), a
    for x in inactive:
        assert x["asset"] in DOC["family_set"] and x.get("reason")


def test_reader_lists_are_in_their_layer():
    seed = _seed_entries()
    layer = {"L3": "kala", "L4": "phala", "L5": "mimamsa"}
    for k in ("family_readers_L3", "family_readers_L4", "family_readers_L5"):
        for a in DOC[k]:
            assert seed[a][0] == layer[k[-2:]], (k, a)


def test_the_strategist_added_members_say_why_and_ka_kota_chakra_is_not_in_the_set():
    for a in ("ka_yojaka", "ka_gochara_v3_century_materialize", "ka_moorti_nirnaya", "bg_gochara_arcs",
              "bg_gochara_citation_resolution", "ka_gochara_sweep", "ka_gochara_v4_41_candidate"):
        assert a in DOC["family_set"] and DOC["_why"][a], a
    assert "ka_kota_chakra" not in DOC["family_set"]


def test_the_semantics_are_stated_in_the_file():
    assert DOC["_semantics"].startswith("The family set is what the WAVE tool refuses.")
    assert "ONE AT A TIME" in DOC["_semantics"] and "23 bo_*" in DOC["_semantics"]
    assert "does not change who admits its L0 pin (Suvarna, N-71)" in DOC["_semantics"]


def test_none_of_the_23_bo_writers_is_in_the_family_set():
    writers = json.loads(DIGESTS.read_text(encoding="utf-8"))["writers"]
    bo = sorted(k for k in writers if k.startswith("bo_"))
    assert len(bo) == 23
    assert not set(bo) & set(DOC["family_set"])


def test_the_resolved_questions_are_recorded_in_the_file():
    qs = DOC["_resolved_questions"]
    assert len(qs) == 3 and all(isinstance(q, str) and q.startswith(f"Q{i + 1} (ruled):") for i, q in enumerate(qs))


# E5.3's FAMILY_NAME_PATTERN (platform/scripts/governance/suvarna_level_wave.py, branch suvarna/engine-E5.3), copied here
# because that module is not on main yet. Parity: when the E5.3 module is readable (this checkout once it lands, or the
# sibling worktree), the copy must equal its pattern; the pattern stays as the second line of defence.
FAMILY_NAME_PATTERN = re.compile(r"^(ka_gochara|ka_vedha_gochara|gochara_|bg_gochara_|kala_gochara_)")


def test_the_copied_name_pattern_equals_e5_3s_when_readable():
    cand = REPO / "platform/scripts/governance/suvarna_level_wave.py"
    if not cand.exists():
        import pytest
        pytest.skip("suvarna_level_wave.py (E5.3) is not part of this checkout yet: pattern parity not checked here")
    m = re.search(r'^FAMILY_NAME_PATTERN = re\.compile\(r"([^"]+)"\)', cand.read_text(encoding="utf-8"), re.M)
    assert m and m.group(1) == FAMILY_NAME_PATTERN.pattern


def test_every_seed_asset_the_name_pattern_treats_as_family_is_in_the_file():
    seed = _seed_entries()
    matched = sorted(a for a in seed if FAMILY_NAME_PATTERN.match(a))
    assert len(matched) >= 7
    assert not [a for a in matched if a not in DOC["family_set"]], "file and name pattern disagree"
    assert {a for a in matched if not seed[a][1]} <= {x["asset"] for x in DOC["_notes"]["inactive"]}


# ---- round trip: the committed file is exactly what the generator makes from the committed input ----------------------
# The generator (00_ARCHITECTURE/control/generate_level_map.py) lives on suvarna/engine-E6.3 (PR #2891), not in this small PR,
# which carries no machine-local path. Here the round trip runs only where the generator is part of THIS checkout and is
# otherwise SKIPPED with a visible reason; it is a NON-skipping check in the E6.3 branch (test_e6_3_family_file_roundtrip.py),
# which compares this very pair byte-for-byte as soon as both files are on its checkout.
def _generator():
    import importlib.util
    cand = REPO / "00_ARCHITECTURE/control/generate_level_map.py"
    if not cand.exists():
        return None
    spec = importlib.util.spec_from_file_location("generate_level_map_roundtrip", cand)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod if hasattr(mod, "family_inactive_allowed") else None


def test_the_committed_file_is_byte_identical_to_what_the_generator_makes_from_the_committed_input():
    g = _generator()
    if g is None:
        import pytest
        pytest.skip("generate_level_map.py is not part of this checkout (it lands with the E6.3 PR #2891, whose "
                    "test_e6_3_family_file_roundtrip.py then checks this pair): round trip not run here")
    rows = g.load_registry_from_seed(SEED)
    inp = g.load_family_input(REPO / "00_ARCHITECTURE/control/family_lists_input.json")
    doc = g.build_family_assets(inp, rows, version=DOC["version"], frozen_at=DOC["frozen_at"],
                                registry_revision=DOC["registry_revision"])
    assert json.dumps(doc, indent=2, ensure_ascii=False) + "\n" == FILE.read_text(encoding="utf-8")
