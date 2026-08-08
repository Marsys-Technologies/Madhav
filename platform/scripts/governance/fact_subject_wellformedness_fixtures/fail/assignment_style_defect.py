# FAIL fixture — same defect class via the bare-assignment shape rather than
# a dict-literal key (fact_subject = <expr> instead of "fact_subject": <expr>).
def _build_row(planet_name, category):
    fact_subject = planet_name.upper()
    return {"fact_category": category, "fact_subject": fact_subject}
