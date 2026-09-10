# FAIL fixture — local graha drishti dict using frozenset (NB_GRAHA_DRISHTI pattern)
# Defect class: file-local dict mapping planet names to frozenset of aspect house offsets.

NB_GRAHA_DRISHTI: dict = {
    "mars": frozenset({4, 7, 8}),
    "jupiter": frozenset({5, 7, 9}),
    "saturn": frozenset({3, 7, 10}),
}
NB_DEFAULT_DRISHTI = frozenset({7})


def check_aspect(graha: str, house_offset: int) -> bool:
    aspects = NB_GRAHA_DRISHTI.get(graha.lower(), NB_DEFAULT_DRISHTI)
    return house_offset in aspects
