"""E6.3: the FAMILY_ASSETS.json generator round trip.

(1) ALWAYS runs: an embedded input + embedded registry seed must generate EXACTLY the embedded expected file (byte for
byte), including `_notes`/`_why` carried through and an inactive member allowed by `_notes.inactive`.
(2) The committed pair (00_ARCHITECTURE/control/family_lists_input.json -> FAMILY_ASSETS.json) is checked byte-for-byte
when BOTH files exist on this checkout; the family PR (#2888, suvarna/engine-E6.3-family) carries them. Where FAMILY_ASSETS.json
is absent the test is SKIPPED with that reason (it never passes silently); once the family PR is merged the skip is gone."""
import importlib.util
import json
import pathlib

import pytest

REPO = pathlib.Path(__file__).resolve().parents[4]
CTRL = REPO / "00_ARCHITECTURE" / "control"
SEED_FILE = REPO / "platform" / "scripts" / "seed" / "asset_registry_seed.ts"

_spec = importlib.util.spec_from_file_location("generate_level_map_rt", CTRL / "generate_level_map.py")
G = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(G)

SEED = "export const ASSETS: AssetDef[] = [\n  { asset_id: 'ka_a', layer: 'kala', depends_on: [], is_active: true },\n  { asset_id: 'ka_b', layer: 'kala', depends_on: ['ka_a'], is_active: true },\n  { asset_id: 'ka_old', layer: 'kala', depends_on: [], is_active: false },\n  { asset_id: 'ph_r', layer: 'phala', depends_on: ['ka_b'], is_active: true },\n]\nexport const COEFFICIENTS = []\n"
INPUT = {
    "family_gochara": [
        "ka_old",
        "ka_a"
    ],
    "family_sangam": [
        "ka_b"
    ],
    "family_kshetra": [],
    "family_readers_L3": [],
    "family_readers_L4": [
        "ph_r"
    ],
    "family_readers_L5": [],
    "_notes": {
        "inactive": [
            {
                "asset": "ka_old",
                "reason": "retired sweep"
            }
        ]
    },
    "_why": {
        "ka_old": "name pattern"
    }
}
EXPECTED = '{\n  "version": "0.1-draft",\n  "frozen_at": "2026-10-02T00:00:00+00:00",\n  "registry_revision": 7,\n  "family_gochara": [\n    "ka_a",\n    "ka_old"\n  ],\n  "family_sangam": [\n    "ka_b"\n  ],\n  "family_kshetra": [],\n  "family_readers_L3": [],\n  "family_readers_L4": [\n    "ph_r"\n  ],\n  "family_readers_L5": [],\n  "family_set": [\n    "ka_a",\n    "ka_b",\n    "ka_old",\n    "ph_r"\n  ],\n  "_notes": {\n    "inactive": [\n      {\n        "asset": "ka_old",\n        "reason": "retired sweep"\n      }\n    ]\n  },\n  "_why": {\n    "ka_old": "name pattern"\n  }\n}\n'


def _rows(text):
    return G.validate_registry([{k: v for k, v in r.items() if k != "asset_kind"} for r in G.parse_seed_text(text)])


def test_embedded_input_generates_exactly_the_embedded_file():
    doc = G.build_family_assets(INPUT, _rows(SEED), version="0.1-draft", frozen_at="2026-10-02T00:00:00+00:00",
                                registry_revision=7)
    assert json.dumps(doc, indent=2, ensure_ascii=False) + "\n" == EXPECTED


def test_the_generated_file_is_a_fixed_point_of_the_generator():
    again = G.build_family_assets(json.loads(EXPECTED), _rows(SEED), version="0.1-draft",
                                  frozen_at="2026-10-02T00:00:00+00:00", registry_revision=7)
    assert json.dumps(again, indent=2, ensure_ascii=False) + "\n" == EXPECTED


def test_an_unrecorded_inactive_member_is_refused_in_the_embedded_case():
    bad = dict(INPUT, _notes={"inactive": []})
    with pytest.raises(G.LevelMapError):
        G.build_family_assets(bad, _rows(SEED), version="0.1-draft", frozen_at="2026-10-02T00:00:00+00:00", registry_revision=7)


def test_the_committed_family_file_is_byte_identical_to_the_generator_output_when_present():
    committed, inp = CTRL / "FAMILY_ASSETS.json", CTRL / "family_lists_input.json"
    if not committed.exists() or not inp.exists():
        pytest.skip("FAMILY_ASSETS.json is not on this checkout (it lands with the family PR #2888): round trip of the "
                    "committed pair not run")
    cur = json.loads(committed.read_text(encoding="utf-8"))
    # the registry is the committed draft registry input (the live active registry, see regenerate_draft_level_map.py; the seed
    # is a stale stand-in that still holds ka_gochara_v3_century_materialize active), and the draft stamp is a generator note
    reg = CTRL / "registry_input_draft.json"
    if not reg.exists():
        pytest.skip("registry_input_draft.json is not on this checkout")
    notes = {"_stamp": cur["_stamp"]} if "_stamp" in cur else None
    doc = G.build_family_assets(G.load_family_input(inp), G.load_registry_json(reg), version=cur["version"],
                                frozen_at=cur["frozen_at"], registry_revision=cur["registry_revision"], notes=notes)
    assert json.dumps(doc, indent=2, ensure_ascii=False) + "\n" == committed.read_text(encoding="utf-8")
