# PASS fixture — the established post-Lane-A1 safe idiom: PLANET_TO_SUBJECT.get()
# with a .upper() fallback IN THE SAME EXPRESSION. The .upper() only fires for
# a body genuinely unknown to the map; the SSoT is still consulted first.
for graha in ALL_GRAHAS:
    rows.append({
        "fact_category": "graha_avastha_sayanadi",
        "fact_subject": PLANET_TO_SUBJECT.get(graha, graha.upper()),
        "fact_key": "D1",
    })
