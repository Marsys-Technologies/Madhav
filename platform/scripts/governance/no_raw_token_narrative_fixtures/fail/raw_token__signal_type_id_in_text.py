# FAIL fixture — raw signal_type_id embedded in a narrative text field.
# Defect (F-131): template like 'GRAHA: category: key = value' is a raw
# internal MSR template pasted into signal_headline_text without glossing.


def build_signal_text(signal_type_id: str, category: str, key: str, value: str) -> str:
    # BAD: raw internal token in narrative text
    signal_headline_text = f"{signal_type_id}: {category}: {key} = {value}"
    return signal_headline_text


def build_row(graha: str, category: str, key: str, val: str) -> dict:
    return {
        "signal_headline_text": f"GRAHA: {category}: {key} = {val}",  # BAD: raw template
        "signal_text": f"{graha} {category} {key}",                   # also bad
    }
