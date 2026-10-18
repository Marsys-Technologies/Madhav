"""
test_nakshatra_vocabulary_data_frozen.py -- the frozen constants module equals the L0 sources, and the vocabulary is a LEAF.

Engine finding on #3460: brahmagyan.nakshatra_vocabulary imported brahmagyan.l0_ontology (whose seeder calls
conn.commit()), so l0_ontology.py entered the gochara writers' whole-closure no-commit conformance check (§N.2).
The normaliser now reads brahmagyan/nakshatra_vocabulary_data.py, a generated constants-only copy; this test keeps
that copy honest (byte-equal to a fresh derivation from the L0 modules) and keeps the vocabulary's import closure
free of any module that touches a connection.

WHO REGENERATES (CLAUDE.md N.7 item 3): the L0 OWNER, in the same change that edits brahmagyan/l0_nakshatra.py or
brahmagyan/l0_ontology.py, runs `python platform/scripts/governance/freeze_nakshatra_vocabulary_data.py` (and its `--check`)
as part of that change's own tests; until then this test is red -- drift is a failing test, never a silent divergence.
Verified by mutation: one character in the frozen module, one alt_name in l0_nakshatra.py and one synonym in l0_ontology.py
each turn this file red.
"""
from __future__ import annotations

import ast
import pathlib
import subprocess
import sys

SIDECAR = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SIDECAR))

from brahmagyan import nakshatra_vocabulary as voc  # noqa: E402
from brahmagyan import nakshatra_vocabulary_data as data  # noqa: E402
from brahmagyan.l0_nakshatra import NAKSHATRAS_ENRICHED  # noqa: E402
from brahmagyan.l0_ontology import NAK_DATA  # noqa: E402

GENERATOR = SIDECAR.parent / "scripts" / "governance" / "freeze_nakshatra_vocabulary_data.py"


def test_frozen_rows_equal_a_fresh_derivation_from_the_l0_modules():
    lexicon = tuple((r["nakshatra_id"], r["name_en"], r["name_sa_iast"], tuple(r["alt_names"]))
                    for r in sorted(NAKSHATRAS_ENRICHED, key=lambda r: r["nakshatra_id"]) if 1 <= r["nakshatra_id"] <= 27)
    ontology = tuple((nid, en, sa, tuple(syns)) for nid, en, sa, syns in sorted(NAK_DATA, key=lambda t: t[0]))
    assert data.LEXICON_ROWS == lexicon, "frozen lexicon rows drifted: run platform/scripts/governance/freeze_nakshatra_vocabulary_data.py"
    assert data.ONTOLOGY_ROWS == ontology, "frozen ontology rows drifted: run platform/scripts/governance/freeze_nakshatra_vocabulary_data.py"
    assert len(lexicon) == len(ontology) == 27


def test_the_generator_reproduces_the_committed_file_byte_for_byte():
    r = subprocess.run([sys.executable, str(GENERATOR), "--check"], capture_output=True, text=True, timeout=120)
    assert r.returncode == 0, "brahmagyan/nakshatra_vocabulary_data.py is not what the generator writes; re-run it"


def test_the_data_module_is_constants_only():
    tree = ast.parse(pathlib.Path(data.__file__).read_text(encoding="utf-8"))
    assert not [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))], "the frozen module must import nothing"
    assert not [n for n in ast.walk(tree) if isinstance(n, (ast.Call, ast.FunctionDef, ast.ClassDef))], "constants only"


def _imports_of(path: pathlib.Path) -> set[str]:
    out: set[str] = set()
    for n in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(n, ast.Import):
            out.update(a.name for a in n.names)
        elif isinstance(n, ast.ImportFrom):
            out.add(n.module or "")
    return out


def test_the_vocabulary_is_a_leaf_with_no_database_code_in_its_closure():
    imports = _imports_of(pathlib.Path(voc.__file__))
    assert imports == {"__future__", "unicodedata", "types", "typing", "brahmagyan.nakshatra_vocabulary_data"}, imports
    for mod in (voc, data):
        tree = ast.parse(pathlib.Path(mod.__file__).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                owner = ast.unparse(node.func.value).lower()
                assert not (node.func.attr in ("commit", "rollback", "close", "execute", "cursor", "connect") and ("conn" in owner or "cur" in owner or "psycopg" in owner)), (mod.__name__, ast.unparse(node))


def test_the_normaliser_behaves_exactly_as_before_the_freeze():
    assert voc.normalize_nakshatra("Mula") == "Moola" and voc.nakshatra_index("Dhanishta") == 23
    assert voc.normalize_nakshatra("Mṛgaśirā") == "Mrigasira" and voc.canonical_nakshatra("Purva") is None
    assert len(voc.NAKSHATRA_SYNONYMS) == 105 and voc.AMBIGUOUS_BARE_TOKENS == {"purva", "uttara", "poorva", "phalguni", "ashadha", "asadha", "bhadrapada", "bhadra"}
    assert dict(voc.SUPPRESSED_AMBIGUOUS_ALIASES) == {"Purva": ("Purva Phalguni", "lexicon alt_names"), "Uttara": ("Uttara Phalguni", "lexicon alt_names"), "uttara": ("Uttara Phalguni", "ontology synonym")}
