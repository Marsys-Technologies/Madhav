# EXPECT-VIOLATIONS: 3
def report():
    subsystems_ok: list[str] = []
    return {
        "grounding_status": "GROUNDED",
        "verification_pass_status": "UNGROUNDED",
        "subsystems_ok": subsystems_ok,
    }
