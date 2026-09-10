# PASS fixture — signal headline built from a gloss map, not raw token interpolation.

SIGNAL_TYPE_GLOSS = {
    "graha_dignity_per_varga": "dignity in divisional chart",
    "yoga_label": "yoga activation",
    "dosha_label": "dosha presence",
}


def build_signal_headline(signal_type_id: str, graha: str, label: str) -> str:
    # GOOD: gloss the signal_type_id through a readable label
    type_label = SIGNAL_TYPE_GLOSS.get(signal_type_id, signal_type_id.replace("_", " "))
    return f"{graha} — {type_label}: {label}"


def build_row(graha: str, signal_type_id: str, value: str) -> dict:
    return {
        # GOOD: narrative field uses glossed label
        "signal_headline_text": build_signal_headline(signal_type_id, graha, value),
    }
