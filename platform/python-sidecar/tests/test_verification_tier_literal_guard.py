"""
test_verification_tier_literal_guard.py -- Q-L1-16(a) tier-constant guard.

CLAUDE.md §N.4 (S7 ruling): a writer emits a verification tier through a named constant
from `brahmagyan/verification_tiers.py` (derived from `verification_vocab.py`), never a
bare string literal; and (Q-L1-16(a), SS ruling N-62) the canonical spelling of "no second derivation ran" is `single`
(`SINGLE` / `UNVERIFIED_DEFAULT`), never the deprecated alias `single_pass`.

Three guards (AST-based, so comments and docstrings that merely DESCRIBE a tier are
ignored; only a real string constant in code counts):

  1. NO NEW `single_pass` EMISSION. No non-test sidecar module may contain the string
     constant "single_pass" or reference the `SINGLE_PASS` alias symbol, except the
     explicit allow-lists below. READERS may name the alias (a rank/weight table must
     keep accepting stored rows); WRITERS must not emit it.
  2. BARE-LITERAL RATCHET. For each writer module, the number of bare vocabulary-member
     string constants (excluding the check-status words `PASS`/`pass`, a different field)
     may not exceed its recorded baseline, and a writer file with no baseline entry must
     have none. New code therefore cannot add a bare tier literal; converting existing
     ones to constants only lowers a count (baselines may then be tightened, but the test
     does not force that, so concurrent conversion lanes do not collide on this file).
  3. The named constants exist, agree with the vocabulary, and `emit_tier()` rejects the
     deprecated alias.

This is a static source-text check on purpose: the emitted STRING is identical either way;
the defect class is the source text's resilience to drift.
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys
from typing import NamedTuple

import pytest

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SIDECAR))

from brahmagyan import verification_tiers as tiers  # noqa: E402
from brahmagyan import verification_vocab as vocab  # noqa: E402

_ALIAS = "single_pass"

#: Directories whose modules WRITE rows (the ratchet scope).
_WRITER_ROOTS = (
    "ga_writers", "pipeline/orchestrator/writers", "bodha_writers", "services", "brahmagyan",
)

#: The vocabulary and its symbol layer DEFINE the spellings; they are the one place literals belong.
_DEFINES_THE_VOCABULARY = frozenset({
    "brahmagyan/verification_vocab.py", "brahmagyan/verification_tiers.py",
})

#: Modules exempt from guard 1 because they ARE the vocabulary / its declared readers.
#: Value = reason. Adding an entry here is a deliberate act.
_ALIAS_READER_ALLOWLIST: dict[str, str] = {
    "brahmagyan/verification_vocab.py": "defines the deprecated-alias vocabulary entry",
    "brahmagyan/verification_tiers.py": "defines SINGLE_PASS (the reader-side alias symbol)",
    "pipeline/orchestrator/writers/bo_pramana_mapa.py": (
        "READER: _VERIFICATION_TIER_RANKS must keep ranking stored `single_pass` rows"
    ),
}

#: GRANDFATHERED L2 WRITERS that still emit the alias. These are NOT exempt in principle:
#: they are L2 (`bo_*`) writers whose switch to SINGLE rides the S-L2 batch (changing them
#: now would move the writer digests of assets under active L2 acceptance, and would
#: change F-10 tier-inversion ranks in bo_pramana_mapa: single_pass=2 vs single=1).
#: Value = maximum count of "single_pass" constants. The count may only go DOWN; an L1
#: (`ga_*`) writer must never appear here.
_GRANDFATHERED_ALIAS_EMITTERS: dict[str, int] = {
    "pipeline/orchestrator/writers/bo_bimba.py": 4,
    "pipeline/orchestrator/writers/bo_karanajala.py": 5,
}

#: Bare-literal baselines: per writer module, the number of string constants equal to a
#: vocabulary member (docstrings excluded; `PASS`/`pass` excluded). RATCHET -- may only
#: go down. Counts recorded 2026-10 at the Q-L1-16(a) constants PR.
_BARE_LITERAL_BASELINE: dict[str, int] = {
    "bodha_writers/arudha_emitter.py": 3,
    "bodha_writers/bhavat_bhavam_amplifier.py": 4,
    "bodha_writers/formulas.py": 13,
    "bodha_writers/nakshatra_semantic_emitter.py": 3,
    "bodha_writers/special_lagna_emitter.py": 3,
    "bodha_writers/sudarshana_emitter.py": 3,
    "bodha_writers/vargottama_dhana_emitter.py": 3,
    "ga_writers/build_runner.py": 14,
    "ga_writers/data_plane_contracts.py": 2,
    "ga_writers/ga_ayurdaya_writer.py": 3,
    "ga_writers/ga_condition_writer.py": 5,
    "ga_writers/ga_dashas_writer.py": 1,
    "ga_writers/ga_panchanga_writer.py": 13,
    "ga_writers/ga_positions_writer.py": 3,
    "ga_writers/ga_sade_sati_writer.py": 7,
    "ga_writers/ga_sensitive_degree_writer.py": 10,
    "ga_writers/ga_strength_writer.py": 11,
    "ga_writers/ga_structural_writer.py": 10,
    "ga_writers/ga_tajaka_writer.py": 7,
    "ga_writers/ga_vargas_writer.py": 7,
    "ga_writers/ga_yoga_writer.py": 4,
    "pipeline/orchestrator/writers/bo_bimba.py": 4,
    "pipeline/orchestrator/writers/bo_drishti.py": 1,
    "pipeline/orchestrator/writers/bo_karanajala.py": 8,
    "pipeline/orchestrator/writers/bo_laksana.py": 11,
    "pipeline/orchestrator/writers/bo_pramana_mapa.py": 6,
    "pipeline/orchestrator/writers/bo_sangati.py": 2,
    "pipeline/orchestrator/writers/bo_upaya.py": 3,
    "services/ka_tithi_pravesha/writer.py": 3,
    "brahmagyan/phala/l4_rectification.py": 1,
    "brahmagyan/signal_register_glossary.py": 1,
}

#: Baselines are TIGHT (equal to the counts at the Q-L1-16(a) PR). A conversion lane that
#: removes literals leaves slack below its file's number; tighten the entry in the same PR
#: (the test only fails on growth, so concurrent lanes do not collide here).

#: Strings assigned to a `*verif*` / `verification_pass_status` target that are NOT vocabulary
#: members. Key = (file, value); value = why. Deliberately tiny: each is a defect or a label,
#: not a tier a writer may invent. Stale entries are harmless (a lane that fixes one may delete it).
_NON_MEMBER_VERIF_ALLOWLIST: dict[tuple[str, str], str] = {
    ("ga_writers/ga_strength_writer.py", "floored_sarva_mismatch"): (
        "fixed by the Q03 tier-honesty lane (not a vocabulary member; Q03 removes this entry)"
    ),
    ("ga_writers/ga_sensitive_writer.py", "data_error"): (
        "KP_PARSE_ERROR error-path row stamps a non-vocabulary tier (assert_legal / the chart_facts "
        "CHECK would reject it); ga_sensitive is the Q03 tier-honesty lane's file -- fix there"
    ),
}
#: Prose descriptions keyed `verification_pass_status` (documentation dicts, not stored tiers).
_VERIF_PROSE_FILES = frozenset({"ga_writers/_vimshottari_independent_verifier.py"})

#: Words that are check/gate RESULTS on a different field, not tiers.
_NOT_A_TIER = frozenset(vocab.PROHIBITED_STATUSES)
_TIER_WORDS = frozenset(vocab.ALL_STATUSES) - _NOT_A_TIER


def _is_test_path(p: pathlib.Path) -> bool:
    return any(part in ("tests", "__tests__") for part in p.parts)


def _rel(p: pathlib.Path) -> str:
    return p.relative_to(_SIDECAR).as_posix()


def _sidecar_modules() -> list[pathlib.Path]:
    return [
        p for p in sorted(_SIDECAR.rglob("*.py"))
        if not _is_test_path(p) and ".venv" not in p.parts and "node_modules" not in p.parts
        and "site-packages" not in p.parts
    ]


def _docstring_ids(tree: ast.AST) -> set[int]:
    ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            body = node.body
            if (
                body and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                ids.add(id(body[0].value))
    return ids


def _parse(p: pathlib.Path) -> ast.AST | None:
    try:
        return ast.parse(p.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return None


class _Str(NamedTuple):
    value: str
    lineno: int


def _fold(node: ast.AST) -> str | None:
    """Constant-fold a string expression made only of literals joined by `+`."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left, right = _fold(node.left), _fold(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _string_constants(tree: ast.AST) -> list[_Str]:
    """Every string constant in code (docstrings excluded), PLUS every constant-folded
    `"a" + "b"` concatenation, so `"single_" + "pass"` cannot hide from the guard."""
    skip = _docstring_ids(tree)
    out: list[_Str] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in skip:
            out.append(_Str(n.value, n.lineno))
        elif isinstance(n, ast.BinOp):
            folded = _fold(n)
            if folded is not None:
                out.append(_Str(folded, n.lineno))
    return out


def _leaf_strings(node: ast.AST | None) -> list[str]:
    """String leaves a value expression can evaluate to (literal, folded concat, ternary, or)."""
    if node is None:
        return []
    folded = _fold(node)
    if folded is not None:
        return [folded]
    if isinstance(node, ast.IfExp):
        return _leaf_strings(node.body) + _leaf_strings(node.orelse)
    if isinstance(node, ast.BoolOp):
        return [x for v in node.values for x in _leaf_strings(v)]
    return []


_VERIF_NAME = re.compile(r"(?:^|_)verif(?:_|$)", re.IGNORECASE)
_VERIF_KEYS = frozenset({"verification_pass_status"})


def _is_verif_target(name: str | None) -> bool:
    return bool(name) and (name in _VERIF_KEYS or _VERIF_NAME.search(name) is not None)


def _target_name(t: ast.AST) -> str | None:
    if isinstance(t, ast.Name):
        return t.id
    if isinstance(t, ast.Attribute):
        return t.attr
    return None


def _verif_assigned_strings(tree: ast.AST) -> list[tuple[int, str, str]]:
    """(lineno, target, value) for every string assigned to a `*verif*` /
    `verification_pass_status` name, dict key, subscript, or keyword argument."""
    out: list[tuple[int, str, str]] = []
    for n in ast.walk(tree):
        pairs: list[tuple[str | None, ast.AST | None]] = []
        if isinstance(n, ast.Assign):
            for t in n.targets:
                key = _target_name(t)
                if key is None and isinstance(t, ast.Subscript) and isinstance(t.slice, ast.Constant):
                    key = t.slice.value if isinstance(t.slice.value, str) else None
                pairs.append((key, n.value))
        elif isinstance(n, ast.AnnAssign):
            pairs.append((_target_name(n.target), n.value))
        elif isinstance(n, ast.Dict):
            for k, v in zip(n.keys, n.values):
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    pairs.append((k.value, v))
        elif isinstance(n, ast.keyword):
            pairs.append((n.arg, n.value))
        for key, val in pairs:
            if _is_verif_target(key):
                out.extend((getattr(val, "lineno", 0), key or "", v) for v in _leaf_strings(val))
    return out


def _alias_references(tree: ast.AST) -> int:
    """Count 'single_pass' string constants + references to the SINGLE_PASS alias symbol."""
    n = sum(1 for c in _string_constants(tree) if c.value == _ALIAS)
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id == "SINGLE_PASS":
            n += 1
        elif isinstance(node, ast.Attribute) and node.attr == "SINGLE_PASS":
            n += 1
        elif isinstance(node, ast.ImportFrom):
            n += sum(1 for a in node.names if a.name == "SINGLE_PASS")
    return n


def _literal_count(tree: ast.AST) -> int:
    return sum(1 for c in _string_constants(tree) if c.value in _TIER_WORDS)


# ── guard 1: no new `single_pass` emission ────────────────────────────────────


def test_no_single_pass_emission_outside_allowlists():
    offenders: list[tuple[str, int]] = []
    for p in _sidecar_modules():
        rel = _rel(p)
        if rel in _ALIAS_READER_ALLOWLIST or rel in _GRANDFATHERED_ALIAS_EMITTERS:
            continue
        tree = _parse(p)
        if tree is None:
            continue
        n = _alias_references(tree)
        if n:
            offenders.append((rel, n))
    assert offenders == [], (
        "The deprecated tier alias 'single_pass' (SINGLE_PASS) must not be emitted by "
        "writers -- use brahmagyan.verification_tiers.SINGLE (Q-L1-16(a)). If this file "
        f"is a genuine READER of stored rows, add it to _ALIAS_READER_ALLOWLIST: {offenders}"
    )


def test_grandfathered_alias_emitters_only_shrink_and_are_never_l1():
    for rel, ceiling in _GRANDFATHERED_ALIAS_EMITTERS.items():
        assert not rel.startswith("ga_writers/"), f"{rel}: an L1 writer may not be grandfathered"
        tree = _parse(_SIDECAR / rel)
        assert tree is not None
        assert _alias_references(tree) <= ceiling, (
            f"{rel} gained a 'single_pass' reference (ceiling {ceiling}); emit SINGLE instead"
        )


def test_allowlisted_paths_exist():
    for rel in (*_ALIAS_READER_ALLOWLIST, *_GRANDFATHERED_ALIAS_EMITTERS, *_BARE_LITERAL_BASELINE):
        assert (_SIDECAR / rel).is_file(), f"stale allow-list/baseline entry: {rel}"


# ── guard 2: bare-literal ratchet ─────────────────────────────────────────────


def test_bare_tier_literals_do_not_grow():
    grew: list[str] = []
    for root in _WRITER_ROOTS:
        for p in sorted((_SIDECAR / root).rglob("*.py")):
            if _is_test_path(p) or _rel(p) in _DEFINES_THE_VOCABULARY:
                continue
            tree = _parse(p)
            if tree is None:
                continue
            n = _literal_count(tree)
            allowed = _BARE_LITERAL_BASELINE.get(_rel(p), 0)
            if n > allowed:
                grew.append(f"{_rel(p)}: {n} bare tier literal(s) > baseline {allowed}")
    assert grew == [], (
        "Bare verification-tier string literal(s) added to a writer. Import the named "
        "constant from brahmagyan.verification_vocab (SINGLE, FLOORED, CLASSICAL_MATCH, "
        "TWO_PASS_VERIFIED via two_pass_verdict(), ...) instead (CLAUDE.md §N.4): "
        + "; ".join(grew)
    )


def test_guard_detects_a_synthetic_offender():
    """The detectors can fail: a literal alias, the alias symbol, and a bare tier all count;
    prose in a docstring or comment does not."""
    bad = ast.parse('row = {"verification_pass_status": "single_pass"}')
    assert _alias_references(bad) == 1 and _literal_count(bad) == 1
    sym = ast.parse("from brahmagyan.verification_vocab import SINGLE_PASS\nx = SINGLE_PASS")
    assert _alias_references(sym) == 2
    bare = ast.parse('v = "floored"')
    assert _literal_count(bare) == 1
    clean = ast.parse(
        'from brahmagyan.verification_vocab import SINGLE\n'
        '"""mentions single_pass and floored in prose"""\n'
        'def f():\n    "single_pass is a deprecated alias"\n    # "floored"\n    return SINGLE\n'
    )
    assert _alias_references(clean) == 0 and _literal_count(clean) == 0


# ── guard 3: the constants themselves ─────────────────────────────────────────


_CONSTANT_FOR_MEMBER = {
    "two_pass_verified": "TWO_PASS_VERIFIED",
    "classical_match": "CLASSICAL_MATCH",
    "divergent_flagged": "DIVERGENT_FLAGGED",
    "single": "SINGLE",
    "single_pass": "SINGLE_PASS",
    "documented_approximation": "DOCUMENTED_APPROXIMATION",
    "computed_extension": "COMPUTED_EXTENSION",
    "floored": "FLOORED",
    "not_defined_for_nodes": "NOT_DEFINED_FOR_NODES",
    "scope_cap_sentinel": "SCOPE_CAP_SENTINEL",
    "skipped_malformed_source": "SKIPPED_MALFORMED_SOURCE",
    "external_computation_required": "EXTERNAL_COMPUTATION_REQUIRED",
    "pending_w3_verification": "PENDING_W3_VERIFICATION",
}


def test_every_vocabulary_member_has_exactly_one_named_constant():
    assert set(_CONSTANT_FOR_MEMBER) == vocab.ALL_STATUSES
    for status, name in _CONSTANT_FOR_MEMBER.items():
        assert getattr(tiers, name) == status, name
        assert name in tiers.__all__, name


def test_unverified_default_is_the_canonical_single():
    assert tiers.SINGLE == "single"
    assert vocab.UNVERIFIED_DEFAULT == tiers.UNVERIFIED_DEFAULT == tiers.SINGLE
    assert tiers.DEPRECATED_ALIAS_STATUSES == frozenset({tiers.SINGLE_PASS})
    assert tiers.DEPRECATED_ALIAS_STATUSES == frozenset(
        e.status for e in vocab.VERIFICATION_PASS_STATUS_VOCAB if e.deprecated_alias_of
    )
    assert vocab.canonical(tiers.SINGLE_PASS) == tiers.SINGLE
    # Readers keep accepting the alias: it is still a legal, unverified member.
    assert tiers.SINGLE_PASS in vocab.ALL_STATUSES
    assert not vocab.is_verified(tiers.SINGLE_PASS)


def test_re_exported_constants_are_the_vocabulary_objects():
    assert tiers.TWO_PASS_VERIFIED is vocab.TWO_PASS_VERIFIED
    assert tiers.CLASSICAL_MATCH is vocab.CLASSICAL_MATCH
    assert tiers.DIVERGENT_FLAGGED is vocab.DIVERGENT_FLAGGED


def test_emit_tier_rejects_the_deprecated_alias_and_prohibited_spellings():
    assert tiers.emit_tier(tiers.SINGLE) == "single"
    assert tiers.emit_tier(tiers.FLOORED) == "floored"
    with pytest.raises(ValueError, match="DEPRECATED alias"):
        tiers.emit_tier(tiers.SINGLE_PASS)
    with pytest.raises(ValueError, match="PROHIBITED"):
        tiers.emit_tier("PASS")
    with pytest.raises(ValueError, match="not in the settled vocabulary"):
        tiers.emit_tier("made_up")
    # Table restriction still enforced through the helper.
    with pytest.raises(ValueError, match="CHECK constraint"):
        tiers.emit_tier(tiers.DOCUMENTED_APPROXIMATION, table="chart_divisionals")


# ── guard 2b: strings assigned to a verification target must be vocabulary members ─────


def test_strings_assigned_to_verification_targets_are_vocabulary_members():
    """Closes the 'a made-up tier string never reaches the literal ratchet' blind spot: any
    string (literal, folded concatenation, ternary branch) assigned to a `*verif*` name,
    keyword, dict key or subscript, or to `verification_pass_status`, must be a settled
    vocabulary member (or an explicit allow-list entry above)."""
    members = vocab.ALL_STATUSES | vocab.PROHIBITED_STATUSES
    bad: list[str] = []
    for root in _WRITER_ROOTS:
        for p in sorted((_SIDECAR / root).rglob("*.py")):
            rel = _rel(p)
            if _is_test_path(p) or rel in _DEFINES_THE_VOCABULARY or rel in _VERIF_PROSE_FILES:
                continue
            tree = _parse(p)
            if tree is None:
                continue
            for lineno, target, value in _verif_assigned_strings(tree):
                if value not in members and (rel, value) not in _NON_MEMBER_VERIF_ALLOWLIST:
                    bad.append(f"{rel}:{lineno} {target}={value!r}")
    assert bad == [], "non-vocabulary verification tier assigned: " + "; ".join(bad)


def test_concatenated_alias_and_made_up_tiers_are_detected():
    cat = ast.parse('row = {"verification_pass_status": "single_" + "pass"}')
    assert _alias_references(cat) == 1
    made_up = ast.parse('bindu_verif = "floored_x"\nverif = "a" if c else "single"')
    got = {v for _, _, v in _verif_assigned_strings(made_up)}
    assert got == {"floored_x", "a", "single"}
    unrelated = ast.parse('verification_window = "2026"\nverified = "yes"\nverify_note = "x"')
    assert _verif_assigned_strings(unrelated) == []
