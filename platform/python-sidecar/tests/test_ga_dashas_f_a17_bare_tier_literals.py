"""
test_ga_dashas_f_a17_bare_tier_literals.py — F-A17 (L1 W2 DECIDE #3): ga_dashas_writer.py
emitted `verification_pass_status`/`verification_method` values as bare string literals
("two_pass_verified", "classical_match", "single", "scope_cap_sentinel") at ~38 call
sites, instead of using the named constants brahmagyan/verification_vocab.py exists
specifically to provide (CLAUDE.md §N.4: "Writers must still emit the tier via
brahmagyan/verification_vocab.py named constants... never a bare string literal").

A drifted literal can silently diverge from the vocabulary's own spelling with no
import-time error; a named constant cannot. This is a static source-text check, not a
runtime-behavior check, because the emitted STRING VALUE is identical either way -- the
defect is in the source text's own resilience to drift, which only a text-level guard
can catch.

`scope_cap_sentinel` needed special handling: it was a legal vocabulary member
(verification_vocab.py entry 9) with no exported named constant at all. Adding one
there (the doctrinally cleaner fix) was tried and reverted: verification_vocab.py is a
shared L0 module every ga_*/bo_* writer's provenance digest transitively includes
(asset_runner.py's get_writer_source_hash walks the local-import closure) -- editing it
and regenerating nirmana-writer-digests.json shifted ~24 unrelated L1+L2 writers'
digests and made `nirmana_analysis_layer_pins.py --check` report ALL THREE of L0/L1/L2's
writer_inventory_sha256 stale -- the exact "would invalidate already-frozen capsules, not
forced through unilaterally" residual this same file's own F-A10 fix already named for
`RESTRICTED_TABLE_VOCAB`. Resolved instead with a single controlled `entry_for()` lookup
inside ga_dashas_writer.py itself (verification_vocab.py untouched, zero blast radius) --
one bare-literal lookup site instead of two raw emission sites, still reading the
vocabulary's own canonical value rather than a second hardcoded copy.
"""
from __future__ import annotations

import pathlib
import re

_WRITER_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "ga_writers" / "ga_dashas_writer.py"
)

# Docstring/comment prose lines that legitimately quote these strings to DESCRIBE the
# vocabulary in English, not to emit a value, PLUS the one controlled entry_for() lookup
# site that resolves SCOPE_CAP_SENTINEL from the canonical vocabulary without touching
# the shared L0 module. Line numbers are 1-indexed and pinned so a genuine new code-path
# regression elsewhere in the file cannot hide behind this allowlist growing silently --
# adding a line here requires deliberately widening it.
_ALLOWED_PROSE_LINES = frozenset({986, 987, 991, 3396})
_ALLOWED_LOOKUP_LINES = frozenset({67})

_BARE_LITERAL_RE = re.compile(
    r'"(two_pass_verified|classical_match|scope_cap_sentinel)"'
)
# "single" needs its own pattern: too common a substring/word to share the group above
# (avoids false-triggering on "single_pass" or unrelated english usage elsewhere).
_BARE_SINGLE_RE = re.compile(r'(?<!_)"single"(?!_)')


def _source_lines() -> list[str]:
    return _WRITER_PATH.read_text(encoding="utf-8").splitlines()


def test_no_bare_tier_literals_outside_allowed_sites():
    lines = _source_lines()
    offenders = []
    for lineno, text in enumerate(lines, start=1):
        if lineno in _ALLOWED_PROSE_LINES or lineno in _ALLOWED_LOOKUP_LINES:
            continue
        if _BARE_LITERAL_RE.search(text) or _BARE_SINGLE_RE.search(text):
            offenders.append((lineno, text.strip()))
    assert offenders == [], (
        "Bare verification_pass_status/verification_method string literal(s) found; "
        "use the imported brahmagyan.verification_vocab named constant (or the module-"
        "level SCOPE_CAP_SENTINEL derived via entry_for()) instead "
        f"-- F-A17 regression: {offenders}"
    )


def test_scope_cap_sentinel_resolved_via_canonical_vocab_lookup():
    """SCOPE_CAP_SENTINEL must be a module-level attribute derived from
    verification_vocab.entry_for(), not a second hardcoded copy of the string --
    proves the fix reads the single source of truth rather than drifting from it."""
    from ga_writers import ga_dashas_writer as mod
    from brahmagyan import verification_vocab as vocab

    assert mod.SCOPE_CAP_SENTINEL == "scope_cap_sentinel"
    entry = vocab.entry_for("scope_cap_sentinel")
    assert entry is not None
    assert mod.SCOPE_CAP_SENTINEL == entry.status


def test_verification_vocab_module_untouched():
    """Confirms the fix carries zero cross-writer digest blast radius: verification_
    vocab.py must NOT export a SCOPE_CAP_SENTINEL symbol -- if a future edit adds one
    there, it reintroduces the exact L0/L1/L2 writer_inventory_sha256 staleness this
    fix deliberately avoided; that edit needs its own coordinated cross-layer follow-up,
    not a silent reappearance alongside an unrelated ga_dashas change."""
    from brahmagyan import verification_vocab as vocab

    assert not hasattr(vocab, "SCOPE_CAP_SENTINEL")
    # The vocabulary member itself must still exist -- only the writer-facing symbol
    # was deliberately withheld, not the underlying entry.
    assert vocab.entry_for("scope_cap_sentinel") is not None
