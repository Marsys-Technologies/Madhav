"""
Irreplaceable-outcome guard for mi_bhavisya.py (R6 fix, superseded by SS N-104).

History: R6 first scoped the writer's per-chart DELETE to lifecycle_status IN ('pending', 'due') so a
routine rebuild could not destroy rows carrying a native-verified outcome (confirmed/denied/partial,
written exclusively by mi_abhilekha's journal-answer sync).  SS N-104 (an application of N-46) went
further: calibration records are HISTORY, so the writer has NO delete or update of
mimamsa_predictions / mimamsa_manifestation_sets at all -- a pending row is as unreplaceable as a
confirmed one, because its emitted_at is the only evidence of WHEN the claim was made.

This file keeps the source-text guards (cheap, DB-free).  The behavioural proof -- real rebuilds over
existing rows on a fake and on a disposable PostgreSQL, byte-for-byte, with mutation proofs -- is
tests/test_mi_bhavisya_append_only.py.
"""
import inspect
import re

from pipeline.orchestrator.writers import mi_bhavisya


def _run_code() -> str:
    src = inspect.getsource(mi_bhavisya.MiBhavisyaWriter.run)
    return "\n".join(l for l in src.splitlines() if not l.strip().startswith("#"))


def test_run_has_no_delete_update_or_truncate():
    code = _run_code()
    for kw in ("DELETE", "TRUNCATE"):
        assert not re.search(rf"\b{kw}\b", code), f"{kw} against the frozen tables is forbidden (SS N-104)"
    assert not re.search(r"\bUPDATE\b", code), "UPDATE of a frozen prediction is forbidden (SS N-104)"


def test_inserts_never_overwrite_on_conflict():
    code = _run_code()
    assert code.count("ON CONFLICT") == 2 and code.count("DO NOTHING") == 2
    assert "DO UPDATE" not in code


def test_only_ever_inserts_the_initial_pending_status():
    # outcome statuses are written by mi_abhilekha's journal sync alone, never by this writer
    code = _run_code()
    for status in ("confirmed", "denied", "partial", "expired"):
        assert f"'{status}'" not in code and f'"{status}"' not in code
    assert '"pending"' in code


def test_does_not_reference_the_dropped_outcome_columns():
    # outcome_observed/brier_score belonged to the v1.0 table dropped by migration 346a and
    # recreated with a different schema by 347_mimamsa_bhavisya.sql -- never resurrect it.
    code = _run_code()
    assert "outcome_observed" not in code
    assert "brier_score" not in code
