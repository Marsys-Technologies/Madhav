# PASS fixture — dicts that look like planet data but are NOT aspect-degree maps.
# The scanner must not flag these.

# A house-signification dict (not aspect degrees)
HOUSE_SIGNIFICATIONS: dict = {
    "Sun": [1, 9, 10],
    "Moon": [4],
    "Mars": [1, 3, 6, 8, 10],
}

# A strength dict (not aspect degrees)
NATURAL_STRENGTHS: dict = {
    "Sun": 0.8,
    "Moon": 0.7,
    "Mars": 0.7,
}

# A timing constant dict (not aspect degrees)
PERIOD_YEARS: dict = {
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
}
