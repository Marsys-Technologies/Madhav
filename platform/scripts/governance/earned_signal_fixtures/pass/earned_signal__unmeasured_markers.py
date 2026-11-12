# Explicit absence of grounding makes no success claim.
def report():
    return {"grounding_status": "UNGROUNDED"}


def scaffold():
    return {"grounding_status": "SCAFFOLD"}


def stored_provenance():
    return [
        {"verification_pass_status": "floored"},
        {"verification_pass_status": "computed_extension"},
    ]
