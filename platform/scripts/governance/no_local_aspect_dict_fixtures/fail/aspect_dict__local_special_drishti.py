# FAIL fixture — local graha-to-aspect-degree dict (SPECIAL_DRISHTI_DEG pattern)
# This is the defect class: a file-local dict mapping planet names to aspect degree lists.
# It must NOT be defined here; use the canonical oracle in brahmagyan/aspects.py.

SPECIAL_DRISHTI_DEG = {
    "Mars": [90.0, 180.0, 210.0],
    "Jupiter": [120.0, 180.0, 240.0],
    "Saturn": [60.0, 180.0, 270.0],
}
_DEFAULT_DRISHTI_DEG = [180.0]


def get_aspects(graha: str) -> list:
    return SPECIAL_DRISHTI_DEG.get(graha, _DEFAULT_DRISHTI_DEG)
