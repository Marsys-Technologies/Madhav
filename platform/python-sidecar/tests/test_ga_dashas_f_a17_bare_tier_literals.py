"""
test_ga_dashas_f_a17_bare_tier_literals.py — F-A17 (L1 W2 DECIDE #3): ga_dashas_writer.py
emitted `verification_pass_status`/`verification_method` values as bare string literals
("two_pass_verified", "classical_match", "single", "scope_cap_sentinel") at ~38 call
sites, instead of importing the named constants brahmagyan/verification_vocab.py exists
specifically to provide (CLAUDE.md §N.4: "Writers must still emit the tier via
brahmagyan/verification_vocab.py named constants... never a bare string literal").

A drifted literal can silently diverge from the vocabulary's own spelling with no
import-time error; a named constant cannot. This is a static source-text check, not a
runtime-behavior check, because the emitted STRING VALUE is identical either way -- the
defect is in the source text's own resilience to drift, which only a text-level guard
can catch.

`scope_cap_sentinel` additionally required a new named constant
(SCOPE_CAP_SENTINEL) in verification_vocab.py -- it was a legal vocabulary member
(entry 9) but had no importable symbol, which is precisely why the bare literal existed
in the first place.
"""
from __future__ import annotations

import pathlib
import re

_WRITER_PATH = (
    pathlib.Path(__file__).resolve().parents[1] / "ga_writers" / "ga_dashas_writer.py"
)

# Docstring/comment prose lines that legitimately quote these strings to DESCRIBE the
# vocabulary in English, not to emit a value. Line numbers are 1-indexed and pinned so
# a genuine new code-path regression elsewhere in the file cannot hide behind this
# allowlist growing silently -- adding a line here requires deliberately widening it.
_ALLOWED_PROSE_LINES = frozenset({961, 962, 966, 3371})

_BARE_LITERAL_RE = re.compile(
    r'"(two_pass_verified|classical_match|scope_cap_sentinel)"'
)
# "single" needs its own pattern: too common a substring/word to share the group above
# (avoids false-triggering on "single_pass" or unrelated english usage elsewhere).
_BARE_SINGLE_RE = re.compile(r'(?<!_)"single"(?!_)')


def _source_lines() -> list[str]:
    return _WRITER_PATH.read_text(encoding="utf-8").splitlines()


def test_no_bare_tier_literals_outside_allowed_prose():
    lines = _source_lines()
    offenders = []
    for lineno, text in enumerate(lines, start=1):
        if lineno in _ALLOWED_PROSE_LINES:
            continue
        if _BARE_LITERAL_RE.search(text) or _BARE_SINGLE_RE.search(text):
            offenders.append((lineno, text.strip()))
    assert offenders == [], (
        "Bare verification_pass_status/verification_method string literal(s) found; "
        "use the imported brahmagyan.verification_vocab named constant instead "
        "(TWO_PASS_VERIFIED / CLASSICAL_MATCH / UNVERIFIED_DEFAULT / SCOPE_CAP_SENTINEL) "
        f"-- F-A17 regression: {offenders}"
    )


def test_writer_imports_scope_cap_sentinel_constant():
    lines = _source_lines()
    import_block = "\n".join(lines[:60])
    assert "SCOPE_CAP_SENTINEL" in import_block, (
        "ga_dashas_writer.py must import SCOPE_CAP_SENTINEL from "
        "brahmagyan.verification_vocab, not spell the scope-cap sentinel tier as a "
        "bare literal (F-A17)."
    )


def test_verification_vocab_exports_scope_cap_sentinel():
    from brahmagyan import verification_vocab as vocab

    assert vocab.SCOPE_CAP_SENTINEL == "scope_cap_sentinel"
    # Must still be a legal member of the settled vocabulary, not a new one invented
    # alongside this fix (§N.8: no member added, only a symbol for an existing one).
    assert vocab.SCOPE_CAP_SENTINEL in vocab.ALL_STATUSES
