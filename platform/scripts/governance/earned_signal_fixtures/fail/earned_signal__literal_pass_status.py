# FAIL fixture — reproduces F-11 verbatim in shape (SAMAPTI_N8_EARNED_SIGNAL_REGISTER
# v1.0, `ga_nakshatra.py:87`): an unconditional `verification_pass_status: "PASS"`
# stamped on every emitted row, with zero verification logic anywhere behind it.
# The §N.8-correct value for a signal with no detector is None.
# EXPECT-VIOLATIONS: 1
def _enrich(rows, eng_ver, computed_at):
    enriched = []
    for r in rows:
        enriched.append({
            **r,
            "fact_id": r["id"],
            "verification_pass_status": "PASS",
            "engine_version": eng_ver,
            "computed_at": computed_at,
        })
    return enriched
