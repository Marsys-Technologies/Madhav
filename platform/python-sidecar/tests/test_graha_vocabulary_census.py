"""
test_graha_vocabulary_census.py — ADHIṢṬHĀNA Campaign A, Lane A2 census gate.

R17 (Adoption over addition): graha-identifier normalization work is accepted
by REMOVAL counts, never by SSoT-module existence. Before this lane the
codebase had 46 independent Python dict literals each normalizing graha
(planet) identifiers (codes/long-forms/Sanskrit names) to some local
convention, disagreeing subtly with each other. The fix promoted the best
existing resolver (`valence_doctrine.norm_graha`) to a new canonical module,
`brahmagyan/graha_vocabulary.py`, and retired every other independent map to
either an import of that SSoT or a dict comprehension DERIVED from it
(`{name: norm_graha(name) for name in (...)}` / `to_title(name)`), preserving
each site's exact prior output values and `.get()`-miss semantics.

This is the PERMANENT regression gate (mirrors tests/test_domain_vocabulary_
census.py's pattern): a literal `{"SUN": "SUN", "MOON": "MOON", ...}`-shaped
dict — i.e. several graha-identifier tokens as HARDCODED STRING KEYS in one
dict literal — is the defect class. A comprehension that calls norm_graha()/
to_title() has no such literal keys and does not trip this scanner; that IS
the adoption signal (R17 measures by removal, not by inspection of import
lines, so this scanner deliberately looks for the SHAPE of independence, not
whether graha_vocabulary is merely imported somewhere in the file).

WHAT IS A "VIOLATION" FOR THE CENSUS GATE
------------------------------------------
A Python source file (outside tests/graha_vocabulary.py itself) containing a
dict literal with >= GRAHA_KEY_THRESHOLD (4) distinct string keys that
case-insensitively match a known graha-identifier token (short code, long
English name, or classical Sanskrit name — the same vocabulary
brahmagyan/graha_vocabulary._GRAHA_ALIASES covers, plus the handful of
free-text/prose variants some sites recognize, e.g. "sol"/"luna"/"budh").

WHAT IS NOT A VIOLATION
------------------------
- brahmagyan/graha_vocabulary.py itself (the SSoT — the ONE permitted map)
- Test files / __tests__ directories
- Dict COMPREHENSIONS (`{k: norm_graha(k) for k in (...)}`) — no literal
  string VALUES keyed by graha tokens, so they structurally cannot match
- Dicts whose graha-token keys number fewer than the threshold (e.g. a
  2-planet Yogakaraka table) — not a general-purpose alias/subject map
- Dicts that map graha tokens to something OTHER than an identifier/subject
  code (dignity tables, house-lordship tables, karaka tables, PyJHora
  numeric-id adapters) — a different domain that happens to use graha names
  as keys is not this lane's defect class (see bo_laksana._DOSHA_GROUP_GRAHA,
  ga_vargas_writer.LAL_KITAB_PAKKA_GHAR / _AV_BODY_TO_JHORA_ID, explicitly
  excluded below with reasoning)
"""
from __future__ import annotations

import ast
import pathlib
import sys

import pytest

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIDECAR))

from brahmagyan.graha_vocabulary import _GRAHA_ALIASES  # noqa: E402

# ── Scan scope: every directory a graha map was found in during the A2 audit ──
_SCAN_DIRS = [
    _SIDECAR / "ga_writers",
    _SIDECAR / "bodha_writers",
    _SIDECAR / "pipeline",
    _SIDECAR / "services",
    _SIDECAR / "brahmagyan",
]

# ── The graha-identifier vocabulary this scanner recognizes as "keys of a
# graha map" — the SSoT's own alias keys (already covers short codes, long
# English names, and classical Sanskrit names) plus the small set of extra
# free-text/prose variants a few sites (bo_laksana, ka_temporal) recognize
# that the SSoT itself does not carry (those are documented extras, not a
# second source of truth — see bo_laksana._EXTRA_TEXT_ALIASES).
_GRAHA_TOKENS: frozenset[str] = frozenset(
    {k.lower() for k in _GRAHA_ALIASES}
    | {v.lower() for v in _GRAHA_ALIASES.values()}
    | {
        "lagna", "su", "mo", "ma", "me", "ju", "ve", "sa", "ra", "ke",
        "sol", "luna", "mangal", "budh", "brihaspati", "sukra", "sani",
        "rahoo", "kethu", "north_node", "south_node", "true_node",
    }
)

# A dict literal needs at least this many DISTINCT graha-token keys before
# it counts as a graha map (a 2-3 entry table is more likely a doctrinal
# lookup — Yogakaraka-by-lagna, dosha-group primary graha — than an
# identifier normalizer).
GRAHA_KEY_THRESHOLD = 4

# ── Known-safe exclusions (file-level) ─────────────────────────────────────
_SSOT_FILE = "graha_vocabulary.py"

# ── Known intentional exclusions: real dict literals with >=4 graha-token
# keys that are NOT identifier-normalization maps — a different domain
# (dignity/lordship/karaka/PyJHora-adapter tables) that happens to use graha
# names as keys. Documented in the Lane A2 PR. Keyed by
# (filename, assigned-name) so a genuinely new independent alias map in the
# same file cannot hide behind this allowlist.
_INTENTIONAL_EXCLUSIONS: frozenset[tuple[str, str]] = frozenset({
    # bo_laksana.py: dosha-group -> primary graha (keys are dosha groups,
    # not graha tokens; only 2 of 3 values happen to be graha codes)
    ("bo_laksana.py", "_DOSHA_GROUP_GRAHA"),
    # bo_laksana.py: documented EXTRA prose aliases the SSoT itself does not
    # carry (sol/luna/mangal/budh/brihaspati/sukra/sani/rahoo/kethu) — a
    # deliberate, minimal, in-lane addendum layered ON TOP of SSoT-derived
    # tokens (see _GRAHA_NAME_MAP just above it in the same file), not an
    # independent alias table.
    ("bo_laksana.py", "_EXTRA_TEXT_ALIASES"),
    # ga_vargas_writer.py: Lal Kitab Pakka Ghar — graha -> fixed HOUSE NUMBER
    # (int), a classical doctrinal table, not an identifier map
    ("ga_vargas_writer.py", "LAL_KITAB_PAKKA_GHAR"),
    # ga_vargas_writer.py: PyJHora's OWN numeric planet-id encoding for
    # ashtakavarga.get_ashtaka_varga() — a third-party adapter ID system,
    # not this codebase's fact_subject vocabulary
    ("ga_vargas_writer.py", "_AV_BODY_TO_JHORA_ID"),
    # valence_doctrine.py: natural-nature / functional-lordship / dignity /
    # harsh-aspect tables — graha -> a doctrinal SCORE or aspect-offset set,
    # not an identifier/subject code
    ("valence_doctrine.py", "_NATURAL_NATURE"),
    ("valence_doctrine.py", "_HARSH_SPECIAL_ASPECTS"),
    # l0_sutravali_extractor.py: PLANET_CANON uses a THIRD 3-letter output
    # convention (MON/RAH/KET, not the SSoT's MOON/RAH_MEAN/KET_MEAN) for
    # this single L0 sutra-extraction consumer only — a genuinely different
    # value contract, not force-migrated to avoid growing the SSoT with a
    # single-consumer output form (would need a 3rd to_*() helper for one
    # call site).
    ("l0_sutravali_extractor.py", "PLANET_CANON"),
    # chart_facts_writer_a3.py: dead/orphaned module — the containing
    # package (pipeline/writers/__init__.py) already fails to import
    # (references a deleted pipeline.writers.forensic_writer module,
    # pre-existing breakage unrelated to this lane; see FORENSIC A2/GA2
    # retirement note in CLAUDE.md §B). Not touched to avoid expanding
    # scope into an already-broken, unreachable package.
    ("chart_facts_writer_a3.py", "GRAHA_NAMES"),
    # ka_temporal/date_resolver.py: _GRAHA_ALIASES is a `dict[str, list[str]]`
    # synonym-REGISTRATION table (canonical name -> list of aliases), a
    # genuinely different data shape from the flat alias-map defect class
    # this census targets (its literal VALUES are list nodes, not string
    # constants, so it is naturally excluded by the value-shape check
    # above too — listed here for documentation, not because the scanner
    # would otherwise catch it).
    ("date_resolver.py", "_GRAHA_ALIASES"),
})


def _is_excluded_path(path: pathlib.Path) -> bool:
    name = path.name
    if name == _SSOT_FILE:
        return True
    s = str(path)
    if "__tests__" in s or "/tests/" in s or name.startswith("test_"):
        return True
    if "__pycache__" in s:
        return True
    return False


def _dict_literal_graha_key_hits(node: ast.Dict) -> set[str]:
    """Distinct graha-token keys (lowercased) among this dict literal's
    entries where BOTH the key AND the value are graha-identifier tokens
    (i.e. this is actually an alias/subject NORMALIZATION map — one graha
    representation to another — not a doctrinal lookup table that merely
    uses graha names as keys with non-identifier values: dignity states,
    sign names, house numbers, directions, themes, years, ids, lists).
    Comprehensions (ast.DictComp) have no `.keys`/`.values` list at all and
    are never passed here — see _find_graha_maps."""
    hits: set[str] = set()
    for k, v in zip(node.keys, node.values):
        if k is None:  # dict unpacking (**other) — skip
            continue
        if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
            continue
        low_k = k.value.strip().lower()
        if low_k not in _GRAHA_TOKENS:
            continue
        if not (isinstance(v, ast.Constant) and isinstance(v.value, str)):
            continue
        low_v = v.value.strip().lower()
        if low_v not in _GRAHA_TOKENS:
            continue
        hits.add(low_k)
    return hits


def _assigned_names(target: ast.AST) -> list[str]:
    if isinstance(target, ast.Name):
        return [target.id]
    if isinstance(target, ast.Tuple):
        out = []
        for elt in target.elts:
            out.extend(_assigned_names(elt))
        return out
    return []


def _find_graha_maps(path: pathlib.Path) -> list[tuple[str, int, int]]:
    """Return [(assigned_name, num_graha_keys, lineno), ...] for every dict
    LITERAL (not comprehension) assigned in this file whose graha-token key
    count meets GRAHA_KEY_THRESHOLD, excluding the documented allowlist."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(source)
    except (OSError, SyntaxError):
        return []

    found: list[tuple[str, int, int]] = []
    for node in ast.walk(tree):
        dict_node: ast.Dict | None = None
        names: list[str] = []
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            dict_node = node.value
            for t in node.targets:
                names.extend(_assigned_names(t))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.value, ast.Dict):
            dict_node = node.value
            names.extend(_assigned_names(node.target))

        if dict_node is None:
            continue

        hits = _dict_literal_graha_key_hits(dict_node)
        if len(hits) < GRAHA_KEY_THRESHOLD:
            continue

        for name in (names or ["<unnamed>"]):
            if (path.name, name) in _INTENTIONAL_EXCLUSIONS:
                continue
            found.append((name, len(hits), node.lineno))
    return found


def _collect_py_files() -> list[pathlib.Path]:
    files: list[pathlib.Path] = []
    for d in _SCAN_DIRS:
        if not d.is_dir():
            continue
        for p in d.rglob("*.py"):
            if not _is_excluded_path(p):
                files.append(p)
    return files


def _census() -> dict[str, list[tuple[str, int, int]]]:
    """Return {relative_path: [(name, num_keys, lineno), ...]} for every
    file with at least one surviving independent graha map."""
    out: dict[str, list[tuple[str, int, int]]] = {}
    for path in sorted(_collect_py_files()):
        hits = _find_graha_maps(path)
        if hits:
            out[str(path.relative_to(_SIDECAR))] = hits
    return out


def test_scanner_finds_known_writer_files():
    """Sanity: the scanner's scan scope reaches the files this lane touched."""
    names = {p.name for p in _collect_py_files()}
    for expected in (
        "ga_positions_writer.py", "ga_vichara_writer.py", "bo_laksana.py",
        "ka_yojaka.py", "taranga_service.py",
    ):
        assert expected in names, f"{expected} not reached by census scan scope"


def test_ssot_module_is_excluded_from_scan():
    names = {p.name for p in _collect_py_files()}
    assert "graha_vocabulary.py" not in names


def test_ssot_itself_has_the_one_permitted_graha_map():
    """graha_vocabulary._GRAHA_ALIASES is the ONE permitted independent
    literal — sanity check the SSoT module still defines a real graha-token
    dict literal (it is excluded from the tree scan above by file name, so
    check it directly here by re-parsing the module's own source)."""
    ssot_path = _SIDECAR / "brahmagyan" / _SSOT_FILE
    tree = ast.parse(ssot_path.read_text(encoding="utf-8"))
    dict_literals = [
        n.value for n in ast.walk(tree)
        if (isinstance(n, (ast.Assign, ast.AnnAssign)) and isinstance(n.value, ast.Dict))
    ]
    hit_counts = [len(_dict_literal_graha_key_hits(n)) for n in dict_literals]
    assert any(c >= GRAHA_KEY_THRESHOLD for c in hit_counts), (
        "graha_vocabulary.py no longer defines a graha-token dict literal "
        "meeting the census threshold — the SSoT itself would fail its own gate"
    )


def test_python_independent_graha_maps_census_is_one():
    """THE GATE (R17): exactly ONE independent Python graha map survives
    tree-wide — the SSoT itself (brahmagyan/graha_vocabulary._GRAHA_ALIASES,
    excluded from the scan by file name, counted here directly). Every other
    site must be a comprehension DERIVED from norm_graha()/to_title(), which
    this scanner cannot see as a literal (that absence IS the pass signal).

    Before ADHIṢṬHĀNA Lane A2: 46 independent literal graha-alias maps found
    tree-wide by this exact scanner shape (AST dict-literal scan + value-
    shape verification — both key AND value must be graha-identifier
    tokens), re-run directly against the pre-lane git tree (commit
    53d6c92be) as a detector-cited measurement, not an estimate. Of these
    46: 1 (valence_doctrine._GRAHA_ALIASES) was PROMOTED — moved, not
    copied — to become this module; 1 (ga_yoga_writer.PLANET_SUBJECTS) was
    dead code, deleted outright; 2 remain independent by documented,
    reasoned exclusion (l0_sutravali_extractor.PLANET_CANON — a third,
    single-consumer 3-letter output convention; chart_facts_writer_a3.
    GRAHA_NAMES — inside an already-broken, unreachable package); the
    remaining 42 were retired to comprehensions calling norm_graha()/
    to_title(). Only 13 of the 46 were in the lane brief's own original
    enumeration — the rest (33) were surfaced by this full-tree census
    itself, which is the R17-mandated measurement, not the brief's
    estimate.
    After: 0 outside the SSoT (this test), + the SSoT's own 1 = 1 total
    (the 2 documented exclusions are reasoned non-defects, not counted
    against the R17 gate — see _INTENTIONAL_EXCLUSIONS above).
    """
    census = _census()
    if census:
        lines = ["Independent Python graha maps found outside the SSoT (R17 violation):"]
        for fname, hits in sorted(census.items()):
            for name, nkeys, lineno in hits:
                lines.append(f"  {fname}:{lineno}: {name!r} ({nkeys} graha-token keys)")
        pytest.fail("\n".join(lines))

    # The SSoT itself is the exactly-one permitted independent map.
    assert len(_GRAHA_ALIASES) >= GRAHA_KEY_THRESHOLD, (
        "brahmagyan.graha_vocabulary._GRAHA_ALIASES must remain the one "
        "permitted independent graha map"
    )
