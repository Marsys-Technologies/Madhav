# FAIL fixture — a literal reproduction of the Lane A1 ga_condition_writer.py
# defect (pre-fix): fact_subject built from a bare .upper() on a Title-case
# graha name, with no PLANET_TO_SUBJECT/norm_graha routing anywhere.
for graha in ALL_GRAHAS:
    rows.append({
        "fact_category": "graha_avastha_baladi_per_varga",
        "fact_subject": graha.upper(),
        "fact_key": f"{varga_code}.baladi",
    })
