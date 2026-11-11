# Explicit absence of grounding and a mutable accumulator make no success claim.
def report(subsystems):
    subsystems_ok: list[str] = []
    for subsystem in subsystems:
        subsystems_ok.append(subsystem)
    return {
        "grounding_status": "UNGROUNDED",
        "subsystems_ok": subsystems_ok,
    }


def scaffold():
    return {"grounding_status": "SCAFFOLD"}
