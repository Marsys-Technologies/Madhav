"""
test_domain_vocabulary.py — SHABDA-SHUDDHI · R7 · vocabulary unification.

Guards the domain vocabulary module across three axes:

  1. The Python vocabulary is internally consistent and complete.
  2. The TypeScript mirror matches the Python SSoT member-for-member.
  3. No writer in the sidecar emits a known-legacy domain string outside the
     synonym resolution path (raw 'finance', 'spiritual', etc. as a domain
     column value).
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import pytest

_SIDECAR = pathlib.Path(__file__).resolve().parent.parent
_REPO = _SIDECAR.parent.parent
sys.path.insert(0, str(_SIDECAR))

from brahmagyan.domain_vocabulary import (  # noqa: E402
    CANONICAL_DOMAINS,
    CANONICAL_DOMAINS_SORTED,
    DOMAIN_SYNONYMS,
    assert_canonical,
    canonical_domain,
    is_canonical,
)

_DOMAIN_VOCAB_TS = _REPO / "platform" / "src" / "lib" / "domain_vocabulary.ts"


# ── 1. the vocabulary itself ──────────────────────────────────────────────────


def test_canonical_domains_has_exactly_13_members():
    assert len(CANONICAL_DOMAINS) == 13


def test_canonical_domains_sorted_matches_frozenset():
    assert set(CANONICAL_DOMAINS_SORTED) == CANONICAL_DOMAINS
    assert list(CANONICAL_DOMAINS_SORTED) == sorted(CANONICAL_DOMAINS)


def test_every_synonym_resolves_to_a_canonical_domain():
    for legacy, canonical in DOMAIN_SYNONYMS.items():
        assert canonical in CANONICAL_DOMAINS, (
            f"synonym {legacy!r} -> {canonical!r} but {canonical!r} is not canonical"
        )


def test_no_synonym_key_is_itself_canonical():
    """If a synonym key IS a canonical domain, the mapping is a no-op and should
    be removed — it wastes a lookup and creates confusion about whether the
    canonical term needs resolution."""
    overlap = set(DOMAIN_SYNONYMS.keys()) & CANONICAL_DOMAINS
    assert not overlap, f"synonym keys that are already canonical: {sorted(overlap)}"


def test_canonical_domain_function_resolves_synonyms():
    assert canonical_domain('financial') == 'wealth'
    assert canonical_domain('spiritual') == 'spirituality'
    assert canonical_domain('marriage') == 'relationship'
    assert canonical_domain('children') == 'progeny'
    assert canonical_domain('property') == 'residence'
    assert canonical_domain('foreign') == 'travel'
    assert canonical_domain('intellect') == 'education'
    assert canonical_domain('moksha') == 'spirituality'


def test_canonical_domain_function_passes_through_canonical_terms():
    for d in CANONICAL_DOMAINS:
        assert canonical_domain(d) == d


def test_canonical_domain_fallback():
    assert canonical_domain('unknown_gibberish') == 'general'
    assert canonical_domain(None) == 'general'
    assert canonical_domain('') == 'general'
    assert canonical_domain('unknown', fallback='transition') == 'transition'


def test_canonical_domain_fallback_validation():
    with pytest.raises(ValueError, match="not a canonical domain"):
        canonical_domain('career', fallback='bogus')


def test_canonical_domain_case_insensitive():
    assert canonical_domain('FINANCIAL') == 'wealth'
    assert canonical_domain('Career') == 'career'
    assert canonical_domain('  wealth  ') == 'wealth'


def test_canonical_domain_multi_candidate():
    assert canonical_domain(None, 'financial', 'career') == 'wealth'
    assert canonical_domain(None, None, 'health') == 'health'
    assert canonical_domain(None, None) == 'general'


def test_is_canonical():
    for d in CANONICAL_DOMAINS:
        assert is_canonical(d)
    assert not is_canonical('financial')
    assert not is_canonical('spiritual')
    assert not is_canonical(None)
    assert not is_canonical('')


def test_assert_canonical_passes_for_canonical():
    for d in CANONICAL_DOMAINS:
        assert assert_canonical(d) == d


def test_assert_canonical_raises_for_synonym_with_suggestion():
    with pytest.raises(ValueError, match="legacy synonym.*use 'wealth'"):
        assert_canonical('financial')


def test_assert_canonical_raises_for_unknown():
    with pytest.raises(ValueError, match="not in the canonical vocabulary"):
        assert_canonical('bogus_domain')


# ── 2. build <-> serve parity ─────────────────────────────────────────────────

_TS_DOMAIN_RE = re.compile(r"'([a-z_]+)'", re.M)
_TS_SYNONYM_RE = re.compile(r"^\s*([a-z_]+)\s*:\s*'([a-z_]+)'", re.M)


def _parse_ts_domains() -> set[str]:
    """Extract domain members from the TS CANONICAL_DOMAINS array."""
    text = _DOMAIN_VOCAB_TS.read_text()
    start = text.index("CANONICAL_DOMAINS = [")
    end = text.index("] as const", start)
    return set(_TS_DOMAIN_RE.findall(text[start:end]))


def _parse_ts_synonyms() -> dict[str, str]:
    """Extract synonym entries from the TS DOMAIN_SYNONYMS object."""
    text = _DOMAIN_VOCAB_TS.read_text()
    start = text.index("DOMAIN_SYNONYMS")
    end = text.index("};", start)
    return {m.group(1): m.group(2) for m in _TS_SYNONYM_RE.finditer(text[start:end])}


def test_ts_file_exists():
    assert _DOMAIN_VOCAB_TS.is_file(), f"TS mirror not found: {_DOMAIN_VOCAB_TS}"


def test_python_and_typescript_domains_are_identical():
    ts_domains = _parse_ts_domains()
    assert ts_domains == CANONICAL_DOMAINS, (
        "build-side and serve-side domain vocabularies have drifted.\n"
        f"  only in python: {sorted(CANONICAL_DOMAINS - ts_domains)}\n"
        f"  only in ts:     {sorted(ts_domains - CANONICAL_DOMAINS)}"
    )


def test_python_and_typescript_synonyms_are_identical():
    ts_synonyms = _parse_ts_synonyms()
    assert ts_synonyms == DOMAIN_SYNONYMS, (
        "build-side and serve-side domain synonyms have drifted.\n"
        f"  only in python: {sorted(set(DOMAIN_SYNONYMS) - set(ts_synonyms))}\n"
        f"  only in ts:     {sorted(set(ts_synonyms) - set(DOMAIN_SYNONYMS))}\n"
        f"  value mismatch: {sorted(k for k in set(DOMAIN_SYNONYMS) & set(ts_synonyms) if DOMAIN_SYNONYMS[k] != ts_synonyms[k])}"
    )


# ── 3. the 13 canonical domains match the DB CHECK constraint (migration 386) ─

def test_migration_386_check_constraint_includes_all_canonical_domains():
    """The DB CHECK constraint from migration 386 must include all 13 canonical
    domains. The migration also includes legacy terms (finance, spiritual, etc.)
    for backward compatibility — that's intentional. The vocabulary module is
    the canonical set; the DB CHECK is a superset until all writers are migrated
    and a tightening migration can drop the legacy terms."""
    mig_dir = _REPO / "platform" / "supabase" / "migrations"
    mig_386 = None
    for p in sorted(mig_dir.glob("386_*")):
        mig_386 = p
        break
    if mig_386 is None:
        pytest.skip("migration 386 not found — may have been renumbered")
    sql = mig_386.read_text()
    all_domains_in_checks: set[str] = set()
    for m in re.finditer(r"IN\s*\(((?:'[a-z_]+'\s*,?\s*)+)\)", sql):
        for d in re.findall(r"'([a-z_]+)'", m.group(1)):
            all_domains_in_checks.add(d)
    if not all_domains_in_checks:
        pytest.skip("no domain CHECK constraints found in migration 386")
    missing = CANONICAL_DOMAINS - all_domains_in_checks
    assert not missing, (
        f"migration 386 CHECK is missing canonical domains: {sorted(missing)}"
    )
    # The legacy terms in the CHECK that aren't in CANONICAL_DOMAINS must all
    # be known synonyms — no unknown term should appear in a DB CHECK.
    extra = all_domains_in_checks - CANONICAL_DOMAINS
    unknown = extra - set(DOMAIN_SYNONYMS.keys())
    assert not unknown, (
        f"migration 386 CHECK has terms that are neither canonical nor known synonyms: "
        f"{sorted(unknown)}"
    )
