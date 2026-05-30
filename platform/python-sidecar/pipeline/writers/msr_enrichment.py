"""
msr_enrichment.py — MARSYS-JIS G4-03
MSR signal enrichment pass: adds source_corroboration_count and
recomputes verification_certainty for each signal.

In production this pass would join with chart_facts and the RAG corpus.
For now it is a deterministic stub that assigns corroboration defaults
and recomputes the formula from salience.py.
"""
from typing import Optional


def enrich_signals(signals: list, chart_facts: Optional[dict] = None) -> list:
    """
    Enrich MSR signals with source corroboration counts and
    recomputed verification_certainty.

    Parameters
    ----------
    signals:
        List of signal dicts.  Each dict may already carry
        'source_corroboration_count'; if absent, defaults to 1.
    chart_facts:
        Optional dict of pre-fetched chart_facts data.
        Reserved for future use; not consumed by this stub.

    Returns
    -------
    List of enriched signal dicts (new dicts — originals unmodified).
    """
    from pipeline.writers.salience import verification_certainty

    result = []
    for sig in signals:
        count = sig.get("source_corroboration_count", 1)
        enriched = dict(sig)
        enriched["source_corroboration_count"] = count
        enriched["verification_certainty"] = verification_certainty(count)
        result.append(enriched)
    return result
