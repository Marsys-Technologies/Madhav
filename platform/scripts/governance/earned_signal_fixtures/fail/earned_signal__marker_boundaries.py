# EXPECT-VIOLATIONS: 5
def report():
    subsystems_ok: list[str] = []
    return {
        "grounding_status": "GROUNDED",
        "verification_pass_status": "UNGROUNDED",
        "subsystems_ok": subsystems_ok,
    }


def wrong_field_or_positive_label():
    return [
        {"validator_verdict": "floored"},
        {"verification_pass_status": "two_pass_verified"},
    ]
