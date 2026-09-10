# PASS fixture — planet-keyed dicts that are NOT dignity tables.
# Scanner must not flag sign-lord, natural-friend, or other planet-indexed dicts
# that do not contain {exalt, debil, own, neutral, moolatrikona} keys.

SIGN_LORDS = ["Mars", "Venus", "Mercury", "Moon", "Sun", "Mercury",
              "Venus", "Mars", "Jupiter", "Saturn", "Saturn", "Jupiter"]

NATURAL_FRIENDS = {
    "Sun": ["Moon", "Mars", "Jupiter"],
    "Moon": ["Sun", "Mercury"],
    "Mars": ["Sun", "Moon", "Jupiter"],
}

PERIOD_YEARS = {
    "Sun": 6, "Moon": 10, "Mars": 7, "Rahu": 18, "Jupiter": 16,
    "Saturn": 19, "Mercury": 17, "Ketu": 7, "Venus": 20,
}
